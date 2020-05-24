import zmq
import random
import sys
import time
from sensor import Sensor

HUB_ADDR = "tcp://128.195.64.140"
SENS_ADDR = "tcp://128.195.79.249"
SURV_ADDR = "tcp://128.200.205.245"
FOG_ADDR = "tcp://128.195.77.175"

port = "6000"
if len(sys.argv) > 1:
    port = sys.argv[1]

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:%s" % port)

sen = Sensor()
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
    time.sleep(0.5)
