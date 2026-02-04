# プロジェクト全体方針 (AGENTS.md)

## 本書の目的

このファイルは **AiDiy プロジェクト全体の基本方針、アーキテクチャ概要、開発環境のセットアップ手順** を記載した総合ドキュメントです。
本書は **日本語で分かりやすく記載しています**（全書共通の方針として、追記時もこの方針を維持します）。

**対象読者：**
- AiDiyプロジェクトの全体像を把握したい開発者
- 新規メンバーのオンボーディング
- プロジェクトの基本方針や命名規則を確認したい開発者

**このドキュメントの役割：**
- プロジェクト全体の概要と目的の理解
- 日本語命名規約とテーブル命名規則の把握
- 開発環境のセットアップとコマンドの参照
- バックエンドとフロントエンドの詳細ドキュメントへのナビゲーション

**バックエンドサーバーとフロントエンドサーバーの詳細は別ドキュメント：**
- **バックエンド（FastAPI + SQLAlchemy + SQLite）の実装詳細** → [backend_server/AGENTS.md](./backend_server/AGENTS.md)
- **フロントエンド（Vue 3 + Vite + TypeScript）の実装詳細** → [frontend_server/AGENTS.md](./frontend_server/AGENTS.md)

**関連ドキュメント：**
- **[./CLAUDE.md](./CLAUDE.md)** - Claude Code向けインデックス（クイックスタート、アーキテクチャサマリー）
- **[./docs/](./docs/)** - HTML形式の詳細ドキュメント（コーディングルール、実装例など）
- **[./backend_server/AGENTS.md](./backend_server/AGENTS.md)** - バックエンド実装の完全ガイド
- **[./frontend_server/AGENTS.md](./frontend_server/AGENTS.md)** - フロントエンド実装の完全ガイド

**このファイルの内容：**
- AiDiyとは何か（プロジェクトの目的と特徴）
- プロジェクト概要と基本方針
- 日本語命名規約とテーブル命名規則
- アーキテクチャ概要（デュアルサーバー構成、主要な設計パターン）
- 開発コマンド（起動方法、依存関係管理）
- アクセスURL・ポート設定
- よくある問題と解決方法
- テスト手順
- バックエンド/フロントエンドドキュメントの内容インデックス

**コーディングルール・開発フローは別ドキュメント：**
- **[./docs/03_コーディングルール/](./docs/03_コーディングルール/_index.html)** - 詳細なコーディングルール、命名規則、ベストプラクティス
- **[./docs/04_フロントエンド画面追加例/](./docs/04_フロントエンド画面追加例/_index.html)** - フロントエンドCRUD画面追加手順

---

## 📚 ドキュメントリソース（docs/フォルダ）

プロジェクトの詳細なドキュメントは **`docs/`フォルダ** にHTML形式で整備されています。

| フォルダ | 内容 |
|---------|------|
| **[docs/00_AiDiyシステムの歩き方/](./docs/00_AiDiyシステムの歩き方/_index.html)** | システム全体の概要、FAQ |
| **[docs/01_明日のために！その１_バックエンド_M配車区分実装例/](./docs/01_明日のために！その１_バックエンド_M配車区分実装例/_index.html)** | バックエンドAPI実装例 |
| **[docs/02_明日のために！その２_バックエンド_M配車区分テスト例/](./docs/02_明日のために！その２_バックエンド_M配車区分テスト例/_index.html)** | バックエンドテスト手順 |
| **[docs/03_コーディングルール/](./docs/03_コーディングルール/_index.html)** | 命名規則、ベストプラクティス、レビューチェックリスト |
| **[docs/04_フロントエンド画面追加例/](./docs/04_フロントエンド画面追加例/_index.html)** | フロントエンドCRUD画面追加手順 |

**開発時は必ず参照してください。** 特にコーディングルール（docs/03）は必読です。

---

## AiDiyとは

**AiDiy** (AI Do-It-Yourself) は、**日本語を第一言語とするフルスタックビジネス管理システムの開発フレームワーク/テンプレート** です。

### プロジェクトの目的

1. **日本語ネイティブな開発環境の提供**
   - データベーステーブル名、カラム名、API endpoints、JSON keys、Vue components 全てが日本語
   - 日本語話者にとって理解しやすく、ビジネスドメインと完全に一致したコード

