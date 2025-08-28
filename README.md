## Title here

This repository accompanies the research paper (add paper citation here).

This toolkit provides everything needed to:
- Calibrate your camera using intrinsic parameters.
- Generate a homography matrix to map image pixels into road-plane coordinates.
- Measure vehicle lateral position relative to a lane line from wheel-view videos.

Included in this repository:
- `chessboard_A4.png` — print on **A4** for camera calibration.  
- `calibration_board_B1.png` — print **two copies** on **B1-sized boards** for homography calibration.  
- Cross-platform launchers (`mac_launcher.sh`, `win_launcher.bat`) to automate the entire pipeline.

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
│   ├── videos/                    # Input calibration + driving videos
│
├── output/
│   ├── csv/                       # Measurement CSVs (per frame)
│   ├── videos/                    # Debug videos
│
├── scripts/
│   ├── run_calibration.py         # Intrinsic calibration
│   ├── run_homography.py          # Homography matrix generation
│   ├── run_measurement.py         # Lane measurement
│   └── utils/                     # Helper functions
│
│── launchers/
│   ├── mac_launcher.sh            # macOS/Linux launcher
│   ├── win_launcher.bat           # Windows launcher
│ 
├── requirements.txt               # Python dependencies
└── README.md                      # This document
```

### Installation

#### Option 1: Clone with Git
```bash
git clone https://github.com/yourusername/lane-measurement.git
cd lane-measurement
```

#### Option 2: Download ZIP
1. Download the latest release
2. Extract the downloaded ZIP file
3. Navigate to the extracted folder in your terminal (macOS/Linux) or Command Prompt (Windows)

---

### Configuration
This project comes with a default configuration file in the repository root called `config.jason`. 

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
| `wheel_offset_cm` | Half the vehicle’s wheel-to-wheel track width. Used to convert wheel→lane distance into lane-centre distance. |
| `column_width` | Half-width of vertical search strip around the wheel x-coordinate for histogram peak finding. |
| `min_lane_width` | Rejects contours narrower than this. Typical range: **10–40 px** (default = 15). |
| `max_jump` | Maximum allowed frame-to-frame jump in pixels for lane detection (stability filter). Typical range: **10–60 px** (default = 30). |
| `gaussian_kernel` | Blur kernel before thresholding to reduce noise. Must be odd × odd (e.g., `[7,7]`, `[15,15]`). Default = `[15,15]`. |
| `block_size` | Window size for adaptive thresholding. Larger values adapt to broader lighting gradients. Must be odd ≥ 3 (default = 25). |
| `c_const` | Constant subtracted in adaptive thresholding. Shifts threshold up/down. More negative = stricter. Range: **−20 → +20** (default = −8). |
| `min_contour_area` | Rejects small blobs before aspect-ratio filtering. Typical range: **50–1000 px²** (default = 150). |
| `min_aspect_ratio` | Height:width filter — keeps long, thin shapes typical of lane paint. Typical range: **2–10** (default = 5.0). |
| `morph_kernel` | Structuring element size `[width, height]` used for morphological close/open operations to clean thresholded image. Default = `[10,15]`. |

---

### How It Works

Run the launcher for your operating system:

**macOS / Linux**  

Open a terminal in the project folder, make the launcher executable (first time only), then run:

```bash
chmod +x mac_launcher.sh
./mac_launcher.sh
 ```

**Windows**

Simply double-click win_launcher.bat in File Explorer,
or run it from Command Prompt / PowerShell:
```bat
win_launcher.bat
```

When you run the launcher, the following steps will run in sequence:

#### Step 1: Environment Setup
- On the first run, a new folder called **`venv/`** is created.  
- All required dependencies listed in `requirements.txt` are installed into this virtual environment.  
- This ensures a clean, isolated Python environment regardless of your system setup.

#### Step 2: Camera Calibration
- Every camera has its own intrinsic properties (focal length, distortion coefficients, etc.).  
- To account for this, you must run **camera calibration** using the provided `chessboard.png` (A4 print).  
- Input:
  - At least 10 photos of the chessboard pattern at different distances/angles taken with the same camera setup used for driving.
  - Accepted formats: `*.jpg`, `*.jpeg`, `*.png`, `*.bmp`, `*.tif`, `*.tiff` 
- Place these images in the `data/chessboard_images` folder.
- Output:  
  - `data/calib/camera_intrinsics.npz` containing `camera_matrix` and `dist_coeffs`  
  - This file is unique to each camera and only needs to be created once per setup.

<img src="https://github.com/user-attachments/assets/01599bea-576f-4e40-acdd-e667ff1c1d80" width="500">

A `camera_intrinsics_summary.json` file is also created, which provides a simple summary of your calibration, including the number of images used, image size, and RMS error.

<img src="https://github.com/user-attachments/assets/4bcce1f5-a0e3-4e31-850d-7046b59caafa" width="500"><br>

#### Step 3: Compute Homography Matrix
- Next, you’ll map image pixels to real-world coordinates using the provided **B1 calibration boards** (print two copies of `calibration_board_B1.png`).  
- Record a short video of the boards placed flat on the road surface with the short side against the wheel of the vehicle.  
- The script will show the first frame and prompt you to click the 4 corners of the calibration board, **starting with the top-left corner, moving clockwise.**  
- A homography matrix is computed and saved as `data/homography/[video_name]_homography.json`

<img src="https://github.com/user-attachments/assets/7578e7fe-4c09-4fa0-8b86-8d2f461ecf7b" width="500">

To confirm the homography transformation worked, a **sanity check** is built into the homography step:

- You select 2 points on the calibration board with a **known distance**.  
- The script transforms these points into real-world coordinates and calculates the distance.  
- **Example:**
  - Each calibration square is **20 cm high × 35 cm wide**.  
  - Clicking top and bottom corners of a square → should return ~20 cm.  
  - Clicking across a square → should return ~35 cm.

You will be asked each time whether you want to create a new homography matrix for a video.  
- You only need **one homography matrix per camera setup**.  
- However, if the **camera is moved** (angle, height, or position), you must create a **new homography matrix** for that recording.

#### Step 4: Lane Measurement
- With calibration and homography set, you can now measure lane position from a driving video.  
- Input: wheel-view driving video.  
- You’ll be prompted to click on the wheel reference point once.  
- For each frame:
  - Lane line is detected using a histogram-based method.  
  - Distance between the wheel and lane line is mapped to real-world coordinates.
 
---

## Outputs

After running the full pipeline, two types of outputs are created:

- **CSV file** (`output/csv/[video_name]_measurements.csv`):  
  Contains frame-by-frame measurements of the vehicle’s lateral position.
  - Values represent the distance from wheel → lane line, corrected by the wheel-to-vehicle centre offset. 
  - Each row corresponds to one video frame.
  - `NaN` indicates no valid lane line was detected for that frame.

- **Debug video** (`output/videos/[video_name]_debug.mp4`):  
  Shows the wheel reference, detected lane line, frame number, and lateral distance overlayed for visual verification.  
    - Every frame in the **debug video** is numbered (`Frame 123`) and has the lateral distance overlayed (`187.3 cm`).  
    - These frame numbers **match the rows in the CSV file** exactly.  
    - This lets you:
        - Visually inspect detections.
        - Identify measurement errors (e.g., overtaking vehicles, shadows).
        - Manually remove problematic frames from the CSV before final analysis.

At the end of processing, the script also prints **summary statistics**.

<img src="https://github.com/user-attachments/assets/eaeb7bb7-ed0f-44f4-b937-7fb5e7468c87" width="500">

---

## Troubleshooting

**Common issues:**

- **`No calibration file found`**  
  → Run the calibration step again with `chessboard.png`.  

- **`No homography file exists`**  
  → Run homography generation with the B1 calibration boards.  

- **Wheel point mis-clicked**  
  → Rerun measurement and click the correct wheel reference point.  

- **Permission denied (macOS/Linux)**  
  → Make the launcher executable:  
  ```bash
  chmod +x mac_launcher.sh
  ```

---

## License
This project is open source and available under the [MIT License](LICENSE).
