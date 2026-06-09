# プロジェクト全体方針 (AGENTS.md)

## 本書の目的

このファイルは **AiDiy プロジェクト全体の実装概要、基本方針、アーキテクチャ概要** を示す入口ドキュメントです。
具体的な起動手順、追加手順、検証手順、トラブル対応などの HowTo は `.aidiy/knowledge/` に集約します。

本書は日本語で分かりやすく記載します。追記時も同じ方針を維持してください。
AI エージェントは、本書に個別手順や一時的な作業メモを追記しないでください。

## HowTo の参照先

ファイル操作や実装作業を伴う場合は、まず `.aidiy/knowledge/_index.md` を確認してください。
業務システム機能追加は `docs/` の開発ガイドを優先し、コアシステム機能調整は `.aidiy/knowledge/_index.md` を入口にします。

| 目的 | 参照先 |
|------|--------|
| ナレッジ全体の入口 | [`.aidiy/knowledge/_index.md`](./.aidiy/knowledge/_index.md) |
| 起動、依存関係、DB、API確認、よくある問題 | [`.aidiy/knowledge/共通,開発環境運用手順.md`](./.aidiy/knowledge/共通,開発環境運用手順.md) |
| Backend API / DB 追加 | [`.aidiy/knowledge/backend_server,M系マスタ追加手順.md`](./.aidiy/knowledge/backend_server,M系マスタ追加手順.md)、[`.aidiy/knowledge/backend_server,T系トランザクション追加手順.md`](./.aidiy/knowledge/backend_server,T系トランザクション追加手順.md)、[`.aidiy/knowledge/backend_server,V系エンドポイント追加手順.md`](./.aidiy/knowledge/backend_server,V系エンドポイント追加手順.md)、[`.aidiy/knowledge/backend_server,S系スケジューラ追加手順.md`](./.aidiy/knowledge/backend_server,S系スケジューラ追加手順.md) |
| スキーマ変更 | [`.aidiy/knowledge/backend_server,スキーマ変更手順.md`](./.aidiy/knowledge/backend_server,スキーマ変更手順.md) |
| 設定管理 (conf/) | [`.aidiy/knowledge/backend_server,設定管理(conf).md`](./.aidiy/knowledge/backend_server,設定管理(conf).md) |
| frontend_web 画面追加 | [`.aidiy/knowledge/frontend_web,画面追加手順.md`](./.aidiy/knowledge/frontend_web,画面追加手順.md) |
| frontend_web Router / Store パターン | [`.aidiy/knowledge/frontend_web,Vue Routerパターン.md`](./.aidiy/knowledge/frontend_web,Vue Routerパターン.md)、[`.aidiy/knowledge/frontend_web,Pinia Storeパターン.md`](./.aidiy/knowledge/frontend_web,Pinia Storeパターン.md) |
| frontend_avatar / Electron / VRM / 音声 | [`.aidiy/knowledge/frontend_avatar,ElectronIPC追加手順.md`](./.aidiy/knowledge/frontend_avatar,ElectronIPC追加手順.md)、[`.aidiy/knowledge/frontend_avatar,VRM_VRMA追加手順.md`](./.aidiy/knowledge/frontend_avatar,VRM_VRMA追加手順.md)、[`.aidiy/knowledge/backend_server,frontend_avatar,AI音声処理.md`](./.aidiy/knowledge/backend_server,frontend_avatar,AI音声処理.md) |
| AI コア / Code CLI / MCP | [`.aidiy/knowledge/backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md`](./.aidiy/knowledge/backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md)、[`.aidiy/knowledge/backend_server,backend_hermes,frontend_avatar,frontend_web,CodeCLI追加手順.md`](./.aidiy/knowledge/backend_server,backend_hermes,frontend_avatar,frontend_web,CodeCLI追加手順.md)、[`.aidiy/knowledge/backend_server,backend_tools,MCP活用手順.md`](./.aidiy/knowledge/backend_server,backend_tools,MCP活用手順.md) |
| backend_hermes Provider / Slash Command | [`.aidiy/knowledge/backend_hermes,Provider一覧と選択ロジック.md`](./.aidiy/knowledge/backend_hermes,Provider一覧と選択ロジック.md)、[`.aidiy/knowledge/backend_hermes,Slash Command一覧.md`](./.aidiy/knowledge/backend_hermes,Slash Command一覧.md) |
| GitHub issue 運用 | [`.aidiy/knowledge/共通,GitHubIssue運用手順.md`](./.aidiy/knowledge/共通,GitHubIssue運用手順.md) |

