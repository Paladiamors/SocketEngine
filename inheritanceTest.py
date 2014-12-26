'''
Created on Dec 26, 2014

@author: justin
'''


class mixA:
    
    def __init__(self):        
        self.register()
    
    def register(self):
        
        self.funcRegister.append(self.greet)
    
    def greet(self):
        print "mixA"
        
class mixB:
    
    def __init__(self):
        self.register()
    
    def register(self):
        self.funcRegister.append(self.greet)
        
    def greet(self):
        print "mixB"
        

class Main(mixA, mixB):
    
    def __init__(self):
        
        self.funcRegister = []
        for base in Main.__bases__:
            base.__init__(self)
        
    def runRegister(self):
        
        for func in self.funcRegister:
            func(self)
            
            
if __name__ == "__main__":
    
    main = Main()
    main.runRegister()
    
    print Main.__bases__