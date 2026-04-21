@echo off
REM QA-Buster Local Development Setup Script for Windows

echo.
echo QA-Buster Development Setup
echo ================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo Checking Python version...
python --version

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt

REM Copy .env.example to .env
if not exist .env (
    echo.
    echo Creating .env file from template...
    copy .env.example .env
    echo Please update .env with your Google Sheet CSV_URL
) else (
    echo.
    echo .env already exists
)

REM Create static directory if it doesn't exist
if not exist static (
    mkdir static
)

REM Initialize database
echo.
echo Initializing database...
python -c "from database import init_db; init_db(); print('✓ Database initialized')"

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Update CSV_URL in .env with your Google Sheet
echo 2. Start LM Studio on localhost:1234 (optional)
echo 3. Run: python main.py
echo.
pause
