@echo off
chcp 65001 >nul
title 필생보 교재 생성기
cd /d "%~dp0"

echo ============================================
echo   필생보 교재 생성기 시작
echo ============================================
echo.

where node >nul 2>nul
if errorlevel 1 (
  echo [오류] Node.js 가 설치돼 있지 않습니다.
  echo   https://nodejs.org 에서 LTS 버전을 설치한 뒤, 이 파일을 다시 더블클릭하세요.
  echo.
  pause
  exit /b
)

if not exist "node_modules" (
  echo [최초 1회] 필요한 파일을 설치합니다. 1~3분 걸립니다...
  echo.
  call npm install
  echo.
)

echo 웹앱을 켭니다. 잠시 후 브라우저가 자동으로 열립니다.
echo (안 열리면 주소창에  http://localhost:3000  을 입력하세요.)
echo 이 창을 닫으면 웹앱도 꺼집니다.  종료: Ctrl + C
echo.

call npm run web

echo.
echo 웹앱이 종료되었습니다.
pause
