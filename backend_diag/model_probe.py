#!/usr/bin/env python3
# 診断専用 read-only bridge。CLI は status / test 固定ID のみ。
# config クラスを初期化せず、コピーしたモデル加工処理だけを読み込む。
import datetime
import http.client
import importlib.util
import json
import re
import ssl
import sys
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
CONFIG_LIMIT = 128 * 1024
RESPONSE_LIMIT = 1024 * 1024
REGISTRY = (
    ('gemini', 'Gemini', 'gemini_key_id', 'google'),
    ('freeai', 'FreeAI（Gemini）', 'freeai_key_id', 'google'),
    ('claude', 'Claude', 'claude_key_id', 'anthropic'),
    ('openai', 'OpenAI API', 'openai_key_id', 'openai'),
    ('azure', 'Azure OpenAI', 'azure_key_id', None),
    ('copilot', 'GitHub Copilot', 'copilot_key_id', None),
    ('openrt', 'OpenRouter', 'openrt_key_id', 'openrouter'),
    ('ollama', 'Ollama Cloud', 'ollama_key_id', 'ollama'),
    ('huggingface_read', 'Hugging Face 読取', 'huggingface_key_read', None),
    ('huggingface_write', 'Hugging Face 書込', 'huggingface_key_write', None),
    ('discord', 'Discord Bot', 'DISCORD_BOT_TOKEN', None),
)
ENDPOINTS = {
    'google': ('generativelanguage.googleapis.com', '/v1beta/models'),
    'anthropic': ('api.anthropic.com', '/v1/models'),
    'openai': ('api.openai.com', '/v1/models'),
    'openrouter': ('openrouter.ai', '/api/v1/models'),
    'ollama': ('ollama.com', '/v1/models'),
}

def load_catalog():
    target = Path(__file__).resolve().with_name('model_catalog_copy.py')
    spec = importlib.util.spec_from_file_location('aidiy_model_catalog', target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_config(reader=None):
    try:
        if reader:
            raw = reader(ROOT / '_config' / 'AiDiy_key.json')
        else:
            with (ROOT / '_config' / 'AiDiy_key.json').open('rb') as stream:
                raw = stream.read(CONFIG_LIMIT + 1)
        if isinstance(raw, str):
            raw = raw.encode('utf-8')
        if len(raw) > CONFIG_LIMIT:
            raise ValueError('size')
        value = json.loads(raw.decode('utf-8-sig'))
        if not isinstance(value, dict):
            raise ValueError('shape')
        return '読込済み', value
    except FileNotFoundError:
        return '未作成', {}
    except Exception:
        return '読込不可', {}


def configured(value, ident):
    return isinstance(value, str) and bool(value.strip()) and not value.strip().startswith('<') and not (ident == 'ollama' and value.strip().lower() == 'ollama')


def status(reader=None):
    state, values = read_config(reader)
    rows = []
    for ident, label, key, probe in REGISTRY:
        present = None if state == '読込不可' else configured(values.get(key), ident)
        public = ident == 'openrt'
        reason = ('設定を読み取れません。' if state == '読込不可' else
                  'キーが未設定です。' if not present and not public else
                  'この項目の接続テストは未対応です。' if not probe else '')
        rows.append(dict(id=ident, 名前=label, キー名=key, 設定済み=present,
                         キー不要=public, 状態='未実施', 理由=reason,
                         テスト可能=state != '読込不可' and bool(probe) and (bool(present) or public),
                         説明='起動時の公開モデル一覧キャッシュを表示します。キーの有効性は確認しません。' if public else '設定有無のみ。接続は未確認です。'))
    return dict(設定状態=state, 項目=rows, モデル=[])


def fetch_metadata(provider, headers, page_token=None):
    host, endpoint = ENDPOINTS[provider]
    if page_token:
        if provider != 'google' or not isinstance(page_token, str) or len(page_token) > 4096:
            raise ValueError('pagination')
        endpoint += '?' + urlencode({'pageToken': page_token})
    # http.client は環境 proxy を使用しない。固定 host、TLS検証、redirectなし。
    connection = http.client.HTTPSConnection(host, timeout=8, context=ssl.create_default_context())
    try:
        connection.request('GET', endpoint, headers={'Accept': 'application/json', **headers})
        response = connection.getresponse()
        if response.status < 200 or response.status >= 300:
            raise ValueError('http')
        raw = response.read(RESPONSE_LIMIT + 1)
        if len(raw) > RESPONSE_LIMIT:
            raise ValueError('size')
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError('shape')
        return data
    finally:
        connection.close()


def safe_details(models, secrets, limit=500):
    result = []
    for ident, entry in models.items():
        if not isinstance(ident, str) or len(ident) > 200 or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/@+\-]*', ident):
            continue
        values = dict(entry)
        values['model_id'] = ident
        cleaned = {}
        for name in ('model_id', '作成日', 'トークン数', 'モダリティ'):
            val = values.get(name)
            if val is not None:
                val = str(val)
                if len(val) > 512 or any(secret in val for secret in secrets):
                    val = None
            cleaned[name] = val
        if cleaned['model_id'] is not None:
            result.append(cleaned)
    return result if limit is None else result[:limit]


