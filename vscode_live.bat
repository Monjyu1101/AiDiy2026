@echo off
chcp 65001 >nul
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"

title AiDiy Live
ECHO.
ECHO ============================================================
ECHO   AiDiy Live
ECHO   %~nx0
ECHO ============================================================

set "LAUNCHER=%USERPROFILE%\.local\bin\aidiy_live.cmd"
if not exist "%LAUNCHER%" set "LAUNCHER=aidiy_live"

:SELECT_MODEL
ECHO.
ECHO AiDiy Live model list
ECHO   1: FreeAI Gemini native audio
ECHO   2: Gemini native audio
ECHO   3: OpenAI GPT Realtime 2.1 Mini
ECHO   0: Exit
ECHO.
ECHO Press Enter to use the default provider and model.
ECHO You can also select the model in the application.
ECHO.
set "PROVIDER="
set "MODEL="
set "MODEL_NUMBER="
set /p "MODEL_NUMBER=Model number [Enter: default]: "
if "%MODEL_NUMBER%"=="0" goto END
if not defined MODEL_NUMBER goto LAUNCH_DEFAULT
if "%MODEL_NUMBER%"=="1" set "PROVIDER=freeai"
if "%MODEL_NUMBER%"=="1" set "MODEL=gemini-2.5-flash-native-audio-preview-09-2025"
if "%MODEL_NUMBER%"=="2" set "PROVIDER=gemini"
if "%MODEL_NUMBER%"=="2" set "MODEL=gemini-2.5-flash-native-audio-preview-12-2025"
if "%MODEL_NUMBER%"=="3" set "PROVIDER=openai"
if "%MODEL_NUMBER%"=="3" set "MODEL=gpt-realtime-2.1-mini"
if defined MODEL goto LAUNCH_SELECTED
ECHO Invalid input. Enter a number or press Enter.
goto SELECT_MODEL

:LAUNCH_DEFAULT
ECHO aidiy_live %*
call "%LAUNCHER%" %*
set "EXIT_CODE=%ERRORLEVEL%"
goto FINISH

:LAUNCH_SELECTED
ECHO aidiy_live --provider "%PROVIDER%" --model "%MODEL%" %*
call "%LAUNCHER%" --provider "%PROVIDER%" --model "%MODEL%" %*
set "EXIT_CODE=%ERRORLEVEL%"

:FINISH
if "%EXIT_CODE%"=="0" goto END

:FAILED
ECHO.
ECHO AiDiy Live failed to start. Exit code: %EXIT_CODE%
ECHO Check the error shown above.
ECHO If the command was not found, run the frontend_vscode setup in your AiDiy installation.
ECHO Browser mode: %~nx0 --browser
pause
endlocal & exit /b %EXIT_CODE%

:END
endlocal & exit /b 0
