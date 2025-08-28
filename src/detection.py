import numpy as np
import cv2
from src import config

def find_lane_line_by_histogram(binary_img, wheel_x, wheel_y,
                                prev_detection=None):
    # Detect lane line in front of the wheel using vertical histogram.
    # Returns (x, y) of detected lane point or None if not found.

    # Extract narrow strip in front of the wheel
    x_min = max(0, wheel_x - config.COLUMN_WIDTH)
    x_max = min(binary_img.shape[1], wheel_x + config.COLUMN_WIDTH)
    strip = binary_img[0:wheel_y, x_min:x_max]
    if strip.size == 0:
        return None

    # Vertical histogram of white pixels
    histogram = np.sum(strip == 255, axis=1).astype(np.float32)
    if histogram.max() == 0:
        return None

    # Threshold relative to strongest row
    peak_threshold = histogram.max() * 0.2
    above = histogram >= peak_threshold

    # Find contiguous runs
    continuous_peaks = []
    start = None
    for i, is_peak in enumerate(above):
        if is_peak and start is None:
            start = i
        elif not is_peak and start is not None:
            end = i - 1
            length = end - start + 1
            total = histogram[start:end+1].sum()
            if length >= config.MIN_LANE_WIDTH and total >= (config.MIN_LANE_WIDTH * 2):
                continuous_peaks.append((start, end, length, total))
            start = None
    if start is not None:
        end = len(above) - 1
        length = end - start + 1
        total = histogram[start:end+1].sum()
        if length >= config.MIN_LANE_WIDTH and total >= (config.MIN_LANE_WIDTH * 2):
            continuous_peaks.append((start, end, length, total))

    if not continuous_peaks:
        return None

    # Temporal constraint: prefer continuity
    best_peak = None
    if prev_detection is not None:
        prev_row = prev_detection[1]
        candidates = [p for p in continuous_peaks if abs((p[0] + p[1]) / 2 - prev_row) <= config.MAX_JUMP]
        if candidates:
            best_peak = max(candidates, key=lambda p: p[3])

    # Fallback: strongest peak near centre of strip
    if best_peak is None:
        img_center = len(histogram) / 2
        best_peak = max(
            continuous_peaks,
            key=lambda p: (p[3], -abs(((p[0] + p[1]) / 2) - img_center))
        )

    start_idx, end_idx, _, _ = best_peak

    # Choose lane point according to config
    if config.LANE_POINT_MODE == "far":
        lane_y = end_idx
    elif config.LANE_POINT_MODE == "near":
        lane_y = start_idx
    elif config.LANE_POINT_MODE == "centre":
        lane_y = int(round((start_idx + end_idx) / 2))
    else:
        raise ValueError("LANE_POINT_MODE must be 'near', 'centre', or 'far'")

    return (wheel_x, lane_y)
