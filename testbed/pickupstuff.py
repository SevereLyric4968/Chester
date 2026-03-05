import cv2

from pyniryo import NiryoRobot, PoseObject, PinID
from pyniryo.vision.image_functions import uncompress_image

from intelligent_pickup import (
    PinkThresholdHSV, PinkCentroidDetector,
    CenteringConfig, VisualCenteringController,
    ElectromagnetPiecePicker,
)


def clean_square(s: str) -> str:
    return s.strip().upper()


def clean_piece(s: str) -> str:
    return s.strip().lower()


def main():
    robot_ip = "192.168.42.1"
    robot = NiryoRobot(robot_ip)
    pin_electromagnet = PinID.DO4

    Square_Poses = {
        "D3": PoseObject(0.205,  0.000, 0.148, 0, 1.5, 0),
        "D6": PoseObject(0.305,  0.000, 0.148, 0, 1.5, 0),
        "G6": PoseObject(0.305, -0.07, 0.147, 0, 1.5, 0),
        "G3": PoseObject(0.205,  -0.07, 0.148, 0, 1.5, 0),
    }

    # Vision centering config 
    cfg = CenteringConfig(
        deadband_px=15,
        max_step_m=0.004,
        dt_s=0.15,
        max_iters=600,
        timeout_s=59.0,
        target_offset_px=(-6, 112),   
        use_tracking_roi=True,
        tracking_roi_size=(260, 260),
    )

    try:
        #robot.calibrate_auto()

        hsv = PinkThresholdHSV()
        detector = PinkCentroidDetector(hsv_cfg=hsv, min_area_px=400, show=True)
        centerer = VisualCenteringController(robot=robot, detector=detector, cfg=cfg)

        picker = ElectromagnetPiecePicker(
            robot,
            pin_electromagnet=pin_electromagnet,
            pickup_drop_m=0.04,
        )

        valid_squares = ", ".join(Square_Poses.keys())
        print(f"Valid squares: {valid_squares}")

        pick_sq = clean_square(input("Pick from square (D3/D6/G3/G6): "))
        if pick_sq not in Square_Poses:
            raise ValueError(f"Unknown square '{pick_sq}'. Valid: {valid_squares}")

        piece_type = clean_piece(input("Piece type (pawn/rook/bishop/etc): "))

        robot.move_pose(Square_Poses[pick_sq])

        centerer.calibrate_jacobian(delta_m=0.015)

        print(f"Centering over {pick_sq} ...")
        result = centerer()

        if not result.success:
            print(
                f"Failed to center at {pick_sq}. iters={result.iters}, "
                f"last error px={result.last_error_px}, centroid={result.last_centroid_px}"
            )
            return

        print(
            f"Centered at {pick_sq} in {result.iters} iters. "
            f"Final error px={result.last_error_px}"
        )

        p = robot.get_pose()
        pickup_xy_pose = PoseObject(p.x, p.y, p.z, p.roll, p.pitch, p.yaw)
        picker.pick_at(piece_type, pickup_xy_pose)

        place_sq = clean_square(input("Place to square (E4/C2/B3/D8): "))
        if place_sq not in Square_Poses:
            raise ValueError(f"Unknown square '{place_sq}'. Valid: {valid_squares}")

        robot.move_pose(Square_Poses[place_sq])
        picker.place_at(Square_Poses[place_sq])

        print(f"Done: moved {piece_type} from {pick_sq} to {place_sq}.")

        print("Press Q or ESC to quit windows.")
        while True:
            img = uncompress_image(robot.get_img_compressed())
            img = cv2.flip(img, 0)

            h, w = img.shape[:2]
            ox, oy = cfg.target_offset_px
            target = (w // 2 + int(ox), h // 2 + int(oy))

            detector(img, target_px=target, use_roi=(detector.roi is not None))

            key = cv2.waitKey(10) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                break

    finally:
        cv2.destroyAllWindows()
        # robot.close_connection()


if __name__ == "__main__":
    main()

