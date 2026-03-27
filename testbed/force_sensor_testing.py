from pyniryo import *
import numpy as np

forceSensor = PinID.AI1
robotIpAddress = "192.168.42.2"
robot = NiryoRobot(robotIpAddress)
robot.calibrate_auto()

usingElectromagnet = True

#stuff for turning on and off the electromagnet
pin_electromagnet = PinID.DO4
robot.setup_electromagnet(pin_electromagnet)
if(usingElectromagnet): 
    robot.activate_electromagnet(pin_electromagnet)
else:
    robot.deactivate_electromagnet(pin_electromagnet)

while True:
    print(robot.analog_read(forceSensor))