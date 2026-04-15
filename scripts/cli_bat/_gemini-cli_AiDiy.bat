@echo off
cd /d "%~dp0../.."

set "GEMINI_CMD=%USERPROFILE%\AppData\Roaming\npm\gemini.cmd"
ECHO gemini --yolo
call "%GEMINI_CMD%" --yolo

exit
