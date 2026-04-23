# backend_server 実装要点まとめ

## 本書の目的

このファイルは **backend_server（バックエンドサーバー）の実装詳細** を記載したドキュメントです。
本書は **日本語で分かりやすく記載しています**（全書共通の方針として、追記時もこの方針を維持します）。

**対象読者：** このプロジェクトのバックエンド（FastAPI + SQLAlchemy + SQLite）を理解・修正・拡張する開発者

**このファイルの役割：**
- バックエンドの全体構造とファイル配置の理解
- 実装の特徴とアーキテクチャパターンの把握
- 新規機能追加やデバッグ時の参照ガイド

**関連ドキュメント：**
- **[../CLAUDE.md](../CLAUDE.md)** - Claude Code向けインデックス（プロジェクト全体概要）
- **[../AGENTS.md](../AGENTS.md)** - プロジェクト全体方針（基本方針、開発コマンド、共通問題）
- **[../docs/開発ガイド/11_コーディングルール/](../docs/開発ガイド/11_コーディングルール/_index.html)** - コーディングルール、命名規則、ベストプラクティス
- **[../backend_mcp/AGENTS.md](../backend_mcp/AGENTS.md)** - MCP サーバー実装詳細（Chrome DevTools / Desktop Capture / SQLite / PostgreSQL / Logs / Code Check / Backup Check / Backup Save）
- **[../frontend_web/AGENTS.md](../frontend_web/AGENTS.md)** - フロントエンド Web 実装詳細（Vue 3 + TypeScript）
- **[../frontend_avatar/AGENTS.md](../frontend_avatar/AGENTS.md)** - フロントエンド Avatar 実装詳細（Electron + WebSocket + VRM）

**📚 ドキュメントリソース（docs/フォルダ）：**
プロジェクトの詳細なドキュメントは `docs/開発ガイド/` フォルダにHTML形式で整備されています。
- **[../docs/開発ガイド/03_明日のために！その３_バックエンド開発/](../docs/開発ガイド/03_明日のために！その３_バックエンド開発/_index.html)** - バックエンドAPI実装手順
- **[../docs/開発ガイド/11_コーディングルール/](../docs/開発ガイド/11_コーディングルール/_index.html)** - 命名規則、ベストプラクティス、レビューチェックリスト（**必読**）

**フロントエンドの情報は別ドキュメント：**
このドキュメントはバックエンドに特化しています。
- MCP サーバー（Chrome DevTools / Desktop Capture / SQLite / PostgreSQL / Logs / Code Check / Backup Check / Backup Save） → `backend_mcp/AGENTS.md`
- ブラウザ向け業務UI → `frontend_web/AGENTS.md`
- Electron アバタークライアント（AIコア専用） → `frontend_avatar/AGENTS.md`

**このファイルの内容：**
- まず知っておくこと（基本原則）
- バックエンド構成（ファイル構成と役割）
- Key Architectural Patterns（DB VIEWs、ID生成、API設計、監査フィールド、ログ、WebSocket、認証、Reboot機構）
- Database & Data Management（DB設定、初期データ、ログイン情報）
- API エンドポイント一覧とレスポンス形式
- AIコア backend実装
- Development Commands（backend固有）
- 追加手順（新規テーブル、VIEW、機能）
- Debugging方法

---

## まず知っておくこと（基本原則）

### 技術スタック
- **FastAPI + SQLAlchemy + SQLite** で構成
- **Python 3.13.3** + **uv** (パッケージマネージャ)
- **JWT認証** (python-jose, HS256, 60分有効期限)
- **AI統合** (Anthropic Claude, OpenAI, Google Gemini via respective SDKs)

### 命名規約と文字コード
- **画面/URL/JSON/DB の識別子は日本語が基本**
  - テーブル名: `C権限`, `M車両`, `T配車`
  - カラム名: `利用者ID`, `配車日付`, `商品名`
  - API endpoints: `/core/利用者/一覧`, `/apps/商品/作成`
  - JSON keys: `{"利用者名": "admin", "権限ID": "1"}`
- **文字コードは UTF-8 固定** - 全ファイル必須
- システム用語や一般名詞は英字: `request`, `query`, `item`, `items`, `total`, `limit`

### API設計の原則
- **原則 POST メソッド**（例外: `GET /` と `GET /core/サーバー状態`）
- **統一レスポンス形式:** `{"status": "OK"/"NG", "message": "...", "data": {...}}`
- **一覧系は `items`/`total`/`limit` で統一:** `{"items": [], "total": 100, "limit": 10000}`
- **認証必須**（`/core/auth/ログイン` 以外）- JWT Bearer token via `Authorization` header

## 実装の全体像と特徴

### core/apps デュアルサーバー + backend_mcp 連携
`backend_server` 自体は **2つの独立した FastAPI サーバー** で構成され、プロジェクト全体では別プロセスの `backend_mcp`（port 8095）が連携します。

**core_main.py (port 8091) - コア機能サーバー:**
- C系（Core/Common）: 権限、利用者、採番
- A系（AI/Advanced）: AIコア、会話履歴
- WebSocket機能: リアルタイムAI通信
- `/core/*` エンドポイント

**apps_main.py (port 8092) - アプリケーション機能サーバー:**
- M系（Master）: 配車区分、車両、商品分類、取引先分類、取引先、商品、商品構成、生産区分、生産工程
- T系（Transaction）: 配車、生産、商品入庫/出庫/棚卸
- V系（View）: 各マスタ・トランザクションの結合ビュー
- S系（Scheduler/Special）: 配車/生産の週表示・日表示
- `/apps/*` エンドポイント

**共有リソース:**
- **同じデータベース** (`_data/AiDiy/database.db`)
- **共通モジュール**: `database.py`, `core_schema.py`, `apps_schema.py`, `auth.py`, `deps.py`, `log_config.py`, `AIコア/AIセッション管理.py`

**外部連携サーバー (`backend_mcp`, port 8095):**
- 8 つの MCP サーバー（`aidiy_chrome_devtools` / `aidiy_desktop_capture` / `aidiy_sqlite` / `aidiy_postgres` / `aidiy_logs` / `aidiy_code_check` / `aidiy_backup_check` / `aidiy_backup_save`）を SSE で提供
- `backend_server/_config/AiDiy_mcp.json` から接続先を定義（必要なものだけ列挙可）
- Claude Agent SDK 系でブラウザ自動操作・画面キャプチャに加え、AIエージェントの自己検証（DB / ログ / 型チェック）にも利用
- 詳細は `../backend_mcp/AGENTS.md` を参照

### 実装の主要な特徴

**1. 日本語命名規約の徹底:**
- データベーステーブル名: `C権限`, `M商品`, `T配車`
- カラム名: `利用者ID`, `配車日付`, `商品名`
- APIエンドポイント: `/core/利用者/一覧`, `/apps/商品/作成`
- JSONキー: `{"利用者名": "admin", "権限ID": "1"}`

**2. POST中心のAPI設計:**
- CRUDは全てPOSTメソッド（`/一覧`, `/取得`, `/登録`, `/変更`, `/削除`）
- 例外: `GET /` (疎通確認), `GET /core/サーバー状態` (ステータス取得)
- 統一レスポンス形式: `{"status": "OK"/"NG", "message": "...", "data": {...}}`

**3. Database VIEWsを使わないアーキテクチャ:**
- V系エンドポイントは **データベースVIEWオブジェクトを作成しない**
- 全て **生SQLクエリ（SELECT + LEFT JOIN）** で実装
- 例: `V利用者` は `C利用者` と `C権限` をJOINする生SQLを実行

**4. カスタムID生成システム (C採番):**
- **AUTOINCREMENTを使用しない**
- `C採番` テーブルで各テーブルのID採番を管理
- `/core/C採番/採番` APIで次のIDを取得（トランザクション保護）
- 予測可能で制御しやすいID管理

**5. 監査フィールドの標準化:**
- 全テーブルに自動付与: `登録日時`, `登録利用者ID`, `登録利用者名`, `登録端末ID`, `更新日時`, `更新利用者ID`, `更新利用者名`, `更新端末ID`
- `core_crud/utils.py` と `apps_crud/utils.py` の共通ヘルパー関数で統一生成
- `create_audit_fields(認証情報)` と `update_audit_fields(認証情報)` を使用

**6. Reboot機構（内部再起動システム）:**
- `temp/reboot_core.txt` (core_main用) または `temp/reboot_apps.txt` (apps_main用) を作成するとサーバーが自動再起動
- 起動時に `@app.on_event("startup")` でファイルを検知して `os._exit(0)`
- バックグラウンドスレッドで1秒毎に監視
- `_start.py` によるプロセス監視と組み合わせて使用

**7. 構成管理システム (conf/):**
- シングルトン `ConfigManager` (`conf/__main__.py`)
- JSON設定ファイル (`_config/AiDiy_key.json`) から読み込み
- AI APIキー、モデル設定などを一元管理
- `app.conf` でアクセス可能

**8. WebSocket統合 (AIコア/AIセッション管理.py):**
- `WebSocketManager` クラスで接続管理
- セッション状態の永続化（リロード対応）
- AIコアの音声・画像・テキストストリーミング
- プロセス間通信対応（PIDベースのソケットID生成）

**9. AI統合機能 (AIコア/):**
- マルチベンダーAI対応: Anthropic Claude, OpenAI, Google Gemini
- ストリーミング処理: `AIストリーミング処理.py`
- 音声処理: `AI音声処理.py`, `AI音声認識.py`
- チャット: `AIチャット.py`
- コード生成: `AIコード.py`

### 新しい Code CLI を追加する手順（重要）

`hermes_cli` 追加時の実装を、今後の CLI 追加手順として残します。
新しい code CLI を追加するときは、**最低でも以下を一式対応**してください。

#### 1. 実行ランタイムの追加
対象: `AIコア/AIコード_cli.py`

- `_コマンドパス取得()` に新CLI名を追加
- `バージョン確認()` に新CLIの `--version` 実行方法を追加
- `_コマンド構築()` に
  - 新規会話コマンド
  - 継続会話コマンド
  - 必要ならモデル指定
  を追加
- Windows 固有事情がある場合は、Windows 分岐を追加する
  - 例: `hermes_cli` は Windows では `wsl bash -i -c "hermes ..."` で呼び出す

#### 2. CodeAgent 側の表示・メッセージ対応
対象: `AIコア/AIコード.py`

- welcome 文言
- 未インストール時メッセージ
- 必要なら AI 名に応じた説明文
に新CLI名を追加する

#### 3. モデル定義の追加
対象: `conf/conf_model.py`

- `CODE_<CLI名>_MODELS` を追加
- `_sync_local_model_configs()` に `AiDiy_code_<cli名>.json` の読込を追加
- `get_code_models()` の返却値に新CLIを追加

#### 4. 設定JSONの追加
対象:
- `conf/conf_json.py`
- `_config/AiDiy_key.json`
- `_config/AiDiy_code_<cli名>.json`

- `conf_json.DEFAULT_CONFIG` に `CODE_<CLI名>_MODEL` を追加
- `AiDiy_key.json` にも同じキーを追加
- `AiDiy_code_<cli名>.json` を作成し、最低でも `auto` モデルを定義する

#### 5. 設定UI対応
対象:
- `frontend_web/src/components/AiDiy/dialog/AI設定再起動.vue`
- `frontend_avatar/src/dialog/AI設定再起動.vue`

- `CODE_MODEL_KEYS` に新CLIの設定キーを追加
- `availableModels.code_models` に新CLIが来ても表示・選択できることを確認する

