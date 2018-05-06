#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import config

import json #write json
import tarfile #tar files
import logging #log event
logging.basicConfig(level=logging.INFO)

import os.path #test paths
import shutil 

import requests #fetch urls
#Only for debug purpose
#import requests_cache
#monkey patching...
#requests_cache.install_cache('httpcache', backend='sqlite', expire_after=12*3600)

import concurrent.futures #multithreading

#parameters
VLMWS = "https://v-l-m.org/ws"
VLMRACERESULTS = VLMWS+"/raceinfo/results.php?idr={idr}"
VLMBOATTRACKS = VLMWS+"/boatinfo/tracks.php?idu={idu}&idr={idr}&starttime=1"

DISKPREFIX = "tmp/{idr}"
DISKRACERESULTS = DISKPREFIX+"/results.json"
DISKBOATTRACKS = DISKPREFIX+"/{idu}.json"

BACKUPPREFIX = "backup"
BACKUPIDR = BACKUPPREFIX+"/{idr}.tar.gz"

def idr_archived(idr):
    return os.path.exists(BACKUPIDR.format(idr=idr))

def archive(idr) :
    if idr_archived(idr): #already done ?
        logging.info("%s is already archived", idr)
        return True

    #Prepare session
    session = requests.session()
    session.auth = config.VLMAUTH
    adapter = requests.adapters.HTTPAdapter(
    pool_connections=100, pool_maxsize=100)
    session.mount('https://', adapter)
    session.headers.update({'Connection':'Keep-Alive'})

    root = DISKPREFIX.format(idr=idr)

    if not os.path.exists(root) :
        logging.info("Creating %s for %s", root, idr)
        os.mkdir(root)

    diskresult = DISKRACERESULTS.format(idr=idr)

    if not os.path.exists(diskresult):
        logging.info("Fetching results for %s", idr)
        result = session.get(VLMRACERESULTS.format(idr = idr))
        with open(diskresult, 'w') as f:
            json.dump(result.json(), f, ensure_ascii=False)

    errors = []
    with open(diskresult, 'r') as f:
        results = json.load(f)
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            # Start the load operations and mark each future with its URL
            future_to_url = {}
            
            for u in results['results'] :
                future = executor.submit(fetch_idr_idu, session, idr, u)
                future_to_url[future] = u
            for future in concurrent.futures.as_completed(future_to_url):
                u = future_to_url[future]
                try:
                    if not future.result() :
                        errors.append(u)
                except Exception as exc:
                    logging.error("fetching %s in %s generated an exception %s", u, idr, exc)
                    errors.append(u)
                    
    if len(errors) > 0 :
        logging.error("Fetching %s was incomplete", idr)
    else :
        logging.info("Archiving %s", idr)
        tar = tarfile.open(BACKUPIDR.format(idr=idr), "w:gz")
        tar.add(root)
        tar.close()
        logging.info("Archived %s", idr)
        shutil.rmtree(DISKPREFIX.format(idr=idr), ignore_errors=True)

def fetch_idr_idu(session, idr, idu) :
    disktracks = DISKBOATTRACKS.format(idr=idr, idu=idu)
    if not os.path.exists(disktracks) :
        logging.info("Fetching tracks for %s in %s", idu, idr)
        result = session.get(VLMBOATTRACKS.format(idr = idr, idu=idu))
        with open(disktracks, 'w') as f:
            json.dump(result.json(), f, ensure_ascii=False)
    return True

if __name__ == "__main__":
    archive("20071001")