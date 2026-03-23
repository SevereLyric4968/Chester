#this implemenation of inverse kinematics will be calculated using kinematic decoupling.
#the hope is that it will be as fast as the already implemented IKFast inverse kinematics but will be more accurate and precise.
from pyniryo import *
import numpy as np

#want to take in the desired end effector pose and calculate the joint angles needed to achieve that pose.
class poseIK:
    def __init__(self, x,y,z,roll,pitch,yaw): #the desired end effector position in meters and radians
        heightOfEndEffector = 0.1652 #need to check this value
        z = z + heightOfEndEffector #add the height of the end effector to get the position of the tip of the end effector (able to make this assumion because the end effector is always pointed down)
        #joint limits in radians -2,949 ≤ Joint 1 ≤ 2,949, -1,83 ≤ Joint 2 ≤ 0,61, -1.34 ≤ Joint 3 ≤ 1,57, -2,089 ≤ Joint 4 ≤ 2,089, -1,919 ≤ Joint 5 ≤ 1.922, -2,53 ≤ Joint 6 ≤ 2,53

#robot.move_joints(0,0,0,0,0,0)

if __name__ == "__main__":
    robotIpAddress = "10.10.10.10"
    robot = NiryoRobot(robotIpAddress)
    robot.calibrate_auto()
    poseIK(robot)