#### 6. 確認観点
新CLI追加後は、少なくとも以下を確認すること。

- AI設定再起動ダイアログで新CLIが選べる
- `AiDiy_key.json` に新CLI用キーが存在する
- `_config/AiDiy_code_<cli名>.json` が存在する
- バージョン確認が通る
- 新規会話コマンドが組み立てられる
- 継続会話コマンドが組み立てられる
- Windows 特有の呼び出し条件がある場合、その分岐が入っている

#### 7. `hermes_cli` 追加時の具体例
- CLI名: `hermes_cli`
- バージョン確認:
  - Windows: `wsl bash -i -c "hermes --version"`
  - 非Windows: `hermes --version`
- 新規会話:
  - `hermes chat --yolo -Q -q "..."`
- 継続会話:
  - `hermes chat --continue --yolo -Q -q "..."`
- モデル設定キー:
  - `CODE_HERMES_CLI_MODEL`
- モデル定義JSON:
  - `_config/AiDiy_code_hermes_cli.json`

### コードエージェントの自己改善機能（重要）

issue #4 対応として、コードエージェントには **本体修正完了後に知見整理だけを追加実行する自己改善機能** を持たせています。

#### 基本方針
- 共通ルーチン化ではなく、**`AIコア/AIコード.py` の後段制御として実装**する
- 本体の修正・検証・通知が終わったあとで、**同じエージェントをもう一度呼び出して** `.aidiy/knowledge` へ知見を書き込ませる
- これにより、フロントエンドは **本体修正完了を先に認識** できる
- 自己改善フェーズでは、**アプリ本体の追加修正は行わず**、 `.aidiy/knowledge` 配下の知見整理だけを行う

#### 実行タイミング
対象: `AIコア/AIコード.py`

- `input_text` 系:
  - `_基本AI処理()` 完了後に自己改善書き込みを実行
- `input_request` 系:
  - 検証ループ完了
  - 生成ファイル通知完了
  - `update_info` 送信完了
  - input / LiveAI への完了通知完了
  - **その後** に自己改善書き込みを実行

#### 書き込み先
- `.aidiy/knowledge` は **コードエージェントの実行ルート直下**を使用する
- つまり、プロジェクトごとの知見として蓄積する
- 書き込み対象の基本ファイル:
  - `.aidiy/knowledge/_index.md`
  - `.aidiy/knowledge/_最終変更.md`
  - `.aidiy/knowledge/<修正テーマ>.md`

#### 自己改善フェーズで整理する内容
- 今回の依頼内容
- 最終応答
- 変更ファイル一覧
- 修正内容の要約
- 関連ファイル・関連箇所
- 次回以降の注意点
- 類似修正時に再利用できる知見

#### `.aidiy/knowledge` 知見の事前利用
対象:
- `AIコア/AIコード_cli.py`
- `AIコア/AIコード_claude.py`
- （今後追加される `AIコード_xxxx.py` も同様）

- `.aidiy/knowledge/_index.md` が存在する場合のみ、プロンプトへ知見参照指示を差し込む
- 差し込み位置は **添付ファイル情報の前** とする
- 追加する指示の意図:
  - `.aidiy/knowledge` と `_index.md` を確認し
  - 類似修正の知見があれば利用する

#### 実装ルール
- 自己改善処理は **本体修正完了後の別フェーズ** として扱う
- 自己改善処理のために、フロントの完了通知を遅らせない
- `.aidiy/knowledge` が未作成なら、必要に応じて作成してよい
- `.aidiy/knowledge` 更新は、単なる作業ログではなく **次回再利用できる知見** を残すことを目的とする

**10. ログシステム (log_config.py):**
- 統一ログフォーマット
- `EndpointFilter` で頻繁に呼ばれるエンドポイント (`/core/サーバー状態`) を除外
- モジュール別ロガー取得: `get_logger(__name__)`

**11. パスワード管理の現状:**
- `C利用者` のパスワード保存は **段階移行対応**
- DB初期作成直後に `init_C利用者_data()` が投入する初期利用者は **プレーンテキスト保存** のまま
- 通常の `C利用者` 登録、および `C利用者` 変更でのパスワード更新時は **bcrypt ハッシュ保存**
- `core_crud/C利用者.py` の `authenticate_C利用者` は **平文一致 + bcrypt 照合** の二重対応
- 既存DBのプレーンテキスト利用者もログイン可能で、パスワード変更後にハッシュ保存へ移行できる

### No Alembic Migrations（マイグレーションなし）
- このプロジェクトは **Alembicを使用しません**
- スキーマ変更は **SQLAlchemyモデルの更新 + データベースリセット**
- データベースリセット手順:
  1. 全サーバー停止
  2. `_data/AiDiy/database.db` を削除
  3. サーバー再起動（テーブル自動作成 + 初期データ投入）

### テーブルスキーマ変更時の必須対応（重要）

テーブル追加・項目追加などスキーマを変更した場合、**既存のデータベースファイルには古いスキーマが残っている**可能性があります。
以下の対応を **必ず** 実施してください。

#### SQLite の ALTER TABLE 制約（重要）

SQLite の `ALTER TABLE` は以下の操作**のみ**サポートしています：

| 操作 | 可否 |
|------|------|
| `ADD COLUMN` カラム追加 | ✅ 可能 |
| `RENAME TABLE` テーブル名変更 | ✅ 可能 |
| `RENAME COLUMN` カラム名変更 | ✅ 可能 |
| カラム削除 | ❌ 直接不可（テーブル再作成が必要） |
| カラムの型・制約変更 | ❌ 直接不可（テーブル再作成が必要） |

#### 1. カラム追加・テーブル追加時（ALTER TABLE ADD COLUMN）

既存データベースを調べ、テーブルやカラムが存在しない場合は `ALTER TABLE` で追加してください。
サーバー起動時（`on_event("startup")`）に自動適用されるよう、`init.py` などに組み込むのが推奨です。

```python
# 例: M得意先 に 得意先略称 を追加する場合（apps_crud/init.py に追記）
from sqlalchemy import text

def apply_schema_migrations(db: Session):
    """既存DBへのスキーマ変更を適用する（起動時に自動実行）"""
    # カラムの存在確認
    result = db.execute(text("PRAGMA table_info(M得意先)")).fetchall()
    existing_columns = [row[1] for row in result]

    # カラムが存在しない場合のみ追加（冪等性を保つ）
    if "得意先略称" not in existing_columns:
        db.execute(text("ALTER TABLE M得意先 ADD COLUMN 得意先略称 TEXT"))
        db.commit()
```

**手順:**
1. `PRAGMA table_info(<テーブル名>)` で既存カラム一覧を確認
2. 想定カラムが存在しない場合のみ `ALTER TABLE ... ADD COLUMN` を実行（冪等性を保つ）
3. `apps_crud/init.py` または `core_crud/init.py` の起動処理（`init_db_data`）に組み込む

> **過去事例（M得意先）:** `得意先略称` カラムをモデルに追加したが既存DBに未反映のため起動エラー。
> `apply_schema_migrations` で `ALTER TABLE` を実行して解決。同様の事象は**どのマスタ追加時も発生しうる**。

#### 2. カラム削除・型変更時（テーブル再作成パターン）

カラム削除や型変更が必要な場合は、**テーブル再作成**が必要です。

```python
# 例: テーブル再作成（カラム削除・型変更時）
def recreate_table_without_old_column(db: Session):
    db.execute(text("""
        CREATE TABLE M得意先_new (
            得意先ID TEXT PRIMARY KEY,
            得意先名 TEXT NOT NULL,
            得意先略称 TEXT,
            -- ... 必要なカラムのみ定義
            登録日時 TEXT, 登録利用者ID TEXT, 登録利用者名 TEXT, 登録端末ID TEXT,
            更新日時 TEXT, 更新利用者ID TEXT, 更新利用者名 TEXT, 更新端末ID TEXT
        )
    """))
    db.execute(text("""
        INSERT INTO M得意先_new SELECT 得意先ID, 得意先名, 得意先略称, ...
        FROM M得意先
    """))
    db.execute(text("DROP TABLE M得意先"))
    db.execute(text("ALTER TABLE M得意先_new RENAME TO M得意先"))
    db.commit()
```

#### 3. 機能削除時（DROP TABLE）

機能削除により不要になったテーブルは、既存データベースに残り続けます。
不要テーブルは **必ず削除** してください。

```python
# 例: 不要になった T旧テーブル を削除する場合
def drop_obsolete_tables(db: Session):
    """不要になったテーブルを削除する"""
    db.execute(text("DROP TABLE IF EXISTS T旧テーブル"))
    db.commit()
```

**手順:**
1. 削除対象テーブルに関連する Model / CRUD / Router / Schema / `__init__.py` の登録をすべて削除
2. `apps_main.py` または `core_main.py` の `create_all` 対象からも除外
3. `DROP TABLE IF EXISTS` で既存DBのテーブルを削除（起動時処理に組み込む）

#### 4. 確認コマンド（SQLite）

```bash
# 現在のテーブル一覧を確認
sqlite3 backend_server/_data/AiDiy/database.db ".tables"

# テーブルのカラム構成を確認
sqlite3 backend_server/_data/AiDiy/database.db "PRAGMA table_info(テーブル名);"
```

#### 5. チェックリスト（テーブル構造変更時）

- [ ] `apps_models/` または `core_models/` のモデルを変更した
- [ ] 変更内容（追加/削除/リネーム）を確認した
- [ ] カラム追加 → `ALTER TABLE ADD COLUMN` を `init.py` に追加した
- [ ] カラム削除・型変更 → テーブル再作成スクリプトを `init.py` に追加した
- [ ] 不要テーブル → `DROP TABLE IF EXISTS` を `init.py` に追加した
- [ ] `apps_crud/` または `core_crud/` の CRUD 関数を更新した
- [ ] `apps_schema/` または `core_schema/` の Pydantic スキーマを更新した
- [ ] `apps_crud/__init__.py` または `core_crud/__init__.py` を確認した
- [ ] バックエンドを再起動してエラーがないことを確認した

## バックエンド構成 (backend_server/)

### Core Files（エントリーポイントと共通モジュール）

**エントリーポイント（FastAPIサーバー）:**
- **core_main.py** (port 8091) - Core/Common features (C系, A系)
  - 管理するテーブル: `C採番`, `C権限`, `C利用者`, `A会話履歴`
  - 登録するルーター: `auth`, `C権限`, `V権限`, `C利用者`, `V利用者`, `C採番`, `V採番`, `files`, `AIコア`, `A会話履歴`
  - `@app.on_event("startup")`:
    - Reboot監視スレッド起動 (`temp/reboot_core.txt`)
    - ログ設定初期化 (`setup_logging()`)
    - 設定管理初期化 (`app_conf.init()`)
    - C系初期データ投入 (`core_crud.init_db_data(db)`)
  - エンドポイント:
    - `GET /` - 疎通確認
    - `GET /core/サーバー状態` - サーバー状態取得（ready_count/busy_count）

