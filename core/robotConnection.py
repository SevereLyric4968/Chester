from pyniryo import *
# "pip install "pyniryo<1.2"" <- this fixed it
robotIpAddress = "10.10.10.10"
print("a")

print("b")
robot = NiryoRobot(robotIpAddress)
print("c")
robot.calibrate_auto()
print("d")
pose_target_obj = PoseObject(0.14, 0, 0.2, 0, 0.75, 0) # in meters and radians
robot.move_pose(pose_target_obj)
print("e")
#robot.move_to_home_pose

#test