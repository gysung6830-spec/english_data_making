@echo off
chcp 65001 >nul
title Pilsaengbo Textbook Generator
cd /d "%~dp0"

echo ============================================
echo   Pilsaengbo - textbook generator
echo ============================================
echo.

where node >nul 2>nul
if errorlevel 1 goto NO_NODE

if not exist "node_modules" goto FIRST_RUN
goto RUN

:FIRST_RUN
echo [First run] Installing required files... 1-3 minutes.
echo.
call npm install
if errorlevel 1 goto NPM_FAIL
echo.
echo [First run] Installing PDF engine (Chromium browser).
echo   If this step is skipped, PDF is auto-installed on first use.
call npx --yes playwright install chromium
echo.
goto RUN

:RUN
echo Starting the web app. Your browser will open shortly.
echo If it does not open, open this address:  http://localhost:3000
echo Keep this window open. To stop: press Ctrl + C, or close the window.
echo.
call npm run web
echo.
echo The web app has stopped.
goto END

:NO_NODE
echo [ERROR] Node.js is not installed.
echo   Install the LTS version from https://nodejs.org
echo   then double-click this file again.
goto END

:NPM_FAIL
echo.
echo [ERROR] npm install failed. Check your internet connection and run again.
goto END

:END
echo.
pause
