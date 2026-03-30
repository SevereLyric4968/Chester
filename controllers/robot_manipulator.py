from pyniryo import NiryoRobot, PinID, PoseObject
import utils.z_calibration as zCal
import utils.inverse_kinematics as ik

import math

from testbed.intelligent_pickup import (
    CenteringConfig,
    IntelligentPickupSystem,
    sticker_from_piece_colour,
)


class RobotManipulator:

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

    zCalibrate = False
    usingIK = False   

    def __init__(self, ip, boardCoords, databus):
        self.databus = databus
        self.robot = None
        self.intelligent_system = None
        self.last_target_pose = None

        print("MAKING MANIPULATOR")

        try:
            self.robot = NiryoRobot(ip)
            self.databus.connectionStatus = "connected"

            self.pin_electromagnet = PinID.DO4
            self.robot.setup_electromagnet(self.pin_electromagnet)

            self.robot.calibrate_auto()

            if self.zCalibrate:
                self.robotCalibration = zCal.ZCalibration(self.robot)

            self.home = PoseObject(0.0023, -0.1335, 0.2, 0, math.pi/2, 0) # (0.1343, 0, 0.1652, 0, 1, 0) changed home position to face to the right not blocking board

            if self.usingIK:
                ik.calculateIK(self.robot, *[
                    self.home.x, self.home.y, self.home.z,
                    self.home.roll, self.home.pitch, self.home.yaw
                ])
            else:
                self.robot.move_pose(self.home)

            self.databus.homedStatus = "Homed"
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

            self.intelligent_system = IntelligentPickupSystem.create(
                self.robot,
                pin_electromagnet=self.pin_electromagnet,
                cfg=cfg,
                detector_show=True,
                detector_min_area_px=400,
            )

            print("robot ready")

        except Exception as e:
            print(f"robot failed to connect: {e}")
            self.robot = None
            self.intelligent_system = None

        self.boardMap, self.storageMap, self.storageOccupancy = self.init_maps(boardCoords)

    def _piece_type(self, piece):
        return {
            'p': 'pawn', 'r': 'rook', 'n': 'knight',
            'b': 'bishop', 'q': 'queen', 'k': 'king'
        }[piece.lower()]

    def _piece_colour(self, piece):
        return "white" if piece.isupper() else "black"

    def _make_pose(self, x_mm, y_mm, z):
        return PoseObject(x_mm / 1000, y_mm / 1000, z, 0, math.pi/2, 0)

    def _move_pose(self, pose):
        #Unified movement wrapper
        if self.usingIK:
            ik.calculateIK(
                self.robot,
                pose.x, pose.y, pose.z,
                pose.roll, pose.pitch, pose.yaw
            )
        else:
            self.robot.move_pose(pose)

    def move(self, x, y, z=cruiseHeight):
        if self.robot is None:
            return

        self.databus.movementStatus = "Moving"
        self.databus.homedStatus = "Not Homed"

        pose = self._make_pose(x, y, z)
        self.last_target_pose = pose

        self._move_pose(pose)

    def pickup(self, piece):
        if self.robot is None:
            return

        if self.last_target_pose is None:
            raise RuntimeError("pickup() before move()")

        self.databus.movementStatus = "Moving"

        piece_type = self._piece_type(piece)
        piece_colour = self._piece_colour(piece)

        # fallback if no intelligent system
        if self.intelligent_system is None:
            pose = self.robot.get_pose()
            z = self.robotCalibration.getZBaseline(pose.x, pose.y) if self.zCalibrate else self.boardHeight

            target = PoseObject(
                pose.x, pose.y,
                z + self.pieceHeights[piece.lower()],
                0, math.pi/2, 0
            )

            self._move_pose(target)
            self.robot.activate_electromagnet(self.pin_electromagnet)
            self.databus.magnetStatus = "On"
            self._move_pose(pose)
            return

        self.intelligent_system.cfg.sticker_color = sticker_from_piece_colour(piece_colour)
        self.intelligent_system.cfg.piece_type = piece_type

        self.intelligent_system.centerer._tracking_roi = None
        self.intelligent_system.centerer._pre_vision_done = False

        self._move_pose(self.last_target_pose)

        self.intelligent_system.centerer.calibrate_jacobian()
        result = self.intelligent_system.centerer()

        if not result.success:
            raise RuntimeError(f"centering failed: {result.last_error_px}")

        p = self.robot.get_pose()
        corrected = PoseObject(p.x, p.y, p.z, p.roll, p.pitch, p.yaw)

        self.intelligent_system.picker.pick_at(piece_type, corrected)
        self.databus.magnetStatus = "On"


    def place(self, piece="p"):
        if self.robot is None:
            return

        if self.last_target_pose is None:
            raise RuntimeError("place() before move()")

        self.databus.movementStatus = "Moving"

        piece_type = self._piece_type(piece)

        if self.intelligent_system is None:
            pose = self.robot.get_pose()
            z = self.robotCalibration.getZBaseline(pose.x, pose.y) if self.zCalibrate else self.boardHeight

            target = PoseObject(
                pose.x, pose.y,
                z + self.pieceHeights[piece.lower()],
                0, math.pi/2, 0
            )

            self._move_pose(target)
            self.robot.deactivate_electromagnet(self.pin_electromagnet)
            self.databus.magnetStatus = "Off"
            self._move_pose(pose)
            return

        self._move_pose(self.last_target_pose)
        self.intelligent_system.picker.place_at(piece_type, self.last_target_pose)

        self.databus.magnetStatus = "Off"


    def return_home(self):
        if self.robot is None:
            return

        print("returning home")
        self._move_pose(self.home)

        self.databus.movementStatus = "Idle"
        self.databus.homedStatus = "Homed"


    def init_board_map(self, startPos, offsetX, offsetY):
        boardMap = {}
        for rank in range(8):
            for file in range(8):
                square = chr(ord("a")+file) + str(rank+1)
                boardMap[square] = (
                    startPos[0] - offsetX*rank,
                    startPos[1] + offsetY*file
                )
        return boardMap

    def init_storage_map(self, whiteStartPos, blackStartPos, offset):
        storageMap = {}
        layout = {
            'p': [(0,i) for i in range(8)],
            'r': [(1,0),(1,1),(2,0),(2,1)],
            'n': [(1,2),(1,3),(2,2),(2,3)],
            'b': [(1,4),(1,5),(2,4),(2,5)],
            'q': [(1,7),(2,6),(2,7)],
            'k': [(1,6)]
        }

        for piece in layout:
            storageMap[piece.upper()] = [
                (pos[0]*offset + whiteStartPos[0],
                 pos[1]*offset + whiteStartPos[1])
                for pos in layout[piece]
            ]

            storageMap[piece] = [
                (pos[0]*offset + blackStartPos[0],
                 pos[1]*offset + blackStartPos[1])
                for pos in layout[piece]
            ]

        return storageMap

    def init_storage_occupancy(self, storageMap, mode="standard"):
        standardCounts = {
            'P':8,'p':8,'R':2,'r':2,'N':2,'n':2,
            'B':2,'b':2,'Q':1,'q':1,'K':1,'k':1
        }

        occ = {}
        for piece in storageMap:
            occ[piece] = []
            total = len(storageMap[piece])
            onBoard = standardCounts[piece]

            for i in range(total):
                occ[piece].append(i > onBoard if mode=="standard" else True)

        return occ

    def init_maps(self, boardCoords):
        return (
            self.init_board_map(
                boardCoords["boardStart"],
                boardCoords["xOffset"],
                boardCoords["yOffset"]
            ),
            self.init_storage_map(
                boardCoords["whiteStorageStart"],
                boardCoords["blackStorageStart"],
                boardCoords["storageOffset"]
            ),
            self.init_storage_occupancy({})
        )