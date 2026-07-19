@echo off
chcp 949 >nul
cd /d "%~dp0"
echo ============================================================
echo   영어 지문 - 3형식 PDF 생성기 : 최초 1회 설치
echo ============================================================
echo.
echo [1/3] 파이썬 라이브러리 설치 중...
pip install -r requirements.txt
if errorlevel 1 goto err
echo.
echo [2/3] 렌더링용 Chromium 설치 중...
python -m playwright install chromium
if errorlevel 1 echo    [주의] Chromium 설치에 실패했습니다. 인터넷 확인 후 다시 실행하세요.
echo.
echo [3/3] 한글 폰트 안내
echo    인터넷이 되면 나눔명조 웹폰트가 자동으로 로드됩니다.
echo    오프라인에서 쓰려면 나눔명조 폰트를 Windows에 직접 설치하세요.
echo.
echo [선택] 자동 OCR, 번역 기능은 ANTHROPIC_API_KEY 설정 시 사용됩니다.
echo.
echo 설치 완료! 이제 start.bat 을 더블클릭하면 웹앱이 열립니다.
echo.
pause
exit /b 0

:err
echo.
echo [주의] 라이브러리 설치에 실패했습니다. 파이썬 3.10 이상이 설치되어 있는지 확인하세요.
pause
exit /b 1
