# AIモデル設定変更手順

> 文書: `backend_server,frontend_avatar,frontend_web,AIモデル設定変更手順.md` | 実装: `_config/AiDiy_key.json`, `backend_server/conf/conf_json.py`, `frontend_web/src/components/AiDiy/dialog/AI設定再起動.vue`

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
| `CHAT_AI_NAME` | `_chat` | `gemini_chat`, `openrt_chat`, `freeai_chat`, `ollama_chat` |
| `LIVE_AI_NAME` | `_live` | `gemini_live`, `openai_live` |
| `CODE_AI1_NAME`〜`CODE_AI6_NAME` | 原則 `_sdk` または `_cli`、例外 `aidiy_hermes` | `claude_sdk`, `claude_cli`, `copilot_cli`, `codex_cli`, `antigravity_cli`, `grok_cli`, `opencode_cli`, `aidiy_hermes` |
| `TASK_AI_NAME` / `TEAM_AI_NAME` | Code AI と同じ候補を使用 | `claude_cli`, `codex_cli`, `aidiy_hermes` |

判定は完全一致を前提にする。`startswith()` などの前方一致へ変えない。

## TASK / TEAM モデルの3種指定

モデルだけは AI 名1つに対して plan / do / check の3種を持つ。

| キー | 使う処理 |
|------|---------|
| `TASK_AI_MODEL_plan` | Aタスクの準備＝明細分解（`task_sub/sub_init.py`）、Aチーム要員選定・経験まとめ、雑談発言 |
| `TASK_AI_MODEL_do` | Aタスクの各ステップ実行（`task_sub/sub_proc.py`）、自己作業、要求・明細・依頼レコードの既定値 |
| `TASK_AI_MODEL_check` | 終了時の最終確認（`task_sub/sub_terminate.py`） |
| `TEAM_AI_MODEL_plan` / `_do` / `_check` | 作業ループの段（S・P=plan / D=do / C・A=check、`team_sub/sub_SPDCA__common.py` の `段フェーズ`） |

判断基準:

- 共通設定（`AiDiy_key.json`）と `Aタスク要求` レコードが3種を持つ。要求側の指定が優先で、
  空なら共通設定のフェーズ別値を使う（`task_sub/sub_init.py` の `入力モデル()`、
  `task_sub/sub_terminate.py` の `要求モデル()`）。
- `Aタスク明細` は各ステップの実行だけなので `TASK_AI_MODEL_do` 1列。本登録時に要求の `_do` が入る。
- フェーズが1つしかない処理も、キー名でどのフェーズかを明示する。
  会話要求と雑談は `TASK_AI_MODEL_plan`、自己作業は `TASK_AI_MODEL_do`、経験まとめは依頼の `*_AI_MODEL_plan`。
- `Aチーム目標` と `Aチーム依頼` は TEAM・TASK それぞれ3列（計6列）を持ち、
  目標 → 依頼 → Aタスク要求 と3種のまま引き渡す（`sub_SPDCA__common.AI設定を決める()` → `タスク投入()`）。
- TEAM 側3種は作業ループの段（S・P=plan / D=do / C・A=check）、TASK 側3種は投入した Aタスクの
  内部フェーズ（準備 / 各ステップ / 最終確認）に対応する。
- Aタスクを作らず code_agents を直に呼ぶ段（S・P・C・A）は `段のモデル()` が区分に対応する
  フェーズを選び、`auto` なら共通設定のフェーズ別値へ落とす。
- 旧版の単一キー（`TASK_AI_MODEL` / `TEAM_AI_MODEL`）は廃止済み。設定・DB列・API・MCP のいずれにも
  存在しないので、新しいキーだけを使う。
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
- 設定変更は既存 WebSocket セッションへ即時完全反映される前提にしない。再起動後の再接続で確認する
- Code AI は現行6枠。枠数確認は `backend_server/core_router/AIコア.py` と frontend の `PanelKey` を見る

## 確認方法

- `GET http://127.0.0.1:8091/core/AIコア/モデル情報/取得` で現在設定と利用可能モデル一覧を確認する（要認証）
- 設定 UI で Chat / Live / Code1〜Code6 / Task / Team の選択肢が出ることを確認する（Task / Team は plan / do / check の3行）
- 保存後に `AiDiy_key.json` が更新され、core server が再起動することを確認する
