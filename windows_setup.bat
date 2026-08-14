@echo off
REM ============================================================
REM  Windows 최초 1회 설치 (파이썬 가상환경 + 패키지 + .env)
REM  ※ WeasyPrint용 GTK3 런타임과 (선택) poppler 는 이 스크립트로
REM     설치되지 않습니다 — docs\실행_가이드.md 의 'Windows' 절을 먼저 보세요.
REM  사용법: 이 파일을 더블클릭하거나, 명령프롬프트에서 windows_setup.bat
REM ============================================================
cd /d "%~dp0"

echo [1/3] 가상환경(.venv) 생성...
python -m venv .venv || (echo Python 이 설치돼 있는지 확인하세요. & pause & exit /b 1)
call .venv\Scripts\activate.bat

echo [2/3] 파이썬 패키지 설치...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt || (echo 패키지 설치 실패. & pause & exit /b 1)

echo [3/3] .env 준비...
if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo    .env 를 만들었습니다. 메모장으로 열어 ANTHROPIC_API_KEY 를 입력하세요.
) else (
  echo    .env 가 이미 있습니다.
)

echo.
echo 설치 완료!
echo  - GTK3 런타임을 아직 안 깔았다면 반드시 먼저 설치하세요(안 그러면 PDF 생성 실패).
echo  - 실행: windows_run.bat  (또는  python webapp.py)
pause
