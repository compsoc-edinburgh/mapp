# Class to connect to and monitor remote machine
import paramiko
import os
import getpass
import sys

class Snoop:
    # Init method, creates SSH connection to remote host
    def __init__(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            username = str(sys.argv[1])
            hostname = str(sys.argv[2])
        except IndexError:
            raise Exception("Expect command line arguments <username> <host>")

        self.pswd = getpass.getpass('Remote Password:')
        self.client.connect(username=username,
                            password=str(self.pswd),
                            hostname=hostname,
                            port=22)
        


    # Runs a user check on the remote host
    def usercheck(self):
        stdin, stdout, stderr = self.client.exec_command("who")
        users = stdout.readlines()
        sys.stderr.write(stderr.read())
        
        for user in users:
            print user
            
            
        
    # Walls the remote host with message:str
    def wall(self,message):
        stdin, stdout, stderr = self.client.exec_command("echo '%s' | wall" % message)
        sys.stderr.write(stderr.read())

if __name__ == "__main__":
    this = Snoop()
    this.usercheck()
