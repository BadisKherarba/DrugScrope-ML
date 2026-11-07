@echo off
echo ========================================================
echo Checking Python version and setting up Python 3.10 environment
echo ========================================================

:: 1. Check if Python 3.10 is accessible via py launcher
py -3.10 --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Python 3.10 is already installed.
    goto create_venv
)

:: 2. Check if default python is 3.10
python -c "import sys; exit(0 if sys.version_info[:2] == (3, 10) else 1)" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Default Python is 3.10.
    goto create_venv
)

:: 3. Python 3.10 is not found, install it using winget
echo [INFO] Python 3.10 was not found. Installing Python 3.10 via Windows Package Manager (winget)...
winget install -e --id Python.Python.3.10 --accept-source-agreements --accept-package-agreements

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Automatic installation via winget failed or was cancelled.
    echo Please download and install Python 3.10 manually from:
    echo https://www.python.org/downloads/release/python-31011/
    echo Remember to check "Add Python to PATH" during installation!
    pause
    exit /b 1
)

:create_venv
echo.
echo ========================================================
echo Creating Python 3.10 Virtual Environment (.venv)...
echo ========================================================
py -3.10 -m venv .venv 2>nul || python -m venv .venv

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

echo [OK] Activating virtual environment and installing packages...
call .venv\Scripts\activate.bat

python -m pip install --upgrade pip
pip install numpy pandas matplotlib openpyxl seaborn

echo.
echo ========================================================
echo Setup complete!
echo To run your data check script:
echo   1. call .venv\Scripts\activate
echo   2. python data\raw\check_data.py
echo ========================================================
pause

