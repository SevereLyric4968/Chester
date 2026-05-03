from __future__ import annotations  # allow newer type hints

from dataclasses import dataclass  # make simple classes
from typing import Optional, Tuple, Dict, Literal  # type hints
from pathlib import Path  # file paths
import re  # search text patterns

import time  # delays and timers
import cv2  # OpenCV vision
import numpy as np  # arrays and maths
import numpy.linalg as LA  # matrix solving

from pyniryo import NiryoRobot, PoseObject, PinID  # Niryo robot tools
from pyniryo.vision.image_functions import uncompress_image  # decode camera image

# needs edited to use Sams calculateIK stuff instead of move_pose

PIECE_VISION_DROP_M: Dict[str, float] = {  # z drop before vision measure knights and kings
    "p": 0.052,  # pawn vision drop
    "b": 0.039,  # bishop vision drop
    "r": 0.048,  # rook vision drop
    "n": 0.0,  # knight drop needs measured
    "q": 0.036,  # queen vision drop
    "k": 0.0,  # king drop needs measured
}

PIECE_HEIGHT_M: Dict[str, float] = {  # piece heights in metres
    "p": 60.0 / 1000.0,  # pawn height
    "r": 64.5 / 1000.0,  # rook height
    "n": 69.0 / 1000.0,  # knight height
    "b": 73.5 / 1000.0,  # bishop height
    "q": 78.0 / 1000.0,  # queen height
    "k": 82.5 / 1000.0,  # king height
}

boardHeight = 0.0500 # Used so pickup Z is absolute: board height + piece height.

PIECE_NAME_TO_SYMBOL: Dict[str, str] = {  # convert names to symbols
    "pawn": "p",  # pawn name
    "rook": "r",  # rook name
    "knight": "n",  # knight name
    "bishop": "b",  # bishop name
    "queen": "q",  # queen name
    "king": "k",  # king name
    "p": "p",  # pawn symbol
    "r": "r",  # rook symbol
    "n": "n",  # knight symbol
    "b": "b",  # bishop symbol
    "q": "q",  # queen symbol
    "k": "k",  # king symbol
}


def normalise_piece_symbol(piece_type: str) -> str:  # make piece input one letter
    piece = piece_type.strip().lower()  # clean input text
    symbol = PIECE_NAME_TO_SYMBOL.get(piece)  # look up symbol
    if symbol is None:  # invalid piece
        raise ValueError(  # stop with helpful error
            f"Unsupported piece_type '{piece_type}'. "
            f"Use one of: pawn, rook, knight, bishop, queen, king "
            f"or symbols p, r, n, b, q, k."
        )
    return symbol  # return one-letter piece


def piece_colour_from_symbol(piece: str) -> str:  # get chess colour
    piece = piece.strip()  # clean text
    return "white" if piece.isupper() else "black"  # uppercase means white


def piece_type_from_symbol(piece: str) -> str:  # get piece type
    return normalise_piece_symbol(piece.strip().lower())  # return one-letter type


@dataclass(frozen=True)
class PinkThresholdHSV:  # stores pink HSV limits
    h_min: Optional[int] = None  # min hue
    h_max: Optional[int] = None  # max hue
    s_min: Optional[int] = None  # min saturation
    s_max: Optional[int] = None  # max saturation
    v_min: Optional[int] = None  # min value
    v_max: Optional[int] = None  # max value

    def __call__(self) -> Tuple[np.ndarray, np.ndarray]:  # return OpenCV bounds
        if None in (self.h_min, self.h_max, self.s_min, self.s_max, self.v_min, self.v_max):  # missing value
            raise ValueError("HSV thresholds not initialised. Load from MATLAB file first.")  # stop

        lower = np.array([self.h_min, self.s_min, self.v_min], dtype=np.uint8)  # lower HSV
        upper = np.array([self.h_max, self.s_max, self.v_max], dtype=np.uint8)  # upper HSV
        return lower, upper  # return limits


@dataclass(frozen=True)
class GreenThresholdHSV:  # stores green HSV limits
    h_min: Optional[int] = None  # min hue
    h_max: Optional[int] = None  # max hue
    s_min: Optional[int] = None  # min saturation
    s_max: Optional[int] = None  # max saturation
    v_min: Optional[int] = None  # min value
    v_max: Optional[int] = None  # max value

    def __call__(self) -> Tuple[np.ndarray, np.ndarray]:  # return OpenCV bounds
        if None in (self.h_min, self.h_max, self.s_min, self.s_max, self.v_min, self.v_max):  # missing value
            raise ValueError("HSV thresholds not initialised. Load from MATLAB file first.")  # stop

        lower = np.array([self.h_min, self.s_min, self.v_min], dtype=np.uint8)  # lower HSV
        upper = np.array([self.h_max, self.s_max, self.v_max], dtype=np.uint8)  # upper HSV
        return lower, upper  # return limits


@dataclass(frozen=True)
class MatlabHSVSpec:  # raw MATLAB HSV values
    h_min: float  # min hue 0-1
    h_max: float  # max hue 0-1
    s_min: float  # min saturation 0-1
    s_max: float  # max saturation 0-1
    v_min: float  # min value 0-1
    v_max: float  # max value 0-1
    hue_wrap: bool  # true if hue wraps around red


def _extract_matlab_scalar(text: str, name: str) -> float:  # read one MATLAB value
    pattern = rf"{name}\s*=\s*([0-9]*\.?[0-9]+)\s*;"  # value pattern
    m = re.search(pattern, text)  # find value
    if not m:  # not found
        raise ValueError(f"Could not find '{name}' in MATLAB mask file.")  # stop
    return float(m.group(1))  # return number


