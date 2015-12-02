import csv
import sys

from redis import Redis

r = Redis()

with open(sys.argv[1], 'r') as drillhallcsv:
    dhreader = csv.reader(drillhallcsv)
    for rownumber, row in enumerate(dhreader):
        for colnumber, machine in enumerate(row):
            #if sys.argv[2] == "-a":
            #    if machine != "":
            #        r.lpush('drillhall-machines',machine)
            r.hmset(machine, {
                'hostname': machine,
                'col': colnumber,
                'row': rownumber
            })
