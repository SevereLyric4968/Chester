from pyniryo import NiryoRobot, PinID, PoseObject
import utils.z_calibration as zCal
import utils.inverse_kinematics as ik

import math

from testbed.intelligent_pickup import (
    CenteringConfig,
    IntelligentPickupSystem,
)

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
    cruiseHeight = 0.208
    boardHeight = 0.0530

    zCalibrate=False
    usingIK=False
    useIntelligentPickup=False


    def __init__(self,ip,databus):
        robot_ip=ip
        self.databus=databus
        self.intelligent_system = None
        self.last_target_pose = None

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
            
            self.home = PoseObject(0.0023, -0.1335, 0.2, 0, math.pi/2, 0)
            
            print("trying ik")

            if self.usingIK:
                ik.calculateIK(self.robot, *self.home)
            else:
                self.robot.move_pose(self.home)

            print("robot calculated")
            
            self.databus.homedStatus="Homed"
            self.databus.magnetStatus = "Off"
            self.databus.movementStatus = "Idle"

            cfg = CenteringConfig(
                deadband_px=15,
                max_step_m=0.004,
                dt_s=0.15,
                max_iters=600,
                timeout_s=59.0,
                target_offset_px=(0, -90),
                use_tracking_roi=True,
                tracking_roi_size=(260, 260),
            )

            if self.useIntelligentPickup:
                self.intelligent_system = IntelligentPickupSystem.create(
                    self.robot,
                    pin_electromagnet=self.pin_electromagnet,
                    cfg=cfg,
                    detector_show=True,
                    detector_min_area_px=400,
                )
            else:
                self.intelligent_system = None

        except:
            print("robot failed to connect")
            self.robot = None

    def pickup(self, piece,z):
        if self.robot is None:
            return

        self.databus.movementStatus = "Moving"

        if not self.useIntelligentPickup or self.intelligent_system is None:
            pickZ=z+pieceHeights[piece.lower()]
            pose = self.robot.get_pose()
            #z = self.robotCalibration.getZBaseline(pose.x, pose.y) if self.zCalibrate else self.boardHeight

            target = PoseObject(pose.x, pose.y,pickZ,0, math.pi/2, 0)

            self.robot.move_pose(target)
            self.robot.activate_electromagnet(self.pin_electromagnet)
            self.databus.magnetStatus = "On"
            self.robot.move_pose(pose)
            return

        result = self.intelligent_system.pickup_piece(
            piece=piece,
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
            if self.usingIK:
                move = [pose.x, pose.y, z+pieceHeights[piece.lower()], 0, math.pi/2, 0]
                ik.calculateIK(self.robot,*move)
            else:
                move=PoseObject(pose.x, pose.y, placeZ, 0, math.pi/2, 0)
                self.robot.move_pose(move)

            self.robot.deactivate_electromagnet(self.pin_electromagnet)
            self.databus.magnetStatus = "Off"

            # raise
            if self.usingIK:
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

            if self.usingIK:
                move=[x, y, z, 0, math.pi/2, 0]
                ik.calculateIK(self.robot,*move)
            else:
                move=PoseObject(x, y, z, 0, math.pi/2, 0)
                self.robot.move_pose(move)

    def return_home(self):
        if self.robot is not None:
            print("trying")
            if self.usingIK:
                ik.calculateIK(self.robot, self.home[0], self.home[1], self.home[2])
            else:
                self.robot.move_pose(self.home)
            print("great success")
            self.databus.movementStatus = "Idle"
            self.databus.homedStatus = "Homed"