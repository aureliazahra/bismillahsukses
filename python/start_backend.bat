@echo off
setlocal ENABLEEXTENSIONS
title Obserra Backend Launcher

REM Change to this script's directory (python/)
cd /d "%~dp0"

echo =============================================
echo   Obserra Backend - One Click Starter
echo   Working dir: %CD%
echo =============================================
echo.

REM Detect Python launcher or python
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  set PY=py -3
) else (
  set PY=python
)

echo Checking Python installation...
%PY% --version
if %ERRORLEVEL% NEQ 0 (
  echo Python not found. Please install Python 3.7+ and try again.
  pause
  exit /b 1
)

echo.
echo Upgrading pip...
%PY% -m pip install --upgrade pip

echo.
echo Installing core requirements...
%PY% -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
  echo Failed to install requirements. Trying individual packages...
  %PY% -m pip install fastapi uvicorn[standard] pydantic python-multipart
)

echo.
echo Installing camera dependencies...
%PY% -m pip install opencv-python numpy PyQt5

echo.
echo Checking camera availability...
%PY% setup_camera.py
if %ERRORLEVEL% NEQ 0 (
  echo.
  echo Camera setup failed. You may need to:
  echo 1. Connect a webcam
  echo 2. Check Windows privacy settings
  echo 3. Update camera drivers
  echo 4. Run as administrator
  echo.
  echo Continuing anyway...
)

echo.
echo Starting backend at http://localhost:8000
echo (Press Ctrl+C in this window to stop)
echo.

REM Run the advanced API with streaming endpoints
%PY% -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

echo.
echo Backend stopped.
pause