def load_matlab_hsv_mask_file(path: str | Path) -> MatlabHSVSpec:  # load MATLAB mask file
    path = Path(path)  # make path object
    text = path.read_text(encoding="utf-8")  # read file text

    h_min = _extract_matlab_scalar(text, "channel1Min")  # read hue min
    h_max = _extract_matlab_scalar(text, "channel1Max")  # read hue max
    s_min = _extract_matlab_scalar(text, "channel2Min")  # read sat min
    s_max = _extract_matlab_scalar(text, "channel2Max")  # read sat max
    v_min = _extract_matlab_scalar(text, "channel3Min")  # read val min
    v_max = _extract_matlab_scalar(text, "channel3Max")  # read val max

    hue_wrap = "|" in text and "channel1Min" in text and "channel1Max" in text  # detect wrap mask

    return MatlabHSVSpec(  # return mask data
        h_min=h_min,  # hue min
        h_max=h_max,  # hue max
        s_min=s_min,  # sat min
        s_max=s_max,  # sat max
        v_min=v_min,  # val min
        v_max=v_max,  # val max
        hue_wrap=hue_wrap,  # wrap flag
    )


def _matlab_h_to_cv(h: float) -> int:  # convert MATLAB hue
    return int(round(np.clip(h, 0.0, 1.0) * 179.0))  # OpenCV hue range


def _matlab_sv_to_cv(x: float) -> int:  # convert sat/value
    return int(round(np.clip(x, 0.0, 1.0) * 255.0))  # OpenCV sat/value range


def pink_threshold_from_matlab_file(path: str | Path) -> PinkThresholdHSV:  # make pink threshold
    spec = load_matlab_hsv_mask_file(path)  # load MATLAB data
    return PinkThresholdHSV(  # converted pink limits
        h_min=_matlab_h_to_cv(spec.h_min),  # hue min
        h_max=_matlab_h_to_cv(spec.h_max),  # hue max
        s_min=_matlab_sv_to_cv(spec.s_min),  # sat min
        s_max=_matlab_sv_to_cv(spec.s_max),  # sat max
        v_min=_matlab_sv_to_cv(spec.v_min),  # val min
        v_max=_matlab_sv_to_cv(spec.v_max),  # val max
    )


def green_threshold_from_matlab_file(path: str | Path) -> GreenThresholdHSV:  # make green threshold
    spec = load_matlab_hsv_mask_file(path)  # load MATLAB data
    return GreenThresholdHSV(  # converted green limits
        h_min=_matlab_h_to_cv(spec.h_min),  # hue min
        h_max=_matlab_h_to_cv(spec.h_max),  # hue max
        s_min=_matlab_sv_to_cv(spec.s_min),  # sat min
        s_max=_matlab_sv_to_cv(spec.s_max),  # sat max
        v_min=_matlab_sv_to_cv(spec.v_min),  # val min
        v_max=_matlab_sv_to_cv(spec.v_max),  # val max
    )


def pink_mask_uses_hue_wrap(path: str | Path) -> bool:  # check pink wrap
    return load_matlab_hsv_mask_file(path).hue_wrap  # return wrap flag


def sticker_from_piece_colour(piece_colour: str) -> str:  # choose sticker colour
    piece_colour = piece_colour.strip().lower()  # clean text
    if piece_colour == "black":  # black piece
        return "pink"  # black has pink sticker
    if piece_colour == "white":  # white piece
        return "green"  # white has green sticker
    raise ValueError("Piece colour must be 'black' or 'white'")  # invalid colour


def _clip_roi(x: int, y: int, w: int, h: int, img_w: int, img_h: int) -> Tuple[int, int, int, int]:  # keep ROI inside image
    x = max(0, min(x, img_w - 1))  # clamp x
    y = max(0, min(y, img_h - 1))  # clamp y
    w = max(1, min(w, img_w - x))  # clamp width
    h = max(1, min(h, img_h - y))  # clamp height
    return x, y, w, h  # return safe ROI


def crop_roi(img: np.ndarray, roi: Tuple[int, int, int, int]) -> Tuple[np.ndarray, Tuple[int, int]]:  # crop image area
    H, W = img.shape[:2]  # image size
    x, y, w, h = _clip_roi(*roi, W, H)  # safe ROI
    return img[y:y + h, x:x + w], (x, y)  # cropped image and offset


