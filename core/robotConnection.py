from pyniryo import *
#version mismatch which doesn't seem fixable
robot = NiryoRobot("10.10.10.10")
robot.calibrate_auto()

robot.move(PoseObject(90, -57, 211, 127, 77, 85))
robot.close_connection()