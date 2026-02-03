from pyniryo import *

robotIpAddress = "192.168.42.1"
robot2IpAddress = "192.168.42.2" #this for ethernet use a laptop with IP address 192.168.42.100
print("a")


robot = NiryoRobot(robotIpAddress)
robot2 = NiryoRobot(robot2IpAddress)
print("b")

robot.calibrate_auto()
robot2.calibrate_auto()

print("d")
pose_target_obj = PoseObject(0.2, 0, 0.2, 0, 0.75, 0) # in meters and radians
robot.move_pose(pose_target_obj)


#robot 2 movement
print("e")
pose_target_obj2 = PoseObject(0.2, 0, 0.2, 0, 0.75, 0) # in meters and radians
robot2.move_pose(pose_target_obj2)

pose_home = PoseObject(0.14, 0, 0.2, 0, 0.75, 0)
robot.move_pose(pose_home)
robot2.move_pose(pose_home)
