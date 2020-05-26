
import sys, zmq, select, time, socket
from parameters import *
from datetime import datetime
from twilio.rest import Client
from gcloud import storage
import numpy as np
import cv2
import os

# Topic Filters: "10001" - Central Hub | "10002" - Sensors | "10003" - Screenshots | "10004" - Footage

frame_width = 1280
frame_height = 720

#HOUR = 3600 # one hour = 60 minutes = 3600 seconds (time.time() is in seconds)
HOUR = 20
class Fog:
    def __init__(self, emergency_contact = "+19495298086", hub_port = "8000", surv_port = "7000"):
        self.hub_port = hub_port
        self.surv_port = surv_port

        self.hub_addr = HUB_ADDR
        self.surv_addr = SURV_ADDR

        self.text_sent = False
        self.emergency_contact = emergency_contact
        self.text_client = Client("ACfb45069384449efc0a19acb6ea88d359", "0046fd99e4b7e2c5291a48faf8bce35d")

        self._init_net()
        self._init_cloud()
        self._init_hub()
        self._init_footage()

    def _init_net(self):
        self.hub_topic = HUB_TOPIC
        self.screenshot_topic = SCREENSHOT_TOPIC
        self.footage_topic = FOOTAGE_TOPIC

        self.context = zmq.Context()
        self.sub_socket = self.context.socket(zmq.SUB)

        self.sub_socket.connect("%s:%s" % (self.hub_addr, self.hub_port))
        self.sub_socket.connect("%s:%s" % (self.surv_addr, self.surv_port))

        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.hub_topic)
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.screenshot_topic)
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.footage_topic)

        #self.pub_socket.bind("tcp://*:%s" % self.cloud_port)

        self.read_list = [self.sub_socket]
        self.err_list = [self.sub_socket]

    def _init_cloud(self):
        # figure out credentials/auth for client
        self.cloud_client = storage.Client() # options: project, credentials, http
        self.hub_bucket = self.cloud_client.get_bucket('securisys-hub')
        self.image_bucket = self.cloud_client.get_bucket('securisys-image')
        self.footage_bucket = self.cloud_client.get_bucket('securisys-footage')

    def _init_hub(self):
        self.hub_string = ""
        self.first_read = None
        self.hub_dt = datetime.now()

    def _init_footage(self):
        self.frames = []
        self.start = None
        self.footage_dt = datetime.now()
        
        try:
            os.remove("output/video.avi")
        except:
            pass
        self._outVideo = cv2.VideoWriter('output/video.avi', cv2.VideoWriter_fourcc(*'mjpg'), 10, (frame_width, frame_height))

    def _process_hub(self, payload):
        self.minute = payload[0] == '1'
        self.screenshot = payload[1] == '1'
        self.motion = payload[2] == '1'
        self.light = payload[3] == '1'
        self.sound = payload[4] == '1'
        self.gas = payload[5] == '1'
        self.vibration = payload[6] == '1'

        self.hub_string = "Minute: %r | Screen: %r | Motion: %r | Light: %r | Sound: %r | Gas: %r | Vibration: %r\n" % (self.minute, self.screenshot, self.motion, self.light, self.sound, self.gas, self.vibration)
        print(self.hub_string)

    def _send_text(self, message="Emergency! There has been a break-in!"):
        # alert "authorities" of emergency
        self.text_sent = True
        self.text_client.messages.create(to=self.emergency_contact, from_="+19496494383", body=message)

    def _make_file(self):
        # converts string to txt as output/hub.txt
        with open('output/hub.txt', 'w') as f:
            f.write(self.hub_string)

    def _append_file(self):
        with open('output/hub.txt', 'a') as f:
            f.write(self.hub_string)

    def _ship_hub(self):
        # figure out how to push latest reading to the cloud
        blob = self.hub_bucket.blob(self.hub_dt.strftime('%m-%d-%Y_%H-%M-%S_%f.txt'))
        blob.upload_from_filename(filename='output/hub.txt')
        return

    def _handle_hub(self, payload):
        # process the hub reading
        self._process_hub(payload)
        if self.first_read is None:
            self._make_file()
            self.first_read = time.time()
        else:
            self._append_file()

        if self.minute and not self.text_sent:
            self._send_text()

        if not self.minute:
            self.text_sent = False

        if time.time() - self.first_read >= HOUR:
            # push txt file to cloud
            self._ship_hub()
            # re-init hub for new hour
            self._init_hub()

    def _make_image(self, payload):
        # converts image to jpeg as output/image.jpeg
        
        #get the image back into the normal numpy format
        nparr = np.fromstring(bytes(payload), np.uint8)
        #reconstruct the image
        remade_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        #write image to output/image.jpeg
        cv2.imwrite("output/image.jpeg", remade_img)
        return

    def _ship_screenshot(self):
        # figure out how to push screenshot to the cloud
        dtime = datetime.now()
        blob = self.image_bucket.blob(dtime.strftime('%m-%d-%Y_%H-%M-%S_%f.jpeg'))
        blob.upload_from_filename(filename='output/image.jpeg')

    def _handle_screenshot(self, payload):
        self._make_image(payload)
        self._ship_screenshot()

    def _add_video(self, payload):
        # split payload into frames
        nparr = np.fromstring(bytes(payload), np.uint8)
        # reconstruct the image
        remade_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        # add the image to our video frames
        self._outVideo.write(remade_img)
        #self.frames.append(remade_img)

    def _make_video(self):
        # convert self.frames into video at output/video.avi
        frame_width = 1280
        frame_height = 720
        
        
        #for frame in self.frames:
        #    
        #    frame = cv2.resize(frame, (frame_width,frame_height))
        #    outVideo.write(frame)
        self._outVideo.release()
        return

    def _ship_video(self):
        # figure out how to push video to the cloud
        blob = self.footage_bucket.blob(self.footage_dt.strftime('%m-%d-%Y_%H-%M-%S_%f.avi'))
        blob.upload_from_filename(filename='output/video.avi')

    def _handle_footage(self, payload):
        if self.start is None:
            self.start = time.time()
        # split payload into frames
        self._add_video(payload)
        # if it has been an hour: ship video to cloud and erase
        if time.time() - self.start >= HOUR:
            # figure out how to convert frames onto video
            self._make_video()
            # figure out how to push video to the cloud
            self._ship_video()
            # re-init footage for new hour
            self._init_footage()

    def run(self):
        while True:
            try:
                result = self.sub_socket.recv()
                if result:
                    topic = result[0:5].decode("utf-8")
                    if topic == HUB_TOPIC:
                        self._handle_hub(result[5:].decode("utf-8"))
                        print("Result: %s" % result)
                    elif topic == SCREENSHOT_TOPIC:
                        self._handle_screenshot(result[5:])
                    elif topic == FOOTAGE_TOPIC:
                        self._handle_footage(result[5:])
            except zmq.Again as err:
                print(err)
                continue

            #readable, writable, errored = select.select(self.read_list, [], self.err_list)
            '''if len(errored) > 0:
                # handle connection error / re-establish connection
                self.sub_socket = self.context.socket(zmq.SUB)
                self.sub_socket.connect("%s:%s" % (self.hub_addr, self.hub_port))
                self.sub_socket.connect("%s:%s" % (self.surv_addr, self.surv_port))
                self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.hub_topic)
                self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.screenshot_topic)
                self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.footage_topic)
                self.read_list = [self.sub_socket]
                self.err_list = [self.sub_socket]

            for sock in readable:
                try:
                    result = sock.recv(flags=zmq.NOBLOCK)
                    if result:
                        topic = result[0:5]
                        if topic == HUB_TOPIC:
                            self._handle_hub(result[5:])
                        elif topic == SCREENSHOT_TOPIC:
                            self._handle_screenshot(result[5:])
                        elif topic == FOOTAGE_TOPIC:
                            self._handle_footage(result[5:])
                except zmq.Again as err:
                    print(err)
                    continue
            '''


