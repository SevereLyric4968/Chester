from pyniryo import *
import numpy as np

forceSensor = PinID.AI1
robotIpAddress = "10.10.10.10"
robot = NiryoRobot(robotIpAddress)

while True:
    print(robot.analog_read(forceSensor))