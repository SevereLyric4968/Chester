from pyniryo import NiryoRobot, PinID, PoseObject



#from main import load_config


class RobotManipulator:
    def __init__(self):
        #config = load_config()

        #robot_1_ip=config["robot_1_ip"]
        robot_1_ip="10.10.10.10"
        #robot_2_ip=config["robot_2_ip"]

        self.robot1 = NiryoRobot(robot_1_ip)
        print("robot 1 connected")
        #robot2 = NiryoRobot(robot_2_ip)
        #print("robot 2 connected")

        self.pin_electromagnet = PinID.DO4
        self.robot1.setup_electromagnet(self.pin_electromagnet)
        #robot2.setup_electromagnet(pin_electromagnet)

        self.robot1.calibrate_auto()
        print("robot 1 calibrated")
        #robot2.calibrate_auto()
        #print("robot 2 calibrated")

    def pickup(self,deltaZ=-0.1475):
        #lower
        pose = self.robot1.get_pose()
        move=PoseObject(pose.x,pose.y,pose.z+deltaZ,0,3.14/2,0)
        self.robot1.move_pose(move)

        self.robot1.activate_electromagnet(self.pin_electromagnet)

        #raise
        self.robot1.move_pose(pose)

    def place(self,deltaZ=-0.1475):
        # lower
        pose = self.robot1.get_pose()
        move = PoseObject(pose.x, pose.y, pose.z + deltaZ, 0, 3.14 / 2, 0)
        self.robot1.move_pose(move)

        self.robot1.deactivate_electromagnet(self.pin_electromagnet)

        # raise
        self.robot1.move_pose(pose)

    def move(self,x,y,z=0.2):
        x=x/1000
        y=y/1000
        print("moving")
        move=PoseObject(x, y, z, 0, 3.14/2, 0)
        self.robot1.move_pose(move)