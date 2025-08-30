## Title here

This repository accompanies the research paper:

(add paper citation here)

This toolkit provides a complete pipeline to:
- Calibrate camera intrinsic parameters.
- Generate a homography matrix to map image pixels to real-world road-plane coordinates.
- Measure a vehicle's lateral position relative to a lane line.

Included in this repository:
- `chessboard_A4.png` — Print on **A4** for camera calibration.  
- `calibration_board_B1.png` — Print **two copies** on **B1-sized boards** for homography calibration.  
- Cross-platform launchers (`mac_launcher.sh`, `win_launcher.bat`) to automate the entire pipeline.

---

### Quick Start (TL;DR)
1. Print `chessboard_A4.png` → take 10–15 photos → save to `data/chessboard_images/`.
2. Print 2 × `calibration_board_B1.png` → record 5–10s homography video → save to `data/videos/`.
3. Record driving video with same camera mount → save to `data/videos/`.
4. Run the launcher (`mac_launcher.sh` or `win_launcher.bat`).
5. Collect outputs from `output/csv/` (for analysis) and `output/videos/` (for checking).

---

### Folder Structure

```
project-root/
│
├── chessboard.png                 # A4 calibration chessboard
├── calibration_board_B1.png       # B1 calibration board
│
├── data/
│   ├── calib/                     # Calibration files (.npz with camera intrinsics)
│   ├── homography/                # Homography JSON files
│   ├── chessboard_images/         # Input chessboard images for computing camera instrinsics
│   └── videos/                    # Input calibration + driving videos
│
├── output/
│   ├── csv/                       # Measurement CSVs (per frame)
│   └── videos/                    # Debug videos
│
├── src/
│   ├── calibration.py             # Camera intrinsic calibration from chessboard images → saves camera_intrinsics.npz
│   ├── config.py                  # Loads config.json and exposes constants (thresholds, kernels, offsets, etc.)
│   ├── homography.py              # Compute/validate/save 3×3 homography mapping (image → road plane)
│   ├── measurement.py             # Pixel → world coordinate mapping + distance calculations
│   └── utils.py                   # Misc. shared helpers (paths, dialogs, overlays)
│
├── scripts/
│   ├── run_calibration.py         # Intrinsic calibration
│   ├── run_homography.py          # Homography matrix generation
│   └── run_measurement.py         # Lane measurement
│
│── launchers/
│   ├── mac_launcher.sh            # macOS/Linux launcher
│   └── win_launcher.bat           # Windows launcher
│ 
├── requirements.txt               # Python dependencies
└── README.md                      # This document
```

### Installation

#### 1. Get the code
**Option A: Clone with Git**
```bash
git clone https://github.com/blair-aitken/lane_detection.git
cd lane_detection
```

