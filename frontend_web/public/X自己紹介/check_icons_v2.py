#!/usr/bin/env python3
"""アイコンURL代替候補のヘルスチェック"""
import urllib.request
import urllib.error
import ssl

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

def check_url(url):
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=10, context=ssl_ctx) as resp:
            status = resp.status
            ctype = resp.headers.get('Content-Type', '')
            return ('OK', status, ctype)
    except urllib.error.HTTPError as e:
        return (f'HTTP_{e.code}', 0, '')
    except Exception as e:
        try:
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=10, context=ssl_ctx) as resp:
                status = resp.status
                ctype = resp.headers.get('Content-Type', '')
                return (f'GET_{status}', status, ctype)
        except Exception as e2:
            return (f'ERROR', 0, '')

# 現在のURL（再確認）
current_urls = [
    ('Anthropic', 'https://anthropic.com/images/favicon.ico'),
    ('Claude', 'https://claude.ai/favicon.ico'),
    ('OpenAI', 'https://openai.com/favicon.ico'),
    ('ChatGPT', 'https://chatgpt.com/favicon.ico'),
    ('Google', 'https://www.google.com/favicon.ico'),
    ('Gemini', 'https://gemini.google.com/favicon.ico'),
    ('Ollama', 'https://ollama.com/favicon.ico'),
    ('OpenRouter', 'https://openrouter.ai/favicon.ico'),
    ('Microsoft', 'https://www.microsoft.com/favicon.ico'),
    ('GitHub', 'https://github.githubassets.com/favicons/favicon.svg'),
    ('Copilot', 'https://github.githubassets.com/assets/copilot-badge-8c7e3f6e.svg'),
    ('MCP', 'https://modelcontextprotocol.io/favicon.ico'),
    ('WebSocket', 'https://upload.wikimedia.org/wikipedia/commons/1/10/WebSocket_icon.svg'),
    ('REST API', 'https://upload.wikimedia.org/wikipedia/commons/1/1f/Rest_api_logo.svg'),
    ('JWT', 'https://jwt.io/img/favicon.ico'),
    ('CDP', 'https://developer.chrome.com/images/chrome-devtools-logo.svg'),
    ('VRM', 'https://vrm.dev/favicon.ico'),
    ('Vue.js', 'https://vuejs.org/logo.svg'),
    ('Vite', 'https://vitejs.dev/logo.svg'),
    ('TypeScript', 'https://www.typescriptlang.org/favicon.ico'),
    ('Electron', 'https://www.electronjs.org/favicon.ico'),
    ('Three.js', 'https://threejs.org/favicon.ico'),
    ('FastAPI', 'https://fastapi.tiangolo.com/img/favicon.ico'),
    ('Python', 'https://www.python.org/favicon.ico'),
    ('Node.js', 'https://nodejs.org/favicon.ico'),
    ('SQLAlchemy', 'https://www.sqlalchemy.org/favicon.ico'),
    ('Pinia', 'https://pinia.vuejs.org/favicon.ico'),
    ('Vue Router', 'https://router.vuejs.org/favicon.ico'),
    ('Axios', 'https://axios-http.com/favicon.ico'),
    ('Monaco', 'https://microsoft.github.io/monaco-editor/favicon.ico'),
    ('Playwright', 'https://playwright.dev/img/playwright-logo.svg'),
    ('Leaflet', 'https://leafletjs.com/favicon.ico'),
    ('ruff', 'https://docs.astral.sh/ruff/favicon.ico'),
    ('SQLite', 'https://sqlite.org/favicon.ico'),
    ('PostgreSQL', 'https://www.postgresql.org/favicon.ico'),
    ('Claude Code', 'https://docs.anthropic.com/en/images/claude-code-logo.svg'),
]

# 代替候補URL
alt_urls = [
    ('Anthropic', 'https://www.cdnlogo.com/logos/a/65/anthropic.svg'),
    ('Anthropic', 'https://upload.wikimedia.org/wikipedia/commons/1/1a/Anthropic_logo.svg'),
    ('OpenAI', 'https://www.cdnlogo.com/logos/o/69/openai.svg'),
    ('OpenAI', 'https://upload.wikimedia.org/wikipedia/commons/4/4d/OpenAI_Logo.svg'),
    ('ChatGPT', 'https://upload.wikimedia.org/wikipedia/commons/0/04/ChatGPT_logo.svg'),
    ('Gemini', 'https://www.gstatic.com/lamda/images/gemini_favicon_64.png'),
    ('Ollama', 'https://ollama.com/public/ollama.png'),
    ('MCP', 'https://modelcontextprotocol.io/logo.svg'),
    ('WebSocket', 'https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/websocket.svg'),
    ('REST API', 'https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/restapi.svg'),
    ('JWT', 'https://jwt.io/img/logo.svg'),
    ('CDP', 'https://www.google.com/favicon.ico'),
    ('Electron', 'https://www.electronjs.org/assets/img/favicon.ico'),
    ('FastAPI', 'https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png'),
    ('Pinia', 'https://pinia.vuejs.org/logo.svg'),
    ('Vue Router', 'https://router.vuejs.org/logo.svg'),
    ('Monaco', 'https://microsoft.github.io/monaco-editor/favicon.ico'),
    ('Leaflet', 'https://leafletjs.com/favicon.ico'),
    ('ruff', 'https://docs.astral.sh/ruff/logo.png'),
]

print('=== 現在のURL 再確認 ===')
for name, url in current_urls:
    status, code, ctype = check_url(url)
    icon = '✅' if status == 'OK' else '❌'
    print(f'  {icon} {name}: {status} | {url}')

print()
print('=== 代替候補URL テスト ===')
for name, url in alt_urls:
    status, code, ctype = check_url(url)
    icon = '✅' if status == 'OK' else '❌'
    print(f'  {icon} {name}: {status} | {url}')
