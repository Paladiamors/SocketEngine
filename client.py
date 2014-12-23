'''
Created on Dec 23, 2014

@author: justin
'''

import sockLib

class Client:
    
    def __init__(self, port):
        
        self.port = port
        self.socket = sockLib.clientSocket(sockLib.gethostname(), port)
        self.protocol = sockLib.JsonProtocol(self.socket)
        
    def sendData(self, data):
        
        print "sending data", data
        self.protocol.sendData(data)