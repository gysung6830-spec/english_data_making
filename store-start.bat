@echo off
cd /d "%~dp0"
title 오르티카영어 판매 사이트

rem ============================================================
rem  판매 사이트를 내 컴퓨터에서 띄웁니다. 이 파일을 두 번 누르세요.
rem  (자료를 만드는 도구 start.bat 과는 다른 파일입니다)
rem
rem  이 파일은 CP949(ANSI) 로 저장되어 있습니다. 메모장으로 고치실 때
rem  '다른 이름으로 저장 > 인코딩: ANSI' 를 골라 주세요.
rem ============================================================

rem --- 관리자 비밀번호 -----------------------------------------
rem 아래 따옴표 안을 원하는 비밀번호로 바꾸세요. 영문+숫자 12자 이상을 권합니다.
rem 한글은 넣지 마세요.
set "ADMIN_PASSWORD=ortica-change-me-1234"

rem 내 컴퓨터에서는 https 가 아니므로 로그인 쿠키 조건을 풀어 줍니다.
set "STORE_HTTPS=0"

rem --- 파이썬 찾기 ---------------------------------------------
set "PY="
where python >nul 2>&1 && set "PY=python"
if not defined PY (
    where py >nul 2>&1 && set "PY=py -3"
)
if not defined PY goto NOPYTHON

echo.
echo   오르티카영어 판매 사이트를 시작합니다.
echo.
echo   [1/2] 필요한 라이브러리를 확인합니다. 처음 한 번은 1~2분 걸립니다.
%PY% -m pip install -q -r store_requirements.txt
if errorlevel 1 goto PIPFAIL

echo   [2/2] 사이트를 켭니다. 잠시 후 브라우저가 열립니다.
echo.
echo        손님 화면   http://localhost:5001
echo        관리자 화면 http://localhost:5001/admin
echo.
echo   끄실 때는 이 창에서 Ctrl+C 를 누르거나 창을 닫으세요.
echo.
start "" cmd /c "timeout /t 4 >nul & start http://localhost:5001"
%PY% store.py
goto ENDED

:NOPYTHON
echo.
echo   [!] 파이썬을 찾지 못했습니다.
echo.
echo       python.org 에서 파이썬 3.11 이상을 받아 설치해 주세요.
echo       설치 화면 맨 아래 "Add Python to PATH" 를 꼭 체크하셔야 합니다.
echo       설치한 뒤 컴퓨터를 다시 켜고 이 파일을 다시 눌러 주세요.
echo.
pause
exit /b 1

:PIPFAIL
echo.
echo   [!] 라이브러리 설치에 실패했습니다.
echo       인터넷 연결을 확인하시고 다시 눌러 주세요.
echo       계속 실패하면 이 창을 캡처해서 보내 주세요.
echo.
pause
exit /b 1

:ENDED
echo.
echo   사이트가 꺼졌습니다.
pause
