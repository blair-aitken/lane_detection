import cv2, os, json, csv, sys
import numpy as np
from tqdm import tqdm
import tkinter as tk
from tkinter import filedialog

# add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src import config
from src.measurement import pixel_to_real_world, calculate_distance


# Lane detection by histogram peak finding
def find_lane_line_by_histogram(binary_img, wheel_x, wheel_y, prev_detection=None):
    x_min = max(0, wheel_x - config.COLUMN_WIDTH)
    x_max = min(binary_img.shape[1], wheel_x + config.COLUMN_WIDTH)
    strip = binary_img[0:wheel_y, x_min:x_max]
    if strip.size == 0:
        return None

    histogram = np.sum(strip == 255, axis=1).astype(np.float32)
    if histogram.max() == 0:
        return None

    peak_threshold = histogram.max() * 0.2
    above = histogram >= peak_threshold

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

    # prefer temporal continuity if available
    best_peak = None
    if prev_detection is not None:
        prev_row = prev_detection[1]
        candidates = [p for p in continuous_peaks if abs((p[0] + p[1]) / 2 - prev_row) <= config.MAX_JUMP]
        if candidates:
            best_peak = max(candidates, key=lambda p: p[3])

    # fallback: strongest, then nearer center
    if best_peak is None:
        img_center = len(histogram) / 2
        best_peak = max(continuous_peaks, key=lambda p: (p[3], -abs(((p[0] + p[1]) / 2) - img_center)))

    start_idx, end_idx, _, _ = best_peak
    band_top, band_bottom = start_idx, end_idx

    # pick the farther side from the wheel
    d_top = abs(wheel_y - band_top)
    d_bottom = abs(wheel_y - band_bottom)
    lane_y = band_top if d_top >= d_bottom else band_bottom

    return (wheel_x, lane_y)


