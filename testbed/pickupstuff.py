from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np

from pyniryo import NiryoRobot
from pyniryo.vision.image_functions import uncompress_image


@dataclass
class PinkThresholdHSV:
    #
    h_min: int = 140
    h_max: int = 179
    s_min: int = 70
    s_max: int = 255
    v_min: int = 70
    v_max: int = 255



def find_pink_centroid_px(
    bgr_img: np.ndarray,
    hsv_cfg,
    *,
    min_area_px: int = 400,
    show: bool = True,
) -> Optional[Tuple[int, int]]:
    """
    Detect pink object, display debug view, and return centroid (cx, cy) in pixels.
    Returns None if not found.
    """

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

    # Visualization
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

            text = f"Pink FOUND  err_px=({dx},{dy})"
            color = (0, 255, 0)
        else:
            text = "Pink NOT found"
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

        cv2.imshow("Niryo Camera (vis)", vis)
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
