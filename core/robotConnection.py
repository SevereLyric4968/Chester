from pyniryo import *
# "pip install "pyniryo<1.2"" <- this fixed it
#robotIpAddress = "10.10.10.10" #this for hotspot - may update when robot cooperates
robotIpAddress = "192.168.42.1"
robot2IpAddress = "192.168.42.2" #this for ethernet use a laptop with IP address 192.168.42.100
print("a")


robot = NiryoRobot(robotIpAddress)
robot2 = NiryoRobot(robot2IpAddress)
print("b")


pin_electromagnet = PinID.DO4


print("c")
robot.calibrate_auto()
robot2.calibrate_auto()


# robot 1 movement
print("d")
#pose_target_obj = PoseObject(0.2, 0, 0.2, 0, 0.75, 0) # in meters and radians
#robot.move_pose(pose_target_obj)


#robot 2 movement
print("e")
#pose_target_obj2 = PoseObject(0.3, 0.1, 0.3, 0, 0.75, 0) # in meters and radians
#robot2.move_pose(pose_target_obj2)

#robot 1 electromagnet 
#robot.setup_electromagnet(pin_electromagnet)
#robot.activate_electromagnet(pin_electromagnet)
#robot.deactivate_electromagnet(pin_electromagnet)



#robot 2 electromagnet
#robot2.setup_electromagnet(pin_electromagnet)
#robot2.activate_electromagnet(pin_electromagnet)
#robot2.deactivate_electromagnet(pin_electromagnet)



#home position
pose_home = PoseObject(0.14, 0, 0.2, 0, 0.75, 0)
#robot.move_pose(pose_home)
#robot2.move_pose(pose_home)



#pick and place code

robot.calibrate_auto()
target_piece = PoseObject(0.2, 0, 0.2, 0, 0.75, 0) # in meters and radians
piece_destination = PoseObject(0.2, 0, 0.2, 0, 0.75, 0)

robot.setup_electromagnet(pin_electromagnet)
robot.activate_electromagnet(pin_electromagnet)

robot.move_pose(target_piece)

robot.move_pose(pose_home)

robot.move_pose(piece_destination)

robot.deactivate_electromagnet(pin_electromagnet)

robot.move_pose(pose_home)