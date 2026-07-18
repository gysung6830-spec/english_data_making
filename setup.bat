@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo   영어 지문 분석 웹앱 - 최초 설치 (윈도우)
echo ============================================================

REM 파이썬 실행기 찾기 (python 우선, 없으면 py)
set PY=python
where python >nul 2>nul || set PY=py
%PY% --version >nul 2>nul || (
  echo [오류] 파이썬을 찾을 수 없습니다.
  echo         https://www.python.org 에서 설치할 때
  echo         "Add Python to PATH" 를 꼭 체크한 뒤 다시 실행하세요.
  pause
  exit /b 1
)

echo [1/3] 파이썬 라이브러리 설치 중... (처음엔 몇 분 걸릴 수 있어요)
%PY% -m pip install --upgrade pip
%PY% -m pip install -r requirements.txt || (
  echo [오류] 라이브러리 설치에 실패했습니다. 위 메시지를 캡처해 알려주세요.
  pause
  exit /b 1
)

echo [2/3] 통합 워크북 PDF 렌더용 Chromium 설치 중...
%PY% -m playwright install chromium

echo [3/3] API 키 설정 파일 준비...
if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo    .env 파일을 만들었습니다. 메모장으로 열어 ANTHROPIC_API_KEY 를 넣을 수 있어요.
  echo    (키 없이 디자인만 볼 거면 웹 화면에서 '샘플 미리보기'를 체크하면 됩니다.)
) else (
  echo    .env 파일이 이미 있습니다.
)

echo.
echo ✅ 설치 완료! 이제 run_webapp.bat 을 더블클릭하면 웹앱이 열립니다.
pause
