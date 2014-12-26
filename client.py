'''
Created on Dec 23, 2014

@author: justin
'''

import sockLib

class BaseClient:
    
    def __init__(self, host, port):
        
        self.host = host
        self.port = port
        self.sock = None
        self.protocol = None
        
    def connect(self):
        """
        connects to a server
        """
        self.sock = sockLib.clientSocket(self.host, self.port)
        self.protocol = sockLib.JsonProtocol(self.sock)


    def disconnect(self):
        """
        disconnects from the server
        """
        
        self.sock.close()
        self.protocol = None
        
