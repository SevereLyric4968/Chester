from pyniryo import *
import numpy as np
import math

robotIpAddress = "192.168.42.1"
#robot2IpAddress = "192.168.42.2" #this for ethernet use a laptop with IP address 192.168.42.100
print("a")


robot = NiryoRobot(robotIpAddress)
#robot2 = NiryoRobot(robot2IpAddress)
print("b")


robot.calibrate_auto()
#robot2.calibrate_auto()
pose = robot.get_pose()
print(pose)


print("d")
pose_target_obj = PoseObject(0.2, 0, 0.2, 0, 0.75, 0) # in meters and radians
robot.move_pose(pose_target_obj)


#robot 2 movement
print("e")
pose_target_obj2 = PoseObject(0.235,  0.075, 0.128, 0, math.pi/2, 0) # in meters and radians
#robot.move_pose(pose_target_obj2)

pose_home = PoseObject(0.0023, -0.1335, 0.208, 0, math.pi/2, 0)
robot.move_pose(pose_home)
#robot2.move_pose(pose_home)
"""

pin_electromagnet = PinID.DO4

robot = NiryoRobot(robotIpAddress)
#robot2 = NiryoRobot(robot2IpAddress)

robot.calibrate_auto()
#robot2.calibrate_auto()

#(0.203, -0.339, 0.027, 0, 1.5, 0) robot
#(0.2, 0.3, 0.038, 0, 1.5, 0) robot2
#test both at 0.038 for calibration start

pickup_location = PoseObject(0.430,  0.15, 0.208, 0, np.pi/2, 0) # in meters and radians 0.038
pickup2_location = PoseObject(0.155,  0.042, 0.208, 0, math.pi/2, 0) # in meters and radians 0.038
pose_home = PoseObject(0.115, 0.0, 0.215, 0, 1.5, 0)

#robot.move_pose(pickup2_location)
robot.setup_electromagnet(pin_electromagnet)
robot.activate_electromagnet(pin_electromagnet)
#robot.deactivate_electromagnet(pin_electromagnet)
#robot.move_pose(pose_home)
"""