2. **実用的なビジネスアプリケーションのテンプレート**
   - 権限管理、マスタデータ管理、トランザクション管理の実装例
   - CRUD操作、検索、ソート、ページングなどの標準機能
   - カスタマイズ可能な基盤システム

3. **AI統合の実験場**
   - マルチベンダーAI対応（Anthropic Claude, OpenAI, Google Gemini）
   - WebSocketによるリアルタイムAI対話
   - 音声・画像・テキスト統合インターフェース (AIコア)

### 提供される機能

**開発フレームワーク/テンプレートシステムとして以下のサンプル実装を提供：**

- **C系 (Core/Common)** - User and permission management
  - C権限 - 権限マスタ
  - C利用者 - 利用者マスタ（JWT認証）
  - C採番 - カスタムID生成システム

- **M系 (Master)** - Master data management
  - M配車区分 - 配車区分マスタ
  - M車両 - 車両マスタ
  - M商品 - 商品マスタ

- **T系 (Transaction)** - Transaction management
  - T配車 - 配車トランザクション
  - T商品入庫/出庫/棚卸 - 在庫管理トランザクション

- **V系 (View)** - Complex query views
  - V利用者、V車両、V商品 - マスタJOIN表示
  - V商品推移表 - トランザクション集計

- **S系 (Scheduler/Special)** - Special processing
  - S配車_週表示、S配車_日表示 - スケジュール表示

- **A系 (AI/Advanced)** - AI integration
  - AIコア - Multi-panel AI interface
  - A会話履歴 - Conversation history storage

- **X系 (Experimental)** - Test/example features
  - Xテトリス、Xインベーダー、Xリバーシ - ゲーム実装例

### 対象ユーザー

- 日本語でビジネスアプリケーションを開発したいチーム
- FastAPI + Vue 3 のフルスタック開発を学びたい開発者
- AI統合の実装例を探している開発者
- 管理画面・CRUD システムのテンプレートを必要とするプロジェクト

## プロジェクトの特徴

### 1. 日本語ファースト設計

**全レイヤーで日本語識別子を使用：**
- Database: テーブル名 `C権限`, カラム名 `利用者ID`
- API: Endpoints `/core/利用者/一覧`, JSON keys `{"利用者名": "admin"}`
- フロントエンド: コンポーネント `C利用者一覧.vue`, ルート `/C管理/C利用者/一覧`
- Code: Variables `利用者名`, `配車日付`, `商品名`

**メリット：**
- ビジネスドメインとコードの完全な一致
- 日本語話者にとって理解しやすい
- ドキュメントとコードのギャップがない

### 2. デュアルサーバーアーキテクチャ

**2つの独立したFastAPIサーバー：**
- **core_main.py** (port 8091) - Core/Common features (C系, A系)
- **apps_main.py** (port 8092) - Application features (M系, T系, V系, S系)
- 同じSQLiteデータベースを共有
- Vite Proxy で `/core/*` と `/apps/*` を自動振り分け

**メリット：**
- 機能のモジュラー化
- 独立したデプロイとスケーリング
- 開発時のサーバー再起動が高速

### 3. POST中心のAPI設計

**全CRUDエンドポイントはPOSTメソッド：**
- `/core/利用者/一覧` (POST) - 一覧取得
- `/core/利用者/取得` (POST) - 1件取得
- `/core/利用者/登録` (POST) - 作成
- `/core/利用者/変更` (POST) - 更新
- `/core/利用者/削除` (POST) - 削除

**統一レスポンス形式：**
```json
{
  "status": "OK" | "NG",
  "message": "メッセージ",
  "data": {...}
}
```

### 4. Database VIEWsを使わないアーキテクチャ

- V系エンドポイントは生SQLクエリ（SELECT + LEFT JOIN）で実装
- データベースVIEWオブジェクトは作成しない
- 柔軟性と保守性を優先

### 5. カスタムID生成システム (C採番)

- AUTOINCREMENTを使用しない
- C採番テーブルで各テーブルのID採番を管理
- トランザクション保護された予測可能なID生成

### 6. 監査フィールドの標準化

**全テーブルに自動付与：**
- 登録日時、登録利用者ID、登録利用者名、登録端末ID
- 更新日時、更新利用者ID、更新利用者名、更新端末ID
- 共通ヘルパー関数で統一生成

### 7. No Alembic Migrations

- マイグレーションツール不使用
- SQLAlchemyモデル更新 + データベースリセットで対応
- シンプルで迅速な開発サイクル

