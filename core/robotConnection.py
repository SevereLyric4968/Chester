from pyniryo import *
#version mismatch which doesn't seem fixable
robotIpAddress = "10.10.10.10"
workspaceName = "workspace_1"
robot = NiryoRobot(robotIpAddress)
robot.calibrate_auto()

robot.move(PoseObject(90, -57, 211, 127, 77, 85))
robot.close_connection()