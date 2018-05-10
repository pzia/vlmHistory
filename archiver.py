#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import archiveLib
import sys

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "update" :
        archiveLib.archiveRaces(func=archiveLib.updateRace)
    else :
        archiveLib.archiveRaces()