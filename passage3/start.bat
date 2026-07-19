@echo off
chcp 949 >nul
cd /d "%~dp0"
echo ============================================
echo   영어 지문 - 3형식 PDF 생성기 (웹앱)
echo   잠시 후 브라우저가 자동으로 열립니다.
echo   종료하려면 이 창에서 Ctrl+C 를 누르세요.
echo ============================================
start "" cmd /c "timeout /t 3 >nul & start http://localhost:5000"
python webapp.py
pause
