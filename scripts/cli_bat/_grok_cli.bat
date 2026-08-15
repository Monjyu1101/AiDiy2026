@echo off
cd /d "%~dp0../.."

ECHO grok --yolo %*
call grok --yolo %*

exit
