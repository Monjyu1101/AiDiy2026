@echo off
setlocal
cd /d "%~dp0../.."

title AiDiy Hermes CLI
ECHO.
ECHO ============================================================
ECHO   AiDiy Hermes CLI
ECHO   %~nx0
ECHO ============================================================

:SELECT_MODEL
ECHO.
ECHO GPT model list
ECHO   1: GPT-6 Astra - frontier reasoning and coding
ECHO   2: GPT-6.1 Sol - frontier reasoning and coding
ECHO   3: GPT-6 Sol
ECHO   4: GPT-5.6 Terra - balanced quality and cost
ECHO   5: GPT-6 Luna - fast, high-volume work
ECHO   0: Exit
ECHO.
set "MODEL="
set "MODEL_NUMBER="
set /p "MODEL_NUMBER=Model number [Enter: GPT-6.1 Sol]: "
if "%MODEL_NUMBER%"=="0" goto END
if not defined MODEL_NUMBER set "MODEL_NUMBER=2"
if "%MODEL_NUMBER%"=="1" set "MODEL=gpt-6-astra"
if "%MODEL_NUMBER%"=="2" set "MODEL=gpt-6.1-sol"
if "%MODEL_NUMBER%"=="3" set "MODEL=gpt-6-sol"
if "%MODEL_NUMBER%"=="4" set "MODEL=gpt-5.6-terra"
if "%MODEL_NUMBER%"=="5" set "MODEL=gpt-6-luna"
if defined MODEL goto LAUNCH
ECHO Invalid input. Enter a number or press Enter.
goto SELECT_MODEL

:LAUNCH
ECHO aidiy_hermes --yolo --provider openai_oauth --model %MODEL% %*
call aidiy_hermes --yolo --provider openai_oauth --model "%MODEL%" %*
set "EXIT_CODE=%ERRORLEVEL%"

endlocal & exit /b %EXIT_CODE%

:END
endlocal & exit /b 0