def public_catalog(fetch=fetch_metadata, catalog=None, now=None):
    """起動時の匿名取得専用。設定ファイルもキーも参照しない。"""
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        catalog = catalog or load_catalog()
        body = fetch('openrouter', {})
        if not isinstance(body.get('data'), list):
            raise ValueError('shape')
        models = catalog.openrouter_catalog(body, now=now)
        details = safe_details(models, [], limit=None)
        result = dict(状態='OK', 公開モデル={item['model_id']:item for item in details}, 確認日時=timestamp,
                      説明='公開OpenRouter一覧の匿名取得成功。キーの有効性は未確認です。')
        if len(json.dumps(result, ensure_ascii=False).encode('utf-8')) > RESPONSE_LIMIT:
            raise ValueError('size')
        return result
    except Exception:
        return dict(状態='NG', 公開モデル={}, 確認日時=timestamp, 説明='公開OpenRouter一覧を取得できませんでした。')


def validated_cache(cache):
    if not isinstance(cache, dict) or cache.get('公開状態') != '取得済' or not isinstance(cache.get('公開モデル'), dict):
        return {}, False
    raw = cache['公開モデル']
    if any(not isinstance(value, dict) for value in raw.values()):
        return {}, False
    details = safe_details(raw, [], limit=None)
    return {item['model_id']:item for item in details}, True


