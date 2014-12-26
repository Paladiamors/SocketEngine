'''
Created on Dec 23, 2014

@author: justin

Modified version of the client to use the select.poll system
'''

import sockLib2
import select
import os
import threading
import time

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
        self.sock = sockLib2.clientSocket(self.host, self.port)
        self.protocol = sockLib2.JsonProtocol(self.sock)


    def disconnect(self):
        """
        disconnects from the server
        """
        
        self.sock.close()
        self.protocol = None
        

class BaseClient2:
    """
    new version of the client that uses the poll system to manage reading and writing of data to connections
    This version of the client can handle multiple clients
    Note we use pipes in this case as an interrupt system (rather hacky since we have no server socket for management of communication
    """
    def __init__(self):
        
        self.fdSocketMap = {} #mapping of fd to sockets
        self.fdProtocolMap = {} #mapping of fd to protocols
        
        self.pollObject = select.poll()
        self.connectionId = 1
    
        self.interruptRPipe = None
        self.interruptWPipe = None
        
        self.running = True
    
    def connect(self, host, port):
        """
        creates a connection to a host
        """
        
        print "connecting to", host, port
        sock = sockLib2.clientSocket(host, port)
        self.fdSocketMap[sock.fileno()] = sock
        
        #probably can generalize the protocol to something else... but use this for now
        self.fdProtocolMap[sock.fileno()] = sockLib2.JsonProtocol(sock)
        
        self.pollObject.register(sock.fileno(), select.POLLIN)
    
        
    def removeConnection(self, fd):
        """
        fd = is the id of the socket to be disconnected
        
        returns true if the socket has been removed
        returns false if the socket has not been removed
        """

        print "removing connection from the server", fd
       
        if fd in self.fdSocketMap:
            sock = self.fdSocketMap.pop(fd)
            self.fdProtocolMap.pop(fd)
            sock.close()
            return True
        
        else:
            return False
    
    def getConnections(self):
        """
        returns the fd and the peer name information from the connected sockets 
        """
        return [[fd, sock.getpeername()] for fd, sock in self.fdSocketMap.items()]
    
    def pollGenerator(self):
        while self.running:
            for fd, event in self.pollObject.poll():
                yield fd, event
        
        print "pollGenerator has stopped"
        
    def mainLoop(self):
                
        for fd, event in self.pollGenerator():
            sock = self.fdSocketMap[fd]
            #if the socket has been closed
            if event & (select.POLLHUP | select.POLLERR | select.POLLNVAL):
                self.removeConnection(fd)
                
            elif event & select.POLLIN:
                
                if sock is not self.interruptRPipe:
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
                
                else:
                    #we agree that we only send a new line character to interrupt the mainloop
                    self.interruptRPipe.readline()
            
            elif event & select.POLLOUT:
                
                protocol = self.fdProtocolMap[fd]
                protocol.sendData()
                if not protocol.hasDataToSend():
                    self.pollObject.modify(sock, select.POLLIN)
                
        print "main loop stopped"

    def startClient(self):
        
        print "starting client"
        r,w = os.pipe()
        
        self.interruptRPipe = os.fdopen(r)
        self.interruptWPipe = os.fdopen(w, "w")
        
        #note that this pipe should never be used for reading, will hang the client
        self.fdSocketMap[r] = self.interruptRPipe
        self.fdProtocolMap[r] = sockLib2.JsonProtocol(self.interruptRPipe)
        self.pollObject.register(self.interruptRPipe, select.POLLIN)
        
        self.mainThread = threading.Thread(target = self.mainLoop)
        self.mainThread.start()
        
    def stopClient(self):
        
        print "stopping client"
        self.running = False
        self.interruptWPipe.write("\n")
        self.interruptWPipe.flush()
        
        #sleep is needed here so the main loop has time to shut down after sending this msg
        time.sleep(0.01)
        
        for fd in self.fdSocketMap.keys():
            self.removeConnection(fd)
        
    def queueMsg(self, msg, fd = None):
        """
        msg = the msg to send
        fd = the file descriptor to send to, optional, if there is only one connection then sends the msg
        """
        
        if not fd:
            fds = self.fdSocketMap.keys()
            fds.pop(fds.index(self.interruptRPipe.fileno()))
            if len(fds) == 1:
                fd = fds[0]
                
            else:
                raise("Either no connection is available or there are multiple connections that the msg can be sent to")
            
        protocol = self.fdProtocolMap[fd]
        protocol.queueMsg(msg)
        print "sending fd, msg", fd, msg
        self.pollObject.modify(fd, select.POLLOUT)
            
        
        
        