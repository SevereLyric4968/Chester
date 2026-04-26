from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Literal
from pathlib import Path
import re

import time
import cv2
import numpy as np
import numpy.linalg as LA

from pyniryo import NiryoRobot, PoseObject, PinID
from pyniryo.vision.image_functions import uncompress_image

# needs edited to use Sams calculateIK stuff instead of move_pose

PIECE_VISION_DROP_M: Dict[str, float] = {
    "p": 0.052,
    "b": 0.039,
    "r": 0.048,
    "n": 0.0,
    "q": 0.036,
    "k": 0.0,
}

PIECE_HEIGHT_M: Dict[str, float] = {
    "p": 60.0 / 1000.0,
    "r": 64.5 / 1000.0,
    "n": 69.0 / 1000.0,
    "b": 73.5 / 1000.0,
    "q": 78.0 / 1000.0,
    "k": 82.5 / 1000.0,
}

# Board height retained from the tester code so absolute placement Z can still be computed.
boardHeight = 0.0500

# Accept either full names or single-letter symbols.
PIECE_NAME_TO_SYMBOL: Dict[str, str] = {
    "pawn": "p",
    "rook": "r",
    "knight": "n",
    "bishop": "b",
    "queen": "q",
    "king": "k",
    "p": "p",
    "r": "r",
    "n": "n",
    "b": "b",
    "q": "q",
    "k": "k",
}


def normalize_piece_symbol(piece_type: str) -> str:
    piece = piece_type.strip().lower()
    symbol = PIECE_NAME_TO_SYMBOL.get(piece)
    if symbol is None:
        raise ValueError(
            f"Unsupported piece_type '{piece_type}'. "
            f"Use one of: pawn, rook, knight, bishop, queen, king "
            f"or symbols p, r, n, b, q, k."
        )
    return symbol


def sticker_from_piece_colour(piece_colour: str) -> str:
    piece_colour = piece_colour.strip().lower()
    if piece_colour == "black":
        return "pink"
    if piece_colour == "white":
        return "green"
    raise ValueError("Piece colour must be 'black' or 'white'")


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


def _clip_roi(x: int, y: int, w: int, h: int, img_w: int, img_h: int) -> Tuple[int, int, int, int]:
    x = max(0, min(x, img_w - 1))
    y = max(0, min(y, img_h - 1))
    w = max(1, min(w, img_w - x))
    h = max(1, min(h, img_h - y))
    return x, y, w, h


def crop_roi(img: np.ndarray, roi: Tuple[int, int, int, int]) -> Tuple[np.ndarray, Tuple[int, int]]:
    H, W = img.shape[:2]
    x, y, w, h = _clip_roi(*roi, W, H)
    return img[y:y + h, x:x + w], (x, y)


