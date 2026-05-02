@echo off
chcp 65001 >nul
setlocal

set "ROOT=%~dp0"
set "PY=%ROOT%backend_hermes\.venv\Scripts\python.exe"

cd /d "%ROOT%"

if not exist "%PY%" (
  echo Python virtual environment was not found:
  echo   %PY%
  echo.
  echo Run from project root after creating .venv.
  pause
  exit /b 1
)

"%PY%" "%ROOT%backend_hermes\cli_main.py" %*
