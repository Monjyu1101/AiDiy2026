# AiDiy - README

## 本書の目的

この README は、**AiDiy の初回セットアップ、起動、停止、クリーンアップ** を素早く確認するための入口です。

詳細設計や実装ルールは次を参照してください。

- [AGENTS.md](./AGENTS.md)
- [backend_server/AGENTS.md](./backend_server/AGENTS.md)
- [command_hermes/AGENTS.md](./command_hermes/AGENTS.md)
- [backend_tools/AGENTS.md](./backend_tools/AGENTS.md)
- [backend_local/AGENTS.md](./backend_local/AGENTS.md)
- [backend_task/AGENTS.md](./backend_task/AGENTS.md)
- [frontend_web/AGENTS.md](./frontend_web/AGENTS.md)
- [frontend_avatar/AGENTS.md](./frontend_avatar/AGENTS.md)
- [docs/](./docs/)

---

## プロジェクト概要

**AiDiy** は、日本語識別子を前提にしたフルスタック業務システムのテンプレートです。

- バックエンド: FastAPI + SQLAlchemy + SQLite
- Command Hermes: `command_hermes` / `aidiy_hermes`（コード支援用 CLI 基盤、常駐サーバーではない）
- バックエンド MCP: FastAPI (SSE / Streamable HTTP / stdio) + Python MCP SDK（**18 サーバーを同居**: Chrome DevTools / Desktop Capture / SQLite / PostgreSQL / Logs / Code Check / Backup / Image Generation / Movie Generation / Speech-to-Text / Text-to-Speech / OBS Studio Control / FFmpeg Control / Notification Sounds / Code Agents / Chat LLM / Task Agents / Windows Control）
- バックエンド Local: `backend_local`（ポート 8094、OpenAI 互換の Gemma ローカル推論サーバー）
- バックエンド Task: `backend_task`（ポート 8093、AIタスク実行 + 定期タスク FastAPI）
- フロントエンド Web: Vue 3 + Vite + TypeScript + Pinia
- フロントエンド Avatar: Vue 3 + Vite + TypeScript + Electron
- 常駐バックエンドは **5 サーバー構成**
  - `core_main.py` : `8091`
  - `apps_main.py` : `9098`
  - `tools_main.py` : `8095`
  - `local_main.py` : `8094`（`_start.py` のデフォルトは起動しない）
  - `task_main.py` : `8093`
- 補助 CLI として `command_hermes` を統合
  - `aidiy_hermes` : on-demand 実行のコードエージェント CLI
- Web フロントは `8090`
- Avatar フロントは `8092`

### 主な特徴

- **マルチ Code CLI 対応** — `claude_sdk` / `claude_cli` / `copilot_cli` / `codex_cli` / `antigravity_cli` / `opencode_cli` / `aidiy_hermes` を切り替えて、`code1`〜`code6` の6コードパネルで同時並走
- **AIタスク自動実行** — 要求を登録すると AI が明細タスクへ分解し、`backend_task` が Code CLI で実行。カンバン方式でも垂直の流れ作業だけでもなく、先行SEQ（複数指定可）で水平の並行分岐を含む**自由なタスクフロー**を定義でき、**クリティカルパス**基準のフロー図で可視化・実行（Web / Avatar の AIタスク画面から操作）
- **自己改善機構** — コードエージェントが修正完了後に `.aidiy/knowledge/` へ知見を自動整理し、使うほど修正精度が上がる
- **日本語ネイティブ** — テーブル名・API・コンポーネント名まで日本語で統一
- **AI 音声対話コーディング** — Avatar に話しかけながらコードを書き進められる

---

## 0. 事前準備

### 必要なソフトウェア

| ソフトウェア | 目安 |
|---|---|
| Python | 3.13 以上 |
| Node.js | 22 系 |
| Git | 最新版推奨 |
| uv | Python パッケージ管理に使用 |

### リポジトリ取得