- **apps_main.py** (port 8092) - Application features (M系, T系, V系, S系)
  - 管理するテーブル: `M配車区分`, `M生産区分`, `M生産工程`, `M商品分類`, `M取引先分類`, `M取引先`, `M車両`, `M商品`, `M商品構成`, `T配車`, `T生産`, `T商品出庫`, `T商品棚卸`, `T商品入庫`
  - 登録するルーター: `M配車区分`, `V配車区分`, `M生産区分`, `V生産区分`, `M生産工程`, `V生産工程`, `M商品分類`, `V商品分類`, `M取引先分類`, `V取引先分類`, `M取引先`, `V取引先`, `M車両`, `V車両`, `M商品`, `V商品`, `M商品構成`, `V商品構成`, `T配車`, `V配車`, `T生産`, `V生産`, `V生産払出`, `T商品出庫`, `V商品出庫`, `T商品棚卸`, `V商品棚卸`, `T商品入庫`, `V商品入庫`, `V商品推移表`, `S配車_週表示`, `S配車_日表示`, `S生産_週表示`, `S生産_日表示`
  - `@app.on_event("startup")`:
    - Reboot監視スレッド起動 (`temp/reboot_apps.txt`)
    - ログ設定初期化 (`setup_logging()`)
    - 設定管理初期化 (`app_conf.init(conf_path_enabled=False, conf_models_enabled=False)`)
    - M/T系初期データ投入 (`apps_crud.init_db_data(db)`)
    - バックアップ並列処理起動（`AIコア.AIバックアップ.バックアップ実行_共通ログ` をバックグラウンドスレッドで実行）
      - `temp/reboot_apps_code_base_path.txt` が存在する場合、その内容を `CODE_BASE_PATH` として読み込みセッション設定に渡す
  - エンドポイント:
    - `GET /` - 疎通確認

**共通データベースモジュール:**
- **database.py** - SQLAlchemy設定（両サーバーで共有）
  - `engine`: SQLiteエンジン (`_data/AiDiy/database.db`)
  - `SessionLocal`: セッションファクトリ (`autocommit=False, autoflush=False`)
  - `Base`: declarative base (全モデルの基底クラス)
  - `get_db()`: DBセッション取得用依存関係関数

