@echo off
REM LinkedIn Daily Automation Scheduler
REM Run this script to execute daily LinkedIn tasks

cd /d "C:\Users\leona\Downloads\AntigravityJobBot"
set PYTHONPATH=C:\Users\leona\Downloads\AntigravityJobBot

echo ========================================
echo LinkedIn Daily Automation
echo ========================================
echo.
echo Tasks:
echo - Generate and post varied content
echo - Like 15 posts
echo - Comment on 5 posts
echo - Follow 10 new profiles
echo.
echo Starting...
echo.

python src\scheduler.py

echo.
echo ========================================
echo Automation Complete!
echo ========================================
pause
