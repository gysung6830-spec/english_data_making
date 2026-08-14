@echo off
REM ============================================================
REM  Windows 실행 — 웹앱을 켜고 브라우저에서 http://127.0.0.1:5000 접속
REM  사용법: 이 파일을 더블클릭하거나, 명령프롬프트에서 windows_run.bat
REM ============================================================
cd /d "%~dp0"
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"

echo 웹앱을 시작합니다.  브라우저에서  http://127.0.0.1:5000  로 접속하세요.
echo (창을 닫으면 종료됩니다.)
python webapp.py
pause
