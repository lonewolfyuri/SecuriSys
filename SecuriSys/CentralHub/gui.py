import guizero as gz
import tkinter as tk
from cryptography.fernet import Fernet
import os, sys, zmq, select, pygame

# self.state values: "init" | "input" | "armed" | "disarmed"

# Topic Filters: "10001" - Centeral Hub | "10002" - Sensors | "10003" - Screenshots | "10004" - Footage
HUB_TOPIC = "10001"
SENSOR_TOPIC = "10002"
SCREENSHOT_TOPIC = "10003"
FOOTAGE_TOPIC = "10004"

w = 800
h = 430
s = 40

class HubGui:
    def __init__(self, sens_port = "6000", surv_port = "7000", fog_port = "8000", sens_addr = "tcp://localhost", surv_addr = "tcp://localhost"):
        self.sens_port = sens_port
        self.surv_port = surv_port
        self.fog_port = fog_port

        self.sens_addr = sens_addr
        self.surv_addr = surv_addr

        self.message = "   Create New Code   " # message to display in gui
        self.key = Fernet.generate_key() # key for passcode enc/dec

        self.failed = 0
        self.alarm = False

        self.encrypt = "" # encrypted code to verify against input code
        self.code = "" # input code to verify aginst encrypted code

        self.state = "" # current state of the system (init, input, armed, or disarmed)
        self.prev_state = "" # previous state of the system

        self.app = gz.App(bg="#171717", title="SecuriSys Central Hub", width=w, height=h) # the guizero app object

        self._init_net()
        self._init_music()
        self._init_app()

    def _init_net(self):
        self.sens_topic = SENSOR_TOPIC
        self.surv_topic = SCREENSHOT_TOPIC

        self.context = zmq.Context()
        self.sub_socket = self.context.socket(zmq.SUB)
        self.pub_socket = self.context.socket(zmq.PUB)

        self.sub_socket.connect("%s:%s" % (self.sens_addr, self.sens_port))
        self.sub_socket.connect("%s:%s" % (self.surv_addr, self.surv_port))

        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.sens_topic)
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.surv_topic)

        self.pub_socket.bind("tcp://*:%s" % self.fog_port)

        self.read_list = [self.sub_socket]
        self.write_list = [self.pub_socket]
        self.err_list = [self.sub_socket, self.pub_socket]

    def _init_music(self):
        pygame.mixer.init()
        pygame.mixer.music.load("resources/alarm.mp3")
        pygame.mixer.music.set_volume(1.0)

    def _init_app(self):
        self.app.set_full_screen()
        #pi dimensions: W - 500 | H - 414
        self._init_state()

        self._init_keyboard()
        self._init_status()
        self._init_hidden()

    def _init_state(self):
        self._change_state("init")

    def _init_keyboard(self):
        self.keyboard_box = gz.Box(self.app, width=int(w / 2), height=h, layout="fill", align="left", border=False)
        self.keyboard_box.text_color = "#171717"
        self.keyboard_box.tk.configure(background="#171717")
        self.keyboard_box.tk.configure(bg="#171717")
        self.keyboard_box.tk.configure(borderwidth=0)
        self.keyboard_box.tk.configure(bd=0)
        self.keyboard_box.tk.configure(highlightthickness=0)
        self.keyboard_box.tk.configure(highlightcolor="#171717")
        self.keyboard_box.tk.configure(highlightbackground="#171717")

        self.key_align_box = gz.Box(self.keyboard_box, width=int(w / 2), height=h, layout="grid", align="right", border=False)
        self.key_align_box.text_color = "#171717"
        self.key_align_box.tk.configure(background="#171717")
        self.key_align_box.tk.configure(bg="#171717")
        self.key_align_box.tk.configure(borderwidth=0)
        self.key_align_box.tk.configure(bd=0)
        self.key_align_box.tk.configure(highlightthickness=0)
        self.key_align_box.tk.configure(highlightcolor="#171717")
        self.key_align_box.tk.configure(highlightbackground="#171717")


        curBtn = gz.PushButton(self.key_align_box, padx=0, pady=0, width=int(w / 7), height=int(h / 4.2), image="resources/key_1_black_smol.gif", command=self._input_1, grid=[0,0])
        curBtn.bg = "#171717"
        curBtn.text_color = "#171717"

        curBtn = gz.PushButton(self.key_align_box, padx=0, pady=0, width=int(w / 7), height=int(h / 4.2), image="resources/key_2_black_smol.gif", command=self._input_2, grid=[1,0])
        curBtn.bg = "#171717"
        curBtn.text_color = "#171717"

        curBtn = gz.PushButton(self.key_align_box, padx=0, pady=0, width=int(w / 7), height=int(h / 4.2), image="resources/key_3_black_smol.gif", command=self._input_3, grid=[2,0])
        curBtn.bg = "#171717"
        curBtn.text_color = "#171717"

        curBtn = gz.PushButton(self.key_align_box, padx=0, pady=0, width=int(w / 7), height=int(h / 4.2), image="resources/key_4_black_smol.gif", command=self._input_4, grid=[0,1])
        curBtn.bg = "#171717"
        curBtn.text_color = "#171717"

        curBtn = gz.PushButton(self.key_align_box, padx=0, pady=0, width=int(w / 7), height=int(h / 4.2), image="resources/key_5_black_smol.gif", command=self._input_5, grid=[1,1])
        curBtn.bg = "#171717"
        curBtn.text_color = "#171717"

        curBtn = gz.PushButton(self.key_align_box, padx=0, pady=0, width=int(w / 7), height=int(h / 4.2), image="resources/key_6_black_smol.gif", command=self._input_6, grid=[2,1])
        curBtn.bg = "#171717"
        curBtn.text_color = "#171717"

        curBtn = gz.PushButton(self.key_align_box, padx=0, pady=0, width=int(w / 7), height=int(h / 4.2), image="resources/key_7_black_smol.gif", command=self._input_7, grid=[0,2])
        curBtn.bg = "#171717"
        curBtn.text_color = "#171717"

        curBtn = gz.PushButton(self.key_align_box, padx=0, pady=0, width=int(w / 7), height=int(h / 4.2), image="resources/key_8_black_smol.gif", command=self._input_8, grid=[1,2])
        curBtn.bg = "#171717"
        curBtn.text_color = "#171717"

        curBtn = gz.PushButton(self.key_align_box, padx=0, pady=0, width=int(w / 7), height=int(h / 4.2), image="resources/key_9_black_smol.gif", command=self._input_9, grid=[2,2])
        curBtn.bg = "#171717"
        curBtn.text_color = "#171717"

        curBtn = gz.PushButton(self.key_align_box, padx=0, pady=0, width=int(w / 7), height=int(h / 4.2), image="resources/key_0_black_smol.gif", command=self._input_0, grid=[1,3])
        curBtn.bg = "#171717"
        curBtn.text_color = "#171717"

        for child in self.key_align_box.tk.winfo_children():
            child.configure(background="#171717")
            child.configure(bg="#171717")
            child.configure(borderwidth=0)
            child.configure(bd=0)
            child.configure(highlightthickness=0)
            child.configure(highlightcolor="#171717")
            child.configure(highlightbackground="#171717")

    def _init_status(self):
        self.status_box = gz.Box(self.app, width=int(w / 2), height=h, align="right", layout="fill")
        self.status_box.tk.configure(background="#171717")
        self.status_box.tk.configure(bg="#171717")

        self.status_align_box = gz.Box(self.status_box, width=int(w / 2), height=h, align="left", layout="fill")
        self.status_align_box.tk.configure(background="#171717")
        self.status_align_box.tk.configure(bg="#171717")

        self.welcome_box = gz.Box(self.status_align_box, width=int(w / 2), height=int(h / 3), align="top")
        self.welcome_message = gz.Text(self.welcome_box, text=self.message, size=s, font="Times New Roman", color="#C0C0C0", align="bottom")

        self.arm_box = gz.Box(self.status_align_box, width=int(w / 2), height=int(h / 2), align="bottom")
        self.arm_box.tk.configure(background="#171717")
        self.arm_box.tk.configure(bg="#171717")

        self.arm_button = gz.PushButton(self.arm_box, command=self._handle_arm, image="resources/button_arm_smol.gif", align="top", width=233, height=90)
        self.arm_button.tk.configure(background="#171717")
        self.arm_button.tk.configure(bg="#171717")
        self.arm_button.bg = "#171717"

    def _init_hidden(self):
        self.sampling_widget = gz.Box(self.app, visible=False)
        self.sampling_widget.repeat(50, self._handle_sockets)

    def _handle_sockets(self):
        print("Handle Sockets")

        self._reset_flags()
        readable, writable, errored = select.select(self.read_list, self.write_list, self.err_list, 0.05)

        print("Select Sockets")

        for sock in errored:
            # re-establish connection
            continue

        for sock in readable:
            result = sock.recv()
            topic = result[0:5]
            if topic == SENSOR_TOPIC:
                self._handle_sensor(result[5:]) # handle sensor data
            elif topic == SCREENSHOT_TOPIC:
                self.screenshot = True # handle screenshot

            # print("Result Input: %s" % result)

        print("Read Sockets")
        self._process_results()


        if self.alarm:
            message = self._get_message()
            for sock in writable:
                sock.send_string("%s%s" % (HUB_TOPIC, message))
            # print("Message Output: %s" % message)

        print("Write Sockets")
        #print("Another Sample!!!")

    def _reset_flags(self):
        self.screenshot = False
        self.motion = False
        self.light = False
        self.sound = False
        self.gas = False
        self.vibration = False

    def _handle_sensor(self, data):
        self.motion = data[0] == '1'
        self.light = data[1] == '1'
        self.sound = data[2] == '1'
        self.gas = data[3] == '1'
        self.vibration = data[4] == '1'

    def _get_message(self):
        result = ""

        if self.screenshot:
            result += '1'
        else:
            result += '0'

        if self.motion:
            result += '1'
        else:
            result += '0'

        if self.light:
            result += '1'
        else:
            result += '0'

        if self.sound:
            result += '1'
        else:
            result += '0'

        if self.gas:
            result += '1'
        else:
            result += '0'

        if self.vibration:
            result += '1'
        else:
            result += '0'

        return result

    def _input_0(self):
        print(self.state)
        if self.state == "init":
            if len(self.encrypt) < 7:
                self.encrypt += "0"
            else:
                self._encrypt_len()
        elif self.state == "input":
            if len(self.code) < 7:
                self.code += "0"
            else:
                self._code_len()

    def _input_1(self):
        print(self.state)
        if self.state == "init":
            if len(self.encrypt) < 7:
                self.encrypt += "1"
            else:
                self._encrypt_len()
        elif self.state == "input":
            if len(self.code) < 7:
                self.code += "1"
            else:
                self._code_len()

    def _input_2(self):
        print(self.state)
        if self.state == "init":
            if len(self.encrypt) < 7:
                self.encrypt += "2"
            else:
                self._encrypt_len()
        elif self.state == "input":
            if len(self.code) < 7:
                self.code += "2"
            else:
                self._code_len()

    def _input_3(self):
        print(self.state)
        if self.state == "init":
            if len(self.encrypt) < 7:
                self.encrypt += "3"
            else:
                self._encrypt_len()
        elif self.state == "input":
            if len(self.code) < 7:
                self.code += "3"
            else:
                self._code_len()

    def _input_4(self):
        print(self.state)
        if self.state == "init":
            if len(self.encrypt) < 7:
                self.encrypt += "4"
            else:
                self._encrypt_len()
        elif self.state == "input":
            if len(self.code) < 7:
                self.code += "4"
            else:
                self._code_len()

    def _input_5(self):
        print(self.state)
        if self.state == "init":
            if len(self.encrypt) < 7:
                self.encrypt += "5"
            else:
                self._encrypt_len()
        elif self.state == "input":
            if len(self.code) < 7:
                self.code += "5"
            else:
                self._code_len()

    def _input_6(self):
        print(self.state)
        if self.state == "init":
            if len(self.encrypt) < 7:
                self.encrypt += "6"
            else:
                self._encrypt_len()
        elif self.state == "input":
            if len(self.code) < 7:
                self.code += "6"
            else:
                self._code_len()

    def _input_7(self):
        print(self.state)
        if self.state == "init":
            if len(self.encrypt) < 7:
                self.encrypt += "7"
            else:
                self._encrypt_len()
        elif self.state == "input":
            if len(self.code) < 7:
                self.code += "7"
            else:
                self._code_len()

    def _input_8(self):
        print(self.state)
        if self.state == "init":
            if len(self.encrypt) < 7:
                self.encrypt += "8"
            else:
                self._encrypt_len()
        elif self.state == "input":
            if len(self.code) < 7:
                self.code += "8"
            else:
                self._code_len()

    def _input_9(self):
        print(self.state)
        if self.state == "init":
            if len(self.encrypt) < 7:
                self.encrypt += "9"
            else:
                self._encrypt_len()
        elif self.state == "input":
            if len(self.code) < 7:
                self.code += "9"
            else:
                self._code_len()

    def _input_code(self):
        self._change_state("input")
        self.code = ""

    def _code_len(self):
        self.code = ""
        self._change_message("Must be 4-8 Digits")

    def _encrypt_len(self):
        self.encrypt = ""
        self._change_message("Must be 4-8 Digits")

    def _wrong_code(self):
        self.code = ""
        self._change_message("Wrong Code!!!")

    def _encrypt_code(self):
        self.encrypt = Fernet(self.key).encrypt(self.encrypt.encode())

    def _check_code(self):
        return self.code.encode() == Fernet(self.key).decrypt(self.encrypt)

    def _handle_arm(self):
        print(self.state)
        if self.state == "input":
            if self._check_code():
                self.failed = 0
                if self.prev_state == "armed":
                    self._stop_alarm()
                    self._change_message("Disarmed")
                    self._change_state("disarmed")
                    self._toggle_arm_button()
                else:
                    self._sound_alarm()
                    self._change_message("Armed")
                    self._change_state("armed")
                    self._toggle_arm_button()
            else:
                self.failed += 1
                self._wrong_code()
                if self.prev_state == "armed" and self.failed >= 5 and not self.alarm:
                    self._sound_alarm()
        elif self.state == "init":
            if len(self.encrypt) >= 4:
                self._encrypt_code()
                self._change_message("Disarmed")
                self._change_state("disarmed")
                self._toggle_arm_button()
            else:
                self._code_len()
        else:
            self._change_message("Input Alarm Code")
            self._input_code()

    def _change_state(self, new_state):
        self.prev_state = self.state
        self.state = new_state

    def _change_message(self, new_message):
        self.message = "   " + new_message + "   "
        self.welcome_message.clear()
        self.welcome_message.append(self.message)

    def _toggle_arm_button(self):
        if self.state == "armed":
            self.arm_button.image = "resources/button_disarm_smol.gif"
        else:
            self.arm_button.image = "resources/button_arm_smol.gif"

    def _process_results(self):
        if not self.alarm:
            if self.state == 'armed' or self.prev_state == 'armed':
                result = self.screenshot or self.motion or self.sound or self.light or self.gas or self.vibration
                if result:
                    self._sound_alarm()

    def _sound_alarm(self):
        self.alarm = True
        pygame.mixer.music.play(9999999, 0.0)
        print("Alarm is on!")

    def _stop_alarm(self):
        self.alarm = False
        pygame.mixer.music.stop()
        print("Alarm is off!")

    def display(self):
        self.app.display()


if __name__ == "__main__":
    hub_gui = HubGui()
    hub_gui.display()
