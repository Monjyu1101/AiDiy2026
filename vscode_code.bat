@echo off
chcp 65001 >nul
rem -*- coding: utf-8 -*-
rem 
rem -------------------------------------------------------------------------
rem COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
rem Licensed under "AiDiy 公開利用ライセンス v1.1".
rem Commercial use requires prior written consent from all copyright holders.
rem See LICENSE for full terms. Thank you for keeping the rules.
rem https://github.com/monjyu1101/AiDiy2026
rem -------------------------------------------------------------------------
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"

title AiDiy Code
ECHO.
ECHO ============================================================
ECHO   AiDiy Code
ECHO   %~nx0
ECHO ============================================================

set "LAUNCHER=%USERPROFILE%\.local\bin\aidiy_code.cmd"
if not exist "%LAUNCHER%" set "LAUNCHER=aidiy_code"

:SELECT_MODEL
ECHO.
ECHO AiDiy Code model list
ECHO   1: Sonnet 5.5 (Copilot CLI)
ECHO   2: GPT-6 Astra
ECHO   3: GPT-6.1 Sol
ECHO   4: GPT-5.6 Terra
ECHO   5: GPT-6 Luna
ECHO   0: Exit
ECHO.
ECHO Press Enter to use the last selected model (or defaults).
ECHO You can also select the model in the application.
ECHO.
set "PROVIDER="
set "MODEL="
set "MODEL_NUMBER="
set /p "MODEL_NUMBER=Model number [Enter: last/default]: "
if "%MODEL_NUMBER%"=="0" goto END
if not defined MODEL_NUMBER goto LAUNCH_DEFAULT
if "%MODEL_NUMBER%"=="1" set "PROVIDER=copilot-cli"
if "%MODEL_NUMBER%"=="1" set "MODEL=claude-sonnet-5.5"
if "%MODEL_NUMBER%"=="2" set "PROVIDER=openai_oauth"
if "%MODEL_NUMBER%"=="2" set "MODEL=gpt-6-astra"
if "%MODEL_NUMBER%"=="3" set "PROVIDER=openai_oauth"
if "%MODEL_NUMBER%"=="3" set "MODEL=gpt-6.1-sol"
if "%MODEL_NUMBER%"=="4" set "PROVIDER=openai_oauth"
if "%MODEL_NUMBER%"=="4" set "MODEL=gpt-5.6-terra"
if "%MODEL_NUMBER%"=="5" set "PROVIDER=openai_oauth"
if "%MODEL_NUMBER%"=="5" set "MODEL=gpt-6-luna"
if defined MODEL goto LAUNCH_SELECTED
ECHO Invalid input. Enter a number or press Enter.
goto SELECT_MODEL

:LAUNCH_DEFAULT
ECHO aidiy_code %*
call "%LAUNCHER%" %*
set "EXIT_CODE=%ERRORLEVEL%"
goto FINISH

:LAUNCH_SELECTED
ECHO aidiy_code --provider "%PROVIDER%" --model "%MODEL%" %*
call "%LAUNCHER%" --provider "%PROVIDER%" --model "%MODEL%" %*
set "EXIT_CODE=%ERRORLEVEL%"

:FINISH
if "%EXIT_CODE%"=="0" goto END

:FAILED
ECHO.
ECHO AiDiy Code failed to start. Exit code: %EXIT_CODE%
ECHO Check the error shown above.
ECHO If the command was not found, run the frontend_ide/host setup in your AiDiy installation.
ECHO Browser mode: %~nx0 --browser
pause
endlocal & exit /b %EXIT_CODE%

:END
endlocal & exit /b 0
