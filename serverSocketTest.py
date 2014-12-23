'''
Created on Dec 23, 2014

@author: justin
'''

import sockLib
import select
import threading
import time



def serverAccept():
        
    serverSocket = sockLib.serverSocket(10500)
    socket, address = serverSocket.accept()
    print "connection detected"
    
    r,w,e = select.select([socket],[] ,[])
    
    for sock in r:
        data = sock.recv(1024)
        print "number of bytes in retrived data is", len(data)
        
        if len(data) == 0:
            print "this socket has closed"
        
    
        
def clientConnect():
    
    clientSocket = sockLib.clientSocket(sockLib.gethostname(), 10500)
    print "client has connected"
    clientSocket.close()
    print "closing connection"
    

if __name__ == "__main__":
    
    print "starting server socket"
    acceptThread = threading.Thread(target = serverAccept)
    acceptThread.start()
    
    time.sleep(0.5)
    
    print "creating client connection"
    clientConnect()
    