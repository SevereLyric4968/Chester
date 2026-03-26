from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Literal
from pathlib import Path
import re

import cv2
import numpy as np
from pyniryo import NiryoRobot
from pyniryo.vision.image_functions import uncompress_image

@dataclass(frozen=True)
class PinkThresholdHSV:
    h_min: Optional[int] = None
    h_max: Optional[int] = None
    s_min: Optional[int] = None
    s_max: Optional[int] = None
    v_min: Optional[int] = None
    v_max: Optional[int] = None

    def __call__(self) -> Tuple[np.ndarray, np.ndarray]:
        if None in (self.h_min, self.h_max, self.s_min, self.s_max, self.v_min, self.v_max):
            raise ValueError("HSV thresholds not initialised. Load from MATLAB file first.")

        lower = np.array([self.h_min, self.s_min, self.v_min], dtype=np.uint8)
        upper = np.array([self.h_max, self.s_max, self.v_max], dtype=np.uint8)
        return lower, upper


@dataclass(frozen=True)
class GreenThresholdHSV:
    h_min: Optional[int] = None
    h_max: Optional[int] = None
    s_min: Optional[int] = None
    s_max: Optional[int] = None
    v_min: Optional[int] = None
    v_max: Optional[int] = None

    def __call__(self) -> Tuple[np.ndarray, np.ndarray]:
        if None in (self.h_min, self.h_max, self.s_min, self.s_max, self.v_min, self.v_max):
            raise ValueError("HSV thresholds not initialised. Load from MATLAB file first.")

        lower = np.array([self.h_min, self.s_min, self.v_min], dtype=np.uint8)
        upper = np.array([self.h_max, self.s_max, self.v_max], dtype=np.uint8)
        return lower, upper


@dataclass(frozen=True)
class MatlabHSVSpec:
    h_min: float
    h_max: float
    s_min: float
    s_max: float
    v_min: float
    v_max: float
    hue_wrap: bool


def _extract_matlab_scalar(text: str, name: str) -> float:
    pattern = rf"{name}\s*=\s*([0-9]*\.?[0-9]+)\s*;"
    m = re.search(pattern, text)
    if not m:
        raise ValueError(f"Could not find '{name}' in MATLAB mask file.")
    return float(m.group(1))


def load_matlab_hsv_mask_file(path: str | Path) -> MatlabHSVSpec:
    path = Path(path)
    text = path.read_text(encoding="utf-8")

    h_min = _extract_matlab_scalar(text, "channel1Min")
    h_max = _extract_matlab_scalar(text, "channel1Max")
    s_min = _extract_matlab_scalar(text, "channel2Min")
    s_max = _extract_matlab_scalar(text, "channel2Max")
    v_min = _extract_matlab_scalar(text, "channel3Min")
    v_max = _extract_matlab_scalar(text, "channel3Max")

    hue_wrap = "|" in text and "channel1Min" in text and "channel1Max" in text

    return MatlabHSVSpec(
        h_min=h_min,
        h_max=h_max,
        s_min=s_min,
        s_max=s_max,
        v_min=v_min,
        v_max=v_max,
        hue_wrap=hue_wrap,
    )


def _matlab_h_to_cv(h: float) -> int:
    return int(round(np.clip(h, 0.0, 1.0) * 179.0))


def _matlab_sv_to_cv(x: float) -> int:
    return int(round(np.clip(x, 0.0, 1.0) * 255.0))


def pink_threshold_from_matlab_file(path: str | Path) -> PinkThresholdHSV:
    spec = load_matlab_hsv_mask_file(path)
    return PinkThresholdHSV(
        h_min=_matlab_h_to_cv(spec.h_min),
        h_max=_matlab_h_to_cv(spec.h_max),
        s_min=_matlab_sv_to_cv(spec.s_min),
        s_max=_matlab_sv_to_cv(spec.s_max),
        v_min=_matlab_sv_to_cv(spec.v_min),
        v_max=_matlab_sv_to_cv(spec.v_max),
    )


def green_threshold_from_matlab_file(path: str | Path) -> GreenThresholdHSV:
    spec = load_matlab_hsv_mask_file(path)
    return GreenThresholdHSV(
        h_min=_matlab_h_to_cv(spec.h_min),
        h_max=_matlab_h_to_cv(spec.h_max),
        s_min=_matlab_sv_to_cv(spec.s_min),
        s_max=_matlab_sv_to_cv(spec.s_max),
        v_min=_matlab_sv_to_cv(spec.v_min),
        v_max=_matlab_sv_to_cv(spec.v_max),
    )


