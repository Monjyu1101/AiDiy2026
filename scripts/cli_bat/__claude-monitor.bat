@echo off
cd /d "%~dp0../.."

ECHO python -m pip install --upgrade pip
ECHO pip install --upgrade wheel
ECHO pip install --upgrade setuptools
     python -m pip install --upgrade pip
     pip install --upgrade wheel
     pip install --upgrade setuptools

ECHO pip install --upgrade claude-monitor
     pip install --upgrade claude-monitor

ECHO claude-monitor --timezone Asia/Tokyo --view realtime
rem start "Claude Monitor" cmd /k "python -m uv tool run claude-monitor --timezone Asia/Tokyo --view realtime"
    start "Claude Monitor" cmd /k "claude-monitor --timezone Asia/Tokyo --view realtime"

ECHO;
ECHO Waiting... 5s
ping localhost -w 1000 -n 5 >nul

exit
