@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 932 >nul
if errorlevel 1 goto temp_error
rem Standalone CP932 batch. Keep CRLF and chcp 932; labels stay ASCII.
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
rem Transfer without CALL. Never read the original batch after self-update.
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
rem Do not expand user input as command text. Empty input keeps default Yes.
set RUN_AIDIY | findstr /i /x /c:"RUN_AIDIY=n" >nul
if not errorlevel 1 goto cancelled

rem Only bootstrap requirements are fatal here. Normal setup owns Node/npm/uv.
set "RC=2"
set "STAGE=prerequisite_git"
echo [確認] Git
git --version >"%AIDIY_TEMP%\probe.txt" 2>&1
if errorlevel 1 goto prerequisite_failed
type "%AIDIY_TEMP%\probe.txt"
type "%AIDIY_TEMP%\probe.txt" >>"%LOG%"
set "STAGE=prerequisite_robocopy"
echo [確認] robocopy
where robocopy >"%AIDIY_TEMP%\probe.txt" 2>&1
if errorlevel 1 goto prerequisite_failed
>>"%LOG%" echo CHECK robocopy OK
set "STAGE=prerequisite_python"
echo [確認] Python実行環境（3.13以上を推奨、旧版でも続行）
py -3 -X utf8 -c "import sys;encoded=sys.executable.encode('cp932');encoded.decode('cp932')!=sys.executable and sys.exit(3);sys.stdout.buffer.write(encoded+b'\r\n');sys.stderr.write('Python '+sys.version.split()[0]+'\n')" >"%AIDIY_TEMP%\python.txt" 2>"%AIDIY_TEMP%\probe.txt"
if not errorlevel 1 goto python_ready
type "%AIDIY_TEMP%\probe.txt" >>"%LOG%"
python -X utf8 -c "import sys;encoded=sys.executable.encode('cp932');encoded.decode('cp932')!=sys.executable and sys.exit(3);sys.stdout.buffer.write(encoded+b'\r\n');sys.stderr.write('Python '+sys.version.split()[0]+'\n')" >"%AIDIY_TEMP%\python.txt" 2>"%AIDIY_TEMP%\probe.txt"
if errorlevel 1 goto prerequisite_failed
:python_ready
set "PYTHON="
set /p "PYTHON="<"%AIDIY_TEMP%\python.txt"
if not defined PYTHON goto prerequisite_failed
type "%AIDIY_TEMP%\probe.txt"
type "%AIDIY_TEMP%\probe.txt" >>"%LOG%"
rem Minimum versions are warnings only. Never block an executable old Python.
"%PYTHON%" -c "import sys;sys.exit(0 if sys.version_info >= (3,13) else 1)" >nul 2>&1
if errorlevel 1 call :python_version_warning

rem Advisory only: setup offers its normal installation and update choices.
set "STAGE=check_node"
node --version >"%AIDIY_TEMP%\probe.txt" 2>&1
set "CHECK_RC=%ERRORLEVEL%"
call :report_optional_check
set "STAGE=check_npm"
rem npm is commonly npm.cmd. A child CMD returns here instead of chaining away.
"%ComSpec%" /d /c npm --version >"%AIDIY_TEMP%\probe.txt" 2>&1
set "CHECK_RC=%ERRORLEVEL%"
call :report_optional_check
set "STAGE=check_uv"
uv --version >"%AIDIY_TEMP%\probe.txt" 2>&1
set "CHECK_RC=%ERRORLEVEL%"
call :report_optional_check
set "STAGE=git_environment"
rem Refuse inherited Git environment variables that redirect the checkout.
if defined GIT_DIR goto failed
if defined GIT_WORK_TREE goto failed
if defined GIT_COMMON_DIR goto failed
if defined GIT_INDEX_FILE goto failed
if defined GIT_OBJECT_DIRECTORY goto failed
set "GIT_TERMINAL_PROMPT=0"
rem Priority: original cwd, original script directory, USERPROFILE fallback.
set "TARGET=%USERPROFILE%\AiDiy2026"
if exist "%AIDIY_SOURCE_DIR%\backend_server\" set "TARGET=%AIDIY_SOURCE_DIR%"
if exist "%AIDIY_CWD%\backend_server\" set "TARGET=%AIDIY_CWD%"
>>"%LOG%" echo TARGET="%TARGET%"
echo 対象フォルダ: "%TARGET%"
if exist "%TARGET%" goto existing