### 8. AI統合システム (AIコア)

**マルチベンダーAI対応：**
- Anthropic Claude (claude-agent-sdk)
- OpenAI (GPT models)
- Google Gemini (Native Audio Preview)

**WebSocketリアルタイム通信：**
- ストリーミングレスポンス
- 音声・画像・テキスト統合
- セッション永続化（リロード対応）

### 9. qTublerシステム（カスタムテーブル）

- UIフレームワーク不使用
- カスタムグリッドレイアウトテーブル
- ソート、ページング、行選択機能
- 統一されたUI/UX

### 10. Reboot機構（内部再起動システム）

- `temp/reboot1.txt` または `temp/reboot2.txt` でサーバー再起動
- `_start.py` による自動プロセス監視
- 設定変更やコード再読み込みに便利

### 11. 実用的な管理画面とサンプルシステム

**完全に動作する管理画面を実装：**
- 権限管理画面（C権限）- 権限マスタのCRUD
- 利用者管理画面（C利用者）- ユーザーマスタのCRUD
- 採番管理画面（C採番）- ID採番設定のCRUD
- マスタデータ管理（M配車区分、M車両、M商品）
- トランザクション管理（T配車、T商品入庫/出庫/棚卸）
- スケジュール表示（S配車_週表示、S配車_日表示）
- ビュー表示（V商品推移表）

**サンプルシステムとして：**
- 車両配車管理システムの実装例
- 商品在庫管理システムの実装例
- 各機能が実際に動作し、カスタマイズ可能
- 統一されたUI/UX（qTublerテーブル、共通ダイアログ）

**実験的機能（X系）：**
- Xテトリス - Canvas APIの実装例
- Xインベーダー - ゲームロジックの実装例
- Xリバーシ - アルゴリズムの実装例
- X自己紹介 - 静的コンテンツの実装例

**メリット：**
- すぐに動かせる完成品
- カスタマイズのベースとして使用可能
- 実装パターンの学習教材として最適
- プロトタイプ作成が迅速

## 概要

Full-stack business management system with JWT authentication, using FastAPI (Python 3.13) + SQLite backend and Vue.js 3 frontend.

日本語標準のVue 3フロントエンド + 日本語APIのFastAPIバックエンド。DBはSQLiteを採用し、管理画面中心の構成。

## 基本方針

- 画面/URL/JSONキー/識別子は日本語を原則とする
- 文字コードはUTF-8固定
- 全ファイルはUTF-8エンコーディング必須
- DBテーブルから取得/保存する項目は、できるだけDB項目名と同じ変数名を使う
- DB項目名 / API上の項目名 / ソケット上の項目名は、できるだけ同じ変数名を使う
- request / query / item / items / total / limit などの一般名は英字のまま使用する
- ファイル内容確認はUTF-8指定で読む（例: `Get-Content -Encoding UTF8`）

## テーブル命名規則

- `C` = Core/Common tables (C権限, C利用者, C採番)
- `M` = Master tables (M車両, M商品, M配車区分)
- `T` = Transaction tables (T配車, T商品入庫, T商品出庫, T商品棚卸)
- `V` = Database VIEWs (V利用者, V車両, V商品)
- `S` = Scheduler/Special processing (S配車_週表示, S配車_日表示)
- `A` = AI/Advanced features (AIコア, A会話履歴)
- `X` = Experimental/Test features

## Japanese Naming Convention

This project uses Japanese identifiers extensively:

- **Database**: Table names (C権限, C利用者), column names (利用者ID, パスワード)
- **API**: JSON keys in requests/responses (ユーザー名, 権限ID)
- **API endpoints**: `/core/利用者/一覧`, `/core/権限/作成`
- **Code**: Variables, class attributes, function parameters use Japanese where it clarifies business domain concepts
- **Vue files**: File names, route paths, component names use Japanese
- **File Encoding**: All files must be UTF-8

When adding new code, follow this convention for business logic. System/framework code can use English.

**Rationale**: Improves clarity for Japanese-speaking stakeholders and aligns code with business domain.

## Architecture Overview

This project consists of three main parts:

### バックエンド (backend_server/)

FastAPI + SQLAlchemy + SQLite backend with Japanese API endpoints and JWT authentication.

**技術スタック：**
- Python 3.13 + uv (package manager)
- FastAPI + Uvicorn (ASGI server)
- SQLAlchemy (ORM, no Alembic)
- SQLite (single file database)
- python-jose (JWT authentication, HS256)
- AI SDKs: anthropic, openai, google-genai, claude-agent-sdk

