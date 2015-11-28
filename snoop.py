# Class to connect to and monitor remote machine
import paramiko
import os
import getpass
import sys

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
        sys.stderr.write(stderr.read())
        
        for user in users:
            print user

        s = self.client.get_transport().open_session()
        paramiko.agent.AgentRequestHandler(s)
        s.get_pty()
        s.invoke_shell()
            
            
        
    # Walls the remote host with message:str
    def wall(self,message):
        stdin, stdout, stderr = self.client.exec_command("echo '%s' | wall" % message)
        sys.stderr.write(stderr.read())


        
if __name__ == "__main__":
    servers = ["fez.tardis.ed.ac.uk",
               "torchwood.tardis.ed.ac.uk",
               "torchwood.tardis.ed.ac.uk",
               "torchwood.tardis.ed.ac.uk",
               "torchwood.tardis.ed.ac.uk"]
    
    try:
        username = str(sys.argv[1])
    except IndexError:
        raise Exception("Expect command line arguments <username>")

    password = getpass.getpass("Remote Password for %s on all machines:" % username)

    srv_cons = dict()

    for server in servers:
        try:
            srv_cons[server] = Snoop(username, password, server)
            print "------------"
            print server
            srv_cons[server].usercheck()
        except AuthenticationException:
            sys.stderr.write("ERROR: Couldn't connect to %s \n" % server)
