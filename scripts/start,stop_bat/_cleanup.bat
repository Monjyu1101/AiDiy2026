@echo off
cd /d "%~dp0../.."

ECHO python _cleanup.py
start "cmd.exe" "python" _cleanup.py

ECHO;
ECHO Waiting... 5s
ping localhost -w 1000 -n 5 >nul

exit