@dataclass
class MultiColorCentroidDetector:  # finds coloured sticker center
    pink_hsv_cfg: PinkThresholdHSV  # pink HSV config
    green_hsv_cfg: GreenThresholdHSV  # green HSV config
    min_area_px: int = 400  # ignore small blobs
    show: bool = True  # show debug windows
    morph_kernel_size: int = 5  # cleanup kernel size
    roi: Optional[Tuple[int, int, int, int]] = None  # search area
    draw_roi: bool = True  # draw ROI box
    pink_wrap_hue: bool = False  # pink hue wrap flag

    def _get_bounds(self, sticker_color: Literal["pink", "green"]) -> Tuple[np.ndarray, np.ndarray]:  # get HSV limits
        if sticker_color == "pink":  # pink requested
            return self.pink_hsv_cfg()  # pink limits
        if sticker_color == "green":  # green requested
            return self.green_hsv_cfg()  # green limits
        raise ValueError(f"Unsupported sticker_color: {sticker_color}")  # invalid colour

    def __call__(
        self,
        bgr_img: np.ndarray,  # camera image
        *,
        sticker_color: Literal["pink", "green"],  # colour to find
        target_px: Optional[Tuple[int, int]] = None,  # target point
        use_roi: bool = True,  # use ROI or full image
    ) -> Optional[Tuple[int, int]]:  # returns centroid or None

        H, W = bgr_img.shape[:2]  # image size

        if target_px is None:  # no target passed
            target_px = (W // 2, H // 2)  # use image center

        img_for_detect = bgr_img  # image used for detection
        offset = (0, 0)  # ROI offset
        roi_used = None  # current ROI

        if use_roi and self.roi is not None:  # crop if ROI enabled
            roi_used = self.roi  # save ROI
            img_for_detect, offset = crop_roi(bgr_img, self.roi)  # crop image

        hsv_img = cv2.cvtColor(img_for_detect, cv2.COLOR_BGR2HSV)  # convert to HSV
        lower, upper = self._get_bounds(sticker_color)  # get colour limits

        if sticker_color == "pink" and self.pink_wrap_hue and lower[0] > upper[0]:  # handle hue wrap
            lower1 = np.array([lower[0], lower[1], lower[2]], dtype=np.uint8)  # high hue lower
            upper1 = np.array([179, upper[1], upper[2]], dtype=np.uint8)  # high hue upper

            lower2 = np.array([0, lower[1], lower[2]], dtype=np.uint8)  # low hue lower
            upper2 = np.array([upper[0], upper[1], upper[2]], dtype=np.uint8)  # low hue upper

            mask1 = cv2.inRange(hsv_img, lower1, upper1)  # high hue mask
            mask2 = cv2.inRange(hsv_img, lower2, upper2)  # low hue mask
            mask = cv2.bitwise_or(mask1, mask2)  # combine masks
        else:
            mask = cv2.inRange(hsv_img, lower, upper)  # normal colour mask

        k = self.morph_kernel_size  # kernel size
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))  # round kernel
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)  # remove noise
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)  # fill gaps

        centroid_roi: Optional[Tuple[int, int]] = None  # centroid in ROI coords

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # find blobs
        if contours:  # blobs found
            largest = max(contours, key=cv2.contourArea)  # biggest blob
            if cv2.contourArea(largest) >= self.min_area_px:  # big enough
                m = cv2.moments(largest)  # blob moments
                if abs(m["m00"]) > 1e-6:  # avoid divide by zero
                    cx = int(m["m10"] / m["m00"])  # centroid x
                    cy = int(m["m01"] / m["m00"])  # centroid y
                    centroid_roi = (cx, cy)  # save centroid

        centroid_full: Optional[Tuple[int, int]] = None  # centroid in full image
        if centroid_roi is not None:  # found centroid
            cx_roi, cy_roi = centroid_roi  # ROI coords
            ox, oy = offset  # ROI offset
            centroid_full = (cx_roi + ox, cy_roi + oy)  # full image coords

        if self.show:  # show debug view
            vis = bgr_img.copy()  # copy image for drawing

            cv2.drawMarker(  # draw target cross
                vis, target_px, (0, 255, 255),
                markerType=cv2.MARKER_CROSS, markerSize=20, thickness=2
            )

            if self.draw_roi and roi_used is not None:  # draw ROI box
                x, y, w, h = roi_used  # ROI values
                x, y, w, h = _clip_roi(x, y, w, h, W, H)  # safe ROI
                cv2.rectangle(vis, (x, y), (x + w, y + h), (255, 255, 0), 2)  # draw box

            label_color = (255, 0, 255) if sticker_color == "pink" else (0, 255, 0)  # draw colour

            if centroid_full is not None:  # if found
                cx, cy = centroid_full  # centroid
                dx, dy = cx - target_px[0], cy - target_px[1]  # pixel error
                cv2.circle(vis, (cx, cy), 8, label_color, -1)  # draw dot
                cv2.line(vis, target_px, (cx, cy), label_color, 2)  # draw error line
                cv2.putText(  # show found text
                    vis, f"{sticker_color.upper()} FOUND err_px=({dx},{dy})",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, label_color, 2
                )
            else:
                cv2.putText(  # show not found text
                    vis, f"{sticker_color.upper()} NOT found",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
                )

            cv2.imshow("Niryo Camera (vis)", vis)  # show camera view
            cv2.imshow(f"{sticker_color.capitalize()} Mask", mask)  # show mask

        return centroid_full  # return detected center


@dataclass
class CenteringConfig:  # settings for centering
    deadband_px: int = 5  # acceptable pixel error
    max_step_m: float = 0.005  # biggest XY move
    dt_s: float = 0.05  # wait between moves
    max_iters: int = 200  # max loop count
    timeout_s: float = 20.0  # max run time
    target_offset_px: Tuple[int, int] = (0, 0)  # offset from image center
    fixed_roi: Optional[Tuple[int, int, int, int]] = None  # fixed search area
    use_tracking_roi: bool = True  # follow detected piece
    tracking_roi_size: Tuple[int, int] = (220, 220)  # tracking box size
    sticker_color: str = "pink"  # colour to detect

    piece_type: Optional[str] = None  # piece name or symbol

    reuse_jacobian: bool = True  # reuse old calibration
    reuse_max_xy_m: float = 0.03  # max XY change for reuse
    reuse_max_z_m: float = 0.01  # max Z change for reuse
    reuse_max_age_s: float = 9999.0  # max calibration age


@dataclass(frozen=True)
class CenteringResult:  # result from centering
    success: bool  # true if centered
    iters: int  # loops used
    last_error_px: Tuple[int, int]  # final pixel error
    last_centroid_px: Optional[Tuple[int, int]]  # final detected point


def _clamp(v: float, lo: float, hi: float) -> float:  # limit value
    return max(lo, min(hi, v))  # clamp result


