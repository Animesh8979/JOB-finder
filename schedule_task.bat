@echo off
cd /d "%~dp0"
echo ========================================================
echo     Remote Job Application Copilot - Scheduler Setup
echo ========================================================
echo.

set "TASK_NAME=JobCopilotAutoFetch"
set "SCHED_BAT=%~dp0run_scheduler.bat"

REM --- Create run_scheduler.bat helper ---
echo Creating background run helper...
(
echo @echo off
echo cd /d "%%~dp0"
echo .venv\Scripts\python.exe -m src.scheduler
) > "%SCHED_BAT%"

REM --- Register scheduled task in Windows ---
echo Registering daily Task Scheduler task (Daily at 9:00 AM)...
schtasks /create /tn "%TASK_NAME%" /tr "\"%SCHED_BAT%\"" /sc daily /st 09:00 /f

echo.
if %errorlevel% equ 0 (
  echo ========================================================
  echo SUCCESS! The background scheduler is registered.
  echo It will run automatically every morning at 09:00 AM.
  echo.
  echo Logs will be appended to: data\scheduler_log.txt
  echo ========================================================
) else (
  echo ========================================================
  echo ERROR: Failed to register the scheduled task.
  echo Please close this, right-click schedule_task.bat,
  echo and select "Run as administrator".
  echo ========================================================
)
echo.
pause
