@echo off
cd /d "%~dp0../.."

set "CLAUDE_CMD=%USERPROFILE%\AppData\Roaming\npm\claude.cmd"
ECHO claude --dangerously-skip-permissions --chrome
call "%CLAUDE_CMD%" --dangerously-skip-permissions --chrome

exit
