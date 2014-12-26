'''
Created on Dec 24, 2014

@author: justin

creating a module for a simple publish-subscribe system
'''
import sockLib2
import server2
import client2

namespace = "pubsub"


class PubSubClientMixin:
    
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


class PubSubServerMixin:
    
    def __init__(self, host, port):
        
        self.fdTopicMap = {} #mapping of fd to topics --> used for knowing what fd is subscribed to what
        self.topicFdMap = {} #mapping of topics to fd --> used to know how to route msgs to fds
    
    def register(self):
        
        callbacks = {"%s:publish" % namespace: self.onPublish,
                     "%s:subscribe" % namespace: self.onSubscribe,
                     "%s:unsubscribe" % namespace: self.onUnsubscribe}
        
        for k,v in callbacks:
            self.handlers[k] = v
        
    def onPublish(self, msg):
        """
        a client or some source publishes some msg on to the platform
        the information is then sent to the subscribers
        
        Note: Handle the case when they abruptly disconnect
        """
        
        if msg["topic"] in self.topicFdMap:
            for fd in self.topicFdMap[msg["topic"]]:
                self.sendMsg(fd, msg)
            
    
    def onSubscribe(self, msg):
        """
        a client subscribes to some topic, 
        the msg comes in and then it is routed to the connected clients
        """
        
        #mapping of topics to fds
        if msg["topic"] not in self.topicFdMap:
            self.topicFdMap[msg["topic"]] = [msg["fd"]]
        else:
            self.topicFdMap[msg["topic"]].append(msg["fd"])
        
        #mapping of fds to topic
        if msg["fd"] not in self.fdTopicMap:
            self.fdTopicMap["fd"] = [msg["topic"]]
        else:
            self.fdTopicMap["fd"].append(msg["topic"])
    
    def onUnsubscribe(self, msg):
        """
        a client unsubscribes from a topic
        """
        
        #removes the mapping of fd from the mapped topic list
        topicFdList = self.topicFdMap[msg["topic"]]
        topicFdList.pop(topicFdList.index[msg["fd"]])
        
        if not topicFdList: #removes the topic from the topicFdList
            self.topicFdMap.pop(msg["topic"])

        #removes the mapping of the topic to the fd        
        fdTopicList = self.fdTopicMap[msg["fd"]]
        fdTopicList.pop(fdTopicList.index(msg["topic"]))
        
        if not fdTopicList: #the file descriptor is not subscribed to anything
            self.fdTopicMap.pop(msg["fd"])
        
class Server(server2.BaseServer):
    
    def __init__(self, port):
        
        server2.BaseServer.__init__(self, port)
        
        
        
