@echo off
cd /d "%~dp0"

set PY=python
where python >nul 2>nul || set PY=py
%PY% --version >nul 2>nul || (
  echo [ERROR] Python not found. Please run setup.bat first.
  pause
  exit /b 1
)

%PY% -c "import flask" >nul 2>nul || (
  echo [INFO] Not installed yet. Please double-click setup.bat first.
  pause
  exit /b 1
)

echo ============================================================
echo   Starting the web app...
echo   Open this address in your browser:  http://localhost:5000
echo   (Close this window to stop the app)
echo ============================================================
%PY% webapp.py
pause