**主要な設計パターン：**
- デュアルサーバーアーキテクチャ (core_main.py + apps_main.py)
- POST中心のAPI設計（統一レスポンス形式）
- Database VIEWsを使わない（生SQLクエリ）
- カスタムID生成システム (C採番)
- 監査フィールドの標準化
- Reboot機構（内部再起動システム）
- 構成管理システム (conf/)
- WebSocket統合 (AIコア/AIソケット管理.py)
- AI統合機能 (AIコア/)

**詳細は [backend_server/AGENTS.md](backend_server/AGENTS.md) を参照**

**backend_server/AGENTS.md に記載されている内容：**

<details>
<summary>📚 バックエンドドキュメントの内容（クリックで展開）</summary>

- **本書の目的** - ドキュメントの対象読者と役割
- **まず知っておくこと（基本原則）** - 技術スタック、命名規約、API設計原則
- **実装の全体像と特徴** - デュアルサーバーアーキテクチャ、11項目の主要な特徴
- **バックエンド構成** - ファイル構成と役割
  - Core Files: core_main.py/apps_main.py の詳細説明
  - 共通データベースモジュール (database.py)
- 共通スキーマ (core_schema.py / apps_schema.py - 分割管理)
  - 共通認証モジュール (auth.py, deps.py)
  - 共通ログモジュール (log_config.py)
- 共通WebSocketモジュール (AIコア/AIソケット管理.py)
  - 構成管理システム (conf/ - ConfigManager singleton)
  - データ・設定ディレクトリ (_data/, _config/, temp/)
  - Models (core_models/, apps_models/ - SQLAlchemy ORM)
  - CRUD Operations (core_crud/, apps_crud/ - データベース操作関数、監査フィールドヘルパー、初期データ投入)
  - API Routers (core_router/, apps_router/ - FastAPI endpoints)
- **Key Architectural Patterns**
  - Database VIEWs (V系は生SQLクエリで実装)
  - Custom ID Generation System (C採番テーブルによる採番管理)
  - API Design Pattern (POST中心、統一レスポンス)
  - Audit Fields Pattern (監査フィールドの自動付与)
  - Logging System (EndpointFilter)
  - WebSocket Support (WebSocketManager, セッション管理)
  - Reboot機構（temp/reboot1.txt, temp/reboot2.txt）
  - Authentication & Security (JWT, 平文パスワード警告)
- **Database & Data Management**
  - Database Configuration (SQLite設定、テーブル自動作成)
  - Initial Data (初期データ投入の詳細)
  - Default Login Credentials (5件のユーザー)
- **API エンドポイント**
  - レスポンス形式（共通）
  - エンドポイント一覧（認証系、コア系CRUD、AI系、アプリ系CRUD、V系、S系）
  - 一覧検索・ページング
- **AIコア Component System (A系)**
  - バックエンド実装（WebSocketエンドポイント、HTTP REST エンドポイント）
  - AI Integration (AIソケット管理.py, AIストリーミング処理.py, AI音声処理.py, AI音声認識.py, AIチャット*.py, AIライブ*.py, AIコード*.py, AI内部ツール.py)
  - AI Providers (Anthropic Claude, OpenAI, Google Gemini)
  - 設定管理（API keys、モデル設定）
  - 会話履歴（A会話履歴テーブル）
- **Development Commands** - backend固有のコマンド
- **追加・変更の手順**
  - 新しいテーブルを追加する（C系/A系の場合）
  - 新しいテーブルを追加する（M系/T系/S系の場合）
  - 新しいV系（一覧）を追加する
  - 新しい機能（API）を追加する
- **デバッグ** - APIテスト、バックエンドログ、DB検証
- **実装の注意点とベストプラクティス**
  - 必須の注意事項 (5項目)
  - ベストプラクティス (5項目、コード例付き)
  - よくある落とし穴 (5項目)

</details>

### フロントエンド (frontend_server/)

Vue 3 + Vite + TypeScript frontend with Japanese component names and routes.

**技術スタック：**
- Vue 3 Composition API + script setup
- Vite (build tool)
- TypeScript (strict mode disabled)
- Pinia (state management)
- Vue Router 4 (日本語URL対応)
- Axios (HTTP client with interceptors)
- dayjs (日付処理)

