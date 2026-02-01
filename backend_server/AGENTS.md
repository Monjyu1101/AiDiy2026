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
- **[../docs/03_コーディングルール/](../docs/03_コーディングルール/_index.html)** - コーディングルール、命名規則、ベストプラクティス
- **[../frontend_server/AGENTS.md](../frontend_server/AGENTS.md)** - フロントエンド実装詳細（Vue 3 + TypeScript）

**📚 ドキュメントリソース（docs/フォルダ）：**
プロジェクトの詳細なドキュメントは `docs/` フォルダにHTML形式で整備されています。
- **[../docs/02_バックエンドAPI追加例/](../docs/02_バックエンドAPI追加例/_index.html)** - バックエンドAPI追加手順
- **[../docs/03_コーディングルール/](../docs/03_コーディングルール/_index.html)** - 命名規則、ベストプラクティス、レビューチェックリスト（**必読**）

**フロントエンド（frontend_server/）の情報は別ドキュメント：**
このドキュメントはバックエンドに特化しています。フロントエンド（Vue.js、Vite、Pinia、ルーティング、コンポーネント構造など）の詳細は `frontend_server/AGENTS.md` を参照してください。

**このファイルの内容：**
- まず知っておくこと（基本原則）
- バックエンド構成（ファイル構成と役割）
- Key Architectural Patterns（DB VIEWs、ID生成、API設計、監査フィールド、ログ、WebSocket、認証、Reboot機構）
- Database & Data Management（DB設定、初期データ、ログイン情報）
- API エンドポイント一覧とレスポンス形式
- AコアAI backend実装
- Development Commands（backend固有）
- 追加手順（新規テーブル、VIEW、機能）
- Debugging方法

---

## まず知っておくこと（基本原則）

### 技術スタック
- **FastAPI + SQLAlchemy + SQLite** で構成
- **Python 3.13** + **uv** (パッケージマネージャ)
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

### デュアルサーバーアーキテクチャ
このプロジェクトは **2つの独立したFastAPIサーバー** で構成されています：

**main1.py (port 8091) - コア機能サーバー:**
- C系（Core/Common）: 権限、利用者、採番
- A系（AI/Advanced）: AコアAI、会話履歴
- WebSocket機能: リアルタイムAI通信
- `/core/*` エンドポイント

**main2.py (port 8092) - アプリケーション機能サーバー:**
- M系（Master）: 配車区分、車両、商品
- T系（Transaction）: 配車、商品入庫/出庫/棚卸
- V系（View）: 各マスタ・トランザクションの結合ビュー
- S系（Scheduler/Special）: 配車週表示・日表示
- `/apps/*` エンドポイント

**共有リソース:**
- **同じデータベース** (`_data/AiDiy/database.db`)
- **共通モジュール**: `database.py`, `schemas.py`, `auth.py`, `deps.py`, `log_config.py`, `ws_manager.py`

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
- `crud1/utils.py` と `crud2/utils.py` の共通ヘルパー関数で統一生成
- `create_audit_fields(認証情報)` と `update_audit_fields(認証情報)` を使用

**6. Reboot機構（内部再起動システム）:**
- `temp/reboot1.txt` (main1用) または `temp/reboot2.txt` (main2用) を作成するとサーバーが自動再起動
- 起動時に `@app.on_event("startup")` でファイルを検知して `os._exit(0)`
- バックグラウンドスレッドで1秒毎に監視
- `_start.py` によるプロセス監視と組み合わせて使用

**7. 構成管理システム (conf/):**
- シングルトン `ConfigManager` (`conf/__main__.py`)
- JSON設定ファイル (`_config/RiKi_AiDiy_key.json`) から読み込み
- AI APIキー、モデル設定などを一元管理
- `app.conf` でアクセス可能

**8. WebSocket統合 (ws_manager.py):**
- `WebSocketManager` クラスで接続管理
- セッション状態の永続化（リロード対応）
- AコアAIの音声・画像・テキストストリーミング
- プロセス間通信対応（PIDベースのソケットID生成）

**9. AI統合機能 (AコアAI/):**
- マルチベンダーAI対応: Anthropic Claude, OpenAI, Google Gemini
- ストリーミング処理: `streaming.py`
- 音声処理: `audio_processing.py`, `recognition.py`
- チャット: `chat.py`
- コード生成: `code.py`

**10. ログシステム (log_config.py):**
- 統一ログフォーマット
- `EndpointFilter` で頻繁に呼ばれるエンドポイント (`/core/サーバー状態`) を除外
- モジュール別ロガー取得: `get_logger(__name__)`

**11. パスワード管理の現状:**
- **警告**: 現在パスワードは **平文保存**
- bcrypt/passlibはインストール済みだが未使用
- `crud1/C利用者.py` の `authenticate_C利用者` で平文比較
- **本番環境では必ずハッシュ化実装が必要**

### No Alembic Migrations（マイグレーションなし）
- このプロジェクトは **Alembicを使用しません**
- スキーマ変更は **SQLAlchemyモデルの更新 + データベースリセット**
- データベースリセット手順:
  1. 全サーバー停止
  2. `_data/AiDiy/database.db` を削除
  3. サーバー再起動（テーブル自動作成 + 初期データ投入）

