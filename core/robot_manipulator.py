from pyniryo import NiryoRobot, PinID, PoseObject

from main import load_config


class RobotManipulator:
    def __init__(self):
        config = load_config()

        robot_1_ip,robot_2_ip=config["robot_1_ip"],config["robot_2_ip"]

        robot1 = NiryoRobot(robot_1_ip)
        print("robot 1 connected")
        robot2 = NiryoRobot(robot_2_ip)
        print("robot 2 connected")

        pin_electromagnet = PinID.DO4
        robot1.setup_electromagnet(pin_electromagnet)
        robot2.setup_electromagnet(pin_electromagnet)

        robot1.calibrate_auto()
        print("robot 1 calibrated")
        robot2.calibrate_auto()
        print("robot 2 calibrated")

    def pickup(self,robot,heightChange):
        #lower
        robot.activate_electromagnet(self.pin_electromagnet)
        #raise

    def place(self,robot,heightChange):
        # lower
        robot.deactivate_electromagnet(self.pin_electromagnet)
        # raise
    def move(self,robot,x,y,z=50):
        move=PoseObject(x, y, z, 0, 3.14/2, 0)
        robot.move_pose(move)