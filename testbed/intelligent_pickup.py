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

#needs edited to use Sams calculateIK stuff instead of move_pose

PIECE_Z_HEIGHTS: Dict[str, Dict[str, float]] = { #all moves are currently starting at z = 0.208
    "pawn": {
        "vision_drop_m": 0.010,
        "pick_drop_m": 0.029,
        "place_drop_m": 0.029,
    },
    "bishop": {
        "vision_drop_m": 0.010,
        "pick_drop_m": 0.029,
        "place_drop_m": 0.029,
    },
    "rook": {
        "vision_drop_m": 0.065,
        "pick_drop_m": 0.052,
        "place_drop_m": 0.050,
    },
    "knight": {
        "vision_drop_m": 0.010,
        "pick_drop_m": 0.029,
        "place_drop_m": 0.029,
    },
    "queen": {
        "vision_drop_m": 0.010,
        "pick_drop_m": 0.029,
        "place_drop_m": 0.029,
    },
    "king": {
        "vision_drop_m": 0.010,
        "pick_drop_m": 0.029,
        "place_drop_m": 0.029,
    },
}


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


def sticker_from_piece_colour(piece_colour: str) -> str:
    piece_colour = piece_colour.strip().lower()
    if piece_colour == "black":
        return "pink"
    if piece_colour == "white":
        return "green"
    raise ValueError("Piece colour must be 'black' or 'white'")


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


@dataclass  #(frozen=True)
class CenteringConfig:
    deadband_px: int = 15  #centered condition
    #k_m_per_px: float = 0.5 check if use
    max_step_m: float = 0.005  #maximum x/y move
    #sign_x: int = 1
    #sign_y: int = 1
    dt_s: float = 0.05  #sleep between iterations
    max_iters: int = 200  #max iterations
    timeout_s: float = 20.0  #hard time limit
    target_offset_px: Tuple[int, int] = (0, 0)  # (x_offset, y_offset) Pixel offset applied to the image center to define the target point.
    fixed_roi: Optional[Tuple[int, int, int, int]] = None  #ROI for detection restriction
    use_tracking_roi: bool = True  #dynamic ROI on detected centroid
    tracking_roi_size: Tuple[int, int] = (220, 220)  # (w,h) window around last centroid
    sticker_color: str = "pink"

    # Used by pre-vision Z lowering
    piece_type: Optional[str] = None

    # Jacobian caching / reuse
    reuse_jacobian: bool = True
    reuse_max_xy_m: float = 0.03    # reuse if |Δx|,|Δy| <= 3 cm from calibration pose
    reuse_max_z_m: float = 0.01     # reuse if |Δz| <= 1 cm
    reuse_max_age_s: float = 9999.0  # reuse if calibration age <= this (seconds)


@dataclass(frozen=True)
class CenteringResult:
    success: bool  #whether deadband was reached
    iters: int  #how many iteration ran
    last_error_px: Tuple[int, int]  #final pixel error
    last_centroid_px: Optional[Tuple[int, int]]  #final centroid position, or none if not detected


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


