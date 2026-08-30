@echo off
setlocal
cd /d "%~dp0../.."

title Grok Build CLI
ECHO.
ECHO ============================================================
ECHO   Grok Build CLI
ECHO   %~nx0
ECHO ============================================================

set "MODEL="
set /p "UPDATE=update [N]/y: "
if /I "%UPDATE%"=="y" (
    ECHO Install/update Grok Build CLI
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://x.ai/cli/install.ps1 | iex"
    if errorlevel 1 goto INSTALL_FAILED
)

:SELECT_MODEL
ECHO.
ECHO Grok Build CLI model list
ECHO   1: Grok 4.6 - default general and coding
ECHO   2: Grok 4.5 - coding and agent tasks
ECHO.
set "MODEL_NUMBER="
set /p "MODEL_NUMBER=Model number [Enter: default]: "
if not defined MODEL_NUMBER goto LAUNCH
if "%MODEL_NUMBER%"=="1" set "MODEL=grok-4.6"
if "%MODEL_NUMBER%"=="2" set "MODEL=grok-4.5"
if defined MODEL goto LAUNCH
ECHO Invalid input. Enter a number or press Enter.
goto SELECT_MODEL

:LAUNCH
if defined MODEL (
    ECHO grok --yolo --model %MODEL% %*
    call grok --yolo --model "%MODEL%" %*
) else (
    ECHO grok --yolo %*
    call grok --yolo %*
)
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%

:INSTALL_FAILED
ECHO Grok Build CLI installation failed.
endlocal & exit /b 1
