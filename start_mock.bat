@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   동형모의고사 생성 웹앱을 시작합니다.
echo   잠시 후 브라우저가 자동으로 열립니다.
echo   (종료하려면 이 창에서 Ctrl+C)
echo ============================================
REM 3초 뒤 브라우저 자동 열기
start "" cmd /c "timeout /t 3 >nul & start http://localhost:5001"
python mock_webapp.py
pause
