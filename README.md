# AiDiy - README

## 本書の目的

このREADMEは、**AiDiy プロジェクトの初回セットアップから起動・停止・クリーンアップまでの手順** を説明するドキュメントです。

**対象読者：**
- プロジェクトを初めて触る開発者
- 環境構築が必要な新規メンバー
- プロジェクトの起動・停止方法を確認したい開発者

**関連ドキュメント：**
- **[./CLAUDE.md](./CLAUDE.md)** - Claude Code向けインデックス（クイックスタート、アーキテクチャサマリー）
- **[./AGENTS.md](./AGENTS.md)** - プロジェクト全体方針（基本方針、テーブル命名規則、開発コマンド）
- **[./docs/](./docs/)** - HTML形式の詳細ドキュメント（コーディングルール、実装例など）
- **[./backend_server/AGENTS.md](./backend_server/AGENTS.md)** - バックエンド実装詳細
- **[./frontend_server/AGENTS.md](./frontend_server/AGENTS.md)** - フロントエンド実装詳細

---

## プロジェクト概要

**AiDiy** は、日本語を第一言語とするフルスタックビジネス管理システムです。

**アーキテクチャ：**
- **バックエンド**: FastAPI (Python 3.13) + SQLAlchemy + SQLite
  - **デュアルサーバー構成**: core_main.py (port 8091) + apps_main.py (port 8092)
- **フロントエンド**: Vue 3 + Vite + TypeScript + Pinia
  - **port 8090**

**特徴：**
- データベーステーブル名、カラム名、API endpoints、JSON keys、Vue componentsが全て日本語
- JWT認証（60分有効期限）
- カスタムID生成システム (C採番)
- WebSocket統合 (AIコア)
- 自動再起動機能

---

## 1. セットアップ (_setup.py)

初回起動前に、プロジェクトの依存関係をインストールします。

### 実行方法

```bash
python _setup.py
```

### 実行内容

このスクリプトは**対話形式**で以下の処理を実行します：

1. **バックエンド環境準備 (uv sync)**
   - `backend_server/` の Python 仮想環境を作成
   - `pyproject.toml` に記載された依存関係をインストール
   - **要件**: uv がインストールされていること
   - インストール方法: `irm https://astral.sh/uv/install.ps1 | iex` (PowerShell)

2. **フロントエンド環境準備 (npm install)**
   - `frontend_server/` の Node.js パッケージをインストール
   - `package.json` に記載された依存関係をインストール
   - **要件**: Node.js と npm がインストールされていること
   - インストール方法: https://nodejs.org/

3. **PostgreSQL関連処理（現在はスキップ）**
   - `DATABASE_TYPE="sqlite"` のため、PostgreSQLユーザー確認・初期データ復元・マイグレーション実行はスキップされます
   - PostgreSQL使用時は `_setup.py` 内の `DATABASE_TYPE` を `"postgresql"` に変更してください

### セットアップ完了後

```bash
python _start.py
```

でシステムを起動できます。

---

## 1.5. APIキー設定（公開リポジトリ向け）

APIキーは `backend_server/_config/AiDiy_key.json` に保存されます。  
このフォルダは **公開リポジトリに含めない** 方針のため、`.gitignore` で除外しています。

初回セットアップ時は以下の手順で作成してください。

```bash
copy backend_server\\AiDiy_key.example.json backend_server\\_config\\AiDiy_key.json
```

作成後、`AiDiy_key.json` 内の各APIキーを設定してください。

---

## 2. システム起動 (_start.py)

バックエンドサーバー（2つ）とフロントエンドサーバーを同時起動します。

### 実行方法

**すべて起動（推奨）:**
```bash
python _start.py
```

**バックエンドのみ起動:**
```bash
python _start.py --backend=yes --frontend=no
```

**フロントエンドのみ起動:**
```bash
python _start.py --backend=no --frontend=yes
```

### 実行内容

1. **ポート競合の自動解決**
   - port 8090 (フロントエンド)
   - port 8091 (バックエンドcore)
   - port 8092 (バックエンドapps)
   - 既にプロセスが使用している場合、自動的に停止します

2. **バックエンドサーバー起動**
   - **core_main.py** (port 8091) - Core/Common機能 (C系, A系)
   - **apps_main.py** (port 8092) - Application機能 (M系, T系, V系, S系)
   - 仮想環境 (.venv) があれば使用、なければ uv run で起動