set "STAGE=clone"
set "STAGING=%USERPROFILE%\.AiDiy2026-clone-%AIDIY_RUN%"
git clone --branch main --single-branch https://github.com/Monjyu1101/AiDiy2026.git "%STAGING%"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" goto failed
rem REN refuses an existing destination. Keep the staging clone on failure.
ren "%STAGING%" "AiDiy2026"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" goto failed

:existing
set "STAGE=repository_validation"
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

set "STAGE=local_backup"
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
set "STAGE=fast_forward_validation"
git merge-base --is-ancestor HEAD FETCH_HEAD
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" goto failed
set "STAGE=fast_forward_update"
git merge --ff-only --no-edit --no-overwrite-ignore --no-autostash FETCH_HEAD
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" goto failed
>>"%LOG%" echo HEAD:
git rev-parse HEAD >>"%LOG%"
if errorlevel 1 goto failed

rem Copy this launcher only when absent. Never overwrite an existing file.
set "STAGE=launcher_copy"
if exist "%TARGET%\_automatic.bat" goto setup
copy /b /v /-y "%~f0" "%TARGET%\_automatic.bat" <nul >nul
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" goto failed

:setup
set "STAGE=setup"
>>"%LOG%" echo SETUP %DATE% %TIME%
echo セットアップ開始。通常の確認入力に回答してください。
"%PYTHON%" -X utf8 -u _setup.py
set "RC=%ERRORLEVEL%"
rem Child tools may change the shared console code page. Restore before Japanese.
chcp 932 >nul
if errorlevel 1 (echo [ERROR] Cannot restore code page 932. TEMP and lock kept. & exit /b 2)
>>"%LOG%" echo SETUP_EXIT=%RC%
if not "%RC%"=="0" goto failed
set "STAGE=start"
>>"%LOG%" echo START_APP %DATE% %TIME%
"%PYTHON%" -X utf8 -u _start.py
set "RC=%ERRORLEVEL%"
rem Child tools may change the shared console code page. Restore before Japanese.
chcp 932 >nul
if errorlevel 1 (echo [ERROR] Cannot restore code page 932. TEMP and lock kept. & exit /b 2)
>>"%LOG%" echo START_EXIT=%RC%
if not "%RC%"=="0" goto failed
>>"%LOG%" echo SUCCESS %DATE% %TIME%
goto finish

:python_version_warning
echo [警告] Pythonは3.13未満です。版の判定では止めず、このPythonでsetup・起動へ進みます。
echo [警告] setupや依存ライブラリが旧版に対応しない場合は、その実際のエラーで停止します。
>>"%LOG%" echo WARNING Python version below 3.13; continuing
exit /b 0

:convert_git_path_text
rem Convert Git UTF-8 path data before FOR/SET reads under CP932. No replacement.
"%PYTHON%" -X utf8 -c "import os,sys;from pathlib import Path;p=Path(os.environ['AIDIY_TEXT_FILE']);text=p.read_bytes().decode('utf-8');encoded=text.encode('cp932');encoded.decode('cp932')!=text and sys.exit(3);p.write_bytes(encoded)" >nul 2>&1
if not errorlevel 1 exit /b 0
echo [エラー] Gitのパス一覧をCP932へ変換できません。文字・読書き権限を確認してください。
>>"%LOG%" echo PATH_ENCODING_FAILED
exit /b 3

:report_optional_check
echo [確認] %STAGE% 終了コード=%CHECK_RC%
>>"%LOG%" echo CHECK %STAGE% exit=%CHECK_RC%
type "%AIDIY_TEMP%\probe.txt"
type "%AIDIY_TEMP%\probe.txt" >>"%LOG%"
if not "%CHECK_RC%"=="0" echo [警告] ツールを確認できません。通常setupの確認・選択へ進みます。
exit /b 0

