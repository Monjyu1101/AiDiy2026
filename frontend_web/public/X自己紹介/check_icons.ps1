# アイコンURLヘルスチェックスクリプト
$urls = @(
    @{Name='Anthropic'; URL='https://anthropic.com/images/favicon.ico'},
    @{Name='Claude'; URL='https://claude.ai/favicon.ico'},
    @{Name='OpenAI'; URL='https://openai.com/favicon.ico'},
    @{Name='ChatGPT'; URL='https://chatgpt.com/favicon.ico'},
    @{Name='Google'; URL='https://www.google.com/favicon.ico'},
    @{Name='Gemini'; URL='https://gemini.google.com/favicon.ico'},
    @{Name='Ollama'; URL='https://ollama.com/favicon.ico'},
    @{Name='OpenRouter'; URL='https://openrouter.ai/favicon.ico'},
    @{Name='Microsoft'; URL='https://www.microsoft.com/favicon.ico'},
    @{Name='GitHub'; URL='https://github.githubassets.com/favicons/favicon.svg'},
    @{Name='Copilot'; URL='https://github.githubassets.com/assets/copilot-badge-8c7e3f6e.svg'},
    @{Name='MCP'; URL='https://modelcontextprotocol.io/favicon.ico'},
    @{Name='WebSocket'; URL='https://upload.wikimedia.org/wikipedia/commons/1/10/WebSocket_icon.svg'},
    @{Name='REST API'; URL='https://upload.wikimedia.org/wikipedia/commons/1/1f/Rest_api_logo.svg'},
    @{Name='JWT'; URL='https://jwt.io/img/favicon.ico'},
    @{Name='CDP'; URL='https://developer.chrome.com/images/chrome-devtools-logo.svg'},
    @{Name='VRM'; URL='https://vrm.dev/favicon.ico'},
    @{Name='Vue.js'; URL='https://vuejs.org/logo.svg'},
    @{Name='Vite'; URL='https://vitejs.dev/logo.svg'},
    @{Name='TypeScript'; URL='https://www.typescriptlang.org/favicon.ico'},
    @{Name='Electron'; URL='https://www.electronjs.org/favicon.ico'},
    @{Name='Three.js'; URL='https://threejs.org/favicon.ico'},
    @{Name='FastAPI'; URL='https://fastapi.tiangolo.com/img/favicon.ico'},
    @{Name='Python'; URL='https://www.python.org/favicon.ico'},
    @{Name='Node.js'; URL='https://nodejs.org/favicon.ico'},
    @{Name='SQLAlchemy'; URL='https://www.sqlalchemy.org/favicon.ico'},
    @{Name='Pinia'; URL='https://pinia.vuejs.org/favicon.ico'},
    @{Name='Vue Router'; URL='https://router.vuejs.org/favicon.ico'},
    @{Name='Axios'; URL='https://axios-http.com/favicon.ico'},
    @{Name='Monaco'; URL='https://microsoft.github.io/monaco-editor/favicon.ico'},
    @{Name='Playwright'; URL='https://playwright.dev/img/playwright-logo.svg'},
    @{Name='Leaflet'; URL='https://leafletjs.com/favicon.ico'},
    @{Name='ruff'; URL='https://docs.astral.sh/ruff/favicon.ico'},
    @{Name='SQLite'; URL='https://sqlite.org/favicon.ico'},
    @{Name='PostgreSQL'; URL='https://www.postgresql.org/favicon.ico'},
    @{Name='Claude Code'; URL='https://docs.anthropic.com/en/images/claude-code-logo.svg'}
)

Write-Host "=== アイコンURL ヘルスチェック ===" -ForegroundColor Cyan
Write-Host ""

$results = @()
foreach ($item in $urls) {
    $name = $item.Name
    $url = $item.URL
    try {
        $resp = Invoke-WebRequest -Uri $url -Method Head -TimeoutSec 15 -UseBasicParsing
        $status = [int]$resp.StatusCode
        $type = $resp.Headers['Content-Type']
        if ($status -eq 200) {
            Write-Host "  [$([char]0x2705)] $name" -ForegroundColor Green
            $results += [PSCustomObject]@{Name=$name; URL=$url; Status='OK'; Type=$type}
        } else {
            Write-Host "  [$([char]0x26A0)] $name (HTTP $status)" -ForegroundColor Yellow
            $results += [PSCustomObject]@{Name=$name; URL=$url; Status="HTTP_$status"; Type=$type}
        }
    } catch {
        Write-Host "  [$([char]0x274C)] $name" -ForegroundColor Red
        $results += [PSCustomObject]@{Name=$name; URL=$url; Status='ERROR'; Type=''}
    }
}

Write-Host ""
Write-Host "=== サマリー ===" -ForegroundColor Cyan
$ok = ($results | Where-Object { $_.Status -eq 'OK' }).Count
$ng = ($results | Where-Object { $_.Status -ne 'OK' }).Count
Write-Host "  OK: $ok  NG: $ng" -ForegroundColor $(if ($ng -eq 0) { 'Green' } else { 'Yellow' })

Write-Host ""
Write-Host "=== NG一覧 ===" -ForegroundColor Yellow
$results | Where-Object { $_.Status -ne 'OK' } | Format-Table Name, Status, URL -AutoSize -Wrap
