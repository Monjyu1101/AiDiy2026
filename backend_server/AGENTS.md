# backend_server 実装概要

## 本書の目的

このファイルは `backend_server` の構成、設計方針、実装入口を示す概要ドキュメントです。
具体的な追加手順、スキーマ変更、起動、デバッグ、落とし穴は `.aidiy/knowledge` に移動しています。
AI エージェントは、本書に個別手順や一時的な作業メモを追記しないでください。
業務システム機能追加は `../docs/` の開発ガイドを優先し、コアシステム機能調整は `../.aidiy/knowledge/_index.md` を入口にします。

## HowTo 参照先

| 目的 | 参照先 |
|------|--------|
| backend の層構造、Model / Schema / CRUD / Router パターン | [`../.aidiy/knowledge/backend_server,実装パターン.md`](../.aidiy/knowledge/backend_server,実装パターン.md) |
| 開発環境起動、依存関係、DB、Swagger、よくある問題 | [`../.aidiy/knowledge/共通,開発環境運用手順.md`](../.aidiy/knowledge/共通,開発環境運用手順.md) |
| 既存 DB へのスキーマ差分反映 | [`../.aidiy/knowledge/backend_server,スキーマ変更手順.md`](../.aidiy/knowledge/backend_server,スキーマ変更手順.md) |
| C採番と監査フィールド | [`../.aidiy/knowledge/backend_server,C採番と監査フィールド.md`](../.aidiy/knowledge/backend_server,C採番と監査フィールド.md) |
| C利用者パスワード運用 | [`../.aidiy/knowledge/backend_server,C利用者パスワード運用.md`](../.aidiy/knowledge/backend_server,C利用者パスワード運用.md) |
| JWT 認証 | [`../.aidiy/knowledge/backend_server,frontend_web,frontend_avatar,JWT認証フロー.md`](../.aidiy/knowledge/backend_server,frontend_web,frontend_avatar,JWT認証フロー.md) |
| M系マスタ追加 | [`../.aidiy/knowledge/backend_server,M系マスタ追加手順.md`](../.aidiy/knowledge/backend_server,M系マスタ追加手順.md) |
| T系トランザクション追加 | [`../.aidiy/knowledge/backend_server,T系トランザクション追加手順.md`](../.aidiy/knowledge/backend_server,T系トランザクション追加手順.md) |
| V系エンドポイント追加 | [`../.aidiy/knowledge/backend_server,V系エンドポイント追加手順.md`](../.aidiy/knowledge/backend_server,V系エンドポイント追加手順.md) |
| S系スケジューラ追加 | [`../.aidiy/knowledge/backend_server,S系スケジューラ追加手順.md`](../.aidiy/knowledge/backend_server,S系スケジューラ追加手順.md) |
| AIコア WebSocket | [`../.aidiy/knowledge/backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md`](../.aidiy/knowledge/backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md) |
| AIモデル設定 | [`../.aidiy/knowledge/backend_server,frontend_avatar,frontend_web,AIモデル設定変更手順.md`](../.aidiy/knowledge/backend_server,frontend_avatar,frontend_web,AIモデル設定変更手順.md) |
| 設定管理（conf_json / conf_model / conf_path） | [`../.aidiy/knowledge/backend_server,設定管理(conf).md`](../.aidiy/knowledge/backend_server,設定管理(conf).md) |
| Code CLI 追加 | [`../.aidiy/knowledge/backend_server,backend_hermes,frontend_avatar,frontend_web,CodeCLI追加手順.md`](../.aidiy/knowledge/backend_server,backend_hermes,frontend_avatar,frontend_web,CodeCLI追加手順.md) |
| MCP 構成・活用 | [`../.aidiy/knowledge/backend_tools,構成.md`](../.aidiy/knowledge/backend_tools,構成.md)、[`../.aidiy/knowledge/backend_server,backend_tools,MCP活用手順.md`](../.aidiy/knowledge/backend_server,backend_tools,MCP活用手順.md) |

## 概要

`backend_server` は AiDiy の FastAPI backend です。
`core_main.py` と `apps_main.py` の 2 サーバーを持ち、同じ SQLite DB を共有します。

| エントリ | 役割 | ポート |
|----------|------|--------|
| `core_main.py` | C系、A系、認証、files、AIコア | 8091 |
| `apps_main.py` | M系、T系、V系、S系 | 8092 |

## 技術スタック

- Python 3.13 系。
- FastAPI。
- SQLAlchemy。
- SQLite。
- uv。
- Pydantic。
- JWT (`python-jose`)。
- AI SDKs: Anthropic / OpenAI / Google Gemini / Claude Agent SDK など。
- WebSocket。

## 基本方針

