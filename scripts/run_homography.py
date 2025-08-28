import cv2, json, os, sys
import numpy as np
import tkinter as tk
from tkinter import filedialog

# add src/ to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.utils import find_calibration_file
from src.homography import compute_homography, save_homography


def choose_video():
    root = tk.Tk(); root.withdraw()
    video_path = filedialog.askopenfilename(
        title="Select HOMOGRAPHY video",
        initialdir="data/videos",
        filetypes=[("Video files", "*.mp4 *.mkv *.avi *.mov"), ("All files", "*.*")]
    )
    root.destroy()
    if not video_path:
        raise RuntimeError("No video selected.")
    return video_path


def pick_points(img, min_points=4):
    pts = []
    disp = img.copy()

    def redraw():
        nonlocal disp
        disp = img.copy()
        h, w = disp.shape[:2]

        # Instructions
        msg = "u=Undo   Esc=Exit   Enter=Save"
        cv2.putText(disp, msg, (6, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2, cv2.LINE_AA)
        cv2.putText(disp, msg, (6, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1, cv2.LINE_AA)

        # Points
        for i, (x, y) in enumerate(pts, 1):
            cv2.circle(disp, (x, y), 4, (0,0,0), 2)
            cv2.circle(disp, (x, y), 3, (255,255,255), -1)
            cv2.putText(disp, str(i), (x+8, y-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0,0,0), 2, cv2.LINE_AA)
            cv2.putText(disp, str(i), (x+8, y-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (255,255,255), 1, cv2.LINE_AA)

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            pts.append((x, y))
            redraw()

    redraw()
    cv2.imshow("Select board corners", disp)
    cv2.setMouseCallback("Select board corners", on_mouse)

    while True:
        cv2.imshow("Select board corners", disp)
        k = cv2.waitKey(1) & 0xFF
        if k in (13, 10):  # Enter
            if len(pts) >= min_points:
                break
        elif k == 27:      # Esc -> cancel
            pts = []
            break
        elif k in (ord('u'), ord('U')):
            if pts:
                pts.pop()
                redraw()

    cv2.destroyAllWindows()
    return pts


def pixel_to_real_world(pixel_point, H):
    p = np.array([[pixel_point[0], pixel_point[1], 1]], dtype=np.float32).T
    world = np.dot(H, p)
    return (world[0] / world[2])[0], (world[1] / world[2])[0]


def main():
    # Load calibration
    calib_path = find_calibration_file()
    calib = np.load(calib_path)
    camera_matrix, dist_coeffs = calib["camera_matrix"], calib["dist_coeffs"]

    # Select video
    video_path = choose_video()
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    out_json = os.path.join("data", "homography", f"{base_name}_homography.json")

    # Always overwrite existing JSON
    if os.path.exists(out_json):
        print(f"[homography] Overwriting existing file → {out_json}")

    # Get first frame
    cap = cv2.VideoCapture(video_path)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError(f"Could not read first frame from {video_path}")

    undistorted = cv2.undistort(frame, camera_matrix, dist_coeffs)
    pts = pick_points(undistorted, min_points=4)
    if len(pts) < 4:
        print("[homography] Cancelled (not enough points).")
        return None

    # Define board real-world size (cm)
    real_pts = [(0, 0), (70, 0), (70, 200), (0, 200)]
    H = compute_homography(pts, real_pts)

    # Save homography JSON
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    save_homography(H, out_json)
    print(f"[homography] saved → {os.path.abspath(out_json)}")

    # --- Homography sanity check ---
    print("\nClick 2 points with a known physical distance (e.g., corners you can measure).")

    check_frame = undistorted.copy()
    points = []

    def on_click(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(points) < 2:
                points.append((x, y))

    cv2.namedWindow("Homography Check")
    cv2.setMouseCallback("Homography Check", on_click)

    while True:
        disp = check_frame.copy()
        h, w = disp.shape[:2]

        msg = "Enter=Confirm   r=Reset   Esc=Exit"
        cv2.putText(disp, msg, (6, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2, cv2.LINE_AA)
        cv2.putText(disp, msg, (6, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1, cv2.LINE_AA)

        # Draw points
        for i, (x, y) in enumerate(points, 1):
            cv2.circle(disp, (x, y), 4, (0,0,0), 2)
            cv2.circle(disp, (x, y), 3, (255,255,255), -1)
            cv2.putText(disp, str(i), (x+8, y-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0,0,0), 2, cv2.LINE_AA)
            cv2.putText(disp, str(i), (x+8, y-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (255,255,255), 1, cv2.LINE_AA)

        # If 2 points → compute distance right away
        if len(points) == 2:
            rw_pts = [pixel_to_real_world(pt, H) for pt in points]
            dist = np.sqrt((rw_pts[0][0] - rw_pts[1][0])**2 +
                           (rw_pts[0][1] - rw_pts[1][1])**2)
            text = f"Distance: {dist:.2f} cm"
            cv2.putText(disp, text,
                        (w - 200, h - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (0, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(disp, text,
                        (w - 200, h - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (255, 255, 255), 1, cv2.LINE_AA)

        cv2.imshow("Homography Check", disp)
        key = cv2.waitKey(20) & 0xFF

        if key == 27:   # ESC
            break
        elif key in (ord('r'), ord('R')):  # Reset points
            points = []
        elif key in (13, 10):  # Enter = confirm and continue
            break

    cv2.destroyWindow("Homography Check")
    return out_json


if __name__ == "__main__":
    main()