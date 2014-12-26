'''
Created on Dec 26, 2014

@author: justin
'''

import os
import select

r,w = os.pipe()

rPipe = os.fdopen(r)
wPipe = os.fdopen(w,"w")

print "writing to write pipe"
wPipe.write("this is a test\n\n\n\n")
wPipe.flush()
print "reading from read pipe"

pollObject = select.poll()
pollObject.register(rPipe, select.POLLIN)

print "polling"

while True:
    for fd, event in pollObject.poll():
        print "after poll"
        print rPipe.readline()
