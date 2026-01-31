@echo off
CD /D "%~dp0.."

ECHO copilot --allow-all-tools
start "Copilot CLI" "%USERPROFILE%\AppData\Roaming\npm\copilot.cmd" --allow-all-tools

ECHO;
ECHO Waiting... 20s
ping localhost -w 1000 -n 20 >nul

exit
