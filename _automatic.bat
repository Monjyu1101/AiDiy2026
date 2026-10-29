@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
rem 単体配布。元cwdを保持し、TEMPの自己コピーだけで処理する。
if /i "%~1"=="--_aidiy_temp" goto temp_entry
if not defined TEMP goto temp_error
if not defined USERPROFILE goto temp_error
set "AIDIY_CWD=%CD%"
set "AIDIY_SOURCE=%~f0"
set "AIDIY_SOURCE_DIR=%~dp0."
set "ATTEMPTS=0"
:make_temp
set /a ATTEMPTS+=1 >nul
if %ATTEMPTS% GTR 10 goto temp_error
set "AIDIY_RUN=%RANDOM%-%RANDOM%-%RANDOM%"
set "AIDIY_TEMP=%TEMP%\AiDiy-automatic-%AIDIY_RUN%"
mkdir "%AIDIY_TEMP%" >nul 2>&1
if errorlevel 1 goto make_temp
copy /b /v /y "%~f0" "%AIDIY_TEMP%\_automatic.bat" >nul
if errorlevel 1 goto temp_error
rem CALLせず制御を移す。更新で元batが書き換わっても、読み直さない。
"%AIDIY_TEMP%\_automatic.bat" --_aidiy_temp
exit /b 2

:temp_entry
if not defined AIDIY_TEMP goto temp_error
if not defined AIDIY_CWD goto temp_error
if not defined AIDIY_SOURCE goto temp_error
if not defined AIDIY_SOURCE_DIR goto temp_error
if /i not "%~dp0"=="%AIDIY_TEMP%\" goto temp_error
set "RC=0"
set "LOCK_OWNED="
set "LOG_ROOT=%LOCALAPPDATA%\AiDiy\automatic\logs"
if not defined LOCALAPPDATA set "LOG_ROOT=%USERPROFILE%\AiDiy\automatic\logs"
if not exist "%LOG_ROOT%\" mkdir "%LOG_ROOT%" >nul 2>&1
set "LOG=%LOG_ROOT%\automatic-%AIDIY_RUN%.log"
>"%LOG%" echo START %DATE% %TIME%
if errorlevel 1 goto log_error
>>"%LOG%" echo CWD="%AIDIY_CWD%"
echo 実行記録: "%LOG%"
set "RUN_AIDIY=y"
set /p "RUN_AIDIY=aidiyセットアップと実行しますか？ [y]/n: "
rem 入力をコマンドへ展開しない。空入力は既定Yes。
set RUN_AIDIY | findstr /i /x /c:"RUN_AIDIY=n" >nul
if not errorlevel 1 goto cancelled

set "STAGE=前提確認"
set "RC=2"
where git >nul 2>&1
if errorlevel 1 goto failed
git --version >nul 2>&1
if errorlevel 1 goto failed
where node >nul 2>&1
if errorlevel 1 goto failed
node -e "const v=process.versions.node.split('.').map(Number);process.exit(v[0]>22||v[0]===22&&v[1]>=13?0:1)" >nul 2>&1
if errorlevel 1 goto failed
where npm >nul 2>&1
if errorlevel 1 goto failed
where uv >nul 2>&1
if errorlevel 1 goto failed
where robocopy >nul 2>&1
if errorlevel 1 goto failed
py -3 -c "import sys;print(sys.executable);sys.exit(0 if sys.version_info >= (3,13) else 1)" >"%AIDIY_TEMP%\python.txt" 2>nul
if not errorlevel 1 goto python_ready
python -c "import sys;print(sys.executable);sys.exit(0 if sys.version_info >= (3,13) else 1)" >"%AIDIY_TEMP%\python.txt" 2>nul
if errorlevel 1 goto failed
:python_ready
set "PYTHON="
set /p "PYTHON="<"%AIDIY_TEMP%\python.txt"
if not defined PYTHON goto failed
rem Gitの対象を外から差し替える環境変数がある場合は停止する。
if defined GIT_DIR goto failed
if defined GIT_WORK_TREE goto failed
if defined GIT_COMMON_DIR goto failed
if defined GIT_INDEX_FILE goto failed
if defined GIT_OBJECT_DIRECTORY goto failed
set "GIT_TERMINAL_PROMPT=0"
rem 優先順: 元cwd、元bat配置先、USERPROFILE。ショートカットの空cwdにも対応。
set "TARGET=%USERPROFILE%\AiDiy2026"
if exist "%AIDIY_SOURCE_DIR%\backend_server\" set "TARGET=%AIDIY_SOURCE_DIR%"
if exist "%AIDIY_CWD%\backend_server\" set "TARGET=%AIDIY_CWD%"
>>"%LOG%" echo TARGET="%TARGET%"
echo 対象: "%TARGET%"
if exist "%TARGET%" goto existing