`.aidiy/knowledge` は作業ログ置き場ではありません。残す内容は、次回以降に再利用できる HowTo、判断基準、注意点、確認方法だけです。

## 関連ドキュメント

| ドキュメント | 役割 |
|--------------|------|
| [CLAUDE.md](./CLAUDE.md) | Claude Code 向けインデックス、クイックスタート、アーキテクチャサマリー |
| [backend_server/AGENTS.md](./backend_server/AGENTS.md) | FastAPI + SQLAlchemy + SQLite の実装詳細 |
| [backend_hermes/AGENTS.md](./backend_hermes/AGENTS.md) | `aidiy_hermes` CLI 基盤の実装詳細 |
| [backend_tools/AGENTS.md](./backend_tools/AGENTS.md) | MCP サーバー群の実装詳細 |
| [frontend_web/AGENTS.md](./frontend_web/AGENTS.md) | Vue 3 + Vite + TypeScript の Web UI 実装詳細 |
| [frontend_avatar/AGENTS.md](./frontend_avatar/AGENTS.md) | Electron/Web デュアルモード Avatar の実装詳細 |
| [docs/](./docs/) | HTML 形式の詳細ドキュメント |

人間向けの紹介資料は [frontend_web/public/X自己紹介/index.html](./frontend_web/public/X自己紹介/index.html) です。

## AiDiy とは

**AiDiy** (AI Do-It-Yourself) は、日本語を第一言語とするフルスタック業務管理システムの開発フレームワーク / テンプレートです。

目的:

- 日本語ネイティブな開発環境を提供する。
- FastAPI + SQLite + Vue 3 による実用的な業務管理テンプレートを提供する。
- 権限管理、マスタ管理、トランザクション管理、スケジューラ、在庫管理の実装例を提供する。
- マルチベンダー AI、音声、画像、Code CLI、MCP を統合する実験基盤として機能する。

## 基本方針

- 画面、URL、JSONキー、識別子は日本語を原則とする。
- 文字コードは UTF-8 固定。
- DB項目名、API項目名、フロントエンド変数名はできるだけ一致させる。
- `request`、`query`、`item`、`items`、`total`、`limit` などの一般名は英字のまま使用してよい。
- ファイル内容確認は UTF-8 指定で読む。
- HowTo、検証手順、失敗対処は AGENTS.md ではなく `.aidiy/knowledge/` に置く。
- `npm run build` は原則として日常的な確認手順に含めない。配布物作成、ビルド成果物確認、利用者明示依頼など、実行理由が明確な場合だけ実行する。

## 日本語ファースト設計

全レイヤーで日本語識別子を使います。

| レイヤー | 例 |
|----------|----|
| Database | テーブル名 `C権限`、カラム名 `利用者ID` |
| API | `/core/利用者/一覧`、`{"利用者名": "admin"}` |
| Frontend | `C利用者一覧.vue`、`/C管理/C利用者/一覧` |
| Code | `利用者名`、`配車日付`、`商品名` |

日本語話者が業務ドメインとコードを直接対応づけられることを優先します。

## アーキテクチャ概要

AiDiy は 3 つの常駐サーバーと 1 つの on-demand CLI 基盤で構成します。

| コンポーネント | 役割 | 主なポート |
|----------------|------|------------|
| `backend_server/core_main.py` | C系、A系、認証、AIコア | 8091 |
| `backend_server/apps_main.py` | M系、T系、V系、S系 | 8092 |
| `backend_tools/tools_main.py` | MCP サーバー群 | 8095 |
| `backend_hermes` | `aidiy_hermes` CLI 基盤 | 常駐なし |
| `frontend_web` | 通常 Web UI | 8090 |
| `frontend_avatar` | Electron/Web デュアルモード Avatar | 8099 |

`core_main.py` と `apps_main.py` は同じ SQLite DB を共有します。
フロントエンドは Vite proxy で `/core/*` を 8091、`/apps/*` を 8092 へ振り分けます。

## ディレクトリ概要

