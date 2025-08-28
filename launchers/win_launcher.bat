@echo off
setlocal enabledelayedexpansion

:: Colors (Windows CMD has limited colors — we'll use ANSI escapes if supported)
for /f "tokens=2 delims==" %%I in ('"echo/ prompt $E ^| cmd"') do set "ESC=%%I"

set BOLD=%ESC%[1m
set RESET=%ESC%[0m
set GREEN=%ESC%[32m
set YELLOW=%ESC%[33m
set CYAN=%ESC%[36m
set RED=%ESC%[31m

:: Helper to print section headers
:section
echo.
echo %CYAN%------------------------------------------------------------%RESET%
echo %BOLD%%~1%RESET%
echo.
goto :eof

:: 1. Python environment
call :section "[1/5] Environment Setup"
if not exist venv (
    echo %YELLOW%Creating Python virtual environment...%RESET%
    python -m venv venv
) else (
    echo %GREEN%Virtual environment already exists.%RESET%
)

:: 2. Install dependencies
call :section "[2/5] Install Dependencies"
venv\Scripts\python -m pip install --upgrade pip >nul
venv\Scripts\python -m pip install -r requirements.txt

:: 3. Camera intrinsics
call :section "[3/5] Calibrate Camera Intrinsics"
if not exist data\calib\camera_intrinsics.npz (
    echo %YELLOW%No intrinsic parameters found — running calibration script...%RESET%
    venv\Scripts\python scripts\run_calibration.py
) else (
    echo %GREEN%Using existing camera_intrinsics.npz%RESET%
)

:: 4. Homography matrix
call :section "[4/5] Compute Homography Matrix"
echo %YELLOW%Do you want to generate a new homography matrix from calibration video?%RESET%
set /p yn="y/n: "
if /i "%yn%"=="y" (
    venv\Scripts\python scripts\run_homography.py
) else (
    echo %GREEN%Skipping homography generation — using existing JSON (if available).%RESET%
)

:: 5. Lane measurement
call :section "[5/5] Calculate Lane Measurements"
venv\Scripts\python scripts\run_measurement.py

:: Done
echo.
echo %CYAN%------------------------------------------------------------%RESET%
echo %GREEN%✅ Pipeline complete.%RESET%
echo Outputs are available in:
echo.
echo   • CSV results:   output\csv
echo   • Debug videos:  output\videos
echo.
pause
