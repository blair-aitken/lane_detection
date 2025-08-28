import cv2, numpy as np, json, os
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

def compute_homography(image_pts, real_pts):
    image_pts = np.array(image_pts, dtype=np.float32)
    real_pts  = np.array(real_pts,  dtype=np.float32)
    if len(image_pts) == 4:
        H = cv2.getPerspectiveTransform(image_pts, real_pts)
    else:
        H, _ = cv2.findHomography(image_pts, real_pts, method=0)
    if H is None:
        raise RuntimeError("Homography computation failed.")
    return H

def save_homography(H, out_json):
    os.makedirs(os.path.dirname(out_json) or ".", exist_ok=True)
    with open(out_json, "w") as f:
        json.dump({"homography_matrix": H.tolist()}, f, indent=2)
