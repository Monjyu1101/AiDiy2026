param([string]$ProjectPath = (Get-Location).Path)

$ErrorActionPreference = 'Stop'
$extensionRoot = $PSScriptRoot
$projectRoot = (Resolve-Path -LiteralPath $ProjectPath).Path
if (-not (Test-Path -LiteralPath $projectRoot -PathType Container)) { throw 'ProjectPath must be a folder.' }
Push-Location -LiteralPath $extensionRoot
try {
    & npm.cmd run compile
    if ($LASTEXITCODE -ne 0) { throw 'Compile failed. Run npm ci in frontend_vscode first.' }
} finally { Pop-Location }
$runRoot = Join-Path $extensionRoot 'out/standalone'
New-Item -ItemType Directory -Force -Path $runRoot | Out-Null
$runId = [guid]::NewGuid().ToString('N')
$readyPath = Join-Path $runRoot "$runId.json"
$nodePath = (Get-Command node.exe).Source
$arguments = @((Join-Path $extensionRoot 'dist/standalone.cjs'), $projectRoot, $readyPath) | ForEach-Object { '"' + $_ + '"' }
$serverProcess = Start-Process -FilePath $nodePath -ArgumentList $arguments -WindowStyle Hidden -PassThru -WorkingDirectory $projectRoot -RedirectStandardOutput "$runRoot/$runId.stdout.log" -RedirectStandardError "$runRoot/$runId.stderr.log"
$deadline = (Get-Date).AddSeconds(15)
while (-not (Test-Path -LiteralPath $readyPath)) {
    if ($serverProcess.HasExited) { throw "Server failed. See $runRoot/$runId.stderr.log" }
    if ((Get-Date) -gt $deadline) { Stop-Process -Id $serverProcess.Id; throw 'Server startup timed out.' }
    Start-Sleep -Milliseconds 100
}
$ready = Get-Content -LiteralPath $readyPath -Encoding UTF8 -Raw | ConvertFrom-Json
$browserCandidates = @(
    "$env:ProgramFiles/Google/Chrome/Application/chrome.exe",
    "${env:ProgramFiles(x86)}/Google/Chrome/Application/chrome.exe",
    "$env:LOCALAPPDATA/Google/Chrome/Application/chrome.exe",
    "${env:ProgramFiles(x86)}/Microsoft/Edge/Application/msedge.exe",
    "$env:ProgramFiles/Microsoft/Edge/Application/msedge.exe"
)
$browserPath = $browserCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if ($browserPath) {
    $browserArguments = @("--app=$($ready.url)", "--user-data-dir=$runRoot/browser-profile", '--no-first-run', '--no-default-browser-check', '--window-size=640,820') | ForEach-Object { '"' + $_ + '"' }
    # ユーザーが操作するチャット専用ウィンドウ。
    Start-Process -FilePath $browserPath -ArgumentList $browserArguments | Out-Null
} else { Start-Process $ready.url | Out-Null }
Write-Host "AiDiy - Project folder: $projectRoot"
Write-Host 'The standalone chat window is open. The server stops after the window has been closed for 60 seconds.'
