@echo off
setlocal

REM Create venv if not exists
if not exist .venv (
    python -m venv .venv
)
call .venv\Scripts\activate.bat

pip install --upgrade pip
pip install -r requirements.txt

set PORT=%1
if "%PORT%"=="" set PORT=8000

echo Starting API on port %PORT% ...
uvicorn api_server:app --host 0.0.0.0 --port %PORT%

endlocal

