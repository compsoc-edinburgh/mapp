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
        sys.stderr.write("INFO: %s\n" % str(ret))
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
    
    servers = ["fez.tardis.ed.ac.uk",
               "torchwood.tardis.ed.ac.uk"]

    lock = Lock()
    
    try:
        username = str(sys.argv[1])
    except IndexError:
        raise Exception("Expect command line arguments <username>")

    password = getpass.getpass("Remote Password for %s on all machines:" % username)
    
    def mapf(serv):
        s = Snoop(username, password, serv, lock)
        userl = s.usercheck()
    
    p = Pool(len(servers))
    p.map(mapf,servers)
