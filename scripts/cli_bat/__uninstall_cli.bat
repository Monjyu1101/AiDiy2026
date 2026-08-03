@ECHO OFF

rem  --------
     PAUSE
rem  --------

ECHO;
ECHO ---------
ECHO uninstall
ECHO ---------
start npm uninstall -g @anthropic-ai/claude-code
start npm uninstall -g @openai/codex
start npm uninstall -g opencode-ai
start npm uninstall -g @github/copilot

ECHO;
ECHO Waiting...5s
ping 127.0.0.1 -w 1000 -n 5 >nul

ECHO;
ECHO -----------
ECHO antigravity
ECHO -----------
rem  antigravity CLI has no uninstall subcommand, so remove it manually
if exist "%LOCALAPPDATA%\agy"         rmdir /s /q "%LOCALAPPDATA%\agy"
if exist "%LOCALAPPDATA%\antigravity" rmdir /s /q "%LOCALAPPDATA%\antigravity"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$k='HKCU:\Environment'; $raw=(Get-Item $k).GetValue('Path',$null,'DoNotExpandEnvironmentNames'); if ($raw) { $t=[IO.Path]::Combine($env:LOCALAPPDATA,'agy','bin').TrimEnd('\'); $keep=@(); foreach ($e in ($raw -split ';')) { if ($e -eq '') { continue }; if ([Environment]::ExpandEnvironmentVariables($e).TrimEnd('\') -ieq $t) { continue }; $keep += $e }; $new=($keep -join ';'); if ($new -ne $raw) { Set-ItemProperty -Path $k -Name Path -Value $new -Type ExpandString; Write-Host ('PATH removed: ' + $t) } else { Write-Host 'PATH entry not found' } }"
rem  user settings in %USERPROFILE%\.antigravity are kept

ECHO;
ECHO --------
ECHO npm list
ECHO --------
npm ls -g --depth=0

ECHO;
ECHO NOTE: PATH change takes effect in a new console (or after sign-out).
ECHO NOTE: user settings (.claude / .codex / .antigravity) are NOT removed.

rem  --------
     PAUSE
rem  --------
