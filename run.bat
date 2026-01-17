@echo off
REM Granada - Development Run Script for Windows
REM This script runs Granada in development mode

echo ========================================
echo    Granada - Arabic Book Search Engine
echo ========================================
echo.

REM Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.8 or later.
    pause
    exit /b 1
)

REM Check Python version
python --version

REM Set environment variables
set FLASK_ENV=development
set FLASK_DEBUG=1

REM Change to script directory
cd /d "%~dp0"

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install requirements if needed
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Initialize database if needed
if not exist "data\granada.db" (
    echo Initializing database...
    python build.py --init-db
)

echo.
echo Starting Granada server...
echo Access the application at: http://127.0.0.1:5000
echo Press Ctrl+C to stop the server.
echo.

python app.py

pause