def read_cache(stream):
    try:
        raw = stream.read(RESPONSE_LIMIT + 1)
        if len(raw) > RESPONSE_LIMIT:
            raise ValueError('size')
        value = json.loads(raw)
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def probe(ident, reader=None, fetch=fetch_metadata, catalog=None, now=None, cache=None):
    output = dict(id=ident, 状態='未実施', 説明='未対応の項目です。', モデル=[], モデル詳細=[], 確認日時=None, 警告=[])
    selected = next((row for row in REGISTRY if row[0] == ident), None)
    if selected is None or selected[3] is None:
        return output
    router, cache_ready = validated_cache(cache)
    if ident == 'openrt':
        if not cache_ready:
            return {**output, '説明': '起動時の公開OpenRouter一覧がまだ利用できません。キーのテストは未実施です。'}
        details = safe_details(router, [])
        return {**output, '状態': 'OK', '説明': '起動時の匿名取得結果を表示。キーの有効性・生成可否・課金状態は未確認です。',
                'モデル': [item['model_id'] for item in details], 'モデル詳細': details,
                '確認日時': cache.get('確認日時'), '一覧範囲': '公開一覧のキャッシュ。最大500件。'}
    state, values = read_config(reader)
    if state == '読込不可':
        return {**output, '説明': '設定を読み取れません。'}
    _, _, key_name, provider = selected
    public = provider == 'openrouter'
    if not public and not configured(values.get(key_name), ident):
        return {**output, '説明': 'キーが未設定です。'}
    key = values.get(key_name, '').strip() if isinstance(values.get(key_name), str) else ''
    # 取得時刻はUIへ返す。モデルの作成日は既存Python関数が生成する。
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        catalog = catalog or load_catalog()
    except Exception:
        return {**output, '説明': '診断用Pythonモデル処理を読み込めません。'}
    warnings = []
    if provider in ('google', 'openai', 'anthropic') and not cache_ready:
        warnings.append('起動時の公開OpenRouter一覧が利用できません。既存Pythonと同じ空一覧時の処理で、日付・対応情報の補完なしで続行しました。')
    try:
        headers = {}
        if provider == 'google':
            headers['x-goog-api-key'] = key
        elif provider == 'anthropic':
            headers.update({'x-api-key': key, 'anthropic-version': '2023-06-01'})
        elif not public:
            headers['Authorization'] = 'Bearer ' + key
        organization = values.get('openai_organization')
        if provider == 'openai' and configured(organization, ''):
            headers['OpenAI-Organization'] = organization.strip()
        body = fetch(provider, headers)
        if provider == 'google':
            if not isinstance(body.get('models'), list):
                raise ValueError('shape')
            entries = list(body['models'])
            token = body.get('nextPageToken')
            pages = 1
            while token:
                if pages >= 20:
                    raise ValueError('pages')
                body = fetch(provider, headers, token)
                if not isinstance(body.get('models'), list):
                    raise ValueError('shape')
                entries.extend(body['models'])
                token = body.get('nextPageToken')
                pages += 1
            models = catalog.google_catalog([
                SimpleNamespace(name=item['name'], supported_actions=item.get('supportedGenerationMethods', []), input_token_limit=item.get('inputTokenLimit'))
                for item in entries
            ], router)
        else:
            if not isinstance(body.get('data'), list):
                raise ValueError('shape')
            if public:
                models = catalog.openrouter_catalog(body, now=now)
            elif provider == 'openai':
                models = catalog.openai_catalog([SimpleNamespace(id=item['id'], created=item['created']) for item in body['data']], router, now=now)
            elif provider == 'anthropic':
                models = catalog.claude_catalog(SimpleNamespace(data=[SimpleNamespace(id=item['id'], created_at=item.get('created_at')) for item in body['data']]), router, now=now)
            else:
                models = catalog.ollama_catalog(body, now=now)
        secrets = [val.strip() for _, _, key_name, _ in REGISTRY if isinstance((val := values.get(key_name)), str) and configured(val, '')]
        if configured(values.get('openai_organization'), ''):
            secrets.append(values['openai_organization'].strip())
        details = safe_details(models, secrets)
        return {**output, '状態': 'OK', 'モデル': [item['model_id'] for item in details], 'モデル詳細': details,
                '確認日時': timestamp, '警告': warnings, '説明': ('公開モデル一覧API取得成功。キーの有効性・生成可否・課金状態は未確認です。' if public else 'モデル一覧API取得成功。既存Pythonの絞り込み・補完を適用。生成可否・課金状態は未確認です。'),
                '一覧範囲': '既存Pythonからコピーした処理による取得モデルの絞り込み結果、表示は最大500件。静的・OAuth候補は含みません。',
                '補完': '起動時の公開OpenRouter一覧キャッシュを利用。テスト時の追加取得は行いません。' if provider in ('google','openai','anthropic') else ''}
    except Exception:
        return {**output, '状態': 'NG', '説明': 'モデル一覧APIの通信または診断用Python処理に失敗しました。', '確認日時': timestamp, '警告': warnings}


def main():
    if sys.argv[1:] == ['status']:
        result = status()
    elif sys.argv[1:] == ['public']:
        result = public_catalog()
    elif len(sys.argv) == 3 and sys.argv[1] == 'test' and sys.argv[2] in {row[0] for row in REGISTRY}:
        result = probe(sys.argv[2], cache=read_cache(sys.stdin.buffer))
    else:
        result = dict(状態='未実施', 説明='未対応の操作です。', モデル=[])
    print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__':
    main()