**共通スキーマ:**
- **core_schema/ / apps_schema/** - Pydantic models（core/apps分離、各々ディレクトリ構成）
  - `__init__.py`: 全クラスを再エクスポート（`import core_schema as schemas` で利用）
  - `common.py`: 共通クラス `ResponseBase`, `ErrorResponse`, `ListRequest`
  - 各テーブルごとに個別ファイル: `C権限.py`, `M商品.py`, `T生産.py` など
  - 各テーブル: `<テーブル名>Base`, `<テーブル名>Create`, `<テーブル名>Update`, `<テーブル名>Delete`, `<テーブル名>Get`, `<テーブル名>`（レスポンス用）
  - 例: `C利用者Base`, `C利用者Create`, `M車両Update` など

**共通認証モジュール:**
- **auth.py** - JWT token creation
  - `SECRET_KEY`: `"dummy-secret-key-for-development"` (**本番環境では環境変数から読込必須**)
  - `ALGORITHM`: `"HS256"`
  - `ACCESS_TOKEN_EXPIRE_MINUTES`: `60`
  - `create_access_token(data, expires_delta)`: JWTトークン生成

- **deps.py** - Dependency injection
  - `oauth2_scheme`: OAuth2PasswordBearer (`tokenUrl="/core/auth/token"`)
  - `get_db()`: DBセッション取得（`database.get_db()` のエイリアス）
  - `get_現在利用者(token, db)`: JWT検証 + 現在利用者取得（全保護エンドポイントで使用）

**共通ログモジュール:**
- **log_config.py** - Unified logging configuration
  - `EndpointFilter`: 特定エンドポイント (`/core/サーバー状態`) のログを除外
  - `setup_logging()`: アプリケーション全体のログ初期化（startup時に呼出）
  - `get_logger(module_name)`: モジュール用ロガー取得
  - 設定済みフラグで重複初期化を防止
  - ログ出力先: `backend_server/temp/logs/yyyyMMdd.AiDiy.log`（日付が変わると自動で新規ファイル）

**共通WebSocketモジュール:**
- **AIコア/AIセッション管理.py** - WebSocket connection manager
  - `WebSocketConnection`: 個別接続管理クラス
    - 接続状態、ボタン状態、モデル設定を保持
    - ストリーミングプロセッサと音声処理を管理
  - `WebSocketManager`: グローバル接続マネージャー
    - `generate_socket_id()`: PID + タイムスタンプ + UUID でユニークID生成
    - `connect()`, `disconnect()`: 接続管理
    - `save_session_state()`: セッション永続化（リロード対応）
    - `get_connection()`, `send_to_socket()`, `broadcast()`: メッセージング
  - グローバルインスタンス: `AIセッション管理`

**リスト制御共通モジュール:**
- **list_controls.py** - 一覧取得の共通パラメータ処理
  - `LIMITED_MAX_ITEMS = 1000`: 件数制限時の上限
  - `is_limit_enabled(request)`: `件数制限` フィールドが True のときのみ上限を適用
  - `should_show_inactive(request)`: `無効も表示` フィールドが True のとき無効データも返す
  - `get_list_limit(request)`: 上限件数を返す（制限なし時は None）
  - 一覧エンドポイントで `from list_controls import ...` してリクエストごとに制御

**重要**: バックエンドは2つのFastAPIサーバーに分かれています：
  - core_main (port 8091) - コア機能 (C系, A系) + WebSocket
  - apps_main (port 8092) - アプリ機能 (M系, T系, V系, S系)

### Configuration System (conf/) - 設定管理システム

シングルトンパターンによる一元的な設定管理を提供します。

**モジュール構成:**
- **__init__.py** - エクスポート定義
  - `Conf` クラス、`_conf_class` インスタンス、`conf` シングルトンをエクスポート
  - `conf_json`, `ConfigJsonManager`, `conf_models`, `conf_path` もエクスポート

- **__main__.py** (実際のConfigManagerクラス定義)
  - `Conf` クラス: メイン設定管理クラス
  - `init(conf_path_enabled=True, conf_models_enabled=True)`: 設定初期化
  - `json`: JSON設定へのアクセス (`conf_json.get("KEY")`)
  - シングルトンインスタンス `conf` を提供

- **conf_json.py** - JSON設定ファイル管理
  - `ConfigJsonManager` クラス
  - `_config/AiDiy_key.json` からAPI keys、モデル設定などを読み込み
  - 設定項目例: `CHAT_AI_NAME`, `CHAT_GEMINI_MODEL`, `LIVE_AI_NAME`, `CODE_AI1_NAME`, API keys

- **conf_path.py** - パス解決ユーティリティ
  - プロジェクトルート、データディレクトリ、設定ファイルパスの解決

- **conf_model.py** - 設定データモデル定義
  - Pydanticモデルで設定の型安全性を提供

**使用方法:**
```python
from conf import conf as app_conf

# core_main.py/apps_main.py startup event
app_conf.init()  # 設定初期化
app.conf = app_conf  # FastAPIアプリに添付

# Routersでの使用
from fastapi import Request

@router.post("/some/endpoint")
def some_endpoint(request: Request):
    config_value = request.app.conf.json.get("CHAT_AI_NAME", "freeai_chat")
    api_key = request.app.conf.json.get("OPENAI_API_KEY")
```

**apps_main.pyでの特殊な初期化:**
```python
# apps_main.pyでは path/models 機能を無効化（コア機能はcore_mainで初期化済み）
app_conf.init(conf_path_enabled=False, conf_models_enabled=False)
```

### Data & Config Directories（データ・設定ディレクトリ）

**データディレクトリ (_data/):**
- **_data/AiDiy/** - 自動作成されるデータディレクトリ
  - `database.db` - SQLiteデータベースファイル（core_mainとapps_mainで共有）
  - ディレクトリは `database.py` の初期化時に自動作成 (`os.makedirs(DB_DIR, exist_ok=True)`)

**設定ディレクトリ (_config/):**
- **_config/** - 設定ファイル（`.gitignore` 対象。実ファイル内容は同期しない。必要な場合は `*.example.json` / `*.template.json` のみ共有）
  - `AiDiy_key.json` - API keys、モデル設定などの機密情報（`conf_json.py` で自動作成）
  - `AiDiy_chat__context.json` - チャットAI用コンテキスト設定ファイル
  - `AiDiy_code__context.json` - コードAI用コンテキスト設定ファイル
  - `AiDiy_code_claude_sdk.json` - Claude Agent SDK モード設定
  - `AiDiy_code_claude_cli.json` - Claude CLI モード設定
  - `AiDiy_code_copilot_cli.json` - Copilot CLI モード設定
  - `AiDiy_code_codex_cli.json` - Codex CLI モード設定
  - `AiDiy_code_gemini_cli.json` - Gemini CLI モード設定
  - `AiDiy_code_hermes_cli.json` - Hermes CLI モード設定
  - `AiDiy_live__context.json` - ライブAI用コンテキスト設定ファイル
  - `AiDiy_live_gemini.json` - Gemini Live モード設定
  - `AiDiy_live_openai.json` - OpenAI Live モード設定
  - `AiDiy_key.json` の設定項目例:
    ```json
    {
      "CHAT_AI_NAME": "freeai_chat",
      "CHAT_GEMINI_MODEL": "gemini-2.5-flash",
      "LIVE_AI_NAME": "freeai_live",
      "CODE_AI1_NAME": "claude_sdk",
      "CODE_AI2_NAME": "copilot_cli",
      "CODE_AI3_NAME": "codex_cli",
      "CODE_AI4_NAME": "gemini_cli",
      "OPENAI_API_KEY": "",
      "ANTHROPIC_API_KEY": "",
      "GEMINI_API_KEY": ""
    }
    ```

**tempディレクトリ (temp/):**
- **temp/** - 一時ファイル・Reboot制御ファイル
  - `reboot_core.txt` - core_mainサーバー再起動トリガー（作成されると自動再起動）
  - `reboot_apps.txt` - apps_mainサーバー再起動トリガー（作成されると自動再起動）
  - `reboot_apps_code_base_path.txt` - apps_main 再起動時に渡す `CODE_BASE_PATH` を記録するファイル（読み込み後自動削除）
  - startup時に自動作成 (`os.makedirs(temp_dir, exist_ok=True)`)

### Models (core_models/ and apps_models/) - SQLAlchemy ORMモデル

カテゴリ別に分離されたSQLAlchemy ORM models。日本語テーブル名・カラム名を使用。

**core_models/** - Core/Common tables (C系, A系):
- **__init__.py** - モデルのエクスポート
  - `from .C採番 import C採番`
  - `from .C権限 import C権限`
  - `from .C利用者 import C利用者`
  - `from .A会話履歴 import A会話履歴`
  - `database.Base` もエクスポート
  - 全テーブルに `有効` カラム (Integer, default=1) を追加済み（起動時マイグレーション対応）

- **C採番.py** - 採番管理テーブル
  - `__tablename__ = "C採番"`
  - 主キー: `採番ID` (String)
  - カラム: `最終採番値` (Integer), `採番備考` (String), + 監査フィールド

- **C権限.py** - 権限マスタテーブル
  - `__tablename__ = "C権限"`
  - 主キー: `権限ID` (String)
  - カラム: `権限名` (String), `権限備考` (String), + 監査フィールド

- **C利用者.py** - 利用者マスタテーブル
  - `__tablename__ = "C利用者"`
  - 主キー: `利用者ID` (String)
  - カラム: `利用者名`, `パスワード` (**平文**), `権限ID` (外部キー), `利用者備考`, + 監査フィールド

- **A会話履歴.py** - AI会話履歴テーブル
  - `__tablename__ = "A会話履歴"`
  - 主キー: `ソケットID` + `シーケンス` (複合)
  - カラム: `チャンネル`, `メッセージ識別`, `メッセージ内容`, `ファイル名`, `サムネイル画像`, + 監査フィールド

**apps_models/** - Application tables (M系, T系):
- **__init__.py** - モデルのエクスポート（C利用者・C採番も cross-import）
  - `from .M配車区分 import M配車区分`
  - `from .M生産区分 import M生産区分`
  - `from .M生産工程 import M生産工程`
  - `from .M商品分類 import M商品分類`
  - `from .M取引先分類 import M取引先分類`
  - `from .M取引先 import M取引先`
  - `from .M車両 import M車両`
  - `from .M商品 import M商品`
  - `from .M商品構成 import M商品構成`（複合主キー: 商品ID + 明細SEQ）
  - `from .T配車 import T配車`
  - `from .T生産 import T生産`（複合主キー: 生産伝票ID + 明細SEQ）
  - `from .T商品入庫 import T商品入庫`
  - `from .T商品出庫 import T商品出庫`
  - `from .T商品棚卸 import T商品棚卸`
  - `database.Base` もエクスポート
  - ※ `C利用者`, `C採番` も cross-import（`apps_main.py` の `create_all` 用）

- **M配車区分.py**, **M生産区分.py**, **M生産工程.py**, **M商品分類.py**, **M取引先分類.py**, **M取引先.py**, **M車両.py**, **M商品.py** - Master tables
  - 日本語 `__tablename__` と監査フィールド
  - 全テーブルに `有効` カラム (Integer, default=1)

- **M商品構成.py** - 明細型マスタ（ヘッダー＋明細を単一テーブルで管理）
  - 複合主キー: `商品ID` + `明細SEQ`（0=ヘッダー行、1以上=明細行）
  - 詳細は「M商品構成の実装」セクション参照

- **T配車.py**, **T商品入庫.py**, **T商品出庫.py**, **T商品棚卸.py** - Transaction tables
  - 日本語 `__tablename__` と監査フィールド
  - T配車: `配車伝票ID` (PK), `配車日付`, `車両ID`, `配車区分ID`, など
  - T商品系: 商品ID、日付、数量などを管理

- **T生産.py** - 生産トランザクション（明細型）
  - 複合主キー: `生産伝票ID` + `明細SEQ`（0=ヘッダー行、1以上=明細行）
  - T生産も M商品構成 と同様の全削除→全再作成パターン

**共通パターン:**
- 全モデルが `database.Base` を継承
- 全テーブルに監査フィールド（登録日時/登録利用者ID/登録利用者名/登録端末ID/更新日時/更新利用者ID/更新利用者名/更新端末ID）
- `__tablename__` は日本語（例: `"C権限"`, `"M商品"`, `"T配車"`）
- カラム名も日本語（例: `利用者ID`, `配車日付`, `商品名`）

### CRUD Operations (core_crud/ and apps_crud/) - データベース操作関数

カテゴリ別に分離されたCRUD操作関数。監査フィールドの自動付与を提供。

**core_crud/** - Core/Common operations (C系, A系):
- **__init__.py** - CRUD modules と utilities をエクスポート
  - `from .C権限 import *`
  - `from .C利用者 import *`
  - `from .A会話履歴 import *`
  - `from .init import init_db_data`
  - `from .utils import create_audit_fields, update_audit_fields, get_current_datetime`

- **utils.py** - 監査フィールドヘルパー（crud1とcrud2で同一内容）
  - `get_current_datetime()` - 現在日時を `'YYYY-MM-DD HH:MM:SS'` 形式で返す
  - `create_audit_fields(認証情報, is_update=False)` - 登録時の監査フィールド辞書を生成
    - `is_update=False`: 登録日時/登録利用者ID/登録利用者名/登録端末ID + 更新日時/更新利用者ID/更新利用者名/更新端末ID
    - `is_update=True`: 更新日時/更新利用者ID/更新利用者名/更新端末ID のみ
  - `update_audit_fields(認証情報)` - 更新時の監査フィールド辞書を生成（`create_audit_fields(認証情報, is_update=True)` のエイリアス）
  - 認証情報: `{"利用者ID": "admin", "利用者名": "Administrator"}`
  - 認証情報がNoneの場合: `"system"` を使用

- **init.py** - 初期データ投入 + スキーママイグレーション（core_main.py startup時に呼出）
  - `init_db_data(db: Session)` - C系、A系の初期データを投入
  - **スキーママイグレーション**: C権限/C利用者/C採番 テーブルに `有効` カラムを自動追加（既存DBへの ALTER TABLE）
  - C権限: 5件（1=システム管理者, 2=管理者, 3=利用者, 4=閲覧者, 9=その他）
  - C利用者: 5件（admin/leader/user/guest/other + パスワード）
  - C採番: 5件（T配車/T生産/T商品棚卸/T商品入庫/T商品出庫 + Xテスト、初期値10000）

- **C権限.py** - C権限テーブルCRUD
  - `get_C権限_list(db)` - 全件取得
  - `get_C権限_by_権限ID(db, 権限ID)` - 1件取得
  - `create_C権限(db, 権限: schemas.C権限Create)` - 作成
  - `update_C権限(db, 権限ID, 権限: schemas.C権限Update)` - 更新
  - `delete_C権限(db, 権限ID)` - 削除

- **C利用者.py** - C利用者テーブルCRUD
  - `authenticate_C利用者(db, 利用者ID, パスワード)` - 認証（**平文比較**）
  - `get_C利用者_list(db)` - 全件取得（**パスワード除外**）
  - `get_C利用者_by_利用者ID(db, 利用者ID)` - 1件取得（**パスワード除外**）
  - `create_C利用者(db, 利用者: schemas.C利用者Create)` - 作成（**パスワード平文保存**）
  - `update_C利用者(db, 利用者ID, 利用者: schemas.C利用者Update)` - 更新
  - `delete_C利用者(db, 利用者ID)` - 削除

- **A会話履歴.py** - A会話履歴テーブルCRUD
  - `get_A会話履歴_list(db, ソケットID, チャンネル, 件数)` - 一覧取得
  - `get_A会話履歴(db, ソケットID, シーケンス)` - 1件取得
  - `create_A会話履歴(db, 会話: schemas.A会話履歴Create, 認証情報)` - 作成
  - `update_A会話履歴(db, ソケットID, シーケンス, 会話: schemas.A会話履歴Update, 認証情報)` - 更新
  - `delete_A会話履歴(db, ソケットID, シーケンス)` - 削除

- **Note**: C採番のCRUD操作は `core_router/C採番.py` で直接models1にアクセス（core_crud/に独立ファイルなし）

**apps_crud/** - Application operations (M系, T系):
- **__init__.py** - CRUD modules と utilities をエクスポート
  - M系（M配車区分, M生産区分, M生産工程, M商品分類, M取引先分類, M取引先, M車両, M商品, M商品構成）の CRUD をエクスポート
  - T系（T配車, T生産, T商品入庫, T商品出庫, T商品棚卸）の CRUD をエクスポート
  - `from .init import init_db_data`
  - `from .utils import create_audit_fields, update_audit_fields, get_current_datetime`

- **utils.py** - core_crud/utils.py と同一内容（監査フィールドヘルパー）
  - NOTE: core_crud と apps_crud で同じ utils.py を保持（通常は変更しない）

- **seed_data.py** - マスタ初期データ定数定義
  - `INITIAL_PRODUCT_COMPOSITIONS`: M商品構成の初期データ定義

- **init.py** - 初期データ投入 + スキーママイグレーション（apps_main.py startup 時に呼出）
  - `init_db_data(db: Session)` - 起動時に自動実行
  - **スキーママイグレーション（既存DB対応）**: 旧テーブル削除・リネーム・カラム追加を自動適用
    - M商品構成明細 旧テーブル → 削除
    - M生産分類 → M生産区分 にリネーム（旧名称対応）
    - M商品構成: 旧スキーマ検出時にテーブル再作成 + カラム追加（生産区分ID, 生産工程ID, 最小ロット構成数量）
    - T生産: 明細SEQ/受入商品ID が未存在時にテーブル再作成
  - **初期データ投入**（データが空の場合のみ）:
    - M配車区分: 8件（1〜8: 通常/定期/予備/緊急/特別/巡回/回送/予備）
    - M生産区分: 複数件（H系/Z系などの生産区分）
    - M生産工程: 複数件（生産工程マスタ）
    - M商品分類: 複数件（商品分類マスタ）
    - M取引先分類: 複数件（取引先分類マスタ）
    - M取引先: 複数件（取引先マスタ）
    - M車両: 8件（1001〜1007 + 1099: １号車〜７号車 + 未定）
    - M商品: 複数件（各種商品）
    - M商品構成: seed_data.py の `INITIAL_PRODUCT_COMPOSITIONS` から投入
    - T配車: 8件（ランダム開始日、今日〜7日先）
    - T生産: 複数件（サンプル生産データ）
    - T商品出庫: 6件（H001商品、明日〜14日以内、数量100〜500）
    - T商品入庫: 3件（H001商品、3日後/8日後/13日後、数量500）
    - T商品棚卸: 1件（H001商品、本日、実棚数量200）

- **M配車区分.py**, **M生産区分.py**, **M生産工程.py**, **M商品分類.py**, **M取引先分類.py**, **M取引先.py**, **M車両.py**, **M商品.py** - Master CRUD
  - 各テーブルの `get_list`, `get_by_ID`, `create` 関数（マスタ系は create のみ、変更/削除はルーターで直接処理）

- **M商品構成.py** - 明細型マスタ CRUD
  - `get_M商品構成`, `get_M商品構成一覧`, `get_M商品構成明細一覧`
  - `build_M商品構成_data`: レコード一覧からヘッダー+明細 dict を組み立て
  - `create_M商品構成`, `update_M商品構成`（全削除→全再作成）, `delete_M商品構成`

- **T配車.py**, **T商品入庫.py**, **T商品出庫.py**, **T商品棚卸.py** - Transaction CRUD
  - 各テーブルの `get_list`, `get_by_ID`, `create`, `update`, `delete` 関数

- **T生産.py** - 生産トランザクション CRUD（明細型、M商品構成と同パターン）
  - `get_T生産`, `get_T生産ヘッダ`, `get_T生産一覧`, `get_T生産明細一覧`
  - `build_T生産_data`, `create_T生産`, `update_T生産`（全削除→全再作成）, `delete_T生産`

**重要**: このプロジェクトでは Database VIEWs は作成しません。V系エンドポイントは全て生SQLクエリで実装されています。

### API Routers (core_router/ and apps_router/) - APIエンドポイント

カテゴリ別に分離されたFastAPI routers。日本語エンドポイント、POST中心設計。

**core_router/** - Core/Common endpoints (core_main.pyで使用):

- **auth.py** - 認証関連エンドポイント
  - `POST /core/auth/ログイン` - ログイン（認証不要）
    - Request: `schemas.LoginRequest` (`利用者ID`, `パスワード`)
    - Response: `{"access_token": "...", "token_type": "bearer"}`
    - 内部: `core_crud.authenticate_C利用者()` で平文パスワード比較
  - `POST /core/auth/token` - OAuth2トークン取得（FastAPI docsUI用、認証不要）
  - `POST /core/auth/ログアウト` - ログアウト（認証必要）
    - JWTはステートレスなのでサーバー側では無効化なし（クライアントでトークン破棄）
  - `POST /core/auth/現在利用者` - 現在利用者情報取得（認証必要）

- **C権限.py**, **C利用者.py**, **C採番.py** - C系テーブルCRUDエンドポイント
  - 各テーブルで以下のエンドポイントを提供:
    - `POST /core/<テーブル名>/一覧` - 一覧取得
    - `POST /core/<テーブル名>/取得` - 1件取得
    - `POST /core/<テーブル名>/登録` - 作成
    - `POST /core/<テーブル名>/変更` - 更新
    - `POST /core/<テーブル名>/削除` - 削除
  - C採番のみ追加エンドポイント:
    - `POST /core/C採番/採番` - ID採番（トランザクション保護）

- **V権限.py**, **V利用者.py**, **V採番.py** - V系 core VIEW query endpoints
  - 各VIEWで以下のエンドポイントを提供:
    - `POST /core/V<名前>/一覧` - 一覧取得（生SQLクエリ、LEFT JOIN使用）
  - 例: `V利用者` は `C利用者` と `C権限` をJOIN

- **AIコア.py** - AIコア WebSocketエンドポイント
  - `WebSocket /core/ws/AIコア` - WebSocket接続
  - セッション管理、ボタン状態の永続化
  - ストリーミングプロセッサとの統合

- **A会話履歴.py** - A会話履歴CRUDエンドポイント
  - `POST /core/A会話履歴/一覧` - 一覧取得（ソケットID、チャンネルでフィルタ可能）
  - `POST /core/A会話履歴/取得` - 1件取得
  - `POST /core/A会話履歴/登録` - 作成
  - `POST /core/A会話履歴/変更` - 更新
  - `POST /core/A会話履歴/削除` - 削除

**apps_router/** - Application endpoints (apps_main.pyで使用):

- **M配車区分.py**, **M生産区分.py**, **M生産工程.py**, **M商品分類.py**, **M取引先分類.py**, **M取引先.py**, **M車両.py**, **M商品.py** - M系テーブルCRUDエンドポイント
  - 各テーブルで以下のエンドポイントを提供:
    - `POST /apps/<テーブル名>/一覧` - 一覧取得
    - `POST /apps/<テーブル名>/取得` - 1件取得
    - `POST /apps/<テーブル名>/登録` - 作成
    - `POST /apps/<テーブル名>/変更` - 更新
    - `POST /apps/<テーブル名>/削除` - 削除

- **M商品構成.py** - 明細型マスタCRUDエンドポイント
  - `POST /apps/M商品構成/一覧`, `/取得`, `/登録`, `/変更`, `/削除`
  - 詳細は「M商品構成の実装」セクション参照

- **T配車.py**, **T商品入庫.py**, **T商品出庫.py**, **T商品棚卸.py** - T系テーブルCRUDエンドポイント
  - 各テーブルで以下のエンドポイントを提供:
    - `POST /apps/<テーブル名>/一覧` - 一覧取得
    - `POST /apps/<テーブル名>/取得` - 1件取得
    - `POST /apps/<テーブル名>/登録` - 作成
    - `POST /apps/<テーブル名>/変更` - 更新
    - `POST /apps/<テーブル名>/削除` - 削除
  - T配車とV配車のみ: 開始日付/終了日付でフィルタ可能

- **T生産.py** - 生産トランザクションCRUDエンドポイント（明細型）
  - `POST /apps/T生産/一覧`, `/取得`, `/登録`, `/変更`, `/削除`

- **V配車区分.py**, **V生産区分.py**, **V生産工程.py**, **V商品分類.py**, **V取引先分類.py**, **V取引先.py**, **V車両.py**, **V商品.py**, **V商品構成.py**, **V配車.py** - V系 VIEW query endpoints
  - 各VIEWで以下のエンドポイントを提供:
    - `POST /apps/V<名前>/一覧` - 一覧取得（生SQLクエリ、LEFT JOIN使用）

- **V生産.py**, **V生産払出.py**, **V商品入庫.py**, **V商品出庫.py**, **V商品棚卸.py**, **V商品推移表.py** - V系 VIEW query endpoints
  - 各VIEWで以下のエンドポイントを提供:
    - `POST /apps/V<名前>/一覧` - 一覧取得（生SQLクエリ、複雑な集計含む）
  - V商品推移表: 入庫/出庫/棚卸を統合した推移表
  - V生産払出: 生産に伴う材料払出の一覧

- **S配車_週表示.py**, **S配車_日表示.py**, **S生産_週表示.py**, **S生産_日表示.py** - S系 special processing endpoints
  - `POST /apps/S配車_週表示/一覧` - 週別配車表示
  - `POST /apps/S配車_日表示/一覧` - 日別配車表示
  - `POST /apps/S生産_週表示/一覧` - 週別生産表示
  - `POST /apps/S生産_日表示/一覧` - 日別生産表示

## Key Architectural Patterns

### Database VIEWs (V系)

**重要**: このプロジェクトでは **Database VIEWs は作成しません**。

V系エンドポイントは全て生SQLクエリ（SELECT + JOIN）で実装されています:

**How V系 endpoints work:**
1. VIEW routers (`core_router/V*.py`, `apps_router/V*.py`) contain raw SQL SELECT statements
2. SQL queries use LEFT JOINs to combine tables (e.g., V利用者 joins C利用者 + C権限)
3. Each V系 router has `/一覧` endpoint that executes SQL directly
4. No database VIEW objects are created

**Example V系 endpoints:**
- `POST /core/V利用者/一覧` - Users joined with permission details via raw SQL
- `POST /apps/V車両/一覧` - Vehicles with joined data
- `POST /apps/V商品/一覧` - Products with calculations
- `POST /apps/V商品推移表/一覧` - Product transaction history aggregations

**To add a new V系 endpoint:**
1. Create router in `core_router/V[名前].py` or `apps_router/V[名前].py` with raw SQL query
2. Implement `/一覧` endpoint with `db.execute(text(sql))` 
3. Register router in `core_main.py` or `apps_main.py`
4. Restart server

### Custom ID Generation System (C採番 Table)

The system uses a **centralized sequential ID generator** instead of database AUTOINCREMENT:

**How it works:**
1. `C採番` table stores current ID counters for each table type
2. Each table (e.g., "C権限", "C利用者", "M車両") has a corresponding row in C採番
3. When creating new records, call the ID allocation endpoint to get the next ID
4. Transaction-based increments ensure no ID conflicts

**Implementation:**
- **Allocation API**: `POST /core/C採番/採番` (defined in `core_router/C採番.py`)
- **Request**: `{"採番区分": "C利用者", "採番数": 1}`
- **Response**: Returns next available ID(s) and increments counter atomically
- **Initial setup**: IDs are seeded in `core_crud/init.py` during first startup

**When to use:**
- Use for tables that need predictable, sequential IDs (C系, M系 tables)
- Add new entries in `core_crud/init.py` when creating new tables that use this system
- Can be bypassed for simple tables that don't need custom ID management

### API Design Pattern

**All CRUD endpoints use POST method** (no GET/PUT/削除 for data operations):
- Function-per-endpoint: `/core/利用者/一覧`, `/core/利用者/作成`, `/core/利用者/更新`, `/core/利用者/削除`
- Unified response format: `{"status": "OK"/"NG", "message": "...", "data": {...}}`
- Request/response keys use Japanese

**Router Registration:**
All routers must be explicitly registered in `core_main.py` or `apps_main.py`:
```python
from core_router import C利用者
app.include_router(C利用者.router)
```
The order matters for startup logging - register in logical groups (C系, M系, T系, V系, S系).

### Audit Fields Pattern

All database tables include standard audit fields:
- **Registration fields** (set on create):
  - `登録日時` - Registration datetime (YYYY-MM-DD HH:MM:SS format)
  - `登録利用者ID` - User ID who created the record
  - `登録利用者名` - User name who created the record
  - `登録端末ID` - Terminal/device ID (defaults to 'localhost')
- **Update fields** (set on create and update):
  - `更新日時` - Last update datetime
  - `更新利用者ID` - User ID who last updated
  - `更新利用者名` - User name who last updated
  - `更新端末ID` - Terminal/device ID

**Helper functions in `core_crud/utils.py` and `apps_crud/utils.py`:**
Always use these helpers to populate audit fields automatically.

### Logging System

Unified logging configuration (`log_config.py`):
- Filters out noisy logs from frequently-called endpoints (e.g., `/core/サーバー状態`)
- `EndpointFilter` class allows customization of excluded endpoints

**Logger usage:**
```python
from log_config import get_logger

logger = get_logger(__name__)
logger.info("Message here")
```

**Setup:**
Logging is initialized in `core_main.py` / `apps_main.py` startup event via `setup_logging()`.

### WebSocket Support（WebSocket統合）

`AIコア/AIセッション管理.py` でWebSocket接続を一元管理。AIコアのリアルタイム通信を提供。

**WebSocketConnection クラス:**
- 個別のWebSocket接続を管理
- プロパティ:
  - `websocket`: FastAPI WebSocketオブジェクト
  - `socket_id`: ユニークなソケットID（PID + タイムスタンプ + UUID）
  - `is_connected`: 接続状態フラグ
  - `ボタン状態`: ボタンの状態（スピーカー、マイク、カメラ、チャット、エージェント1〜4、チャットモード）
  - `モデル設定`: AI modelの設定（app.confからコピー）
  - `streaming_processor`: StreamingProcessor インスタンス
  - `recognition_processor`: 音声認識プロセッサ
  - `audio_data`: 音声データバッファ
- メソッド:
  - `accept()`: WebSocket接続受け入れ
  - `send_json(data)`, `receive_json()`: JSON送受信
  - `close()`: 接続クローズ（プロセッサ停止含む）
  - `update_state(ボタン, manager)`: ボタン状態更新とセッション保存
  - `update_model_settings(設定, manager)`: モデル設定更新とセッション保存

**WebSocketManager クラス:**
- グローバルな接続マネージャー（シングルトン `AIセッション管理` インスタンス）
- プロパティ:
  - `active_connections`: アクティブ接続の辞書 (`socket_id` → `WebSocketConnection`)
  - `session_states`: セッション状態の辞書（リロード後も状態復元）
- メソッド:
  - `generate_socket_id()`: PIDベースのユニークID生成
  - `connect(websocket, socket_id, app_conf)`: 接続登録（新規またはリロード）
    - 新規セッション: app.confからモデル設定をコピー
    - 既存セッション: session_statesから状態復元
  - `save_session_state(socket_id, ボタン, モデル設定, ソース最終更新日時)`: セッション保存
  - `disconnect(socket_id, keep_session)`: 接続切断（オプションでセッション保持）
  - `send_to_socket(socket_id, data)`: 特定ソケットへ送信
  - `broadcast(data)`: 全接続へブロードキャスト
  - `handle_message(socket_id, message)`: クライアントメッセージをストリーミングプロセッサへ転送
  - `get_session_count()`, `get_session_list()`: セッション情報取得

**使用例:**
```python
# core_router/AIコア.py
from AIコア.AIセッション管理 import AIセッション管理

@router.websocket("/core/ws/AIコア")
async def websocket_endpoint(websocket: WebSocket, ...):
    socket_id = await AIセッション管理.connect(websocket, socket_id, request.app.conf)
    try:
        while True:
            message = await connection.receive_json()
            await AIセッション管理.handle_message(socket_id, message)
    finally:
        await AIセッション管理.disconnect(socket_id, keep_session=True)
```

**Note**: WebSocket routesは `core_router/AIコア.py` で実装され、core_main.pyに登録済み。

### Reboot機構（内部再起動システム）

core_main.pyとapps_main.pyに組み込まれた自動再起動機構。

**仕組み:**
1. startup時に `temp/` ディレクトリを作成
2. `temp/reboot_core.txt` (core_main用) または `temp/reboot_apps.txt` (apps_main用) の存在を確認
3. ファイルが存在する場合:
   - ファイルを削除
   - `raise SystemExit("reboot_core.txt detected")` でプロセス終了
4. バックグラウンドスレッドで1秒毎にファイル監視
5. ファイルが作成されると `os._exit(0)` でプロセス終了

**使用方法:**
```python
# core_mainを再起動する場合
with open("backend_server/temp/reboot_core.txt", "w") as f:
    f.write("reboot")

# apps_mainを再起動する場合
with open("backend_server/temp/reboot_apps.txt", "w") as f:
    f.write("reboot")
```

**`_start.py` との連携:**
- `_start.py` がプロセス終了を検知
- 15秒待機後に自動的にサーバーを再起動
- 設定変更や動的なコード再読み込みに使用可能

**実装詳細:**
- core_main.py:91-110 でreboot_core.txt監視スレッド起動
- apps_main.py:138-157 でreboot_apps.txt監視スレッド起動
- デーモンスレッドとして起動（メインプロセス終了時に自動終了）

### Authentication & Security

**JWT Authentication:**
- Algorithm: HS256
- Secret key: `"dummy-secret-key-for-development"` (hardcoded in `auth.py`)
- Token expiration: 60 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Dependency injection: `deps.py::get_現在利用者` validates token and injects current user
- Token refresh endpoint: `POST /core/auth/トークン更新` は既存 JWT が有効な間に新しい 60 分トークンを返す。Web/Avatar 側で C/M/T 操作、S/V 更新監視、AI非音声入力、AIファイル `files_temp` 送信時に利用する

**CRITICAL - Passwords are stored in plaintext:**
- Despite bcrypt/passlib being installed, authentication uses plaintext comparison
- See `core_crud/C利用者.py` for current implementation
- **Implement password hashing before production use**

**CORS Configuration:**
Allowed origins (in `core_main.py` and `apps_main.py`):
- `http://localhost:8090` (production Vite server)
- `http://localhost:5173` (default Vite dev server)
- `http://localhost:3000` (alternative port)
- `https://localhost` (Docker Nginx HTTPS)
- `http://localhost` (Docker Nginx HTTP)

## Database & Data Management

### Database Configuration
- **Location**: `backend_server/_data/AiDiy/database.db` (shared by core_main and apps_main)
- **Schema creation**: Auto-created on startup via `core_models.Base.metadata.create_all()` in `core_main.py` and `apps_models.Base.metadata.create_all()` in `apps_main.py`
- **Initial data seeding**: 
  - Core data: `core_crud.init.init_db_data()` in `core_main.py` startup event
  - App data: `apps_crud.init.init_db_data()` in `apps_main.py` startup event
- **Database VIEWs**: **Not used**. V系 endpoints use raw SQL queries instead
- **Reset database**: Delete `database.db` and restart both FastAPI servers (core_main and apps_main)

**Important**: This project does NOT use Alembic migrations. Schema changes are managed through SQLAlchemy model updates and database resets.

### Initial Data (Startup Seeding)

**Core data (seeded by core_main):**
- **C権限**: 5件（1/2/3/4/9: システム管理者/管理者/利用者/閲覧者/その他）
- **C利用者**: 5件（admin/leader/user/guest/other、パスワードは平文）
- **C採番**: 5件（T配車/T生産/T商品棚卸/T商品入庫/T商品出庫 + Xテスト）
  - 全て初期値 10000、`有効` フラグ付き（Xテストは有効=False）

**Application data (seeded by apps_main):**
- **M配車区分**: 8件（1-8: 通常/定期/予備/緊急/特別/巡回/回送/予備）
- **M車両**: 8件（1001-1007, 1099: １号車〜７号車、未定）
- **M商品**: 5件（H001-H004, H099: 牛飼料/豚飼料/鶏飼料/魚飼料/その他）
- **T配車**: 8件（ランダム開始日、今日〜7日先）
- **T商品出庫**: 6件（H001商品、明日〜14日以内、数量100-500）
- **T商品入庫**: 3件（H001商品、3日後/8日後/13日後、数量500）
- **T商品棚卸**: 1件（H001商品、本日、実棚数量200）

### Default Login Credentials
- Admin: `admin` / `********`
- Manager: `leader` / `secret`
- User: `user` / `user`
- Guest: `guest` / `guest`
- Other: `other` / `other`

**実装確認済みの補足（間違いやすい点）:**
- **初期投入の条件**: `core_crud.init_db_data()` は **admin が未存在のときだけ** C利用者を投入します。既にDBに admin がいる場合、パスワード変更は自動反映されません。
- **DBファイル**: `backend_server/_data/AiDiy/database.db` を core_main / apps_main が共有します。
- **CORS許可リスト**: `core_main.py` / `apps_main.py` は `http://localhost:5173`, `http://localhost:3000`, `http://localhost:8090` のみ許可。ポート変更時は両方更新が必要です。
- **ホットリロード**: `_start.py` 経由の起動は `uvicorn --reload` が付かないため自動リロードされません（再起動 or `temp/reboot_core.txt` / `temp/reboot_apps.txt` を利用）。

## API エンドポイント

### レスポンス形式（共通）
基本形:
```json
{
  "status": "OK",
  "message": "メッセージ",
  "data": {},
  "error": null
}
```

一覧系の `data` は以下に統一:
```json
{
  "items": [],
  "total": 0,
  "limit": 3000
}
```
`limit` は各ルーター内の `MAX_ITEMS`（現在は 10000 固定）。

補足:
- `V利用者/一覧` と `C利用者/一覧|get` は **パスワードを返しません**。
- 認証なしで使えるのは `POST /core/auth/ログイン` のみ。

### エンドポイント一覧（現行）

**認証系 (core_main - port 8091):**
- `POST /core/auth/ログイン`
- `POST /core/auth/ログアウト`
- `POST /core/auth/現在利用者`
- `POST /core/auth/token`（docs 向け）

**コア系 CRUD (core_main - port 8091):**
- `POST /core/C利用者/一覧|get|create|update|delete`
- `POST /core/C権限/一覧|get|create|update|delete`
- `POST /core/C採番/一覧|get|create|update|delete|allocate`
- `POST /core/files/内容取得` - ファイル内容を base64 で返す
- `POST /core/files/内容更新` - ファイルを上書き保存（UTF-8+LF / bat=Shift-JIS+CRLF）

**AI系 (core_main - port 8091):**
- `POST /core/AIコア/初期化`（廃止済み互換）
- `POST /core/AIコア/セッション一覧`（廃止済み互換）
- `POST /core/AIコア/モデル情報/取得`（廃止済み互換）
- `POST /core/AIコア/モデル情報/設定`（廃止済み互換）
- `POST /core/A会話履歴/一覧|get|create|update|delete`

**アプリ系 CRUD (apps_main - port 8092):**
- `POST /apps/M配車区分/一覧|get|create|update|delete`
- `POST /apps/M生産区分/一覧|get|create|update|delete`
- `POST /apps/M生産工程/一覧|get|create|update|delete`
- `POST /apps/M商品分類/一覧|get|create|update|delete`
- `POST /apps/M取引先分類/一覧|get|create|update|delete`
- `POST /apps/M取引先/一覧|get|create|update|delete`
- `POST /apps/M車両/一覧|get|create|update|delete`
- `POST /apps/M商品/一覧|get|create|update|delete`
- `POST /apps/M商品構成/一覧|get|create|update|delete`
- `POST /apps/T配車/一覧|get|create|update|delete`
- `POST /apps/T生産/一覧|get|create|update|delete`
- `POST /apps/T商品入庫/一覧|get|create|update|delete`
- `POST /apps/T商品出庫/一覧|get|create|update|delete`
- `POST /apps/T商品棚卸/一覧|get|create|update|delete`

**V系（一覧専用）:**
- **Core VIEWs (core_main - port 8091):**
  - `POST /core/V利用者/一覧`
  - `POST /core/V権限/一覧`
  - `POST /core/V採番/一覧`
- **Apps VIEWs (apps_main - port 8092):**
  - `POST /apps/V配車区分/一覧`
  - `POST /apps/V生産区分/一覧`
  - `POST /apps/V生産工程/一覧`
  - `POST /apps/V商品分類/一覧`
  - `POST /apps/V取引先分類/一覧`
  - `POST /apps/V取引先/一覧`
  - `POST /apps/V車両/一覧`
  - `POST /apps/V商品/一覧`
  - `POST /apps/V商品構成/一覧`（明細件数を集計して返す）
  - `POST /apps/V配車/一覧`
  - `POST /apps/V生産/一覧`
  - `POST /apps/V生産払出/一覧`
  - `POST /apps/V商品入庫/一覧`
  - `POST /apps/V商品出庫/一覧`
  - `POST /apps/V商品棚卸/一覧`
  - `POST /apps/V商品推移表/一覧`

**S系（スケジューラー）(apps_main - port 8092):**
- `POST /apps/S配車_週表示/一覧`
- `POST /apps/S配車_日表示/一覧`
- `POST /apps/S生産_週表示/一覧`
- `POST /apps/S生産_日表示/一覧`

**例外の GET:**
- `GET /` (core_main & apps_main)（疎通確認）
- `GET /core/サーバー状態` (core_main)（ready/busy の固定レスポンス）

### 一覧検索・ページング
- 一覧 API は基本パラメータなし、`MAX_ITEMS` 上限で取得。
- `T配車` と `V配車` のみ `開始日付`/`終了日付` の絞り込みあり。

## AIコア Component System (A系) - AI統合システム

AIコアは、複数のAIサービスを統合したマルチパネルAIインターフェースのバックエンド実装です。

### バックエンド実装

**WebSocketエンドポイント** (`core_router/AIコア.py`):
- **`WebSocket /core/ws/AIコア`** - メインWebSocket接続
  - クエリパラメータ: `ソケットID` (リロード時に指定)
  - 接続時:
    1. `AIセッション管理.connect()` で接続登録
    2. セッション状態を復元または新規作成
    3. 初期化メッセージ送信（ボタン状態）
    4. ストリーミングプロセッサ起動
  - メッセージ受信:
    - クライアントからのメッセージを `AIセッション管理.handle_message()` へ転送
    - ストリーミングプロセッサが処理
  - 切断時:
    - セッション状態を保存（keep_session=True）
    - プロセッサ停止、接続クローズ

**ファイル管理 WebSocket メッセージ識別 (チャンネル=file):**

| メッセージ識別 | 方向 | 内容 |
|--------------|------|------|
| `files_backup` | 双方向 | バックアップ済みファイル一覧を要求/返信。セッションの `全ファイルリスト` (キャッシュ) を使用 |
| `files_temp` | 双方向 | temp フォルダのファイル一覧を要求/返信。都度ファイルシステムを走査 |
| `files_save` | クライアント→サーバー | ファイル保存後に送信。`バックアップ実行_共通ログ` を再実行してセッションの `全ファイルリスト` を更新（返信なし）。その後クライアントは `files_backup` / `files_temp` を送って一覧を再取得する |

**AI名 命名規則（厳格・完全一致で比較）:**
- `CHAT_AI_NAME`: `gemini_chat` / `freeai_chat` / `openrt_chat`（`_chat` サフィックス必須）
- `LIVE_AI_NAME`: `gemini_live` / `freeai_live` / `openai_live`（`_live` サフィックス必須）
- `CODE_AI*_NAME`: `claude_sdk` / `claude_cli` / `copilot_cli` / `codex_cli` / `gemini_cli` / `hermes_cli`（`_sdk` または `_cli` サフィックス必須）
- 関連比較箇所: `AIコア/AIチャット.py`, `AIコア/AIチャット_gemini.py`, `core_router/AIコア.py`, `AIコア/AIセッション管理.py`
- フロントエンド側: `frontend_web/.../AI設定再起動.vue` の `CHAT_MODEL_KEYS` / `LIVE_MODEL_KEYS` / `LIVE_VOICE_KEYS`

**ファイル API (`core_router/files.py`):**
- `POST /core/files/内容取得` — `{"ファイル名": str}` → base64 でファイル内容を返す
- `POST /core/files/内容更新` — `{"ファイル名": str, "内容": str}` → ファイルを上書き保存
  - 通常ファイル: UTF-8 + `newline="\n"`（Windows 自動 CRLF 変換を抑止）
  - `.bat` / `.cmd`: Shift-JIS + `newline="\r\n"`

**HTTP REST エンドポイント** (廃止済み - 互換性のため残存):
- `POST /core/AIコア/初期化` - セッション初期化（現在はWebSocketで代替）
- `POST /core/AIコア/セッション一覧` - デバッグ用セッション一覧取得
- `POST /core/AIコア/モデル情報/取得` - モデル設定情報の取得
- `POST /core/AIコア/モデル情報/設定` - モデル設定の更新

### AI Integration（AI統合モジュール - AIコア/）

**モジュール構成:**
- **__init__.py** - AIコア modules エクスポート
- **AIセッション管理.py** - WebSocket接続管理
- **AIストリーミング処理.py** - `StreamingProcessor` クラス
  - 音声・画像・テキストのストリーミング処理
  - メッセージキュー管理
  - AI API呼び出し統合
- **AI音声処理.py** - 音声データ処理
  - `初期化_音声データ()` - 音声バッファ初期化
  - 音声データの分割・バッファリング
- **AI音声認識.py** - 音声認識処理
  - SpeechRecognition ライブラリ統合
  - マイク入力からテキスト変換
- **AIチャット.py** - チャットAI処理（共通インターフェース）
- **AIチャット_gemini.py** - Google Gemini チャット実装
- **AIチャット_openrt.py** - OpenAI Realtime チャット実装
- **AIライブ.py** - ライブAI処理（共通インターフェース）
- **AIライブ_gemini.py** - Google Gemini Live 実装
- **AIライブ_openai.py** - OpenAI Realtime 実装
- **AIコード.py** - コードAI処理（共通インターフェース）
- **AIコード_claude.py** - Claude Agent SDK 実装
- **AIコード_cli.py** - その他コードAI実装
- **AI内部ツール.py** - 内部ツール処理
- **AIバックアップ.py** - バックアップ処理

### AI Providers（AI統合）

**対応AIサービス:**
- **Anthropic Claude**
  - パッケージ: `anthropic` (>=0.76.0), `claude-agent-sdk`
  - モデル設定: `CODE_CLAUDE_SDK_MODEL`（SDK）, `CODE_CLAUDE_CLI_MODEL`（CLI）
  - エージェント機能: Claude Agent SDKによるコード生成・実行

- **GitHub Copilot CLI** (`copilot_cli`)
  - モデル設定: `CODE_COPILOT_CLI_MODEL`
  - コマンド: `copilot` (npm グローバル)

- **OpenAI Codex CLI** (`codex_cli`)
  - モデル設定: `CODE_CODEX_CLI_MODEL`
  - コマンド: `codex` (npm グローバル)

- **Google Gemini CLI** (`gemini_cli`)
  - モデル設定: `CODE_GEMINI_CLI_MODEL`
  - コマンド: `gemini` (npm グローバル)

- **Hermes CLI** (`hermes_cli`)
  - モデル設定: `CODE_HERMES_CLI_MODEL`
  - コマンド: `hermes` (Windows では WSL 経由: `wsl bash -i -c "hermes ..."`)

- **OpenAI**
  - パッケージ: `openai`
  - モデル設定: `CHAT_OPENRT_MODEL`, `LIVE_OPENAI_MODEL`, `LIVE_OPENAI_VOICE`
  - リアルタイム機能: GPT Realtime API対応

- **Google Gemini**
  - パッケージ: `google-genai`
  - モデル設定:
    - Chat: `CHAT_GEMINI_MODEL` (例: `"gemini-2.5-flash"`)
    - Free AI: `CHAT_FREEAI_MODEL` (例: `"gemini-2.5-flash"`)
    - Live AI: `LIVE_GEMINI_MODEL`, `LIVE_GEMINI_VOICE` (音声対応)
  - 音声機能: Native Audio Preview対応

**設定管理:**
- API keys: `_config/AiDiy_key.json`
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `GEMINI_API_KEY`
- モデル設定: WebSocketセッション毎にapp.confからコピー（AIコア/AIセッション管理.py）

**会話履歴:**
- **A会話履歴** テーブルでセッション永続化
- フィールド: `ソケットID`, `シーケンス`, `チャンネル`, `メッセージ識別`, `メッセージ内容`, `ファイル名`, `サムネイル画像`
- 監査フィールド付き（登録/更新日時、利用者ID）

**Note**: AI features require valid API keys in the configuration file. Empty keys will cause AI operations to fail.

## Development Commands

**バックエンド依存関係 (Python 3.13.3 + uv):**
```bash
cd backend_server
uv sync          # Install/sync dependencies from pyproject.toml
uv add <package> # Add new dependency
```

**Key dependencies:**
- FastAPI + Uvicorn - Web framework and ASGI server
- SQLAlchemy - ORM for database operations
- Pydantic - Data validation and schema definition
- python-jose - JWT token handling
- AI SDKs: anthropic, openai, google-genai, claude-agent-sdk
- SpeechRecognition - Audio processing (for AI features)
- Pillow - Image processing

**Running backend only:**
```bash
# Core server (core_main)
cd backend_server
.venv/Scripts/python.exe -m uvicorn core_main:app --reload --host 0.0.0.0 --port 8091

# Apps server (apps_main) - in separate terminal
cd backend_server
.venv/Scripts/python.exe -m uvicorn apps_main:app --reload --host 0.0.0.0 --port 8092
```

**VS Code Debugging:**
- `backend_server/.vscode/launch.json`: バックエンドのみ（debugpy）

## M配車区分の実装（現行）
- モデル: `apps_models/M配車区分.py`
- CRUD: `apps_crud/M配車区分.py`
- API: `apps_router/M配車区分.py`
- 一覧ビュー: `apps_router/V配車区分.py`（生 SQL で取得）
- スキーマ: `apps_schema.py` の `M配車区分Base/登録/変更/削除/取得`

使うエンドポイント:
- `POST /apps/M配車区分/一覧|get|create|update|delete`
- `POST /apps/V配車区分/一覧`

注意:
- `M配車区分Update` は `配色枠/配色背景/配色前景` が必須扱いなので、更新時は3色を必ず送る。

## M商品構成の実装（明細型マスタの実装例）

### 概要

M商品構成は **ヘッダー行＋明細行を単一テーブルで管理する「明細型マスタ」** の実装例です。
別テーブルを作らず、`明細SEQ=0` をヘッダー行、`明細SEQ>0` を明細行として同一テーブルで完結させます。

```
M商品構成テーブル
┌──────────┬──────────┬──────────────┬──────────────┬ ...
│ 商品ID   │ 明細SEQ  │ 生産ロット   │ 構成商品ID   │
├──────────┼──────────┼──────────────┼──────────────┼ ...
│ H100     │ 0        │ 1000         │ NULL         │  ← ヘッダー行（見出し）
│ H100     │ 1        │ 1000         │ Z001         │  ← 明細行
│ H100     │ 2        │ 1000         │ Z002         │  ← 明細行
└──────────┴──────────┴──────────────┴──────────────┴ ...
```

### ファイル構成

| ファイル | 役割 |
|--------|------|
| `apps_models/M商品構成.py` | SQLAlchemy モデル（複合主キー） |
| `apps_schema/M商品構成.py` | Pydantic スキーマ（明細 Base 含む） |
| `apps_crud/M商品構成.py` | CRUD（全削除→全再作成パターン） |
| `apps_router/M商品構成.py` | API エンドポイント + バリデーション |
| `apps_router/V商品構成.py` | 一覧用 V 系（生 SQL、明細件数を集計） |

### モデル（apps_models/M商品構成.py）

```python
class M商品構成(Base):
    __tablename__ = "M商品構成"
    商品ID   = Column(Text, primary_key=True)
    明細SEQ  = Column(Integer, primary_key=True)  # 0=ヘッダー、1以上=明細
    生産ロット    = Column(Float, nullable=False)
    商品構成備考  = Column(Text)
    構成商品ID   = Column(Text)           # 明細行のみ使用
    構成数量分子  = Column(Float)          # 明細行のみ使用
    構成数量分母  = Column(Float)          # 明細行のみ使用
    構成商品備考  = Column(Text)
    有効 = Column(Boolean, ...)
    # + 監査フィールド（登録/更新 日時・利用者ID・利用者名・端末ID）
```

### スキーマ（apps_schema/M商品構成.py）

```python
class M商品構成明細Base(BaseModel):
    明細SEQ: int
    構成商品ID: str
    構成数量分子: float
    構成数量分母: float
    構成商品備考: Optional[str] = None

class M商品構成Base(BaseModel):
    生産ロット: float
    商品構成備考: Optional[str] = None
    有効: bool = True
    明細一覧: List[M商品構成明細Base] = Field(default_factory=list)

class M商品構成Create(M商品構成Base):
    商品ID: str

class M商品構成Update(BaseModel):
    商品ID: str
    生産ロット: Optional[float] = None
    商品構成備考: Optional[str] = None
    有効: Optional[bool] = None
    明細一覧: Optional[List[M商品構成明細Base]] = None
```

### CRUD の更新パターン（全削除→全再作成）

明細の追加・削除・並び替えを個別に追跡するより、
**更新時に全レコードを削除して全件を再作成** するのがシンプルで確実です。

```python
def update_M商品構成(db, 商品ID, 商品構成, 認証情報=None):
    # 1. 既存レコードを全削除
    db.query(models.M商品構成).filter(models.M商品構成.商品ID == 商品ID).delete(synchronize_session=False)
    db.flush()
    db.expunge_all()
    # 2. 全件を再作成（ヘッダー行 明細SEQ=0 + 明細行 明細SEQ=1,2,...）
    _create_レコード一覧(db, 商品ID, 生産ロット, ...)
    db.commit()
```

### レスポンス構築（build_M商品構成_data）

取得したレコード一覧からヘッダーと明細を分離してレスポンス dict を組み立てます。

```python
def build_M商品構成_data(db, 商品構成一覧):
    見出し = next((item for item in 商品構成一覧 if item.明細SEQ == 0), 商品構成一覧[0])
    return {
        "商品ID": 見出し.商品ID,
        "生産ロット": float(見出し.生産ロット),
        "明細一覧": _build_明細一覧(db, 商品構成一覧, 見出し.生産ロット),
        # ... 監査フィールドは見出し行から取得
    }
```

### V系（一覧）の実装

`V商品構成/一覧` は `明細SEQ = 0` のヘッダー行だけを集計します。
明細件数は `COUNT(*) WHERE 明細SEQ > 0` のサブクエリで取得します。

```sql
SELECT C.商品ID, P.商品名, C.生産ロット, C.有効,
    (SELECT COUNT(*) FROM M商品構成 D
     WHERE D.商品ID = C.商品ID AND D.明細SEQ > 0) AS 構成商品件数,
    ...
FROM M商品構成 C
LEFT JOIN M商品 P ON C.商品ID = P.商品ID
WHERE C.明細SEQ = 0   -- ヘッダー行のみ
ORDER BY C.商品ID
```

### バリデーション（apps_router/M商品構成.py）

```python
def _validate_request(db, request):
    if request.生産ロット <= 0:
        return "生産ロットは0より大きい値を入力してください"
    明細SEQ一覧 = [明細.明細SEQ for 明細 in request.明細一覧]
    if len(明細SEQ一覧) != len(set(明細SEQ一覧)):
        return "明細SEQが重複しています"
    for 明細 in request.明細一覧:
        if 明細.明細SEQ <= 0:
            return "明細SEQは1以上で入力してください"
```

> **M商品構成固有の仕様**: `構成数量`（分子/分母×生産ロットの計算値）はレスポンス返却用の派生値であり、スキーマには含まれない。フロントエンドでの自動計算もこのテーブル固有の実装（明細型マスタの汎用パターンではない）。

### 初期データ（apps_crud/M商品構成.py）

他の M 系テーブルと同様に `init_M商品構成_data(db)` 関数を持ちます。
初期データは `apps_crud/seed_data.py` の `INITIAL_PRODUCT_COMPOSITIONS` に定義します。

### 新規に明細型マスタを追加する場合

M商品構成の実装を参考に以下の点に注意してください：

1. **単一テーブル設計**: `明細SEQ=0` をヘッダー行として予約する
2. **複合主キー**: `(親ID, 明細SEQ)` の2カラムで主キーを構成する
3. **明細行でしか使わない列は nullable=True**: ヘッダー行では null が入る
4. **更新は全削除→全再作成**: 個別の明細行を追跡しない
5. **V系のカウント**: `WHERE 明細SEQ > 0` で明細件数を集計する

## 追加・変更の手順

### 新しいテーブルを追加する（C系 or A系の場合）
1. `core_models/` にモデル追加（`__tablename__` は日本語、監査カラム統一、`有効` カラム付与）。
2. `core_models/__init__.py` に追加して `create_all()` 対象に含める。
3. `core_schema/<テーブル名>.py` を作成し `Base/Create/Update/Delete/Get` を定義、`core_schema/__init__.py` に import を追加。
4. `core_crud/` に取得/一覧/作成などの関数を追加し `core_crud/__init__.py` に公開。
5. `core_router/` に CRUD ルーターを追加。
6. `core_main.py` に `include_router` を追加。
7. 初期データが必要なら `core_crud/init.py` に追加。
8. 採番が必要なら `C採番` の初期データも追加。

### 新しいテーブルを追加する（M系, T系, S系の場合）
1. `apps_models/` にモデル追加（`__tablename__` は日本語、監査カラム統一、`有効` カラム付与）。
2. `apps_models/__init__.py` に追加して `create_all()` 対象に含める。
3. `apps_schema/<テーブル名>.py` を作成し `Base/Create/Update/Delete/Get` を定義、`apps_schema/__init__.py` に import を追加。
4. `apps_crud/` に取得/一覧/作成などの関数を追加し `apps_crud/__init__.py` に公開。
5. `apps_router/` に CRUD ルーター（M*/T*/S*）を追加。
6. **【重要】`apps_router/` に V系エンドポイント（V*）も必ず追加** - M系・T系の一覧表示に使用
   - V車両、V商品などの実装例を参考にする
   - 生SQLで `SELECT` / `LEFT JOIN` を組み立て
   - `count(*)` で total を取得
