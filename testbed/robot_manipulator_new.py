from pyniryo import NiryoRobot, PinID, PoseObject
from testbed.intelligent_pickup import CenteringConfig,IntelligentPickupSystem

import math

class RobotManipulator:
    global pieceHeights
    pieceHeights = {
        'p': 60 / 1000,
        'r': 64.5 / 1000,
        'n': 69 / 1000,
        'b': 73.5 / 1000,
        'q': 78 / 1000,
        'k': 82.5 / 1000
    }

    def __init__(self, ip, databus):

        print("Initializing RobotManipulator")

        robot_ip = ip

        self.databus = databus

        self.usingIntelligentPickup=False

        try:
            print("trying to connect")
            self.robot = NiryoRobot(robot_ip)
            self.databus.connectionStatus = "connected"
            print("robot connected")

            self.pin_electromagnet = PinID.DO4
            self.robot.setup_electromagnet(self.pin_electromagnet)

            self.robot.calibrate_auto()
            print("robot calibrated")

            self.return_home()

            self.databus.homedStatus = "Homed"
            self.databus.magnetStatus = "Off"
            self.databus.movementStatus = "Idle"

            print("robot manipulator initialised")

        except Exception as e:
            print(e)
            print("robot manipulator initialization failed")
            self.robot = None

    def move(self, x, y, z=0.208):
        if self.robot is None:
            return

        self.databus.homedStatus = "Not Homed"
        self.databus.movementStatus = "Moving"

        move = PoseObject(x, y, z, 0, math.pi / 2, 0)
        self.robot.move_pose(move)
        self.databus.homedStatus = "Idle"

    def return_home(self):
        if self.robot is None:
            return
        home = PoseObject()
        self.robot.move_pose(home)
        self.databus.homedStatus = "Homed"
        self.databus.movementStatus = "Idle"

    def pickup(self, piece, z):
        if self.robot is None:
            return

        if self.usingIntelligentPickup:
            result = self.intelligent_system.pickup_piece(
                piece=piece,
                pickup_z=z,
                approximate_pose=self.robot.get_pose(),
            )

            if not result.success:
                raise RuntimeError(f"centering failed: {result.last_error_px}")
            return

        targetZ = z + pieceHeights[piece.lower()]
        self.lower(targetZ)

    def place(self, piece, z):
        if self.robot is None:
            return

        targetZ = z + pieceHeights[piece.lower()]
        self.lower(targetZ)

    def lower(self,targetZ):
        preDropPose = self.robot.get_pose()
        targetPose = PoseObject(preDropPose.x, preDropPose.y, targetZ, 0, math.pi / 2, 0)

        self.databus.movementStatus = "Moving"
        self.robot.move_pose(targetPose)
        self.toggle_magnet()
        self.robot.move_pose(preDropPose)
        self.databus.movementStatus = "Idle"

    def toggle_magnet(self):
        if self.databus.magnetStatus == "On":
            self.robot.deactivate_electromagnet(self.pin_electromagnet)
            self.databus.magnetStatus = "Off"
        else:
            self.robot.activate_electromagnet(self.pin_electromagnet)
            self.databus.magnetStatus = "On"