set "STAGE=clone"
set "STAGING=%USERPROFILE%\.AiDiy2026-clone-%AIDIY_RUN%"
git clone --branch main --single-branch https://github.com/Monjyu1101/AiDiy2026.git "%STAGING%"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" goto failed
rem renは既存の同名フォルダへ移動しない。競合時は途中取得物を保持する。
ren "%STAGING%" "AiDiy2026"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" goto failed

:existing
set "STAGE=対象検証"
set "RC=3"
cd /d "%TARGET%"
if errorlevel 1 goto failed
call :validate_repository
if errorlevel 1 goto failed
for /f "usebackq delims=" %%G in ("%AIDIY_TEMP%\gitdir.txt") do set "AIDIY_GIT_DIR=%%G"
set "CONTROL=%AIDIY_GIT_DIR%\aidiy-automatic"
if not exist "%CONTROL%\" mkdir "%CONTROL%" >nul 2>&1
if errorlevel 1 goto failed
mkdir "%CONTROL%\run.lock" >nul 2>&1
if errorlevel 1 goto locked
set "LOCK_OWNED=1"
>"%CONTROL%\run.lock\owner.txt" echo %AIDIY_RUN%

set "STAGE=ローカル退避"
set "BACKUP=%CONTROL%\%AIDIY_RUN%"
call :backup_local_state
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" goto failed
>>"%LOG%" echo BACKUP="%BACKUP%"
echo 退避先: "%BACKUP%"

set "STAGE=fetch"
git fetch --no-tags origin main
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" goto failed
set "STAGE=fast-forward検証"
git merge-base --is-ancestor HEAD FETCH_HEAD
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" goto failed
set "STAGE=fast-forward更新"
git merge --ff-only --no-edit --no-overwrite-ignore --no-autostash FETCH_HEAD
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" goto failed
>>"%LOG%" echo HEAD:
git rev-parse HEAD >>"%LOG%"
if errorlevel 1 goto failed

rem 初回配布のbatを次回用に配置する。既存ファイルは上書きしない。
set "STAGE=bat配置"
if exist "%TARGET%\_automatic.bat" goto setup
copy /b /v /-y "%~f0" "%TARGET%\_automatic.bat" <nul >nul
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" goto failed

:setup
set "STAGE=setup"
>>"%LOG%" echo SETUP %DATE% %TIME%
echo セットアップ開始（通常の確認入力を維持します）
"%PYTHON%" -u _setup.py
set "RC=%ERRORLEVEL%"
>>"%LOG%" echo SETUP_EXIT=%RC%
if not "%RC%"=="0" goto failed
set "STAGE=start"
>>"%LOG%" echo START_APP %DATE% %TIME%
"%PYTHON%" -u _start.py
set "RC=%ERRORLEVEL%"
>>"%LOG%" echo START_EXIT=%RC%
if not "%RC%"=="0" goto failed
>>"%LOG%" echo SUCCESS %DATE% %TIME%
goto finish

:validate_repository
if not exist ".git" exit /b 3
if not exist "_setup.py" exit /b 3
if not exist "_start.py" exit /b 3
git rev-parse --show-prefix >"%AIDIY_TEMP%\prefix.txt"
if errorlevel 1 exit /b 3
for %%F in ("%AIDIY_TEMP%\prefix.txt") do if %%~zF GTR 2 exit /b 3
git remote get-url --all origin >"%AIDIY_TEMP%\origin.txt"
if errorlevel 1 exit /b 3
rem originの文字列をコマンドに展開しない。許可リストに完全一致するか確認。
>"%AIDIY_TEMP%\allowed-origins.txt" echo https://github.com/Monjyu1101/AiDiy2026.git
>>"%AIDIY_TEMP%\allowed-origins.txt" echo https://github.com/Monjyu1101/AiDiy2026
>>"%AIDIY_TEMP%\allowed-origins.txt" echo git@github.com:Monjyu1101/AiDiy2026.git
>>"%AIDIY_TEMP%\allowed-origins.txt" echo git@github.com:Monjyu1101/AiDiy2026
for %%F in ("%AIDIY_TEMP%\origin.txt") do if %%~zF EQU 0 exit /b 3
findstr /i /l /x /v /g:"%AIDIY_TEMP%\allowed-origins.txt" "%AIDIY_TEMP%\origin.txt" >"%AIDIY_TEMP%\bad-origins.txt"
if errorlevel 2 exit /b 3
for %%F in ("%AIDIY_TEMP%\bad-origins.txt") do if %%~zF GTR 0 exit /b 3
git branch --show-current >"%AIDIY_TEMP%\branch.txt"
if errorlevel 1 exit /b 3
findstr /x /c:"main" "%AIDIY_TEMP%\branch.txt" >nul
if errorlevel 1 exit /b 3
git rev-parse --absolute-git-dir >"%AIDIY_TEMP%\gitdir.txt"
if errorlevel 1 exit /b 3
for /f "usebackq delims=" %%G in ("%AIDIY_TEMP%\gitdir.txt") do set "AIDIY_GIT_DIR=%%G"
for %%O in (MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD rebase-merge rebase-apply) do if exist "%AIDIY_GIT_DIR%\%%O" exit /b 3
git ls-files --unmerged >"%AIDIY_TEMP%\unmerged.txt"
if errorlevel 1 exit /b 3
for %%F in ("%AIDIY_TEMP%\unmerged.txt") do if %%~zF GTR 0 exit /b 3
exit /b 0