7. `apps_main.py` に `include_router` を追加（**M/T/S系とV系の両方**）。
8. 初期データが必要なら `apps_crud/init.py` に追加。

**補足:** M系テーブルにはV系エンドポイントが必須です。フロントエンドの一覧画面は通常V系エンドポイントを使用します（例: M車両一覧テーブル.vue は `/apps/V車両/一覧` を呼び出す）。V系エンドポイントがないと一覧取得でエラーが発生します。

### 新しい V 系（一覧）を追加する
1. `core_router/V*.py` (C系) or `apps_router/V*.py` (M系/T系) を作成し、生 SQL で `SELECT` / `LEFT JOIN` を組み立てる。
2. `count(*)` は同じ FROM/JOIN 条件で取得する。
3. `core_main.py` or `apps_main.py` に `include_router` を追加。

### 新しい機能（API）を追加する
1. `core_schema.py` または `apps_schema.py` に request/response モデル追加。
2. `core_crud/` or `apps_crud/` に処理を追加（必要ならトランザクション）。
3. `core_router/` or `apps_router/` にエンドポイント追加（POST 前提）。
4. `core_main.py` or `apps_main.py` に `include_router` を追加。

## Debugging

**API Testing:**
- FastAPI Swagger UI (Core): http://localhost:8091/docs (interactive API documentation for core_main)
- FastAPI Swagger UI (Apps): http://localhost:8092/docs (interactive API documentation for apps_main)
- All endpoints accept JSON POST requests
- Test authentication by clicking "Authorize" button in Swagger UI

