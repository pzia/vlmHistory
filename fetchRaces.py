#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import fetchRace

def run(fname = "listeRaces.txt"):
    with open(fname, 'r') as f:
        for idr in f.readline():
            fetchRace.archive(idr)

if __name__ == "__main__":
    run()