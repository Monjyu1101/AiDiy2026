@echo off
cd /d "%~dp0../.."

ECHO agy --dangerously-skip-permissions %*
call agy --dangerously-skip-permissions %*

exit