:backup_local_state
mkdir "%BACKUP%" >nul 2>&1
if errorlevel 1 exit /b 1
git status --porcelain=v1 -z --untracked-files=all >"%BACKUP%\status.bin"
if errorlevel 1 exit /b 1
git diff --binary --full-index --no-ext-diff --no-textconv >"%BACKUP%\working-tree.patch"
if errorlevel 1 exit /b 1
git diff --cached --binary --full-index --no-ext-diff --no-textconv >"%BACKUP%\staged.patch"
if errorlevel 1 exit /b 1
git -c core.quotepath=false ls-files --others --exclude-standard >"%AIDIY_TEMP%\untracked.txt"
if errorlevel 1 exit /b 1
for /f "usebackq eol=| delims=" %%F in ("%AIDIY_TEMP%\untracked.txt") do (
    set "UNTRACKED_FILE=%%F"
    call :backup_file
    if errorlevel 1 exit /b 1
)
if not exist "_config\" goto backup_done
robocopy "_config" "%BACKUP%\_config" /E /COPY:DAT /DCOPY:DAT /XJ /SL /R:1 /W:1 /NFL /NDL /NJH /NJS >nul
if errorlevel 8 exit /b 1
:backup_done
git rev-parse HEAD >"%BACKUP%\head.txt"
if errorlevel 1 exit /b 1
exit /b 0

:backup_file
for %%D in ("%BACKUP%\untracked\%UNTRACKED_FILE%") do if not exist "%%~dpD" mkdir "%%~dpD" >nul 2>&1
if errorlevel 1 exit /b 1
copy /b /v /y "%UNTRACKED_FILE%" "%BACKUP%\untracked\%UNTRACKED_FILE%" >nul
if errorlevel 1 exit /b 1
exit /b 0

:locked
set "RC=3"
echo [ERROR] 別の自動実行中、または前回中断のロックがあります。
echo 全ての自動実行が終了したことを確認してから、次のロックだけを手動確認してください。
echo "%CONTROL%\run.lock"
goto failed

:cancelled
set "RC=0"
>>"%LOG%" echo CANCELLED
goto finish

:failed
if "%RC%"=="0" set "RC=1"
>>"%LOG%" echo FAILED stage=%STAGE% exit=%RC% %DATE% %TIME%
echo [ERROR] "%STAGE%" で停止しました。終了コード=%RC%
echo Python 3.13以上、Git、Node.js 22.13以上、npm、uvが必要です。
echo Gitのorigin/main、競合、権限、ネットワークと画面のエラーを確認してください。
echo 既存変更・退避・途中cloneは削除していません。
echo 実行記録: "%LOG%"
if defined STAGING echo 取得先: "%STAGING%"

:finish
if not defined LOCK_OWNED goto clean_temp
del /q "%CONTROL%\run.lock\owner.txt" >nul 2>&1
rd "%CONTROL%\run.lock" >nul 2>&1
:clean_temp
if not "%RC%"=="0" pause
rem 自分で作った既知の一時ファイルだけを削除。未知のファイルは残す。
for %%F in (python.txt prefix.txt origin.txt allowed-origins.txt bad-origins.txt branch.txt gitdir.txt unmerged.txt untracked.txt) do del /q "%AIDIY_TEMP%\%%F" >nul 2>&1
rem 最終行全体が読み込まれた後に、自分を削除して終了コードを返す。
del /q "%~f0" >nul 2>&1 & rd "%AIDIY_TEMP%" >nul 2>&1 & exit /b %RC%

:log_error
echo [ERROR] 実行ログを作成できません。途中TEMPは保持しました。
pause
exit /b 2
:temp_error
echo [ERROR] TEMPの自己コピーまたは内部起動情報を確認できません。
echo 引数なしで実行し、TEMPの容量・権限を確認してください。途中のファイルは保持しています。
pause
exit /b 2
