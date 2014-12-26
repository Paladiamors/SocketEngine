'''
Created on Dec 25, 2014

@author: justin

using code concept using poll
'''

import sockLib2
import select
import threading


class BaseServer:
    
    def __init__(self, port):
        
        self.port = port
        self.serverSocket = None
        self.pollObject = select.poll()
        self.interruptProtocol = None
        self.running = True
        self.mainThread = None
        
        #connection mapping related:
        self.fdSocketMap = {}
        self.fdProtocolMap = {}
        
        #the mapping of handlers for use by the server
        self.handlers = {"NOK": None}
    
    def pollGenerator(self):
        while self.running:
            for fd, event in self.pollObject.poll():
                yield fd, event
        
        print "pollGenerator has stopped"
    def acceptConnection(self):
        """
        accepts a new connection 
        """
        
        newConnection, address = self.serverSocket.accept()
        print "accepting new connection", newConnection.fileno()
        self.fdSocketMap[newConnection.fileno()] = newConnection
        self.fdProtocolMap[newConnection.fileno()] = sockLib2.JsonProtocol(newConnection)
        self.pollObject.register(newConnection, select.POLLIN)
        
    def removeConnection(self, fd):
        """
        removes the connection from the server
        """
        
        print "removing connection from the server", fd
        sock = self.fdSocketMap.pop(fd)
        self.fdProtocolMap.pop(fd)
        self.pollObject.unregister(fd)


    def startServer(self):
        
        print "starting server"
        self.serverSocket = sockLib2.serverSocket(self.port)
        
        print "server socket id is", self.serverSocket.fileno()
        self.fdSocketMap[self.serverSocket.fileno()] = self.serverSocket
        self.fdProtocolMap[self.serverSocket.fileno()] = sockLib2.JsonProtocol(self.serverSocket)
        self.pollObject.register(self.serverSocket.fileno(), select.POLLIN)
        self.mainThread = threading.Thread(target = self.mainLoop)
        self.mainThread.start()
        
        self.interruptProtocol = sockLib2.JsonProtocol(sockLib2.clientSocket(sockLib2.gethostname(), self.port))
        
    def stopServer(self):
        """
        sends command to stop the server
        """
        
        print "stopping server"
        self.running = False
        self.serverSocket.close()
        self.interruptProtocol.queueMsg({"msgType": "NOK"})
        self.interruptProtocol.sock.close()
        
    def mainLoop(self):
        
        for fd, event in self.pollGenerator():
            sock = self.fdSocketMap[fd]
            #if the fdet has been closed
            if event & (select.POLLHUP | select.POLLERR | select.POLLNVAL):
                self.removeConnection(fd)
                
            elif sock is self.serverSocket:
                self.acceptConnection()
                
            elif event & select.POLLIN:
                msgs = self.fdProtocolMap[fd].recvData()
                
                if msgs is None:
                    self.removeConnection(fd)
                else:
                    for msg in msgs:
                        print msg
                        if msg.get("msgType", None):
                            handle = self.handlers.get(msg["msgType"], None)
                            if handle:
                                handle(msg)

            elif event & select.POLLOUT:
                print "sending data to client"
                protocol = self.fdProtocolMap[fd]
                protocol.sendData()
                if not protocol.hasDataToSend():
                    self.pollObject.modify(sock, select.POLLIN)
                    
        print "mainLoop has stopped"
    
        
if __name__ == "__main__":
    import client2
    import time
    import random

    port = 12005
    server = BaseServer(port)
    server.startServer()
    
    time.sleep(0.5)
    
    clients = [client2.BaseClient2() for x in range(5)]
    [client.startClient() for client in clients]
    
    [client.connect(sockLib2.gethostname(), port) for client in clients]
    
    for x in range(10):
        client = random.choice(clients)
        client.queueMsg({"msgType": "magic"})
        
    [client.stopClient() for client in clients]
    
    time.sleep(0.1)
    server.stopServer()