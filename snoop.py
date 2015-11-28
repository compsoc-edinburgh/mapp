# Class to connect to and monitor remote machine
import paramiko
import os
import getpass
import sys
import time
import re
import json
import urllib2
from multiprocessing import Process, Lock, Pool
        

class Snoop:
    # Init method, creates SSH connection to remote host
    def __init__(self, username, password, hostname, lock=None):
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
                user = re.split("\s+", user.encode("ascii"))
                usr_i, usr_o, usr_e = self.client.exec_command("finger %s" % user[0])
                out = re.search("Name: (.*)", usr_o.readline().encode("ascii"))
                user = (out.group(1), user[4])
                ret.append(user)
            except AttributeError, IndexError:
                pass
        if self.lock is not None:
            self.lock.acquire()
        sys.stderr.write("USERS @ %s: %s\n" % (self.hostname, str(ret)))
        if self.lock is not None:
            self.lock.release()
        return ret
            
            
        
    # $wall the remote host with message:str
    def wall(self,message):
        stdin, stdout, stderr = self.client.exec_command("echo '%s' | wall" % str(message))
        if self.lock is not None:
            self.lock.acquire()
        sys.stderr.write("ERROR on REMOTE: %s\n" % stderr.read())
        if self.lock is not None:
            self.lock.release()


        
        
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
        s = Snoop(username, password, serv, lock)
        userl = s.usercheck()
    
    p = Pool(max(len(servers),1))
    p.map(mapf,servers)
