@echo off
REM TalkFlow Installation Script for Windows

echo ========================================
echo TalkFlow Installation Script
echo ========================================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.9 or higher.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found: Python %PYTHON_VERSION%
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1
echo pip upgraded
echo.

REM Install dependencies
echo Installing dependencies...
echo (This may take 5-10 minutes...)
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Error installing dependencies
    echo Try running manually: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo All dependencies installed successfully
echo.

echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Download models: python download_models.py
echo   2. Activate environment: venv\Scripts\activate
echo   3. Start TalkFlow: python run.py
echo   4. Open browser: http://localhost:8000
echo.
echo For detailed instructions, see QUICKSTART.md
echo.
pause
