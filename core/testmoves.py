from pyniryo import *

robotIpAddress = "192.168.42.1"
robot2IpAddress = "192.168.42.2" #this for ethernet use a laptop with IP address 192.168.42.100

pin_electromagnet = PinID.DO4

robot = NiryoRobot(robotIpAddress)
robot2 = NiryoRobot(robot2IpAddress)

robot.calibrate_auto()
robot2.calibrate_auto()

#(0.203, -0.339, 0.027, 0, 1.5, 0) robot
#(0.2, 0.3, 0.038, 0, 1.5, 0) robot2
#test both at 0.038 for calibration start

pickup_location = PoseObject(0.203, -0.339, 0.027, 0, 1.5, 0) # in meters and radians 0.038
pickup2_location = PoseObject(0.2, 0.3, 0.037, 0, 1.5, 0) # in meters and radians 0.038
pose_home = PoseObject(0.14, 0, 0.2, 0, 1.5, 0)

robot.move_pose(pickup_location)
robot.setup_electromagnet(pin_electromagnet)
robot.activate_electromagnet(pin_electromagnet)
robot.move_pose(pose_home)
robot.move_pose(pickup_location)
robot.deactivate_electromagnet(pin_electromagnet)
robot.move_pose(pose_home)


robot2.move_pose(pickup2_location)
robot2.setup_electromagnet(pin_electromagnet)
robot2.activate_electromagnet(pin_electromagnet)
robot2.move_pose(pose_home)
robot2.move_pose(pickup2_location)
robot2.deactivate_electromagnet(pin_electromagnet)
robot2.move_pose(pose_home)


