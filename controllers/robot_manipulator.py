from pyniryo import NiryoRobot, PinID, PoseObject
import utils.z_calibration as zCal
import utils.inverse_kinematics as ik

import math
class RobotManipulator:

    global pieceHeights, cruiseHeight, boardHeight, zCalibrate
    pieceHeights = {
        'p': 60/1000,
        'r': 64.5/1000,
        'n': 69/1000,
        'b': 73.5/1000,
        'q': 78/1000,
        'k': 82.5/1000
    }
    cruiseHeight = 0.2
    boardHeight = 0.0530

    zCalibrate=False
    usingIK=True

    def __init__(self,ip,boardCoords,databus):
        robot_ip=ip
        self.databus=databus
        print("MAKING MANIPULATOR")

        try:
            print("trying to connect")
            self.robot = NiryoRobot(robot_ip)
            self.databus.connectionStatus="connected"
            print("robot connected")

            self.pin_electromagnet = PinID.DO4
            self.robot.setup_electromagnet(self.pin_electromagnet)

            self.robot.calibrate_auto()
            print("robot calibrated")
            if zCalibrate:
                self.robotCalibration = zCal.ZCalibration(self.robot)
            self.home = []
            print("trying ik")
            if self.usingIK:
                self.home = [0.1343, 0, 0.1652]
                ik.calculateIK(self.robot, *self.home)
            else:
                self.home = PoseObject(0.1343, 0, 0.1652, 0, 1, 0)
                self.robot.move_pose(self.home)
            print("robot calculated")
            self.databus.homedStatus="Homed"
            self.databus.magnetStatus = "Off"
            self.databus.movementStatus = "Idle"

        except:
            print("robot failed to connect")
            self.robot = None


        self.boardMap,self.storageMap,self.storageOccupancy=self.init_maps(boardCoords)

    def pickup(self,piece):
        if self.robot is not None:
            #lower
            self.databus.movementStatus="Moving"
            pose = self.robot.get_pose()
            #print(self.robotCalibration.getZBaseline(pose.x,pose.y))
            z=self.robotCalibration.getZBaseline(pose.x,pose.y) if zCalibrate==True else boardHeight
            if self.usingIK:
                move=[pose.x,pose.y,z+pieceHeights[piece.lower()]]
                print("picking up")
                ik.calculateIK(self.robot,*move)
            else:
                move = PoseObject(pose.x,pose.y,z+pieceHeights[piece.lower()],0,math.pi/2,0)
                self.robot.move_pose(move)

            self.robot.activate_electromagnet(self.pin_electromagnet)
            self.databus.magnetStatus="On"

            #raise
            if self.usingIK:
                ik.calculateIK(self.robot, pose.x,pose.y,pose.z)
            else:
                self.robot.move_pose(pose)

    def place(self,piece="p"):
        if self.robot is not None:
            # lower
            self.databus.movementStatus = "Moving"
            pose = self.robot.get_pose()
            z = self.robotCalibration.getZBaseline(pose.x, pose.y) if zCalibrate == True else boardHeight
            if self.usingIK:
                move = [pose.x, pose.y, z+pieceHeights[piece.lower()]]
                print("placing")
                ik.calculateIK(self.robot,*move)
            else:
                move= PoseObject(pose.x, pose.y, z+pieceHeights[piece.lower()], 0, math.pi/2, 0)
                self.robot.move_pose(move)

            self.robot.deactivate_electromagnet(self.pin_electromagnet)
            self.databus.magnetStatus = "Off"

            # raise
            if self.usingIK:
                ik.calculateIK(self.robot, pose.x,pose.y,pose.z)
            else:
                self.robot.move_pose(pose)

    def move(self, x, y, z=cruiseHeight):
        if self.robot is not None:
            self.databus.homedStatus = "Not Homed"
            self.databus.movementStatus = "Moving"
            x=x/1000
            y=y/1000
            if self.usingIK:
                move=[x, y, z]
                print("moving")
                ik.calculateIK(self.robot,*move)
            else:
                move= PoseObject(x, y, z, 0, math.pi/2, 0)
                self.robot.move_pose(move)

    def return_home(self):
        if self.robot is not None:
            if self.usingIK:
                ik.calculateIK(self.robot, self.home[0], self.home[1], self.home[2])
            else:
                self.robot.move_pose(self.home)
            self.databus.movementStatus = "Idle"
            self.databus.homedStatus = "Homed"

#______________________________________________________________________


    def init_board_map(self,startPos,offsetX,offsetY):
        boardMap={}
        for rank in range(8):
            for file in range(8):
                square=chr(ord("a")+file)+str(rank+1)
                boardMap[square]=(startPos[0]-offsetX*rank,startPos[1]+offsetY*file)

        return boardMap

    def init_storage_map(self,whiteStartPos,blackStartPos,offset):
        storageMap={}
        layout={
            'p' : [(0,i) for i in range(8)],
            'r' : [(1,0),(1,1),(2,0),(2,1)],
            'n' : [(1,2),(1,3),(2,2),(2,3)],
            'b' : [(1,4),(1,5),(2,4),(2,5)],
            'q' : [(1,7),(2,6),(2,7)],
            'k' : [(1,6)]
        }

        for piece in layout:
            # iterate through piece positions
            # apply offset between grid squares
            # append to list in dictionary

            #white
            storageMap[piece.upper()]=[]
            for pos in layout[piece]:
                x=pos[0]*offset+whiteStartPos[0]
                y=pos[1]*offset+whiteStartPos[1]
                storageMap[piece.upper()].append((x,y))

            #black
            #todo potentially need to flip black but thats a later problem
            storageMap[piece]=[]
            for pos in layout[piece]:
                x=pos[0]*offset+blackStartPos[0]
                y=pos[1]*offset+blackStartPos[1]
                storageMap[piece].append((x,y))
        return storageMap

    def init_storage_occupancy(self,storageMap,mode="standard"):
        # True = Occupied
        # False = Free
        standardCounts={
            'P': 8, 'p' : 8,
            'R': 2, 'r' : 2,
            'N': 2, 'n' : 2,
            'B': 2, 'b' : 2,
            'Q': 1, 'q' : 1,
            'K': 1, 'k' : 1
        }
        #todo read board and manually count instead of hard code

        storageOccupancy={}
        for pieceType in storageMap:
            storageOccupancy[pieceType]=[]
            totalSlots = len(storageMap[pieceType])
            onBoard=standardCounts[pieceType]
            for i in range(totalSlots):
                if mode=="standard":
                    storageOccupancy[pieceType].append(i>onBoard)
                else:
                    storageOccupancy[pieceType].append(True)
        return storageOccupancy

    def init_maps(self,boardCoords):
        board_map=self.init_board_map(boardCoords["boardStart"],boardCoords["xOffset"],boardCoords["yOffset"])
        storage_map=self.init_storage_map(boardCoords["whiteStorageStart"],boardCoords["blackStorageStart"],boardCoords["storageOffset"])
        storageOccupancy=self.init_storage_occupancy(storage_map)

        return board_map, storage_map, storageOccupancy