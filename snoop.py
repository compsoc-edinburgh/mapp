# Class to connect to and monitor remote machine
import paramiko
import os
import getpass
import sys
import time
import re
import json
import urllib2
import datetime
from multiprocessing import Process, Lock, Pool
        

class Snoop:
    # Init method, creates SSH connection to remote host
    def __init__(self, username, password, hostname, lock):
        self.lock = lock
        self.hostname = hostname
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(username=username,
                            password=password,
                            hostname=hostname,
                            port=22)
        


    # Runs a user check on the remote host
    def usercheck(self):
        stdin, stdout, stderr = self.client.exec_command("w -h")
        users = stdout.readlines()
        
        ret = []
        for user in users:
            try:
                user = re.split("\s+", user)
                usr_i, usr_o, usr_e = self.client.exec_command("finger %s" % user[0])
                out = re.search("Name: (.*)", usr_o.readline())
                user = (out.group(1), user[4])
                if user[2] == ":0":
                    ret.append(user)
            except AttributeError, IndexError:
                pass
        
        self.lock.acquire()
        sys.stderr.write("USERS @ %s: %s\n" % (self.hostname, str(ret)))
        self.lock.release()

        data_dict = dict()
        data_dict['hostname']  = self.hostname
        data_dict['user']      = str(ret[0])
        data_dict['active']    = str(ret[1])
        data_dict['timestamp'] = str(datetime.utcnow().isoformat())
        
        req = urllib2.Request(
            os.environ.get("SNOOP_URL"),
            json.dumps(data_dict),
            {'Content-Type': 'application/json'})

        try:
            f = urllib2.urlopen(req)
            f.close()
        except as e:
            self.lock.acquire()
            sys.stderr.write("ERR for %s : %s\n" % (self.hostname, str(e)))
            self.lock.release()
        return ret
            
    # $wall the remote host with message:str
    def wall(self,message):
        stdin, stdout, stderr = self.client.exec_command("echo '%s' | wall" % str(message))


        
        
if __name__ == "__main__":
    
    servers = ['rosalinde', 'montparnasse', 'dancaire', 'lillas', 'vervcelli', 'zuniga',
               'rieti', 'venosa','trento', 'pavia', 'orlofsky', 'mereb', 'radames', 'ascoli',
               'tivoli', 'wideopen', 'twite', 'swanland', 'enna', 'gosforth', 'albenga',
               'hart', 'stork', 'brujon', 'pharoah', 'combeferre', 'remendado', 'escamillo',
               'micaela', 'lavello', 'marsala', 'mantua', 'spoleto', 'falconara', 'amelia',
               'parrot', 'wigton', 'falcon', 'raven', 'ciociosan', 'roxanne', 'yakuside',
               'lesgles', 'goro', 'daae', 'owl', 'owl', 'penguin', 'lodi', 'luni', 'palermo',
               'falke', 'scarpia', 'cavaradossi', 'amneris', 'babet', 'amanasro', 'ceilingcat',
               'lowick', 'seascale', 'ostiglia', 'allonby', 'yvan', 'claquesous', 'tosca',
               'spoletta', 'enjolras', 'nehebka', 'parma', 'carmen', 'messina', 'gabriel',
               'aida', 'frosch', 'thenardier', 'zoser', 'pollenzo', 'palestrina', 'ravenna',
               'bechstein', 'mocha', 'bluthner', 'dove', 'scarecrow', 'giry', 'savona',
               'vicenza', 'velma', 'avellino', 'morales', 'pontremoli', 'velletri',
               'angelotti', 'joly', 'courfeyrac', 'crow', 'giudicelli', 'pipit']


    lock = Lock()
    
    try:
        username = str(sys.argv[1])
    except IndexError:
        raise Exception("Expect command line arguments <username>")

    password = getpass.getpass("Remote Password for %s on all machines:" % username)
    
    def mapf(serv):
        try:
            s = Snoop(username, password, serv, lock)
            userl = s.usercheck()
        except as e:
            lock.acquire()
            sys.stderr.write("ERR for %s : %s\n" % (self.hostname))
            lock.release()
    
    p = Pool(max(len(servers),30))
    p.map(mapf,servers)

    #for server in servers:
    #    mapf(server)