| ディレクトリ | 内容 |
|--------------|------|
| `backend_server/` | FastAPI サーバー、SQLAlchemy モデル、CRUD、Router、AIコア |
| `backend_hermes/` | `aidiy_hermes` CLI |
| `backend_tools/` | Chrome DevTools、Desktop Capture、SQLite、PostgreSQL、Logs、Code Check、Backup Check、Backup Save、Image Generation、Speech-to-Text、Text-to-Speech の MCP |
| `frontend_web/` | Vue 3 + Vite + TypeScript の Web UI |
| `frontend_avatar/` | Electron/Web 対応の AI Avatar UI |
| `docs/` | HTML 形式の開発ガイド |
| `.aidiy/knowledge/` | プロジェクト専用 HowTo と再利用ナレッジ |

## テーブル命名規則

| 接頭辞 | 種別 | 例 |
|--------|------|----|
| `C` | Core / Common | `C権限`、`C利用者`、`C採番` |
| `M` | Master | `M商品`、`M取引先`、`M商品構成` |
| `T` | Transaction | `T配車`、`T生産`、`T商品入庫` |
| `V` | View endpoint | `V商品`、`V生産`、`V商品推移表` |
| `S` | Scheduler / Special | `S配車_週表示`、`S生産_日表示` |
| `A` | AI / Advanced | `A会話履歴`、`AIコア` |
| `X` | Experimental | `Xテトリス`、`X世界の絶景` |

`V` 系は DB VIEW オブジェクトではなく、生SQLによる JOIN / 集計エンドポイントとして実装します。

## API 方針

- CRUD エンドポイントは POST 中心。
- レスポンスは `status`、`message`、`data` を持つ統一形式。
- Core API は `/core/*`、Apps API は `/apps/*` に分ける。
- 認証は JWT を使う。

レスポンス例:

```json
{
  "status": "OK",
  "message": "メッセージ",
  "data": {}
}
```

## DB 方針

- SQLite を使う。
- DB ファイルは `backend_server/_data/AiDiy/database.db`。
- Alembic は使わない。
- 既存DBが残る場合、モデル変更だけではスキーマ差分は反映されない。
- カスタムID生成は `C採番` で管理し、AUTOINCREMENT を前提にしない。
- 全テーブルは登録 / 更新の監査フィールドを持つ。

スキーマ変更の具体手順は `.aidiy/knowledge/backend_server,スキーマ変更手順.md` を参照してください。

## 提供機能

### C系 Core / Common

- `C権限`: 権限マスタ。
- `C利用者`: JWT 認証つき利用者マスタ。
- `C採番`: カスタムID生成。

### M系 Master

- 配車区分、生産区分、生産工程、商品分類、取引先分類、取引先、車両、商品。
- `M商品構成`: `明細SEQ=0` をヘッダー、`明細SEQ>=1` を材料明細とする明細型マスタ。

### T系 Transaction

- `T配車`: 配車トランザクション。
- `T生産`: `明細SEQ=0` をヘッダー、`明細SEQ>=1` を払出明細とする明細型トランザクション。
- `T商品入庫`、`T商品出庫`、`T商品棚卸`: 在庫管理トランザクション。

### V系 View Endpoint

- コア、マスタ、トランザクション、在庫推移の JOIN / 集計表示。
- DB VIEW は作らず、Router 内の SELECT + JOIN で実装する。

### S系 Scheduler / Special

- `S配車_週表示`、`S配車_日表示`。
- `S生産_週表示`、`S生産_日表示`。

### A系 AI / Advanced

- `AIコア`: WebSocket + マルチベンダー AI + Code CLI パネル。
- `A会話履歴`: 会話履歴保存。

### X系 Experimental

- `Xテトリス`、`Xインベーダー`、`Xリバーシ`、`X立体リバーシ`。
- `X世界の絶景`。
- `X自己紹介`。

## 業務サンプル概要

| サンプル | 主な構成 |
|----------|----------|
| 配車管理 | `M配車区分`、`M車両`、`T配車`、`V配車`、`S配車_*` |
| 生産管理 | `M生産区分`、`M生産工程`、`M商品`、`M商品構成`、`T生産`、`V生産`、`S生産_*` |
| 資材在庫管理 | `M商品`、`T商品入庫`、`T商品出庫`、`T商品棚卸`、`V商品推移表` |

## 明細型パターン

ヘッダー行と明細行を単一テーブルで管理します。

```text
ID    | 明細SEQ | 意味
------+---------+----------------
P001  | 0       | ヘッダー行
P001  | 1       | 明細行
P001  | 2       | 明細行
```

代表例:

- `M商品構成`: 商品構成ヘッダー + 材料明細。
- `T生産`: 生産指示ヘッダー + 材料払出明細。

