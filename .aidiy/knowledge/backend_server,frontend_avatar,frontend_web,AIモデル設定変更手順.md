# AIモデル設定変更手順

> 文書: `backend_server,frontend_avatar,frontend_web,AIモデル設定変更手順.md` | 実装: `backend_server/_config/AiDiy_key.json`, `backend_server/conf/conf_json.py`, `frontend_web/src/stores/AIモデル設定.ts`

## このメモを使う場面
- Chat / Live / Code AI のモデルや API キーを変更する
- `AiDiy_key.json` と設定 UI の整合を確認する
- 新しい AI 種別や Code CLI を追加した後、設定として選べるようにする

## 関連ファイル
- `backend_server/_config/AiDiy_key.json` — APIキーと現在設定の正マスタ
- `backend_server/conf/conf_json.py` — 設定 JSON の読込、デフォルト、auto 補完
- `backend_server/conf/conf_model.py` — 利用可能モデル一覧
- `backend_server/core_router/AIコア.py` — モデル情報取得/更新 API
- `backend_server/core_router/AIコア/AIセッション管理.py` — セッション用モデル設定
- `frontend_avatar/src/api/config.ts` — backend 取得前のフォールバック
- `frontend_avatar/src/dialog/AI設定再起動.vue` — Avatar 設定 UI
- `frontend_web/src/components/AiDiy/dialog/AI設定再起動.vue` — Web 設定 UI

## AI 種別名のルール

| キー | 末尾ルール | 例 |
|------|-----------|----|
| `CHAT_AI_NAME` | `_chat` | `gemini_chat`, `openrt_chat`, `freeai_chat`, `ollama_chat` |
| `LIVE_AI_NAME` | `_live` | `gemini_live`, `openai_live` |
| `CODE_AI1_NAME`〜`CODE_AI6_NAME` | 原則 `_sdk` または `_cli`、例外 `aidiy_hermes` | `claude_sdk`, `claude_cli`, `copilot_cli`, `codex_cli`, `antigravity_cli`, `opencode_cli`, `aidiy_hermes` |

判定は完全一致を前提にする。`startswith()` などの前方一致へ変えない。

## 設定変更手順

### JSON を直接編集する場合

`backend_server/_config/AiDiy_key.json` を編集し、Chat / Live / Code 6枠のキーを揃える。

```json
{
  "CHAT_AI_NAME": "gemini_chat",
  "LIVE_AI_NAME": "gemini_live",
  "CODE_PERMISSIONS": "auto",
  "CODE_AI1_NAME": "claude_sdk",
  "CODE_AI1_MODEL": "auto",
  "CODE_AI2_NAME": "copilot_cli",
  "CODE_AI2_MODEL": "auto",
  "CODE_AI3_NAME": "codex_cli",
  "CODE_AI3_MODEL": "auto",
  "CODE_AI4_NAME": "antigravity_cli",
  "CODE_AI4_MODEL": "auto",
  "CODE_AI5_NAME": "opencode_cli",
  "CODE_AI5_MODEL": "auto",
  "CODE_AI6_NAME": "aidiy_hermes",
  "CODE_AI6_MODEL": "auto"
}
```

変更後は `backend_server/temp/reboot_core.txt` を作成するか、core server を再起動する。

### 設定 UI から変更する場合

`AI設定再起動.vue` から保存すると、`POST /core/AIコア/モデル設定/更新` が `AiDiy_key.json` を更新し、Reboot 機構で core server を再起動する。

Electron では settings 専用ウィンドウ、Web では同じコンポーネントのモーダル表示を使う。`AI設定再起動.vue` に `window.desktopApi` 前提の処理を直接入れない。

## available_models の流れ

1. frontend が `/core/AIコア/モデル情報/取得` を呼ぶ
2. backend が現在設定と `available_models` を返す
3. 設定 UI が `chat_models` / `live_models` / `code_models` から選択肢を作る
4. 保存時に `/core/AIコア/モデル設定/更新` へ送る
5. 再起動後の再接続で新設定を確認する

新しい AI 種別を追加する場合は、backend が返す `available_models` のキー、frontend の `CHAT_MODEL_KEYS` / `LIVE_MODEL_KEYS` / `LIVE_VOICE_KEYS` / `CODE_MODEL_KEYS`、`conf_json.DEFAULT_CONFIG` を合わせる。

`backend_local` が未起動の場合、`/core/AIコア/モデル情報/取得` は `local_chat` を chat / code モデル候補から除外する。`_start.py` の backend_local 起動デフォルトは No のため、local LLM を使うときだけ明示起動する。

Code CLI の権限モードは `CODE_PERMISSIONS` で管理する。設定 UI では `auto` / `full` / `none` を選択でき、保存時は `AiDiy_key.json` へ書き込まれる。`none` の場合、Claude / Antigravity / Copilot 系の bypass、yolo、自動全ツール許可オプションは付与しない。ただし `codex_cli` はサンドボックス無視を常に有効にするため、`--dangerously-bypass-approvals-and-sandbox` を付与する。CLI 実行時の具体的な反映処理は `AIコード_cli.py` / `AIコード_claude.py` / `command_hermes` 側の実装に合わせて確認する。

## Ollama Chat の local / Cloud 切替

対象:
- `backend_server/core_router/AIコア/AIチャット_ollama.py`
- `backend_server/conf/conf_model.py`
- `backend_server/core_router/AIコア/AIチャット.py`

判断基準:
- `ollama_key_id` が `<` で始まる場合は local Ollama を使う
- 有効なキーがある場合は Ollama Cloud `https://ollama.com/v1` を使う
- local は `ollama_host + "/v1"`、既定は `http://localhost:11434/v1`
- Cloud 直叩き時はモデル名から `:cloud` と入力揺れの `:clude` を外して API に渡す

注意:
- `AiDiy_key.json` は正マスタ。読込時の正規化だけを理由に保存し直さない
- `ollama_chat` は local 実行が正常系なので、キーがプレースホルダーでも welcome 事前チェックで無効扱いにしない
- Cloud のモデル一覧は日付表示形式を他の chat model と揃える

## 注意点

- `frontend_avatar/src/api/config.ts` の `defaultModelSettings()` は backend 取得前のフォールバック。`conf_json.py` のデフォルトとずれると初期表示が混乱する
- `CODE_AI<N>_MODEL` はスロットごとの現在モデル、`CODE_CODEX_CLI_MODEL` のようなキーは CLI 種別ごとのデフォルト。混同しない
- 設定変更は既存 WebSocket セッションへ即時完全反映される前提にしない。再起動後の再接続で確認する
- Code AI は現行6枠。枠数確認は `backend_server/core_router/AIコア.py` と frontend の `PanelKey` を見る

## 確認方法

- `GET http://localhost:8091/core/AIコア/モデル情報/取得` で現在設定と利用可能モデル一覧を確認する（要認証）
- 設定 UI で Chat / Live / Code1〜Code6 の選択肢が出ることを確認する
- 保存後に `AiDiy_key.json` が更新され、core server が再起動することを確認する