class VisualCenteringController:  # moves robot to center sticker
    def __init__(
        self,
        robot: NiryoRobot,  # robot object
        detector: MultiColorCentroidDetector,  # vision detector
        cfg: Optional[CenteringConfig] = None,  # optional settings
    ):
        self.robot = robot  # store robot
        self.detector = detector  # store detector
        self.cfg = CenteringConfig() if cfg is None else cfg  # store config
        self._J_calib_pose: Optional[PoseObject] = None  # pose used for J
        self._J_calib_time: Optional[float] = None  # time J was made
        self._pre_vision_done = False  # z drop flag

        if self.cfg.fixed_roi is not None:  # if fixed ROI set
            self.detector.roi = self.cfg.fixed_roi  # use fixed ROI

        self._tracking_roi: Optional[Tuple[int, int, int, int]] = None  # moving ROI
        self.J: Optional[np.ndarray] = None  # image-to-robot Jacobian
        self._filtered_error: Optional[np.ndarray] = None  # smoothed error

        self._calibration_locked_roi: Optional[Tuple[int, int, int, int]] = None  # ROI locked for calibration
        self._pre_calibration_roi: Optional[Tuple[int, int, int, int]] = None  # old ROI before lock

        self._post_calibration_seed_roi: Optional[Tuple[int, int, int, int]] = None  # ROI after calibration
        self._post_calibration_seed_frames_remaining: int = 0  # frames left to use it

    def _apply_pre_vision_drop_once(self):  # lower camera once before vision
        if self._pre_vision_done:  # already done
            return  # skip

        if self.cfg.piece_type is None:  # no piece type
            return  # skip

        piece_symbol = normalise_piece_symbol(self.cfg.piece_type)  # get symbol

        if piece_symbol not in PIECE_VISION_DROP_M:  # unknown piece
            raise ValueError(  # stop
                f"Unsupported piece_type '{self.cfg.piece_type}'. "
                f"Add it to PIECE_VISION_DROP_M at the top of the file."
            )

        drop = PIECE_VISION_DROP_M[piece_symbol]  # get drop distance

        pose = self.robot.get_pose()  # current pose
        new_z = pose.z - drop  # lowered z

        MIN_SAFE_Z = 0.105  # safe z limit
        if new_z < MIN_SAFE_Z:  # too low
            new_z = MIN_SAFE_Z  # clamp z

        self.robot.move_pose(PoseObject(  # move lower
            pose.x,
            pose.y,
            new_z,
            pose.roll,
            pose.pitch,
            pose.yaw
        ))

        self._pre_vision_done = True  # mark done

    def _get_frame(self) -> np.ndarray:  # get camera image
        img = uncompress_image(self.robot.get_img_compressed())  # decode image
        return cv2.flip(img, 0)  # flip image

    def _show_camera_for(self, duration_s: float):  # show camera while waiting
        end_t = time.time() + duration_s  # end time
        while time.time() < end_t:  # wait loop
            img = self._get_frame()  # get frame
            target = self._make_target(img)  # get target
            use_roi = self._choose_roi_mode()  # choose ROI

            self.detector(  # run detector for display
                img,
                sticker_color=self.cfg.sticker_color,
                target_px=target,
                use_roi=use_roi
            )
            cv2.waitKey(1)  # refresh windows
            time.sleep(0.03)  # small delay

    def _make_target(self, img: np.ndarray) -> Tuple[int, int]:  # target pixel
        H, W = img.shape[:2]  # image size
        ox, oy = self.cfg.target_offset_px  # offset
        return (W // 2 + int(ox), H // 2 + int(oy))  # center plus offset

    def _choose_roi_mode(self) -> bool:  # choose search ROI
        if self._calibration_locked_roi is not None:  # calibration lock active
            self.detector.roi = self._calibration_locked_roi  # use locked ROI
            return True  # ROI on

        if self._post_calibration_seed_roi is not None and self._post_calibration_seed_frames_remaining > 0:  # seed ROI active
            self.detector.roi = self._post_calibration_seed_roi  # use seed ROI
            return True  # ROI on

        if self.cfg.use_tracking_roi and self._tracking_roi is not None:  # tracking ROI active
            self.detector.roi = self._tracking_roi  # use tracking ROI
            return True  # ROI on

        if self.cfg.fixed_roi is not None:  # fixed ROI exists
            self.detector.roi = self.cfg.fixed_roi  # use fixed ROI
            return True  # ROI on

        self.detector.roi = None  # use full image
        return False  # ROI off

    def _update_tracking_roi(self, centroid: Tuple[int, int], img_w: int, img_h: int):  # move ROI around piece
        w_roi, h_roi = self.cfg.tracking_roi_size  # ROI size
        cx, cy = centroid  # centroid point
        x = int(cx - w_roi // 2)  # ROI x
        y = int(cy - h_roi // 2)  # ROI y
        self._tracking_roi = _clip_roi(x, y, w_roi, h_roi, img_w, img_h)  # save safe ROI

    def _make_locked_roi_around_centroid(
        self,
        centroid: Tuple[int, int],  # center point
        img_w: int,  # image width
        img_h: int,  # image height
        pad_px: int = 90,  # padding
    ) -> Tuple[int, int, int, int]:  # locked ROI
        cx, cy = centroid  # center coords
        w = 2 * pad_px  # ROI width
        h = 2 * pad_px  # ROI height
        x = int(cx - pad_px)  # ROI x
        y = int(cy - pad_px)  # ROI y
        return _clip_roi(x, y, w, h, img_w, img_h)  # safe ROI

    def _lock_calibration_roi_from_current_detection(self, samples: int = 5, pad_px: int = 90) -> None:  # lock onto current piece
        img = self._get_frame()  # get frame
        H, W = img.shape[:2]  # image size

        pts = []  # detected points
        for _ in range(samples):  # sample several frames
            img_i = self._get_frame()  # get frame
            target_i = self._make_target(img_i)  # target point
            use_roi = self._choose_roi_mode()  # choose ROI
            c = self.detector(  # detect sticker
                img_i,
                sticker_color=self.cfg.sticker_color,
                target_px=target_i,
                use_roi=use_roi
            )
            cv2.waitKey(1)  # refresh windows
            if c is not None:  # if found
                pts.append(c)  # save point
            time.sleep(0.02)  # short delay

        if not pts:  # no detections
            raise RuntimeError(  # stop
                f"Could not lock calibration ROI because the {self.cfg.sticker_color} sticker was not detected."
            )

        mean_x = int(round(np.mean([p[0] for p in pts])))  # average x
        mean_y = int(round(np.mean([p[1] for p in pts])))  # average y
        locked_centroid = (mean_x, mean_y)  # averaged center

        self._pre_calibration_roi = self.detector.roi  # save old ROI
        self._calibration_locked_roi = self._make_locked_roi_around_centroid(  # make locked ROI
            locked_centroid, W, H, pad_px=pad_px
        )
        self.detector.roi = self._calibration_locked_roi  # use locked ROI

    def _unlock_calibration_roi(self) -> None:  # unlock calibration ROI
        if self._calibration_locked_roi is not None:  # if locked
            self._post_calibration_seed_roi = self._calibration_locked_roi  # keep it briefly
            self._post_calibration_seed_frames_remaining = 12  # number of frames
            self._tracking_roi = self._calibration_locked_roi  # seed tracking

        self._calibration_locked_roi = None  # clear lock
        self._pre_calibration_roi = None  # clear old ROI

    def _consume_post_calibration_seed_frame(self):  # count down seed frames
        if self._post_calibration_seed_frames_remaining > 0:  # if active
            self._post_calibration_seed_frames_remaining -= 1  # use one frame
            if self._post_calibration_seed_frames_remaining <= 0:  # finished
                self._post_calibration_seed_frames_remaining = 0  # clamp count
                self._post_calibration_seed_roi = None  # clear seed ROI

    @staticmethod
    def _err_vec(centroid: Tuple[int, int], target: Tuple[int, int]) -> np.ndarray:  # pixel error vector
        cx, cy = centroid  # current point
        tx, ty = target  # target point
        return np.array([cx - tx, cy - ty], dtype=float)  # current minus target

    def _can_reuse_jacobian(self) -> bool:  # check if old J is valid
        if not self.cfg.reuse_jacobian:  # reuse disabled
            return False  # cannot reuse
        if self.J is None or self._J_calib_pose is None or self._J_calib_time is None:  # missing data
            return False  # cannot reuse

        pose = self.robot.get_pose()  # current pose
        p0 = self._J_calib_pose  # calibration pose

        dx = abs(pose.x - p0.x)  # x difference
        dy = abs(pose.y - p0.y)  # y difference
        dz = abs(pose.z - p0.z)  # z difference

        age = time.time() - self._J_calib_time  # calibration age

        if dx > self.cfg.reuse_max_xy_m or dy > self.cfg.reuse_max_xy_m:  # too far in XY
            return False  # recalibrate
        if dz > self.cfg.reuse_max_z_m:  # too far in Z
            return False  # recalibrate
        if age > self.cfg.reuse_max_age_s:  # too old
            return False  # recalibrate

        return True  # reuse allowed

    def ensure_jacobian(self, *, delta_m: float = 0.015, settle_s: float = 0.4) -> None:  # get valid J
        if self._can_reuse_jacobian():  # if valid cached J
            return  # use it
        self._do_calibrate_jacobian(delta_m=delta_m, settle_s=settle_s)  # calibrate new J

    def _get_centroid_avg(
        self,
        *,
        samples: int = 5,  # number of frames
        sleep_s: float = 0.02,  # delay between frames
        use_roi: Optional[bool] = None,  # force ROI mode
        update_tracking: bool = False,  # update tracking ROI
    ) -> Optional[Tuple[int, int]]:  # average centroid
        pts = []  # detected points

        for _ in range(samples):  # sample loop
            img = self._get_frame()  # get frame
            H, W = img.shape[:2]  # image size
            target = self._make_target(img)  # target point

            roi_mode = self._choose_roi_mode() if use_roi is None else use_roi  # choose ROI mode

            c = self.detector(  # detect sticker
                img,
                sticker_color=self.cfg.sticker_color,
                target_px=target,
                use_roi=roi_mode
            )
            cv2.waitKey(1)  # refresh windows
            self._consume_post_calibration_seed_frame()  # update seed count

            if c is not None:  # found point
                pts.append(c)  # save point
                if update_tracking and self.cfg.use_tracking_roi and self._calibration_locked_roi is None:  # update ROI
                    self._update_tracking_roi(c, W, H)  # follow piece

            time.sleep(sleep_s)  # short delay

        if not pts:  # no points found
            return None  # failed detection

        mean_x = int(round(np.mean([p[0] for p in pts])))  # average x
        mean_y = int(round(np.mean([p[1] for p in pts])))  # average y
        return (mean_x, mean_y)  # averaged point

    def _do_calibrate_jacobian(self, delta_m: float = 0.015, settle_s: float = 0.4):  # calibrate image motion
        print("Calibrating Jacobian...")  # status

        pose0 = self.robot.get_pose()  # starting pose

        def get_centroid_for_calib() -> Tuple[int, int]:  # get reliable centroid
            c = self._get_centroid_avg(  # average samples
                samples=5,
                sleep_s=0.02,
                use_roi=True,
                update_tracking=False
            )
            if c is None:  # not detected
                raise RuntimeError(  # stop calibration
                    f"{self.cfg.sticker_color.capitalize()} sticker not detected during Jacobian calibration."
                )
            return c  # return centroid

        self._lock_calibration_roi_from_current_detection(samples=5, pad_px=90)  # lock to piece

        try:  # always unlock after
            _ = get_centroid_for_calib()  # check starting detection

            self.robot.move_pose(PoseObject(  # move +X
                pose0.x + delta_m, pose0.y,
                pose0.z, pose0.roll, pose0.pitch, pose0.yaw
            ))
            self._show_camera_for(settle_s)  # let image settle
            c_x_plus = get_centroid_for_calib()  # measure +X

            self.robot.move_pose(PoseObject(  # move -X
                pose0.x - delta_m, pose0.y,
                pose0.z, pose0.roll, pose0.pitch, pose0.yaw
            ))
            self._show_camera_for(settle_s)  # let image settle
            c_x_minus = get_centroid_for_calib()  # measure -X

            self.robot.move_pose(pose0)  # return center
            self._show_camera_for(settle_s)  # let image settle

            self.robot.move_pose(PoseObject(  # move +Y
                pose0.x, pose0.y + delta_m,
                pose0.z, pose0.roll, pose0.pitch, pose0.yaw
            ))
            self._show_camera_for(settle_s)  # let image settle
            c_y_plus = get_centroid_for_calib()  # measure +Y

            self.robot.move_pose(PoseObject(  # move -Y
                pose0.x, pose0.y - delta_m,
                pose0.z, pose0.roll, pose0.pitch, pose0.yaw
            ))
            self._show_camera_for(settle_s)  # let image settle
            c_y_minus = get_centroid_for_calib()  # measure -Y

            self.robot.move_pose(pose0)  # return start pose
            self._show_camera_for(settle_s)  # let image settle

            px_x_plus, py_x_plus = c_x_plus  # +X pixels
            px_x_minus, py_x_minus = c_x_minus  # -X pixels
            px_y_plus, py_y_plus = c_y_plus  # +Y pixels
            px_y_minus, py_y_minus = c_y_minus  # -Y pixels

            dpx_dx = (px_x_plus - px_x_minus) / (2.0 * delta_m)  # px change per X metre
            dpy_dx = (py_x_plus - py_x_minus) / (2.0 * delta_m)  # py change per X metre
            dpx_dy = (px_y_plus - px_y_minus) / (2.0 * delta_m)  # px change per Y metre
            dpy_dy = (py_y_plus - py_y_minus) / (2.0 * delta_m)  # py change per Y metre

            self.J = np.array([  # build Jacobian matrix
                [dpx_dx, dpx_dy],
                [dpy_dx, dpy_dy]
            ], dtype=float)

            self._J_calib_pose = pose0  # save calibration pose
            self._J_calib_time = time.time()  # save calibration time

            print("Jacobian estimated:")  # status
            print(self.J)  # show matrix

        finally:
            self._unlock_calibration_roi()  # unlock ROI

    def calibrate_jacobian(self, delta_m: float = 0.015, settle_s: float = 0.4):  # public calibrate
        self._apply_pre_vision_drop_once()  # lower first
        self.ensure_jacobian(delta_m=delta_m, settle_s=settle_s)  # calibrate or reuse

    def _close_windows(self):  # close OpenCV windows
        if not self.detector.show:  # windows not used
            return  # skip
        try:  # avoid crash if missing
            cv2.destroyWindow("Niryo Camera (vis)")  # close camera
            cv2.destroyWindow(f"{self.cfg.sticker_color.capitalize()} Mask")  # close mask
            cv2.waitKey(1)  # refresh close
        except cv2.error:  # window error
            pass  # ignore

    def __call__(self) -> CenteringResult:  # run centering loop
        start = time.time()  # start time
        last_centroid: Optional[Tuple[int, int]] = None  # last point
        last_err = (0, 0)  # last error
        last_good_pose = self.robot.get_pose()  # safe pose

        self._apply_pre_vision_drop_once()  # lower for vision
        self.ensure_jacobian(delta_m=0.015, settle_s=0.4)  # make sure J exists

        if self.J is None:  # J missing
            raise RuntimeError("Jacobian was not calibrated.")  # stop

        self._filtered_error = None  # reset smoothing

        for i in range(1, self.cfg.max_iters + 1):  # control loop
            if (time.time() - start) > self.cfg.timeout_s:  # timeout
                self._close_windows()  # close windows
                return CenteringResult(False, i, last_err, last_centroid)  # failed

            centroid = self._get_centroid_avg(  # get smoothed centroid
                samples=3,
                sleep_s=0.02,
                use_roi=None,
                update_tracking=True,
            )

            last_centroid = centroid  # save point

            if centroid is None:  # no detection
                time.sleep(self.cfg.dt_s)  # wait
                continue  # retry

            img = self._get_frame()  # get frame
            target = self._make_target(img)  # target point

            last_good_pose = self.robot.get_pose()  # save safe pose

            e_raw = self._err_vec(centroid, target)  # raw pixel error

            alpha = 0.45  # filter strength
            if self._filtered_error is None:  # first frame
                self._filtered_error = e_raw.copy()  # start filter
            else:
                self._filtered_error = alpha * e_raw + (1.0 - alpha) * self._filtered_error  # smooth error

            e0_vec = self._filtered_error  # use filtered error
            err_norm = float(np.linalg.norm(e0_vec))  # error size

            dx, dy = int(round(e0_vec[0])), int(round(e0_vec[1]))  # pixel error ints
            last_err = (dx, dy)  # save error

            if abs(dx) <= self.cfg.deadband_px and abs(dy) <= self.cfg.deadband_px:  # centered enough
                self._close_windows()  # close windows
                return CenteringResult(True, i, last_err, last_centroid)  # success

            if err_norm > 35:  # far away
                lam = 0.8  # damping
                k = 0.16  # gain
                max_step = min(self.cfg.max_step_m, 0.0040)  # step limit
            elif err_norm > 22:  # medium error
                lam = 1.0  # damping
                k = 0.12  # gain
                max_step = min(self.cfg.max_step_m, 0.0025)  # step limit
            else:  # close to target
                lam = 1.3  # more damping
                k = 0.08  # smaller gain
                max_step = min(self.cfg.max_step_m, 0.0015)  # small step

            JT = self.J.T  # transpose Jacobian

            dxy = -LA.solve(JT @ self.J + (lam ** 2) * np.eye(2), JT @ e0_vec)  # robot XY correction
            step = k * dxy  # scale correction

            step_x = float(_clamp(step[0], -max_step, max_step))  # limit X step
            step_y = float(_clamp(step[1], -max_step, max_step))  # limit Y step

            pose0 = self.robot.get_pose()  # pose before move

            self.robot.move_pose(PoseObject(  # apply XY move
                pose0.x + step_x,
                pose0.y + step_y,
                pose0.z,
                pose0.roll,
                pose0.pitch,
                pose0.yaw
            ))

            time.sleep(max(self.cfg.dt_s, 0.10))  # wait after move

            centroid_after = self._get_centroid_avg(  # check new centroid
                samples=3,
                sleep_s=0.02,
                use_roi=None,
                update_tracking=True,
            )

            if centroid_after is None:  # lost target
                self.robot.move_pose(last_good_pose)  # go back
                time.sleep(self.cfg.dt_s)  # wait
                continue  # retry

            img2 = self._get_frame()  # new frame
            target2 = self._make_target(img2)  # new target
            e_after_raw = self._err_vec(centroid_after, target2)  # new error vector
            e_after = float(np.linalg.norm(e_after_raw))  # new error size

            improve_margin = 0.5  # required improvement
            if e_after >= (err_norm - improve_margin):  # not improved
                self.robot.move_pose(pose0)  # undo move
                time.sleep(self.cfg.dt_s)  # wait

        self._close_windows()  # close windows
        return CenteringResult(False, self.cfg.max_iters, last_err, last_centroid)  # failed


class ElectromagnetPiecePicker:  # controls magnet pickup
    def __init__(
        self,
        robot: NiryoRobot,  # robot object
        *,
        pin_electromagnet: PinID = PinID.DO4,  # magnet pin
        min_safe_z: float = 0.090,  # lowest safe z
        board_height_m: float = boardHeight,  # absolute board surface height
    ):
        self.robot = robot  # store robot
        self.pin = pin_electromagnet  # store pin
        self.min_safe_z = float(min_safe_z)  # store safe z
        self.board_height_m = float(board_height_m)  # store board height
        self._magnet_setup = False  # setup flag

    def _setup_magnet_once(self):  # setup magnet once
        if not self._magnet_setup:  # not done yet
            self.robot.setup_electromagnet(self.pin)  # setup magnet
            self._magnet_setup = True  # mark setup done

    @staticmethod
    def _with_z(pose: PoseObject, z: float) -> PoseObject:  # copy pose with new z
        return PoseObject(pose.x, pose.y, z, pose.roll, pose.pitch, pose.yaw)  # new pose

    def _get_piece_height(self, piece_type: str) -> float:  # get height by piece
        piece_symbol = normalise_piece_symbol(piece_type)  # normalise piece
        height = PIECE_HEIGHT_M.get(piece_symbol)  # look up height

        if height is None:  # missing height
            raise ValueError(
                f"Unsupported piece_type '{piece_type}'. "
                f"Add it to PIECE_HEIGHT_M at the top of the file."
            )

        return float(height)  # return height

    def _get_piece_top_z(self, piece_type: str) -> float:  # absolute z of piece top
        return float(self.board_height_m + self._get_piece_height(piece_type))

    def pick_at(
        self,
        piece_type: str,
        pickup_xy_pose: PoseObject,
        pickup_z: float | None = None,  # kept for compatibility, no longer used
    ) -> None:  # pick at pose
        self._setup_magnet_once()  # ensure magnet ready

        approach_z = float(pickup_xy_pose.z)  # current safe z
        down_z = self._get_piece_top_z(piece_type)  # board height + piece height

        if down_z < self.min_safe_z:  # too low
            down_z = self.min_safe_z  # clamp z

        approach = self._with_z(pickup_xy_pose, approach_z)  # approach pose
        down = self._with_z(pickup_xy_pose, down_z)  # pickup pose

        print(
            f"[PICK] board_z={self.board_height_m:.3f}, "
            f"approach_z={approach_z:.3f}, down_z={down_z:.3f}"
        )

        self.robot.move_pose(approach)  # move above piece
        self.robot.move_pose(down)  # move down to piece

        pose_after = self.robot.get_pose()  # read actual pose
        print(f"[PICK] actual_z={pose_after.z:.3f}")  # print z

        self.robot.activate_electromagnet(self.pin)  # turn magnet on
        self.robot.move_pose(approach)  # lift piece

    def blind_pick_at(
        self,
        piece_type: str,
        pickup_xy_pose: PoseObject,
        pickup_z: float | None = None,  # kept for compatibility, no longer used
    ) -> None:  # pick without vision
        self._setup_magnet_once()  # ensure magnet ready

        approach_z = float(pickup_xy_pose.z)  # current safe z
        down_z = self._get_piece_top_z(piece_type)  # board height + piece height

        if down_z < self.min_safe_z:  # too low
            down_z = self.min_safe_z  # clamp z

        down = self._with_z(pickup_xy_pose, down_z)  # pickup pose

        print(
            f"[BLIND PICK] board_z={self.board_height_m:.3f}, "
            f"approach_z={approach_z:.3f}, down_z={down_z:.3f}"
        )

        self.robot.move_pose(pickup_xy_pose)  # move to approximate pose
        self.robot.move_pose(down)  # move down

        pose_after = self.robot.get_pose()  # read pose
        print(f"[BLIND PICK] actual_z={pose_after.z:.3f}")  # print z

        self.robot.activate_electromagnet(self.pin)  # turn magnet on
        self.robot.move_pose(pickup_xy_pose)  # lift piece


@dataclass
class IntelligentPickupSystem:  # combines vision and picker
    robot: NiryoRobot  # robot object
    centerer: VisualCenteringController  # centering controller
    picker: ElectromagnetPiecePicker  # magnet picker
    cfg: CenteringConfig  # shared config

    @classmethod
    def create(
        cls,
        robot: NiryoRobot,  # robot object
        *,
        pin_electromagnet: PinID = PinID.DO4,  # magnet pin
        pink_hsv: Optional[PinkThresholdHSV] = None,  # optional pink limits
        green_hsv: Optional[GreenThresholdHSV] = None,  # optional green limits
        pink_mask_file: str | Path | None = None,  # pink mask path
        green_mask_file: str | Path | None = None,  # green mask path
        detector_show: bool = True,  # show debug windows
        detector_min_area_px: int = 400,  # min blob size
        board_height_m: float = boardHeight,  # board surface height
    ) -> "IntelligentPickupSystem":  # return system
        cfg = CenteringConfig(
            deadband_px=5,
            max_step_m=0.004,
            dt_s=0.15,
            max_iters=600,
            timeout_s=59.0,
            target_offset_px=(-40, -60),
            use_tracking_roi=True,
            tracking_roi_size=(260, 260),
        )

        base_dir = Path(__file__).resolve().parent  # folder of this file

        if pink_mask_file is None:  # no pink path
            pink_mask_file = base_dir / "pinkMask.m"  # default pink file
        else:
            pink_mask_file = Path(pink_mask_file)  # use given path

        if green_mask_file is None:  # no green path
            green_mask_file = base_dir / "greenMask.m"  # default green file
        else:
            green_mask_file = Path(green_mask_file)  # use given path

        pink_wrap_hue = False  # default no wrap

        if pink_hsv is None:  # need load pink
            pink_hsv = pink_threshold_from_matlab_file(pink_mask_file)  # load pink HSV
            pink_wrap_hue = pink_mask_uses_hue_wrap(pink_mask_file)  # check wrap

        if green_hsv is None:  # need load green
            green_hsv = green_threshold_from_matlab_file(green_mask_file)  # load green HSV

        print("Loaded HSV from MATLAB:")  # status
        print("  Pink :", pink_hsv)  # show pink values
        print("  Green:", green_hsv)  # show green values
        print("  Pink hue wrap:", pink_wrap_hue)  # show wrap flag

        detector = MultiColorCentroidDetector(  # make detector
            pink_hsv_cfg=pink_hsv,
            green_hsv_cfg=green_hsv,
            min_area_px=detector_min_area_px,
            show=detector_show,
            pink_wrap_hue=pink_wrap_hue,
        )

        centerer = VisualCenteringController(  # make centerer
            robot=robot,
            detector=detector,
            cfg=cfg,
        )

        picker = ElectromagnetPiecePicker(  # make picker
            robot,
            pin_electromagnet=pin_electromagnet,
            board_height_m=board_height_m,
        )

        return cls(  # return full system
            robot=robot,
            centerer=centerer,
            picker=picker,
            cfg=cfg,
        )

    def show_debug_camera_until_quit(self):  # show camera debug
        detector = self.centerer.detector  # get detector

        print("Press Q or ESC to quit windows.")  # instructions
        while True:  # display loop
            img = uncompress_image(self.robot.get_img_compressed())  # get camera image
            img = cv2.flip(img, 0)  # flip image

            h, w = img.shape[:2]  # image size
            ox, oy = self.cfg.target_offset_px  # target offset
            target = (w // 2 + int(ox), h // 2 + int(oy))  # target point

            detector(  # run detection display
                img,
                sticker_color=self.cfg.sticker_color,
                target_px=target,
                use_roi=(detector.roi is not None),
            )

            key = cv2.waitKey(10) & 0xFF  # read key
            if key in (ord("q"), ord("Q"), 27):  # q or esc
                break  # exit loop

        try:  # close windows safely
            cv2.destroyWindow("Niryo Camera (vis)")  # close camera
            cv2.destroyWindow(f"{self.cfg.sticker_color.capitalize()} Mask")  # close mask
            cv2.waitKey(1)  # refresh close
        except cv2.error:  # window error
            pass  # ignore

    def pickup_piece(
        self,
        *,
        piece: str,  # chess piece symbol
        pickup_z: float = boardHeight,  # kept for compatibility; picker uses boardHeight internally
        approximate_pose: Optional[PoseObject] = None,  # starting pose
        calibrate_delta_m: float = 0.015,  # calibration move size
        fallback_to_blind_pick: bool = True,  # allow blind fallback
    ) -> CenteringResult:  # return centering result
        piece_type = piece_type_from_symbol(piece)  # get piece type
        piece_colour = piece_colour_from_symbol(piece)  # get piece colour

        self.cfg.sticker_color = sticker_from_piece_colour(piece_colour)  # set sticker colour
        self.cfg.piece_type = piece_type  # set piece type

        self.centerer._tracking_roi = None  # reset tracking ROI
        self.centerer._pre_vision_done = False  # reset vision drop
        self.centerer._filtered_error = None  # reset smoothing
        self.centerer._calibration_locked_roi = None  # reset calibration lock
        self.centerer._post_calibration_seed_roi = None  # reset seed ROI
        self.centerer._post_calibration_seed_frames_remaining = 0  # reset seed count
        self.centerer.detector.roi = self.cfg.fixed_roi  # restore fixed ROI

        if approximate_pose is None:  # no start pose given
            approximate_pose = self.robot.get_pose()  # use current pose

        self.robot.move_pose(approximate_pose)  # move near piece

        self.centerer.calibrate_jacobian(delta_m=calibrate_delta_m)  # calibrate camera motion
        result = self.centerer()  # center on sticker

        if result.success:  # if centered
            p = self.robot.get_pose()  # get corrected pose
            corrected = PoseObject(p.x, p.y, p.z, p.roll, p.pitch, p.yaw)  # copy pose
            self.picker.pick_at(piece_type, corrected, pickup_z)  # pick piece
            return result  # return success

        if fallback_to_blind_pick:  # if vision failed but fallback allowed
            print("[INTELLIGENT PICKUP] Centering failed, falling back to blind pickup at approximate pose.")  # status
            self.robot.move_pose(approximate_pose)  # go back to approximate pose
            self.picker.blind_pick_at(piece_type, approximate_pose, pickup_z)  # blind pick
            return CenteringResult(True, result.iters, result.last_error_px, result.last_centroid_px)  # report picked

        return result  # return failed result
