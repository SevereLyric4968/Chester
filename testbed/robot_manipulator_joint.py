from pyniryo import NiryoRobot, PinID, PoseObject
import utils.inverse_kinematics as ik
from testbed.intelligent_pickup import CenteringConfig,IntelligentPickupSystem

import math

class RobotManipulator:

    def __init__(self, ip, databus, usingIK):

        print("Initializing RobotManipulator")

        robot_ip = ip

        self.databus = databus

        self.usingIK = usingIK

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

            self.home = (0,0,0)

            if usingIK:
                self.home=(0.014421, -0.09438,0.16172)
            else:
                self.home = PoseObject(0.0023, -0.1335, 0.2, 0, math.pi / 2, 0)
            self.return_home()

            self.databus.homedStatus = "Homed"
            self.databus.magnetStatus = "Off"
            self.databus.movementStatus = "Idle"

            print("robot manipulator initialised")

        except Exception as e:
            print(e)
            print("robot manipulator initialization failed")
            self.robot = None

        global pieceHeights
        if self.usingIK:
            pieceHeights = {
                'p': -8/1000, #56/1000,
                'r': -5/1000, #62/1000,
                'n': 0/1000, #66/1000,
                'b': 4/1000, #70/1000,
                'q': 8/1000, #76/1000,
                'k': 9/1000  #77/1000
            }
        else:
            pieceHeights = {
                'p': 59 / 1000, #60
                'r': 64.5 / 1000,
                'n': 67 / 1000,
                'b': 71.5 / 1000,
                'q': 78 / 1000,
                'k': 80.5 / 1000
            }

    def move(self, x, y, z=0.208):
        if self.robot is None:
            return

        self.databus.homedStatus = "Not Homed"
        self.databus.movementStatus = "Moving"

        if self.usingIK:
            ik.calculateIK(self.robot,x,y,z)
        else:
            move = PoseObject(x, y, z, 0, math.pi / 2, 0)
            self.robot.move_pose(move)

        self.databus.movementStatus = "Idle"

    def return_home(self):
        if self.robot is None:
            return

        if self.usingIK:
            ik.calculateIK(self.robot,*self.home)
        else:
            self.robot.move_pose(self.home)

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
        self.lower(targetZ, 1)

    def place(self, piece, z):
        if self.robot is None:
            return

        targetZ = z + pieceHeights[piece.lower()]
        self.lower(targetZ, 2)

    def lower(self,targetZ,increments):
        preDropX,preDropY,preDropZ = 0,0,0
        if self.usingIK:
            preDropX,preDropY,preDropZ = ik.getFK(self.robot)
        else:
            pose = self.robot.get_pose()
            preDropX,preDropY,preDropZ = pose.x, pose.y, pose.z

        self.databus.movementStatus = "Moving"
        deltaZ=preDropZ-targetZ

        for i in range(increments):
            if self.usingIK:
                ik.calculateIK(self.robot,preDropX,preDropY,preDropZ-deltaZ*(i+1)/increments)
            else:
                move = PoseObject(preDropX, preDropY, preDropZ-deltaZ*(i+1)/increments, 0, math.pi / 2, 0)
                self.robot.move_pose(move)
        self.toggle_magnet()
        if self.usingIK:
            ik.calculateIK(self.robot,preDropX,preDropY,preDropZ)
        else:
            move = PoseObject(preDropX, preDropY, preDropZ, 0, math.pi / 2, 0)
            self.robot.move_pose(move)
        self.databus.movementStatus = "Idle"

    def toggle_magnet(self):
        if self.databus.magnetStatus == "On":
            self.robot.deactivate_electromagnet(self.pin_electromagnet)
            self.databus.magnetStatus = "Off"
        else:
            self.robot.activate_electromagnet(self.pin_electromagnet)
            self.databus.magnetStatus = "On"

    def fist_bump(self):
        if self.robot is None:
            return

        unbump = [-1.5500506554354578, 0.34488448662206134, -0.9264197991304157, -0.19318892568379775, 0.3389171005329339, 0.2071800599543545]
        bump = [-1.5500506554354578, 0.055529840592425495, -0.7491711416148796, -0.14870348283511436, 0.5644122763521229, 0.18263636734818434]
        print("Fist bumping")
        self.robot.move_joints(unbump)
        self.robot.move_joints(bump)
        self.robot.move_joints(unbump)