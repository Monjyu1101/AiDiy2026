# Xビデオ short モード調整 TODO

## 目標
- short モード合計時間：**55秒 ±2秒 (53-57s)**
- long モード合計時間：**3〜7分 (180-420s)**

## 現在の状況（2026-05-15 最終合成後）
合成プロバイダー：freeai → rate limit → **gemini** フォールバック

| ビデオ | short | long | short判定 | long判定 |
|--------|-------|------|-----------|----------|
| `__all` | 62.5s (1.04分) | 435.8s (7.26分) | ↑ 長すぎ (+7.5s) | ↑ やや長め |
| `_aichat` | 57.2s (0.95分) | 261.0s (4.35分) | ↑ ほぼOK (+2.2s) | ✓ |
| `_avatar` | 60.8s (1.01分) | 200.7s (3.34分) | ↑ 長すぎ (+5.8s) | ✓ |
| `_backend` | 54.0s (0.90分) | 247.3s (4.12分) | ✓ | ✓ |
| `_frontend` | 57.0s (0.95分) | 223.5s (3.72分) | ✓ (境界) | ✓ |
| `_hermes` | 64.1s (1.07分) | 186.6s (3.11分) | ↑ 長すぎ (+9.1s) | ✓ |
| `_mcp` | 59.3s (0.99分) | 235.4s (3.92分) | ↑ 長すぎ (+4.3s) | ✓ |

## 問題点・知見

### Gemini TTS の特性
- freeai は 100req/day 制限のため毎回 gemini フォールバック
- gemini TTS は freeai より**ゆっくり**話す（同じテキストで1-2s長い）
- 前回の 65.7s は過去のまずい計測だったが、今回もまだ長い
- 文字数削減の効果が出ているが、ベースが長い

### 各ビデオのシーン別秒数（最新合成前の推定値）
前回のデータ（参考）：
```
__all:   scene_003=7.51s, scene_005=7.39s, scene_007=7.32s, scene_004=6.86s, scene_000=6.84s
_mcp:    scene_000=8.88s, scene_999=8.54s, scene_006=8.42s, scene_005=8.30s
_avatar: scene_002=8.59s, scene_000=7.92s, scene_999=7.99s (長すぎる方)
_hermes: scene_001=8.23s, scene_003=8.16s, scene_000=7.92s (長すぎる方)
```

## 次にやること

### Step 1: 現在の秒数を再計測
```python
python3 /tmp/measure_only.py
```
（スクリプルを作る必要あり。ffprobe で全 audio/short_*.mp3 を計測）

### Step 2: 各ビデオで長すぎるシーンを特定・短縮

#### `__all` (-7.5s 必要, 約33文字削減)
- 最長シーンの short_narration をさらに短縮
- 目安：scene_001 (7.34s推定)「テーブル名・API パス・ファイル名まで日本語で統一したフルスタック業務テンプレートです。」→ 短縮
- scene_003「Core と Apps の 2 サーバー構成で、AI チャットや複数 CLI に対応します。」→ さらに短縮

#### `_mcp` (-4.3s 必要, 約20文字削減)
- scene_001「mcp_main.py が FastAPI の SSE エンドポイントで、13 のツールを一括公開します。」→ 短縮
- scene_002「13 個のツールはブラウザ・DB・バックアップ・音声・画像・動画の 6 グループに分かれます。」→ 短縮

#### `_avatar` (-5.8s 必要, 約27文字削減)
- **重要**: 前回の拡張で逆効果だった可能性。現在 60.8s は元の 48.96s より大幅増加
- 追加したテキストが長すぎた可能性がある
- scene_001: 今回追加した「実行環境の判定は window.desktopApi の有無で行います。」→ 削除
- scene_004: 今回追加した「クリップ切り替えは crossFadeFrom で吸収します。」→ 削除
- scene_005: 今回追加した「Electron と Web は BroadcastChannel でリアルタイム同期します。」→ 削除または短縮

#### `_hermes` (-9.1s 必要, 約42文字削減)
- **重要**: 元の 48.84s から 64.1s へ大幅増加 → 追加したテキストが逆効果
- scene_002: 今回追加「cli_main.py がエントリポイントで、prompt_toolkit を UI に使います。」→ 削除
- scene_004: 今回追加「/model コマンドで provider と model を 2 段階で選べます。」→ 削除または短縮
- scene_999: 今回修正「31 プロバイダー・60 コマンド・5 層構成のコードエージェントです。AiDiy の業務開発にぜひ活かしてください。」→ 短縮

### Step 3: 再合成スクリプト
```bash
cd /workspaces/AiDiy2026/backend_mcp
.venv/bin/python /tmp/regen_4videos.py
```

### Step 4: 目標確認
全ビデオが 53-57s に収まること

## 調整方針（重要）

### Gemini TTS の速度に合わせた文字数目安
- 55秒 / (シーン数) = 1シーンあたりの目標秒数
- `__all`: 10シーン → 各5.5s平均 → 約22-25文字/シーン
- `_mcp`: 8シーン → 各6.9s平均 → 約27-30文字/シーン
- `_avatar`: 7シーン → 各7.9s平均 → 約31-34文字/シーン
- `_hermes`: 7シーン → 各7.9s平均 → 約31-34文字/シーン

gemini の読み上げ速度は約 **4.5文字/秒** (観測値)

### ビデオ別の原則
- `_avatar` と `_hermes`: 元々短すぎたが今回の追加が多すぎた。追加分を削除して元に戻し、1シーンだけ少し伸ばす
- `__all` と `_mcp`: さらなる短縮が必要

## 合成スクリプト場所
- `/tmp/regen_4videos.py` — 4ビデオ限定合成スクリプト（再利用可能）
- `/tmp/regen_short.py` — 全7ビデオ合成スクリプト

## ファイル確認コマンド
```bash
# 現在の秒数確認
python3 -c "
import json, re, os
BASE = '/workspaces/AiDiy2026/frontend_web/public/Xビデオ'
for v in ['__all', '_mcp', '_avatar', '_hermes']:
    path = f'{BASE}/AiDiy紹介{v}/scenario.js'
    js = open(path).read().replace('window.SCENARIO =', '', 1).strip().rstrip(';')
    data = json.loads(js)
    total = sum(s.get('short_duration_sec', 0) for s in data['scenes'])
    print(f'{v}: {total:.2f}s')
    for s in data['scenes']:
        d = s.get('short_duration_sec', 0)
        print(f'  {s[\"id\"]}: {d:.2f}s | {s[\"short_narration\"][:45]}')
"
```
