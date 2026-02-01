@echo off
cd /d "%~dp0../.."

ECHO python _stop.py
start "cmd.exe" "python" _stop.py

ECHO;
ECHO Waiting... 5s
ping localhost -w 1000 -n 5 >nul

exit