class VisualCenteringController:  #Read camera frame - Detect pink centroid (cx, cy) - Compute pixel error relative to target point - Convert pixel error into robot XY motion using a 2x2 Jacobian - Iterate until error is within deadband

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
        self.J: Optional[np.ndarray] = None  #jacobian will be filled by calibrate_jacobian()

    def _apply_pre_vision_drop_once(self):
        if self._pre_vision_done:
            return

        if self.cfg.piece_type is None:
            return

        # Pulled from the top-level tuning table so all real-board Z values
        # can be adjusted in one place.
        drop_table = {
            piece: values["vision_drop_m"]
            for piece, values in PIECE_Z_HEIGHTS.items()
        }

        # normalize piece type just in case caller passed "Rook", " rook ", etc.
        piece = self.cfg.piece_type.strip().lower()
        if piece not in drop_table:
            raise ValueError(
                f"Unsupported piece_type '{self.cfg.piece_type}'. "
                f"Add it to PIECE_Z_HEIGHTS at the top of the file."
            )
        drop = drop_table[piece]

        pose = self.robot.get_pose()
        new_z = pose.z - drop

        # Safety clamp so pre-vision drop can't go dangerously low.
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

    def _make_target(self, img: np.ndarray) -> Tuple[int, int]:
        H, W = img.shape[:2]
        ox, oy = self.cfg.target_offset_px
        return (W // 2 + int(ox), H // 2 + int(oy))

    def _choose_roi_mode(self) -> bool:
        # If tracking ROI already exists, use it
        if self.cfg.use_tracking_roi and self._tracking_roi is not None:
            self.detector.roi = self._tracking_roi
            return True
        # Otherwise, use fixed roi if provided
        return self.detector.roi is not None

    def _update_tracking_roi(self, centroid: Tuple[int, int], img_w: int, img_h: int):  #build new ROI window areound the detected centroid
        w_roi, h_roi = self.cfg.tracking_roi_size
        cx, cy = centroid
        x = int(cx - w_roi // 2)
        y = int(cy - h_roi // 2)
        self._tracking_roi = _clip_roi(x, y, w_roi, h_roi, img_w, img_h)

    @staticmethod
    def _err_vec(centroid: Tuple[int, int], target: Tuple[int, int]) -> np.ndarray:
        #Consistent convention: error = current - target (pixels).
        cx, cy = centroid
        tx, ty = target
        return np.array([cx - tx, cy - ty], dtype=float)

    def _can_reuse_jacobian(self) -> bool:
        """
        Decide whether the cached Jacobian is still valid enough to reuse.
        """
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
        """
        Ensure we have a Jacobian. Reuse cached J if valid, else calibrate.
        """
        if self._can_reuse_jacobian():
            # print("Reusing cached Jacobian.")
            return
        self._do_calibrate_jacobian(delta_m=delta_m, settle_s=settle_s)

    def _do_calibrate_jacobian(self, delta_m: float = 0.015, settle_s: float = 0.4):
        """
        Actual calibration routine (always calibrates).
        """
        print("Calibrating Jacobian...")

        pose0 = self.robot.get_pose()

        def get_centroid_for_calib() -> Tuple[int, int]:
            img = self._get_frame()
            target = self._make_target(img)
            use_roi = self._choose_roi_mode()

            c = self.detector(
                img,
                sticker_color=self.cfg.sticker_color,
                target_px=target,
                use_roi=use_roi
            )
            
            if c is None:
                raise RuntimeError(f"{self.cfg.sticker_color.capitalize()} sticker not detected during Jacobian calibration.")
            return c

        c0 = get_centroid_for_calib()

        # +X
        self.robot.move_pose(PoseObject(
            pose0.x + delta_m, pose0.y,
            pose0.z, pose0.roll, pose0.pitch, pose0.yaw
        ))
        time.sleep(settle_s)
        c1 = get_centroid_for_calib()

        self.robot.move_pose(pose0)
        time.sleep(settle_s)

        # +Y
        self.robot.move_pose(PoseObject(
            pose0.x, pose0.y + delta_m,
            pose0.z, pose0.roll, pose0.pitch, pose0.yaw
        ))
        time.sleep(settle_s)
        c2 = get_centroid_for_calib()

        self.robot.move_pose(pose0)
        time.sleep(settle_s)

        px0, py0 = c0
        px1, py1 = c1
        px2, py2 = c2

        dpx_dx = (px1 - px0) / delta_m
        dpy_dx = (py1 - py0) / delta_m
        dpx_dy = (px2 - px0) / delta_m
        dpy_dy = (py2 - py0) / delta_m

        self.J = np.array([[dpx_dx, dpx_dy],
                           [dpy_dx, dpy_dy]], dtype=float)

        # Cache when/where this J is valid
        self._J_calib_pose = pose0
        self._J_calib_time = time.time()

        print("Jacobian estimated:")
        print(self.J)

    def calibrate_jacobian(self, delta_m: float = 0.015, settle_s: float = 0.4):
        """ Reuse cached J if valid Otherwise calibrate """
        self._apply_pre_vision_drop_once()
        self.ensure_jacobian(delta_m=delta_m, settle_s=settle_s)

    def __call__(self) -> CenteringResult:
        start = time.time()
        last_centroid: Optional[Tuple[int, int]] = None
        last_err = (0, 0)
        last_good_pose = self.robot.get_pose()

        self._apply_pre_vision_drop_once()

        # Auto ensure Jacobian (reuses if possible)
        self.ensure_jacobian(delta_m=0.015, settle_s=0.4)

        for i in range(1, self.cfg.max_iters + 1):
            if (time.time() - start) > self.cfg.timeout_s:  #timeout check
                return CenteringResult(False, i, last_err, last_centroid)

            img = self._get_frame()  #grab image and compute target
            H, W = img.shape[:2]
            target = self._make_target(img)

            use_roi = self._choose_roi_mode()  #check for ROI cropping

            centroid = self.detector(
                img,
                sticker_color=self.cfg.sticker_color,
                target_px=target,
                use_roi=use_roi
            )#detect centroid
 
            last_centroid = centroid
            cv2.waitKey(1)  #OpenCV windows refresh

            if centroid is None:  #no detection = wait and retry
                time.sleep(self.cfg.dt_s)
                continue

            last_good_pose = self.robot.get_pose()  #safe pose if lost

            # Update tracking ROI after a good detection
            if self.cfg.use_tracking_roi:
                self._update_tracking_roi(centroid, W, H)

            e0_vec = self._err_vec(centroid, target)  #compute current pixel error and error norm
            err_norm = float(np.linalg.norm(e0_vec))
            dx, dy = int(e0_vec[0]), int(e0_vec[1])
            last_err = (dx, dy)

            if abs(dx) <= self.cfg.deadband_px and abs(dy) <= self.cfg.deadband_px:  #stop when within deadband
                return CenteringResult(True, i, last_err, last_centroid)

            # Convert pixel error to robot step using Jacobian
            # Damped least squares inversion: dxy = (J^T J + λ^2 I)^(-1) J^T e
            # e is pixel error, dxy is motion in meters.

            lam = 1.0
            JT = self.J.T
            dxy = LA.solve(JT @ self.J + (lam**2) * np.eye(2), JT @ e0_vec)

            if err_norm > 70:  #bigger steps when far and smaller when close
                k = 0.18
            elif err_norm > 30:
                k = 0.14
            else:
                k = 0.10

            step = k * dxy

            step_x = float(_clamp(step[0], -self.cfg.max_step_m, self.cfg.max_step_m))
            step_y = float(_clamp(step[1], -self.cfg.max_step_m, self.cfg.max_step_m))

            # Try step, keep only if it reduces error
            pose0 = self.robot.get_pose()
            e0 = float(np.linalg.norm(e0_vec))

            def measure_error_norm() -> Optional[float]:  #regrab frame, recompute target and measure new error
                img2 = self._get_frame()
                target2 = self._make_target(img2)

                # Recompute ROI mode
                use_roi2 = self._choose_roi_mode()

                c2 = self.detector(
                    img2,
                    sticker_color=self.cfg.sticker_color,
                    target_px=target2,
                    use_roi=use_roi2
                )
                if c2 is None:
                    return None
                e2 = self._err_vec(c2, target2)
                return float(np.linalg.norm(e2))

            def try_move(sign: float) -> bool:
                self.robot.move_pose(PoseObject(
                    pose0.x + sign * step_x,
                    pose0.y + sign * step_y,
                    pose0.z, pose0.roll, pose0.pitch, pose0.yaw
                ))
                time.sleep(self.cfg.dt_s)

                e1 = measure_error_norm()
                if e1 is None:
                    # lost detection go back to last good pose and stop trying
                    self.robot.move_pose(last_good_pose)
                    time.sleep(self.cfg.dt_s)
                    return False

                improve_margin = 2.0 if err_norm > 80 else 0.5  #bigger improvement when far away and smaller when close
                if e1 < (e0 - improve_margin):
                    return True

                self.robot.move_pose(pose0)  #not improved = revert
                time.sleep(self.cfg.dt_s)
                return False

            if not try_move(+1.0):  #if + doesnt improve try -
                _ = try_move(-1.0)

        return CenteringResult(False, self.cfg.max_iters, last_err, last_centroid)

@dataclass(frozen=True)
class PiecePickParams:
    vision_drop_m: float
    pick_drop_m: float
    place_drop_m: float  # how far to go DOWN from current Z to contact the piece


class ElectromagnetPiecePicker:
    def __init__(
        self,
        robot: NiryoRobot,
        *,
        pin_electromagnet: PinID = PinID.DO4,
        piece_params: Dict[str, PiecePickParams] | None = None,
        min_safe_z: float = 0.090,  # safety clamp: never go below this
    ):
        self.robot = robot
        self.pin = pin_electromagnet
        self.min_safe_z = float(min_safe_z)

        # These now come from the top-level PIECE_Z_HEIGHTS tuning table.
        self.piece_params = piece_params or {
            piece: PiecePickParams(
                vision_drop_m=values["vision_drop_m"],
                pick_drop_m=values["pick_drop_m"],
                place_drop_m=values["place_drop_m"],
            )
            for piece, values in PIECE_Z_HEIGHTS.items()
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
        piece = piece_type.strip().lower()
        params = self.piece_params.get(piece)
        if params is None:
            raise ValueError(
                f"Unsupported piece_type '{piece_type}'. "
                f"Add it to PIECE_Z_HEIGHTS at the top of the file."
            )
        return params    

    def pick_at(self, piece_type: str, pickup_xy_pose: PoseObject) -> None:
        self._setup_magnet_once()

        params = self._get_piece_params(piece_type)

        approach_z = float(pickup_xy_pose.z)
        down_z = approach_z - float(params.pick_drop_m)
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

        final_drop = params.place_drop_m if place_drop_m is None else float(place_drop_m)
        final_z = vision_z - final_drop
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
        self.cfg.piece_type = piece_type.strip().lower()

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