## バックエンド構成 (backend_server/)

### Core Files（エントリーポイントと共通モジュール）

**エントリーポイント（FastAPIサーバー）:**
- **main1.py** (port 8091) - Core/Common features (C系, A系)
  - 管理するテーブル: `C採番`, `C権限`, `C利用者`, `A会話履歴`
  - 登録するルーター: `auth`, `C権限`, `V権限`, `C利用者`, `V利用者`, `C採番`, `V採番`, `AコアAI`, `A会話履歴`
  - `@app.on_event("startup")`:
    - Reboot監視スレッド起動 (`temp/reboot1.txt`)
    - ログ設定初期化 (`setup_logging()`)
    - 設定管理初期化 (`app_conf.init()`)
    - C系初期データ投入 (`crud1.init_db_data(db)`)
  - エンドポイント:
    - `GET /` - 疎通確認
    - `GET /core/サーバー状態` - サーバー状態取得（ready_count/busy_count）

- **main2.py** (port 8092) - Application features (M系, T系, V系, S系)
  - 管理するテーブル: `M配車区分`, `M車両`, `M商品`, `T配車`, `T商品出庫`, `T商品棚卸`, `T商品入庫`
  - 登録するルーター: `M配車区分`, `V配車区分`, `M車両`, `V車両`, `M商品`, `V商品`, `T配車`, `V配車`, `T商品出庫`, `V商品出庫`, `T商品棚卸`, `V商品棚卸`, `T商品入庫`, `V商品入庫`, `V商品推移表`, `S配車_週表示`, `S配車_日表示`
  - `@app.on_event("startup")`:
    - Reboot監視スレッド起動 (`temp/reboot2.txt`)
    - ログ設定初期化 (`setup_logging()`)
    - 設定管理初期化 (`app_conf.init(conf_path_enabled=False, conf_models_enabled=False)`)
    - M/T系初期データ投入 (`crud2.init_db_data(db)`)
  - エンドポイント:
    - `GET /` - 疎通確認

**共通データベースモジュール:**
- **database.py** - SQLAlchemy設定（両サーバーで共有）
  - `engine`: SQLiteエンジン (`_data/AiDiy/database.db`)
  - `SessionLocal`: セッションファクトリ (`autocommit=False, autoflush=False`)
  - `Base`: declarative base (全モデルの基底クラス)
  - `get_db()`: DBセッション取得用依存関係関数

**共通スキーマ:**
- **schemas.py** - Pydantic models（全テーブル分を1ファイルに集約）
  - 共通レスポンス: `ResponseBase`, `ErrorResponse`
  - 認証: `LoginRequest`, `Token`
  - 各テーブル: `<テーブル名>Base`, `<テーブル名>Create`, `<テーブル名>Update`, `<テーブル名>Delete`, `<テーブル名>Get`, `<テーブル名>Response`
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
- **ws_manager.py** - WebSocket connection manager
  - `WebSocketConnection`: 個別接続管理クラス
    - 接続状態、画面状態、ボタン状態、モデル設定を保持
    - ストリーミングプロセッサと音声処理を管理
  - `WebSocketManager`: グローバル接続マネージャー
    - `generate_socket_id()`: PID + タイムスタンプ + UUID でユニークID生成
    - `connect()`, `disconnect()`: 接続管理
    - `save_session_state()`: セッション永続化（リロード対応）
    - `get_connection()`, `send_to_socket()`, `broadcast()`: メッセージング
  - グローバルインスタンス: `ws_manager`

**重要**: バックエンドは2つのFastAPIサーバーに分かれています：
  - main1 (port 8091) - コア機能 (C系, A系) + WebSocket
  - main2 (port 8092) - アプリ機能 (M系, T系, V系, S系)

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
  - `_config/RiKi_AiDiy_key.json` からAPI keys、モデル設定などを読み込み
  - 設定項目例: `CHAT_AI`, `CHAT_GEMINI_MODEL`, `LIVE_AI`, `CODE_AI1`, API keys

- **conf_path.py** - パス解決ユーティリティ
  - プロジェクトルート、データディレクトリ、設定ファイルパスの解決

- **conf_model.py** - 設定データモデル定義
  - Pydanticモデルで設定の型安全性を提供

**使用方法:**
```python
from conf import conf as app_conf

# main1.py/main2.py startup event
app_conf.init()  # 設定初期化
app.conf = app_conf  # FastAPIアプリに添付

# Routersでの使用
from fastapi import Request

@router.post("/some/endpoint")
def some_endpoint(request: Request):
    config_value = request.app.conf.json.get("CHAT_AI", "freeai")
    api_key = request.app.conf.json.get("OPENAI_API_KEY")
```

**main2.pyでの特殊な初期化:**
```python
# main2.pyでは path/models 機能を無効化（コア機能はmain1で初期化済み）
app_conf.init(conf_path_enabled=False, conf_models_enabled=False)
```

