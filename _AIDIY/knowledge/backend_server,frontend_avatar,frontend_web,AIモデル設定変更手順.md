# AIモデル設定変更手順

> 文書: `backend_server,frontend_avatar,frontend_web,AIモデル設定変更手順.md` | 実装: `_config/AiDiy_key.json`, `backend_server/conf/conf_json.py`, `backend_server/AIコア/AIチャット_openai.py`, `frontend_web/src/components/AiDiy/dialog/AI設定再起動.vue`

## このメモを使う場面
- Chat / Live / Code / Task / Team AI のモデルや API キーを変更する
- `AiDiy_key.json` と設定 UI の整合を確認する
- 新しい AI 種別や Code CLI を追加した後、設定として選べるようにする

## 関連ファイル
- `_config/AiDiy_key.json` — APIキーと現在設定の正マスタ
- `backend_server/conf/conf_json.py` — 設定 JSON の読込、デフォルト、auto 補完
- `backend_server/conf/conf_model.py` — 利用可能モデル一覧
- `backend_server/core_router/AIコア.py` — モデル情報取得/更新 API
- `backend_server/AIコア/AIセッション管理.py` — セッション用モデル設定
- `frontend_avatar/src/api/config.ts` — backend 取得前のフォールバック
- `frontend_avatar/src/dialog/AI設定再起動.vue` — Avatar 設定 UI
- `frontend_web/src/components/AiDiy/dialog/AI設定再起動.vue` — Web 設定 UI

## AI 種別名のルール

| キー | 末尾ルール | 例 |
|------|-----------|----|
| `CHAT_AI_NAME` | 原則 `_chat`（OAuth は例外） | `gemini_chat`, `openrt_chat`, `openai_chat`, `openai_oauth`, `freeai_chat`, `ollama_chat`, `local_chat` |
| `LIVE_AI_NAME` | `_live` | `gemini_live`, `freeai_live`, `openai_live` |
| `CODE_AI1_NAME`〜`CODE_AI6_NAME` | 原則 `_sdk` または `_cli`、例外 `aidiy_hermes` | `claude_sdk`, `claude_cli`, `copilot_cli`, `codex_cli`, `antigravity_cli`, `grok_cli`, `opencode_cli`, `aidiy_hermes` |
| `TASK_AI_NAME` / `TEAM_AI_NAME` | Code AI と同じ候補を使用 | `claude_cli`, `codex_cli`, `aidiy_hermes` |

判定は完全一致を前提にする。`startswith()` などの前方一致へ変えない。

## TASK / TEAM モデルの3種指定

モデルだけは AI 名1つに対して plan / do / check の3種を持つ。

| キー | 使う処理 |
|------|---------|
| `TASK_AI_MODEL_plan` | Aタスクの準備＝明細分解（`task_sub/sub_init.py`）、Aチーム要員選定・経験まとめ、雑談発言 |
| `TASK_AI_MODEL_do` | Aタスクの各ステップ実行（`task_sub/sub_do.py`）、自己作業、要求・明細・依頼レコードの既定値 |
| `TASK_AI_MODEL_check` | 終了時の最終確認（`task_sub/sub_end.py`） |
| `TEAM_AI_MODEL_plan` / `_do` / `_check` | 作業ループの段（S・P=plan / D=do / C・A=check、`team_sub/sub_SPDCA__common.py` の `段フェーズ`） |

判断基準:

- 共通設定（`AiDiy_key.json`）と `Aタスク要求` レコードが3種を持つ。要求側の指定が優先で、
  空なら共通設定のフェーズ別値を使う（`task_sub/sub_init.py` の `入力モデル()`、
  `task_sub/sub_end.py` の `要求モデル()`）。
- `Aタスク明細` は各ステップの実行だけなので `TASK_AI_MODEL_do` 1列。本登録時に要求の `_do` が入る。
- フェーズが1つしかない処理も、キー名でどのフェーズかを明示する。
  会話要求と雑談は `TASK_AI_MODEL_plan`、自己作業は `TASK_AI_MODEL_do`、経験まとめは依頼の `*_AI_MODEL_plan`。
- `Aチーム目標` と `Aチーム依頼` は TEAM・TASK それぞれ3列（計6列）を持ち、
  目標 → 依頼 → Aタスク要求 と3種のまま引き渡す（`sub_SPDCA__common.AI設定を決める()` → `タスク投入()`）。
- TEAM 側3種は作業ループの段（S・P=plan / D=do / C・A=check）、TASK 側3種は投入した Aタスクの
  内部フェーズ（準備 / 各ステップ / 最終確認）に対応する。
- Aタスクを作らず code_agents を直に呼ぶ段（S・P・C・A）は `段のモデル()` が区分に対応する
  フェーズを選び、`auto` なら共通設定のフェーズ別値へ落とす。
