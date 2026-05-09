@echo off
cd /d "%~dp0../.."

rem ECHO ollama launch claude --model deepseek-v4-flash:cloud
    ECHO ollama launch claude --model deepseek-v4-pro:cloud
rem call "ollama" launch claude --model deepseek-v4-flash:cloud
    call "ollama" launch claude --model deepseek-v4-pro:cloud

exit
