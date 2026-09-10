@echo off
title SocialPulse Hub Server
cd /d "%~dp0"
echo ========================================================
echo Starting SocialPulse Hub Automation Server...
echo Open your browser at: http://localhost:8000
echo ========================================================
python main.py
pause