@dataclass
class MultiColorCentroidDetector:
    pink_hsv_cfg: PinkThresholdHSV
    green_hsv_cfg: GreenThresholdHSV
    min_area_px: int = 400
    show: bool = True
    morph_kernel_size: int = 5
    roi: Optional[Tuple[int, int, int, int]] = None
    draw_roi: bool = True
    pink_wrap_hue: bool = False

    def _get_bounds(self, sticker_color: Literal["pink", "green"]) -> Tuple[np.ndarray, np.ndarray]:
        if sticker_color == "pink":
            return self.pink_hsv_cfg()
        if sticker_color == "green":
            return self.green_hsv_cfg()
        raise ValueError(f"Unsupported sticker_color: {sticker_color}")

    def __call__(
        self,
        bgr_img: np.ndarray,
        *,
        sticker_color: Literal["pink", "green"],
        target_px: Optional[Tuple[int, int]] = None,
        use_roi: bool = True,
    ) -> Optional[Tuple[int, int]]:

        H, W = bgr_img.shape[:2]

        if target_px is None:
            target_px = (W // 2, H // 2)

        img_for_detect = bgr_img
        offset = (0, 0)
        roi_used = None

        if use_roi and self.roi is not None:
            roi_used = self.roi
            img_for_detect, offset = crop_roi(bgr_img, self.roi)

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
            cx_roi, cy_roi = centroid_roi
            ox, oy = offset
            centroid_full = (cx_roi + ox, cy_roi + oy)

        if self.show:
            vis = bgr_img.copy()

            cv2.drawMarker(
                vis, target_px, (0, 255, 255),
                markerType=cv2.MARKER_CROSS, markerSize=20, thickness=2
            )

            if self.draw_roi and roi_used is not None:
                x, y, w, h = roi_used
                x, y, w, h = _clip_roi(x, y, w, h, W, H)
                cv2.rectangle(vis, (x, y), (x + w, y + h), (255, 255, 0), 2)

            label_color = (255, 0, 255) if sticker_color == "pink" else (0, 255, 0)

            if centroid_full is not None:
                cx, cy = centroid_full
                dx, dy = cx - target_px[0], cy - target_px[1]
                cv2.circle(vis, (cx, cy), 8, label_color, -1)
                cv2.line(vis, target_px, (cx, cy), label_color, 2)
                cv2.putText(
                    vis, f"{sticker_color.upper()} FOUND err_px=({dx},{dy})",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, label_color, 2
                )
            else:
                cv2.putText(
                    vis, f"{sticker_color.upper()} NOT found",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
                )

            cv2.imshow("Niryo Camera (vis)", vis)
            cv2.imshow(f"{sticker_color.capitalize()} Mask", mask)

        return centroid_full


@dataclass
class CenteringConfig:
    deadband_px: int = 5
    max_step_m: float = 0.005
    dt_s: float = 0.05
    max_iters: int = 200
    timeout_s: float = 20.0
    target_offset_px: Tuple[int, int] = (0, 0)
    fixed_roi: Optional[Tuple[int, int, int, int]] = None
    use_tracking_roi: bool = True
    tracking_roi_size: Tuple[int, int] = (220, 220)
    sticker_color: str = "pink"

    # accepts either full name or symbol
    piece_type: Optional[str] = None

    reuse_jacobian: bool = True
    reuse_max_xy_m: float = 0.03
    reuse_max_z_m: float = 0.01
    reuse_max_age_s: float = 9999.0


@dataclass(frozen=True)
class CenteringResult:
    success: bool
    iters: int
    last_error_px: Tuple[int, int]
    last_centroid_px: Optional[Tuple[int, int]]


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


class VisualCenteringController:
    def __init__(
        self,
        robot: NiryoRobot,
        detector: MultiColorCentroidDetector,
        cfg: Optional[CenteringConfig] = None,
    ):
        self.robot = robot
        self.detector = detector
        self.cfg = CenteringConfig() if cfg is None else cfg
        self._J_calib_pose: Optional[PoseObject] = None
        self._J_calib_time: Optional[float] = None
        self._pre_vision_done = False

        if self.cfg.fixed_roi is not None:
            self.detector.roi = self.cfg.fixed_roi

        self._tracking_roi: Optional[Tuple[int, int, int, int]] = None
        self.J: Optional[np.ndarray] = None

        self._filtered_error: Optional[np.ndarray] = None

        # Lock ROI during Jacobian calibration so detector stays on the same piece
        self._calibration_locked_roi: Optional[Tuple[int, int, int, int]] = None
        self._pre_calibration_roi: Optional[Tuple[int, int, int, int]] = None

        # Carry the calibration ROI forward into the first centering frames
        self._post_calibration_seed_roi: Optional[Tuple[int, int, int, int]] = None
        self._post_calibration_seed_frames_remaining: int = 0

    def _apply_pre_vision_drop_once(self):
        if self._pre_vision_done:
            return

        if self.cfg.piece_type is None:
            return

        piece_symbol = normalize_piece_symbol(self.cfg.piece_type)

        if piece_symbol not in PIECE_VISION_DROP_M:
            raise ValueError(
                f"Unsupported piece_type '{self.cfg.piece_type}'. "
                f"Add it to PIECE_VISION_DROP_M at the top of the file."
            )

        drop = PIECE_VISION_DROP_M[piece_symbol]

        pose = self.robot.get_pose()
        new_z = pose.z - drop

        MIN_SAFE_Z = 0.105
        if new_z < MIN_SAFE_Z:
            new_z = MIN_SAFE_Z

        self.robot.move_pose(PoseObject(
            pose.x,
            pose.y,
            new_z,
            pose.roll,
            pose.pitch,
            pose.yaw
        ))

        self._pre_vision_done = True

    def _get_frame(self) -> np.ndarray:
        img = uncompress_image(self.robot.get_img_compressed())
        return cv2.flip(img, 0)

    def _show_camera_for(self, duration_s: float):
        end_t = time.time() + duration_s
        while time.time() < end_t:
            img = self._get_frame()
            target = self._make_target(img)
            use_roi = self._choose_roi_mode()

            self.detector(
                img,
                sticker_color=self.cfg.sticker_color,
                target_px=target,
                use_roi=use_roi
            )
            cv2.waitKey(1)
            time.sleep(0.03)

    def _make_target(self, img: np.ndarray) -> Tuple[int, int]:
        H, W = img.shape[:2]
        ox, oy = self.cfg.target_offset_px
        return (W // 2 + int(ox), H // 2 + int(oy))

    def _choose_roi_mode(self) -> bool:
        # Highest priority: active calibration lock
        if self._calibration_locked_roi is not None:
            self.detector.roi = self._calibration_locked_roi
            return True

        # Next: carry calibration ROI briefly into centering startup
        if self._post_calibration_seed_roi is not None and self._post_calibration_seed_frames_remaining > 0:
            self.detector.roi = self._post_calibration_seed_roi
            return True

        # Normal tracking ROI
        if self.cfg.use_tracking_roi and self._tracking_roi is not None:
            self.detector.roi = self._tracking_roi
            return True

        # Fixed ROI fallback
        if self.cfg.fixed_roi is not None:
            self.detector.roi = self.cfg.fixed_roi
            return True

        self.detector.roi = None
        return False

    def _update_tracking_roi(self, centroid: Tuple[int, int], img_w: int, img_h: int):
        w_roi, h_roi = self.cfg.tracking_roi_size
        cx, cy = centroid
        x = int(cx - w_roi // 2)
        y = int(cy - h_roi // 2)
        self._tracking_roi = _clip_roi(x, y, w_roi, h_roi, img_w, img_h)

    def _make_locked_roi_around_centroid(
        self,
        centroid: Tuple[int, int],
        img_w: int,
        img_h: int,
        pad_px: int = 90,
    ) -> Tuple[int, int, int, int]:
        cx, cy = centroid
        w = 2 * pad_px
        h = 2 * pad_px
        x = int(cx - pad_px)
        y = int(cy - pad_px)
        return _clip_roi(x, y, w, h, img_w, img_h)

    def _lock_calibration_roi_from_current_detection(self, samples: int = 5, pad_px: int = 90) -> None:
        img = self._get_frame()
        H, W = img.shape[:2]

        pts = []
        for _ in range(samples):
            img_i = self._get_frame()
            target_i = self._make_target(img_i)
            use_roi = self._choose_roi_mode()
            c = self.detector(
                img_i,
                sticker_color=self.cfg.sticker_color,
                target_px=target_i,
                use_roi=use_roi
            )
            cv2.waitKey(1)
            if c is not None:
                pts.append(c)
            time.sleep(0.02)

        if not pts:
            raise RuntimeError(
                f"Could not lock calibration ROI because the {self.cfg.sticker_color} sticker was not detected."
            )

        mean_x = int(round(np.mean([p[0] for p in pts])))
        mean_y = int(round(np.mean([p[1] for p in pts])))
        locked_centroid = (mean_x, mean_y)

        self._pre_calibration_roi = self.detector.roi
        self._calibration_locked_roi = self._make_locked_roi_around_centroid(
            locked_centroid, W, H, pad_px=pad_px
        )
        self.detector.roi = self._calibration_locked_roi

    def _unlock_calibration_roi(self) -> None:
        # Keep the calibration ROI alive briefly after calibration so
        # the first centering detections stay on the same piece.
        if self._calibration_locked_roi is not None:
            self._post_calibration_seed_roi = self._calibration_locked_roi
            self._post_calibration_seed_frames_remaining = 12

            # Seed normal tracking ROI from the same locked region
            self._tracking_roi = self._calibration_locked_roi

        self._calibration_locked_roi = None
        self._pre_calibration_roi = None

    def _consume_post_calibration_seed_frame(self):
        if self._post_calibration_seed_frames_remaining > 0:
            self._post_calibration_seed_frames_remaining -= 1
            if self._post_calibration_seed_frames_remaining <= 0:
                self._post_calibration_seed_frames_remaining = 0
                self._post_calibration_seed_roi = None

    @staticmethod
    def _err_vec(centroid: Tuple[int, int], target: Tuple[int, int]) -> np.ndarray:
        cx, cy = centroid
        tx, ty = target
        return np.array([cx - tx, cy - ty], dtype=float)

    def _can_reuse_jacobian(self) -> bool:
        if not self.cfg.reuse_jacobian:
            return False
        if self.J is None or self._J_calib_pose is None or self._J_calib_time is None:
            return False

        pose = self.robot.get_pose()
        p0 = self._J_calib_pose

        dx = abs(pose.x - p0.x)
        dy = abs(pose.y - p0.y)
        dz = abs(pose.z - p0.z)

        age = time.time() - self._J_calib_time

        if dx > self.cfg.reuse_max_xy_m or dy > self.cfg.reuse_max_xy_m:
            return False
        if dz > self.cfg.reuse_max_z_m:
            return False
        if age > self.cfg.reuse_max_age_s:
            return False

        return True

    def ensure_jacobian(self, *, delta_m: float = 0.015, settle_s: float = 0.4) -> None:
        if self._can_reuse_jacobian():
            return
        self._do_calibrate_jacobian(delta_m=delta_m, settle_s=settle_s)

    def _get_centroid_avg(
        self,
        *,
        samples: int = 5,
        sleep_s: float = 0.02,
        use_roi: Optional[bool] = None,
        update_tracking: bool = False,
    ) -> Optional[Tuple[int, int]]:
        pts = []

        for _ in range(samples):
            img = self._get_frame()
            H, W = img.shape[:2]
            target = self._make_target(img)

            roi_mode = self._choose_roi_mode() if use_roi is None else use_roi

            c = self.detector(
                img,
                sticker_color=self.cfg.sticker_color,
                target_px=target,
                use_roi=roi_mode
            )
            cv2.waitKey(1)
            self._consume_post_calibration_seed_frame()

            if c is not None:
                pts.append(c)
                if update_tracking and self.cfg.use_tracking_roi and self._calibration_locked_roi is None:
                    self._update_tracking_roi(c, W, H)

            time.sleep(sleep_s)

        if not pts:
            return None

        mean_x = int(round(np.mean([p[0] for p in pts])))
        mean_y = int(round(np.mean([p[1] for p in pts])))
        return (mean_x, mean_y)

    def _do_calibrate_jacobian(self, delta_m: float = 0.015, settle_s: float = 0.4):
        print("Calibrating Jacobian...")

        pose0 = self.robot.get_pose()

        def get_centroid_for_calib() -> Tuple[int, int]:
            c = self._get_centroid_avg(
                samples=5,
                sleep_s=0.02,
                use_roi=True,
                update_tracking=False
            )
            if c is None:
                raise RuntimeError(
                    f"{self.cfg.sticker_color.capitalize()} sticker not detected during Jacobian calibration."
                )
            return c

        self._lock_calibration_roi_from_current_detection(samples=5, pad_px=90)

        try:
            c0 = get_centroid_for_calib()

            self.robot.move_pose(PoseObject(
                pose0.x + delta_m, pose0.y,
                pose0.z, pose0.roll, pose0.pitch, pose0.yaw
            ))
            self._show_camera_for(settle_s)
            c_x_plus = get_centroid_for_calib()

            self.robot.move_pose(PoseObject(
                pose0.x - delta_m, pose0.y,
                pose0.z, pose0.roll, pose0.pitch, pose0.yaw
            ))
            self._show_camera_for(settle_s)
            c_x_minus = get_centroid_for_calib()

            self.robot.move_pose(pose0)
            self._show_camera_for(settle_s)

            self.robot.move_pose(PoseObject(
                pose0.x, pose0.y + delta_m,
                pose0.z, pose0.roll, pose0.pitch, pose0.yaw
            ))
            self._show_camera_for(settle_s)
            c_y_plus = get_centroid_for_calib()

            self.robot.move_pose(PoseObject(
                pose0.x, pose0.y - delta_m,
                pose0.z, pose0.roll, pose0.pitch, pose0.yaw
            ))
            self._show_camera_for(settle_s)
            c_y_minus = get_centroid_for_calib()

            self.robot.move_pose(pose0)
            self._show_camera_for(settle_s)

            px_x_plus, py_x_plus = c_x_plus
            px_x_minus, py_x_minus = c_x_minus
            px_y_plus, py_y_plus = c_y_plus
            px_y_minus, py_y_minus = c_y_minus

            # Central-difference Jacobian
            dpx_dx = (px_x_plus - px_x_minus) / (2.0 * delta_m)
            dpy_dx = (py_x_plus - py_x_minus) / (2.0 * delta_m)
            dpx_dy = (px_y_plus - px_y_minus) / (2.0 * delta_m)
            dpy_dy = (py_y_plus - py_y_minus) / (2.0 * delta_m)

            self.J = np.array([
                [dpx_dx, dpx_dy],
                [dpy_dx, dpy_dy]
            ], dtype=float)

            self._J_calib_pose = pose0
            self._J_calib_time = time.time()

            print("Jacobian estimated:")
            print(self.J)

        finally:
            self._unlock_calibration_roi()

    def calibrate_jacobian(self, delta_m: float = 0.015, settle_s: float = 0.4):
        self._apply_pre_vision_drop_once()
        self.ensure_jacobian(delta_m=delta_m, settle_s=settle_s)

    def __call__(self) -> CenteringResult:
        start = time.time()
        last_centroid: Optional[Tuple[int, int]] = None
        last_err = (0, 0)
        last_good_pose = self.robot.get_pose()

        self._apply_pre_vision_drop_once()
        self.ensure_jacobian(delta_m=0.015, settle_s=0.4)

        self._filtered_error = None

        for i in range(1, self.cfg.max_iters + 1):
            if (time.time() - start) > self.cfg.timeout_s:
                return CenteringResult(False, i, last_err, last_centroid)

            centroid = self._get_centroid_avg(
                samples=3,
                sleep_s=0.02,
                use_roi=None,
                update_tracking=True,
            )

            last_centroid = centroid

            if centroid is None:
                time.sleep(self.cfg.dt_s)
                continue

            img = self._get_frame()
            H, W = img.shape[:2]
            target = self._make_target(img)

            last_good_pose = self.robot.get_pose()

            e_raw = self._err_vec(centroid, target)

            # Low-pass filter
            alpha = 0.45
            if self._filtered_error is None:
                self._filtered_error = e_raw.copy()
            else:
                self._filtered_error = alpha * e_raw + (1.0 - alpha) * self._filtered_error

            e0_vec = self._filtered_error
            err_norm = float(np.linalg.norm(e0_vec))

            dx, dy = int(round(e0_vec[0])), int(round(e0_vec[1]))
            last_err = (dx, dy)

            if abs(dx) <= self.cfg.deadband_px and abs(dy) <= self.cfg.deadband_px:
                return CenteringResult(True, i, last_err, last_centroid)

            # Tuned for your normal 18–35 px operating range
            if err_norm > 35:
                lam = 0.8
                k = 0.16
                max_step = min(self.cfg.max_step_m, 0.0040)
            elif err_norm > 22:
                lam = 1.0
                k = 0.12
                max_step = min(self.cfg.max_step_m, 0.0025)
            else:
                lam = 1.3
                k = 0.08
                max_step = min(self.cfg.max_step_m, 0.0015)

            JT = self.J.T

            # Negative sign is important: move to reduce error
            dxy = -LA.solve(JT @ self.J + (lam ** 2) * np.eye(2), JT @ e0_vec)
            step = k * dxy

            step_x = float(_clamp(step[0], -max_step, max_step))
            step_y = float(_clamp(step[1], -max_step, max_step))

            pose0 = self.robot.get_pose()

            self.robot.move_pose(PoseObject(
                pose0.x + step_x,
                pose0.y + step_y,
                pose0.z,
                pose0.roll,
                pose0.pitch,
                pose0.yaw
            ))

            time.sleep(max(self.cfg.dt_s, 0.10))

            centroid_after = self._get_centroid_avg(
                samples=3,
                sleep_s=0.02,
                use_roi=None,
                update_tracking=True,
            )

            if centroid_after is None:
                self.robot.move_pose(last_good_pose)
                time.sleep(self.cfg.dt_s)
                continue

            img2 = self._get_frame()
            target2 = self._make_target(img2)
            e_after_raw = self._err_vec(centroid_after, target2)
            e_after = float(np.linalg.norm(e_after_raw))

            improve_margin = 0.5
            if e_after >= (err_norm - improve_margin):
                self.robot.move_pose(pose0)
                time.sleep(self.cfg.dt_s)

        return CenteringResult(False, self.cfg.max_iters, last_err, last_centroid)

@dataclass(frozen=True)
class PiecePickParams:
    vision_drop_m: float
    pick_drop_m: float
    place_drop_m: float


class ElectromagnetPiecePicker:
    def __init__(
        self,
        robot: NiryoRobot,
        *,
        pin_electromagnet: PinID = PinID.DO4,
        piece_params: Dict[str, PiecePickParams] | None = None,
        min_safe_z: float = 0.090,
        board_height_m: float = boardHeight,
    ):
        self.robot = robot
        self.pin = pin_electromagnet
        self.min_safe_z = float(min_safe_z)
        self.board_height_m = float(board_height_m)

        self.piece_params = piece_params or {
            symbol: PiecePickParams(
                vision_drop_m=PIECE_VISION_DROP_M[symbol],
                pick_drop_m=PIECE_HEIGHT_M[symbol],
                place_drop_m=PIECE_HEIGHT_M[symbol],
            )
            for symbol in PIECE_VISION_DROP_M.keys()
        }

        self._magnet_setup = False

    def _setup_magnet_once(self):
        if not self._magnet_setup:
            self.robot.setup_electromagnet(self.pin)
            self._magnet_setup = True

    @staticmethod
    def _with_z(pose: PoseObject, z: float) -> PoseObject:
        return PoseObject(pose.x, pose.y, z, pose.roll, pose.pitch, pose.yaw)

    def _get_piece_params(self, piece_type: str) -> PiecePickParams:
        piece_symbol = normalize_piece_symbol(piece_type)
        params = self.piece_params.get(piece_symbol)
        if params is None:
            raise ValueError(
                f"Unsupported piece_type '{piece_type}'. "
                f"Add it to the shared piece dictionaries at the top of the file."
            )
        return params

    def _get_piece_top_z(self, piece_type: str) -> float:
        piece_symbol = normalize_piece_symbol(piece_type)
        height = PIECE_HEIGHT_M.get(piece_symbol)
        if height is None:
            raise ValueError(
                f"Unsupported piece_type '{piece_type}'. "
                f"Add it to PIECE_HEIGHT_M at the top of the file."
            )
        return float(self.board_height_m + height)

    def pick_at(self, piece_type: str, pickup_xy_pose: PoseObject) -> None:
        self._setup_magnet_once()

        approach_z = float(pickup_xy_pose.z)
        down_z = self._get_piece_top_z(piece_type)
        if down_z < self.min_safe_z:
            down_z = self.min_safe_z

        approach = self._with_z(pickup_xy_pose, approach_z)
        down = self._with_z(pickup_xy_pose, down_z)

        print(f"[PICK] approach_z={approach_z:.3f}, down_z={down_z:.3f}")

        self.robot.move_pose(approach)
        self.robot.move_pose(down)

        pose_after = self.robot.get_pose()
        print(f"[PICK] actual_z={pose_after.z:.3f}")

        self.robot.activate_electromagnet(self.pin)
        self.robot.move_pose(approach)

    def place_at(
        self,
        piece_type: str,
        drop_xy_pose: PoseObject,
        *,
        place_drop_m: float | None = None,
    ) -> None:
        self._setup_magnet_once()

        params = self._get_piece_params(piece_type)

        original_z = float(drop_xy_pose.z)

        vision_z = original_z - float(params.vision_drop_m)
        if vision_z < self.min_safe_z:
            vision_z = self.min_safe_z

        final_z = self._get_piece_top_z(piece_type)
        if final_z < self.min_safe_z:
            final_z = self.min_safe_z

        original_pose = self._with_z(drop_xy_pose, original_z)
        vision_pose = self._with_z(drop_xy_pose, vision_z)
        final_pose = self._with_z(drop_xy_pose, final_z)

        print(f"[PLACE] original_z={original_z:.3f}, vision_z={vision_z:.3f}, final_z={final_z:.3f}")

        self.robot.move_pose(original_pose)
        self.robot.move_pose(vision_pose)
        self.robot.move_pose(final_pose)

        pose_after = self.robot.get_pose()
        print(f"[PLACE] actual_z={pose_after.z:.3f}")

        self.robot.deactivate_electromagnet(self.pin)
        self.robot.move_pose(original_pose)

    def __call__(
        self,
        *,
        piece_type: str,
        pickup_xy_pose: PoseObject,
        drop_xy_pose: PoseObject,
        place_drop_m: float | None = None,
    ) -> None:
        self.pick_at(piece_type, pickup_xy_pose)
        self.place_at(piece_type, drop_xy_pose, place_drop_m=place_drop_m)


@dataclass
class IntelligentPickupSystem:
    robot: NiryoRobot
    centerer: VisualCenteringController
    picker: ElectromagnetPiecePicker
    cfg: CenteringConfig

    @classmethod
    def create(
        cls,
        robot: NiryoRobot,
        *,
        pin_electromagnet: PinID = PinID.DO4,
        cfg: Optional[CenteringConfig] = None,
        pink_hsv: Optional[PinkThresholdHSV] = None,
        green_hsv: Optional[GreenThresholdHSV] = None,
        pink_mask_file: str | Path | None = None,
        green_mask_file: str | Path | None = None,
        detector_show: bool = True,
        detector_min_area_px: int = 400,
    ) -> "IntelligentPickupSystem":
        if cfg is None:
            cfg = CenteringConfig()

        base_dir = Path(__file__).resolve().parent

        if pink_mask_file is None:
            pink_mask_file = base_dir / "pinkMask.m"
        else:
            pink_mask_file = Path(pink_mask_file)

        if green_mask_file is None:
            green_mask_file = base_dir / "greenMask.m"
        else:
            green_mask_file = Path(green_mask_file)

        pink_wrap_hue = False

        if pink_hsv is None:
            pink_hsv = pink_threshold_from_matlab_file(pink_mask_file)
            pink_wrap_hue = pink_mask_uses_hue_wrap(pink_mask_file)

        if green_hsv is None:
            green_hsv = green_threshold_from_matlab_file(green_mask_file)

        print("Loaded HSV from MATLAB:")
        print("  Pink :", pink_hsv)
        print("  Green:", green_hsv)
        print("  Pink hue wrap:", pink_wrap_hue)

        detector = MultiColorCentroidDetector(
            pink_hsv_cfg=pink_hsv,
            green_hsv_cfg=green_hsv,
            min_area_px=detector_min_area_px,
            show=detector_show,
            pink_wrap_hue=pink_wrap_hue,
        )

        centerer = VisualCenteringController(
            robot=robot,
            detector=detector,
            cfg=cfg,
        )

        picker = ElectromagnetPiecePicker(
            robot,
            pin_electromagnet=pin_electromagnet,
        )

        return cls(
            robot=robot,
            centerer=centerer,
            picker=picker,
            cfg=cfg,
        )

    def move_piece(
        self,
        *,
        piece_colour: str,
        piece_type: str,
        pickup_pose: PoseObject,
        drop_pose: PoseObject,
        calibrate_delta_m: float = 0.015,
    ) -> CenteringResult:
        self.cfg.sticker_color = sticker_from_piece_colour(piece_colour)
        self.cfg.piece_type = normalize_piece_symbol(piece_type)

        self.centerer._tracking_roi = None
        self.centerer._pre_vision_done = False
        self.centerer.detector.roi = self.cfg.fixed_roi

        self.robot.move_pose(pickup_pose)

        self.centerer.calibrate_jacobian(delta_m=calibrate_delta_m)
        result = self.centerer()

        if not result.success:
            return result

        p = self.robot.get_pose()
        pickup_xy_pose = PoseObject(p.x, p.y, p.z, p.roll, p.pitch, p.yaw)
        self.picker.pick_at(self.cfg.piece_type, pickup_xy_pose)

        self.robot.move_pose(drop_pose)
        self.picker.place_at(self.cfg.piece_type, drop_pose)

        return result

    def show_debug_camera_until_quit(self):
        detector = self.centerer.detector

        print("Press Q or ESC to quit windows.")
        while True:
            img = uncompress_image(self.robot.get_img_compressed())
            img = cv2.flip(img, 0)

            h, w = img.shape[:2]
            ox, oy = self.cfg.target_offset_px
            target = (w // 2 + int(ox), h // 2 + int(oy))

            detector(
                img,
                sticker_color=self.cfg.sticker_color,
                target_px=target,
                use_roi=(detector.roi is not None),
            )

            key = cv2.waitKey(10) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                break