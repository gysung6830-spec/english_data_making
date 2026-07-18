@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM 파이썬 실행기 찾기 (python 우선, 없으면 py)
set PY=python
where python >nul 2>nul || set PY=py
%PY% --version >nul 2>nul || (
  echo [오류] 파이썬을 찾을 수 없습니다. 먼저 setup.bat 을 실행하세요.
  pause
  exit /b 1
)

REM flask 설치 확인
%PY% -c "import flask" >nul 2>nul || (
  echo [안내] 아직 설치가 안 됐습니다. 먼저 setup.bat 을 더블클릭해 주세요.
  pause
  exit /b 1
)

echo ============================================================
echo   웹앱을 시작합니다.
echo   브라우저에서 아래 주소를 여세요:  http://localhost:5000
echo   (종료하려면 이 창을 닫으세요)
echo ============================================================
%PY% webapp.py
pause