def pink_mask_uses_hue_wrap(path: str | Path) -> bool:
    return load_matlab_hsv_mask_file(path).hue_wrap


def _clip_roi(
    x: int, y: int, w: int, h: int, img_w: int, img_h: int
) -> Tuple[int, int, int, int]:
    x = max(0, min(x, img_w - 1))
    y = max(0, min(y, img_h - 1))
    w = max(1, min(w, img_w - x))
    h = max(1, min(h, img_h - y))
    return x, y, w, h


def crop_roi(
    img: np.ndarray, roi: Tuple[int, int, int, int]
) -> Tuple[np.ndarray, Tuple[int, int]]:
    H, W = img.shape[:2]
    x, y, w, h = _clip_roi(*roi, W, H)
    return img[y:y + h, x:x + w], (x, y)


@dataclass
class MultiColorCentroidDetector:
    pink_hsv_cfg: PinkThresholdHSV
    green_hsv_cfg: GreenThresholdHSV
    min_area_px: int = 400
    morph_kernel_size: int = 5
    roi: Optional[Tuple[int, int, int, int]] = None
    pink_wrap_hue: bool = False

    def _get_bounds(
        self, sticker_color: Literal["pink", "green"]
    ) -> Tuple[np.ndarray, np.ndarray]:
        if sticker_color == "pink":
            return self.pink_hsv_cfg()
        if sticker_color == "green":
            return self.green_hsv_cfg()
        raise ValueError(f"Unsupported sticker_color: {sticker_color}")

    def detect(
        self,
        bgr_img: np.ndarray,
        *,
        sticker_color: Literal["pink", "green"],
        use_roi: bool = True,
    ) -> Tuple[Optional[Tuple[int, int]], np.ndarray, Optional[Tuple[int, int, int, int]]]:
        """
        Returns:
            centroid_full: (cx, cy) in full image coords, or None
            mask: binary mask used for detection
            roi_used: actual ROI used, or None
        """
        H, W = bgr_img.shape[:2]
        img_for_detect = bgr_img
        offset = (0, 0)
        roi_used = None

        if use_roi and self.roi is not None:
            roi_used = _clip_roi(*self.roi, W, H)
            img_for_detect, offset = crop_roi(bgr_img, roi_used)

        hsv_img = cv2.cvtColor(img_for_detect, cv2.COLOR_BGR2HSV)
        lower, upper = self._get_bounds(sticker_color)

        if sticker_color == "pink" and self.pink_wrap_hue and lower[0] > upper[0]:
            lower1 = np.array([lower[0], lower[1], lower[2]], dtype=np.uint8)
            upper1 = np.array([179, upper[1], upper[2]], dtype=np.uint8)

            lower2 = np.array([0, lower[1], lower[2]], dtype=np.uint8)
            upper2 = np.array([upper[0], upper[1], upper[2]], dtype=np.uint8)

            mask1 = cv2.inRange(hsv_img, lower1, upper1)
            mask2 = cv2.inRange(hsv_img, lower2, upper2)
            mask = cv2.bitwise_or(mask1, mask2)
        else:
            mask = cv2.inRange(hsv_img, lower, upper)

        k = self.morph_kernel_size
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        centroid_roi: Optional[Tuple[int, int]] = None

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) >= self.min_area_px:
                m = cv2.moments(largest)
                if abs(m["m00"]) > 1e-6:
                    cx = int(m["m10"] / m["m00"])
                    cy = int(m["m01"] / m["m00"])
                    centroid_roi = (cx, cy)

        centroid_full: Optional[Tuple[int, int]] = None
        if centroid_roi is not None:
            ox, oy = offset
            centroid_full = (centroid_roi[0] + ox, centroid_roi[1] + oy)

        return centroid_full, mask, roi_used


