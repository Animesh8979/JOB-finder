@echo off
echo ===================================================
echo   Compiling Job Application Copilot Premium UI
echo ===================================================
cd frontend
call npm run build
cd ..
echo.
echo Compilation complete! You can now start the dashboard using run.bat
pause
