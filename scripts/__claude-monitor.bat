@echo off
CD /D "%~dp0..\backend_server"

ECHO claude-monitor --timezone Asia/Tokyo --view realtime
start "Claude Monitor" cmd /k "python -m uv tool run claude-monitor --timezone Asia/Tokyo --view realtime"

ECHO;
ECHO Waiting... 5s
ping localhost -w 1000 -n 5 >nul

exit
