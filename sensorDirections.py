# sensorDirections.py
# Kyle Chu, Alex Sfakianos
# https://itp.nyu.edu/physcomp/labs/motors-and-transistors/dc-motor-control-using-an-h-bridge/
# \n new line

import RPi.GPIO as GPIO
import time
import threading
from aClass import Asdf
from graphics import *
from buttonas import Buttons
import sys


def pickSensors(trig, echo, forward, a):
    """Picks which sensors to activate; front or back based on forward bool"""
    GPIO.setmode(GPIO.BOARD)

    pick = ['fl', 'fm', 'fr', 'bl', 'bm', 'br']
    pick2 = ['fL', 'fM', 'fR', 'bL', 'bM', 'bR']
    # num is the starting point for pick and pick2 when defining threads
    num = 0

    if not forward:
        num = 3 

    # Defining front sensor threads
    tLeft = threading.Thread(target=access,
                             args = (trig[pick[num]],
                                     echo[pick[num]], a, pick2[num]))                 
    tMid = threading.Thread(target=access,
                            args = (trig[pick[num + 1]],
                                    echo[pick[num + 1]], a, pick2[num + 1]))
    tRight = threading.Thread(target=access,
                              args = (trig[pick[num + 2]],
                                      echo[pick[num + 2]], a, pick2[num + 2]))

    # Start threads for front
    tLeft.start()
    tMid.start()
    tRight.start()


def calibrate(hbridge):
    """Straightens out the front wheel set and set pins to OUTPUT"""
    GPIO.setmode(GPIO.BOARD)
    
    # Front and back motors
    GPIO.setup(hbridge['FM'], GPIO.OUT)
    GPIO.setup(hbridge['BM'], GPIO.OUT)

    # Letters represent logic pins per hbridge,
    # setting true goes in that direction.
    GPIO.setup(hbridge['R'], GPIO.OUT)
    GPIO.setup(hbridge['L'], GPIO.OUT)
    GPIO.setup(hbridge['B'], GPIO.OUT)
    GPIO.setup(hbridge['F'], GPIO.OUT)

    # Activate the front motor
    GPIO.output(hbridge['FM'], True)

    # Go all the way right
    GPIO.output(hbridge['R'], True)
    GPIO.output(hbridge['L'], False)
    time.sleep(2)

    # Go back left to center (~0.5s)
    GPIO.output(hbridge['R'], False)
    GPIO.output(hbridge['L'], True)
    time.sleep(0.525)

    GPIO.output(hbridge['R'], False)
    GPIO.output(hbridge['L'], False)

    # Deactivate the front motor
    GPIO.output(hbridge['FM'], False)

    return True


def access(trig, echo, classVar, ID):
    """Accesses the given sensor and adds the data to classVar (a)"""

    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(trig, GPIO.OUT)
    GPIO.output(trig, False)
    GPIO.setup(echo, GPIO.IN)

    # GREEN
    GPIO.setup(36, GPIO.OUT)
    # RED
    GPIO.setup(32, GPIO.OUT)
    # ORANGE
    GPIO.setup(7, GPIO.OUT)

    GPIO.output(trig, True)
    time.sleep(0.00001)
    GPIO.output(trig, False)

    while GPIO.input(echo) == 0:
        pulse_start = time.time()

    while GPIO.input(echo) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start

    distance = pulse_duration * 17150
    distance = round(distance, 2)

    classVar.addMe([ID, distance])


def direction(a):
    """Accesses the 'a' class to get the outputs of sensors, uses IDs to
decypher which is which, and lastly compares to determine direction to go"""
    sensors = ['L', 'M', 'R']

    for i in range(a.length()):

        # Left Sensor
        if ord(a.getID(i)[1]) == 76:
            sensors[0] = a.getValue(i)

        # Right Sensor
        elif ord(a.getID(i)[1]) == 82:
            sensors[1] = a.getValue(i)

        # Middle Sensor
        elif ord(a.getID(i)[1]) == 77:
            sensors[2] = a.getValue(i)

    print(sensors)


    # Compare directions

    #return dire


def main():

    GPIO.setmode(GPIO.BOARD)
    done = False
    label = ['back left', 'back middle', 'back right']

    # Hbridge motor logic pins
    hbridge = {'FM':7, 'BM':38 ,'R':11, 'L':13, 'B':36, 'F':40}

    # Re-find sensor pins, pair up.
    trig = {'br':33, 'bl':29, 'bm':31, 'fr':20, 'fm':16, 'fl':15}
    echo = {'br':38, 'bl':35, 'bm':36, 'fr':38, 'fm':36, 'fl':35}

    # Set up the car to to straight
    print('calibrating...')
    go = calibrate(hbridge)
    print('centered.')
    print(go)
    p = input('give num')

    a = Asdf()
    forward = True
    while go:

        # Manages the car while it is going forwards, back is ignored.
        if forward:

            pickSensors(trig, echo, forward, a)

            # Delays to prevent overwriting
            time.sleep(0.2)

            # Use second character to determine L, M, R

        # Manages the back sensors, front is ignored again
        elif not forward:

            pickSensors(trig, echo, forward, a)

            # Delay to stop overwriting
            time.sleep(0.2)


        print(a.getID(0))
        direction(a)
        go = False

    GPIO.cleanup()
    sys.exit()


def wheelCheck():

    GPIO.setmode(GPIO.BOARD)
    done = False
    label = ['back left', 'back middle', 'back right']

    # Hbridge motor logic pins
    hbridge = {'FM':7, 'BM':38 ,'R':11, 'L':13, 'B':36, 'F':40}

    # Front and back motors
    GPIO.setup(hbridge['FM'], GPIO.OUT)
    GPIO.setup(hbridge['BM'], GPIO.OUT)

    # Letters represent logic pins per hbridge,
    # setting true goes in that direction.
    GPIO.setup(hbridge['R'], GPIO.OUT)
    GPIO.setup(hbridge['L'], GPIO.OUT)
    GPIO.setup(hbridge['B'], GPIO.OUT)
    GPIO.setup(hbridge['F'], GPIO.OUT)

    GPIO.output(hbridge['FM'], True)
    GPIO.output(hbridge['BM'], False)

    # Going Right
    GPIO.output(hbridge['R'], True)
    GPIO.output(hbridge['L'], False)

    print('going right')
    a = input('num to left')

    # Going Left
    GPIO.output(hbridge['R'], False)
    GPIO.output(hbridge['L'], True)
    
    print('going left')
    a = input('num to back')

    # Going Backwards
    GPIO.output(hbridge['FM'], False)
    GPIO.output(hbridge['BM'], True)
    GPIO.output(hbridge['B'], True)
    GPIO.output(hbridge['F'], False)

    print('running back')
    a = input('num to fowards')
    
    GPIO.output(hbridge['B'], False)
    GPIO.output(hbridge['F'], True)

    print('running forwards')
    a = input('num end')
    GPIO.cleanup()
    time.sleep(1)
    sys.exit() 
