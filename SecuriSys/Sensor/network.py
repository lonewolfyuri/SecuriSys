import zmq
import random
import sys
import time
from sensor import Sensor
from parameters import *
from cryptography.fernet import Fernet

def init():
    sen = Sensor()
    topic = "10002"
    port = "6000"
    if len(sys.argv) > 1:
        port = sys.argv[1]
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:%s" % port)
    return sen, topic, socket

def run(sen, topic, socket):
    while True:
        next()
        time.sleep(0.1)

def _encrypt_payload(self, payload):
    return Fernet(NET_KEY).encrypt(payload)

def next(sen, topic, socket):
    senVals = sen.get_sample()
    messagedata = binarySensor(senVals);
    print(topic + messagedata)
    socket.send_string("%s%s" % (topic, _encrypt_payload(messagedata)))

def binarySensor(senVals):
    vals = ""
    for x in senVals:
        vals += str(x);
    return vals;

sen, topic, socket = init()
run(sen, topic, socket)
