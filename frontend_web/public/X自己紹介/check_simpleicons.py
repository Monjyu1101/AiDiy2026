#!/usr/bin/env python3
"""simpleicons.org 一括チェック"""
import urllib.request, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def chk(url):
    try:
        r = urllib.request.urlopen(url, timeout=15, context=ctx)
        return ('OK', len(r.read()))
    except Exception as e:
        return ('ERR', 0)

slugs = [
    ('Anthropic','anthropic'),('Claude','claude'),('OpenAI','openai'),
    ('ChatGPT','openai'),('Codex CLI','openai'),('Google','google'),
    ('Gemini','gemini'),('Ollama','ollama'),('OpenRouter','openrouter'),
    ('Microsoft','microsoft'),('GitHub','github'),
    ('GitHub Copilot','githubcopilot'),('MCP','modelcontextprotocol'),
    ('WebSocket','websocket'),('REST API','restapi'),
    ('JWT','jsonwebtokens'),('CDP','googlechrome'),('VRM','vrm'),
    ('Vue.js','vuedotjs'),('Vite','vite'),('TypeScript','typescript'),
    ('Electron','electron'),('Three.js','threedotjs'),('FastAPI','fastapi'),
    ('Python','python'),('Node.js','nodedotjs'),('SQLAlchemy','sqlalchemy'),
    ('Pinia','pinia'),('Vue Router','vuerouter'),('Axios','axios'),
    ('Monaco Editor','monacoeditor'),('Playwright','playwright'),
    ('Leaflet','leaflet'),('ruff','ruff'),('SQLite','sqlite'),
    ('PostgreSQL','postgresql'),
]

ok = ng = 0
for name, slug in slugs:
    url = 'https://cdn.simpleicons.org/' + slug
    st, sz = chk(url)
    if st == 'OK':
        ok += 1
        mark = '[OK]'
    else:
        ng += 1
        mark = '[NG]'
    print('  ' + mark + ' ' + name + ': ' + st + ' (' + str(sz) + 'B) | ' + url)

print()
print('OK=' + str(ok) + ' NG=' + str(ng))
