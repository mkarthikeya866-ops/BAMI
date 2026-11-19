@echo off
REM ============================================================
REM BAMI Startup Script for Windows
REM ============================================================
echo ============================================================
echo  BAMI: Bioactive Molecule Intelligence Platform
echo ============================================================

cd /d "%~dp0"

IF EXIST ".venv\Scripts\activate.bat" (
    echo Activating Python virtual environment (.venv)...
    call .venv\Scripts\activate.bat
) ELSE IF EXIST "venv\Scripts\activate.bat" (
    echo Activating Python virtual environment (venv)...
    call venv\Scripts\activate.bat
)

where npm >nul 2>nul
IF %ERRORLEVEL% EQU 0 (
    echo Starting Backend and Frontend via npm run dev...
    npm run dev
) ELSE (
    echo Starting FastAPI Backend on http://127.0.0.1:8000...
    start "BAMI Backend" python -m uvicorn app.main:app --app-dir Backend --host 0.0.0.0 --port 8000 --reload
    echo Starting Frontend Server on http://127.0.0.1:5501...
    start "BAMI Frontend" python -m http.server 5501 --directory Frontend
    echo.
    echo Platform is running!
    echo Open http://localhost:5501 in your browser.
    echo.
)