```bash
git clone https://github.com/Monjyu1101/AiDiy2026
cd AiDiy2026
```

---

## 1. セットアップ

初回は次を実行します。

```bash
python _setup.py
```

`_setup.py` は対話形式で以下を実施します。

1. 共通の Python / npm ツール確認
2. `backend_local` の `uv sync --upgrade`
3. `backend_tools` の `uv sync --upgrade`、必要に応じて MCP 設定ファイル書き込み（Claude / Gemini 向け）
4. `backend_server` の `uv sync --upgrade`
5. `backend_task` の `uv sync --upgrade`
6. `frontend_web` の `npm install`
7. `frontend_avatar` の `npm install`、必要に応じて Electron バイナリの補完
8. `command_hermes` の `.venv` 作成 / `uv sync --upgrade` / `aidiy_hermes` 登録試行

補足:

- DB は SQLite です。
- Alembic は使いません。
- PostgreSQL 関連処理は現在の通常運用では使いません。
- API キー設定ファイル `backend_server/_config/AiDiy_key.json` は初回起動時にひな形が生成されます。

---

## 2. 起動

### 推奨

```bash
python _start.py
```

`_start.py` は**対話形式**です。起動時に以下を確認します。

- バックエンド(local) を起動するか（デフォルト No）
- tools を起動するか
- バックエンド(core, apps) を起動するか
- バックエンド(task) を起動するか
- フロントエンド(Web) を起動するか
- フロントエンド(Avatar) を起動するか

その後、選択したサービスを順に起動し、必要なポートの既存プロセスも自動で整理します。

`command_hermes` は **常駐サーバーではないため `_start.py` の起動対象外** です。セットアップ後は、AIコードパネルから `aidiy_hermes` として呼び出すか、必要時に手動で起動します。

### 個別起動

```bash
# バックエンド Local（OpenAI 互換 Gemma、必要時のみ）
cd backend_local
.venv/Scripts/python.exe -m uvicorn local_main:app --reload --host 0.0.0.0 --port 8094

# バックエンド MCP
cd backend_tools
.venv/Scripts/python.exe -m uvicorn tools_main:app --reload --host 0.0.0.0 --port 8095

# バックエンド Core
cd backend_server
.venv/Scripts/python.exe -m uvicorn core_main:app --reload --host 0.0.0.0 --port 8091

# バックエンド Apps
cd backend_server
.venv/Scripts/python.exe -m uvicorn apps_main:app --reload --host 0.0.0.0 --port 9098

# バックエンド Task
cd backend_task
.venv/Scripts/python.exe -m uvicorn task_main:app --reload --host 0.0.0.0 --port 8093

# Command Hermes（対話 CLI）
cd command_hermes
.venv/Scripts/python.exe cli_main.py

# またはグローバル登録済みなら
aidiy_hermes

# フロントエンド Web
cd frontend_web
npm run dev

# フロントエンド Avatar
cd frontend_avatar
npm run dev
```

### 起動後の URL

| サービス | URL |
|---|---|
| Web フロント | http://localhost:8090 |
| Core API Docs | http://localhost:8091/docs |
| Apps API Docs | http://localhost:9098/docs |
| Backend Local Docs | http://localhost:8094/docs |
| Backend Task Docs | http://localhost:8093/docs |
| Backend MCP 一覧 | http://localhost:8095/ |
| Backend MCP ツール一覧 | http://localhost:8095/{mcp_name}/list |
| Backend MCP SSE 接続 | http://localhost:8095/{mcp_name}/sse （例: `aidiy_chrome_devtools`） |
| Avatar Web モード | http://localhost:8092 |
| Avatar Electron モード | `npm run dev` で Electron アプリ起動 |

