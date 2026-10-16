@echo off
setlocal
cd /d "%~dp0"

REM ===== Settings you can change =====
REM Python version to use (must be installed, check with: py -0)
set PYVER=3.11
REM CUDA build of PyTorch: check https://pytorch.org for the current tag
REM and make sure your NVIDIA driver supports it (run: nvidia-smi)
set CUDA_TAG=cu126
REM ===================================

echo.
echo [1/6] Creating virtual environment .venv
if not exist .venv\Scripts\activate.bat (
    py -%PYVER% -m venv .venv
    if errorlevel 1 (
        echo ERROR: Python %PYVER% not found. Install it first, or change PYVER above.
        pause
        exit /b 1
    )
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip

echo.
echo [2/6] Installing PyTorch with CUDA %CUDA_TAG%
pip install torch torchaudio --index-url https://download.pytorch.org/whl/%CUDA_TAG%
if errorlevel 1 (
    echo ERROR: PyTorch install failed. Check CUDA_TAG and your internet connection.
    pause
    exit /b 1
)

echo.
echo [3/6] Installing core requirements
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: requirements.txt install failed. Read the message above.
    pause
    exit /b 1
)

echo.
echo [4/6] Installing beat_this from GitHub (beat / downbeat tracking)
pip install "beat_this @ https://github.com/CPJKU/beat_this/archive/main.zip"
if errorlevel 1 echo WARNING: beat_this failed to install. Will be handled in Phase 0 checklist.

echo.
echo [5/6] Installing Chromium for Playwright (image export)
python -m playwright install chromium
if errorlevel 1 echo WARNING: Playwright Chromium install failed.

echo.
echo [6/6] Checking installation
python -c "import torch; ok=torch.cuda.is_available(); print('torch', torch.__version__, '| CUDA available:', ok); print('GPU:', torch.cuda.get_device_name(0) if ok else 'NONE - CPU only!')"

ffmpeg -version >nul 2>&1
if errorlevel 1 echo WARNING: ffmpeg not found. Install with: winget install --id Gyan.FFmpeg -e   (then open a new terminal)

node --version >nul 2>&1
if errorlevel 1 echo WARNING: Node.js not found. Install with: winget install --id OpenJS.NodeJS.LTS -e   (then open a new terminal)

echo.
echo ===== Done. If "CUDA available" above says False, fix that before anything else. =====
echo Not installed by this script (handled in Phase 0): BTC chord model, RMVPE weights, WhisperX.
echo Next: run  python scripts\check_env.py --deep  (really transcribes with the GPU, catches cuDNN DLL problems).
pause
endlocal
