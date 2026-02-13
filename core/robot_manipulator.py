from pyniryo import NiryoRobot, PinID, PoseObject

class RobotManipulator:
    def __init__(self,ip="10.10.10.10"):

        robot_ip=ip

        self.robot = NiryoRobot(robot_ip)
        print("robot connected connected")

        self.pin_electromagnet = PinID.DO4
        self.robot.setup_electromagnet(self.pin_electromagnet)

        self.robot.calibrate_auto()
        print("robot calibrated")

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