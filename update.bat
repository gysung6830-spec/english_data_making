@echo off
cd /d "%~dp0"
echo ============================================
echo   최신 코드로 업데이트합니다...
echo ============================================

where git >nul 2>nul
if errorlevel 1 (
  echo.
  echo [!] Git 이 설치되어 있지 않아요.
  echo     git-scm.com 에서 Git 을 설치한 뒤 다시 실행하세요.
  echo     (또는 DEPLOY/README 안내대로 최신 코드를 ZIP으로 받으세요)
  pause
  exit /b 1
)

git pull
if errorlevel 1 (
  echo.
  echo [!] 업데이트 중 문제가 생겼어요. 위 메시지를 복사해서 문의하세요.
  pause
  exit /b 1
)

echo.
echo 부품(라이브러리) 최신 상태 확인 중...
python -m pip install -q -r requirements.txt

echo.
echo ============================================
echo   업데이트 완료! 이제 start.bat 으로 실행하세요.
echo ============================================
pause