## AI コア概要

AIコアは、テキスト、音声、画像、ファイル、コード支援を統合する多パネル UI です。

| 種別 | 役割 |
|------|------|
| `CHAT_AI_NAME` | テキストチャット |
| `LIVE_AI_NAME` | 音声リアルタイム対話 |
| `CODE_AI1_NAME`〜`CODE_AI6_NAME` | code1〜code6 のコード支援 |

Code AI の有効値は `claude_sdk`、`claude_cli`、`copilot_cli`、`codex_cli`、`antigravity_cli`、`opencode_cli`、`aidiy_hermes` を想定します。

## frontend_web 概要

- Vue 3 + Vite + TypeScript。
- Vue Router と Pinia を使用。
- qTubler によるカスタムテーブル UI。
- `_Layout`、`_TopBar`、`_TopMenu` による共通レイアウト。
- qAlert、qConfirm、qColorPicker などの共通ダイアログを持つ。

## frontend_avatar 概要

frontend_avatar は Electron デスクトップアプリと通常 Web ブラウザの両方で動作します。

| 項目 | Electron モード | Web モード |
|------|----------------|-----------|
| 判定 | `window.desktopApi` あり | `window.desktopApi` なし |
| 認証 Storage | `localStorage` | `sessionStorage` |
| UI | 複数 Electron ウィンドウ | 左アバター + 右タブ |
| アクセス | `http://127.0.0.1:8099` | `http://localhost:8099` |

主な技術:

- Electron。
- Three.js。
- `@pixiv/three-vrm`。
- `@pixiv/three-vrm-animation`。
- WebSocket。
- BroadcastChannel `avatar-desktop-sync`。

## 3D アバター概要

- VRM モデルを Three.js で表示する。
- VRMA モーションを `public/vrma/` から再生する。
- 背景透過により Electron の透明フレームレスウィンドウと重ねられる。
- マイク入力 / AI 音声出力のレベルを口パクや演出へ反映する。

## MCP 概要

`backend_tools` は 14 個の MCP サーバーを同居させます。

| MCP | 役割 |
|-----|------|
| `aidiy_chrome_devtools` | Chrome ブラウザ自動操作 |
| `aidiy_desktop_capture` | デスクトップキャプチャ |
| `aidiy_sqlite` | AiDiy SQLite DB 確認 |
| `aidiy_postgres` | 外部 PostgreSQL 確認 |
| `aidiy_logs` | backend_server / backend_tools ログ確認 |
| `aidiy_code_check` | Python 構文 / ruff / TypeScript 型チェック |
| `aidiy_backup` | 差分バックアップ保存 / 確認（HTTP は `save` / `check` に分岐） |
| `aidiy_image_generation` | AI 画像生成（OpenAI / Gemini / FreeAI / Codex CLI / Antigravity CLI） |
| `aidiy_movie_generation` | AI 動画生成（Google Gemini Veo） |
| `aidiy_speech_to_text` | 音声認識（speech_recognition / OpenAI Whisper） |
| `aidiy_text_to_speech` | テキスト音声合成（Edge / OpenAI / Gemini / FreeAI） |
| `aidiy_obs_studio_control` | OBS Studio WebSocket 制御（配信、録画、シーン、ソース、音声） |
| `aidiy_ffmpeg_control` | ffmpeg / ffprobe / ffplay 実行（動画合成、字幕焼き込み、プレビュー再生） |
| `aidiy_code_agents` | AI コードエージェント実行（CodeAI CLI 経由） |

各 MCP は **SSE Transport**、**Streamable HTTP Transport**、**stdio gateway（`mcp_stdio.py`）** の 3 トランスポートを同一ポートで提供します。Python の `requests` でそのまま呼び出せるため、自動化スクリプトやバックエンドルーターからも利用できます。

MCP の使い分けと設定は `.aidiy/knowledge/backend_server,backend_tools,MCP活用手順.md` を参照してください。

## 実装確認の入口

実装内容を確認するときは、まずサブプロジェクトの AGENTS.md を確認し、実際のコードを優先してください。

- Backend: `backend_server/AGENTS.md`
- Hermes: `backend_hermes/AGENTS.md`
- MCP: `backend_tools/AGENTS.md`
- Web: `frontend_web/AGENTS.md`
- Avatar: `frontend_avatar/AGENTS.md`

docs と実装が食い違う場合は、現行実装を確認したうえで「現行実装では」と明記します。
