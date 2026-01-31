@echo off
CD ".."

ECHO claude --dangerously-skip-permissions --chrome
start "cmd.exe" "%USERPROFILE%\AppData\Roaming\npm\claude.cmd" --dangerously-skip-permissions --chrome

ECHO;
ECHO Waiting... 20s
ping localhost -w 1000 -n 20 >nul

exit
