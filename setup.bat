@echo off
cd /d "%~dp0"
echo ============================================================
echo   English Passage Analyzer - First-time Setup (Windows)
echo ============================================================

set PY=python
where python >nul 2>nul || set PY=py
%PY% --version >nul 2>nul || (
  echo [ERROR] Python not found.
  echo         Install from https://www.python.org and CHECK
  echo         "Add Python to PATH" during install, then run this again.
  pause
  exit /b 1
)

echo [1/3] Installing Python libraries... this can take a few minutes
%PY% -m pip install --upgrade pip
%PY% -m pip install -r requirements.txt || (
  echo [ERROR] Library install failed. Please screenshot the messages above.
  pause
  exit /b 1
)

echo [2/3] Installing Chromium for workbook PDF rendering...
%PY% -m playwright install chromium

echo [3/3] Preparing API key file (.env)...
if not exist ".env" copy ".env.example" ".env" >nul

echo.
echo [DONE] Setup complete! Now double-click run_webapp.bat to start.
pause
