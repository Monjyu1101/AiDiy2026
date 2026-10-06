@echo off
chcp 65001 >nul
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0frontend_discord"
if not exist "node_modules\tsx\dist\cli.mjs" (
  echo frontend_discord の依存関係がありません。python frontend_discord\_setup.py を実行してください。
  exit /b 1
)
node "%~dp0frontend_discord\panel\launch.mjs" %*
exit /b %errorlevel%