- 日本語テーブル名、日本語カラム名、日本語 endpoint を使う。
- CRUD endpoint は POST 中心。
- レスポンスは `status`、`message`、`data` を持つ統一形式にする。
- DB VIEW オブジェクトは作らず、V系 Router の生 SQL で JOIN / 集計する。
- Alembic は使わない。
- 既存DB向けスキーマ差分は起動時の冪等処理で反映する。
- 採番は `C採番` で管理する。
- 監査フィールドは共通 helper を使う。
- フロントエンドのポートを変える場合は、`core_main.py` / `apps_main.py` の CORS 許可リストも合わせて確認する。

## ディレクトリ構成

| パス | 役割 |
|------|------|
| `core_main.py` | Core / Common / AI サーバー |
| `apps_main.py` | 業務アプリサーバー |
| `database.py` | SQLite 接続、Session、Base |
| `deps.py` | 認証 dependency |
| `auth.py` | JWT 生成・検証 |
| `log_config.py` | ログ設定 |
| `conf/` | 設定管理、モデル一覧、JSON 設定 |
| `core_models/` | C系 / A系 SQLAlchemy model |
| `apps_models/` | M系 / T系 SQLAlchemy model |
| `core_schema/` | C系 / A系 Pydantic schema |
| `apps_schema/` | M系 / T系 / S系 Pydantic schema |
| `core_crud/` | C系 / A系 CRUD |
| `apps_crud/` | M系 / T系 / S系 CRUD |
| `core_router/` | Core API / V系 / AIコア |
| `apps_router/` | Apps API / V系 / S系 |
| `AIコア/` | AI provider、WebSocket、Code CLI 連携 |
| `_config/` | `AiDiy_key.json` などの設定 |
| `_data/` | SQLite DB |
| `temp/` | logs、reboot file、一時ファイル |

## core/apps の分担

Core:

- `C権限`
- `C利用者`
- `C採番`
- `A会話履歴`
- `auth`
- `files`
- `AIコア`

Apps:

- `M配車区分`、`M車両`、`M商品`、`M商品分類`、`M取引先分類`、`M取引先`、`M生産区分`、`M生産工程`、`M商品構成`
- `T配車`、`T生産`、`T商品入庫`、`T商品出庫`、`T商品棚卸`
- `V*`
- `S配車_*`、`S生産_*`

## DB と初期化

DB ファイルは `backend_server/_data/AiDiy/database.db` です。
`create_all()` は新規テーブル作成には効きますが、既存テーブルのカラム追加・削除・型変更には効きません。

スキーマ差分、初期データ、DBリセットの判断は `.aidiy/knowledge` の手順を優先してください。

## 設定管理

`backend_server/conf/` が設定管理の中心です。3 クラスで構成されます。

| クラス | 役割 |
|----------|------|
| `conf_path` | 実行パス解決、外部エージェントプロジェクト探索 |
| `conf_json` | `AiDiy_key.json` の読み書き、不足キー補完、即時保存 |
| `conf_models` | AI モデル一覧管理、provider API からの取得とキャッシュ |

詳細は `.aidiy/knowledge/backend_server,設定管理(conf).md` を参照してください。

## AI コア

AIコアは、テキスト、音声、画像、ファイル、コード支援を統合する WebSocket 中心の機能です。

主な領域:

- `AIセッション管理`
- `AIストリーミング処理`
- `AI音声処理`
- `AIチャット*`
- `AIコード*`
- `AIコード_cli.py`
- `AIコード_claude.py`

Code AI は `code1`〜`code6` / `CODE_AI1_NAME`〜`CODE_AI6_NAME` を前提にします。

AI 名の規約:

| 設定キー | 規約 |
|----------|------|
| `CHAT_AI_NAME` | `_chat` で終わる |
| `LIVE_AI_NAME` | `_live` で終わる |
| `CODE_AI1_NAME`〜`CODE_AI6_NAME` | 原則 `_sdk` または `_cli`、例外として `aidiy_hermes` |

比較は完全一致を前提にし、前方一致へ寄せない。

## MCP 連携

MCP サーバー本体は `backend_tools` にあります。
`backend_server` では `_config/AiDiy_mcp.json` を読み、Claude Agent SDK などへ MCP 設定を渡します。

MCP の構成と使い分けは `backendMCP構成.md` と `MCP活用手順.md` を参照してください。

## 実装時の入口

- 新規 M/T/S は `apps_*` と `apps_main.py` を見る。
- 新規 C/A は `core_*` と `core_main.py` を見る。
- 一覧画面用の JOIN は V系 Router を見る。
- 認証付き API は `deps.get_現在利用者` を使う。
- AIコア変更は `core_router/AIコア.py` と `AIコア/` を起点に見る。
- 具体手順は必ず `.aidiy/knowledge/_index.md` から該当 HowTo を開く。
