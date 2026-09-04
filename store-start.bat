@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Ortica영어 판매 사이트

REM ============================================================
REM  판매 사이트를 내 컴퓨터에서 띄웁니다. 이 파일을 두 번 누르세요.
REM  (자료를 만드는 도구 start.bat 과는 다른 파일입니다)
REM ============================================================

echo.
echo   Ortica영어 판매 사이트를 시작합니다.
echo.

REM --- 관리자 비밀번호 ---------------------------------------
REM 아래 따옴표 안을 원하는 비밀번호로 바꾸세요. 12자 이상을 권합니다.
set "ADMIN_PASSWORD=ortica-바꾸세요-1234"

REM 내 컴퓨터에서는 https 가 아니므로 로그인 쿠키 조건을 풀어 줍니다.
set "STORE_HTTPS=0"

echo   [1/2] 필요한 라이브러리를 확인합니다...
python -m pip install -q -r store_requirements.txt
if errorlevel 1 (
  echo.
  echo   ! 설치에 실패했습니다. 파이썬이 깔려 있는지 확인해 주세요.
  echo     python.org 에서 받으실 때 "Add Python to PATH" 를 꼭 체크하세요.
  pause
  exit /b 1
)

echo   [2/2] 사이트를 켭니다. 잠시 후 브라우저가 열립니다.
start "" cmd /c "timeout /t 3 >nul & start http://localhost:5001"
python store.py

echo.
echo   사이트가 꺼졌습니다.
pause
