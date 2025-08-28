import os, glob, re
from datetime import datetime
import pytz
from src import config

def extract_aest_from_filename(filename):
    match = re.search(r"(\d{4}-\d{2}-\d{2})[_\s](\d{2}-\d{2}-\d{2})", filename)
    if match:
        datetime_str = f"{match.group(1)} {match.group(2)}"
        return datetime.strptime(datetime_str, "%Y-%m-%d %H-%M-%S")
    return None

def convert_aest_to_utc(aest_time):
    aest = pytz.timezone("Australia/Sydney")
    return aest.localize(aest_time).astimezone(pytz.utc)

def utc_to_decimal(utc_time):
    midnight = utc_time.replace(hour=0, minute=0, second=0, microsecond=0)
    return round((utc_time - midnight).total_seconds(), 1)

def find_file(base_dir, ext="*.npz"):
    matches = glob.glob(os.path.join(base_dir, "**", ext), recursive=True)
    if len(matches) == 0:
        raise FileNotFoundError(f"No files matching {ext} found under {base_dir}/")
    if len(matches) > 1:
        raise RuntimeError(f"Multiple {ext} files found: {matches}")
    return matches[0]

def find_calibration_file():
    return find_file(config.CALIB_SEARCH_DIR, "*.npz")

def find_homography_file():
    return find_file(config.HOMOGRAPHY_SEARCH_DIR, "*.json")
