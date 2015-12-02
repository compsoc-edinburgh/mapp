# Class to connect to and monitor remote machine
import paramiko
import os
import getpass
import sys
import time
import re
import json
import requests
import hashlib
from datetime import datetime
from multiprocessing import Process, Pool

import config
requests.packages.urllib3.disable_warnings()

class Snoop:
    # Init method, creates SSH connection to remote host
    def __init__(self, username, password, hostname):
        self.hostname = hostname
        self.client = paramiko.SSHClient()
        self.crypto = hashlib.sha512()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(username=username,
                            password=password,
                            hostname=hostname,
                            port=22, timeout=8)
        


    # Runs a user check on the remote host
    def usercheck(self):
        stdin, stdout, stderr = self.client.exec_command("w -h")
        users = stdout.readlines()
        
        data_dict = {
            "user":"",
            "active":""
        }
        ret = []
        
        for user in users:
            try:
                user = re.split("\s+", user)
                usr_i, usr_o, usr_e = self.client.exec_command("finger %s -p" % user[0])
                out = re.search("Name: (.*)", usr_o.readline())
                self.crypto.update(str(out.group(1)) + str(config.MAPP_SECRET))
                ret = (self.crypto.hexdigest(), user[4])
                if re.match("tty\d+", user[1]) is not None:
                    data_dict['user']      = str(ret[0])
                    data_dict['active']    = str(ret[1])
            except AttributeError, IndexError:
                pass
        
        sys.stdout.write("USER on %s: %s\n" % (self.hostname, data_dict['user']))
        Snoop.checkin(self.hostname, username=data_dict['user'], active=data_dict['active'])
        return ret

    
    # $ wall the remote host with message:str
    def wall(self,message):
        stdin, stdout, stderr = self.client.exec_command("echo '%s' | wall" % str(message))


    # Callback to the web service to update
    @staticmethod
    def checkin(hostname, username="", active=""):
        data_dict = {
            "hostname":str(hostname),
            "user":str(username),
            "active":str(active),
            "timestamp":str(datetime.utcnow().isoformat())
        }
        
        url = "https://localhost:5000/update"
        payload = json.dumps(data_dict)
        headers={'Content-Type': 'application/json'}

        r = requests.post(url, data=payload, headers=headers, verify=False)
        if r.status_code != 200:
            sys.stderr.write("ERROR: couldn't reach callcack, got %d\n" % r.status_code)
        else:
            sys.stderr.write("CALLBACK ok\n")

        # req = urllib2.Request(
        #     "http://localhost:5000/update",
        #     json.dumps(data_dict),
        #     {'Content-Type': 'application/json'})
        # try:
        #     f = urllib2.urlopen(req, timeout=5)
        #     print json.loads(f.read())['status']
        #     f.close()
        # except Exception as e:
        #     sys.stderr.write("********\nERROR %s error when opening url : %s\n" % (hostname, str(e)))

        
        
if __name__ == "__main__":

    servers = ['localhost']
    try:
        server_file = open(sys.argv[2], 'r')
        servers = json.loads(server_file.read())
    except IOError:
        print("Input server list '"+sys.argv[1]+"' not found.")
    except IndexError:
        print("No input file")
    except ValueError:
        print("Malformed JSON input list")

        
    try:
        username = str(sys.argv[1])
    except IndexError:
        raise Exception("Expect command line arguments <username>")

    password = getpass.getpass("Remote Password for %s on all machines:" % username)
    
    def mapf(serv):
        try:
            s = Snoop(username, password, serv)
            userl = s.usercheck()
        except Exception as e:
            sys.stderr.write("NO-GO for host %s : %s\n" % (serv, str(e)))
            Snoop.checkin(serv)

    p = Pool(30)

    while True:
        p.map(mapf,servers)
        sys.stderr.write("INFO sleeping\n")
        time.sleep(300)

    #for server in servers:
    #    mapf(server)
