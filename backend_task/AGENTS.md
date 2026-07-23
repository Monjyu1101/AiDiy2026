# backend_task 実装概要

## 本書の目的

このファイルは `backend_task` の構成、提供 API、実装入口を示す概要ドキュメントです。
AI エージェントは、本書に個別手順や一時的な作業メモを追記しないでください。
コアシステム機能調整は `../.aidiy/knowledge/_index.md` を入口にします。

## 概要

`backend_task` はポート `8093` 上で動作する **AIタスク実行 + 定期タスク** の FastAPI 常駐サーバーです。
`backend_server/apps_main.py` 起動後にルート `_start.py` から起動されます。

- Backend: FastAPI + uvicorn（Python 3.13+、uv 管理）
- 起動: `uvicorn task_main:app --host 0.0.0.0 --port 8093`
- DB: `backend_server/_data/AiDiy/database.db` を共有（`Aタスク要求` / `Aタスク明細` / `Aタスク実行条件` テーブル）
- 新規タスクID: `TASK.mmdd.hhmmss`
- 定期処理: 60 秒間隔のハートビートログ + 5 秒間隔の AIタスク監視ループ（明細起動） + 10 秒間隔の実行開始条件監視ループ（発火確認は hh:mm 変化時＝毎分）
- 再起動: `backend_task/temp/reboot_task.txt` 検知で終了し、ルート `_start.py` 起動中なら自動再起動

## AIタスク実行の流れ

1. フロントエンド（frontend_web `/AIタスク` 画面 / frontend_avatar タスクウィンドウ）が `/task/タスク要求/AI登録` で要求を仮登録（準備開始）する。
2. 監視ループ（5秒間隔）が`準備開始`かつPID未設定の仮登録を検出し、`準備中`へ更新してから`sub_init.py`サブプロセスで要求をAI分解し、`Aタスク明細`を生成する。
3. 先行 SEQ が完了した未実行明細を `sub_proc.py` で 1 ステップずつ実行する（Code CLI = `TASK_AI_NAME` / `TASK_AI_MODEL`、開始 / 終了明細は `sub_start.py` / `sub_terminate.py`）。
4. code agent 実行中は原則直列。軽量明細のみ並行起動を許可。実行回数上限（3 回）超過で失敗にする。
5. 実行開始条件（`Aタスク実行条件`: 時間指定 / 間隔実行 / 定時実行 / フォルダ変化）付きのタスクは本登録後 `準備完了` で待ち、監視ループが毎分（hh:mm 変化時）次回実行日時と条件を確認して、成立時に明細 → 要求の順で `待機` に戻して実行する。対象は要求が `準備完了` / `完了` かつ明細が全件待機または全件完了のタスクのみ（実行途中は開始しない）。次回実行日時は発火可能状態（実行有効 かつ 要求が `準備完了` / `完了`）の間だけ保持し、それ以外は空にする（実行条件の編集・実行有効切替・起動時も同じルールで再計算 = `tasks_watcher.実行条件再計算`）。即時（条件なし）は本登録で直接 `待機` になる。

タスクフローの特徴:

- カンバン方式ではなく、`先行SEQ`（カンマ区切りで複数指定可）による依存定義の DAG。
- 垂直の直列フローだけでなく、水平の並行分岐を自由に組める。
- 実行可能判定は「先行 SEQ が全て完了」（`tasks_db.実行可能明細一覧`）で、依存が満たされた明細から実行する。
- フロー図（frontend の `AIタスク_フロー図.vue`）は最長経路 = クリティカルパス基準で列を配置して進行を可視化する。

`TASK_AI_NAME` の有効値は Code AI と同じ（`claude_sdk` / `claude_cli` / `copilot_cli` / `codex_cli` / `antigravity_cli` / `opencode_cli` / `aidiy_hermes`）です。

## 提供 API

すべて `/task` 配下、CRUD 系は POST 統一・`{"status", "message", "data"}` 形式です。

| エンドポイント | 役割 |
|----------------|------|
| `GET /`、`GET /health` | 稼働状況、ヘルスチェック |
| `POST /task/タスク要求/一覧` / `最大更新日時` | タスク要求の一覧、ポーリング用最大更新日時 |
| `POST /task/タスク要求/AI登録` / `登録` / `更新登録` / `本登録` | 要求の仮登録（準備開始）、更新（再分解）、AI 分解結果の確定。AI登録の`タスクID`は省略時に自動採番 |
| `POST /task/タスク要求/有効切替` / `AI失敗` | 有効フラグ切替、AI 分解失敗の記録 |
| `POST /task/タスク明細/一覧` / `最大更新日時` | タスク明細の一覧、ポーリング用最大更新日時 |
| `POST /task/タスク明細/更新登録` / `有効切替` / `完了` / `失敗` / `全消去` | 明細の編集、有効切替、実行結果の記録 |
| `POST /task/タスク実行条件/取得` | 要求に紐づく実行開始条件の取得（登録は AI登録 / 更新登録 に同梱） |
| `POST /task/プロジェクト選択肢` | 要求編集ダイアログのプロジェクト候補 |

## ファイル構成

| パス | 役割 |
|------|------|
| `task_main.py` | 軽量な FastAPI エントリポイント。ログ初期化と app 生成だけを担当 |
| `task_proc/app.py` | FastAPI アプリ生成、ルーター登録、lifespan / reboot watcher の接続 |
| `task_proc/routes.py` | `GET /`、`GET /health` の API ルーター |
| `task_proc/runtime.py` | ハートビート、`reboot_task.txt` 監視、AIタスク監視ループの起動 |
| `task_proc/tasks_api.py` | `/task/タスク要求/*`、`/task/タスク明細/*` の API ルーター |
| `task_proc/tasks_db.py` | `Aタスク要求` / `Aタスク明細` / `Aタスク実行条件` テーブルの sqlite3 直接アクセス |
| `task_proc/tasks_watcher.py` | 5 秒間隔の監視ループ。sub_* サブプロセスの起動と状態遷移 |
| `sub_init.py` | 要求を AI 分解して明細を生成するサブプロセス |
| `sub_start.py` / `sub_proc.py` / `sub_terminate.py` | 開始明細 / 1 ステップ実行 / 終了明細のサブプロセス |
| `_start.py` | 単体起動、およびルート `_start.py` からの起動委譲先 |
| `_setup.py` | `uv sync --upgrade` による依存関係セットアップ |
| `_cleanup.py` | `.venv` / `temp` / Python キャッシュの削除 |
| `pyproject.toml` | uv 依存定義 |

## フロントエンドからの利用

- frontend_web / frontend_avatar とも Vite proxy `/task/*` → `http://127.0.0.1:8093` 経由で呼び出す（avatar は `taskClient`、Electron 本番は 8093 直結）。
- 画面は frontend_web `src/components/AIタスク/`、frontend_avatar `src/components/AIタスク/`（Electron は task1〜task3 ウィンドウ + taskDialog）。

## セットアップ・起動

```bash
cd backend_task && uv sync --upgrade
cd backend_task && uv run uvicorn task_main:app --reload --host 0.0.0.0 --port 8093
```

ルートから起動する場合は `python _start.py` を使います。
起動順は `backend_server/apps_main.py` の後です。
