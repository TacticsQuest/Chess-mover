@echo off
REM Chess Mover Machine - Windows Launcher
REM This script launches the Chess Mover control application

echo ================================================
echo   Chess Mover Machine - Control Application
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.11+ from python.org
    echo During installation, check "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Check if we're in the right directory
if not exist main.py (
    echo ERROR: Cannot find main.py
    echo Make sure you're running this from the Chess Mover Machine folder
    echo.
    pause
    exit /b 1
)

REM Check dependencies
echo Checking dependencies...
python -c "import serial" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Installing required dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo Dependencies OK
echo.
echo Starting Chess Mover Machine...
echo.
echo ================================================
echo.

REM Launch the application
python main.py

REM If application exits with error, pause to see error message
if errorlevel 1 (
    echo.
    echo ================================================
    echo Application exited with an error.
    echo Check the error message above.
    echo ================================================
    pause
)