if __name__ == "__main__":
    fog = Fog()
    fog.run()


'''
def send_hub_topic_command(sock, message, log=True):
    """ returns message received """
    response = "I am response"

    if log:
        print('sending: "{}"'.format(message), file=sys.stderr)

    sock.sendto(message.encode('utf8'), 'localhost') # server is gateway device

    # Receive response
    if log:
        print('waiting for response', file=sys.stderr)
        response, _ = sock.recvfrom(4096)
    if log:
        print('received: "{}"'.format(response), file=sys.stderr)

    return response


def send_sensor_topic_command(sock, message, log=True):
    pass


def send_screenshot_topic_command(sock, message, log=True):
    pass


def send_footage_topic_command(sock, message, log=True):
    pass


if __name__ == "__main__":
    # Socket to talk to server
    context = zmq.Context()
    socket = context.socket(zmq.SUB)

    print("Collecting updates from raspberry pis...")
    PORT = 5556
    socket.connect("tcp://localhost:%s" % PORT)

    # Subscribe to zipcode, default is NYC, 10001
    # topicfilter = "10001"
    # socket.setsockopt_string(zmq.SUBSCRIBE, topicfilter)

    while True:
        string = socket.recv()
        topic, messagedata = string.split()
        print(topic)
        print(messagedata)
        if topic == HUB_TOPIC:
            send_hub_topic_command(messagedata)
        elif topic == SENSOR_TOPIC:
            send_sensor_topic_command()
        elif topic == SCREENSHOT_TOPIC:
            pass
        elif topic == FOOTAGE_TOPIC:
            pass
'''