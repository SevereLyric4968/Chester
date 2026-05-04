from pyniryo import NiryoRobot, PinID, PoseObject
import utils.z_calibration as zCal
import utils.inverse_kinematics as ik

import math

from testbed.intelligent_pickup import IntelligentPickupSystem

class RobotManipulator:

    global pieceHeights, cruiseHeight, boardHeight, zCalibrate,usingIK
    pieceHeights = {
        #heights needed for custom kinematics
        'p': 56/1000,
        'r': 62/1000,
        'n': 66/1000,
        'b': 71/1000,
        'q': 77/1000,
        'k': 77/1000
        #actual heights
        #'p': 60/1000,
        #'r': 64.5/1000,
        #'n': 69/1000,
        #'b': 73.5/1000,
        #'q': 78/1000,
        #'k': 82.5/1000
    }

    zCalibrate=False
    usingIK=True

    """if usingIK:
        getPose="ik.getFK(self.robot)"
        moveTo="ik.calculateIK(self.robot,pose)"
    else:
        getPose="self.robot.get_pose"
        moveTo="self.robot.move_pose(pose)"""

    #useIntelligentPickup=False


    def __init__(self,ip,databus,useIntelligentPickup=False):
        print("Initializing RobotManipulator")

        robot_ip=ip
        self.databus=databus
        self.intelligent_system = None
        self.last_target_pose = None
        self.useIntelligentPickup=useIntelligentPickup

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

            if usingIK:
                self.home=(0.014421, -0.09438,0.16172)
                print("l")
                ik.calculateIK(self.robot, *self.home)
                print("wasnt sam")
            else:
                self.home = PoseObject(0.0023, -0.1335, 0.2, 0, math.pi / 2, 0)
                self.robot.move_pose(self.home)
            
            self.databus.homedStatus="Homed"
            self.databus.magnetStatus = "Off"
            self.databus.movementStatus = "Idle"

            if self.useIntelligentPickup:
                self.intelligent_system = IntelligentPickupSystem.create(
                    self.robot,
                    pin_electromagnet=self.pin_electromagnet,
                    detector_show=True,
                    detector_min_area_px=400,
                )
                
            else:
                self.intelligent_system = None
            print("robot manipulator initialised")
        except Exception as e:
            print(e)
            print("robot manipulator initialization failed")
            self.robot = None

    def pickup(self, piece,z):
        if self.robot is None:
            return

        self.databus.movementStatus = "Moving"

        if not self.useIntelligentPickup or self.intelligent_system is None:
            pickZ=z+pieceHeights[piece.lower()]
            if usingIK:
                pose=ik.getFK(self.robot)
                target = [pose[0],pose[1],pickZ]
                ik.calculateIK(self.robot,*target)
                self.robot.activate_electromagnet(self.pin_electromagnet)
                self.databus.magnetStatus = "On"
                ik.calculateIK(self.robot,*pose)
            else:
                pose = self.robot.get_pose()
                target = PoseObject(pose.x, pose.y, pickZ, 0, math.pi / 2, 0)
                self.robot.move_pose(target)
                self.robot.activate_electromagnet(self.pin_electromagnet)
                self.databus.magnetStatus = "On"
                self.robot.move_pose(pose)
            return

        result = self.intelligent_system.pickup_piece(
            piece=piece,
            pickup_z=z,
            approximate_pose=self.robot.get_pose(),
        )

        if not result.success:
            raise RuntimeError(f"centering failed: {result.last_error_px}")

        self.databus.magnetStatus = "On"

    def place(self,piece, z):
        if self.robot is not None:
            placeZ=z+pieceHeights[piece.lower()]+0.002
            # lower
            self.databus.movementStatus = "Moving"
            pose = self.robot.get_pose()
            #z = self.robotCalibration.getZBaseline(pose.x, pose.y) if zCalibrate == True else boardHeight
            if usingIK:
                pose=ik.getFK(self.robot)
                move = [pose[0], pose[1], z+pieceHeights[piece.lower()], 0, math.pi/2, 0]
                ik.calculateIK(self.robot,*move)
            else:
                move=PoseObject(pose.x, pose.y, placeZ, 0, math.pi/2, 0)
                self.robot.move_pose(move)

            self.robot.deactivate_electromagnet(self.pin_electromagnet)
            self.databus.magnetStatus = "Off"

            # raise
            if usingIK:
                ik.calculateIK(self.robot, *pose)
            else:
                self.robot.move_pose(pose)

    def move(self, x, y, z=0.208):
        if self.robot is not None:
            self.databus.homedStatus = "Not Homed"
            self.databus.movementStatus = "Moving"
            print("tryna move")
            print("x =",x)
            print("y =",y)
            print("z =",z)

            if usingIK:
                move=[x, y, z, 0, math.pi/2, 0]
                ik.calculateIK(self.robot,*move)
            else:
                move=PoseObject(x, y, z, 0, math.pi/2, 0)
                self.robot.move_pose(move)

    def return_home(self):
        if self.robot is not None:
            print("trying")
            if usingIK:
                ik.calculateIK(self.robot, self.home[0], self.home[1], self.home[2])
            else:
                self.robot.move_pose(self.home)
            print("great success")
            self.databus.movementStatus = "Idle"
            self.databus.homedStatus = "Homed"