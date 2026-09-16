$ErrorActionPreference = 'Stop'
$extensionRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$testRoot = Join-Path $extensionRoot 'out/extension-host'
New-Item -ItemType Directory -Force -Path "$testRoot/user-data/User", "$testRoot/extensions", "$testRoot/workspace" | Out-Null
$settings = '{"security.workspace.trust.enabled":false,"workbench.startupEditor":"none","telemetry.telemetryLevel":"off","update.mode":"none"}'
[IO.File]::WriteAllText("$testRoot/user-data/User/settings.json", $settings, [Text.UTF8Encoding]::new($false))
$codeCmd = (Get-Command code.cmd).Source
$codeExe = Join-Path (Split-Path (Split-Path $codeCmd -Parent) -Parent) 'Code.exe'
$resultPath = Join-Path $testRoot ('result-' + [guid]::NewGuid().ToString('N') + '.txt')
$oldResult = $env:AIDIY_TEST_RESULT
$oldElectron = $env:ELECTRON_RUN_AS_NODE
try {
    $env:AIDIY_TEST_RESULT = $resultPath
    $env:ELECTRON_RUN_AS_NODE = $null
    $arguments = @(
        '--new-window', '--disable-extensions', '--disable-gpu', '--skip-welcome', '--skip-release-notes',
        "--user-data-dir=$testRoot/user-data", "--extensions-dir=$testRoot/extensions",
        "--extensionDevelopmentPath=$extensionRoot", "--extensionTestsPath=$extensionRoot/test/extension-host.cjs",
        "$testRoot/workspace"
    ) | ForEach-Object { '"' + $_ + '"' }
    $testProcess = Start-Process -FilePath $codeExe -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput "$testRoot/stdout.log" -RedirectStandardError "$testRoot/stderr.log"
    if (-not $testProcess.WaitForExit(60000)) {
        & "$env:SystemRoot/System32/taskkill.exe" /PID $testProcess.Id /T /F | Out-Null
        throw 'Extension Host test timed out. See out/extension-host logs.'
    }
    if (-not (Test-Path -LiteralPath $resultPath)) {
        Get-Content -LiteralPath "$testRoot/stdout.log", "$testRoot/stderr.log" -Encoding UTF8 -Tail 20
        throw 'Extension Host test did not complete.'
    }
    Get-Content -LiteralPath $resultPath -Encoding UTF8
} finally {
    $env:AIDIY_TEST_RESULT = $oldResult
    $env:ELECTRON_RUN_AS_NODE = $oldElectron
}
