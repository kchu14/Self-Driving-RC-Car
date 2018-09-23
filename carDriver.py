# carDriver.py
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

def flashing(pin, storage):
    """Flashes a light at given pin number"""
    GPIO.setup(pin, GPIO.OUT)
    while storage.getAll()[0] == 0:
        GPIO.output(pin, False)
        time.sleep(0.5)
        GPIO.output(pin, True)
        time.sleep(0.5)
        

def setup():
    waiting = True
    #Red
    orange = 18
    green = 22
    temp = Asdf()
    temp.addMe(0)

    GPIO.setmode(GPIO.BOARD)

    # Hbridge motor logic pins
    hbridge = {'FM':7, 'BM':38 ,'R':11, 'L':13, 'B':36, 'F':40}

    # Re-find sensor pins, pair up.
    trig = {'br':33, 'bl':29, 'bm':31, 'fr':12, 'fm':16, 'fl':15}
    # Verify pin numbers
    echo = {'br':38, 'bl':35, 'bm':36, 'fr':38, 'fm':36, 'fl':35}

    # Set up motors
    GPIO.setup(hbridge['FM'], GPIO.OUT)
    GPIO.setup(hbridge['BM'], GPIO.OUT)

    # Pins 23 and 24 for LED
    # Needs 5V, Trigger, GRD
    # Make this an ORANGE light
    GPIO.setup(orange, GPIO.OUT)
    # Make this a GREEN light
    GPIO.setup(green, GPIO.OUT)

    # Activate the ORANGE light to show calibrating
    GPIO.output(orange, True)
    GPIO.output(green, False)

    # Set up motor logic pins
    GPIO.setup(hbridge['R'], GPIO.OUT)
    GPIO.setup(hbridge['L'], GPIO.OUT)
    GPIO.setup(hbridge['B'], GPIO.OUT)
    GPIO.setup(hbridge['F'], GPIO.OUT)

    # Set up the car to to straight
    print('calibrating... ')
    go = calibrate(hbridge)
    print('centered.')
    print('ready to begin. Block the front sensors to begin driving.')

    ####### Beginning the car starting sequence #######

    # Creates the first storage list for starting the car.
    storage1 = Asdf()

    orangeFlash = threading.Thread(target=flashing, args = (orange, temp))

    # Starting sequence...
    print('starting flash')
    orangeFlash.start()
    while waiting:
        
        # Reset the variable checking for sensor ranges.
        threes = 0
        # Activate the front sensors
        forward = True
        pickSensors(trig, echo, forward, storage1)

        # Check data points for each of the sensors.
        print('testing threes')
        print(storage1.getAll())
        for i in range(storage1.length()):
            print(storage1.getValue(i))
            # Checks if the returned data is less than 5 cm
            if storage1.getValue(i) <= 5:
                threes += 1

        # threes == 3 if all of the front sensors are covered (w/i 5 cm)
        if threes == 3:
            print('threes valid')
            waiting = False
            # Enable forward by default so that
            forward = True
            go = True
            GPIO.output(23, False)
            # Leave green light on for the rest of running, disable at end.
            GPIO.output(24, True)
            temp.reset()
            temp.addMe(1)
            return hbridge, trig, echo, forward, go

        # Only need to worry about overwriting when the sensors aren't covered
        else:
            # Delay to stop overwriting
            time.sleep(0.2)

        # Clear the storage no matter what.
        storage1.reset()

def pickSensors(trig, echo, forward, storage1):
    """Picks which sensors to activate; front or back based on forward bool.
    a is a storage list for the respective direction."""
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
                                     echo[pick[num]], storage1, pick2[num]))
    tMid = threading.Thread(target=access,
                            args = (trig[pick[num + 1]],
                                    echo[pick[num + 1]], storage1, pick2[num + 1]))
    tRight = threading.Thread(target=access,
                              args = (trig[pick[num + 2]],
                                      echo[pick[num + 2]], storage1, pick2[num + 2]))

    # Start threads for front
    tLeft.start()
    tMid.start()
    tRight.start()