**バックエンドログ:**
- Console output where `_start.py` or uvicorn was launched
- Check `backend_server/startup_log.txt` for startup issues
- 日付ログ: `backend_server/temp/logs/yyyyMMdd.AiDiy.log`
- Database query logging: Set SQLAlchemy `echo=True` in `database.py`

**Database inspection:**
- Location: `backend_server/_data/AiDiy/database.db`
- Use SQLite Browser or DBeaver to inspect tables/VIEWs
- Remember to close DB tools before running server to avoid "database locked" errors

## 実装の注意点とベストプラクティス

### 必須の注意事項

**1. core/apps サーバー起動:**
- **`backend_server` を使うには両方のサーバー (core_main + apps_main) を起動する必要があります**
- `_start.py` を使えば自動で両方起動
- 個別起動の場合: 2つのターミナルで core_main.py と apps_main.py を起動
- Claude のブラウザ自動操作も使う場合は、別途 `backend_mcp` も起動します

**2. パスワードセキュリティ:**
- **現在パスワードは平文保存** - 本番環境では必ずハッシュ化実装が必要
- bcrypt/passlibはインストール済みだが未使用
- `core_crud/C利用者.py` の `authenticate_C利用者` で平文比較
- 実装例:
  ```python
  from passlib.context import CryptContext
  pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
  hashed = pwd_context.hash("password")
  verified = pwd_context.verify("password", hashed)
  ```

