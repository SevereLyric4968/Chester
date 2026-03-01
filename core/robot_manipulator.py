from pyniryo import NiryoRobot, PinID, PoseObject

class RobotManipulator:
    def __init__(self,ip,boardCoords):

        robot_ip=ip

        self.robot = NiryoRobot(robot_ip)
        print("robot connected connected")

        self.pin_electromagnet = PinID.DO4
        self.robot.setup_electromagnet(self.pin_electromagnet)

        self.robot.calibrate_auto()
        print("robot calibrated")


        self.boardMap,self.storageMap,self.storageOccupancy=self.init_maps(boardCoords)

    def pickup(self,deltaZ=-0.1475):
        #lower
        pose = self.robot.get_pose()
        move=PoseObject(pose.x,pose.y,pose.z+deltaZ,0,3.14/2,0)
        self.robot.move_pose(move)

        self.robot.activate_electromagnet(self.pin_electromagnet)

        #raise
        self.robot.move_pose(pose)

    def place(self,deltaZ=-0.1475):
        # lower
        pose = self.robot.get_pose()
        move = PoseObject(pose.x, pose.y, pose.z + deltaZ, 0, 3.14 / 2, 0)
        self.robot.move_pose(move)

        self.robot.deactivate_electromagnet(self.pin_electromagnet)

        # raise
        self.robot.move_pose(pose)

    def move(self,x,y,z=0.2):
        x=x/1000
        y=y/1000
        print("moving")
        move=PoseObject(x, y, z, 0, 3.14/2, 0)
        self.robot.move_pose(move)

    def return_home(self):
        self.robot.move_to_home_pose()


#______________________________________________________________________


    def init_board_map(self,startPos,offset):
        boardMap={}
        for rank in range(8):
            for file in range(8):
                square=chr(ord("a")+file)+str(rank+1)
                boardMap[square]=(startPos[0]-offset*rank,startPos[1]+offset*file)

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
        board_map=self.init_board_map(boardCoords["boardStart"],boardCoords["boardOffset"])
        storage_map=self.init_storage_map(boardCoords["whiteStorageStart"],boardCoords["blackStorageStart"],boardCoords["storageOffset"])
        storageOccupancy=self.init_storage_occupancy(storage_map)

        return board_map, storage_map, storageOccupancy