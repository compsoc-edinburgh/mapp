#!/usr/bin/env python
import argparse

import csv
import sys

from redis import Redis

parser = argparse.ArgumentParser()
parser.add_argument('room')
parser.add_argument('file')
parser.add_argument('-k', '--redis-key', dest='authkey')

args = parser.parse_args()

if args.authkey:
    r = Redis().from_url("redis://:{}@localhost/0".format(args.authkey))
else:
    r = Redis()

machines = set()

with open(args.file, 'r') as placecsv:
    preader = csv.reader(placecsv)

    for rownumber, row in enumerate(preader):
        for colnumber, machine in enumerate(row):
            print(rownumber, colnumber, machine)
            machines.add(machine)
            
            r.hmset(machine, {
                'hostname': machine,
                'col': colnumber,
                'row': rownumber,
                'user': '',
            })
    machines.add("")

machines.remove("")

# empty the list
machines_key = "{}-machines".format(args.room) 
r.delete(machines_key)
for machine in machines:
    r.lpush(machines_key, machine)

