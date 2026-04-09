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
    print("starting")
    print("x ", x, "y", y,"z ", z)
    d1 = 0.221 #length of first section of arm
    d2 = 0.235 #length of second section of arm
    #0.075 for end effector
    d3 = 0.075-0.1715 #roughly the height of the end effector minus the height of the first joint
    z = z + d3 #add the height of the end effector to get the position of the tip of the end effector (able to make this assumion because the end effector is always pointed down)
    #joint limits in radians -2,949 ≤ Joint 1 ≤ 2,949, -1,83 ≤ Joint 2 ≤ 0,61, -1.34 ≤ Joint 3 ≤ 1,57, -2,089 ≤ Joint 4 ≤ 2,089, -1,919 ≤ Joint 5 ≤ 1.922, -2,53 ≤ Joint 6 ≤ 2,53
    print("m1 try")
    motorOneAngle = (np.arctan2(y,x))
    print("m1 got")
    print("m2 try")
    a = np.sqrt((x**2)+(y**2))
    h=np.sqrt((a**2)+(z**2))
    theta2 = np.arccos(((d1**2)+(d2**2)-(h**2))/(2*d1*d2))
    phi = np.arccos((d1**2+h**2-d2**2)/(2*d1*h))
    print("maffs")
    lamda = np.arctan2(z,a)
    theta1 = lamda + phi
    motorTwoAngle = -(np.pi/2 - theta1)
    print("m2 got")
    motorThreeAngle = -(np.pi/2 - theta2)
    print("m3 got")
    motorFourAngle = 0
    psi = np.pi/2 - lamda
    zeta = np.pi - (theta2 + phi)
    theta3 = psi + zeta
    motorFiveAngle = -(np.pi - theta3)
    motorSixAngle = motorOneAngle
    print(motorOneAngle, motorTwoAngle, motorThreeAngle, motorFourAngle, motorFiveAngle, motorSixAngle)
    if(np.isnan(angle) for angle in [motorOneAngle, motorTwoAngle, motorThreeAngle, motorFourAngle, motorFiveAngle, motorSixAngle]):
        print("point too far for arm to reach")
        return
    if(-2.949 > motorOneAngle > 2.949 or -1.83 > motorTwoAngle > 0.61 or -1.34 > motorThreeAngle > 1.57 or -2.089 > motorFourAngle > 2.089 or -1.919 > motorFiveAngle > 1.922 or -2.53 > motorSixAngle > 2.53):
        print("calculated angles are out of bounds")
        return
    robot.move_joints(motorOneAngle, motorTwoAngle, motorThreeAngle, motorFourAngle, motorFiveAngle, motorSixAngle)

def getFK(robot):
    j1, j2, j3, j4, j5, j6 = robot.get_joints()
    baseHeight = 0.1715
    d1 = 0.221 #length of first section of arm
    d2 = 0.235 #length of second section of arm
    #0.075 for end effector
    d3 = 0.075
    z = baseHeight + d1*np.sin(np.pi/2 + j2) + d2*np.cos(np.pi/2-(j3+j2)) + d3*np.cos(np.pi/2-(j3+j2)-j5)
    h = d1*np.cos(np.pi/2 + j2) + d2*np.sin(np.pi/2-(j3+j2))
    x = h*np.cos(j1)
    y = h*np.sin(j1)
    print("x ", x, "y", y,"z ", z)
    return (x,y,z)

if __name__ == "__main__":
    robotIpAddress = "192.168.42.1"
    robot = NiryoRobot(robotIpAddress)
    robot.calibrate_auto()
    #robot.move_joints(0,0,0,0,0,0)
    calculateIK(robot, 0.0001,0.0001,0.0975) #warped bottom left
    #getFK(robot)
    #print(robot.get_pose())
    #calculateIK(robot,0.353, 0.087, 0.09) #warped top right

    # A1 (0.353, -0.116, 0.055)  #old board 0.307, 0.095, 0.045
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