# Class to connect to and monitor remote machine
import paramiko
import getpass
import sys
import time
import re
import json
import requests
import hashlib
import socket
from datetime import datetime
from multiprocessing import Process, Pool

import config
requests.packages.urllib3.disable_warnings()

class Snoop:
    # Init method, creates SSH connection to remote host
    def __init__(self, username, hostname):
        self.hostname = hostname
        self.client = paramiko.SSHClient()
        self.crypto = hashlib.sha512()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.client.connect(username=username,
                            gss_auth=True,
                            gss_kex=True,
                            gss_deleg_creds=False, # turn off afs access
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
                
                # if re.match("tty\d+", user[1]) is not None:
                if user[1] == ":0":
                    usr_i, usr_o, usr_e = self.client.exec_command("finger %s -p" % user[0])
                    out = re.search("Name: (.*)", usr_o.readline())
                    
                    self.crypto.update(str(out.group(1)) + str(config.MAPP_SECRET))

                    data_dict['user'] = self.crypto.hexdigest()
                    data_dict['active'] = user[3]
            
            except (AttributeError, IndexError) as e:
                pass

        print_usr = "None"
        try:
            if data_dict['user'] != "":
                print_usr = data_dict['user'][:15] + "..."
        except Exception as e:
            pass
            
        sys.stdout.write("USER on %s: %s\n" % (self.hostname, print_usr))
        return Snoop.checkin(self.hostname, username=data_dict['user'], active=data_dict['active'], status="online")

    # Real callback to the web service
    @staticmethod
    def update_machines(machines):
        url = "https://mapp.tardis.ed.ac.uk/api/update"
        payload = {
            "machines": machines,
            "callback-key": str(config.CALLBACK_KEY)
        }

        headers = {"Content-Type": "application/json"}

        try:
            r = requests.post(url, data=json.dumps(payload), headers=headers, verify=False, timeout=20)
            if r.status_code != 200:
                sys.stderr.write("ERROR: couldn't reach callback, got %d\n" % r.status_code)
            else:
                sys.stderr.write("CALLBACK ok for all machines %s\n" % str(datetime.now().isoformat()))
        except Exception as e:
            sys.stderr.write("********\nERROR (all) When opening url : %s\n" % (str(e))) 
        
    # Callback to the web service to update
    @staticmethod
    def checkin(hostname, username="", active="", status=""):
        return {
            "hostname": str(hostname),
            "user": str(username),
            "active": str(active),
            "timestamp": str(datetime.now().isoformat()),
            "status": str(status),
        }

if __name__ == "__main__":

    servers = ['localhost']
    try:
        server_file = open(sys.argv[1], 'r')
        servers = json.loads(server_file.read())
        server_file.close()
    except IOError:
        print("Input server list '"+sys.argv[2]+"' not found.")
    except IndexError:
        print("No input file")
    except ValueError:
        print("Malformed JSON input list")

    username = getpass.getuser()
    password = ""
    if "localhost" in servers:
        servers = [socket.gethostname()]
        print("Using name {}", servers[0])
    else:
        try:
            username = str(sys.argv[2])
        except IndexError:
            pass
            # raise Exception("Expect command line arguments <hosts.json> <username>")
        getpass.getpass("Is username %s okay?" % username)

    def mapf(serv):
        try:
            s = Snoop(username, serv)
            return s.usercheck()
        except Exception as e:
            sys.stdout.write("NO-GO for host %s : %s\n" % (serv, str(e)))
            return Snoop.checkin(serv, status="offline")

    # Run at different frequencies throughought the day
    def heuristic_run():
        now = datetime.now()
        go = False

	# between 6pm and 9am
        if now.hour > 18 or now.hour < 9:
            go = now.minute % 30 == 0        # half-hourly
        # during the weekday, hh:50, hh:55, hh:60, hh:65, hh:70
        elif (now.minute >= 50 or now.minute <= 10) and now.isoweekday() <= 5:
            go = now.minute % 5 == 0        # 5 minute during week on the hour
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
        authcheck = Snoop(username, servers[0])
        del authcheck
    except Exception as e:
        sys.stdout.write("AUTH FAIL! Reason: (%s)\n" % str(e))
        sys.exit()

    sys.stdout.write("AUTH OK, starting initial run...\n")

    first = True
 
    while True:
        try:
            if heuristic_run() or first:
                p = Pool(30)
                results = filter(lambda x: x is not None, p.map(mapf,servers))
                del p
                sys.stdout.write("DONE iteration over %d servers at %s\n" % (len(servers), str(datetime.now().isoformat())))
                Snoop.update_machines(results)
                sys.stdout.write("RESULTS %s\n" % str(results))
                if first:
                    first = False
                    sys.stdout.write("INIT OK, waiting...\n")

        except KeyboardInterrupt:
            sys.exit()
