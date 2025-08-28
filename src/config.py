import json
import os

# Path to config.json
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "config.json")

with open(CONFIG_FILE, "r") as f:
    _cfg = json.load(f)

# Default search paths
CALIB_SEARCH_DIR = "data/calib"
HOMOGRAPHY_SEARCH_DIR = "data/homography"

# Expose config values
LANE_POINT_MODE    = _cfg.get("lane_point_mode", "far")
WHEEL_OFFSET_CM    = _cfg.get("wheel_offset_cm", 91.7)
COLUMN_WIDTH       = _cfg.get("column_width", 5)
MIN_LANE_WIDTH     = _cfg.get("min_lane_width", 15)
MAX_JUMP           = _cfg.get("max_jump", 30)

GAUSSIAN_KERNEL    = tuple(_cfg.get("gaussian_kernel", [15, 15]))
BLOCK_SIZE         = _cfg.get("block_size", 25)
C_CONST            = _cfg.get("c_const", -8)

MIN_CONTOUR_AREA   = _cfg.get("min_contour_area", 150)
MIN_ASPECT_RATIO   = _cfg.get("min_aspect_ratio", 5.0)
MORPH_KERNEL       = tuple(_cfg.get("morph_kernel", [10, 15]))
