#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import fetchRace

def run(fname = "listeRaces.txt"):
    with open(fname, 'r') as f:
        for idr in f.readlines():
            fetchRace.archive(idr[:-1])

if __name__ == "__main__":
    run()