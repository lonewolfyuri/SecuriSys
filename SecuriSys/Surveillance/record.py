#run with the following command:
#python3 record.py


# Import packages
import os
import argparse
import cv2
import numpy as np
import sys
import time
from threading import Thread
import importlib.util
import zmq
import random
import sys
import time
from datetime import datetime

from cryptography.fernet import Fernet
from gcloud import storage
from cryptography import *
from parameters import *

import base64
from os import path

frame_width = 1280
frame_height = 720
port = "7000"

#HOUR = 3600 # one hour = 60 minutes = 3600 seconds (time.time() is in seconds)
HOUR = 20

###for initial construction
outVideo = cv2.VideoWriter('output/video.avi', cv2.VideoWriter_fourcc(*'mjpg'), 10, (1280, 720))


def send_packet(socket, topic, payload):
    packet =bytes(topic, 'utf8') + payload
    socket.send(packet)
    print("sent", topic)
    
def encrypt_bytes(data):
    return Fernet(NET_KEY).encrypt(data)

def package_imgstr(frm):
    img_encode = cv2.imencode('.jpg', frm)[1]
    data_encode = np.array(img_encode)
    return data_encode.tostring()

def run(videostream, interpreter, socket, bucket):
    ndx = 0
    outVideo, start, footage_dt = _init_footage()
    while True:
        next(videostream, interpreter, socket, outVideo)
        if time.time() - start >= HOUR:
            _ship_footage(bucket, footage_dt)
            outVideo, start, footage_dt = _init_footage()
        # Press 'q' to quit
        if cv2.waitKey(1) == ord('q'):
            break
        if ndx > 10:
            ndx = 0
            send_packet(socket, CONNECT_SURV_TOPIC, encrypt_bytes(bytes("KeepMeAliave!", 'utf8')))
            #send_packet(socket, CONNECT_SURV_TOPIC, encrypt_bytes(b'keepaliave'))
        else:
            ndx += 1

def init_client():
    client = storage.Client()  # options: project, credentials, http
    bucket = client.get_bucket('securisys-footage')
    return client, bucket

