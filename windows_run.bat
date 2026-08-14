@echo off
REM ============================================================
REM  Run the web app. Then open http://127.0.0.1:5000 in a browser.
REM  Usage: double-click this file, or run  windows_run.bat
REM ============================================================
cd /d "%~dp0"
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"

echo Starting the web app.  Open  http://127.0.0.1:5000  in your browser.
echo (Close this window to stop the server.)
python webapp.py
pause
