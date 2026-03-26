import cv2

from pyniryo import NiryoRobot, PoseObject, PinID
import math
from intelligent_pickup import (
    CenteringConfig,
    IntelligentPickupSystem,
)


def main():
    robot = NiryoRobot("192.168.42.1")

    square_poses = {
        "B2": PoseObject(0.155,  -0.08, 0.208, 0, math.pi/2, 0),
        "C4": PoseObject(0.225,  -0.05, 0.208, 0, math.pi/2, 0),
        "F2": PoseObject(0.155,  0.042, 0.208, 0, math.pi/2, 0),
        "G3": PoseObject(0.190,  0.07, 0.208, 0, math.pi/2, 0),
    }

    home_pose = PoseObject(0.14, 0, 0.2, 0, 1.5, 0)

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

    try:
        system = IntelligentPickupSystem.create(
            robot,
            pin_electromagnet=PinID.DO4,
            cfg=cfg,
            detector_show=True,
            detector_min_area_px=400,
        )

        valid_squares = ", ".join(square_poses.keys())

        while True:
            print(f"\nValid squares: {valid_squares}")
            print("Type Q at any prompt to quit.")

            pick_sq = input("Pick from square (B2/C4/F2/G3): ").strip().upper()
            if pick_sq in ("Q", "QUIT", "EXIT"):
                break
            if pick_sq not in square_poses:
                print(f"Unknown square '{pick_sq}'. Valid: {valid_squares}")
                continue

            place_sq = input("Place to square (B2/C4/F2/G3): ").strip().upper()
            if place_sq in ("Q", "QUIT", "EXIT"):
                break
            if place_sq not in square_poses:
                print(f"Unknown square '{place_sq}'. Valid: {valid_squares}")
                continue

            piece_colour = input("Piece colour (black/white): ").strip()
            if piece_colour.upper() in ("Q", "QUIT", "EXIT"):
                break

            piece_type = input("Piece type (pawn/rook/bishop/etc): ").strip()
            if piece_type.upper() in ("Q", "QUIT", "EXIT"):
                break

            try:
                result = system.move_piece(
                    piece_colour=piece_colour,
                    piece_type=piece_type,
                    pickup_pose=square_poses[pick_sq],
                    drop_pose=square_poses[place_sq],
                )

                if not result.success:
                    print(
                        f"Failed to center at {pick_sq}. iters={result.iters}, "
                        f"last error px={result.last_error_px}, centroid={result.last_centroid_px}"
                    )
                else:
                    print(
                        f"Done: moved {piece_type} ({piece_colour}) from {pick_sq} to {place_sq}. "
                        f"Centering final error px={result.last_error_px}"
                    )

            except Exception as e:
                print(f"Move failed: {e}")

            # Always return home after each attempt
            try:
                robot.move_pose(home_pose)
                print("Returned to home pose.")
            except Exception as e:
                print(f"Failed to move to home pose: {e}")

        print("Exiting.")

    finally:
        cv2.destroyAllWindows()
        # robot.close_connection()


if __name__ == "__main__":
    main()