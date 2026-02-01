@echo off
cd /d "%~dp0../.."

ECHO gemini --yolo
start "Gemini CLI" "%USERPROFILE%\AppData\Roaming\npm\gemini.cmd" --yolo

ECHO;
ECHO Waiting... 20s
ping localhost -w 1000 -n 20 >nul

exit