3. **フロントエンドサーバー起動**
   - **Vite dev server** (port 8090)
   - npm run dev を実行

4. **ブラウザ自動起動**
   - http://localhost:8090 を自動的に開きます

5. **プロセス監視と自動再起動**
   - サーバーがクラッシュした場合、15秒後に自動的に再起動します
   - 無限ループ防止のため、再起動間隔は15秒固定

### アクセスURL

起動後、以下のURLでアクセスできます：

| サービス | URL |
|---------|-----|
| **フロントエンド** | http://localhost:8090 |
| **バックエンド (core)** | http://localhost:8091 |
| **バックエンド (apps)** | http://localhost:8092 |
| **API ドキュメント (core)** | http://localhost:8091/docs |
| **API ドキュメント (apps)** | http://localhost:8092/docs |

### デフォルトログイン

- **ユーザー名**: `admin`
- **パスワード**: `********`
  - 他の初期ユーザー（leader/user/guest/other）は [AGENTS.md](./AGENTS.md) を参照

### 実装確認済みの注意点（間違いやすいポイント）

- **初期パスワードの反映タイミング**: `backend_server/core_crud/init.py` の初期データ投入は「**admin が未存在**」のときだけ実行されます。既に DB がある場合、`admin` のパスワードは自動では更新されません。
- **DBファイルの場所**: SQLite は `backend_server/_data/AiDiy/database.db` に作成され、core_main / apps_main で共有されます。
- **_setup.py の案内表示**: セットアップ完了メッセージに `python start.py` と出ますが、実際の起動ファイルは **`_start.py`** です。
- **ポート変更時の連動修正**: フロントエンドのポートを変える場合、`frontend_server/vite.config.ts` に加えて `backend_server/core_main.py` と `backend_server/apps_main.py` の CORS 許可リスト、`_start.py` のポート設定も更新が必要です。

### 停止方法

**Ctrl+C** を押すと、全てのサーバーが正常に停止します。

---

## 3. システム停止 (_stop.py)

実行中のバックエンド・フロントエンドサーバーをポート番号で停止します。

### 実行方法

**すべて停止:**
```bash
python _stop.py
```

**バックエンドのみ停止:**
```bash
python _stop.py --backend=yes --frontend=no
```

**フロントエンドのみ停止:**
```bash
python _stop.py --backend=no --frontend=yes
```

### 実行内容

1. **ポート使用中のプロセス検索**
   - netstat コマンドで該当ポートを使用しているプロセスIDを特定

2. **プロセス強制停止**
   - taskkill コマンドで該当プロセスを強制停止
   - port 8090 (フロントエンド)
   - port 8091 (バックエンドcore)
   - port 8092 (バックエンドapps)

### 使用場面

- `_start.py` が応答しなくなった場合
- ポート競合が発生した場合
- 手動で特定のサーバーだけを停止したい場合

---

## 4. クリーンアップ (_cleanup.py)

プロジェクトを他の担当者に渡す前、または環境をリセットしたい場合に実行します。

### 実行方法

```bash
python _cleanup.py
```

### 実行内容

このスクリプトは**対話形式**で以下のファイル/フォルダを削除します：

#### バックエンド関連

| 対象 | 説明 | デフォルト |
|------|------|----------|
| `__pycache__/` | Pythonバイトコードキャッシュ | 自動削除 |
| `.pytest_cache/` | pytestキャッシュ | 自動削除 |
| `.venv/` | Python仮想環境 | 確認後削除 (y) |
| `logs/` | ログファイル（中身のみ） | 確認後削除 (y) |
| `temp/` | 一時ファイル（中身のみ） | 確認後削除 (y) |
| `backend_server/_data/AiDiy/database.db` | SQLiteデータベース | 確認後削除 (n) |

#### フロントエンド関連

| 対象 | 説明 | デフォルト |
|------|------|----------|
| `node_modules/` | Node.jsパッケージ | 確認後削除 (y) |
| `dist/` | ビルド成果物 | 自動削除 |

#### その他

| 対象 | 説明 | デフォルト |
|------|------|----------|
| `backup/` | バックアップフォルダ | 確認後削除 (y) |

### クリーンアップ後の再セットアップ

クリーンアップ後は、再度セットアップが必要です：

```bash
python _setup.py
```

---

## トラブルシューティング