**3. Database VIEWs:**
- **V系 API は DB VIEW を作らず、生 SQL で取得します**
- 全てのV系エンドポイントは `db.execute(text(sql))` で実装
- 複雑なJOINや集計もSQLで記述

**4. API設計パターン:**
- 全CRUDエンドポイントはPOSTメソッド
- 例外: `GET /` (疎通確認), `GET /core/サーバー状態` (ステータス)
- 統一レスポンス形式を維持: `{"status": "OK"/"NG", "message": "...", "data": {...}}`

**5. 文字エンコーディング:**
- **全ファイルは UTF-8 エンコーディング必須**
- 日本語識別子を使用するため
- Windowsコンソールのエンコーディングは `_start.py` が変更しないため、必要に応じてターミナル側で調整

### ベストプラクティス

**1. 監査フィールドの使用:**
```python
from core_crud.utils import create_audit_fields, update_audit_fields

# 作成時
認証情報 = {"利用者ID": 現在利用者.利用者ID, "利用者名": 現在利用者.利用者名}
監査項目 = create_audit_fields(認証情報)
db.add(Model(..., **監査項目))

# 更新時
監査項目 = update_audit_fields(認証情報)
for key, value in 監査項目.items():
    setattr(record, key, value)
```

**2. エラーハンドリング:**
```python
try:
    # DB操作
    db.commit()
    return schemas.ResponseBase(status="OK", message="成功", data={...})
except Exception as e:
    db.rollback()
    logger.error(f"エラー: {e}")
    return schemas.ResponseBase(status="NG", message="エラー発生", error={"detail": str(e)})
```

