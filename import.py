import csv

from redis import Redis

r = Redis()

with open('/home/skull/Downloads/drillhall.csv', 'r') as drillhallcsv:
    dhreader = csv.reader(drillhallcsv)
    for rownumber, row in enumerate(dhreader):
        for colnumber, machine in enumerate(row):
            r.hmset(machine, {
                'hostname': machine,
                'col': colnumber,
                'row': rownumber
            })