# File dialogs
def choose_files():
    root = tk.Tk()
    root.withdraw()

    video_path = filedialog.askopenfilename(
        title="Select input VIDEO",
        initialdir="data/videos",
        filetypes=[("Video files", "*.mkv *.mp4 *.avi *.mov"), ("All files", "*.*")]
    )
    if not video_path:
        raise RuntimeError("No video selected.")

    homog_path = filedialog.askopenfilename(
        title="Select HOMOGRAPHY JSON",
        initialdir="data/homography",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    if not homog_path:
        raise RuntimeError("No homography file selected.")

    root.destroy()
    return video_path, homog_path


# Main processing
def main():
    video_path, homog_path = choose_files()
    base_name = os.path.splitext(os.path.basename(video_path))[0]

    # outputs
    out_csv_path = os.path.join("output", "csv", f"{base_name}_measurements.csv")
    out_video_path = os.path.join("output", "videos", f"{base_name}_debug.mp4")
    os.makedirs(os.path.dirname(out_csv_path), exist_ok=True)
    os.makedirs(os.path.dirname(out_video_path), exist_ok=True)

    # load calibration
    calib_path = "data/calib/camera_intrinsics.npz"
    if not os.path.exists(calib_path):
        raise RuntimeError("No calibration found. Run calibration first.")
    calib = np.load(calib_path)
    camera_matrix, dist_coeffs = calib["camera_matrix"], calib["dist_coeffs"]

    # load homography (be tolerant to key names)
    with open(homog_path, "r") as f:
        data = json.load(f)
    H_list = data.get("homography_matrix") or data.get("H") or data
    homography_matrix = np.array(H_list, dtype=np.float32)
    if homography_matrix.shape != (3, 3):
        raise RuntimeError(f"Homography is not 3x3. Got shape {homography_matrix.shape} from {homog_path}")

    print(f"[measurement] video → {video_path}")
    print(f"[measurement] calibration → {calib_path}")
    print(f"[measurement] homography → {homog_path}")

    # open video + collect wheel click (ESC = abort)
    cap = cv2.VideoCapture(video_path)
    total_frames_meta = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # metadata

    ret, first_frame = cap.read()
    if not ret:
        raise RuntimeError("Could not read first frame")
    first_frame = cv2.undistort(first_frame, camera_matrix, dist_coeffs)

    wheel = {"x": None, "y": None, "set": False}

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            wheel["x"], wheel["y"], wheel["set"] = x, y, True

    win_title = "Click reference point (ESC to cancel)"
    cv2.imshow(win_title, first_frame)
    cv2.setMouseCallback(win_title, on_mouse)
    while True:
        k = cv2.waitKey(10) & 0xFF
        if wheel["set"] or k == 27:  # ESC
            break
    cv2.destroyAllWindows()
    if not wheel["set"]:
        raise RuntimeError("Wheel point not selected (ESC pressed).")

    # fps fallback (some containers report 0)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 1:
        fps = 30.0

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_vid = cv2.VideoWriter(out_video_path, fourcc, fps, (width, height))
    if not out_vid.isOpened():
        raise RuntimeError("Failed to open VideoWriter. Check codec/fps/frame size.")

    # stats
    all_distances = []
    nan_count = 0
    processed_frames = 0

    with open(out_csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["frame", "cm_to_lane"])

        prev_lane_detection = None

        with tqdm(total=total_frames_meta if total_frames_meta > 0 else None, unit="frame") as pbar:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_idx = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1

                undistorted = cv2.undistort(frame, camera_matrix, dist_coeffs)
                gray = cv2.cvtColor(undistorted, cv2.COLOR_BGR2GRAY)
                blurred = cv2.GaussianBlur(gray, config.GAUSSIAN_KERNEL, 0)
                adaptive = cv2.adaptiveThreshold(
                    blurred, 255,
                    cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY,
                    blockSize=config.BLOCK_SIZE, C=config.C_CONST
                )

                contours, _ = cv2.findContours(adaptive, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                clean = np.zeros_like(adaptive)
                for cnt in contours:
                    x, y, w, h = cv2.boundingRect(cnt)
                    if w * h >= config.MIN_CONTOUR_AREA and max(w, h) / (min(w, h) + 1e-5) >= config.MIN_ASPECT_RATIO:
                        cv2.drawContours(clean, [cnt], -1, 255, -1)
                adaptive = clean

                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, config.MORPH_KERNEL)
                adaptive = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, kernel, iterations=1)
                adaptive = cv2.morphologyEx(adaptive, cv2.MORPH_OPEN, kernel, iterations=1)

                pt_lane = find_lane_line_by_histogram(adaptive, wheel["x"], wheel["y"], prev_lane_detection)
                pt_wheel = (wheel["x"], wheel["y"])

                if pt_lane:
                    prev_lane_detection = pt_lane
                    real_wheel = pixel_to_real_world(pt_wheel, homography_matrix)
                    real_lane = pixel_to_real_world(pt_lane, homography_matrix)
                    dist = calculate_distance(real_wheel, real_lane)
                    lateral_pos = dist + config.WHEEL_OFFSET_CM
                    all_distances.append(lateral_pos)
                    writer.writerow([frame_idx, lateral_pos])

                    # overlay distance + line
                    cv2.line(undistorted, pt_wheel, pt_lane, (255, 255, 255), 2)
                    cv2.putText(undistorted, f"{lateral_pos:.1f}cm",
                                (undistorted.shape[1]-140, undistorted.shape[0]-20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 4)
                    cv2.putText(undistorted, f"{lateral_pos:.1f}cm",
                                (undistorted.shape[1]-140, undistorted.shape[0]-20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)
                else:
                    nan_count += 1
                    writer.writerow([frame_idx, "NaN"])

                # always overlay frame number
                cv2.putText(undistorted, f"Frame {frame_idx}",
                            (10, undistorted.shape[0] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2, cv2.LINE_AA)
                cv2.putText(undistorted, f"Frame {frame_idx}",
                            (10, undistorted.shape[0] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)

                # always write frame + update progress
                out_vid.write(undistorted)
                processed_frames += 1
                if pbar is not None:
                    pbar.update(1)

    cap.release()
    out_vid.release()
    print(f"[measurement] results → {out_csv_path}")
    print(f"[measurement] debug video → {out_video_path}")

    # summary statistics
    print("\n[summary statistics]")
    frames_valid = len(all_distances)
    frames_total = frames_valid + nan_count if (frames_valid + nan_count) > 0 else 1

    if frames_valid > 0:
        arr = np.array(all_distances, dtype=float)
        print(f"  Frames with valid data: {frames_valid} / {frames_total} ({frames_valid/frames_total*100:.1f}%)")
        print(f"  Frames with NaN: {nan_count} / {frames_total} ({nan_count/frames_total*100:.1f}%)")
        print(f"  Mean:   {np.mean(arr):.2f} cm")
        print(f"  Median: {np.median(arr):.2f} cm")
        print(f"  Min:    {np.min(arr):.2f} cm")
        print(f"  Max:    {np.max(arr):.2f} cm")
        if frames_valid > 1:
            print(f"  SD:     {np.std(arr, ddof=1):.2f} cm")
        else:
            print("  SD:     n/a (only one valid frame)")
    else:
        print(f"  Frames with valid data: 0 / {frames_total} (0.0%)")
        print(f"  Frames with NaN: {nan_count} / {frames_total} (100.0%)")
        print("  No valid lane detections.")


if __name__ == "__main__":
    main()
