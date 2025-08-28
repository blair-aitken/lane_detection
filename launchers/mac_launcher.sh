#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Colors
BOLD=$(tput bold)
RESET=$(tput sgr0)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
CYAN=$(tput setaf 6)
RED=$(tput setaf 1)

divider() {
  echo -e "\n${CYAN}------------------------------------------------------------${RESET}\n"
}

section() {
  divider
  echo -e "${BOLD}$1${RESET}\n"
}

# 1. Python environment
section "[1/5] Environment Setup"
if [ ! -d "venv" ]; then
  echo "${YELLOW}Creating Python virtual environment...${RESET}"
  python3 -m venv venv
else
  echo "${GREEN}Virtual environment already exists.${RESET}"
fi

# 2. Install dependencies
section "[2/5] Install Dependencies"
./venv/bin/python -m pip install --upgrade pip >/dev/null
./venv/bin/python -m pip install -r requirements.txt

# 3. Camera intrinsics
section "[3/5] Calibrate Camera Intrinsics"
if [ ! -f "data/calib/camera_intrinsics.npz" ]; then
  echo "${YELLOW}No intrinsic parameters found — running calibration script...${RESET}"
  ./venv/bin/python scripts/run_calibration.py
else
  echo "${GREEN}Using existing camera_intrinsics.npz${RESET}"
fi

# 4. Homography matrix
section "[4/5] Compute Homography Matrix"
echo -e "${YELLOW}Do you want to generate a new homography matrix from calibration video?${RESET}"
read -p "y/n: " yn
if [[ "$yn" == "y" || "$yn" == "Y" ]]; then
  ./venv/bin/python scripts/run_homography.py
else
  echo "${GREEN}Skipping homography generation — using existing JSON (if available).${RESET}"
fi

# 5. Lane measurement
section "[5/5] Calculate Lane Measurements"
./venv/bin/python scripts/run_measurement.py

divider
printf "Pipeline complete. Outputs are available in:\n\n"
printf "  • CSV results:   %soutput/csv%s\n" "$CYAN" "$RESET"
printf "  • Debug videos:  %soutput/videos%s\n\n" "$CYAN" "$RESET"