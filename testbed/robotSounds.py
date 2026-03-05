from pyniryo import *

robotIpAddress = "192.168.42.1"

robot = NiryoRobot(robotIpAddress)
robot.calibrate_auto()
robot.set_volume(50)
#robot.say("Hello",0)