**Option B: Download ZIP**
1. Download the latest release [here](https://github.com/blair-aitken/lane_detection/archive/refs/heads/main.zip)
2. Extract the downloaded ZIP file
3. Navigate to the extracted folder in your terminal (macOS/Linux) or Command Prompt (Windows)

#### 2. Install Python

If you don't have Python 3.9+ installed, follow these instructions.

#### For macOS:
- Install Homebrew (package manager for macOS) if you don’t already have it:
 
 ```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

- Install Python:

```bash
brew install python
```

- Verify installation:

```bash
python3 --version
pip3 --version
```

#### For Windows:
- Go to the official [Python Downloads page](https://www.python.org/downloads/windows/) and download the latest stable release (Python 3.9+).
- Run the installer
  - During installation, check the box that says `Add Python to PATH`.
  - Choose “Install Now.”
- Verify installation:

```bat
python --version
pip --version
```

---

### Data Preparation

Before you can measure lane position, there are two short setup steps:

- Take images of the chessboard (to calibrate the camera).
- Generate a homography video (to convert video pixels into real-world road distances).

#### Chessboard Images

We use a printed chessboard pattern for camera calibration because it provides a grid of evenly spaced corners that the software can reliably detect. Every camera has its own intrinsic properties (such as focal length and distortion coefficients) that bend the image, making straight lines in the real world appear slightly curved. By capturing the chessboard from different angles and positions, calibration software can estimate these properties and correct the distortion, ensuring that measurements taken from the video are geometrically accurate.

1. Print `chessboard_A4.png` on A4 paper.
2. Mount flat on stiff cardboard or foam board (no bending).
3. Take 10–15 photos with your camera. Move the board around the frame, tilt it at different angles, and vary the distance.

<img src="https://github.com/user-attachments/assets/01599bea-576f-4e40-acdd-e667ff1c1d80" width="500">

4. Save the photos into `data/chessboard_images/`

#### Homography Video

We use calibration boards on the road to generate a homography, which tells the software how to map video pixels into real-world distances (in cm or meters). The boards provide a known size and shape on the road surface, so the software can “learn” how your specific camera sees the ground plane.

The camera must be mounted in the exact position and angle you’ll use for the driving video. If the camera is moved, tilted, or re-mounted in any way, you must record a new homography video.

1. Print two copies of `calibration_board_B1.png` on **B1-sized boards.**
2. Park your car on a flat road or, ideally, the same test track you’ll use for driving.
3. Place both boards flat on the ground beside the wheel you’re measuring from (short side against the tyre).

 <img src="https://github.com/user-attachments/assets/c822ab3c-de8f-4d6d-99cc-62d6df6689ac" width="500">

4. Record a 5 second video of the boards with your mounted camera.
5. Save the video into `data/videos/`

#### Record Your Driving Video

This is the video the system will analyse for lane position. It must be recorded with the same camera mount used for calibration and homography.

1. Mount the camera securely above the wheel so the lane line is clearly visible.
2. Record your driving video.
3. Save it into `data/videos/`
  
---

### Configuration

This project comes with a configuration file in the repository root called `config.json`

The only setting you need to change is `wheel_offset_cm`, because every vehicle has a different width.
- To calculate this value, measure the total width of your vehicle (outside wheel to outside wheel), then divide by 2.
- Enter this distance (in centimetres).
- The software uses this to convert the wheel-to-lane measurement into a centre-of-vehicle-to-lane measurement.

All other settings can be left as they are unless you want to fine-tune detection performance.

```json
  "wheel_offset_cm": 91.7,
  "column_width": 5,
  "min_lane_width": 15,
  "max_jump": 30,
  "gaussian_kernel": [15, 15],
  "block_size": 25,
  "c_const": -8,
  "min_contour_area": 150,
  "min_aspect_ratio": 5.0,
  "morph_kernel": [10, 15]
```

You may edit values if you want to tune performance (e.g., for different cameras, lighting, or vehicles).

| Variable | Description |
| --- | --- |
| `wheel_offset_cm` | Half the vehicle’s wheel-to-wheel track width. |
| `column_width` | Half-width of vertical search strip around the wheel x-coordinate for histogram peak finding. |
| `min_lane_width` | Rejects contours narrower than this. Typical range: 10–40 px (default = 15). |
| `max_jump` | Maximum allowed frame-to-frame jump in pixels for lane detection (stability filter). Typical range: 10–60 px (default = 30). |
| `gaussian_kernel` | Blur kernel before thresholding to reduce noise. Must be odd × odd (e.g., `[7,7]`, `[15,15]`). Default = `[15,15]`. |
| `block_size` | Window size for adaptive thresholding. Larger values adapt to broader lighting gradients. Must be odd ≥ 3 (default = 25). |
| `c_const` | Constant subtracted in adaptive thresholding. Shifts threshold up/down. More negative = stricter. Typical range: −20 → +20 (default = −8). |
| `min_contour_area` | Rejects small blobs before aspect-ratio filtering. Typical range: 50–1000 px² (default = 150). |
| `min_aspect_ratio` | Height:width filter — keeps long, thin shapes typical of lane paint. Typical range: 2–10 (default = 5.0). |
| `morph_kernel` | Structuring element size `[width, height]` used for morphological close/open operations to clean thresholded image. Default = `[10,15]`. |

---

### How It Works

Run the launcher for your operating system:

**macOS / Linux**  

Open a terminal in the project folder, make the launcher executable (first time only), then run:

```bash
cd launchers
chmod +x mac_launcher.sh
./mac_launcher.sh
 ```

**Windows**

Simply double-click win_launcher.bat in File Explorer,
or run it from Command Prompt / PowerShell:
```bat
launchers/win_launcher.bat
```

When you run the launcher, the following steps will run in sequence:

#### Step 1: Environment Setup
- On the first run, a new folder called **`venv/`** is created.  
- All required dependencies listed in `requirements.txt` are installed into this virtual environment.  
- This ensures a clean, isolated Python environment regardless of your system setup.

#### Step 2: Camera Calibration
- Run camera calibration using the printed chessboard pattern.
- **Input:**
  - At least 10 images of the chessboard pattern at different distances/angles taken with the same camera setup used for driving.
  - Save these images in the `data/chessboard_images` folder.
  - Will accept `*.jpg`, `*.jpeg`, `*.png`, `*.bmp`, `*.tif`, `*.tiff` formats only.
- **Output:**
  - `data/calib/camera_intrinsics.npz` (camera matrix and distortion coefficients).
  - `camera_intrinsics_summary.json` (summary of calibration, RMS error, number of images).

<img src="https://github.com/user-attachments/assets/4bcce1f5-a0e3-4e31-850d-7046b59caafa" width="500"><br>

#### Step 3: Compute Homography Matrix
- Run homography generation using the calibration board.
- **Input:**
  - Short video (5–10 seconds) of the boards placed flat on the road surface beside the wheel.
  - Save this video in data/videos/.
- A homography matrix is computed and saved as `data/homography/[video_name]_homography.json`
- During this step you will be prompted to click each of the four corners of the calibration board on screen, starting from the top-left corner and moving clockwise.
  - The pixels you select in the video correspond to the known real-world coordinates of the board (e.g., [0,0] at the top-left corner).
  - Using these matches, the software computes a homography matrix and saves it as `data/homography/[video_name]_homography.json`

<img src="https://github.com/user-attachments/assets/7578e7fe-4c09-4fa0-8b86-8d2f461ecf7b" width="500">

- **Confirm homography matrix**
  - After computing the homography matrix, you have the option to run a sanity check.
  - In this step, you can select any two points on the calibration board in the video. The software will transform these into real-world coordinates and report the measured distance.
  - This check is important because the point of homography is to ensure that the pixel-to-distance ratio is consistent across the whole frame. I.e., the same distance at the top of the image should equal the same distance at the bottom.
  - Example with the calibration board:
    - Each square is 20 cm high × 35 cm wide.
    - Clicking the top and bottom of a square should return ~20 cm.
    - Clicking across a square should return ~35 cm.
    - If the returned values match what you expect, it confirms the homography is working correctly.

#### Step 4: Lane Measurement
- With calibration and homography set, you can now measure lane position from a driving video.  
- **Input:**
  - Wheel-view driving video.
  - Save this video in the `data/videos` folder.
- You’ll be prompted to click on the wheel reference point once.  
- For each frame:
  - Lane line is detected using a histogram-based method.  
  - Distance between the wheel and lane line is mapped to real-world coordinates.
 
---

### Main Outputs (from your driving video)

After calibration and homography are set, running the pipeline on your driving video produces two main outputs:

- **CSV file** (`output/csv/[video_name]_measurements.csv`):  
  - Contains frame-by-frame measurements of the vehicle’s lateral position.  
  - Values represent the distance from wheel → lane line, corrected by the wheel-to-vehicle centre offset.  
  - `NaN` indicates no valid lane line was detected for that frame.  

- **Debug video** (`output/videos/[video_name]_debug.mp4`):  
  - Shows the wheel reference point, detected lane line, frame number, and lateral distance.  
  - Frame numbers in the video **match the rows in the CSV**.  
  - Useful for:  
    - Spot-checking detection quality.  
    - Identifying errors (e.g., shadows, passing vehicles).  
    - Manually cleaning the CSV before final analysis.  

At the end of processing, the script also prints **summary statistics** in the terminal.

<img src="https://github.com/user-attachments/assets/eaeb7bb7-ed0f-44f4-b937-7fb5e7468c87" width="500">

---

### Limitations

This toolkit is designed for controlled experiments and may not perform perfectly in all conditions. Key limitations to be aware of:
- Lighting and shadows
  - Lane detection works best with clearly visible white or yellow lines.
  - Strong shadows, glare, or faded markings can reduce accuracy.
- Board calibration
  - Camera calibration requires sharp, in-focus chessboard images. Blurry or warped boards will degrade results.
  - Homography calibration must be done with the same camera mount used for the driving video. Any change in angle or height requires recalibration.
- Vehicle-specific setup
  - The only configuration parameter that must be changed per vehicle is wheel_offset_cm. An incorrect value will shift the lane-centre measurements.
- Data quality
  - The system assumes stable camera mounting. Vibrations or loose mounts can distort results.
  - NaN values in the CSV indicate frames where no reliable lane line was detected. Manual cleaning of the CSV may be required for final analysis.
- Scope of use
  - This toolkit is intended for research use on closed roads or test tracks.
  - It is not a production-grade driver-assistance system.

---

### Example Data
A small example dataset is included in `data/example/` so you can test the full pipeline without collecting your own data first.

---

### Troubleshooting

**Common issues:**

- **`No calibration file found`**  
  → Run the calibration step again with `chessboard.png`.  

- **`No homography file exists`**  
  → Run homography generation with the calibration boards.  

- **Wheel point mis-clicked**  
  → Rerun measurement and click the correct wheel reference point.  

- **Permission denied (macOS/Linux)**  
  → Make the launcher executable:  
  ```bash
  chmod +x mac_launcher.sh
  ```

---

### License
This project is open source and available under the [MIT License](LICENSE).
