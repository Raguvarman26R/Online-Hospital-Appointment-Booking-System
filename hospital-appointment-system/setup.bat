@echo off
title Setup & Test - Online Hospital Appointment System
echo ========================================================
echo   Setting Up Dependencies and Running Agile Test Suite
echo ========================================================
echo.
echo 1. Installing requirements...
python -m pip install -r requirements.txt
echo.
echo 2. Running automated unit test suite (9 test categories)...
python -m unittest test_app.py -v
echo.
echo ========================================================
echo   Verification Completed!
echo   To launch the server, double click "run.bat"
echo ========================================================
pause
