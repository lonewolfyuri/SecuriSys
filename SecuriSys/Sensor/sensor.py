# setup for sensors

#from gpiozero import MotionSensor, LightSensor
import RPi.GPIO as GPIO
import time

motionSen = 21   ## GPIO pin of motion sen
lightSen = 16   ## GPIO pin of light sen
soundSen = 24    ## GPIO pin of sound sen
gasSen= 18 ;     ## GPIO pin of gas sen
vibrateSen = 4; ## GPIO pin of vibrate sen

#GPIO SETUP of sensors
GPIO.setmode(GPIO.BCM)
GPIO.setup(motionSen, GPIO.IN)
GPIO.setup(lightSen, GPIO.IN)
GPIO.setup(soundSen, GPIO.IN)
GPIO.setup(gasSen, GPIO.IN)
GPIO.setup(vibrateSen, GPIO.IN)

#initial empty tuple of all functs
sensors = ()


## bool sensor functs

## could add the while loop to continously read from sensors in each function
## right now, its just a basic shell that returns true if activity is found and false otherwise
def Motion(motionSen):
    if GPIO.input(motionSen):
        return True;
    else:
        return False;

def Light(lightSen):
    if GPIO.input(lightSen):
        return True;
    else:
        return False;

def Sound(soundSen):
    if GPIO.input(soundSen):
        return True;
    else:
        return False;

def Gas(gasSen):
    if GPIO.input(gasSen):
        return True;
    else:
        return False;

def Vibration(vibrateSen):
    if GPIO.input(vibrateSen):
        return True;
    else:
        return False;

#Adding motion function to the GPIO pin 21
GPIO.add_event_detect(motionSen, GPIO.BOTH, bouncetime=300);
GPIO.add_event_callback(motionSen, Motion);

#Adding light function to the GPIO pin 16
GPIO.add_event_detect(lightSen, GPIO.BOTH, bouncetime=300);
GPIO.add_event_callback(lightSen, Light);

#Adding sound function to the GPIO pin 24
GPIO.add_event_detect(soundSen, GPIO.BOTH, bouncetime=300);
GPIO.add_event_callback(soundSen, Sound);

#Adding gas function to the GPIO pin 18
GPIO.add_event_detect(gasSen, GPIO.BOTH, bouncetime=300);
GPIO.add_event_callback(gasSen, Gas);

#Adding vibration function to the GPIO pin 4
GPIO.add_event_detect(vibrateSen, GPIO.BOTH, bouncetime=300);
GPIO.add_event_callback(vibrateSen, Vibration);

#updated sensor tuple w all the funct but are not continously active
#still returns bool
sensors = (Motion(motionSen), Light(lightSen), Sound(soundSen), Gas(gasSen), Vibration(vibrateSen));

for x in sensors:
    print(x)

## loop to activate sensors continously ##
""" while True:
    Motion(motionSen);
    Light(lightSen);
    Sound(soundSen);
    Gas(gasSen);
    Vibration(vibrateSen);
"""
