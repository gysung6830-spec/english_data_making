@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo   영어 지문 - 3형식 PDF 생성기 : 최초 1회 설치 (Windows)
echo ============================================================
echo.

echo [1/3] 파이썬 라이브러리 설치 중...
pip install -r requirements.txt
if errorlevel 1 goto :err

echo.
echo [2/3] 렌더링용 Chromium 설치 중 (playwright)...
python -m playwright install chromium
if errorlevel 1 (
  echo    [!] Chromium 설치에 실패했습니다. 인터넷 연결 확인 후 다시 실행하세요.
)

echo.
echo [3/3] 한글 폰트 안내
echo    - 인터넷이 되면 '나눔명조' 웹폰트가 자동 로드되어 별도 설치 없이 동작합니다.
echo    - 오프라인에서 쓰려면 '나눔명조(NanumMyeongjo)' 폰트를 Windows에 설치하세요.
echo      (네이버 나눔글꼴 배포처에서 무료 설치 가능)

echo.
echo 설치 완료! 웹앱을 실행하려면  start.bat  을 더블클릭하세요.
echo (선택) 자동 OCR/번역을 쓰려면 시스템 환경변수 ANTHROPIC_API_KEY 를 설정하세요.
echo.
pause
exit /b 0

:err
echo.
echo [!] 라이브러리 설치에 실패했습니다. 파이썬(3.10+)이 설치되어 있는지 확인하세요.
pause
exit /b 1
