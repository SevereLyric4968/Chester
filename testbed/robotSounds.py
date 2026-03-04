from pyniryo import *

robotIpAddress = "10.10.10.10"

robot = NiryoRobot(robotIpAddress)
robot.calibrate_auto()
robot.set_volume(50)
robot.say("Hello",0)