#!/usr/bin/env python3
#-*- coding:utf-8 -*-

#auth parameters
import archiveLib
import logging
import magic

def testMimeRacemap(idr):
    session = archiveLib.makeSession()

    res = archiveLib.fetch_png(session, archiveLib.VLMRACEMAP.format(idr=idr), "tmp/{idr}.png".format(idr=idr))
    mime = magic.detect_from_filename("tmp/{idr}.png".format(idr=idr))
    
    logging.info("Type %s is %s", idr, mime.mime_type)
    return(True)

if __name__ == "__main__":
    archiveLib.iterRaces(func=testMimeRacemap)
    #testMimeRacemap("2008443505")