**主要な設計パターン：**
- シングルページアプリケーション (SPA)
- カテゴリベースのコンポーネント構成
- 統一されたCRUD画面パターン
- qTublerシステム（カスタムテーブルコンポーネント）
- 共通ダイアログシステム (qAlert, qConfirm, qColorPicker)
- レイアウトシステム (_Layout, _TopBar, _TopMenu)
- WebSocket統合 (AIコアWebSocket)

**詳細は [frontend_server/AGENTS.md](frontend_server/AGENTS.md) を参照**

**frontend_server/AGENTS.md に記載されている内容：**

<details>
<summary>📚 フロントエンドドキュメントの内容（クリックで展開）</summary>

- **本書の目的** - ドキュメントの対象読者と役割
- **まず知っておくこと（基本原則）** - 技術スタック、命名規約、TypeScript設定、コンポーネント設計原則
- **実装の全体像と特徴** - 12項目の主要な特徴、No UI Framework説明
- **フロントエンド構成** - ファイル構成と役割
  - Core Files: main.ts, App.vue, vite.config.ts, tsconfig.json の詳細
  - Routing (router/ - Vue Router設定、認証ガード、日本語URL対応、全ルート一覧)
  - State Management (stores/ - Pinia auth store の詳細、State/取得ters/Actions)
  - API Client (api/ - Axios client, WebSocket client の詳細)
  - Component Structure (components/ - 全コンポーネントの説明)
    - Layout Components (_Layout, _TopBar, _TopMenu)
    - Shared Components (_Modal, qAlertDialog, qConfirmDialog, qColorPickerDialog, qTubler, qTublerFrame, qAlert.ts)
    - Feature Components (C管理/, Mマスタ/, Tトラン/, Sスケジューラー/, Vビュー/, AIコア/, Xテスト/)
  - Styles (assets/ - グローバルCSS、メニューCSS、Scoped Styles)
- **qTublerシステム（カスタムテーブルコンポーネント）**
  - コンポーネント構成 (qTubler.vue, qTublerFrame.vue)
  - Props, Emits, Column型定義
  - 使用例（コード付き）
  - qTublerの5つの特徴
- **AIコア Component System (A系)**
  - Main container (AIコア.vue - セッション管理、グリッドレイアウト)
  - Sub components (チャット、イメージ、エージェント)
  - Component communication pattern
  - Image capture flow
  - Layout behavior (1-6パネル)
  - WebSocket統合
- **Authentication Flow** - フロントエンド視点の認証フロー
- **Development Commands** - frontend固有のコマンド
- **新規テーブル/ビュー/機能 追加手順**
  - 新規テーブル（管理系のCRUD画面）
  - 新規V系（参照系の一覧）
  - 新規機能（カテゴリ追加）
- **Debugging** - Browser DevTools、VS Code debugging
- **実装の注意点とベストプラクティス**
  - 必須の注意事項 (6項目)
  - ベストプラクティス (6項目、コード例付き)
  - よくある落とし穴 (5項目)

</details>

## Development Commands

### Starting the Application

**Recommended: Use the unified launcher**
```bash
python _start.py
```
This launcher:
- Kills any processes on ports 8090/8091/8092
- Starts FastAPI backend core_main (port 8091 - コア機能)
- Starts FastAPI backend apps_main (port 8092 - アプリ機能)
- Starts Vite dev server (port 8090)
- Opens browser to http://localhost:8090
- Monitors servers and auto-restarts crashed processes after 15 seconds
- Stops gracefully on Ctrl+C
- Sets console encoding for Windows

**Individual servers:**
```bash
# バックエンド Core のみ（プロジェクトルートから）
cd backend_server
.venv/Scripts/python.exe -m uvicorn core_main:app --reload --host 0.0.0.0 --port 8091

# バックエンド Apps のみ（プロジェクトルートから）
cd backend_server
.venv/Scripts/python.exe -m uvicorn apps_main:app --reload --host 0.0.0.0 --port 8092

# フロントエンドのみ（プロジェクトルートから）
cd frontend_server
npm run dev
```

**VS Code Debugging:**
Press F5 in VS Code:
- Root `.vscode/launch.json`: Runs `_start.py` with full stack
- `backend_server/.vscode/launch.json`: バックエンドのみ（debugpy）
- `frontend_server/.vscode/launch.json`: フロントエンドのみ（Chromeデバッグ）

### バックエンドのコード変更を反映する方法

