@echo off
REM LUCA Command Center Installation Script for Windows
REM This script sets up the Django CRM application

echo ==================================
echo LUCA Command Center Installation
echo ==================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.9 or higher and try again.
    pause
    exit /b 1
)

echo [OK] Python found
python --version

REM Step 1: Create virtual environment
echo.
echo Step 1: Creating virtual environment...
if exist venv\ (
    echo Virtual environment already exists. Skipping...
) else (
    python -m venv venv
    echo [OK] Virtual environment created
)

REM Step 2: Activate virtual environment and install dependencies
echo.
echo Step 2: Installing dependencies...
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip >nul 2>&1

REM Install root requirements
if exist requirements.txt (
    echo Installing root requirements.txt...
    pip install -r requirements.txt
    echo [OK] Root requirements installed
)

REM Install Django app requirements
if exist telis_recruitment\requirements.txt (
    echo Installing telis_recruitment\requirements.txt...
    pip install -r telis_recruitment\requirements.txt
    echo [OK] Django app requirements installed
)

REM Step 3: Setup environment variables
echo.
echo Step 3: Setting up environment configuration...
if exist .env (
    echo .env file already exists. Skipping...
) else (
    copy .env.example .env >nul
    echo [OK] Created .env file from .env.example
    echo [WARNING] Please edit .env file and set your SECRET_KEY and other settings!
)

REM Also copy to telis_recruitment if needed
if not exist telis_recruitment\.env (
    copy .env.example telis_recruitment\.env >nul 2>&1 && echo [OK] Also copied .env to telis_recruitment\ || echo [NOTE] Could not copy .env to telis_recruitment\ (may not be needed)
)

REM Step 4: Run database migrations
echo.
echo Step 4: Running database migrations...
cd telis_recruitment
python manage.py migrate
echo [OK] Database migrations completed

REM Step 5: Collect static files
echo.
echo Step 5: Collecting static files...
python manage.py collectstatic --noinput >nul 2>&1
echo [OK] Static files collected

REM Step 6: Create superuser (optional)
echo.
echo Step 6: Create admin superuser...
set /p CREATE_USER="Do you want to create a superuser now? (y/n): "
if /i "%CREATE_USER%"=="y" (
    python manage.py createsuperuser
    echo [OK] Superuser created
) else (
    echo Skipped. You can create a superuser later with: python manage.py createsuperuser
)

cd ..

REM Installation complete
echo.
echo ==================================
echo Installation Complete!
echo ==================================
echo.
echo To start the LUCA Command Center:
echo.
echo   1. Activate virtual environment:
echo      venv\Scripts\activate.bat
echo.
echo   2. Navigate to Django app:
echo      cd telis_recruitment
echo.
echo   3. Start the development server:
echo      python manage.py runserver
echo.
echo   4. Open your browser and visit:
echo      http://127.0.0.1:8000/crm/
echo.
echo For production deployment, see docs\DEPLOYMENT.md
echo.
echo [WARNING] Don't forget to edit .env with your SECRET_KEY and API keys!
echo.
pause
