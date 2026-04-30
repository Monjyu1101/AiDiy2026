@echo off
cd /d "%~dp0../.."

set "COPILOT_CMD=%USERPROFILE%\AppData\Roaming\npm\opencode.cmd"
ECHO opencode
call "%COPILOT_CMD%"

exit
