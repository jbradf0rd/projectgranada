@echo off
REM Granada - Build Script for Windows
REM This script builds the Windows executable

echo ========================================
echo    Granada Build Script
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

REM Change to script directory
cd /d "%~dp0"

REM Check if virtual environment exists and activate
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo Building Granada executable...
echo.

REM Run the build script
python build.py --clean

echo.
if %ERRORLEVEL% equ 0 (
    echo Build completed successfully!
    echo.
    echo The executable is located in: dist\granada\granada.exe
) else (
    echo Build failed. Please check the error messages above.
)

echo.
pause
