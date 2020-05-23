import sys, zmq, select, time, socket
from datetime import datetime
from twilio.rest import Client

# Topic Filters: "10001" - Central Hub | "10002" - Sensors | "10003" - Screenshots | "10004" - Footage
HUB_TOPIC = "10001"
SENSOR_TOPIC = "10002"
SCREENSHOT_TOPIC = "10003"
FOOTAGE_TOPIC = "10004"

DEVICE_ID = ""

HOUR = 3600 # one hour = 60 minutes = 3600 seconds (time.time() is in seconds)

class Fog:
    def __init__(self, emergency_contact = "+19495298086", hub_port = "5000", surv_port = "7000", cloud_port = "10000", hub_addr = "tcp://localhost", surv_addr = "tcp://localhost"):
        self.hub_port = hub_port
        self.surv_port = surv_port
        self.cloud_port = cloud_port

        self.hub_addr = hub_addr
        self.surv_addr = surv_addr

        self.text_sent = False
        self.emergency_contact = emergency_contact
        self.client = Client("ACfb45069384449efc0a19acb6ea88d359", "0046fd99e4b7e2c5291a48faf8bce35d")

        self._init_net()
        self._init_footage()

    def _init_net(self):
        self.hub_topic = HUB_TOPIC
        self.screenshot_topic = SCREENSHOT_TOPIC
        self.footage_topic = FOOTAGE_TOPIC

        self.context = zmq.Context()
        self.sub_socket = self.context.socket(zmq.SUB)
        self.pub_socket = self.context.socket(zmq.PUB)

        self.sub_socket.connect("%s:%s" % (self.hub_addr, self.hub_port))
        self.sub_socket.connect("%s:%s" % (self.surv_addr, self.surv_port))

        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.hub_topic)
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.screenshot_topic)
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.footage_topic)

        self.pub_socket.bind("tcp://*:%s" % self.cloud_port)

        self.read_list = [self.sub_socket]
        self.write_list = [self.pub_socket]
        self.err_list = [self.sub_socket, self.pub_socket]

    def _init_footage(self):
        self.frames = []
        self.start = None
        self.datetime = datetime.now()

    def _make_message(self, device_id, action, data=''):
        if data:
            return '{{ "device" : "%s", "action":"%s", "data" : "%s" }}' % (device_id, action, data)
        else:
            return '{{ "device" : "%s", "action":"%s"}}' % (device_id, action)

    def _send_command(self, message, log=True):
        if log:
            print('sending: "{}"'.format(message), file=sys.stderr)
        self.pub_socket.send(message.encode('utf8'))

    def _process_hub(self, payload):
        self.minute = payload[0] == '1'
        self.screenshot = payload[1] == '1'
        self.motion = payload[2] == '1'
        self.light = payload[3] == '1'
        self.sound = payload[4] == '1'
        self.gas = payload[5] == '1'
        self.vibration = payload[6] == '1'

    def _send_text(self, message="Emergency! There has been a break-in!"):
        # alert "authorities" of emergency
        self.client.messages.create(to=self.emergency_contact, from_="+19496494383", body=message)

    def _ship_hub(self):
        # figure out how to push latest reading to the cloud
        message = self._make_message(DEVICE_ID, 'hub', 'minute=%b, screenshot=%b, motion=%b, light=%b, sound=%b, gas=%b, vibration=%b' % (self.minute, self.screenshot, self.motion, self.light, self.sound, self.gas, self.vibration))
        self._send_command(message, False)

    def _handle_hub(self, payload):
        self._process_hub(payload)
        if self.minute and not self.text_sent:
            self._send_text()
        if not self.minute:
            self.text_sent = False
        self._ship_hub()

    def _ship_screenshot(self, payload):
        # figure out how to push screenshot to the cloud
        message = self._make_message(DEVICE_ID, 'image', 'payload=%s' % payload)
        self._send_command(message, False)

    def _split_video(self, payload):
        # split payload into frames
        frames = payload.split("\n")
        for frame in frames:
            # convert frame into image
            frame = frame # convert frame here
            # append image to self.frames
            self.frames.append(frame)

    def _make_video(self):
        # convert self.frames into video
        return

    def _ship_video(self):
        # figure out how to push video to the cloud
        message = self._make_message(DEVICE_ID, 'video')
        self._send_command(message, False)

    def _add_footage(self, payload):
        if self.start is None:
            self.start = time.time()
        # split payload into frames
        self._split_video(payload)
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
            readable, writable, errored = select.select(self.read_list, self.write_list, self.err_list)

            for sock in errored:
                # handle connection error / re-establish connection
                continue

            for sock in readable:
                try:
                    result = sock.recv(flags=zmq.NOBLOCK)
                    topic = result[0:5]
                    if topic == HUB_TOPIC:
                        self._handle_hub(result[5:])
                    elif topic == SCREENSHOT_TOPIC:
                        self._ship_screenshot(result[5:])
                    elif topic == FOOTAGE_TOPIC:
                        self._add_footage(result[5:])
                except zmq.Again as err:
                    print(err)
                    continue

            for sock in writable:
                # dead code for now.
                continue


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