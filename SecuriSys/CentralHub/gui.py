import guizero as gz
import tkinter as tk
import tkinter.ttk as ttk

from guizero import Window
from parameters import *
from cryptography.fernet import Fernet
import zmq, select, pygame, fcntl, os, socket

# self.state values: "init" | "input" | "armed" | "disarmed"

w = 800
h = 430
s = 40

class HubGui:
    def __init__(self, sens_port = "6000", surv_port = "7000", fog_port = "8000"):
        self.sens_port = sens_port
        self.surv_port = surv_port
        self.fog_port = fog_port

        self.sens_addr = SENS_ADDR
        self.surv_addr = SURV_ADDR

        self.message = "   Create New Code   " # message to display in gui
        self.key = Fernet.generate_key() # key for passcode enc/dec

        self.failed = 0
        self.alarm = False
        self.timer = 0
        self.sensor_timer = 0

        self.encrypt = "" # encrypted code to verify against input code
        self.code = "" # input code to verify aginst encrypted code

        self.state = "" # current state of the system (init, input, armed, or disarmed)
        self.prev_state = "" # previous state of the system

        self.app = gz.App(bg="#171717", title="SecuriSys Central Hub", width=w, height=h) # the guizero app object

        self._init_net()
        self._init_music()
        self._init_intro()
        self._init_app()

    def _init_net(self):
        self.sens_topic = SENSOR_TOPIC
        self.surv_topic = SCREENSHOT_TOPIC

        self.context = zmq.Context()
        self.sub_socket = self.context.socket(zmq.SUB)

        self.sub_socket.connect("%s:%s" % (self.sens_addr, self.sens_port))
        self.sub_socket.connect("%s:%s" % (self.surv_addr, self.surv_port))

        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.sens_topic)
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.surv_topic)

        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_socket.bind("tcp://*:%s" % self.fog_port)

    def _init_music(self):
        pygame.mixer.init()
        pygame.mixer.music.load("resources/alarm.mp3")
        pygame.mixer.music.set_volume(0.8)

    def _init_intro(self):
        self.intro = Window(self.app, bg="#171717", title="SecuriSys Central Hub", width=w, height=h)
        self._init_loading()

    def _init_loading(self):
        self.progress = ttk.Progressbar(self.intro.tk, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack()
        self.progress_ndx = 0

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

    def _sensor_timer(self):
        if self.sensor_timer >= 300:
            self.sensor_timer = 0
            self._sound_alarm()
        else:
            self.sensor_timer += 1

    def _minute_timer(self):
        if self.timer >= 300:
            self.timer = 0
            print("Minute: %r" % self.minute)
            self.minute = True
        else:
            self.timer += 1

    def _handle_sockets(self):
        if not self.done:
            self._progress_bar()

        # print("Handle Sockets")
        self._reset_flags()
        try:
            result = self.sub_socket.recv(flags=zmq.NOBLOCK)
            if result:
                topic = result[0:5].decode("utf-8")
                print("Topic: %s" % topic)
                if topic == SENSOR_TOPIC:
                    self.sensor_timer = 0
                    self._handle_sensor(result[5:].decode("utf-8"))  # handle sensor data
                elif topic == SCREENSHOT_TOPIC:
                    self.screenshot = True  # handle screenshot
                # print("Read from a Socket")
                print("Result Input: %s" % result)
        except zmq.Again as err:
            print(err)
            # print("Didn't read from a Socket")
        except:
            self.sub_socket = self.context.socket(zmq.SUB)
            self.sub_socket.connect("%s:%s" % (self.sens_addr, self.sens_port))
            self.sub_socket.connect("%s:%s" % (self.surv_addr, self.surv_port))
            self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.sens_topic)
            self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.surv_topic)

        # print("Read Sockets")
        self._process_results()
        self._sensor_timer();
        if self.alarm:
            self._minute_timer();
            message = self._get_message()
            self.pub_socket.send_string("%s%s" % (HUB_TOPIC, message))
            self.pub_socket.send_string("%s" % HUB_TOPIC)

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

        if self.minute:
            result += '1'
        else:
            result += '0'

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
        return self.code == Fernet(self.key).decrypt(self.encrypt).decode()

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
        self.timer = 0
        self.sensor_timer = 0
        self.minute = False
        pygame.mixer.music.play(9999999, 0.0)
        print("Alarm is on!")

    def _stop_alarm(self):
        self.alarm = False
        self.timer = 0
        self.sensor_timer = 0
        self.minute = False
        pygame.mixer.music.stop()
        print("Alarm is off!")

    def _get_increment(self):
        self.progress_ndx += 1
        if self.progress_ndx <= 25:
            return 1
        elif self.progress_ndx <= 50:
            return 2
        elif self.progress_ndx <= 75:
            return 3
        else:
            return 2

    def _progress_bar(self):
        if self.progress['value'] < 100:
            self.progress['value'] += self._get_increment()
            self.app.after(100, self._progress_bar)
        else:
            self.done = True
            self.intro.hide()

    def display(self):
        self.done = False
        self.intro.show()
        self.app.display()


if __name__ == "__main__":
    hub_gui = HubGui()
    hub_gui.display()