### Data & Config Directories（データ・設定ディレクトリ）

**データディレクトリ (_data/):**
- **_data/AiDiy/** - 自動作成されるデータディレクトリ
  - `database.db` - SQLiteデータベースファイル（main1とmain2で共有）
  - ディレクトリは `database.py` の初期化時に自動作成 (`os.makedirs(DB_DIR, exist_ok=True)`)

**設定ディレクトリ (_config/):**
- **_config/** - 設定ファイル（.gitignoreに追加推奨）
  - `RiKi_AiDiy_key.json` - API keys、モデル設定などの機密情報
  - ファイルが存在しない場合は `conf_json.py` で自動作成（デフォルト値）
  - 設定項目例:
    ```json
    {
      "CHAT_AI": "freeai",
      "CHAT_GEMINI_MODEL": "gemini-3-pro-image-preview",
      "LIVE_AI": "freeai_live",
      "CODE_AI1": "copilot",
      "OPENAI_API_KEY": "",
      "ANTHROPIC_API_KEY": "",
      "GEMINI_API_KEY": ""
    }
    ```

**tempディレクトリ (temp/):**
- **temp/** - 一時ファイル・Reboot制御ファイル
  - `reboot1.txt` - main1サーバー再起動トリガー（作成されると自動再起動）
  - `reboot2.txt` - main2サーバー再起動トリガー（作成されると自動再起動）
  - startup時に自動作成 (`os.makedirs(temp_dir, exist_ok=True)`)

### Models (models1/ and models2/) - SQLAlchemy ORMモデル

カテゴリ別に分離されたSQLAlchemy ORM models。日本語テーブル名・カラム名を使用。

**models1/** - Core/Common tables (C系, A系):
- **__init__.py** - モデルのエクスポート
  - `from .C採番 import C採番`
  - `from .C権限 import C権限`
  - `from .C利用者 import C利用者`
  - `from .A会話履歴 import A会話履歴`
  - `database.Base` もエクスポート

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

**models2/** - Application tables (M系, T系):
- **__init__.py** - モデルのエクスポート
  - `from .M配車区分 import M配車区分`
  - `from .M車両 import M車両`
  - `from .M商品 import M商品`
  - `from .T配車 import T配車`
  - `from .T商品入庫 import T商品入庫`
  - `from .T商品出庫 import T商品出庫`
  - `from .T商品棚卸 import T商品棚卸`
  - `database.Base` もエクスポート

- **M配車区分.py**, **M車両.py**, **M商品.py** - Master tables
  - 日本語 `__tablename__` と監査フィールド

- **T配車.py**, **T商品入庫.py**, **T商品出庫.py**, **T商品棚卸.py** - Transaction tables
  - 日本語 `__tablename__` と監査フィールド
  - T配車: `配車伝票ID` (PK), `配車日付`, `車両ID`, `配車区分ID`, など
  - T商品系: 商品ID、日付、数量などを管理

**共通パターン:**
- 全モデルが `database.Base` を継承
- 全テーブルに監査フィールド（登録日時/登録利用者ID/登録利用者名/登録端末ID/更新日時/更新利用者ID/更新利用者名/更新端末ID）
- `__tablename__` は日本語（例: `"C権限"`, `"M商品"`, `"T配車"`）
- カラム名も日本語（例: `利用者ID`, `配車日付`, `商品名`）

### CRUD Operations (crud1/ and crud2/) - データベース操作関数

カテゴリ別に分離されたCRUD操作関数。監査フィールドの自動付与を提供。

**crud1/** - Core/Common operations (C系, A系):
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

- **init.py** - 初期データ投入（main1.py startup時に呼出）
  - `init_db_data(db: Session)` - C系、A系の初期データを投入
  - C権限: 5件（1=システム管理者, 2=管理者, 3=利用者, 4=閲覧者, 9=その他）
  - C利用者: 5件（admin/leader/user/guest/other + パスワード）
  - C採番: 4件（T配車/T商品棚卸/T商品入庫/T商品出庫、初期値10000）

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

- **Note**: C採番のCRUD操作は `routers1/C採番.py` で直接models1にアクセス（crud1/に独立ファイルなし）

**crud2/** - Application operations (M系, T系):
- **__init__.py** - CRUD modules と utilities をエクスポート
  - M系、T系の各CRUD module をエクスポート
  - `from .init import init_db_data`
  - `from .utils import create_audit_fields, update_audit_fields, get_current_datetime`

- **utils.py** - crud1/utils.py と同一内容（監査フィールドヘルパー）
  - NOTE: crud1とcrud2で同じutils.pyを保持（通常は変更しない）

- **init.py** - 初期データ投入（main2.py startup時に呼出）
  - `init_db_data(db: Session)` - M系、T系の初期データを投入
  - M配車区分: 8件（1〜8: 通常/定期/予備/緊急/特別/巡回/回送/予備）
  - M車両: 8件（1001〜1007 + 1099: １号車〜７号車 + 未定）
  - M商品: 5件（H001〜H004 + H099: 牛飼料/豚飼料/鶏飼料/魚飼料/その他）
  - T配車: 8件（ランダム開始日、今日〜7日先）
  - T商品出庫: 6件（H001商品、明日〜14日以内、数量100〜500）
  - T商品入庫: 3件（H001商品、3日後/8日後/13日後、数量500）
  - T商品棚卸: 1件（H001商品、本日、実棚数量200）

- **M配車区分.py**, **M車両.py**, **M商品.py** - Master CRUD operations
  - 各テーブルの `get_list`, `get_by_ID`, `create`, `update`, `delete` 関数

- **T配車.py**, **T商品入庫.py**, **T商品出庫.py**, **T商品棚卸.py** - Transaction CRUD operations
  - 各テーブルの `get_list`, `get_by_ID`, `create`, `update`, `delete` 関数

**重要**: このプロジェクトでは Database VIEWs は作成しません。V系エンドポイントは全て生SQLクエリで実装されています。

### API Routers (routers1/ and routers2/) - APIエンドポイント

カテゴリ別に分離されたFastAPI routers。日本語エンドポイント、POST中心設計。

**routers1/** - Core/Common endpoints (main1.pyで使用):

- **auth.py** - 認証関連エンドポイント
  - `POST /core/auth/ログイン` - ログイン（認証不要）
    - Request: `schemas.LoginRequest` (`利用者ID`, `パスワード`)
    - Response: `{"access_token": "...", "token_type": "bearer"}`
    - 内部: `crud1.authenticate_C利用者()` で平文パスワード比較
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

- **AコアAI.py** - AコアAI WebSocketエンドポイント
  - `WebSocket /core/ws/AコアAI` - WebSocket接続
  - セッション管理、画面状態/ボタン状態の永続化
  - ストリーミングプロセッサとの統合

- **A会話履歴.py** - A会話履歴CRUDエンドポイント
  - `POST /core/A会話履歴/一覧` - 一覧取得（ソケットID、チャンネルでフィルタ可能）
  - `POST /core/A会話履歴/取得` - 1件取得
  - `POST /core/A会話履歴/登録` - 作成
  - `POST /core/A会話履歴/変更` - 更新
  - `POST /core/A会話履歴/削除` - 削除

**routers2/** - Application endpoints (main2.pyで使用):

- **M配車区分.py**, **M車両.py**, **M商品.py** - M系テーブルCRUDエンドポイント
  - 各テーブルで以下のエンドポイントを提供:
    - `POST /apps/<テーブル名>/一覧` - 一覧取得
    - `POST /apps/<テーブル名>/取得` - 1件取得
    - `POST /apps/<テーブル名>/登録` - 作成
    - `POST /apps/<テーブル名>/変更` - 更新
    - `POST /apps/<テーブル名>/削除` - 削除

- **T配車.py**, **T商品入庫.py**, **T商品出庫.py**, **T商品棚卸.py** - T系テーブルCRUDエンドポイント
  - 各テーブルで以下のエンドポイントを提供:
    - `POST /apps/<テーブル名>/一覧` - 一覧取得
    - `POST /apps/<テーブル名>/取得` - 1件取得
    - `POST /apps/<テーブル名>/登録` - 作成
    - `POST /apps/<テーブル名>/変更` - 更新
    - `POST /apps/<テーブル名>/削除` - 削除
  - T配車とV配車のみ: 開始日付/終了日付でフィルタ可能

- **V配車区分.py**, **V車両.py**, **V商品.py**, **V配車.py** - V系 VIEW query endpoints
  - 各VIEWで以下のエンドポイントを提供:
    - `POST /apps/V<名前>/一覧` - 一覧取得（生SQLクエリ、LEFT JOIN使用）

- **V商品入庫.py**, **V商品出庫.py**, **V商品棚卸.py**, **V商品推移表.py** - V系 VIEW query endpoints
  - 各VIEWで以下のエンドポイントを提供:
    - `POST /apps/V<名前>/一覧` - 一覧取得（生SQLクエリ、複雑な集計含む）
  - V商品推移表: 入庫/出庫/棚卸を統合した推移表

- **S配車_週表示.py**, **S配車_日表示.py** - S系 special processing endpoints
  - `POST /apps/S配車_週表示/一覧` - 週別配車表示（特殊な集計処理）
  - `POST /apps/S配車_日表示/一覧` - 日別配車表示（特殊な集計処理）

## Key Architectural Patterns

### Database VIEWs (V系)

**重要**: このプロジェクトでは **Database VIEWs は作成しません**。

V系エンドポイントは全て生SQLクエリ（SELECT + JOIN）で実装されています:

**How V系 endpoints work:**
1. VIEW routers (`routers1/V*.py`, `routers2/V*.py`) contain raw SQL SELECT statements
2. SQL queries use LEFT JOINs to combine tables (e.g., V利用者 joins C利用者 + C権限)
3. Each V系 router has `/一覧` endpoint that executes SQL directly
4. No database VIEW objects are created

**Example V系 endpoints:**
- `POST /core/V利用者/一覧` - Users joined with permission details via raw SQL
- `POST /apps/V車両/一覧` - Vehicles with joined data
- `POST /apps/V商品/一覧` - Products with calculations
- `POST /apps/V商品推移表/一覧` - Product transaction history aggregations

**To add a new V系 endpoint:**
1. Create router in `routers1/V[名前].py` or `routers2/V[名前].py` with raw SQL query
2. Implement `/一覧` endpoint with `db.execute(text(sql))` 
3. Register router in `main1.py` or `main2.py`
4. Restart server

### Custom ID Generation System (C採番 Table)

The system uses a **centralized sequential ID generator** instead of database AUTOINCREMENT:

**How it works:**
1. `C採番` table stores current ID counters for each table type
2. Each table (e.g., "C権限", "C利用者", "M車両") has a corresponding row in C採番
3. When creating new records, call the ID allocation endpoint to get the next ID
4. Transaction-based increments ensure no ID conflicts

**Implementation:**
- **Allocation API**: `POST /core/C採番/採番` (defined in `routers1/C採番.py`)
- **Request**: `{"採番区分": "C利用者", "採番数": 1}`
- **Response**: Returns next available ID(s) and increments counter atomically
- **Initial setup**: IDs are seeded in `crud1/init.py` during first startup

**When to use:**
- Use for tables that need predictable, sequential IDs (C系, M系 tables)
- Add new entries in `crud1/init.py` when creating new tables that use this system
- Can be bypassed for simple tables that don't need custom ID management

### API Design Pattern

**All CRUD endpoints use POST method** (no GET/PUT/削除 for data operations):
- Function-per-endpoint: `/core/利用者/一覧`, `/core/利用者/作成`, `/core/利用者/更新`, `/core/利用者/削除`
- Unified response format: `{"status": "OK"/"NG", "message": "...", "data": {...}}`
- Request/response keys use Japanese

**Router Registration:**
All routers must be explicitly registered in `main.py`:
```python
from routers import C利用者
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

**Helper functions in `crud1/utils.py` and `crud2/utils.py`:**
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
Logging is initialized in `main.py` startup event via `setup_logging()`.

### WebSocket Support（WebSocket統合）

`ws_manager.py` でWebSocket接続を一元管理。AコアAIのリアルタイム通信を提供。

**WebSocketConnection クラス:**
- 個別のWebSocket接続を管理
- プロパティ:
  - `websocket`: FastAPI WebSocketオブジェクト
  - `socket_id`: ユニークなソケットID（PID + タイムスタンプ + UUID）
  - `is_connected`: 接続状態フラグ
  - `画面状態`: 6つのコンポーネント表示状態（チャット、イメージ、エージェント1〜4）
  - `ボタン状態`: 3つのボタン状態（スピーカー、マイク、カメラ）
  - `モデル設定`: AI modelの設定（app.confからコピー）
  - `streaming_processor`: StreamingProcessor インスタンス
  - `recognition_processor`: 音声認識プロセッサ
  - `audio_data`: 音声データバッファ
- メソッド:
  - `accept()`: WebSocket接続受け入れ
  - `send_json(data)`, `receive_json()`: JSON送受信
  - `close()`: 接続クローズ（プロセッサ停止含む）
  - `update_state(画面, ボタン, manager)`: 画面・ボタン状態更新とセッション保存
  - `update_model_settings(設定, manager)`: モデル設定更新とセッション保存

**WebSocketManager クラス:**
- グローバルな接続マネージャー（シングルトン `ws_manager` インスタンス）
- プロパティ:
  - `active_connections`: アクティブ接続の辞書 (`socket_id` → `WebSocketConnection`)
  - `session_states`: セッション状態の辞書（リロード後も状態復元）
- メソッド:
  - `generate_socket_id()`: PIDベースのユニークID生成
  - `connect(websocket, socket_id, app_conf)`: 接続登録（新規またはリロード）
    - 新規セッション: app.confからモデル設定をコピー
    - 既存セッション: session_statesから状態復元
  - `save_session_state(socket_id, 画面, ボタン, モデル設定, ソース最終更新日時)`: セッション保存
  - `disconnect(socket_id, keep_session)`: 接続切断（オプションでセッション保持）
  - `send_to_socket(socket_id, data)`: 特定ソケットへ送信
  - `broadcast(data)`: 全接続へブロードキャスト
  - `handle_message(socket_id, message)`: クライアントメッセージをストリーミングプロセッサへ転送
  - `get_session_count()`, `get_session_list()`: セッション情報取得

**使用例:**
```python
# routers1/AコアAI.py
from ws_manager import ws_manager

@router.websocket("/ws/AコアAI")
async def websocket_endpoint(websocket: WebSocket, ...):
    socket_id = await ws_manager.connect(websocket, socket_id, request.app.conf)
    try:
        while True:
            message = await connection.receive_json()
            await ws_manager.handle_message(socket_id, message)
    finally:
        await ws_manager.disconnect(socket_id, keep_session=True)
```

**Note**: WebSocket routesは `routers1/AコアAI.py` で実装され、main1.pyに登録済み。

### Reboot機構（内部再起動システム）

main1.pyとmain2.pyに組み込まれた自動再起動機構。

**仕組み:**
1. startup時に `temp/` ディレクトリを作成
2. `temp/reboot1.txt` (main1用) または `temp/reboot2.txt` (main2用) の存在を確認
3. ファイルが存在する場合:
   - ファイルを削除
   - `raise SystemExit("reboot1.txt detected")` でプロセス終了
4. バックグラウンドスレッドで1秒毎にファイル監視
5. ファイルが作成されると `os._exit(0)` でプロセス終了

**使用方法:**
```python
# main1を再起動する場合
with open("backend_server/temp/reboot1.txt", "w") as f:
    f.write("reboot")

# main2を再起動する場合
with open("backend_server/temp/reboot2.txt", "w") as f:
    f.write("reboot")
```

**`_start.py` との連携:**
- `_start.py` がプロセス終了を検知
- 15秒待機後に自動的にサーバーを再起動
- 設定変更や動的なコード再読み込みに使用可能

**実装詳細:**
- main1.py:74-98 でreboot1.txt監視スレッド起動
- main2.py:93-117 でreboot2.txt監視スレッド起動
- デーモンスレッドとして起動（メインプロセス終了時に自動終了）

### Authentication & Security

**JWT Authentication:**
- Algorithm: HS256
- Secret key: `"dummy-secret-key-for-development"` (hardcoded in `auth.py`)
- Token expiration: 60 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Dependency injection: `deps.py::get_現在利用者` validates token and injects current user

**CRITICAL - Passwords are stored in plaintext:**
- Despite bcrypt/passlib being installed, authentication uses plaintext comparison
- See `crud1/C利用者.py` for current implementation
- **Implement password hashing before production use**

**CORS Configuration:**
Allowed origins (in `main.py`):
- `http://localhost:8090` (production Vite server)
- `http://localhost:5173` (default Vite dev server)
- `http://localhost:3000` (alternative port)

## Database & Data Management

### Database Configuration
- **Location**: `backend_server/_data/AiDiy/database.db` (shared by main1 and main2)
- **Schema creation**: Auto-created on startup via `models1.Base.metadata.create_all()` in `main1.py` and `models2.Base.metadata.create_all()` in `main2.py`
- **Initial data seeding**: 
  - Core data: `crud1.init.init_db_data()` in `main1.py` startup event
  - App data: `crud2.init.init_db_data()` in `main2.py` startup event
- **Database VIEWs**: **Not used**. V系 endpoints use raw SQL queries instead
- **Reset database**: Delete `database.db` and restart both FastAPI servers (main1 and main2)

**Important**: This project does NOT use Alembic migrations. Schema changes are managed through SQLAlchemy model updates and database resets.

### Initial Data (Startup Seeding)

**Core data (seeded by main1):**
- **C権限**: 5件（1/2/3/4/9: システム管理者/管理者/利用者/閲覧者/その他）
- **C利用者**: 5件（admin/leader/user/guest/other、パスワードは平文）
- **C採番**: 4件（T配車/T商品棚卸/T商品入庫/T商品出庫）

**Application data (seeded by main2):**
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
- **初期投入の条件**: `crud1.init_db_data()` は **admin が未存在のときだけ** C利用者を投入します。既にDBに admin がいる場合、パスワード変更は自動反映されません。
- **DBファイル**: `backend_server/_data/AiDiy/database.db` を main1 / main2 が共有します。
- **CORS許可リスト**: `main1.py` / `main2.py` は `http://localhost:5173`, `http://localhost:3000`, `http://localhost:8090` のみ許可。ポート変更時は両方更新が必要です。
- **ホットリロード**: `_start.py` 経由の起動は `uvicorn --reload` が付かないため自動リロードされません（再起動 or `temp/reboot1.txt` / `temp/reboot2.txt` を利用）。

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

**認証系 (main1 - port 8091):**
- `POST /core/auth/ログイン`
- `POST /core/auth/ログアウト`
- `POST /core/auth/現在利用者`
- `POST /core/auth/token`（docs 向け）

**コア系 CRUD (main1 - port 8091):**
- `POST /core/C利用者/一覧|get|create|update|delete`
- `POST /core/C権限/一覧|get|create|update|delete`
- `POST /core/C採番/一覧|get|create|update|delete|allocate`

**AI系 (main1 - port 8091):**
- `POST /core/AコアAI/初期化`
- `POST /core/AコアAI/画面変更`
- `POST /core/A会話履歴/一覧|get|create|update|delete`

**アプリ系 CRUD (main2 - port 8092):**
- `POST /apps/M配車区分/一覧|get|create|update|delete`
- `POST /apps/M車両/一覧|get|create|update|delete`
- `POST /apps/M商品/一覧|get|create|update|delete`
- `POST /apps/T配車/一覧|get|create|update|delete`
- `POST /apps/T商品入庫/一覧|get|create|update|delete`
- `POST /apps/T商品出庫/一覧|get|create|update|delete`
- `POST /apps/T商品棚卸/一覧|get|create|update|delete`

**V系（一覧専用）:**
- **Core VIEWs (main1 - port 8091):**
  - `POST /core/V利用者/一覧`
  - `POST /core/V権限/一覧`
  - `POST /core/V採番/一覧`
- **Apps VIEWs (main2 - port 8092):**
  - `POST /apps/V配車区分/一覧`
  - `POST /apps/V車両/一覧`
  - `POST /apps/V商品/一覧`
  - `POST /apps/V配車/一覧`
  - `POST /apps/V商品入庫/一覧`
  - `POST /apps/V商品出庫/一覧`
  - `POST /apps/V商品棚卸/一覧`
  - `POST /apps/V商品推移表/一覧`

**S系（スケジューラー）(main2 - port 8092):**
- `POST /apps/S配車_週表示/一覧`
- `POST /apps/S配車_日表示/一覧`

**例外の GET:**
- `GET /` (main1 & main2)（疎通確認）
- `GET /core/サーバー状態` (main1)（ready/busy の固定レスポンス）

### 一覧検索・ページング
- 一覧 API は基本パラメータなし、`MAX_ITEMS` 上限で取得。
- `T配車` と `V配車` のみ `開始日付`/`終了日付` の絞り込みあり。

## AコアAI Component System (A系) - AI統合システム

AコアAIは、複数のAIサービスを統合したマルチパネルAIインターフェースのバックエンド実装です。

### バックエンド実装

**WebSocketエンドポイント** (`routers1/AコアAI.py`):
- **`WebSocket /core/ws/AコアAI`** - メインWebSocket接続
  - クエリパラメータ: `ソケットID` (リロード時に指定)
  - 接続時:
    1. `ws_manager.connect()` で接続登録
    2. セッション状態を復元または新規作成
    3. 初期化メッセージ送信（画面状態、ボタン状態）
    4. ストリーミングプロセッサ起動
  - メッセージ受信:
    - クライアントからのメッセージを `ws_manager.handle_message()` へ転送
    - ストリーミングプロセッサが処理
  - 切断時:
    - セッション状態を保存（keep_session=True）
    - プロセッサ停止、接続クローズ

**HTTP REST エンドポイント** (廃止済み - 互換性のため残存):
- `POST /core/AコアAI/初期化` - セッション初期化（現在はWebSocketで代替）
- `POST /core/AコアAI/画面変更` - 画面状態保存（現在はWebSocketで代替）

### AI Integration（AI統合モジュール - AコアAI/）

**モジュール構成:**
- **__init__.py** - AコアAI modules エクスポート
- **streaming.py** - `StreamingProcessor` クラス
  - 音声・画像・テキストのストリーミング処理
  - メッセージキュー管理
  - AI API呼び出し統合
- **audio_processing.py** - 音声データ処理
  - `初期化_音声データ()` - 音声バッファ初期化
  - 音声データの分割・バッファリング
- **recognition.py** - 音声認識処理
  - SpeechRecognition ライブラリ統合
  - マイク入力からテキスト変換
- **chat.py** - チャットAI処理
  - テキストベースのAI対話
  - 会話履歴管理
- **code.py** - コードAI処理
  - Claude Agent SDK統合
  - コード生成・実行
- **backup.py** - バックアップ処理

### AI Providers（AI統合）

**対応AIサービス:**
- **Anthropic Claude**
  - パッケージ: `anthropic` (>=0.76.0), `claude-agent-sdk`
  - モデル設定: `CODE_CLAUDE_SDK_MODEL`, `CODE_CLAUDE_CLI_MODEL`
  - エージェント機能: Claude Agent SDKによるコード生成・実行

- **OpenAI**
  - パッケージ: `openai`
  - モデル設定: `CHAT_OPENRT_MODEL`, `LIVE_OPENAI_MODEL`, `LIVE_OPENAI_VOICE`
  - リアルタイム機能: GPT Realtime API対応

- **Google Gemini**
  - パッケージ: `google-genai`
  - モデル設定:
    - Chat: `CHAT_GEMINI_MODEL` (例: `"gemini-3-pro-image-preview"`)
    - Free AI: `CHAT_FREEAI_MODEL` (例: `"gemini-2.5-flash"`)
    - Live AI: `LIVE_GEMINI_MODEL`, `LIVE_GEMINI_VOICE` (音声対応)
  - 音声機能: Native Audio Preview対応

**設定管理:**
- API keys: `_config/RiKi_AiDiy_key.json`
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `GEMINI_API_KEY`
- モデル設定: WebSocketセッション毎にapp.confからコピー（ws_manager.py:186-219）

**会話履歴:**
- **A会話履歴** テーブルでセッション永続化
- フィールド: `ソケットID`, `シーケンス`, `チャンネル`, `メッセージ識別`, `メッセージ内容`, `ファイル名`, `サムネイル画像`
- 監査フィールド付き（登録/更新日時、利用者ID）

**Note**: AI features require valid API keys in the configuration file. Empty keys will cause AI operations to fail.

## Development Commands

**バックエンド依存関係 (Python 3.13 + uv):**
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
# Core server (main1)
cd backend_server
.venv/Scripts/python.exe -m uvicorn main1:app --reload --host 0.0.0.0 --port 8091

# Apps server (main2) - in separate terminal
cd backend_server
.venv/Scripts/python.exe -m uvicorn main2:app --reload --host 0.0.0.0 --port 8092
```

**VS Code Debugging:**
- `backend_server/.vscode/launch.json`: バックエンドのみ（debugpy）

## M配車区分の実装（現行）
- モデル: `models2/M配車区分.py`
- CRUD: `crud2/M配車区分.py`
- API: `routers2/M配車区分.py`
- 一覧ビュー: `routers2/V配車区分.py`（生 SQL で取得）
- スキーマ: `schemas.py` の `M配車区分Base/登録/変更/削除/取得`

使うエンドポイント:
- `POST /apps/M配車区分/一覧|get|create|update|delete`
- `POST /apps/V配車区分/一覧`

注意:
- `M配車区分Update` は `配色枠/配色背景/配色前景` が必須扱いなので、更新時は3色を必ず送る。

## 追加・変更の手順

### 新しいテーブルを追加する（C系 or A系の場合）
1. `models1/` にモデル追加（`__tablename__` は日本語、監査カラム統一）。
2. `models1/__init__.py` に追加して `create_all()` 対象に含める。
3. `schemas.py` に `Base/登録/変更/削除/取得` を追加。
4. `crud1/` に取得/一覧/作成などの関数を追加し `crud1/__init__.py` に公開。
5. `routers1/` に CRUD ルーターを追加。
6. `main1.py` に `include_router` を追加。
7. 初期データが必要なら `crud1/init.py` に追加。
8. 採番が必要なら `C採番` の初期データも追加。

### 新しいテーブルを追加する（M系, T系, S系の場合）
1. `models2/` にモデル追加（`__tablename__` は日本語、監査カラム統一）。
2. `models2/__init__.py` に追加して `create_all()` 対象に含める。
3. `schemas.py` に `Base/登録/変更/削除/取得` を追加。
4. `crud2/` に取得/一覧/作成などの関数を追加し `crud2/__init__.py` に公開。
5. `routers2/` に CRUD ルーターを追加。
6. `main2.py` に `include_router` を追加。
7. 初期データが必要なら `crud2/init.py` に追加。

### 新しい V 系（一覧）を追加する
1. `routers1/V*.py` (C系) or `routers2/V*.py` (M系/T系) を作成し、生 SQL で `SELECT` / `LEFT JOIN` を組み立てる。
2. `count(*)` は同じ FROM/JOIN 条件で取得する。
3. `main1.py` or `main2.py` に `include_router` を追加。

### 新しい機能（API）を追加する
1. `schemas.py` に request/response モデル追加。
2. `crud1/` or `crud2/` に処理を追加（必要ならトランザクション）。
3. `routers1/` or `routers2/` にエンドポイント追加（POST 前提）。
4. `main1.py` or `main2.py` に `include_router` を追加。

## Debugging

**API Testing:**
- FastAPI Swagger UI (Core): http://localhost:8091/docs (interactive API documentation for main1)
- FastAPI Swagger UI (Apps): http://localhost:8092/docs (interactive API documentation for main2)
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

**1. デュアルサーバー起動:**
- **必ず両方のサーバー (main1 + main2) を起動する必要があります**
- `_start.py` を使えば自動で両方起動
- 個別起動の場合: 2つのターミナルで main1.py と main2.py を起動

**2. パスワードセキュリティ:**
- **現在パスワードは平文保存** - 本番環境では必ずハッシュ化実装が必要
- bcrypt/passlibはインストール済みだが未使用
- `crud1/C利用者.py` の `authenticate_C利用者` で平文比較
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
from crud1.utils import create_audit_fields, update_audit_fields

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
from models1 import C利用者

@router.post("/protected/endpoint")
def protected_endpoint(現在利用者: C利用者 = Depends(get_現在利用者)):
    # 現在利用者.利用者ID, 現在利用者.利用者名 などにアクセス可能
    return {"user": 現在利用者.利用者ID}
```

**5. WebSocket使用:**
```python
from ws_manager import ws_manager

@router.websocket("/ws/custom")
async def custom_websocket(websocket: WebSocket, request: Request):
    socket_id = await ws_manager.connect(websocket, None, request.app.conf)
    try:
        while True:
            data = await ws_manager.get_connection(socket_id).receive_json()
            await ws_manager.send_to_socket(socket_id, {"response": "..."})
    finally:
        await ws_manager.disconnect(socket_id)
```

### よくある落とし穴

**1. C採番の使い忘れ:**
- 新規テーブル追加時は `crud1/init.py` または `crud2/init.py` にC採番の初期値を追加
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

## 注意点
- **V 系 API は DB VIEW を作らず、生 SQL で取得します。**
- `T配車/変更` は `配車伝票ID` を **関数パラメータ** として受け取ります（POST bodyとは別）。
- パスワードは平文保存のため、運用前にハッシュ化対応が必要です。
- **両方のサーバー (main1 + main2) を起動する必要があります。** `_start.py` を使えば自動で両方起動します。


