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
        "E4": PoseObject(0.205,  0.000, 0.148, 0, 1.5, 0),
        "C2": PoseObject(0.205, -0.040, 0.148, 0, 1.5, 0),
        "B3": PoseObject(0.245, -0.040, 0.148, 0, 1.5, 0),
        "D8": PoseObject(0.165,  0.040, 0.148, 0, 1.5, 0),
    }

    # Vision centering config 
    cfg = CenteringConfig(
        deadband_px=15,
        max_step_m=0.002,
        dt_s=0.15,
        max_iters=600,
        timeout_s=45.0,
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

        pick_sq = clean_square(input("Pick from square (E4/C2/B3/D8): "))
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


"""from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np

from pyniryo import NiryoRobot
from pyniryo.vision.image_functions import uncompress_image


@dataclass
class PinkThresholdHSV:
#Continuously grab camera frames
#Convert image to HSV
#Threshold to isolate pink pixels
#Clean the mask with morphology
#Find the largest pink blob
#Compute its centroid
#Display visualisation + pixel error

    h_min: int = 125
    h_max: int = 179
    s_min: int = 40
    s_max: int = 255
    v_min: int = 40
    v_max: int = 255



def find_pink_centroid_px(
    bgr_img: np.ndarray,
    hsv_cfg,
    *,
    min_area_px: int = 400,
    show: bool = True,
) -> Optional[Tuple[int, int]]:

    h, w = bgr_img.shape[:2]
    center = (w // 2, h // 2)

    # HSV threshold 
    hsv_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)
    lower = np.array([hsv_cfg.h_min, hsv_cfg.s_min, hsv_cfg.v_min], dtype=np.uint8)
    upper = np.array([hsv_cfg.h_max, hsv_cfg.s_max, hsv_cfg.v_max], dtype=np.uint8)
    mask = cv2.inRange(hsv_img, lower, upper)

    # Morphology 
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    centroid = None
    found = False

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) >= min_area_px:
            m = cv2.moments(largest)
            if abs(m["m00"]) > 1e-6:
                cx = int(m["m10"] / m["m00"])
                cy = int(m["m01"] / m["m00"])
                centroid = (cx, cy)
                found = True

    # Visualisation
    if show:
        vis = bgr_img.copy()

        # Image center crosshair
        cv2.drawMarker(
            vis,
            center,
            (0, 255, 255),
            markerType=cv2.MARKER_CROSS,
            markerSize=20,
            thickness=2,
        )

        if found:
            cx, cy = centroid
            dx = cx - center[0]
            dy = cy - center[1]

            cv2.circle(vis, (cx, cy), 8, (0, 255, 0), -1)
            cv2.line(vis, center, (cx, cy), (0, 255, 0), 2)

            text = f"Pink FOUND :) err_px=({dx},{dy})"
            color = (0, 255, 0)
        else:
            text = "Pink NOT found :("
            color = (0, 0, 255)

        cv2.putText(
            vis,
            text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )

        cv2.imshow("Niryo Camera", vis)
        cv2.imshow("Pink Mask", mask)

    return centroid


def main():
    robot_ip = "192.168.42.1"
    robot = NiryoRobot(robot_ip)

    print("Streaming camera. Press Q or ESC to quit.")

    while True:
        img = uncompress_image(robot.get_img_compressed())

        centroid = find_pink_centroid_px(
            img,
            hsv_cfg=PinkThresholdHSV(),
            min_area_px=400,
            show=True,
        )

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q"), 27):
            break

    cv2.destroyAllWindows()
    robot.close_connection()


if __name__ == "__main__":
    main()
"""