from pyniryo import *
import numpy as np

forceSensor = PinID.AI1
robotIpAddress = "10.10.10.10"
robot = NiryoRobot(robotIpAddress)
robot.calibrate_auto()

#stuff for turning on and off the electromagnet
pin_electromagnet = PinID.DO4
robot.setup_electromagnet(pin_electromagnet)
robot.activate_electromagnet(pin_electromagnet)
#robot.deactivate_electromagnet(pin_electromagnet)

while True:
    print(robot.analog_read(forceSensor))