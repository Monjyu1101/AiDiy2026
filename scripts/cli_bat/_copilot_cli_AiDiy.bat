@echo off
cd /d "%~dp0../.."

set "COPILOT_CMD=%USERPROFILE%\AppData\Roaming\npm\copilot.cmd"
ECHO copilot --allow-all-tools
call "%COPILOT_CMD%" --allow-all-tools

exit
