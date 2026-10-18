# バックエンドの起動と再起動

> 文書: `backend_server,command_hermes,backend_tools,バックエンド起動.md` | 実装: `_start.py`, `backend_server/temp/reboot_core.txt`, `backend_taskteam/taskteam_main.py`

## このメモを使う場面
- バックエンドのコード変更を反映させる
- core/apps/tools/task・team を起動または再起動する
- ポート残留や import エラーで起動できない原因を切り分ける

## 関連ファイル
- `_start.py` — 対話形式の起動スクリプト
- `backend_server/temp/reboot_core.txt` — core 再起動トリガー
- `backend_server/temp/reboot_apps.txt` — apps 再起動トリガー
- `backend_tools/temp/reboot_tools.txt` — tools 再起動トリガー
- `backend_taskteam/temp/reboot_taskteam.txt` — task・team 統合サーバーの再起動トリガー
- `backend_taskteam/taskteam_main.py` — task・team 統合サーバー本体
- `command_hermes/cli_main.py` — `aidiy_hermes` の実体（常駐サーバーではない）

## 起動方法

```powershell
# 対話形式
python _start.py

# 個別起動（コード変更を --reload で即時反映）
cd backend_server
.\.venv\Scripts\python.exe -m uvicorn core_main:app --reload --host 0.0.0.0 --port 8091
.\.venv\Scripts\python.exe -m uvicorn apps_main:app --reload --host 0.0.0.0 --port 8098

cd ..\backend_tools
.\.venv\Scripts\python.exe -m uvicorn tools_main:app --reload --host 0.0.0.0 --port 8095

cd ..\backend_taskteam
.\.venv\Scripts\python.exe -m uvicorn taskteam_main:app --reload --host 0.0.0.0 --port 8093

cd ..\backend_local
.\.venv\Scripts\python.exe -m uvicorn local_main:app --reload --host 0.0.0.0 --port 8096

# Hermes は on-demand CLI
cd ..\command_hermes
.\.venv\Scripts\python.exe cli_main.py
```

`_start.py` は常駐系だけを起動する。`command_hermes` は `_start.py` の対象外で、必要時に `aidiy_hermes` または `cli_main.py` として実行する。

## `_start.py` の選択肢

| プロンプト | デフォルト | 内容 |
|------------|------------|------|
| `バックエンド(local) 起動しますか?` | No | port 8096。未起動時は AI設定の `local_chat` 候補から除外 |
| `tools 起動しますか?` | Yes | port 8095 |
| `バックエンド(core,apps) 起動しますか?` | Yes | port 8091 / 8098 |
| `バックエンド(task,team) 起動しますか?` | Yes | port 8093。`/task/*` と `/team/*` を同じプロセスで提供 |
| `フロントエンド(Web) 起動しますか?` | Yes | port 8090 |
| `フロントエンド(Avatar) 起動しますか?` | No | port 8092 |

Enter キーでデフォルト選択。`_start.py` 起動は `--reload` なしのため、コード変更後は reboot ファイルを作るか、個別起動へ切り替える。

## 再起動手順

```powershell
New-Item -ItemType File -Force backend_server/temp/reboot_core.txt
New-Item -ItemType File -Force backend_server/temp/reboot_apps.txt
New-Item -ItemType File -Force backend_tools/temp/reboot_tools.txt
New-Item -ItemType File -Force backend_taskteam/temp/reboot_taskteam.txt
```

各サーバーは `temp/reboot_*.txt` を監視し、検知すると終了する。`_start.py` が子プロセス終了を検知して同じコマンドで再起動する。

## ポート残留の解消

```powershell
netstat -ano | findstr :8091
taskkill /PID <pid> /F
```

`8098`、`8095`、`8093`、`8096` も同じ手順で確認する。

### Windows の出力文字コード

Diag は Python を `-X utf8` で起動するが、`netstat` / `taskkill` の出力は Windows の OEM コードページを使う。この出力を既定の `text=True` だけで読むと、読取スレッドの `UnicodeDecodeError` に続いて `stdout` が `None` になり、PID 解析の `splitlines` でも失敗する。ルートと Local / Tools / Core・Apps / Task・Team / Web / Avatar の起動スクリプトでは、Windows のこの2コマンドだけ `encoding="oem", errors="replace"` を明示する。Python・Node のログや JSON は引き続き UTF-8 とし、macOS / Linux の読み取り方法は変更しない。PowerShell で日本語の実行パスを返す場合は送信側を `[Console]::OutputEncoding` で UTF-8 に揃えて読み取る。

再検証は `python -B -X utf8 scripts/checks/test_start_native_output.py`。CP932 の日本語見出しと不正バイトを含む標準エラーを出す合成プロセスで、本物の subprocess 読取スレッド・PID 抽出・停止失敗時のメッセージ・ポート解放後の再確認を検証する。実際のサービスや PID は停止しない。POSIX では Windows 専用 codec の実行試験をスキップし、既存の lsof 経路と模擬出力による試験を行う。

### Web が「確認中」から進まない場合

Diag は標準入力を停止要求用のパイプとして読み続ける。Web / Avatar / ルートの `get_npm_command()` で `npm --version` の標準入力を継承すると、Windows で確認処理が戻らなくなる場合がある。サーバー本体の起動処理だけでなく、バージョン確認にも `stdin=subprocess.DEVNULL` を指定する。タイムアウト指定だけで対処しない。

再検証は `python -B -X utf8 scripts/checks/test_diag_start.py`。標準入力の EOF を待つ模擬 npm を使い、監視側の制御パイプを開いたまま確認が完了することを別プロセスで検証する。実際の npm / サービスや GUI を使わずに同じ条件を作れる。

## 起動時処理

- `core_main.py` は C系/A系、`apps_main.py` は M/T/V/S系を担当する。
- `apps_main.py` は `database.Base.metadata.create_all(... tables=[...])` で apps 系テーブルだけを作る。新規 Model を追加したら tables 配列にも追加する。
- `startup_event()` は `apps_crud.apply_schema_migrations(db)`、`apps_crud.init_db_data(db)` の順で実行する。
- `backend_taskteam` は `_start.py` では apps 起動後に起動する。単一 lifespan が task の起動・状態監視と team のシミュレーション・起動・状態監視をまとめて開始し、停止時に全タスクをキャンセルする。
- `backend_taskteam/temp/reboot_taskteam.txt` 検知で統合プロセス全体が終了し、`_start.py` 起動中なら自動再起動される。移行互換として同じ `temp` 内の `reboot_task.txt` / `reboot_team.txt` も受け付けるが、新規運用では `reboot_taskteam.txt` を使う。
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
http://127.0.0.1:8091/docs
http://127.0.0.1:8098/docs
http://127.0.0.1:8093/docs
http://127.0.0.1:8095/aidiy_sqlite/sse
```

Backend 変更後の最小確認:

```powershell
cd backend_server
.\.venv\Scripts\python.exe -m py_compile apps_main.py apps_crud\init.py
.\.venv\Scripts\python.exe -c "import apps_main; import core_main"

cd ..\backend_taskteam
.\.venv\Scripts\python.exe -m py_compile taskteam_main.py taskteam_proc\app.py taskteam_proc\runtime.py
.\.venv\Scripts\python.exe -c "import taskteam_main"
```
