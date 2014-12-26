'''
Created on Feb 24, 2014

for this library, we make the assumption that we know the length of the msg when sending
(not really for streaming data when the content is not known)

new version to be used with select.poll
Makes an update to the sendData function --> the server will register the socket for sending and do the unregister when there is no msgs in the buffer
'''

import json
import socket

gethostname = socket.gethostname 
SHUT_RD = socket.SHUT_RD
SHUT_WR = socket.SHUT_WR
SHUT_RDWR = socket.SHUT_RDWR


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
        self.msgBuffer = [] #a buffer of msgs
        self.sendBuffer = "" #a buffer with the current msg for sending
        self.closed = False
        self.readHeader = True
        self.msgSize = 0
        self.index = 0 #the index of upto where the msg has been sent
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


    def queueMsg(self, msg):
        """
        given a msg, appends the data to the buffer
        """
        self.msgBuffer.append(msg)
    
    def hasDataToSend(self):
        """
        a check to determine if this connection has data to send to the client
        if there are msgs in the msg buffer or if there are incomplete msgs, then return true
        else return false
        """
        
        if self.msgBuffer or self.index < self.msgSize:
            return True
        else:
            return False

    
    def sendData(self):
        """
        this function takes out data from the msg buffer and places it into the send buffer --> this is read and sent out to the client
        using poll, when the socket is available for writing, it will send out more data to the client
        
        returns the number of bytes sent
        """


        #if there is no msg in the buffer for sending, loads it and prepares it for sending
        if self.msgBuffer and self.index == 0:
            #converts the msg in to the send buffer, calculates the msg size, adds that into the header
            #adds the size of the header into the msg size
            self.sendBuffer = json.dumps(self.msgBuffer.pop())
            self.msgSize = len(self.sendBuffer)
            qbyte = self._int2Qbyte(self.msgSize)
            data = "".join([qbyte, self.sendBuffer])
            self.msgSize += 4 #for adding the qbyte into the msg 
        
        #performs sending of the msg
        if self.index < self.msgSize:
            sent = self.sock.send(data[self.index:])
            self.index += sent
            if sent == 0:
                raise Exception("Socket was closed during sending")
        
        #sending is complete, reset the state to the inital state
        #note: we don't use a while loop here to send msgs because that can cause this process to block
        if self.index == self.msgSize:
            self.sendBuffer = ''
            self.index = 0
            self.msgSize = 0

        return sent
    
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
    
