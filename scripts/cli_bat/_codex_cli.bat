@echo off
cd /d "%~dp0../.."

set "CODEX_CMD=%USERPROFILE%\AppData\Roaming\npm\codex.cmd"
ECHO codex --dangerously-bypass-approvals-and-sandbox
call "%CODEX_CMD%" --dangerously-bypass-approvals-and-sandbox

exit
