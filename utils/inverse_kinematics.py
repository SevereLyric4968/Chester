#this implemenation of inverse kinematics will be calculated using kinematic decoupling.
#the hope is that it will be as fast as the already implemented IKFast inverse kinematics but will be more accurate and precise.
from pyniryo import *
import numpy as np

#want to take in the desired end effector pose and calculate the joint angles needed to achieve that pose.
"""class poseIK:
    def __init__(self, robot): #the desired end effector position in meters and radians
        self.robot = robot
"""
def calculateIK(robot, x, y, z, *args):
    print("x ", x, "y", y,"z ", z)
    d1 = 0.221 #length of first section of arm
    d2 = 0.235 #length of second section of arm
    #0.075 for end effector
    d3 = 0.075-0.1715 #roughly the height of the end effector minus the height of the first joint
    z = z + d3 #add the height of the end effector to get the position of the tip of the end effector (able to make this assumion because the end effector is always pointed down)
    #joint limits in radians -2,949 ≤ Joint 1 ≤ 2,949, -1,83 ≤ Joint 2 ≤ 0,61, -1.34 ≤ Joint 3 ≤ 1,57, -2,089 ≤ Joint 4 ≤ 2,089, -1,919 ≤ Joint 5 ≤ 1.922, -2,53 ≤ Joint 6 ≤ 2,53
    motorOneAngle = (np.arctan2(y,x))
    a = np.sqrt((x**2)+(y**2))
    h=np.sqrt((a**2)+(z**2))
    theta2 = np.arccos(((d1**2)+(d2**2)-(h**2))/(2*d1*d2))
    phi = np.arccos((d1**2 + h**2 - d2**2) / (2 * d1 * h))
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
    #print(motorOneAngle, motorTwoAngle, motorThreeAngle, motorFourAngle, motorFiveAngle, motorSixAngle)
    robot.move_joints(motorOneAngle, motorTwoAngle, motorThreeAngle, motorFourAngle, motorFiveAngle, motorSixAngle)

if __name__ == "__main__":
    robotIpAddress = "10.10.10.10"
    robot = NiryoRobot(robotIpAddress)
    robot.calibrate_auto()
    #robot.move_joints(0,0,0,0,0,0)
    calculateIK(robot, 0.1, 0.095, 0.045) #warped bottom left
    print(robot.get_pose())
    #calculateIK(robot,0.353, 0.087, 0.09) #warped top right
    #z = 0.1715
    #calculateIK(robot, 0.3142,0.05, z)
    #for i in range(3): #draw square at different heights
    #    calculateIK(robot, 0.3142,0.05, z)
    #    calculateIK(robot, 0.3142,-0.05, z)
    #    calculateIK(robot, 0.2,-0.05, z)
    #    calculateIK(robot, 0.2,0.05, z)
    #    calculateIK(robot, 0.3142,0.05, z)
    #    z = z-(0.07/(i+1))

    # A1 (0.353, -0.116)  #old board 0.307, 0.095, 0.045
    # B2 (0.35,0.0921)
    # C3 (0.3148,0.1)
    # D4 (0.3851,0.1270)
    # E5 (0.3851,0.1270)
    # F6 (0.3851,0.1270)
    # G7 (0.3851,0.1270)
    # H8 (0.1, 0.087)



#x = 0.0456, y = 0.0094, z = 0.0174

#small square
#x = 0.3142, y = -0.0499
#x = 0.2080, y = 0.0545