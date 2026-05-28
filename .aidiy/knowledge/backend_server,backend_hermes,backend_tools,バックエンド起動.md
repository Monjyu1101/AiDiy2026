# バックエンドの起動と再起動

> 文書: `backend_server,backend_hermes,backend_tools,バックエンド起動.md` | 実装: `_start.py`, `backend_server/temp/reboot_core.txt`

## このメモを使う場面
- バックエンドのコード変更を反映させる
- core/apps/mcp を起動または再起動する
- ポート残留や import エラーで起動できない原因を切り分ける

## 関連ファイル
- `_start.py` — 対話形式の起動スクリプト
- `backend_server/temp/reboot_core.txt` — core 再起動トリガー
- `backend_server/temp/reboot_apps.txt` — apps 再起動トリガー
- `backend_tools/temp/reboot_mcp.txt` — mcp 再起動トリガー
- `backend_hermes/cli_main.py` — `aidiy_hermes` の実体（常駐サーバーではない）

## 起動方法

```powershell
# 対話形式
python _start.py

# 個別起動（コード変更を --reload で即時反映）
cd backend_server
.\.venv\Scripts\python.exe -m uvicorn core_main:app --reload --host 0.0.0.0 --port 8091
.\.venv\Scripts\python.exe -m uvicorn apps_main:app --reload --host 0.0.0.0 --port 8092

cd ..\backend_tools
.\.venv\Scripts\python.exe -m uvicorn tools_main:app --reload --host 0.0.0.0 --port 8095

# Hermes は on-demand CLI
cd ..\backend_hermes
.\.venv\Scripts\python.exe cli_main.py
```

`_start.py` は常駐系だけを起動する。`backend_hermes` は `_start.py` の対象外で、必要時に `aidiy_hermes` または `cli_main.py` として実行する。

## `_start.py` の選択肢

| プロンプト | デフォルト | 内容 |
|------------|------------|------|
| `tools 起動しますか?` | Yes | port 8095 |
| `バックエンド(core,apps) 起動しますか?` | Yes | port 8091 / 8092 |
| `フロントエンド(Web) 起動しますか?` | Yes | port 8090 |
| `フロントエンド(Avatar) 起動しますか?` | No | port 8099 |

Enter キーでデフォルト選択。`_start.py` 起動は `--reload` なしのため、コード変更後は reboot ファイルを作るか、個別起動へ切り替える。

## 再起動手順

```powershell
New-Item -ItemType File -Force backend_server/temp/reboot_core.txt
New-Item -ItemType File -Force backend_server/temp/reboot_apps.txt
New-Item -ItemType File -Force backend_tools/temp/reboot_mcp.txt
```

各サーバーは `temp/reboot_*.txt` を監視し、検知すると終了する。`_start.py` が子プロセス終了を検知して同じコマンドで再起動する。

## ポート残留の解消

```powershell
netstat -ano | findstr :8091
taskkill /PID <pid> /F
```

`8092`、`8095` も同じ手順で確認する。

## 起動時処理

- `core_main.py` は C系/A系、`apps_main.py` は M/T/V/S系を担当する。
- `apps_main.py` は `database.Base.metadata.create_all(... tables=[...])` で apps 系テーブルだけを作る。新規 Model を追加したら tables 配列にも追加する。
- `startup_event()` は `apps_crud.apply_schema_migrations(db)`、`apps_crud.init_db_data(db)` の順で実行する。
- 起動直後はベースラインバックアップのログが混ざることがある。

## import エラーの切り分け

```powershell
cd backend_server

# 構文確認（import は実行しない）
.\.venv\Scripts\python.exe -m py_compile apps_main.py apps_crud\init.py

# import 確認（router/schema/crud まで読み込む）
.\.venv\Scripts\python.exe -c "import apps_main; import core_main"
```

- `py_compile` は構文エラーだけを拾う。
- `ImportError` や `AttributeError` は import 確認で拾う。
- `startup_event()` は import 時に実行されないため、初期データとスキーマ補正は実起動で確認する。
- `apps_models/__init__.py` または `apps_crud/__init__.py` の import 漏れは `AttributeError: module has no attribute` として出やすい。

## 注意点

- スキーマ変更後は既存 DB にも変更を適用する。適用漏れはサーバー起動エラーの原因になる。
- `_stop.py` は存在しない。停止は `Ctrl+C` またはポート解放で行う。
- SQLite Browser / DBeaver が DB を開いたままだと `database is locked` が発生するため、閉じてから起動する。

## 確認方法

```text
http://localhost:8091/docs
http://localhost:8092/docs
http://localhost:8095/aidiy_sqlite/sse
```

Backend 変更後の最小確認:

```powershell
cd backend_server
.\.venv\Scripts\python.exe -m py_compile apps_main.py apps_crud\init.py
.\.venv\Scripts\python.exe -c "import apps_main; import core_main"
```
