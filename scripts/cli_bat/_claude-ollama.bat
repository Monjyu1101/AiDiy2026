@echo off
cd /d "%~dp0../.."

ECHO ollama launch claude --model deepseek-v4-flash:cloud
call "ollama" launch claude --model deepseek-v4-flash:cloud

exit
