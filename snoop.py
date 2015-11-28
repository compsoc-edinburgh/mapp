# Class to connect to and monitor remote machine
import paramiko
import os
import getpass
import sys
import time
import re

from multiprocessing import Process, Lock, Pool

class Collector:
    def __init__(self, username, password, servers):
        self.username = str(username)
        self.password = str(password)
        self.servers  = list(servers)
        self.pool = Pool(len(servers))
        self.out = []

    def run(self):
        for server in self.servers:
            print "trying " + server
            self.pool.apply_async(self.mapfun, args=(server, ), callback=self.callback)
        self.pool.close()
        self.pool.join()
        print self.out

    def callback(self, result):
        print result
        self.out.append(result)

    @staticmethod
    def mapfun(un, pw, hn):
        s = Snoop(username=un, password=pw, hostname=hn)
        return s.usercheck()
        

class Snoop:
    # Init method, creates SSH connection to remote host
    def __init__(self, username, password, hostname):
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
        return ret
            
            
        
    # $wall the remote host with message:str
    def wall(self,message):
        stdin, stdout, stderr = self.client.exec_command("echo '%s' | wall" % str(message))
        sys.stderr.write("ERROR on REMOTE: %s" % stderr.read())


        
        
if __name__ == "__main__":
    servers = ["fez.tardis.ed.ac.uk",
               "torchwood.tardis.ed.ac.uk"]
    
    try:
        username = str(sys.argv[1])
    except IndexError:
        raise Exception("Expect command line arguments <username>")

    password = getpass.getpass("Remote Password for %s on all machines:" % username)
    
    srv_cons = dict()

    

    #coll = Collector(username, password, servers)

    #coll.run()

    # threads = []
    # for server in servers:
    #    thread = Process( target=f, args=(username, password, server, ))
    #    thread.start()
    #    threads.append(p)
       
        

    for server in servers:
        srv_cons[server] = Snoop(username, password, server)
        print "------------"
        print server
        print srv_cons[server].usercheck()
