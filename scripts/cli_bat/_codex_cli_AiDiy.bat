@echo off
cd /d "%~dp0../.."

ECHO codex --dangerously-bypass-approvals-and-sandbox
start "Codex CLI" "%USERPROFILE%\AppData\Roaming\npm\codex.cmd" --dangerously-bypass-approvals-and-sandbox

ECHO;
ECHO Waiting... 20s
ping localhost -w 1000 -n 20 >nul

exit
