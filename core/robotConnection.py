from pyniryo import *
# "pip install "pyniryo<1.2"" <- this fixed it
robotIpAddress = "10.10.10.10" #this for hotspot - may update when robot cooperates
robot2IpAddress = "192.168.42.1" #this for ethernet
print("a")

print("b")
robot = NiryoRobot(robotIpAddress)
robot2 = NiryoRobot(robot2IpAddress)

print("c")
robot.calibrate_auto()
robot2.calibrate_auto()
print("d")
pose_target_obj = PoseObject(0.14, 0, 0.2, 0, 0.75, 0) # in meters and radians
robot.move_pose(pose_target_obj)
robot2.move_pose(pose_target_obj)
print("e")
#robot.move_to_home_pose

#test