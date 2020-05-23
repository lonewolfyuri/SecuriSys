import sys, zmq, socket

# Topic Filters: "10001" - Central Hub | "10002" - Sensors | "10003" - Screenshots | "10004" - Footage
HUB_TOPIC = "10001"
SENSOR_TOPIC = "10002"
SCREENSHOT_TOPIC = "10003"
FOOTAGE_TOPIC = "10004"


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