`_start.py` で起動した場合、uvicorn の `--reload` フラグが付かないため、コード変更が自動で反映されません。

**方法1: Reboot機構を使う（推奨）**
```bash
# core_main.py を再起動
echo. > backend_server/temp/reboot1.txt

# apps_main.py を再起動
echo. > backend_server/temp/reboot2.txt
```

**方法2: 個別起動で --reload を有効化**
```bash
cd backend_server
.venv/Scripts/python.exe -m uvicorn core_main:app --reload --host 0.0.0.0 --port 8091
```

**方法3: _start.py を再起動**
```bash
# Ctrl+C で停止してから
python _start.py
```

### Dependency Management

**バックエンド（Python 3.13 + uv）:**
```bash
cd backend_server
uv sync          # Install/sync dependencies from pyproject.toml
uv add <package> # Add new dependency
```

**フロントエンド（Node.js + npm + TypeScript）:**
```bash
cd frontend_server
npm install        # Install dependencies
npm run dev        # Start dev server
npm run build      # Type-check and build for production
npm run preview    # Preview production build
npm run type-check # Run TypeScript type checking without building
```

### Database Management

**Database Location:**
```
backend_server/_data/AiDiy/database.db
```

**Database Reset (recreate all tables and initial data):**
1. Stop all servers (Ctrl+C on `_start.py` or `python _stop.py`)
2. Delete `backend_server/_data/AiDiy/database.db`
3. Restart servers (`python _start.py`)
4. Tables and initial data auto-created on startup

**注意:** 初期データ（admin など）は「該当レコードが未存在」の場合のみ投入されます。既存DBでは自動更新されません。

**Inspect Database:**
- Use SQLite Browser or DBeaver
- Close DB tools before starting servers (avoid "database locked" errors)

### API Testing

**FastAPI Swagger UI:**
- Core API: http://localhost:8091/docs
- Apps API: http://localhost:8092/docs

