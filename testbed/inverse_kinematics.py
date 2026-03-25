#this implemenation of inverse kinematics will be calculated using kinematic decoupling.
#the hope is that it will be as fast as the already implemented IKFast inverse kinematics but will be more accurate and precise.
from pyniryo import *
import numpy as np

#want to take in the desired end effector pose and calculate the joint angles needed to achieve that pose.
"""class poseIK:
    def __init__(self, robot): #the desired end effector position in meters and radians
        self.robot = robot
"""
def calculateIK(robot, x, y, z, roll, pitch, yaw):
    calculateIK(robot, x, y, z) #roll pitch yaw are not needed 

def calculateIK(robot, x, y, z):
    heightOfEndEffector = 0.116 #need to check this value
    z = z - heightOfEndEffector #add the height of the end effector to get the position of the tip of the end effector (able to make this assumion because the end effector is always pointed down)
    x -= 0.0456
    y -= 0.0094
    z -= 0.0174
    #joint limits in radians -2,949 ≤ Joint 1 ≤ 2,949, -1,83 ≤ Joint 2 ≤ 0,61, -1.34 ≤ Joint 3 ≤ 1,57, -2,089 ≤ Joint 4 ≤ 2,089, -1,919 ≤ Joint 5 ≤ 1.922, -2,53 ≤ Joint 6 ≤ 2,53
    motorOneAngle = (np.arctan2(y,x))
    print(motorOneAngle)
    a = np.sqrt(pow(x,2)+pow(y,2))
    h=np.sqrt(pow(a,2)+pow(z,2))
    d1 = 0.221
    d2 = 0.235
    theta2 = np.arccos((pow(d1,2)+pow(d2,2)-pow(h,2))/(2*d1*d2))
    phi = np.arcsin(d2*(np.sin(theta2)/h))
    lamda = np.arctan2(z,a)
    theta1 = lamda + phi
    motorTwoAngle = -(np.pi/2 - theta1)
    motorThreeAngle = -(np.pi/2 - theta2)
    motorFourAngle = 0
    psi = np.pi/2 - lamda
    zeta = np.pi - (theta2 + phi)
    theta3 = psi + zeta
    motorFiveAngle = -(np.pi - theta3)
    motorSixAngle = 0
    print(motorOneAngle, motorTwoAngle, motorThreeAngle, motorFourAngle, motorFiveAngle, motorSixAngle)
    robot.move_joints(motorOneAngle, motorTwoAngle, motorThreeAngle, motorFourAngle, motorFiveAngle, motorSixAngle)

if __name__ == "__main__":
    robotIpAddress = "192.168.42.2"
    robot = NiryoRobot(robotIpAddress)
    robot.calibrate_auto()
    #robot.move_joints(0.3,0,0,0,0,0)
    calculateIK(robot, 0.2832, 0.0393, 0.140)

    #x = 0.3543, y = 0.0524, z = 0.1354 roll = -2.161, pitch = 1.569, yaw = -2.204
    #x = 0.2098, y = 0.0433, z = 0.1357 roll = 3.054, pitch = 1.569, yaw = 2.889
    #x = 0.2554, y = 0.0527, z = 0.1531 roll = 2.011, pitch = 1.570, yaw = 2.211
    #x = 0.2832, y = 0.0393, z = 0.1355 roll = 1.974, pitch = 1.570, yaw = 1.923


#x = 0.0456, y = 0.0094, z = 0.0174