def draw_detection(
    vis: np.ndarray,
    *,
    centroid: Optional[Tuple[int, int]],
    color_name: str,
    draw_color: Tuple[int, int, int],
    roi_used: Optional[Tuple[int, int, int, int]],
    target_px: Tuple[int, int],
) -> None:
    cv2.drawMarker(
        vis,
        target_px,
        (0, 255, 255),
        markerType=cv2.MARKER_CROSS,
        markerSize=20,
        thickness=2,
    )

    if roi_used is not None:
        x, y, w, h = roi_used
        cv2.rectangle(vis, (x, y), (x + w, y + h), (255, 255, 0), 2)

    if centroid is not None:
        cx, cy = centroid
        dx = cx - target_px[0]
        dy = cy - target_px[1]
        cv2.circle(vis, (cx, cy), 8, draw_color, -1)
        cv2.line(vis, target_px, (cx, cy), draw_color, 2)
        cv2.putText(
            vis,
            f"{color_name.upper()} FOUND err=({dx},{dy})",
            (10, 30 if color_name == "pink" else 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            draw_color,
            2,
        )
    else:
        cv2.putText(
            vis,
            f"{color_name.upper()} NOT found",
            (10, 30 if color_name == "pink" else 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            draw_color,
            2,
        )


def main():
    robot_ip = "192.168.42.1"

    BASE_DIR = Path(__file__).resolve().parent
    pink_mask_file = BASE_DIR / "pinkMask.m"
    green_mask_file = BASE_DIR / "greenMask.m"

    fixed_roi: Optional[Tuple[int, int, int, int]] = None
    # Example:
    # fixed_roi = (120, 80, 400, 300)

    pink_hsv = pink_threshold_from_matlab_file(pink_mask_file)
    green_hsv = green_threshold_from_matlab_file(green_mask_file)
    pink_wrap_hue = pink_mask_uses_hue_wrap(pink_mask_file)

    print("Loaded HSV from MATLAB:")
    print("  Pink :", pink_hsv)
    print("  Green:", green_hsv)
    print("  Pink hue wrap:", pink_wrap_hue)

    detector = MultiColorCentroidDetector(
        pink_hsv_cfg=pink_hsv,
        green_hsv_cfg=green_hsv,
        min_area_px=400,
        morph_kernel_size=5,
        roi=fixed_roi,
        pink_wrap_hue=pink_wrap_hue,
    )

    active_mode = "both"   # "pink", "green", or "both"
    use_roi = fixed_roi is not None

    robot = NiryoRobot(robot_ip)

    try:
        print("Camera/mask test started.")
        print("Controls:")
        print("  q / ESC : quit")
        print("  p       : active display = pink")
        print("  g       : active display = green")
        print("  b       : active display = both")
        print("  r       : toggle ROI on/off")

        while True:
            img = uncompress_image(robot.get_img_compressed())
            img = cv2.flip(img, 0)

            H, W = img.shape[:2]
            target = (W // 2, H // 2)

            vis = img.copy()

            pink_centroid, pink_mask, pink_roi = detector.detect(
                img, sticker_color="pink", use_roi=use_roi
            )
            green_centroid, green_mask, green_roi = detector.detect(
                img, sticker_color="green", use_roi=use_roi
            )

            if active_mode in ("pink", "both"):
                draw_detection(
                    vis,
                    centroid=pink_centroid,
                    color_name="pink",
                    draw_color=(255, 0, 255),
                    roi_used=pink_roi,
                    target_px=target,
                )

            if active_mode in ("green", "both"):
                draw_detection(
                    vis,
                    centroid=green_centroid,
                    color_name="green",
                    draw_color=(0, 255, 0),
                    roi_used=green_roi,
                    target_px=target,
                )

            mode_text = f"mode={active_mode} | roi={'on' if use_roi else 'off'}"
            cv2.putText(
                vis,
                mode_text,
                (10, H - 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

            cv2.imshow("Niryo Camera Debug", vis)
            cv2.imshow("Pink Mask", pink_mask)
            cv2.imshow("Green Mask", green_mask)

            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), 27):
                break
            elif key == ord("p"):
                active_mode = "pink"
            elif key == ord("g"):
                active_mode = "green"
            elif key == ord("b"):
                active_mode = "both"
            elif key == ord("r"):
                use_roi = not use_roi
                print(f"ROI {'enabled' if use_roi else 'disabled'}")

    finally:
        cv2.destroyAllWindows()
        try:
            robot.close_connection()
        except Exception:
            pass


if __name__ == "__main__":
    main()