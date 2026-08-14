@echo off
REM ============================================================
REM  First-time setup on Windows (venv + packages + .env)
REM  NOTE: GTK3 runtime (required) and poppler (optional) are NOT
REM        installed here. Install the GTK3 runtime first (see the run guide
REM        in the docs folder), otherwise PDF generation will fail.
REM  Usage: double-click this file, or run  windows_setup.bat
REM ============================================================
cd /d "%~dp0"

echo [1/3] Creating virtual environment (.venv) ...
python -m venv .venv
if errorlevel 1 (
  echo   ERROR: Python not found. Install Python 3.10+ and check "Add python.exe to PATH".
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"

echo [2/3] Installing Python packages ...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo   ERROR: package install failed.
  pause
  exit /b 1
)

echo [3/3] Preparing .env ...
if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo   Created .env  -  open it in Notepad and set ANTHROPIC_API_KEY.
) else (
  echo   .env already exists.
)

echo.
echo Done!
echo   1^) Install GTK3 runtime first if you have not (required, else PDF fails).
echo   2^) Edit .env  ->  ANTHROPIC_API_KEY=sk-ant-...
echo   3^) Run:  windows_run.bat   (or  python webapp.py)
pause