- 現行実装ではフェーズ別キーを使う。`conf_json` は旧版の単一キー（`TASK_AI_MODEL` / `TEAM_AI_MODEL`）を
  フェーズ別キーへ自動移行しない。旧キーは未知キーとして JSON に残り得るが、フェーズ別キーの不足分は
  既定値で補完される。旧値を引き継ぐ場合は plan / do / check それぞれへ明示的に設定する。
- API（`/task/タスク要求/AI登録`・`/更新登録`、`/team/目標/保存`・`/team/依頼/登録`・`/変更`）は
  フェーズ別キーだけを受け付ける。未指定の項目は更新最終レコード → 規定値の順で補完される。
- MCP の `aidiy_task_agents.submit` は `ai_model_plan` / `_do` / `_check`、
  `aidiy_team_agents.submit` は `team_ai_model_plan` / `task_ai_model_plan` などでフェーズ別に指定する。

## 設定変更手順

### JSON を直接編集する場合

`_config/AiDiy_key.json` を編集し、Chat / Live / Code 6枠のキーを揃える。

```json
{
  "CHAT_AI_NAME": "gemini_chat",
  "LIVE_AI_NAME": "gemini_live",
  "CODE_PERMISSIONS": "auto",
  "CODE_AI1_NAME": "codex_cli",
  "CODE_AI1_MODEL": "auto",
  "CODE_AI2_NAME": "claude_sdk",
  "CODE_AI2_MODEL": "auto",
  "CODE_AI3_NAME": "copilot_cli",
  "CODE_AI3_MODEL": "auto",
  "CODE_AI4_NAME": "antigravity_cli",
  "CODE_AI4_MODEL": "auto",
  "CODE_AI5_NAME": "opencode_cli",
  "CODE_AI5_MODEL": "auto",
  "CODE_AI6_NAME": "aidiy_hermes",
  "CODE_AI6_MODEL": "auto",
  "TASK_AI_NAME": "codex_cli",
  "TASK_AI_MODEL_plan": "auto",
  "TASK_AI_MODEL_do": "auto",
  "TASK_AI_MODEL_check": "auto",
  "TEAM_AI_NAME": "codex_cli",
  "TEAM_AI_MODEL_plan": "auto",
  "TEAM_AI_MODEL_do": "auto",
  "TEAM_AI_MODEL_check": "auto"
}
```

変更後は `backend_server/temp/reboot_core.txt` を作成するか、core server を再起動する。

### 設定 UI から変更する場合

現行実装では `POST /core/AIコア/モデル情報/設定` に `セッションID` と `モデル設定` を送る。セッション内の設定更新、JSON 保存、サーバー再起動は次の指定で分かれる。

- `save: true`: `AiDiy_key.json` へ保存する。再起動要求がなければサーバーは再起動しない。
- `再起動要求`: `reboot_core` / `reboot_apps` / `reboot_tools` / `reboot_local` / `reboot_task` / `reboot_team` の指定先だけに再起動を要求する。Task / Team は同じ統合プロセスが対象。
- `リセット: true`: 設定を既定値へ戻して保存する。UI のリセット操作では全バックエンドの再起動も要求する。

Web / Avatar とも「保存(json書換)」は `save: true`、再起動要求なし。「設定/再起動」は apps / tools の再起動を要求するが、現行実装では Web は `save: true`、Avatar は `save: false` で送る。Avatar で次回起動にも設定を残す場合は「保存(json書換)」を使う。

Electron では settings 専用ウィンドウ、Web では同じコンポーネントのモーダル表示を使う。`AI設定再起動.vue` に `window.desktopApi` 前提の処理を直接入れない。

## available_models の流れ

1. frontend が `POST /core/AIコア/モデル情報/取得` を呼ぶ
2. backend が現在設定と `available_models` を返す
3. 設定 UI が `chat_models` / `live_models` / `code_models` から選択肢を作る
4. 設定時に `POST /core/AIコア/モデル情報/設定` へ送り、保存する場合は `save: true` を指定する
5. モデル情報の再取得で設定を確認し、再起動を要求した場合は再接続後も確認する

新しい AI 種別を追加する場合は、backend が返す `available_models` のキー、frontend の `CHAT_MODEL_KEYS` / `LIVE_MODEL_KEYS` / `LIVE_VOICE_KEYS` / `CODE_MODEL_KEYS`、`conf_json.DEFAULT_CONFIG` を合わせる。

`openai_chat` は `AiDiy_key.json` の `openai_key_id` を使い、`openai_oauth` は Codex CLI と `command_hermes` が共用する OAuth 認証ストアを使う。旧設定値 `openai_oauth_chat` は読込時に `openai_oauth` へ自動移行する。Codex CLI でログイン済みなら再認証は不要。初回利用前に `command_hermes` からログインする場合は
`.venv/Scripts/python.exe hermes_main.py auth add openai-codex` （Linux / macOS は `.venv/bin/python`）を実行する。OAuth token は
`AiDiy_key.json` には保存せず、`${CODEX_HOME:-~/.codex}/auth.json` から解決する。Hermes でログインや更新をした場合も同じファイルへ書き込む。
`aidiy_hermes` を起動して provider `openai_oauth` を選択する方法でも、同じ OAuth 認証を開始できる。

