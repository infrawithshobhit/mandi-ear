@echo off
echo.
echo ========================================
echo   MANDI EAR™ Agricultural Intelligence
echo ========================================
echo.
echo 🌾 Starting MANDI EAR Platform...
echo 📦 Auto-installing dependencies...
echo.

cd /d "%~dp0"
python standalone_mandi_ear.py

echo.
echo 🛑 MANDI EAR™ has stopped.
pause