import guizero as gz
import base64
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

# self.state values: "init" | "input" | "armed" | "disarmed"

w = 860
h = 430
s = 40

class HubGui:
    def __init__(self):
        self.message = "   Create New Code   " # message to display in gui
        self.key = Fernet.generate_key() # key for passcode enc/dec

        self.failed = 0

        self.encrypt = "" # encrypted code to verify against input code
        self.code = "" # input code to verify aginst encrypted code

        self.state = "" # current state of the system (init, input, armed, or disarmed)
        self.prev_state = "" # previous state of the system

        self.app = gz.App(bg="#171717", title="SecuriSys Central Hub", width=w, height=h) # the guizero app object

        self._init_app()

    def _init_app(self):
        self.app.set_full_screen()
        #pi dimensions: W - 500 | H - 414
        self._init_state()
        self._init_keyboard()
        self._init_status()

    def _init_keyboard(self):
        self.keyboard_box = gz.Box(self.app, width=int(w / 2), height=h, layout="fill", align="left", border=False)
        self.keyboard_box.tk.configure(background="#171717")
        self.keyboard_box.tk.configure(bg="#171717")

        self.key_align_box = gz.Box(self.keyboard_box, width=int(w / 2), height=h, layout="grid", align="right", border=False)
        self.key_align_box.tk.configure(background="#171717")
        self.key_align_box.tk.configure(bg="#171717")

        curBtn = gz.PushButton(self.key_align_box, padx=0, pady=0, width=83, height=103, image="key_1_smol.gif", command=self._input_1, grid=[0,0])
        curBtn.bg = "#171717"

        curBtn = gz.PushButton(self.key_align_box, padx=0, pady=0, width=83, height=103, image="key_2_smol.gif", command=self._input_2, grid=[1,0])
        curBtn.bg = "#171717"

        curBtn = gz.PushButton(self.key_align_box, padx=0, pady=0, width=83, height=103, image="key_3_smol.gif", command=self._input_3, grid=[2,0])
        curBtn.bg = "#171717"

        curBtn = gz.PushButton(self.key_align_box, padx=0, pady=0, width=83, height=103, image="key_4_smol.gif", command=self._input_4, grid=[0,1])
        curBtn.bg = "#171717"

        curBtn = gz.PushButton(self.key_align_box, padx=0, pady=0, width=83, height=103, image="key_5_smol.gif", command=self._input_5, grid=[1,1])
        curBtn.bg = "#171717"

        curBtn = gz.PushButton(self.key_align_box, padx=0, pady=0, width=83, height=103, image="key_6_smol.gif", command=self._input_6, grid=[2,1])
        curBtn.bg = "#171717"

        curBtn = gz.PushButton(self.key_align_box, padx=0, pady=0, width=83, height=103, image="key_7_smol.gif", command=self._input_7, grid=[0,2])
        curBtn.bg = "#171717"

        curBtn = gz.PushButton(self.key_align_box, padx=0, pady=0, width=83, height=103, image="key_8_smol.gif", command=self._input_8, grid=[1,2])
        curBtn.bg = "#171717"

        curBtn = gz.PushButton(self.key_align_box, padx=0, pady=0, width=83, height=103, image="key_9_smol.gif", command=self._input_9, grid=[2,2])
        curBtn.bg = "#171717"

        curBtn = gz.PushButton(self.key_align_box, padx=0, pady=0, width=83, height=103, image="key_0_smol.gif", command=self._input_0, grid=[1,3])
        curBtn.bg = "#171717"

        for child in self.key_align_box.tk.winfo_children():
            child.configure(background="#171717")
            child.configure(bg="#171717")

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

        self.arm_button = gz.PushButton(self.arm_box, command=self._handle_arm, image="button_arm_smol.gif", align="top", width=233, height=90)
        self.arm_button.tk.configure(background="#171717")
        self.arm_button.tk.configure(bg="#171717")
        self.arm_button.bg = "#171717"

    def _init_state(self):
        self._change_state("init")

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
        #print(self.encrypt)
        self.encrypt = Fernet(self.key).encrypt(self.encrypt.encode())
        #print(self.encrypt)

    def _check_code(self):
        #print(self.encrypt)
        #decrypt = Fernet(self.key).decrypt(self.encrypt)
        #print(decrypt)
        #print(self.code.encode())
        return self.code.encode() == Fernet(self.key).decrypt(self.encrypt)

    def _handle_arm(self):
        print(self.state)
        if self.state == "input":
            if self._check_code():
                self.failed = 0
                if self.prev_state == "armed":
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
            self.arm_button.image = "button_disarm_smol.gif"
        else:
            self.arm_button.image = "button_arm_smol.gif"



    def display(self):
        self.app.display()


if __name__ == "__main__":
    hub_gui = HubGui()

    hub_gui.display()
