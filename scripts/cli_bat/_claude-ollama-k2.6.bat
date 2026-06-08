@echo off
cd /d "%~dp0../.."

    ECHO "ollama" launch claude --model kimi-k2.6:cloud   -- --dangerously-skip-permissions --chrome
    call "ollama" launch claude --model kimi-k2.6:cloud   -- --dangerously-skip-permissions --chrome

exit
