from pyniryo import *
import numpy as np
plane1 = []
plane2 = []
midpoint = [0,0]

#pass in robot maybe? unsure what's needed to move the arm
def start():
    "going to create 2 planes that split the chessboard along the middle and use them to set the baseline for z"
    zArray = []
    xyArray = [[125,-114],[130,134],[257,-123],[257,126],[416,-137],[418,-152]] #coordinates that check the back left, back right, middle left, middle right, front left, front right of the board
    midpoint = [(xyArray[2][0]+xyArray[3][0])/2, (xyArray[2][1]+xyArray[3][1])/2] #find the midpoint to use as the point to split the planes
    for i in range(len(xyArray)):
        "move through the different x,y coordinates and find the z value for each one to create a plane"
        z = 0.130
        while(not(robot.collision_detected())): #move arm down
            pose_target_obj = PoseObject(xyArray[i][0], xyArray[i][1], z, 0, 0.75, 0) # in meters and radians
            robot.move_pose(pose_target_obj)
            z = z-0.001
        robot.clear_collision_detected()
        zArray.append(robot.get_pose()[2])
    plane1 = createPlane(xyArray[:4], zArray[:4]) # unsure how this accessing of arrays works it autofilled
    print("plane1: " + str(plane1) + " inserted coords: " + str(xyArray[:4]))
    plane2 = createPlane(xyArray[2:], zArray[2:]) # unsure how this accessing of arrays works it autofilled
    print("plane2: " + str(plane2) + " inserted coords: " + str(xyArray[2:]))

def createPlane(xyPassed, zPassed):
    xMean = 0
    yMean = 0
    zMean = 0
    size = len(xyPassed)
    for i in range(size):
        xMean = xMean + xyPassed[i][0]
        yMean = yMean + xyPassed[i][1]
        zMean = zMean + zPassed[i]
    xMean = xMean/size
    yMean = yMean/size
    zMean = zMean/size
    A = []
    for i in range(size):
        Pi = (xyPassed[i][0] - xMean, xyPassed[i][1] - yMean, zPassed[i] - zMean)
        A.append(Pi)
    U, S, Vt = np.linalg.svd(A)
    print(Vt)
    d = -(Vt[2][0]*xMean + Vt[2][1]*yMean + Vt[2][2]*zMean)
    return (Vt[2][0], Vt[2][1], Vt[2][2], d) # stored in the form [a,b,c,d] where ax + by + cz + d = 0 describes a plane 
        
def getZBaseline(x,y):
    "input an x,y coordinate and return the z coordinate from the plane" 
    if(x<midpoint[0]):
        return ((-plane1[0]*x - plane1[1]*y - plane1[3])/plane1[2])
    return ((-plane2[0]*x - plane2[1]*y - plane2[3])/plane2[2])

robotIpAddress = "10.10.10.10"
robot = NiryoRobot(robotIpAddress)
pin_electromagnet = PinID.DO4
robot.calibrate_auto()
start()
getZBaseline(150, 0)