@echo off
cd /d "%~dp0"
set "VPY=.venv\Scripts\python.exe"

REM Disk discipline: re-source env vars so a "run without setup" still anchors caches on D:.
call "%~dp0_env_d_disk.bat"

if not exist "%VPY%" (
  echo It looks like setup hasn't run yet. Running setup first...
  call setup.bat
)

echo.
echo Starting the Job Application Copilot FastAPI Server...
echo Launching your browser to http://127.0.0.1:8000...
echo.

:: Browser is opened automatically by the server process once ready

:: Run the server
"%VPY%" server.py
pause
