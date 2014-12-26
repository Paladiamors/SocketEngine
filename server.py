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
from client import BaseClient

port = 14003

class BaseServer:
    """
    The base server will have a some handlers registered to the system
    Additional functionality of the server can be added by subclassing the server class and registering the functionality to the server
    state information and handling of that state information can be handled by the addition of modules to the class
    
    3 main threads will run for this server:
    1. an accept thread that handles all incoming connections
    2. a main loop thread to handle processing of all msgs
    3. a send thread that handles sending of msgs to clients
    """
    def __init__(self, port  = 12000):
    
        self.port = port
        self.socketProtocolMap = {} #dict of socket:protocol objects, for use by select
        self.protocolIdMap = {} #dict mapping protocols to ids
        self.idProtocolMap = {} #dict containing mapping of ids to protocols
        self.socketIdCounter = 1
        
        self.acceptQueue = Queue.Queue()
        self.serverSocket = sockLib.serverSocket(port)
        self.interruptSocket = None
        self.running = True
        self.handlers = {"NOP": None} #used for handling msgs
        
        self.sendQueue = Queue.Queue() #the queue used to send the data to the clients (stored as protocol, msg) pairs

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
                self.interruptSocket.sendData({"msg": "NOP"})
    
        print "server no longer accepting connections"
        
    def _addConnections(self):
        """
        called in the mainLoop to add new sockets to the list of activeConnections
        """
        while not self.acceptQueue.empty():
            
            print "adding socket to active client"
            sock = self.acceptQueue.get()
            protocol = sockLib.JsonProtocol(sock)
            self.socketProtocolMap[sock] = protocol
            self.protocolIdMap[protocol] = self.socketIdCounter
            self.idProtocolMap[self.socketIdCounter] = protocol
            self.socketIdCounter += 1
    
    def _removeConnection(self, sock):
        """
        when a socket has disconnected have it removed
        """
        
        protocol = self.socketProtocolMap.pop(sock)
        protocolId = self.protocolIdMap.pop(protocol)
        self.idProtocolMap.pop(protocolId)
        
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
        
        self.interruptSocket.sendData({"msg": "NOP"})
    
    def handleMsg(self, msg):
        """
        generic function used for handling of msgs
        """
        try:
            handler = self.handlers.get(msg["msg"], None)
            if handler:
                handler(msg)
        except:
            print "processing of msg failed", msg
            
            
    def mainLoop(self):
        """
        the main loop for processing incoming messages
        """
        while self.running:

            #bunch of tasks to be handle on each pass of the main loop
            #if the number of tasks here becomes large, can switch this part out into a separate loop
            self._addConnections()
            
            if not self.socketProtocolMap.keys():
                time.sleep(0.1)
            else:
                r,w,e  = select.select(self.socketProtocolMap.keys(), [], [])
                
                for sock in r:
                    data = self.socketProtocolMap[sock].recvData()
                
                    if data is None:
                        print "client has disconnected"
                        self._removeConnection(sock)
                    elif data:
                        #there is some data for processing
                        map(self.handleMsg, data)
                    else:
                        #no data for processing
                        pass

        print "main loop stopping"
    
    
    #### Define msg handlers here:
    
if __name__ == "__main__":

    server = BaseServer(port)
    server.startServer()
    
    time.sleep(0.5)
    clients = [sockLib.JsonProtocol(sockLib.clientSocket(sockLib.gethostname(), port)) for x in range(5)]
    
    time.sleep(0.1)
    for x in range(10):
        client = random.choice(clients)
        client.sendData({"msg": "magic"})

    for client in clients:
        client.sock.close()
        
    time.sleep(0.1)
    server.stopServer()