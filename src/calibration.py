import cv2
import numpy as np
from typing import Iterable, Tuple, List

def _make_object_points(chessboard_dims: Tuple[int, int], square_size_mm: float) -> np.ndarray:
    """Create (N,3) grid of 3D object points in mm for a planar chessboard."""
    cols, rows = chessboard_dims  # inner corners per row/col (OpenCV uses (cols, rows))
    objp = np.zeros((cols * rows, 3), np.float32)
    objp[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2)
    objp *= float(square_size_mm)
    return objp

def calibrate_camera(
    image_files: Iterable[str],
    chessboard_dims: Tuple[int, int],
    square_size_mm: float,
):
    """
    Calibrate a pinhole camera from chessboard images.

    Returns:
        camera_matrix: (3,3) float64
        dist_coeffs:   (k,)  float64
        rms_error:     float (reprojection RMS)
        image_size:    (w, h)
        n_used:        int   (number of images with valid detections)
    """
    image_files = list(image_files)
    if not image_files:
        raise RuntimeError("No images provided to calibrate_camera().")

    objpoints: List[np.ndarray] = []
    imgpoints: List[np.ndarray] = []

    objp = _make_object_points(chessboard_dims, square_size_mm)

    gray_shape = None
    used = 0

    # sub-pixel corner refinement criteria
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-3)

    for fname in image_files:
        img = cv2.imread(fname)
        if img is None:
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        if gray_shape is None:
            gray_shape = gray.shape[::-1]  # (w, h)
        elif gray.shape[::-1] != gray_shape:
            raise RuntimeError(
                f"Inconsistent image size: {fname} has {gray.shape[::-1]}, expected {gray_shape}"
            )

        found, corners = cv2.findChessboardCorners(gray, chessboard_dims, None)
        if not found:
            continue

        corners_sub = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), crit)
        objpoints.append(objp)
        imgpoints.append(corners_sub)
        used += 1

    if not objpoints:
        raise RuntimeError("No valid chessboard detections found in supplied images.")

    # Calibrate
    rms, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, gray_shape, None, None
    )

    # Quick report
    print(f"[calibration] images used: {used}/{len(image_files)}")
    print(f"[calibration] image size : {gray_shape}")
    print(f"[calibration] RMS error  : {rms:.4f}")

    return camera_matrix, dist_coeffs, float(rms), tuple(gray_shape), int(used)