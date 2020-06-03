import guizero as gz
import tkinter as tk
import tkinter.ttk as ttk

from guizero import Window, Picture
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
        self.screenshot_timer = 0
        self.done = False
        self.first = True

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

    def _init_app(self):
        self.app.set_full_screen()
        self._init_intro()
        #pi dimensions: W - 500 | H - 414
        self._init_state()
        self._init_keyboard()
        self._init_status()
        self._init_hidden()

    def _init_intro(self):
        self.intro = Window(self.app, bg="#171717", title="SecuriSys Central Hub", width=w, height=h)
        self.intro.set_full_screen()
        self.intro_box = gz.Box(self.intro, width=w, height=h, layout="fill", align="top", border=False)
        #self.intro_box.tk.configure()
        #self.intro_bg = tk.Label(self.intro.tk, image=tk.PhotoImage("resources/loading.png"))
        #self.intro_bg.place(x=0, y=0, relwidth=1, relheight=1)
        self.intro_bg = Picture(self.intro_box, image="resources/loading_final.png", align="left", width=self.intro_box.width, height=self.intro_box.height)

        s = ttk.Style()
        s.theme_use('clam')
        s.configure("silver.Horizontal.TProgressbar", foreground='#C0C0C0', background='#171717')
        self._init_loading()

    def _init_loading(self):
        self.loading_box = gz.Box(self.intro, width=self.intro.width, height=int(self.intro.height / 4), layout="fill", align="bottom", border=False)
        self.progress = ttk.Progressbar(self.loading_box.tk, style="silver.Horizontal.TProgressbar", orient=tk.HORIZONTAL, length=int(self.loading_box.width * 0.8), mode='determinate', maximum=120)
        self.progress.pack()

    def _show_loading(self):
        self.intro.show()

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

        buttons = []
        boxes = []

        curBox = gz.Box(self.key_align_box, width=int(w / 6.5), height=int(h / 4), grid=[0,0])
        curBtn = gz.PushButton(curBox, width=int(curBox.width * 3 / 4), height=int(curBox.height * 3 / 4), image="resources/key_1_black_smol.gif", command=self._input_1)
        curBtn.bg = "#171717"
        curBtn.text_color = "#171717"

        buttons.append(curBtn)
        boxes.append(curBox)

        curBox = gz.Box(self.key_align_box, width=int(w / 6.5), height=int(h / 4), grid=[1, 0])
        curBtn = gz.PushButton(curBox, width=int(curBox.width * 3 / 4), height=int(curBox.height * 3 / 4), image="resources/key_2_black_smol.gif", command=self._input_2)
        curBtn.bg = "#171717"
        curBtn.text_color = "#171717"

        buttons.append(curBtn)
        boxes.append(curBox)

        curBox = gz.Box(self.key_align_box, width=int(w / 6.5), height=int(h / 4), grid=[2, 0])
        curBtn = gz.PushButton(curBox, width=int(curBox.width * 3 / 4), height=int(curBox.height * 3 / 4), image="resources/key_3_black_smol.gif", command=self._input_3)
        curBtn.bg = "#171717"
        curBtn.text_color = "#171717"

        buttons.append(curBtn)
        boxes.append(curBox)

        curBox = gz.Box(self.key_align_box, width=int(w / 6.5), height=int(h / 4), grid=[0, 1])
        curBtn = gz.PushButton(curBox, width=int(curBox.width * 3 / 4), height=int(curBox.height * 3 / 4), image="resources/key_4_black_smol.gif", command=self._input_4)
        curBtn.bg = "#171717"
        curBtn.text_color = "#171717"

        buttons.append(curBtn)
        boxes.append(curBox)

        curBox = gz.Box(self.key_align_box, width=int(w / 6.5), height=int(h / 4), grid=[1, 1])
        curBtn = gz.PushButton(curBox, width=int(curBox.width * 3 / 4), height=int(curBox.height * 3 / 4), image="resources/key_5_black_smol.gif", command=self._input_5)
        curBtn.bg = "#171717"
        curBtn.text_color = "#171717"

        buttons.append(curBtn)
        boxes.append(curBox)

        curBox = gz.Box(self.key_align_box, width=int(w / 6.5), height=int(h / 4), grid=[2, 1])
        curBtn = gz.PushButton(curBox, width=int(curBox.width * 3 / 4), height=int(curBox.height * 3 / 4), image="resources/key_6_black_smol.gif",command=self._input_6)
        curBtn.bg = "#171717"
        curBtn.text_color = "#171717"

        buttons.append(curBtn)
        boxes.append(curBox)

        curBox = gz.Box(self.key_align_box, width=int(w / 6.5), height=int(h / 4), grid=[0, 2])
        curBtn = gz.PushButton(curBox, width=int(curBox.width * 3 / 4), height=int(curBox.height * 3 / 4), image="resources/key_7_black_smol.gif", command=self._input_7)
        curBtn.bg = "#171717"
        curBtn.text_color = "#171717"

        buttons.append(curBtn)
        boxes.append(curBox)

        curBox = gz.Box(self.key_align_box, width=int(w / 6.5), height=int(h / 4), grid=[1, 2])
        curBtn = gz.PushButton(curBox, width=int(curBox.width * 3 / 4), height=int(curBox.height * 3 / 4), image="resources/key_8_black_smol.gif", command=self._input_8)
        curBtn.bg = "#171717"
        curBtn.text_color = "#171717"

        buttons.append(curBtn)
        boxes.append(curBox)

        curBox = gz.Box(self.key_align_box, width=int(w / 6.5), height=int(h / 4), grid=[2, 2])
        curBtn = gz.PushButton(curBox, width=int(curBox.width * 3 / 4), height=int(curBox.height * 3 / 4), image="resources/key_9_black_smol.gif", command=self._input_9)
        curBtn.bg = "#171717"
        curBtn.text_color = "#171717"

        buttons.append(curBtn)
        boxes.append(curBox)

        curBox = gz.Box(self.key_align_box, width=int(w / 6.5), height=int(h / 4), grid=[1, 3])
        curBtn = gz.PushButton(curBox, width=int(curBox.width * 3 / 4), height=int(curBox.height * 3 / 4), image="resources/key_0_black_smol.gif",command=self._input_0)
        curBtn.bg = "#171717"
        curBtn.text_color = "#171717"

        buttons.append(curBtn)
        boxes.append(curBox)

        for button in buttons:
            child = button.tk
            child.configure(background="#171717")
            child.configure(bg="#171717")
            child.configure(borderwidth=0)
            child.configure(bd=0)
            child.configure(highlightthickness=0)
            child.configure(highlightcolor="#171717")
            child.configure(highlightbackground="#171717")

        for box in boxes:
            child = box.tk
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
            if not self.alarm:
                self._sound_alarm()
        else:
            self.sensor_timer += 1

    def _screenshot_timer(self):
        if self.screenshot_timer >= 300:
            self.screenshot_timer = 0
            if not self.alarm:
                self._sound_alarm()
        else:
            self.screenshot_timer += 1

    def _minute_timer(self):
        if self.timer >= 300:
            self.timer = 0
            print("Minute: %r" % self.minute)
            self.minute = True
        else:
            self.timer += 1

    def _encrypt_payload(self, payload):
        return Fernet(NET_KEY).encrypt(payload.encode("utf-8"))

    def _decrypt_payload(self, payload):
        return Fernet(NET_KEY).decrypt().decode("utf-8")

    def _handle_sockets(self):
        sensor_in = False
        screenshot_in = False
        if self.first:
            self.first = False
            self._show_loading()

        if not self.done:
            self._progress_bar()

        # print("Handle Sockets")
        self._reset_flags()
        try:
            result = self.sub_socket.recv(flags=zmq.NOBLOCK)
            if result:
                topic = result[0:5].decode("utf-8")
                print("Topic: %s" % topic)
                #print("Result Input: %s" % result)
                if topic == SENSOR_TOPIC:
                    sensor_in = True
                    self.sensor_timer = 0
                    self._handle_sensor(self._decrypt_payload(result[5:].decode("utf-8")))  # handle sensor data
                elif topic == SCREENSHOT_TOPIC:
                    self.screenshot = True  # handle screenshot
                elif topic == CONNECT_SURV_TOPIC:
                    screenshot_in = True
                    self.screenshot_timer = 0
                # print("Read from a Socket")
        except zmq.Again as err:
            print(err)
            # print("Didn't read from a Socket")
        except socket.error as err:
            print("Reconnecting Sockets")
            print(err)
            self.sub_socket = self.context.socket(zmq.SUB)
            self.sub_socket.connect("%s:%s" % (self.sens_addr, self.sens_port))
            self.sub_socket.connect("%s:%s" % (self.surv_addr, self.surv_port))
            self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.sens_topic)
            self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.surv_topic)

        # print("Read Sockets")
        self._process_results()
        if not sensor_in and (self.state == "armed" or self.prev_state == "armed"):
            self._sensor_timer()
        if not screenshot_in and (self.state == "armed" or self.prev_state == "armed"):
            self._screenshot_timer()
        if self.alarm:
            self._minute_timer()
            message = self._get_message()
            self.pub_socket.send_string("%s%s" % (HUB_TOPIC, self._encrypt_payload(message)))
            self.pub_socket.send_string("%s" % HUB_TOPIC)
        self.pub_socket.send_string("%s" % CONNECT_HUB_TOPIC)

    def _reset_flags(self):
        self.screenshot = False
        self.motion = False
        self.light = False
        self.sound = False
        self.gas = False
        self.vibration = False

    def _handle_sensor(self, data):
        print("Sensor Data: %s" % data)
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
                if self.screenshot or self.motion or self.sound or self.light or self.gas or self.vibration:
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
        if self.progress['value'] <= 30:
            return 1
        elif self.progress['value'] <= 50:
            return 2
        elif self.progress['value'] <= 100:
            return 3
        else:
            return 2

    def _progress_bar(self):
        if self.progress['value'] < 130:
            self.progress['value'] += self._get_increment()
        else:
            self.done = True
            self.intro.hide()

    def display(self):
        self.app.display()


if __name__ == "__main__":
    hub_gui = HubGui()
    hub_gui.display()
