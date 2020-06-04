
import sys, zmq, select, time, socket
from parameters import *
from datetime import datetime
from twilio.rest import Client
from gcloud import storage
import numpy as np
import cv2
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import sys

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

        self.hub_timer = time.time()

        self.text_sent = False
        self.conn_fail = False
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
        if self.text_sent and not self.minute and not self.conn_fail:
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
            
    def _decrypt_payload(self, payload):
        return Fernet(NET_KEY).decrypt(payload)

    def run(self):
        while True:
            print("Time Since Last Hub: %f" % (time.time() - self.hub_timer))
            if time.time() - self.hub_timer > 60:
                self.conn_fail = True
                if not self.text_sent:
                    self._send_text("Emergency! Lost Communication with Central Hub!")
                self.hub_timer = time.time()
            try:
                result = self.sub_socket.recv(flags=zmq.NOBLOCK)
                if result:
                    topic = result[0:5].decode("utf-8")
                    if topic == HUB_TOPIC:
                        self._handle_hub(self._decrypt_payload(result[5:]).decode("utf-8"))
                    elif topic == SCREENSHOT_TOPIC:
                        self._handle_screenshot(self._decrypt_payload(result[5:]))
                    elif topic == FOOTAGE_TOPIC:
                        self._handle_footage(self._decrypt_payload(result[5:]))
                    elif topic == CONNECT_HUB_TOPIC:
                        self.hub_timer = time.time()
                        if self.conn_fail and self.text_sent:
                            self.text_sent = False
                        self.conn_fail = False
            except zmq.Again as err:
                print(err)
            except:
                print("Reconnecting Sockets")
                print(err)
                self.sub_socket = self.context.socket(zmq.SUB)

                self.sub_socket.connect("%s:%s" % (self.hub_addr, self.hub_port))
                self.sub_socket.connect("%s:%s" % (self.surv_addr, self.surv_port))

                self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.hub_topic)
                self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.screenshot_topic)
                self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.footage_topic)
                self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, CONNECT_HUB_TOPIC)


if __name__ == "__main__":
    fog = Fog()
    fog.run()