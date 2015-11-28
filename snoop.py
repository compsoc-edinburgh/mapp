# Class to connect to and monitor remote machine
import paramiko
import os
import getpass
import sys
import time

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
        stdin, stdout, stderr = self.client.exec_command("who")
        users = stdout.readlines()

        refined = []
        for user in users:
            user = user.split(' ')[0]
            usr_i, user, usr_e = self.client.exec_command("finger %s" % user)
            out = user.readlines()

            
            refined.append(out)

        return refined
            
            
        
    # Walls the remote host with message:str
    def wall(self,message):
        stdin, stdout, stderr = self.client.exec_command("echo '%s' | wall" % message)
        sys.stderr.write(stderr.read())




def f(username, password, server):
    try:
        s = Snoop(username, password, server)
        return s.usercheck()
    except paramiko.AuthenticationException:
        return []

        
        
if __name__ == "__main__":
    servers = ["fez.tardis.ed.ac.uk",
               "torchwood.tardis.ed.ac.uk",
               "fez.tardis.ed.ac.uk",
               "torchwood.tardis.ed.ac.uk",
               "fez.tardis.ed.ac.uk"]
    
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