OpenAI Chat のモデル候補は API / OAuth で共通。API で取得した一覧があれば両方に使い、空の場合のみ OAuth の一覧を取得する。選択モデルも `CHAT_OPENAI_MODEL` を共用する。旧 `CHAT_OPENAI_OAUTH_MODEL` は設定読込時に移行し、現在の `CHAT_AI_NAME` が `openai_oauth` なら旧 OAuth 側の選択値を優先する。

`backend_local` が未起動の場合、`/core/AIコア/モデル情報/取得` は `local_chat` を chat / code モデル候補から除外する。`_start.py` の backend_local 起動デフォルトは No のため、local LLM を使うときだけ明示起動する。

Code CLI の権限モードは `CODE_PERMISSIONS` で管理する。設定 UI では `auto` / `full` / `none` を選択でき、保存時は `AiDiy_key.json` へ書き込まれる。`none` の場合、Claude / Antigravity / Copilot / Grok 系の bypass、yolo、自動全ツール許可オプションは付与しない（`grok_cli` は `--always-approve` を省略する）。ただし `codex_cli` はサンドボックス無視を常に有効にするため、`--dangerously-bypass-approvals-and-sandbox` を付与する。CLI 実行時の具体的な反映処理は `AIコード_cli.py` / `AIコード_claude.py` / `command_hermes` 側の実装に合わせて確認する。

## Ollama Chat の local / Cloud 切替

対象:
- `backend_server/AIコア/AIチャット_ollama.py`
- `backend_server/conf/conf_model.py`
- `backend_server/AIコア/AIチャット.py`

判断基準:
- `ollama_key_id` が `<` で始まる場合は local Ollama を使う
- 有効なキーがある場合は Ollama Cloud `https://ollama.com/v1` を使う
- local は `ollama_host + "/v1"`、既定は `http://127.0.0.1:11434/v1`
- Cloud 直叩き時はモデル名から `:cloud` と入力揺れの `:clude` を外して API に渡す

注意:
- `AiDiy_key.json` は正マスタ。読込時の正規化だけを理由に保存し直さない
- `ollama_chat` は local 実行が正常系なので、キーがプレースホルダーでも welcome 事前チェックで無効扱いにしない
- Cloud のモデル一覧は日付表示形式を他の chat model と揃える

## 注意点

- `frontend_avatar/src/api/config.ts` の `defaultModelSettings()` は backend 取得前のフォールバック。`conf_json.py` のデフォルトとずれると初期表示が混乱する
- `CODE_AI<N>_MODEL` はスロットごとの現在モデル、`CODE_CODEX_CLI_MODEL` のようなキーは CLI 種別ごとのデフォルト。混同しない
- `claude_cli` のモデル候補は `scripts/cli_bat/_claude-code.bat` の `MODEL` 値と `auto` に揃える。`_config/AiDiy_code_claude_cli.json` が古い場合は `conf_model.py` の初期化時に候補を同期する
- `copilot_cli` のモデル候補は `backend_server/conf/conf_model.py` で定義し、`scripts/cli_bat/_copilot_cli.bat` の `MODEL` 値と一致させる。`_config/AiDiy_code_copilot_cli.json` が古い場合は候補を同期する
- `codex_cli` のモデル候補は `scripts/cli_bat/_codex_cli.bat` の `MODEL` 値と `auto` に揃える。`_config/AiDiy_code_codex_cli.json` が古い場合は `conf_model.py` の初期化時に候補を同期する
- `grok_cli` のモデル候補も `scripts/cli_bat/_grok_cli.bat` の `MODEL` 値と `auto` に揃える。`_config/AiDiy_code_grok_cli.json` が古い場合は同様に同期する
- `aidiy_hermes` の設定画面候補は `scripts/cli_bat/_hermes_cli.bat` の OpenAI OAuth モデルと `auto` に揃える。候補は `conf_model.py` の `_get_aidiy_hermes_models()` で定義する。候補値は `openai_oauth/<モデルID>` とし、専用の `AiDiy_code_*.json` は使わない
- 設定変更は既存 WebSocket セッションへ即時完全反映される前提にしない。再起動後の再接続で確認する
- Code AI は現行6枠。枠数確認は `backend_server/core_router/AIコア.py` と frontend の `PanelKey` を見る

## 確認方法

- `POST http://127.0.0.1:8091/core/AIコア/モデル情報/取得` に `{"セッションID": "対象セッションID"}` を送り、現在設定と利用可能モデル一覧を確認する。接続前は `{}` を送り、共通設定の既定値と候補を取得できる
- 設定 UI で Chat / Live / Code1〜Code6 / Task / Team の選択肢が出ることを確認する（Task / Team は plan / do / check の3行）
- 「保存(json書換)」で `AiDiy_key.json` が更新され、サーバーが再起動しないことを確認する。再起動を要求した場合は、指定したサーバーの再起動と再接続を確認する
