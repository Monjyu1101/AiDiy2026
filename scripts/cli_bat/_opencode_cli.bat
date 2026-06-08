@echo off
cd /d "%~dp0../.."

ECHO ollama launch opencode --model kimi-k2.6:cloud
call ollama launch opencode --model kimi-k2.6:cloud

exit