MCP は 18 サーバー（`aidiy_chrome_devtools` / `aidiy_desktop_capture` / `aidiy_sqlite` / `aidiy_postgres` / `aidiy_logs` / `aidiy_code_check` / `aidiy_backup` / `aidiy_image_generation` / `aidiy_movie_generation` / `aidiy_speech_to_text` / `aidiy_text_to_speech` / `aidiy_obs_studio_control` / `aidiy_ffmpeg_control` / `aidiy_notification_sounds` / `aidiy_code_agents` / `aidiy_chat_llms` / `aidiy_task_agents` / `aidiy_windows_control`）です。詳細は [backend_tools/AGENTS.md](./backend_tools/AGENTS.md) を参照してください。
`aidiy_chrome_devtools` は `session` パラメータ（省略時 `default`）で複数の Chrome を並行セッション管理でき、システムテストの自動実行など並行実行が可能です（使用後は `close_session` で破棄）。

### 初期ログイン

- `admin / ********`
- `leader / secret`
- `user / user`
- `guest / guest`
- `other / other`

注意:

- 初期データ投入は **admin が未存在のときだけ** 実行されます。
- 既存 DB がある場合、初期ユーザー情報は自動更新されません。

---

## 3. 停止

### `_start.py` で起動した場合

ターミナルで `Ctrl+C` を押してください。

### 手動で止めたい場合

`_stop.py` は現在ありません。必要ならポート使用プロセスを手動停止してください。

```powershell
netstat -ano | findstr :8090
netstat -ano | findstr :8091
netstat -ano | findstr :9098
netstat -ano | findstr :8093
netstat -ano | findstr :8094
netstat -ano | findstr :8095
netstat -ano | findstr :8092
taskkill /PID <pid> /F
```

補足:

- `_start.py` を再実行すると、対象ポートの既存プロセスは起動前に自動整理されます。
- バックエンドのみ再読込したい場合は `backend_server/temp/reboot_core.txt` または `backend_server/temp/reboot_apps.txt` を作成します。
- `command_hermes` はポート待受しない CLI のため、必要なら `Ctrl+C` でその場のプロセスだけ停止します。

---

## 4. クリーンアップ

環境を渡し直す、または開発環境を整理したい場合は次を実行します。

```bash
python _cleanup.py
```

主に次を対話的に削除します。

- `.venv`
- `node_modules`
- `dist`
- `__pycache__`
- `temp`
- `logs`
- 必要に応じて SQLite DB

`_cleanup.py` は `command_hermes` についても `.venv` / `venv` と Python キャッシュの削除対象を確認します。

クリーンアップ後は再度 `python _setup.py` が必要です。

---

## 5. よくある注意点

- `_start.py` は **CLI 引数で backend/web/avatar を切り替える方式ではありません**。起動時の対話で選びます。
- Claude 系のブラウザ自動操作を使う場合は `backend_tools` も起動してください。
- `_start.py` 起動時のバックエンドは `uvicorn --reload` なしです。コード変更を即反映したい場合は個別起動か reboot 機構を使います。
- `command_hermes` は `_start.py` では起動しません。`python _setup.py` で導入し、`aidiy_hermes` または `command_hermes\cli_main.py` を必要時に実行します。
- Web フロントの AI 画面ルートは **`/AiDiy`** です。
- Avatar は Electron と Web の両モードがあります。Web モードでは認証情報を `sessionStorage` に保持します。
- DB ファイルは通常 `backend_server/_data/AiDiy/database.db` にあります。

---

## 6. 次に読むもの

1. [AGENTS.md](./AGENTS.md)
2. [backend_server/AGENTS.md](./backend_server/AGENTS.md)
3. [command_hermes/AGENTS.md](./command_hermes/AGENTS.md)
4. [backend_tools/AGENTS.md](./backend_tools/AGENTS.md)
5. [backend_local/AGENTS.md](./backend_local/AGENTS.md)
6. [backend_task/AGENTS.md](./backend_task/AGENTS.md)
7. [frontend_web/AGENTS.md](./frontend_web/AGENTS.md)
8. [frontend_avatar/AGENTS.md](./frontend_avatar/AGENTS.md)
9. [docs/開発ガイド/README.md](./docs/開発ガイド/README.md)
