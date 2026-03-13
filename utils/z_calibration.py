from pyniryo import *
import numpy as np

forceSensor = PinID.AI1

class ZCalibration:
    def __init__(self, robot):
        self.plane1 = []
        self.plane2 = []
        self.midpoint = [0,0]
        self.start(robot)
        robot.deactivate_electromagnet(forceSensor)

    #pass in robot maybe? unsure what's needed to move the arm
    def start(self, robot):
        "going to create 2 planes that split the chessboard along the middle and use them to set the baseline for z"
        zArray = []
        xyArray = [[0.125,-0.114],[0.130,0.134],[0.257,-0.123],[0.257,0.126],[0.4047, -0.1293],[0.4059, 0.1335]] #coordinates that check the back left, back right, middle left, middle right, front left, front right of the board
        self.midpoint = [(xyArray[2][0]+xyArray[3][0])/2, (xyArray[2][1]+xyArray[3][1])/2] #find the midpoint to use as the point to split the planes
        for i in range(len(xyArray)):
            "move through the different x,y coordinates and find the z value for each one to create a plane"
            pose_target_obj = PoseObject(xyArray[i][0], xyArray[i][1], 0.13, 0, np.pi/2, 0) # in meters and radians
            robot.move_pose(pose_target_obj)
            z = 0.054
            while(robot.analog_read(forceSensor)<1.9): #move arm down
                pose_target_obj = PoseObject(xyArray[i][0], xyArray[i][1], z, 0, np.pi/2, 0) # in meters and radians
                robot.move_pose(pose_target_obj)
                z = z-0.001
                #print(robot.analog_read(forceSensor))
            print(robot.get_pose())
            zArray.append(robot.get_pose().z)
            pose_target_obj = PoseObject(xyArray[i][0], xyArray[i][1], 0.130, 0, np.pi/2, 0) # in meters and radians
            robot.move_pose(pose_target_obj)
            #robot.clear_collision_detected()
        print("zArray :" + str(zArray))
        self.plane1 = self.createPlane(xyArray[:4], zArray[:4])
        print("plane1: " + str(self.plane1) + " inserted coords: " + str(xyArray[:4]))
        self.plane2 = self.createPlane(xyArray[2:], zArray[2:])
        print("plane2: " + str(self.plane2) + " inserted coords: " + str(xyArray[2:]))

    def createPlane(self, xyPassed, zPassed):
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
        d = -(Vt[2][0]*xMean + Vt[2][1]*yMean + Vt[2][2]*zMean)
        return [Vt[2][0], Vt[2][1], Vt[2][2], d] # stored in the form [a,b,c,d] where ax + by + cz + d = 0 describes a plane

    def getZBaseline(self, x,y):
        "input an x,y coordinate and return the z coordinate from the plane"
        #if(x<self.midpoint[0]):
        return ((-self.plane1[0]*x - self.plane1[1]*y - self.plane1[3])/self.plane1[2])
        #return ((-self.plane2[0]*x - self.plane2[1]*y - self.plane2[3])/self.plane2[2])

if __name__ == "__main__":
    robotIpAddress = "192.168.42.2"
    robot = NiryoRobot(robotIpAddress)
    robot.calibrate_auto()
    robotCalibration = ZCalibration(robot)
    print("z position 0f 0.400,0 :" + str(robotCalibration.getZBaseline(0.400, 0)))