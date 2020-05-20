# setup for sensors

#from gpiozero import MotionSensor, LightSensor
import RPi.GPIO as GPIO
import time

class Sensor:
    def __init__(self, time = 300):
        self.motionSen = 21   ## GPIO pin of motion sen
        self.lightSen = 16   ## GPIO pin of light sen
        self.soundSen = 24    ## GPIO pin of sound sen
        self.gasSen= 18 ;     ## GPIO pin of gas sen
        self.vibrateSen = 4; ## GPIO pin of vibrate sen

        self._init_sensors()
        self._init_events(time)

    def _init_sensors(self):
        #GPIO SETUP of sensors
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.motionSen, GPIO.IN)
        GPIO.setup(self.lightSen, GPIO.IN)
        GPIO.setup(self.soundSen, GPIO.IN)
        GPIO.setup(self.gasSen, GPIO.IN)
        GPIO.setup(self.vibrateSen, GPIO.IN)

        #initial empty tuple of all functs
        self.sensors = ()

    def _init_events(self, time = 300):
        #Adding motion function to the GPIO pin 21
        GPIO.add_event_detect(self.motionSen, GPIO.BOTH, bouncetime=time);
        GPIO.add_event_callback(self.motionSen, self.Motion);

        #Adding light function to the GPIO pin 16
        GPIO.add_event_detect(self.lightSen, GPIO.BOTH, bouncetime=time);
        GPIO.add_event_callback(self.lightSen, self.Light);

        #Adding sound function to the GPIO pin 24
        GPIO.add_event_detect(self.soundSen, GPIO.BOTH, bouncetime=time);
        GPIO.add_event_callback(self.soundSen, self.Sound);

        #Adding gas function to the GPIO pin 18
        GPIO.add_event_detect(self.gasSen, GPIO.BOTH, bouncetime=time);
        GPIO.add_event_callback(self.gasSen, self.Gas);

        #Adding vibration function to the GPIO pin 4
        GPIO.add_event_detect(self.vibrateSen, GPIO.BOTH, bouncetime=time);
        GPIO.add_event_callback(self.vibrateSen, self.Vibration);

    ## bool sensor functs

    ## could add the while loop to continously read from sensors in each function
    ## right now, its just a basic shell that returns true if activity is found and false otherwise
    def Motion(self, motionSen):
        return GPIO.input(motionSen)

    def Light(self, lightSen):
        return GPIO.input(lightSen)

    def Sound(self, soundSen):
        return GPIO.input(soundSen)

    def Gas(self, gasSen):
        return GPIO.input(gasSen)

    def Vibration(self, vibrateSen):
        return GPIO.input(vibrateSen)

    def get_sample(self):
        #updated sensor tuple w all the funct but are not continously active
        #still returns bool
        self.sensors = (self.Motion(self.motionSen), self.Light(self.lightSen), self.Sound(self.soundSen), self.Gas(self.gasSen), self.Vibration(self.vibrateSen));
        return self.sensors

    def print_sample(self):
        for x in self.sensors:
            print(x)

## loop to activate sensors continously ##
""" while True:
    Motion(motionSen);
    Light(lightSen);
    Sound(soundSen);
    Gas(gasSen);
    Vibration(vibrateSen);
"""

if __name__ == "__main__":
    sen = Sensor()

    while True:
        sen.get_sample()
        sen.print_sample()
        time.sleep(0.5)