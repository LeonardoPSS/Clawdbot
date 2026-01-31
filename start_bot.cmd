@echo off
REM LinkedIn Bot Launcher - Startup Version
cd /d "C:\Users\leona\Downloads\AntigravityJobBot"
set PYTHONPATH=C:\Users\leona\Downloads\AntigravityJobBot

echo ⏳ Waiting 30 seconds for system to stabilize...
timeout /t 30 /nobreak > nul

echo 🚀 Starting AntigravityJobBot...
python bot_manager.py