def calibrate(hbridge):
    """Straightens out the front wheel set and set pins to OUTPUT"""
    GPIO.setmode(GPIO.BOARD)
    print('running cal')

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

def forwards(front):
    """Accesses the 'set' storage list to get the outputs of sensors,
    uses IDs to decypher which is which, and lastly compares to determine
    direction to go"""
    sensors = ['L', 'M', 'R']
    directions = ["left", "straight", "right"]

    # inches distance for safetyDist
    inSafe = 10
    # If the car is within this proximity, it will stop.
    safetyDist = inSafe * 2.54

    # inches distance for turnDist
    inTurn = 30
    # If the car is within this proximity of an object, it will begin turning
    # Still must be further than safetyDist.
    turnDist = inTurn * 2.54

    for i in range(a.length()):

        # Left Sensor
        if ord(front.getID(i)[1]) == 76:
            sensors[0] = a.getValue(i)

        # Right Sensor
        elif ord(front.getID(i)[1]) == 82:
            sensors[1] = a.getValue(i)

            # Middle Sensor
        elif ord(front.getID(i)[1]) == 77:
            sensors[2] = a.getValue(i)


    for dist in sensors:
        if dist <= safetyDist:
            return 'back'

    for i in range(len(sensors)):
        # If a sensor is within that range, turn
        if sensors[i] <= turnDist:
            return directions[i]

    return 'straight'

def manuever(DIR, hbridge):
    """Drives the car in the given direction based on DIR var"""
    if DIR == 'left':
        # Going left
        GPIO.output(hbridge['R'], False)
        GPIO.output(hbridge['L'], True)

    elif DIR == 'right':
        # Going Right
        GPIO.output(hbridge['R'], True)
        GPIO.output(hbridge['L'], False)

    elif DIR == 'straight':
        # Going straight
        GPIO.output(hbridge['R'], False)
        GPIO.output(hbridge['L'], False)

def goBack(back):
    """Continues back until within given distance, back is the storage list.
    Checks the 2nd letter to get ID of sensor."""
    sensors = ['L', 'M', 'R']
    backwards = True
    # Number of inches to switch directions (go forwards)
    switchIn = 10
    # Converts to cm
    switchDist = switchIn * 2.54

    for i in range(a.length()):

        # Left Sensor
        if ord(front.getID(i)[1]) == 76:
            sensors[0] = a.getValue(i)

        # Right Sensor
        elif ord(front.getID(i)[1]) == 82:
            sensors[1] = a.getValue(i)

            # Middle Sensor
        elif ord(front.getID(i)[1]) == 77:
            sensors[2] = a.getValue(i)

    for dist in sensors:
        if dist <= switchIn:
            return 'switch'

    return 'continue'

def main():
    hbridge, trig, echo, forward, go = setup()

    GPIO.setmode(GPIO.BOARD)
    done = False
    label = ['back left', 'back middle', 'back right']

    # Create alternate storage lists for the actual running of the car.
    front = Asdf()
    back = Asdf()

    while go:
        # Manages the car while it is going forwards, back is ignored.
        if forward:
            # Turn on back Motor so that the car begins going forwards
            GPIO.output(hbridge['FM'], True)
            GPIO.output(hbrdige['BM'], False)

            # Activate the front sensors.
            pickSensors(trig, echo, forward, front)

            # Delays to prevent overwriting
            time.sleep(0.2)

            # Manages motor 1's ability to steer the car.
            turnTo = forwards(front)
            if turnTo != 'back':
                manuever(turnTo, hbridge)

            # Needs to check if it has cleared the barrier

            # Clear the storage lists
            front.reset()

        # Manages the back sensors, front is ignored again
        elif not forward:
            # Set the back Motor to backwards.
            GPIO.output(hbridge['FM'], False)
            GPIO.output(hbrdige['BM'], True)

            # Activate the back sensors.
            pickSensors(trig, echo, forward, back)

            # Delay to stop overwriting
            time.sleep(0.2)

            # Gets whether or not to continue going backwards
            cont = goBack(back)

            if cont == 'switch':
                forward = True

            # Clear the storage lists
            back.reset()

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
