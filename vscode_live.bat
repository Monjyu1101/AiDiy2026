@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

title AiDiy Live
ECHO.
ECHO ============================================================
ECHO   AiDiy Live
ECHO   %~nx0
ECHO ============================================================

:SELECT_MODEL
ECHO.
ECHO モデル選択
ECHO   1: freeai/gemini-2.5-flash-native-audio-preview-09-2025
ECHO   2: gemini/gemini-2.5-flash-native-audio-preview-12-2025
ECHO   3: openai/gpt-realtime-2.1-mini
ECHO   0: 終了
ECHO.
ECHO 未入力で Enter: モデルを指定せずに起動します。
ECHO Provider は選んだモデルに合わせて自動設定します。
ECHO 起動後も画面の「モデル」から選択できます。
ECHO.
set "PROVIDER="
set "MODEL="
set "MODEL_NUMBER="
set /p "MODEL_NUMBER=番号 [Enter: 指定なし]: "
if not defined MODEL_NUMBER goto LAUNCH_DEFAULT
if "%MODEL_NUMBER%"=="0" goto END
if "%MODEL_NUMBER%"=="1" (
    set "PROVIDER=freeai"
    set "MODEL=gemini-2.5-flash-native-audio-preview-09-2025"
)
if "%MODEL_NUMBER%"=="2" (
    set "PROVIDER=gemini"
    set "MODEL=gemini-2.5-flash-native-audio-preview-12-2025"
)
if "%MODEL_NUMBER%"=="3" (
    set "PROVIDER=openai"
    set "MODEL=gpt-realtime-2.1-mini"
)
if defined PROVIDER goto LAUNCH_SELECTED
ECHO 0〜3 の番号を入力するか、Enter を押してください。
goto SELECT_MODEL

:LAUNCH_DEFAULT
call "%~dp0frontend_vscode\aidiy_live.cmd" %*
set "EXIT_CODE=%ERRORLEVEL%"
goto FINISH

:LAUNCH_SELECTED
call "%~dp0frontend_vscode\aidiy_live.cmd" --provider "%PROVIDER%" --model "%MODEL%" %*
set "EXIT_CODE=%ERRORLEVEL%"

:FINISH
endlocal & exit /b %EXIT_CODE%

:END
endlocal & exit /b 0
