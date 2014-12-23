'''
Created on Feb 24, 2014

for this library, we make the assumption that we know the length of the msg when sending
(not really for streaming data when the content is not known)
'''

import json
import socket

gethostname = socket.gethostname 

class JsonProtocol:
    """
    A protocol to send and receive JSON data
    this protocol is to provide a non blocking interface for recieving msgs
    provides a simple interface to send msgs (which is blocking)
    """

    maxRead = 10000
     
    def __init__(self, sock):
        self.sock = sock
        self.recvBuffer = "" #string for storage of incoming msgs
        self.closed = False
        self.readHeader = True
        self.msgSize = 0
        self.index = 0
        self.msgList = []

    def _int2Qbyte(self, value):
        """
        value = integer
        converts the value into a 4 byte string
        """
        
        chars = []
        for x in range(4):
            divisor = 256**(3-x)
            quotient = value/256**(3-x)
            
            chars.append(chr(quotient))
            value = value % divisor
            
        return "".join(chars)
    
    def _qbyte2int(self, qbyte):
        """
        returns a 4 character string into an int 
        """
        
        values = [ord(char)*256**(3-x) for x,char in enumerate(qbyte)]
        return sum(values)

    def sendData(self, data):
        """
        data = data structure to convert into json and sends it to the other process
        we accept that this can block (assume that this is not being used in a select)
        
        returns the number of bytes sent
        """

        #converts the data into json
        data = json.dumps(data)
        
        bytesSent = 0
        msgSize = len(data)
        qbyte = self._int2Qbyte(msgSize)
        data = "".join([qbyte, data])
        msgSize += 4 #for adding the qbyte into the msg        
        
        index = 0
        while bytesSent < msgSize:
            sent = self.sock.send(data[index:index+(msgSize-index)])
            if sent == 0:
                raise Exception("Socket was closed during sending")
            
            bytesSent += sent

        return bytesSent
    
    def recvData(self):
        """
        the receive data function
        when a msg is complete, returns it, this function is to be used with a select
        """
        
        data = self.sock.recv(self.maxRead)

        if not data:
            #no more data, returns None if the connection has been closed
            self.closed = True
            return None
        else:
            self.readBytes = len(data)
            self.recvBuffer = "".join([self.recvBuffer, data])

        run = True
        
        while run:
        
            if self.readHeader:
                if len(self.recvBuffer) - self.index >= 4:
                    qbyte = self.recvBuffer[self.index:self.index+4]
                    self.msgSize = self._qbyte2int(qbyte)
                    self.readHeader = False
                    self.index += 4
                else:
                    run = False #stop the loop
                    
                    
            if not self.readHeader:
                if len(self.recvBuffer) - self.index >= self.msgSize:
                    msg = self.recvBuffer[self.index:self.index + self.msgSize]
                    self.msgList.append(json.loads(msg))
                    
                    self.readHeader = True
                    self.index += self.msgSize
                    self.msgSize = 0                    
        
                else:
                    run = False #stop the loop
                    
        #outside the while loop, perform cleaning
        if self.index: #if the index is non-zero
            self.recvBuffer = self.recvBuffer[self.index:]
            self.index = 0
  
        if self.msgList:
            #empty the msg list and return the results held
            result = self.msgList
            self.msgList = []
            return result
        else:
            #returns an empty list (no results)
            return [] 
            
def int2Qbyte(value):
    """
    value = integer
    converts the value into a 4 byte string
    """
    
    chars = []
    for x in range(4):
        divisor = 256**(3-x)
        quotient = value/256**(3-x)
        
        chars.append(chr(quotient))
        value = value % divisor
        
    return "".join(chars)

def qbyte2int(qbyte):
    """
    returns a 4 character string into an int 
    """
    
    values = [ord(char)*256**(3-x) for x,char in enumerate(qbyte)]
    return sum(values)

def clientSocket(address, port):
    """
    address = creates a client socket to connect to some server
    port = port number to connect to
    """
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.connect((address, port))
    
    return clientsocket

def serverSocket(port,backlog = 5):
    """
    creates a listening socket for the server
    port = port number to listen to
    backlog = number of backlog sockets
    
    """
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind((socket.gethostname(), port))
    serversocket.listen(backlog)
    
    return serversocket

def sendData(socket,data):
    """
    data will be some data structure that will be converted into json
    """
    dataString = json.dumps(data)
    l = int2Qbyte(len(dataString))
    
    socket.send( l + dataString)
    
def recvData(socket):
    """
    data will be some data structure that is loaded from the socket and converted back from json
    """
    
    firstRead = socket.recv(1024)
    dataLength = qbyte2int(firstRead[:4])
    data = firstRead[4:]
    
    readBytes = len(data)
    
    while readBytes < dataLength:
        newData = socket.recv(1024)
        readBytes += len(newData)
        data = "".join((data,newData))
        
    return json.loads(data)
    
if __name__ == "__main__":
    value = 29132132
    qbyte = int2Qbyte(value)
    print qbyte
    result = qbyte2int(qbyte)
    print result
    
