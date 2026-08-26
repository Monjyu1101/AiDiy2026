@echo off
setlocal
cd /d "%~dp0../.."

set "MODEL="
set "ANTIGRAVITY_INSTALLER=%TEMP%\aidiy_antigravity_install.cmd"
set "AGY_EXE=%LOCALAPPDATA%\agy\bin\agy.exe"
set /p "UPDATE=update [N]/y: "
if /I "%UPDATE%"=="y" (
    ECHO Install/update Antigravity CLI
    curl -fsSL https://antigravity.google/cli/install.cmd -o "%ANTIGRAVITY_INSTALLER%"
    if errorlevel 1 goto INSTALL_FAILED
    call "%ANTIGRAVITY_INSTALLER%"
    if errorlevel 1 goto INSTALL_FAILED
    del /q "%ANTIGRAVITY_INSTALLER%" >nul 2>&1
)

:SELECT_MODEL
ECHO.
ECHO Antigravity CLI model list
ECHO   1: Gemini 3.7 Flash - default
ECHO.
set "MODEL_NUMBER="
set /p "MODEL_NUMBER=Model number [Enter: default]: "
if not defined MODEL_NUMBER goto LAUNCH
if "%MODEL_NUMBER%"=="1" set "MODEL=gemini-3.7-flash"
if defined MODEL goto LAUNCH
ECHO Invalid input. Enter a number or press Enter.
goto SELECT_MODEL

:LAUNCH
if exist "%AGY_EXE%" goto LAUNCH_BY_PATH
where agy >nul 2>&1
if errorlevel 1 goto NOT_INSTALLED

if defined MODEL (
    ECHO agy --dangerously-skip-permissions --model %MODEL% %*
    call agy --dangerously-skip-permissions --model "%MODEL%" %*
) else (
    ECHO agy --dangerously-skip-permissions %*
    call agy --dangerously-skip-permissions %*
)
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%

:LAUNCH_BY_PATH
if defined MODEL (
    ECHO "%AGY_EXE%" --dangerously-skip-permissions --model %MODEL% %*
    call "%AGY_EXE%" --dangerously-skip-permissions --model "%MODEL%" %*
) else (
    ECHO "%AGY_EXE%" --dangerously-skip-permissions %*
    call "%AGY_EXE%" --dangerously-skip-permissions %*
)
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%

:NOT_INSTALLED
ECHO Antigravity CLI is not installed. Restart this script and enter y at the update prompt.
endlocal & exit /b 1

:INSTALL_FAILED
del /q "%ANTIGRAVITY_INSTALLER%" >nul 2>&1
ECHO Antigravity CLI installation failed.
endlocal & exit /b 1
