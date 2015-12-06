import csv
import sys

from redis import Redis

r = Redis()

# Arg1: CSV file to import
# Arg2: -a if you want to push instead of update
# Arg3: List to push onto, by name

with open(sys.argv[1], 'r') as placecsv:
    preader = csv.reader(placecsv)

    try:
        if sys.argv[2] == "-a":
            r.hset(sys.argv[3], "name", sys.argv[4])
            r.hset(sys.argv[3], "key", sys.argv[3])
    except IndexError:
        pass
    
    for rownumber, row in enumerate(preader):
        for colnumber, machine in enumerate(row):
            try:
                if sys.argv[2] == "-a":
                    if machine != "":
                        r.lpush(sys.argv[3],machine)
            except IndexError:
                pass
            r.hmset(machine, {
                'hostname': machine,
                'col': colnumber,
                'row': rownumber
            })
