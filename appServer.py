'''
Created on Dec 24, 2014

@author: justin
'''
import sockLib
import server

port = 12000
class PubSub:
    
    def __init__(self, host, port):
        pass
        
        
    def subscribe(self, topic):
        """
        send a subscription message to subscribe to a topic
        """
        
        self.protocol.sendData({"msg":"subscribe", "topic": topic})
        
    def unsubscribe(self, topic):
        """
        sends a message to unsubscribe from a topic
        """
        
        self.protocol.sendData({"msg": "unsub", "topic": topic})
        
    def publish(self, msg):
        """
        publishes a msg to the server
        """
        
        self.protocol.sendData


class Server(server.BaseServer):
    
    def __init__(self, port):
        
        server.BaseServer.__init__(self, port)
        
        
        
