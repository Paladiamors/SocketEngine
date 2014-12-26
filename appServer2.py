'''
Created on Dec 24, 2014

@author: justin

creating a module for a simple publish-subscribe system
'''
import sockLib2
import server2
import client2

namespace = "pubsub"


class PubSubClientModule:
    """
    the parent object is the client object that provides the basic functionality for the module    
    """
    
    namespace = namespace
    
    def __init__(self, parent):
        self.parent = parent
        

    def register(self):
        """
        registers the handlers to the client
        """
        callbacks = {"%s:record" % namespace : self.onRecord}

        for k,v in callbacks.items():
            self.parent.handlers[k] = v
            
    def subscribe(self, topic):
        """
        send a subscription message to subscribe to a topic
        """
        
        self.parent.protocol.sendData({"msgType":"%s:subscribe" % namespace, "topic": topic})
        
    def unsubscribe(self, topic):
        """
        sends a message to unsubscribe from a topic
        """
        
        self.parent.protocol.sendData({"msgType": "%s:unsubscribe" % namespace, "topic": topic})
        
    def publish(self, topic, msg):
        """
        publishes a msg with a topic to the server
        """
        
        msg["msgType"] = "%s:publish" % namespace
        msg["topic"] = topic
        self.parent.protocol.sendData(msg)

    def onRecord(self, msg):
        """
        the msg that comes back --> does this need to be overridden? or do we create some kind of queue system 
        where the msgs can be handled? something to think about ...  
        """
        
        pass
        

class PubSubServerModule:
    """
    the module will handle 3 different kinds of msgs
    
    publish, subscribe and unsubscribe
    
    if there is a publication, the information will come out as a record Type which is handled by the clients....
    not sure if dealing with a client getting it's own published message back makes sense in this sense, but something to think about later on
    """
    
    namespace = namespace
    
    def __init__(self, parent):
        
        self.parent = parent
        self.fdTopicMap = {} #mapping of fd to topics --> used for knowing what fd is subscribed to what
        self.topicFdMap = {} #mapping of topics to fd --> used to know how to route msgs to fds
    
    def register(self):
        
        callbacks = {"%s:publish" % namespace: self.onPublish,
                     "%s:subscribe" % namespace: self.onSubscribe,
                     "%s:unsubscribe" % namespace: self.onUnsubscribe}
        
        for k,v in callbacks.items():
            self.parent.handlers[k] = v
    
        self.parent.removeConnectionHooks.append(self.disconnectHook)
        
    def disconnectHook(self, fd):
        """
        fd = of the lost connection
        removes the list of subscribed topics from fdTopicMap
        removes the fd from the dict of topics
        """
        
        if fd in self.fdTopicMap:
            self.fdTopicMap.pop(fd) #pops the file descriptor from the topic Map
            
        for topic in self.topicFdMap:
            if fd in topic:
                topic.pop(topic.index(fd)) #pops the fd from the list of subscribed file descriptors
                
    
    def onPublish(self, msg):
        """
        a client or some source publishes some msg on to the platform
        the information is then sent to the subscribers
        
        Note: Handle the case when they abruptly disconnect
        """
        
        print "publish msg", msg
        msg["msgType"] = "%s:record" % namespace
        if msg["topic"] in self.topicFdMap:
            for fd in self.topicFdMap[msg["topic"]]:
                self.parent.sendMsg(fd, msg)
            
    
    def onSubscribe(self, msg):
        """
        a client subscribes to some topic, 
        the msg comes in and then it is routed to the connected clients
        """
        
        #mapping of topics to fds
        print "subscription msg", msg
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
        print "unsubscribe msg", msg
        topicFdList = self.topicFdMap[msg["topic"]]
        topicFdList.pop(topicFdList.index[msg["fd"]])
        
        if not topicFdList: #removes the topic from the topicFdList
            self.topicFdMap.pop(msg["topic"])

        #removes the mapping of the topic to the fd        
        fdTopicList = self.fdTopicMap[msg["fd"]]
        fdTopicList.pop(fdTopicList.index(msg["topic"]))
        
        if not fdTopicList: #the file descriptor is not subscribed to anything
            self.fdTopicMap.pop(msg["fd"])
        


if __name__ == "__main__":
    
    import server2
    import time
    
    port = 12001
    server = server2.BaseServer(port, PubSubServerModule)    
    
    server.startServer()
    client = client2.BaseClient(PubSubClientModule)
    client.startClient()
    client.connect(sockLib2.gethostname(), port)
    
    time.sleep(0.5)
    client.stopClient()
    server.stopServer()

    
    print "test"
    