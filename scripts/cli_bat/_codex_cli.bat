@echo off
setlocal
cd /d "%~dp0../.."

set "CODEX_CMD=%USERPROFILE%\AppData\Roaming\npm\codex.cmd"
set "MODEL="
set /p "UPDATE=update [N]/y: "
if /I "%UPDATE%"=="y" (
    ECHO Install/update Codex CLI
    call npm install -g @openai/codex
    if errorlevel 1 goto INSTALL_FAILED
)

:SELECT_MODEL
ECHO.
ECHO Codex CLI model list
ECHO   1: GPT-5.6 Sol - frontier reasoning and coding
ECHO   2: GPT-5.6 Terra - balanced quality and cost
ECHO   3: GPT-5.6 Luna - fast, high-volume work
ECHO.
set "MODEL_NUMBER="
set /p "MODEL_NUMBER=Model number [Enter: default]: "
if not defined MODEL_NUMBER goto LAUNCH
if "%MODEL_NUMBER%"=="1" set "MODEL=gpt-5.6-sol"
if "%MODEL_NUMBER%"=="2" set "MODEL=gpt-5.6-terra"
if "%MODEL_NUMBER%"=="3" set "MODEL=gpt-5.6-luna"
if defined MODEL goto LAUNCH
ECHO Invalid input. Enter a number or press Enter.
goto SELECT_MODEL

:LAUNCH
if defined MODEL (
    ECHO codex --dangerously-bypass-approvals-and-sandbox --model %MODEL% %*
    call "%CODEX_CMD%" --dangerously-bypass-approvals-and-sandbox --model "%MODEL%" %*
) else (
    ECHO codex --dangerously-bypass-approvals-and-sandbox %*
    call "%CODEX_CMD%" --dangerously-bypass-approvals-and-sandbox %*
)
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%

:INSTALL_FAILED
ECHO Codex CLI installation failed.
endlocal & exit /b 1
