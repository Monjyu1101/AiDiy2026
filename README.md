# AiDiy - README

## 本書の目的

この README は、**AiDiy の初回セットアップ、起動、停止、クリーンアップ** を素早く確認するための入口です。

詳細設計や実装ルールは次を参照してください。

- [AGENTS.md](./AGENTS.md)
- [backend_server/AGENTS.md](./backend_server/AGENTS.md)
- [frontend_web/AGENTS.md](./frontend_web/AGENTS.md)
- [frontend_avatar/AGENTS.md](./frontend_avatar/AGENTS.md)
- [docs/](./docs/)

---

## プロジェクト概要

**AiDiy** は、日本語識別子を前提にしたフルスタック業務システムのテンプレートです。

- バックエンド: FastAPI + SQLAlchemy + SQLite
- フロントエンド Web: Vue 3 + Vite + TypeScript + Pinia
- フロントエンド Avatar: Vue 3 + Vite + TypeScript + Electron
- バックエンドはデュアルサーバー構成
  - `core_main.py` : `8091`
  - `apps_main.py` : `8092`
- Web フロントは `8090`
- Avatar フロントは `8099`

### 主な特徴

- **マルチ Code CLI 対応** — `claude_sdk` / `claude_cli` / `copilot_cli` / `codex_cli` / `gemini_cli` / `hermes_cli` を切り替えて同時並走
- **自己改善機構** — コードエージェントが修正完了後に `.aidiy/` へ知見を自動整理し、使うほど修正精度が上がる
- **日本語ネイティブ** — テーブル名・API・コンポーネント名まで日本語で統一
- **AI 音声対話コーディング** — Avatar に話しかけながらコードを書き進められる

---

## 0. 事前準備

### 必要なソフトウェア

| ソフトウェア | 目安 |
|---|---|
| Python | 3.13 系 |
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
2. `backend_server` の `uv sync`
3. `frontend_web` の `npm install`
4. `frontend_avatar` の `npm install`
5. 必要に応じて Electron バイナリの補完

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

- バックエンド(core, apps) を起動するか
- フロントエンド(Web) を起動するか
- フロントエンド(Avatar) を起動するか

その後、選択したサービスを順に起動し、必要なポートの既存プロセスも自動で整理します。

### 個別起動

```bash
# バックエンド Core
cd backend_server
.venv/Scripts/python.exe -m uvicorn core_main:app --reload --host 0.0.0.0 --port 8091

# バックエンド Apps
cd backend_server
.venv/Scripts/python.exe -m uvicorn apps_main:app --reload --host 0.0.0.0 --port 8092

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
| Apps API Docs | http://localhost:8092/docs |
| Avatar Web モード | http://localhost:8099 |
| Avatar Electron モード | `npm run dev` で Electron アプリ起動 |

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
netstat -ano | findstr :8092
netstat -ano | findstr :8099
taskkill /PID <pid> /F
```

補足:

- `_start.py` を再実行すると、対象ポートの既存プロセスは起動前に自動整理されます。
- バックエンドのみ再読込したい場合は `backend_server/temp/reboot_core.txt` または `backend_server/temp/reboot_apps.txt` を作成します。

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

クリーンアップ後は再度 `python _setup.py` が必要です。

---

## 5. よくある注意点

- `_start.py` は **CLI 引数で backend/web/avatar を切り替える方式ではありません**。起動時の対話で選びます。
- `_start.py` 起動時のバックエンドは `uvicorn --reload` なしです。コード変更を即反映したい場合は個別起動か reboot 機構を使います。
- Web フロントの AI 画面ルートは **`/AiDiy`** です。
- Avatar は Electron と Web の両モードがあります。Web モードでは認証情報を `sessionStorage` に保持します。
- DB ファイルは通常 `backend_server/_data/AiDiy/database.db` にあります。

---

## 6. 次に読むもの

1. [AGENTS.md](./AGENTS.md)
2. [backend_server/AGENTS.md](./backend_server/AGENTS.md)
3. [frontend_web/AGENTS.md](./frontend_web/AGENTS.md)
4. [frontend_avatar/AGENTS.md](./frontend_avatar/AGENTS.md)
5. [docs/開発ガイド/README.md](./docs/開発ガイド/README.md)