:prerequisite_failed
echo [エラー] 必須ツールを実行できません: %STAGE%
>>"%LOG%" echo REQUIRED_CHECK_FAILED %STAGE%
type "%AIDIY_TEMP%\probe.txt"
type "%AIDIY_TEMP%\probe.txt" >>"%LOG%"
set "RC=2"
goto failed

:validate_repository
if not exist ".git" exit /b 3
if not exist "_setup.py" exit /b 3
if not exist "_start.py" exit /b 3
git rev-parse --show-prefix >"%AIDIY_TEMP%\prefix.txt"
if errorlevel 1 exit /b 3
for %%F in ("%AIDIY_TEMP%\prefix.txt") do if %%~zF GTR 2 exit /b 3
git remote get-url --all origin >"%AIDIY_TEMP%\origin.txt"
if errorlevel 1 exit /b 3
rem Treat origin URLs as data, never command text. Match the exact allowlist.
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
set "AIDIY_TEXT_FILE=%AIDIY_TEMP%\gitdir.txt"
call :convert_git_path_text
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
set "AIDIY_TEXT_FILE=%AIDIY_TEMP%\untracked.txt"
call :convert_git_path_text
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
echo [エラー] 別の自動実行中、または前回中断したロックが残っています。
echo 全ての自動実行が終了したことを確認してから、次のロックを手動確認してください。
echo "%CONTROL%\run.lock"
goto failed

:cancelled
set "RC=0"
>>"%LOG%" echo CANCELLED
goto finish

:failed
if "%RC%"=="0" set "RC=1"
>>"%LOG%" echo FAILED stage=%STAGE% exit=%RC% %DATE% %TIME%
echo [エラー] "%STAGE%" で停止しました。終了コード=%RC%
echo Git・Python・robocopyの実行環境が必要です。版の不足だけでは停止しません。
echo 上記の処理名とエラー表示、origin/main、競合、権限を確認してください。
echo 既存変更・退避・途中cloneは削除していません。
echo 実行記録: "%LOG%"
if defined STAGING echo 途中clone: "%STAGING%"

:finish
if not defined LOCK_OWNED goto clean_temp
if exist "%CONTROL%\run.lock\owner.txt" del /q "%CONTROL%\run.lock\owner.txt" >nul 2>&1
if exist "%CONTROL%\run.lock\" rd "%CONTROL%\run.lock" >nul 2>&1
:clean_temp
rem Delete only known scratch files. Never delete the currently executing batch.
for %%F in (python.txt probe.txt prefix.txt origin.txt allowed-origins.txt bad-origins.txt branch.txt gitdir.txt unmerged.txt untracked.txt) do if exist "%AIDIY_TEMP%\%%F" del /q "%AIDIY_TEMP%\%%F" >nul 2>&1
>>"%LOG%" echo TEMP_COPY_RETAINED="%~f0"
rem Restore the caller directory before returning. Do not modify that directory.
cd /d "%AIDIY_CWD%" >nul 2>&1
if not errorlevel 1 goto exit_ready
echo [警告] 元の実行フォルダへ復帰できませんでした。
>>"%LOG%" echo CWD_RESTORE_FAILED
if "%RC%"=="0" set "RC=1"
:exit_ready
rem Keep this small TEMP batch so CMD can finish reading it without path errors.
rem No deferred deletion process, wildcard cleanup, ENDLOCAL or self-delete.
if not "%RC%"=="0" pause
exit /b %RC%

:log_error
echo [エラー] 実行ログを作成できません。TEMPのファイルは保持しました。
pause
exit /b 2
:temp_error
echo [エラー] TEMPの自己コピーまたは内部起動情報を確認できません。
echo 引数なしで実行し、TEMPの空き容量・権限を確認してください。ファイルは保持しています。
pause
exit /b 2
