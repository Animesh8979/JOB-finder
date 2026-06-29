@echo off
echo Starting Ai Job Finder Background Daemon...
echo Close this window to stop the background process.
title Ai Job Finder Daemon
python cron_daemon.py
pause