**Using Swagger UI:**
1. Click "Authorize" button (top right)
2. Enter JWT token from localStorage (login first at http://localhost:8090)
3. Test endpoints interactively
4. All CRUD endpoints use POST method

## Access URLs & Port Configuration

- フロントエンド: http://localhost:8090
- バックエンドAPI（Core - core_main）: http://localhost:8091
- バックエンドAPI（Apps - apps_main）: http://localhost:8092
- API Documentation (Core): http://localhost:8091/docs (FastAPI Swagger UI)
- API Documentation (Apps): http://localhost:8092/docs (FastAPI Swagger UI)

**Default Login Credentials** (seeded on first startup):
- Admin: `admin` / `********`
- Manager: `leader` / `secret`
- User: `user` / `user`
- Guest: `guest` / `guest`
- Other: `other` / `other`

**実装確認済みの補足（間違いやすい点）:**
- **初期データ投入の条件**: `core_crud.init_db_data()` は **admin が未存在のときだけ** C利用者を投入します。既存DBでは自動更新されません。
- **DBファイル位置**: `backend_server/_data/AiDiy/database.db`（core_main / apps_main で共有）。
- **_start.py の起動挙動**: `uvicorn --reload` は付かないため、バックエンドは自動リロードされません（手動再起動 or reboot1/2.txt を利用）。
- **ポート変更の連動修正**: `frontend_server/vite.config.ts` の `server.port` を変える場合、`backend_server/core_main.py` と `apps_main.py` の CORS 許可リスト、`_start.py` のポート設定も更新が必要。
- **_setup.py の案内文**: 画面表示は `python start.py` ですが、実ファイルは **`_start.py`** です。

**Vite Proxy Configuration** (`frontend_server/vite.config.ts`):
- `/core/*` → `http://127.0.0.1:8091` (core_main - コア機能)
- `/apps/*` → `http://127.0.0.1:8092` (apps_main - アプリ機能)

**CORS allowed origins** (`backend_server/core_main.py` and `apps_main.py`):
- `http://localhost:8090` (production Vite server)
- `http://localhost:5173` (default Vite dev server)
- `http://localhost:3000` (alternative port)

**Port conflicts**: `_start.py` auto-kills processes on 8090/8091/8092. To manually kill:
```bash
# Windows
netstat -ano | findstr :8091
taskkill /PID <pid> /F

# Linux/Mac
lsof -ti:8091 | xargs kill -9
```

## Common Issues

| Issue | Symptoms | Solution |
|-------|----------|----------|
| **Port conflicts** | `_start.py` fails with "address already in use" | `_start.py` auto-kills processes on 8090/8091/8092, but may fail if unresponsive. Manually kill with `taskkill /F /PID <pid>` on Windows |
| **Japanese characters garbled** | 文字化け in console or UI | Ensure all files are UTF-8 encoded. `_start.py` は出力を cp932/UTF-8 でデコードしますが、**コンソール設定は変更しません** |
| **401 Unauthorized** | API calls fail with 401, redirected to login | JWT token expired or invalid. Check `localStorage` for token, re-login if needed |
| **CORS errors** | "blocked by CORS policy" in browser console | Verify origin in `core_main.py` and `apps_main.py` allowed list: `localhost:8090`, `localhost:5173`, `localhost:3000` |
| **Module not found (Python)** | `ModuleNotFoundError` when starting backend | Run `cd backend_server && uv sync` to install dependencies |
| **Module not found (npm)** | Vite build errors or missing packages | Run `cd frontend_server && npm install` |
| **Database locked** | `sqlite3.OperationalError: database is locked` | Close any SQLite browser/tools accessing `database.db` |
| **Tables not created** | API errors about missing tables | Restart backend servers (core_main and apps_main) - tables auto-create on startup |
| **Auto-restart loop** | `_start.py` restarts servers repeatedly | Check for Python/Node errors in console. Servers restart 15 seconds after crash. Fix the underlying error to stop the loop |
| **Initial data not updating** | admin password or initial records not changing | Initial data only inserts when DB is empty or specific records don't exist. To force re-initialization: stop servers → delete `backend_server/_data/AiDiy/database.db` → restart servers |
| **Vue component shows as text** | Japanese component name appears as text in browser | Japanese tags are invalid in HTML. Use `<component :is="日本語コンポーネント名" />` instead of `<日本語コンポーネント名 />` |
| **Database reset needed** | Need to recreate tables from scratch | Stop all servers → Delete `backend_server/_data/AiDiy/database.db` → Restart servers (tables and initial data auto-created) |
| **WebSocket接続エラー (AIコア)** | `LiveAI未初期化のため音声送信不可: ws-xxxx` | WebSocket接続と LiveAI 初期化のタイミング問題。フロントエンドで接続→設定送信の順序を確認。バックエンドログで初期化ステップを確認。詳細は [backend_server/AGENTS.md](./backend_server/AGENTS.md) の「AIコア Component System」セクション参照 |
| **コード変更が反映されない** | バックエンドのコードを変更しても動作が変わらない | `_start.py` で起動した場合は `--reload` なし。`temp/reboot1.txt` または `temp/reboot2.txt` を作成して再起動、または上記「バックエンドのコード変更を反映する方法」参照 |

## Testing

No automated test suites are configured. Testing is done manually:
- **API testing**: FastAPI Swagger UI at http://localhost:8091/docs
- **UI testing**: Browser at http://localhost:8090
- **Sample data**: Auto-seeded on first startup via `crud/init.py`

## Detailed Implementation

実装の詳細は各サブAGENTS.mdを参照：

- **[./backend_server/AGENTS.md](./backend_server/AGENTS.md)** - バックエンド実装詳細（API/DB/認証/初期データ/追加手順）
- **[./frontend_server/AGENTS.md](./frontend_server/AGENTS.md)** - フロントエンド実装詳細（画面/routing/認証/追加手順）

## Additional Notes

**File Encoding Requirement:**
- **ALL files MUST be UTF-8 encoded** to support Japanese identifiers throughout the codebase
- Windows コンソールのエンコーディングは `_start.py` が変更しないため、必要に応じてターミナル側で調整

**Critical Development Pattern:**
- Vue component tags must use ASCII names
- Use `<component :is="日本語コンポーネント名" />` syntax for dynamic Japanese component names
- File content checks should specify UTF-8 (e.g., `Get-Content -Encoding UTF8`)

**No Alembic Migrations:**
- This project does NOT use Alembic migrations
- Schema changes are managed through SQLAlchemy model updates and database resets
- The `samplePY/` implementation uses Alembic if migrations are needed

**Database VIEWs:**
- VIEWs are not created as database objects in this implementation
- VIEW endpoints (`core_router/V*.py`, `apps_router/V*.py`) use raw SQL queries with JOINs
- Each VIEW router directly executes SELECT statements to fetch joined data