### ポート競合エラー

**現象:**
```
[ポート 8091] プロセス検出: PID=12345
```

**解決方法:**
1. `_stop.py` を実行してプロセスを停止
2. または `_start.py` が自動的にポートをクリアします

### 文字化け

**現象:**
- コンソール出力やAPIレスポンスが文字化けする

**解決方法:**
- すべてのファイルが **UTF-8 エンコーディング** で保存されているか確認
- `_start.py` は **バックエンド出力を cp932 / フロントエンド出力を UTF-8 としてデコード** しますが、**コンソール自体の設定は変更しません**
- 文字化けが続く場合は、ターミナル側のエンコーディング設定も確認してください（例: Windows Terminal / VS Code 統合ターミナル）

### モジュールが見つからない (ModuleNotFoundError)

**現象:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**解決方法:**
```bash
# バックエンド
cd backend_server
uv sync

# フロントエンド
cd frontend_server
npm install
```

### データベースがロックされている

**現象:**
```
sqlite3.OperationalError: database is locked
```

**解決方法:**
- SQLiteブラウザや他のツールを閉じてからサーバーを起動
- データベースファイルへのアクセスを独占しているプロセスがないか確認

### 401 Unauthorized エラー

**現象:**
- APIリクエストが 401 エラーを返す

**解決方法:**
- JWTトークンの有効期限（60分）が切れています
- http://localhost:8090/ログイン から再ログインしてください

### サーバーが自動再起動を繰り返す

**現象:**
- `_start.py` がサーバーを起動後、15秒ごとに再起動を繰り返す

**解決方法:**
- コンソール出力でエラーメッセージを確認
- Python または Node.js のエラーを修正
- データベース接続エラー、モジュール不足、構文エラーなどが原因の可能性があります

---

## VS Code での起動（F5キー）

VS Code を使用している場合、F5キーでデバッグ起動が可能です。

### 設定ファイル

**ルート `.vscode/launch.json`:**
- `_start.py` を実行する設定

**`backend_server/.vscode/launch.json`:**
- core_main.py または apps_main.py を個別に起動・デバッグ

**`frontend_server/.vscode/launch.json`:**
- Vite dev server を起動し、Chrome でデバッグ

### 使い方

1. VS Code でプロジェクトルートを開く
2. `_start.py` を開く
3. **F5キー** を押す
4. または、「実行とデバッグ」パネルから起動構成を選択

---

## 開発のヒント

### ホットリロード

- **バックエンド**: `_start.py` で起動した場合は **uvicorn の `--reload` が付かない** ため自動リロードされません。  
  変更反映は「再起動」または「`temp/reboot_core.txt` / `temp/reboot_apps.txt` を作成して再起動」です。  
  `--reload` が必要な場合は README 内の **個別起動コマンド** を利用してください。
- **フロントエンド**: コード変更時に自動的にリロードされます（Vite HMR）

### デバッグ

- **バックエンド**: VS Code でブレークポイントを設定してデバッグ可能
- **フロントエンド**: ブラウザの DevTools でデバッグ可能

### ログ

- **バックエンド**: `_start.py` を実行したコンソールに出力されます
  - 色付き出力: `[バックエンド(core)]` / `[バックエンド(apps)]`
- **フロントエンド**: `_start.py` を実行したコンソールに出力されます
  - 色付き出力: `[フロントエンド]`

### API ドキュメント

FastAPI の自動生成ドキュメント（Swagger UI）で API をテストできます：
- http://localhost:8091/docs (core API)
- http://localhost:8092/docs (apps API)

---

## 次のステップ

セットアップと起動が完了したら、以下のドキュメントを参照してください：

1. **[./AGENTS.md](./AGENTS.md)** - プロジェクト全体の方針と基本情報
2. **[./docs/](./docs/)** - HTML形式の詳細ドキュメント（コーディングルール、実装例など）
3. **[./backend_server/AGENTS.md](./backend_server/AGENTS.md)** - バックエンド実装詳細
4. **[./frontend_server/AGENTS.md](./frontend_server/AGENTS.md)** - フロントエンド実装詳細
5. **[./CLAUDE.md](./CLAUDE.md)** - Claude Code (claude.ai/code) 向けインデックス

---

## ライセンスとサポート

プロジェクトの詳細な実装方針やトラブルシューティングについては、上記の関連ドキュメントを参照してください。


