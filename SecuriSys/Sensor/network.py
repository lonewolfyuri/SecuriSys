import zmq
import random
import sys
import time
import sensor

port = "6000"
if len(sys.argv) > 1:
    port =  sys.argv[1]
    int(port)

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:%s" % port)

sen = sensor.Sensor()
topic = "10002"


def binarySensor(senVals):
    vals = ""
    for x in senVals:
        vals += str(x);
    return vals;

while True:
    senVals = sen.get_sample()
    messagedata = binarySensor(senVals);
    print (topic+messagedata)
    socket.send_string((topic+messagedata))
    time.sleep(1)
