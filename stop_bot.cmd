@echo off
REM LinkedIn Bot Stopper
taskkill /F /FI "WINDOWTITLE eq python*main.py*" 2>nul
taskkill /F /FI "IMAGENAME eq python.exe" /FI "MEMUSAGE gt 50000" 2>nul
echo LinkedIn Bot stopped (if it was running).
