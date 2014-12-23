'''
Created on Dec 23, 2014

@author: justin
'''


import sockLib
import Queue
import threading
import select
import time
import random

import logging

port = 12000

class Server:
    
    def __init__(self, port  = 12000):
    
        self.port = port
        self.activeClients = {} #dict of socket:protocol objects
        self.acceptQueue = Queue.Queue()
        self.serverSocket = sockLib.serverSocket(port)
        self.interruptSocket = None
        self.running = True
        
        print "creating connection"
        self.acceptThread = threading.Thread(target = self.acceptConnection)
        self.acceptThread.start()
        
        #this socket is used for notifying the process of new information
        self.interruptSocket = sockLib.JsonProtocol(sockLib.clientSocket(sockLib.gethostname(), port))
        
        print "starting server main loop"
        self.mainThread = threading.Thread(target = self.mainLoop)
        self.mainThread.start()

    def acceptConnection(self):
        
        while self.running:
            sock, address = self.serverSocket.accept()
            print "connection from", sock.getsockname()
            print "adding connection to queue"
            self.acceptQueue.put(sock)
            
            if self.interruptSocket:
                self.interruptSocket.sendData("connection accepted")
    
        print "server no longer accepting connections"
        
    def addConnections(self):
        
        while not self.acceptQueue.empty():
            
            print "adding socket to active client"
            sock = self.acceptQueue.get()
            self.activeClients[sock] = sockLib.JsonProtocol(sock)

    def stopServer(self):
        
        self.running = False
        
        #stop accept thread
        sock = sockLib.clientSocket(sockLib.gethostname(), self.port)
        sock.close()
        
        self.interruptSocket.sendData("stopping")
        
    def mainLoop(self):
        
        while self.running:

            self.addConnections()
            
            if not self.activeClients.keys():
                time.sleep(0.1)
            else:
                r,w,e  = select.select(self.activeClients.keys(), [], [])
                
                for sock in r:
                    data = self.activeClients[sock].recvData()
                
                if data is None:
                    print "client has disconnected"
                    self.activeClients.pop(sock)
                else:
                    print data

        print "main loop stopping"
    
    
    #### Define msg handlers here:
    
class Client:
    
    def __init__(self, port):
        
        self.port = port
        self.socket = sockLib.clientSocket(sockLib.gethostname(), port)
        self.protocol = sockLib.JsonProtocol(self.socket)
        
    def sendData(self, data):
        
        print "sending data", data
        self.protocol.sendData(data)
        

if __name__ == "__main__":

    server = Server(port)
    
    time.sleep(0.5)
    clients = [Client(port) for x in range(5)]
    
    time.sleep(0.1)
    for x in range(10):
        client = random.choice(clients)
        client.sendData({"msg": "magic"})

    for client in clients:
        client.socket.close()
        
    time.sleep(0.1)
    server.stopServer()