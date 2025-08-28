import sys, os, glob, argparse, json
import numpy as np

# make 'src' importable when run from scripts/
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.calibration import calibrate_camera  # noqa: E402

DEFAULT_IMG_DIR = "data/chessboard_images"
DEFAULT_OUT_NPZ = "data/calib/camera_intrinsics.npz"

def find_images(root: str):
    """Find all chessboard images recursively under root."""
    exts = ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tif", "*.tiff")
    files = []
    for ext in exts:
        files.extend(glob.glob(os.path.join(root, "**", ext), recursive=True))
    return sorted(files)

def parse_args():
    p = argparse.ArgumentParser(description="Calibrate camera from chessboard images.")
    p.add_argument("--img-dir", default=DEFAULT_IMG_DIR,
                   help=f"Folder containing chessboard images (default: {DEFAULT_IMG_DIR})")
    p.add_argument("--cols", type=int, default=9, help="Inner corners per row (columns). Default=9")
    p.add_argument("--rows", type=int, default=6, help="Inner corners per column (rows). Default=6")
    p.add_argument("--square-mm", type=float, default=25.0, help="Square size in mm. Default=25.0")
    p.add_argument("--out", default=DEFAULT_OUT_NPZ,
                   help=f"Output .npz path (default: {DEFAULT_OUT_NPZ})")
    return p.parse_args()

def main():
    args = parse_args()
    chessboard_dims = (args.cols, args.rows)

    # load images
    images = find_images(args.img_dir)
    if not images:
        raise RuntimeError(f"No chessboard images found in {args.img_dir}")

    # run calibration
    cam_mtx, dist_coeffs, rms, image_size, n_used = calibrate_camera(
        images, chessboard_dims, args.square_mm
    )

    # save results
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    np.savez(
        args.out,
        camera_matrix=cam_mtx,
        dist_coeffs=dist_coeffs,
        rms=rms,
        image_size=image_size,
        n_images_used=n_used,
        chessboard_cols=args.cols,
        chessboard_rows=args.rows,
        square_mm=args.square_mm,
    )
    print(f"[calibration] saved intrinsics → {args.out}")

    # save human-readable JSON
    summary_json = os.path.splitext(args.out)[0] + "_summary.json"
    with open(summary_json, "w") as f:
        json.dump(
            {
                "output_npz": args.out,
                "image_dir": os.path.abspath(args.img_dir),
                "images_used": n_used,
                "image_size": image_size,
                "rms": rms,
                "chessboard_dims": {"cols": args.cols, "rows": args.rows},
                "square_mm": args.square_mm,
            },
            f,
            indent=2,
        )
    print(f"[calibration] summary → {summary_json}")

if __name__ == "__main__":
    main()