**3. ログ出力:**
```python
from log_config import get_logger
logger = get_logger(__name__)

logger.info("情報メッセージ")
logger.warning("警告メッセージ")
logger.error("エラーメッセージ")
logger.debug("デバッグメッセージ")
```

**4. JWT認証の使用:**
```python
from deps import get_現在利用者
from core_models import C利用者

@router.post("/protected/endpoint")
def protected_endpoint(現在利用者: C利用者 = Depends(get_現在利用者)):
    # 現在利用者.利用者ID, 現在利用者.利用者名 などにアクセス可能
    return {"user": 現在利用者.利用者ID}
```

**5. WebSocket使用:**
```python
from AIセッション管理 import AIセッション管理

@router.websocket("/ws/custom")
async def custom_websocket(websocket: WebSocket, request: Request):
    socket_id = await AIセッション管理.connect(websocket, None, request.app.conf)
    try:
        while True:
            data = await AIセッション管理.get_connection(socket_id).receive_json()
            await AIセッション管理.send_to_socket(socket_id, {"response": "..."})
    finally:
        await AIセッション管理.disconnect(socket_id)
```

### よくある落とし穴

**1. C採番の使い忘れ:**
- 新規テーブル追加時は `core_crud/init.py` または `apps_crud/init.py` にC採番の初期値を追加
- ID生成時は `POST /core/C採番/採番` を呼び出す

**2. 監査フィールドの設定漏れ:**
- 全てのCRUDで `create_audit_fields` または `update_audit_fields` を使用
- 手動で日時を設定しない（`get_current_datetime()` を使用）

**3. トランザクション管理:**
- 複数テーブルの更新は `db.commit()` でまとめて確定
- エラー時は必ず `db.rollback()` を呼び出す

**4. Rebootファイルの削除忘れ:**
- Reboot機構を使用した後、ファイルは自動削除される
- 手動で作成した場合、削除されるまで再起動ループが発生する

**5. WebSocketセッション管理:**
- リロード時は既存の `ソケットID` を渡してセッション復元
- 新規セッションとリロードセッションを区別する

**6. apps_crud/__init__.py への登録忘れ (重要):**
- 新規テーブル（M系/T系）追加時、`apps_crud/<テーブル名>.py` を作成するだけでは不十分
- **必ず `apps_crud/__init__.py` に import と __all__ への追加が必要**
- 忘れると `crud.get_M○○` や `crud.create_M○○` が使えず、ImportErrorやAttributeErrorが発生
- 例: マスタテーブル追加時は以下を追加:
  ```python
  from apps_crud.M○○ import get_M○○, get_M○○一覧, create_M○○
  # __all__ リストにも 'get_M○○', 'get_M○○一覧', 'create_M○○' を追加
  ```
- 同様に `core_crud/__init__.py` も C系/A系追加時に更新必要

## 注意点
- **V 系 API は DB VIEW を作らず、生 SQL で取得します。**
- `T配車/変更` は `配車伝票ID` を **関数パラメータ** として受け取ります（POST bodyとは別）。
- パスワードは平文保存のため、運用前にハッシュ化対応が必要です。
- **両方のサーバー (core_main + apps_main) を起動する必要があります。** `_start.py` を使えば自動で両方起動します。Claude のブラウザ自動操作まで確認する場合は `backend_mcp` も合わせて起動します。
