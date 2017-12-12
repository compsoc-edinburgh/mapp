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
                            port=22, timeout=60)
        


    # Runs a user check on the remote host
    def usercheck(self):
        stdin, stdout, stderr = self.client.exec_command("w -h")
        users = stdout.readlines()
        
        data_dict = {
            "user"   : "",
            "active" : ""
        }
        
        for user in users:
            try:
                user = re.split("\s+", user)
                
                if re.match("tty\d+", user[1]) is not None:
                    usr_i, usr_o, usr_e = self.client.exec_command("finger %s -p" % user[0])
                    out = re.search("Name: (.*)", usr_o.readline())
                    
                    self.crypto.update(str(out.group(1)) + str(config.MAPP_SECRET))

                    data_dict['user']      = self.crypto.hexdigest()
                    data_dict['active']    = user[3]
            
            except AttributeError, IndexError:
                pass

        print_usr = "None"
        try:
            if data_dict['user'] != "":
                print_usr = data_dict['user'][:15] + "..."
        except Exception:
            pass
            
        sys.stdout.write("USER on %s: %s\n" % (self.hostname, print_usr))
        Snoop.checkin(self.hostname, username=data_dict['user'], active=data_dict['active'], status="online")
        return data_dict

    
    # $ wall the remote host with message:str
    def wall(self,message):
        stdin, stdout, stderr = self.client.exec_command("echo '%s' | wall" % str(message))


    # Callback to the web service to update
    @staticmethod
    def checkin(hostname, username="", active="", status=""):
        data_dict = {
            "hostname"     : str(hostname),
            "user"         : str(username),
            "active"       : str(active),
            "timestamp"    : str(datetime.now().isoformat()),
            "callback-key" : str(config.CALLBACK_KEY),
            "status"       : str(status),
        }
        
        url = "https://localhost:5000/update"
        payload = json.dumps(data_dict)
        headers={'Content-Type':   'application/json'}

        try:
            r = requests.post(url, data=payload, headers=headers, verify=False, timeout=20)
            if r.status_code != 200:
                sys.stderr.write("ERROR: couldn't reach callcack, got %d\n" % r.status_code)
            else:
                sys.stderr.write("CALLBACK ok for %s %s\n" % (hostname, data_dict['timestamp']))
        except Exception as e:
            sys.stderr.write("********\nERROR (%s) When opening url : %s\n" % (hostname, str(e)))
        

def mapf(serv):
    try:
        s = Snoop(username, password, serv)
        userl = s.usercheck()
    except Exception as e:
        sys.stderr.write("NO-GO for host %s : %s\n" % (serv, str(e)))
        Snoop.checkin(serv, status="offline")

if __name__ == "__main__":

    servers = ['localhost']
    try:
        server_file = open(sys.argv[2], 'r')
        servers = json.loads(server_file.read())
        server_file.close()
    except IOError:
        print("Input server list '"+sys.argv[2]+"' not found.")
    except IndexError:
        print("No input file")
    except ValueError:
        print("Malformed JSON input list")

        
    try:
        username = str(sys.argv[1])
    except IndexError:
        raise Exception("Expect command line arguments <username> <hosts.json>")

    password = getpass.getpass("Remote Password for %s on all machines:" % username)

    def mapf(serv):
        try:
            s = Snoop(username, password, serv)
            userl = s.usercheck()
        except Exception as e:
            sys.stdout.write("NO-GO for host %s : %s\n" % (serv, str(e)))
            Snoop.checkin(serv, status="offline")

    # Run at different frequencies throughought the day
    def heuristic_run():
        now = datetime.now()
        go = False
        if now.hour > 22 or now.hour < 6:
            go = now.minute      == 0        # hourly
            
        elif now.hour > 18 or now.hour < 9:
            go = now.minute % 30 == 0        # half-hourly
            
        elif (now.minute >= 50 or now.minute <= 10) and now.isoweekday() <= 5:
            go = now.minute % 5  == 0        # 5 minute during week on the hour

        else:
            go = now.minute % 15 == 0        # 15 minute default
            
        go = go and now.second == 0          # Only fire on the 1st second

        if go:
            time.sleep(1)
            return True
        else:
            return False

    sys.stdout.write("CHECKING authentication...\n")

    try:
        authcheck = Snoop(username, password, servers[0])
        del authcheck
    except Exception as e:
        sys.stdout.write("AUTH FAIL! Reason: (%s)\n" % str(e))
        #sys.exit()

    sys.stdout.write("AUTH OK, starting initial run...\n")
    
    p = Pool(30)
    p.map(mapf, servers)
    del p

    sys.stdout.write("INIT OK, waiting...\n")

    while True:
        if heuristic_run():
            p = Pool(30)
            p.map(mapf,servers)
            del p
            sys.stdout.write("DONE iteration over %d servers at %s\n" % (len(servers), str(datetime.now().isoformat())))
