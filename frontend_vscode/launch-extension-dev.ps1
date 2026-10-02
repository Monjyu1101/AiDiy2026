param(
    [string]$ProjectPath = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
$extensionRoot = $PSScriptRoot
$projectRoot = (Resolve-Path -LiteralPath $ProjectPath).Path
if (-not (Test-Path -LiteralPath $projectRoot -PathType Container)) {
    throw 'ProjectPath must be a folder.'
}
if (-not (Test-Path -LiteralPath (Join-Path $extensionRoot 'dist/extension.js'))) {
    Push-Location -LiteralPath $extensionRoot
    try {
        & npm.cmd run compile
        if ($LASTEXITCODE -ne 0) { throw 'Compile failed. Run npm ci in frontend_vscode first.' }
    } finally { Pop-Location }
}
Write-Host "Project folder: $projectRoot"
Write-Host 'Open the chat with: AiDiy: チャットを開く'
# 通常の VS Code が同じフォルダを開いていても、試用ホストで確実に開く。
$tryProfile = Join-Path $extensionRoot 'out/manual-profile'
& code.cmd --new-window --skip-welcome --skip-release-notes "--user-data-dir=$tryProfile" "--extensionDevelopmentPath=$extensionRoot" $projectRoot
if ($LASTEXITCODE -ne 0) { throw 'Could not start VS Code.' }
