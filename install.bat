@echo off

REM Check if CUDA is installed by trying to run nvcc
nvcc --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: CUDA is not installed or nvcc is not in PATH
    echo Please install CUDA toolkit version 12.4 or higher
    pause
    exit /b 1
)

REM Get CUDA version and check if it's >= 12.4
for /f "tokens=2 delims=," %%a in ('nvcc --version ^| findstr "release"') do (
    set "version_str=%%a"
)
set "version_str=%version_str:release =%"
for /f "tokens=1 delims=." %%a in ("%version_str%") do (
    set "major_version=%%a"
)
for /f "tokens=2 delims=." %%a in ("%version_str%") do (
    set "minor_version=%%a"
)

if %major_version% LSS 12 (
    echo ERROR: CUDA version must be 12.4 or higher
    echo Current version: %version_str%
    pause
    exit /b 1
)
if %major_version% EQU 12 (
    if %minor_version% LSS 4 (
        echo ERROR: CUDA version must be 12.4 or higher
        echo Current version: %version_str%
        pause
        exit /b 1
    )
)

echo CUDA %version_str% found. Proceeding with installation...

echo Creating virtual environment...
python -m venv soe_venv

echo Activating virtual environment...
call soe_venv\Scripts\activate

echo Updating pip...
python -m pip install --upgrade pip

echo Installing PyTorch with CUDA 12.4...
pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

echo Installing other Python packages...
pip install --upgrade -r requirements.txt

echo Installation complete!
nvcc --version
pip freeze

echo Deactivating virtual environment...
call soe_venv\Scripts\deactivate

pause