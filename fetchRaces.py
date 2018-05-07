#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import fetchRace
import concurrent.futures

def run(fname = "listeRaces.txt"):
    with open(fname, 'r') as f:
        with concurrent.futures.ProcessPoolExecutor(max_workers=3) as executor:
            for idr in f.readlines():
                executor.submit(fetchRace.archive, idr[:-1])

if __name__ == "__main__":
    run()