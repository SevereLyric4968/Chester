from pyniryo import *
import numpy as np
import math

robotIpAddress = "192.168.42.1"
robot = NiryoRobot(robotIpAddress)
robot.calibrate_auto()
pin_electromagnet = PinID.DO4

#(0.203, -0.339, 0.027, 0, 1.5, 0) robot
#(0.2, 0.3, 0.038, 0, 1.5, 0) robot2
#test both at 0.038 for calibration start

def _with_z(pose: PoseObject, z: float) -> PoseObject:
        return PoseObject(pose.x, pose.y, z, pose.roll, pose.pitch, pose.yaw)

pickup2_location = PoseObject(0.23,  -0.02, 0.208, 0, math.pi/2, 0) # in meters and radians 0.038
pose_home = PoseObject(0.115, 0.0, 0.215, 0, 1.5, 0) #0.115, 0.0, 0.215, 0, 1.5, 0
approach_z = float(pickup2_location.z)

rook_z = approach_z - 0.048                                 #0.098 - 0.050 = 0.048
bishop_z = approach_z - 0.089                               #0.089 - 0.050 = 0.039
pawn_z = approach_z - 0.102                                 #0.102 - 0.050 = 0.052  
knight_z = approach_z - 0.04 #dont have yet
queen_z = approach_z - 0.086                                #0.086 - 0.050 = 0.036
king_z = approach_z - 0.04 #dont have yet



rook = _with_z(pickup2_location, rook_z)
bishop = _with_z(pickup2_location, bishop_z)
pawn = _with_z(pickup2_location, pawn_z)
knight = _with_z(pickup2_location, knight_z)
queen = _with_z(pickup2_location, queen_z)
king = _with_z(pickup2_location, king_z)




#robot.move_pose(pickup2_location)

#robot.move_pose(rook)
#robot.move_pose(bishop)
#robot.move_pose(pawn)
#robot.move_pose(knight)
#robot.move_pose(queen)
#robot.move_pose(king)
robot.setup_electromagnet(pin_electromagnet)
robot.activate_electromagnet(pin_electromagnet)
robot.deactivate_electromagnet(pin_electromagnet)
#robot.move_pose(pickup2_location)

robot.move_pose(pose_home)