def handle_person(frame, scores, boxes, i):
    ymin = int(max(1, (boxes[i][0] * imH)))
    xmin = int(max(1, (boxes[i][1] * imW)))
    ymax = int(min(imH, (boxes[i][2] * imH)))
    xmax = int(min(imW, (boxes[i][3] * imW)))

    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (10, 255, 0), 2)

    label = '%s: %d%%' % ("person", int(scores[i] * 100))  # Example: 'person: 72%'
    labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)  # Get font size
    label_ymin = max(ymin, labelSize[1] + 10)  # Make sure not to draw label too close to top of window
    cv2.rectangle(frame, (xmin, label_ymin - labelSize[1] - 10), (xmin + labelSize[0], label_ymin + baseLine - 10), (255, 255, 255), cv2.FILLED)  # Draw white box to put label text in
    cv2.putText(frame, label, (xmin, label_ymin - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)  # Draw label text

    return frame, True

def adjust_gamma(image, gamma=1.0):
	# build a lookup table mapping the pixel values [0, 255] to
	# their adjusted gamma values
	invGamma = 1.0 / gamma
	table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
	# apply gamma correction using the lookup table
	return cv2.LUT(image, table)

def _handle_gamma(frame):
    hour = datetime.now().hour
    if hour < 4 or hour >= 22:
        return adjust_gamma(frame, 2.0)
    elif hour < 5 or hour >= 21:
        return adjust_gamma(frame, 1.66)
    elif hour < 6 or hour >= 20:
        return adjust_gamma(frame, 1.33)
    else:
        return frame

def _get_features(interpreter, output_details):
    # Retrieve detection results
    boxes = interpreter.get_tensor(output_details[0]['index'])[0]  # Bounding box coordinates of detected objects
    classes = interpreter.get_tensor(output_details[1]['index'])[0]  # Class index of detected objects
    scores = interpreter.get_tensor(output_details[2]['index'])[0]  # Confidence of detected objects
    # num = interpreter.get_tensor(output_details[3]['index'])[0]  # Total number of detected objects (inaccurate and not needed)
    return boxes, classes, scores

def _handle_img(frame):
    # Acquire frame and resize to expected shape [1xHxWx3]
    frame = _handle_gamma(frame)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_resized = cv2.resize(frame_rgb, (width, height))
    input_data = np.expand_dims(frame_resized, axis=0)
    return frame, frame_rgb, frame_resized, input_data

def _init_footage():
    try:
        os.remove("output/video.avi")
    except:
        pass

    return cv2.VideoWriter('output/video.avi', cv2.VideoWriter_fourcc(*'mjpg'), 10, (frame_width, frame_height)), time.time(), datetime.now()

def _ship_footage(bucket, footage_dt):
    # figure out how to push video to the cloud
    blob = bucket.blob(footage_dt.strftime('%m-%d-%Y_%H-%M-%S_%f.avi'))
    blob.upload_from_filename(filename='output/video.avi')

def next(videostream, interpreter, socket, outVideo):
    # for frame1 in camera.capture_continuous(rawCapture, format="bgr",use_video_port=True):
    t1 = cv2.getTickCount()

    # Grab frame from video stream
    frame1 = videostream.read()

    # Acquire frame and resize to expected shape [1xHxWx3]
    frame, frame_rgb, frame_resized, input_data = _handle_img(frame1.copy())

    # Normalize pixel values if using a floating model (i.e. if model is non-quantized)
    if floating_model:
        input_data = (np.float32(input_data) - input_mean) / input_std

    # Perform the actual detection by running the model with the image as input
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    boxes, classes, scores = _get_features(interpreter, output_details)

    # Loop over all detections and draw detection box if confidence is above minimum threshold
    # for i in range(len(scores)):
    send_ss_topic = False

    for i in range(len(scores)):  # just loop[ over the person object
        if ((scores[i] > min_conf_threshold) and (scores[i] <= 1.0)):
            # Get bounding box coordinates and draw box
            # Interpreter can return coordinates that are outside of image dimensions, need to force them to be within image using max() and min()
            # Draw label
            object_name = labels[int(classes[i])]  # Look up object name from "labels" array using class index
            # object_name= labels
            if (object_name == "person"):
                frame, send_ss_topic = handle_person(frame, scores, boxes, i)

    # package, encrypt, and publish our packets
    outVideo.write(frame)
    imgStr = package_imgstr(frame)

    payload = encrypt_bytes(imgStr)
    if (send_ss_topic):
        send_packet(socket, SCREENSHOT_TOPIC, payload)
    
    t2 = cv2.getTickCount()
    time1 = (t2 - t1) / freq
    frame_rate_calc = 1 / time1
    # Draw framerate in corner of frame
    cv2.putText(frame, 'FPS: {0:.2f}'.format(frame_rate_calc), (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2, cv2.LINE_AA)

    # All the results have been drawn on the frame, so it's time to display it.
    cv2.imshow('Object detector', frame)

    # Calculate framerate
    


# Define VideoStream class to handle streaming of video from webcam in separate processing thread
# Source - Adrian Rosebrock, PyImageSearch: https://www.pyimagesearch.com/2015/12/28/increasing-raspberry-pi-fps-with-python-and-opencv/
class VideoStream:
    """Camera object that controls video streaming from the Picamera"""
    def __init__(self,resolution=(640,480),framerate=30):
        # Initialize the PiCamera and the camera image stream
        self.stream = cv2.VideoCapture(0)
        ret = self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        ret = self.stream.set(3,resolution[0])
        ret = self.stream.set(4,resolution[1])
            
        # Read first frame from the stream
        (self.grabbed, self.frame) = self.stream.read()

	# Variable to control when the camera is stopped
        self.stopped = False

    def start(self):
	# Start the thread that reads frames from the video stream
        Thread(target=self.update,args=()).start()
        return self

    def update(self):
        # Keep looping indefinitely until the thread is stopped
        while True:
            # If the camera is stopped, stop the thread
            if self.stopped:
                # Close camera resources
                self.stream.release()
                return

            # Otherwise, grab the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
	# Return the most recent frame
        return self.frame

    def stop(self):
	# Indicate that the camera and thread should be stopped
        self.stopped = True

MODEL_NAME = "Sample_TFLite_model"
GRAPH_NAME = 'detect.tflite'
LABELMAP_NAME = 'labelmap.txt'
min_conf_threshold = float(.50)
imW, imH = int(1280), int(720)
use_TPU = True

# Import TensorFlow libraries
# If tflite_runtime is installed, import interpreter from tflite_runtime, else import from regular tensorflow
# If using Coral Edge TPU, import the load_delegate library
pkg = importlib.util.find_spec('tflite_runtime')
if pkg:
    from tflite_runtime.interpreter import Interpreter
    if use_TPU:
        from tflite_runtime.interpreter import load_delegate
else:
    from tensorflow.lite.python.interpreter import Interpreter
    if use_TPU:
        from tensorflow.lite.python.interpreter import load_delegate

# If using Edge TPU, assign filename for Edge TPU model
if use_TPU:
    # If user has specified the name of the .tflite file, use that name, otherwise use default 'edgetpu.tflite'
    if (GRAPH_NAME == 'detect.tflite'):
        GRAPH_NAME = 'edgetpu.tflite'       

# Get path to current working directory
CWD_PATH = os.getcwd()

# Path to .tflite file, which contains the model that is used for object detection
PATH_TO_CKPT = os.path.join(CWD_PATH,MODEL_NAME,GRAPH_NAME)

# Path to label map file
PATH_TO_LABELS = os.path.join(CWD_PATH,MODEL_NAME,LABELMAP_NAME)

# Load the label map
with open(PATH_TO_LABELS, 'r') as f:
    labels = [line.strip() for line in f.readlines()]

# Have to do a weird fix for label map if using the COCO "starter model" from
# https://www.tensorflow.org/lite/models/object_detection/overview
# First label is '???', which has to be removed.
if labels[0] == '???':
    del(labels[0])

# Load the Tensorflow Lite model.
# If using Edge TPU, use special load_delegate argument
if use_TPU:
    interpreter = Interpreter(model_path=PATH_TO_CKPT, experimental_delegates=[load_delegate('libedgetpu.so.1.0')])
    print(PATH_TO_CKPT)
else:
    interpreter = Interpreter(model_path=PATH_TO_CKPT)

interpreter.allocate_tensors()

# Get model details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
height = input_details[0]['shape'][1]
width = input_details[0]['shape'][2]

floating_model = (input_details[0]['dtype'] == np.float32)

input_mean = 127.5
input_std = 127.5

# Initialize frame rate calculation
frame_rate_calc = 1
freq = cv2.getTickFrequency()

# Initialize video stream
videostream = VideoStream(resolution=(imW,imH),framerate=10).start()
time.sleep(1)

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:%s" % port)

client, bucket = init_client()
run(videostream, interpreter, socket, bucket)

# Clean up
cv2.destroyAllWindows()
videostream.stop()
