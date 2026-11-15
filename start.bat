@echo off
rem Forkinator 3000 - double-click to run. Needs Python 3 (https://www.python.org/downloads/).
cd /d "%~dp0"

set "PY="
py -3 --version >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if not defined PY (
  python --version >nul 2>nul
  if not errorlevel 1 set "PY=python"
)
if not defined PY (
  echo.
  echo  Python 3 is not installed.
  echo  Install it from https://www.python.org/downloads/
  echo  IMPORTANT: tick "Add python.exe to PATH" in the installer, then double-click start.bat again.
  echo.
  start "" "https://www.python.org/downloads/"
  pause
  exit /b 1
)

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo  Created .env - add your Gemini key there for the real AI (optional^).
)

%PY% -u server.py
pause
