@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

title AiDiy Code
ECHO.
ECHO ============================================================
ECHO   AiDiy Code
ECHO   %~nx0
ECHO ============================================================

:SELECT_MODEL
ECHO.
ECHO モデル選択
ECHO   1: Sonnet 5.5     (copilot_cli)
ECHO   2: GPT-6 Astra    (openai_oauth)
ECHO   3: GPT-6.1 Sol    (openai_oauth)
ECHO   4: GPT-5.6 Terra  (openai_oauth)
ECHO   5: GPT-6 Luna     (openai_oauth)
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
    set "PROVIDER=copilot-cli"
    set "MODEL=claude-sonnet-5.5"
)
if "%MODEL_NUMBER%"=="2" (
    set "PROVIDER=openai_oauth"
    set "MODEL=gpt-6-astra"
)
if "%MODEL_NUMBER%"=="3" (
    set "PROVIDER=openai_oauth"
    set "MODEL=gpt-6.1-sol"
)
if "%MODEL_NUMBER%"=="4" (
    set "PROVIDER=openai_oauth"
    set "MODEL=gpt-5.6-terra"
)
if "%MODEL_NUMBER%"=="5" (
    set "PROVIDER=openai_oauth"
    set "MODEL=gpt-6-luna"
)
if defined PROVIDER goto LAUNCH_SELECTED
ECHO 0〜5 の番号を入力するか、Enter を押してください。
goto SELECT_MODEL

:LAUNCH_DEFAULT
call "%~dp0frontend_vscode\aidiy_code.cmd" %*
set "EXIT_CODE=%ERRORLEVEL%"
goto FINISH

:LAUNCH_SELECTED
call "%~dp0frontend_vscode\aidiy_code.cmd" --provider "%PROVIDER%" --model "%MODEL%" %*
set "EXIT_CODE=%ERRORLEVEL%"

:FINISH
if "%EXIT_CODE%"=="0" goto EXIT
ECHO.
ECHO 起動に失敗しました。上のエラー内容を確認してください。
ECHO Electron の未配置エラーの場合は、python frontend_vscode\_setup.py を実行してください。
ECHO ブラウザで開く場合は、%~nx0 --browser を実行してください。
pause

:EXIT
endlocal & exit /b %EXIT_CODE%

:END
endlocal & exit /b 0
