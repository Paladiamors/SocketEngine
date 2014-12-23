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
from client import Client

port = 12000

class Server:
    
    def __init__(self, port  = 12000):
    
        self.port = port
        self.activeClients = {} #dict of socket:protocol objects
        self.acceptQueue = Queue.Queue()
        self.serverSocket = sockLib.serverSocket(port)
        self.interruptSocket = None
        self.running = True
        

    def _acceptConnections(self):
        """
        to be used in a threaded process to accept incoming connections
        connections are added to self.acceptQueue 
        
        an interrupt msg is sent to the main loop to have the socket added to the list of readable sockets
        """
        
        while self.running:
            sock, address = self.serverSocket.accept()
            print "connection from", sock.getsockname()
            print "adding connection to queue"
            self.acceptQueue.put(sock)
            
            if self.interruptSocket:
                self.interruptSocket.sendData("connection accepted")
    
        print "server no longer accepting connections"
        
    def _addConnections(self):
        """
        called in the mainLoop to add new sockets to the list of activeConnections
        """
        while not self.acceptQueue.empty():
            
            print "adding socket to active client"
            sock = self.acceptQueue.get()
            self.activeClients[sock] = sockLib.JsonProtocol(sock)

    def startServer(self):
        """
        starts the server by performing 2 tasks:
        1. starting the accept thread (allowing for connections to the server)
        2. starting of the mainThread which handles communication coming in from the main server
        
        to be called when the user is ready to start the server
        """

        print "starting accept thread"
        self.acceptThread = threading.Thread(target = self._acceptConnections)
        self.acceptThread.start()
        
        #this socket is used for notifying the process of new information
        self.interruptSocket = sockLib.JsonProtocol(sockLib.clientSocket(sockLib.gethostname(), port))
        
        print "starting main thread"
        self.mainThread = threading.Thread(target = self.mainLoop)
        self.mainThread.start()

        
    def stopServer(self):
        """
        stops the server:
        sets the running flag to false, down the accept thread by creating a fake connection which causes the while loop to stop
        sends a message via the interrupt socket which causes the main loop to stop
        """
        
        #TODO:consider having the close the active sockets in the active sockets dict
        self.running = False
        
        #stop accept thread
        sock = sockLib.clientSocket(sockLib.gethostname(), self.port)
        sock.close()
        
        self.interruptSocket.sendData("stopping")
        
    def mainLoop(self):
        
        while self.running:

            #bunch of tasks to be handle on each pass of the main loop
            #if the number of tasks here becomes large, can switch this part out into a separate loop
            self._addConnections()
            
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
        

if __name__ == "__main__":

    server = Server(port)
    server.startServer()
    
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