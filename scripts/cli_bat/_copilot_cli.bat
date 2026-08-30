@echo off
setlocal
cd /d "%~dp0../.."

title GitHub Copilot CLI
ECHO.
ECHO ============================================================
ECHO   GitHub Copilot CLI
ECHO   %~nx0
ECHO ============================================================

set "COPILOT_CMD=%USERPROFILE%\AppData\Roaming\npm\copilot.cmd"
set "MODEL="
set /p "UPDATE=update [N]/y: "
if /I "%UPDATE%"=="y" (
    ECHO Install/update GitHub Copilot CLI
    call npm install -g @github/copilot
    if errorlevel 1 goto INSTALL_FAILED
)

:SELECT_MODEL
ECHO.
ECHO GitHub Copilot CLI model list
ECHO   1: GPT-5.6 Sol - frontier reasoning and coding
ECHO   2: GPT-5.6 Terra - balanced quality and cost
ECHO   3: GPT-5.6 Luna - fast, high-volume work
ECHO   4: Claude Fable 5 - highest Claude capability
ECHO   5: Claude Opus 5 - complex agentic coding
ECHO   6: Claude Sonnet 5 - balanced coding and speed
ECHO   7: Claude Haiku 4.5 - fast and lightweight
ECHO   8: Gemini 3.7 Flash - latest Gemini Flash
ECHO.
set "MODEL_NUMBER="
set /p "MODEL_NUMBER=Model number [Enter: default]: "
if not defined MODEL_NUMBER goto LAUNCH
if "%MODEL_NUMBER%"=="1" set "MODEL=gpt-5.6-sol"
if "%MODEL_NUMBER%"=="2" set "MODEL=gpt-5.6-terra"
if "%MODEL_NUMBER%"=="3" set "MODEL=gpt-5.6-luna"
if "%MODEL_NUMBER%"=="4" set "MODEL=claude-fable-5"
if "%MODEL_NUMBER%"=="5" set "MODEL=claude-opus-5"
if "%MODEL_NUMBER%"=="6" set "MODEL=claude-sonnet-5"
if "%MODEL_NUMBER%"=="7" set "MODEL=claude-haiku-4.5"
if "%MODEL_NUMBER%"=="8" set "MODEL=gemini-3.7-flash"
if defined MODEL goto LAUNCH
ECHO Invalid input. Enter a number or press Enter.
goto SELECT_MODEL

:LAUNCH
if defined MODEL (
    ECHO copilot --allow-all-tools --model %MODEL% %*
    call "%COPILOT_CMD%" --allow-all-tools --model "%MODEL%" %*
) else (
    ECHO copilot --allow-all-tools %*
    call "%COPILOT_CMD%" --allow-all-tools %*
)
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%

:INSTALL_FAILED
ECHO GitHub Copilot CLI installation failed.
endlocal & exit /b 1
