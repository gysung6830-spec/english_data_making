@echo off
chcp 65001 >nul
title Pilsaengbo Textbook Generator
cd /d "%~dp0"

echo ============================================
echo   Pilsaengbo - textbook generator
echo ============================================
echo.

where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js is not installed.
  echo   Install the LTS version from https://nodejs.org
  echo   then double-click this file again.
  echo.
  pause
  exit /b
)

if not exist "node_modules" (
  echo [First run] Installing required files... 1-3 minutes.
  echo.
  call npm install
  echo.
  echo [First run] Installing PDF engine (Chromium browser)...
  call npx playwright install chromium
  echo.
)

echo Starting the web app. Your browser will open shortly.
echo If it does not open, open this address:  http://localhost:3000
echo Keep this window open. To stop: press Ctrl + C, or close the window.
echo.

call npm run web

echo.
echo The web app has stopped.
pause
