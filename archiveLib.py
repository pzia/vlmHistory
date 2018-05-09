#!/usr/bin/env python3
#-*- coding:utf-8 -*-

#auth parameters
import config

#libraries
import json #write json
import tarfile #tar files
import logging #log event
logging.basicConfig(level=logging.INFO)
import os.path #test paths
import shutil 
import requests #fetch urls
import concurrent.futures #multithreading

#parameters
VLM = "https://v-l-m.org"
VLMWS = VLM+"/ws"
VLMRACERESULTS = VLMWS+"/raceinfo/results.php?idr={idr}" #idr
VLMRACEDESC = VLMWS+"/raceinfo/desc.php?idrace={idr}" #idr
VLMRACEMAP = VLM+"/cache/racemaps/{idr}.png" #idr
VLMRACEEXCLUSIONS = VLMWS+"/raceinfo/exclusions.php?idr={idr}" #idr
VLMBOATTRACKS = VLMWS+"/boatinfo/tracks.php?idu={idu}&idr={idr}&starttime=1" #idr & idu

DISKPREFIX = "tmp/{idr}" #idr
DISKRACERESULTS = DISKPREFIX+"/results.json" #idr
DISKRACEDESC = DISKPREFIX+"/desc.json" #idr
DISKRACEMAP = DISKPREFIX+"/racemap.png" #idr
DISKRACEEXCLUSIONS = DISKPREFIX+"/exclusions.json" #idr
DISKBOATTRACKS = DISKPREFIX+"/{idu}.json" #idr & idu

BACKUPPREFIX = "backup"
BACKUPIDR = BACKUPPREFIX+"/{idr}.tar.gz"

CONCURRENTPROCESSES = 3
CONCURRENTTHREADS = 20

def idr_archived(idr):
    """Return True if there is a corresponding tar.gz"""
    return os.path.exists(BACKUPIDR.format(idr=idr))

def updateRace(idr):
    logging.info("Updating %s", idr)
    if idr_archived(idr):
        logging.info("Extracting %s archive", idr)
        tgz = BACKUPIDR.format(idr=idr)
        t = tarfile.open(tgz, 'r')
        t.extractall()
        os.remove(tgz)
        t.close()
    return archiveRace(idr)

def archiveRace(idr) :
    """Archive a whole race description and tracks"""
    if idr_archived(idr): #already done ?
        logging.info("%s is already archived", idr)
        return True

    #Prepare session
    session = requests.session() #new session
    session.auth = config.VLMAUTH #permanent auth to session
    adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100)
    session.mount('https://', adapter) #configure the pool
    session.headers.update({'Connection':'Keep-Alive'}) #keep alive the connections

    root = DISKPREFIX.format(idr=idr) #tmp root for files

    if not os.path.exists(root) : #create if needed
        logging.info("Creating %s for %s", root, idr)
        os.mkdir(root)

    diskresult = DISKRACERESULTS.format(idr=idr) #file path for results

    if not os.path.exists(diskresult):
        logging.info("Fetching results for %s", idr)
        result = session.get(VLMRACERESULTS.format(idr = idr)) #fetch race results
        with open(diskresult, 'w') as f:
            json.dump(result.json(), f, ensure_ascii=False)

    errors = []
    with open(diskresult, 'r') as f:
        results = json.load(f)
        with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENTTHREADS) as executor:
            future_to_url = {} #Keeping corresponding idu for logging          
            for u in results['results'] : #feed the pool
                future = executor.submit(fetch_idr_idu_boattracks, session, idr, u)
                future_to_url[future] = u
            for future in concurrent.futures.as_completed(future_to_url):
                u = future_to_url[future]
                try:
                    if not future.result() : #Return is False, not a success
                        errors.append(u)
                except Exception as exc:
                    #Exception, not a success at all
                    logging.error("fetching %s in %s generated an exception %s", u, idr, exc)
                    errors.append(u)
                    
    if len(errors) > 0 :
        logging.error("Fetching %s was incomplete", idr)
        return False
    else :
        logging.info("Archiving %s", idr)
        tar = tarfile.open(BACKUPIDR.format(idr=idr), "w:gz")
        tar.add(root)
        tar.close()
        logging.info("Archived %s", idr)
        shutil.rmtree(DISKPREFIX.format(idr=idr), ignore_errors=True)
        return True

def fetch_idr_idu_boattracks(session, idr, idu) :
    """Fetch tracks for idu in idr"""
    disktracks = DISKBOATTRACKS.format(idr=idr, idu=idu)
    if not os.path.exists(disktracks) :
        logging.info("Fetching tracks for %s in %s", idu, idr)
        result = session.get(VLMBOATTRACKS.format(idr = idr, idu=idu))
        with open(disktracks, 'w') as f:
            json.dump(result.json(), f, ensure_ascii=False)
    return True

def fetch_idr_idu(session, idr, idu, url_pattern, disk_pattern):
    return fetch_json(session, url_pattern.format(idr=idr, idu=idu), disk_pattern.format(idr=idr, idu=idu))

def fetch_idr(session, idr, url_pattern, disk_pattern):
    return fetch_json(session, url_pattern.format(idr=idr), disk_pattern.format(idr=idr))

def fetch_json(session, url, file):
    """Fetch url and save as a file"""
    #Throw exception mainly if it's not possible to create the file or if there is no valid json output
    if not os.path.exists(file):
        logging.info("Fetching %s from %s", file, url)
        result = session.get(url)
        d = result.json()
        if not d['success'] :
            return False
        with open(file, 'w') as f:
            json.dump(d, f, ensure_ascii=False)
    return True

def archiveRaces(fname = "listeRaces.txt", func=archiveRace):
    with open(fname, 'r') as f:
        with concurrent.futures.ProcessPoolExecutor(max_workers=CONCURRENTPROCESSES) as executor:
            for idr in f.readlines():
                executor.submit(func, idr[:-1])


if __name__ == "__main__":
    print('Run archiver.py')