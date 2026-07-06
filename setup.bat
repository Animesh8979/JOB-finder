@echo off
cd /d "%~dp0"
echo ============================================
echo    Job Application Copilot  -  Setup
echo ============================================
echo.

REM --- 0) Disk discipline: keep ALL caches on D: (user constraint: no C disk) ---
call "%~dp0_env_d_disk.bat"
echo Cache roots anchored on D: drive (see _env_d_disk.bat for the full list).
echo.

set "PYDIR=%LOCALAPPDATA%\Programs\Python\Python312"
set "SYSPY=%PYDIR%\python.exe"

REM --- 1) Make sure a real Python is available ---
if not exist "%SYSPY%" (
  py -3 -c "import sys" 1>nul 2>nul
  if errorlevel 1 (
    echo Python was not found. Installing Python 3.12 via winget...
    winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements --scope user --silent
  )
)

REM --- 2) Create the virtual environment ---
if exist "%SYSPY%" (
  echo Using Python at "%SYSPY%"
  if not exist ".venv\Scripts\python.exe" "%SYSPY%" -m venv .venv
) else (
  py -3 -c "import sys" 1>nul 2>nul
  if errorlevel 1 (
    echo.
    echo Could not find or install Python automatically.
    echo Please install Python 3.12 from https://www.python.org/downloads/
    echo During install, tick "Add python.exe to PATH", then run setup.bat again.
    pause
    exit /b 1
  )
  echo Using the "py" launcher
  if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
)

set "VPY=.venv\Scripts\python.exe"
if not exist "%VPY%" (
  echo Failed to create the virtual environment.
  pause
  exit /b 1
)

REM --- 3) Install dependencies ---
echo.
echo Installing dependencies (the first time can take a few minutes)...
"%VPY%" -m pip install --upgrade pip
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Dependency installation failed. Scroll up to read the error.
  pause
  exit /b 1
)

REM --- 4) Install the browser used for review-first apply ---
echo.
echo Installing the browser for review-first apply (Chromium)...
"%VPY%" -m playwright install chromium

echo.
echo ============================================
echo    Setup complete!  Now double-click run.bat
echo ============================================
pause
