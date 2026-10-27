# _AIDIY/knowledge インデックス

このフォルダは AiDiy2026 専用の再利用ナレッジ置き場です。
残す内容は、次回の修正で使える HowTo、判断基準、注意点、確認方法だけにします。

## ファイル命名規則

ナレッジファイル名は `対象モジュール,トピック名.md` とします。
`,` の左側にどのモジュール（群）に関連するかを並べ、右側にトピックを日本語で記述します。

```
モジュール1,モジュール2,トピック名.md
```

モジュール名には以下を使います:

| モジュール名 | 対象 |
|-------------|------|
| `共通` | プロジェクト全体、横断的な話題 |
| `backend_diag` | aidiy_diag の環境診断・モデル情報・Vue 画面 |
| `backend_server` | FastAPI サーバー（core_main / apps_main） |
| `command_hermes` | `aidiy_hermes` CLI 基盤 |
| `backend_tools` | MCP サーバー群 |
| `backend_local` | ローカル LLM サーバー（OpenAI 互換 Gemma 推論） |
| `backend_taskteam` | AIタスク実行 + 定期タスクと複数AIエージェントのチーム活動を統合した FastAPI サーバー |
| `frontend_web` | Vue 3 + Vite + TypeScript Web UI |
| `frontend_avatar` | Electron/Web デュアルモード Avatar |
| `frontend_channels` | Discord Bot の Code（Hermes）チャット / Live（AIコア）音声接続 |
| `frontend_ide` | Console / Code / Live / IDEのVue共通画面、VS Code拡張ホスト、宇宙表示・ファイルビューア |

例:

- `backend_server,スキーマ変更手順.md` — backend_server 単独の話題
- `frontend_avatar,frontend_web,アバター表示とVRMA.md` — 両方のフロントエンドにまたがる話題
- `backend_server,frontend_web,frontend_avatar,JWT認証フロー.md` — 3モジュールにまたがる話題
- `共通,開発環境運用手順.md` — プロジェクト全体の話題

メタファイル（`_index.md`、`_最終変更.md`）は接頭辞をつけず、`_` 始まりのままにします。

総合テストの手順・実施結果・エビデンスは `セルフテスト,アプリコマンド,xx編.md` とします。主目的は総合テストで、記録した操作と画面は副産物として操作手順書の素材に再利用します。例は `セルフテスト,aidiy_diag,システム起動編.md`。エビデンスは `Diag-システム起動_101_起動直後画面.png` のように短い編名・確認番号・場面を含め、本文にインラインで掲載します。各冊のテスト通過後に、元のMarkdownと同じフォルダへ同名のPDFも作成します。本文の修正後はPDFも再生成します。

説明資料の構成・文体・画像説明は[説明資料の書き方](./セルフテスト,_説明資料の書き方.md)にまとめます。文書全体を簡潔で丁寧に書き、先頭に総合評価、各画像の直前に短い説明を添えます。再試験後は本文と総合評価を一緒に更新します。解消した課題の経緯は掲載せず、修正後の最終結果だけに整理します。

画像は `images/<参照元Markdownの拡張子なしファイル名>/<ファイル名>` に保存します。例は `images/セルフテスト,aidiy_diag,システム起動編/` です。ファイル名は `Diag-システム起動_101_起動直後画面.png` のように内容を先に示し、日付や実施IDを先頭に付けません。実施日時・結果・操作上の注意・画像説明は参照元のMarkdownへ直接記載します。JSON・ログ・結果テキストや、整理作業の台帳は説明資料として残さず、照合した事実と判定だけを本文に記載します。実施IDのサブフォルダは作りません。再試験でも既存画像は上書きせず、同じ場面を区別する説明や末尾の `_確認02`、`_確認03` を付けます。`temp/` は作業用で、正式な証跡の保存先には使いません。

今回の必須対象はWindowsです。Mac／Linux実機と長時間連続運転は「PASS（環境依存・判定対象外）」として未実施を明記し、実行成功とは区別します。各冊に対象OSと推奨試験の扱いを明記します。

## ファイル内容先頭書式

各ナレッジファイルの先頭は以下の形式に統一します。

```markdown
# <タイトル>

> 文書: `モジュール,トピック名.md` | 実装: `backend_server/path/file.py`, `frontend_web/src/path/file.vue`

## このメモを使う場面

- <このメモが役立つ状況を箇条書き>
```

ブロック引用（`> 文書: … | 実装: …`）行の目的:
- `文書:` — このファイル自身のファイル名を記載する。全文検索で `文書名.md` → 該当ファイルがヒットしやすくなる。
- `実装:` — このナレッジが参照する主要なソースファイルパスを `,` 区切りで列挙する。grep で `ファイル名.vue` → 関連ナレッジが特定できる。

例:

```markdown
# AI モデル設定変更手順

> 文書: `backend_server,frontend_avatar,frontend_web,AIモデル設定変更手順.md` | 実装: `backend_server/conf/conf_json.py`, `frontend_web/src/components/AiDiy/dialog/AI設定再起動.vue`

## このメモを使う場面

- AI ベンダーやモデル名を切り替えるとき
- `.env` の `CHAT_AI_NAME` などの設定値を変更するとき
```

- `# <タイトル>` はファイル名末尾のトピック部分と対応させる（`AIモデル設定変更手順` など）。
- `## このメモを使う場面` は必ず箇条書きで簡潔に書く。

## 使い方

1. 目的に近いカテゴリから該当ファイルを開く。
2. 使う前に、関連ファイルとして書かれているソースを確認して現行実装との差を埋める。
3. 迷う場合は、下の「迷ったときの入口」から最初に見るファイルを決める。
4. 知見を追記するときは、作業履歴ではなく次回使える手順へ圧縮して既存ファイルへ統合する。

## 重複しやすい話題の使い分け

| 話題 | 使い分け |
|------|----------|
| Node.js 外部 API の proxy / TLS / 安全な失敗ログ | [`共通,Node.js外部API通信の注意点.md`](./共通,Node.js外部API通信の注意点.md) を参照する。Discord と aidiy_diag の実装差、環境変数の優先順位、loopback mock による再検証をまとめる。 |
| 音声処理 | `AudioController` 単体、マイク、再生、エコー抑制、音声 WebSocket は [`backend_server,frontend_avatar,AI音声処理.md`](./backend_server,frontend_avatar,AI音声処理.md) に集約する。 |
| VRM / VRMA | モデルやモーションファイルを追加する場合は [`frontend_avatar,VRM_VRMA追加手順.md`](./frontend_avatar,VRM_VRMA追加手順.md)、表示サイズ・向き・表示選択 UI は [`frontend_avatar,frontend_web,アバター表示とVRMA.md`](./frontend_avatar,frontend_web,アバター表示とVRMA.md)、描画内部やカメラワークは [`frontend_avatar,3Dアバター制御(Three.js VRM).md`](<./frontend_avatar,3Dアバター制御(Three.js VRM).md>) を使う。 |
| MCP / 起動 | backend 常駐サーバーの起動は [`backend_server,command_hermes,backend_tools,バックエンド起動.md`](./backend_server,command_hermes,backend_tools,バックエンド起動.md)、MCP サーバー構成は [`backend_tools,構成.md`](./backend_tools,構成.md)、Code CLI への MCP 登録は [`command_hermes,backend_tools,CodeCLI_MCP設定.md`](./command_hermes,backend_tools,CodeCLI_MCP設定.md) を使う。 |

## 最優先ルール

| 目的 | 参照ファイル |
|------|--------------|
| `AGENTS.md` / `_AIDIY.md` / `CLAUDE.md` を整理する | [`共通,AGENTS整理手順.md`](./共通,AGENTS整理手順.md) |

## 迷ったときの入口

直近のConsole改名・Task／Team独立化・Diag起動追加などの部分再試験は、[変更影響・再試験計画](./セルフテスト,共通,変更影響・再試験計画.md)を先に確認します。Task／Teamの今回の結果は、それぞれの操作編を参照します。計画全体の未実施項目とは分けて確認します。

| 症状・依頼 | 最初に見るファイル |
|-----------|------------------|
| 総合テストの説明資料を、簡潔・丁寧に、画像説明を添えてまとめる | [説明資料の書き方](./セルフテスト,_説明資料の書き方.md) |
| aidiy_diagの起動・停止を総合テストし、操作手順書素材を残す | [システム起動編](./セルフテスト,aidiy_diag,システム起動編.md) |
| aidiy_diagのプロジェクト選択・アプリ起動を総合テストし、操作手順書素材を残す | [アプリ起動編](./セルフテスト,aidiy_diag,アプリ起動編.md) |
| aidiy_diagの導入状況・モデル・外部連携を総合テストし、操作手順書素材を残す | [環境確認編](./セルフテスト,aidiy_diag,環境確認編.md) |
| IDEの利用開始・閲覧・Code/Live連携を総合テストし、操作手順書素材を残す | [IDE操作編](./セルフテスト,aidiy_ide,操作編.md) |
| WebのAI機能を確認する | [AiDiy編](./セルフテスト,frontend_web,AiDiy編.md) |
| 独立Task・Teamを操作・確認する | [変更影響・再試験計画](./セルフテスト,共通,変更影響・再試験計画.md)。[Task操作編](./セルフテスト,aidiy_task,操作編.md)・[Team操作編](./セルフテスト,aidiy_team,操作編.md)に現行の操作と確認結果をまとめています。 |
| Webの配車・生産・在庫を確認する | [配車管理編](./セルフテスト,frontend_web,配車管理編.md)、[生産・在庫管理編](./セルフテスト,frontend_web,生産・在庫管理編.md) |
| Avatarを実行方式ごとに確認する | [Electron実行編](./セルフテスト,aidiy_avatar,Electron実行編.md)、[Web実行編](./セルフテスト,aidiy_avatar,Web実行編.md) |
| Electron画面の0.5秒長押しドラッグ、透明パネルで領域を先に確保する表示開始ズーム | [`共通,Electronウィンドウ基本方針.md`](./共通,Electronウィンドウ基本方針.md) |
| 今後の改善提案を比較し、採用条件を検討する | [`共通,明日のために,改善提案.md`](./共通,明日のために,改善提案.md) |
| 未解決の改善課題と再現条件・検証限界を確認する | [`共通,明日のために,改善課題.md`](./共通,明日のために,改善課題.md) |
| AGENTS / CLAUDE / _AIDIY の役割分担整理 | [`共通,AGENTS整理手順.md`](./共通,AGENTS整理手順.md) |
| DB スキーマ差分、起動時のカラム不足 | [`backend_server,スキーマ変更手順.md`](./backend_server,スキーマ変更手順.md) |
| M / T / V / S 系の追加、登録漏れ | [`backend_server,M系マスタ追加手順.md`](./backend_server,M系マスタ追加手順.md)、[`backend_server,T系トランザクション追加手順.md`](./backend_server,T系トランザクション追加手順.md)、[`backend_server,V系エンドポイント追加手順.md`](./backend_server,V系エンドポイント追加手順.md)、[`backend_server,S系スケジューラ追加手順.md`](./backend_server,S系スケジューラ追加手順.md) |
| M系マスタへのカラム追加 | [`backend_server,M系マスタカラム追加手順.md`](./backend_server,M系マスタカラム追加手順.md) |
| 採番、監査フィールド、初期データ | [`backend_server,C採番と監査フィールド.md`](./backend_server,C採番と監査フィールド.md) |
| backend の層構造、実装パターン、落とし穴 | [`backend_server,実装パターン.md`](./backend_server,実装パターン.md) |
| ログイン、401、トークン延長、パスワード | [`backend_server,frontend_web,frontend_avatar,JWT認証フロー.md`](./backend_server,frontend_web,frontend_avatar,JWT認証フロー.md)、[`backend_server,frontend_web,frontend_avatar,認証延長ルール.md`](./backend_server,frontend_web,frontend_avatar,認証延長ルール.md)、[`backend_server,C利用者パスワード運用.md`](./backend_server,C利用者パスワード運用.md) |
| backend / MCP / task・team 起動、ポート残留 | [`backend_server,command_hermes,backend_tools,バックエンド起動.md`](./backend_server,command_hermes,backend_tools,バックエンド起動.md)、[`backend_tools,構成.md`](./backend_tools,構成.md) |
| AIタスク（要求分解・明細DAG・実行開始条件）、AIチーム（依頼・経験・作業ループ・自動会話）の仕様 | `backend_taskteam/AGENTS.md`（構成・仕様の入口。実行記録と繰り返し監視の HowTo は次項） |
| AIタスクの実行済み記録が空になる、間隔実行が1回のエラーで止まる、実行監視タスクを作る | [`backend_taskteam,AIタスクの実行記録と繰り返し監視.md`](./backend_taskteam,AIタスクの実行記録と繰り返し監視.md) |
| aidiy_hermes で MCP が `failed` / ツール未認識 | [`command_hermes,backend_tools,MCP_SSE接続.md`](./command_hermes,backend_tools,MCP_SSE接続.md) |
| upstream hermes-agent の新版を command_hermes へ取り込む、移植後に起動しない | [`command_hermes,upstream移植手順.md`](./command_hermes,upstream移植手順.md) |
| Windows ネイティブで terminal / file 操作が落ちる、OS 分岐を入れたい | [`command_hermes,Windows対応規則.md`](./command_hermes,Windows対応規則.md) |
| hermes を MCP サーバーとして Code CLI から使う | [`command_hermes,MCP_サーバー起動.md`](./command_hermes,MCP_サーバー起動.md) |
| プロジェクト別に Chat / Code の会話履歴を分析する | [`backend_server,frontend_ide,frontend_web,frontend_avatar,会話履歴のプロジェクト識別.md`](./backend_server,frontend_ide,frontend_web,frontend_avatar,会話履歴のプロジェクト識別.md) |
| AIチャット / AIコードの引数・実行オプション（会話継続・履歴保存・ストリーム送信・出力ファイル保存）を追加・変更する | [`backend_server,backend_tools,AIチャット・AIコード共通パラメータ.md`](./backend_server,backend_tools,AIチャット・AIコード共通パラメータ.md) |
| AI モデル、WebSocket、code1〜code6 | [`backend_server,frontend_avatar,frontend_web,AIモデル設定変更手順.md`](./backend_server,frontend_avatar,frontend_web,AIモデル設定変更手順.md)、[`backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md`](./backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md)、[`backend_server,frontend_avatar,frontend_web,AIコードパネル拡張手順.md`](./backend_server,frontend_avatar,frontend_web,AIコードパネル拡張手順.md) |
| Code CLI 追加、CLI 出力、MCP 設定 | [`backend_server,command_hermes,frontend_avatar,frontend_web,CodeCLI追加手順.md`](./backend_server,command_hermes,frontend_avatar,frontend_web,CodeCLI追加手順.md)、[`backend_server,command_hermes,frontend_avatar,CodeCLI表示ANSI制御コード対処.md`](./backend_server,command_hermes,frontend_avatar,CodeCLI表示ANSI制御コード対処.md)、[`command_hermes,backend_tools,CodeCLI_MCP設定.md`](./command_hermes,backend_tools,CodeCLI_MCP設定.md)、[`command_hermes,backend_tools,Antigravity_CLIのMCP接続設定.md`](./command_hermes,backend_tools,Antigravity_CLIのMCP接続設定.md) |
| frontend_web 画面、X系、proxy | [`frontend_web,画面追加手順.md`](./frontend_web,画面追加手順.md)、[`frontend_web,X系静的画面追加.md`](./frontend_web,X系静的画面追加.md)、[`frontend_web,frontend_avatar,backend_server,Viteプロキシ設定.md`](./frontend_web,frontend_avatar,backend_server,Viteプロキシ設定.md) |
| frontend_web の UI ルール、qTubler、明細型編集 | [`frontend_web,実装パターン.md`](./frontend_web,実装パターン.md) |
| 画面コンポーネントを直す（**frontend_avatar に同名コピーがあるので両方直す**） | [`frontend_web,実装パターン.md`](./frontend_web,実装パターン.md)（「frontend_avatar との二重管理」）、[`frontend_web,frontend_avatar,共通ユーティリティ.md`](./frontend_web,frontend_avatar,共通ユーティリティ.md) |
| frontend_avatar、Electron、VRM / VRMA、音声 | [`frontend_avatar,変更チェック.md`](./frontend_avatar,変更チェック.md)、[`frontend_avatar,ElectronIPC追加手順.md`](./frontend_avatar,ElectronIPC追加手順.md)、[`frontend_avatar,VRM_VRMA追加手順.md`](./frontend_avatar,VRM_VRMA追加手順.md)、[`frontend_avatar,frontend_web,アバター表示とVRMA.md`](./frontend_avatar,frontend_web,アバター表示とVRMA.md)、[`backend_server,frontend_avatar,AI音声処理.md`](./backend_server,frontend_avatar,AI音声処理.md) |
| VS Code の AiDiy Code / AiDiy Live 拡張を変更・検証・配布する | [`frontend_ide,VSCodeチャット拡張変更手順.md`](./frontend_ide,VSCodeチャット拡張変更手順.md) |
| Code の `out/*.cjs` など生成物6件だけが差分に出る、上書きせず再検証する | [`frontend_ide,VSCodeチャット拡張変更手順.md`](./frontend_ide,VSCodeチャット拡張変更手順.md)（「Code の生成物だけが差分に出た場合」） |
| Code の `out/aidiy_code/<起動ID>.json` だけが変更通知に出る | [`frontend_ide,VSCodeチャット拡張変更手順.md`](./frontend_ide,VSCodeチャット拡張変更手順.md)（「Code の起動完了JSONだけが変更された場合」） |
| Discord の Code / Live 接続、Bot 設定、音声中継を変更・検証する | [`frontend_discord,Discord接続変更手順.md`](./frontend_discord,Discord接続変更手順.md) |
| Discord 音声のチャンク境界で無音が混ざる、発話末尾が欠ける、Opus 回帰テストを見直す | [`frontend_discord,Discord接続変更手順.md`](./frontend_discord,Discord接続変更手順.md)（「出力チャンク境界と末尾処理の再修正チェック」） |
| command_hermes の CLI 起動・確認 | [`command_hermes,backend_server,運用手順.md`](./command_hermes,backend_server,運用手順.md) |
| backend_tools の起動・SSE・環境変数 | [`backend_tools,backend_server,運用手順.md`](./backend_tools,backend_server,運用手順.md) |
| バックアップ保存先、旧 `.backup_local/`・`backup/` から `.aidiy_backup/` への移行、保存版との比較 | [`command_hermes,共通,MCPバックアップ検証手順.md`](./command_hermes,共通,MCPバックアップ検証手順.md) |
| backend_tools の `/tts` `/imageGen` `/movieGen` HTTP API、save_path 挙動、SSE マウント方法 | [`backend_tools,HTTP_API_save_path挙動.md`](./backend_tools,HTTP_API_save_path挙動.md) |
| Markdown、BOM、ナレッジ整理 | [`共通,Markdown現状追従チェック.md`](./共通,Markdown現状追従チェック.md)、[`共通,UTF8BOM問題対処.md`](./共通,UTF8BOM問題対処.md)、[`共通,ナレッジ更新手順.md`](./共通,ナレッジ更新手順.md) |
| フォルダ確認結果の件数・参照内容・検証範囲を照合する | [`共通,ナレッジ更新手順.md`](./共通,ナレッジ更新手順.md)（「フォルダ確認結果の根拠と記録の整合性」） |
| 開発環境操作、DB、Swagger、よくある問題 | [`共通,開発環境運用手順.md`](./共通,開発環境運用手順.md) |
| GitHub issue の確認・close | [`共通,GitHubIssue運用手順.md`](./共通,GitHubIssue運用手順.md) |
| MCP（TTS / OBS / ffmpeg / Chrome devtools）で紹介動画を自動生成する | [`共通,mcp利用による自動ビデオ生成手順.md`](./共通,mcp利用による自動ビデオ生成手順.md) ※ 実装済み自動化: `backend_tools/aidiy_automations/ビデオページ生成/ビデオページ生成_紹介.py`, `backend_tools/aidiy_automations/ビデオページ生成/ビデオページ生成_解説.py` |
| 紹介ビデオ（take）またはアバター版プレゼンターを新規作成・改版する | [`frontend_web,X系紹介ビデオとアバター作成手順.md`](./frontend_web,X系紹介ビデオとアバター作成手順.md) |
| ニュース型掛け合いビデオ（female+male 2アバター・1ページ複数ターン）を作成・改版する | [`frontend_web,X系ニュース型掛け合いビデオ.md`](./frontend_web,X系ニュース型掛け合いビデオ.md) |

既存の運用で `_最終変更.md` を参照する場合は、履歴ではなく [`再修正時の確認入口`](./_最終変更.md) として扱います。

## Backend データ・スキーマ

| 目的 | 参照ファイル |
|------|--------------|
| SQLite スキーマ変更と手動 DB 再作成の前提を確認する | [`backend_server,スキーマ変更手順.md`](./backend_server,スキーマ変更手順.md) |
| C採番と監査フィールドを使う | [`backend_server,C採番と監査フィールド.md`](./backend_server,C採番と監査フィールド.md) |
| backend の Model / Schema / CRUD / Router パターンを確認する | [`backend_server,実装パターン.md`](./backend_server,実装パターン.md) |

## Backend 認証

| 目的 | 参照ファイル |
|------|--------------|
| JWT ログインから 401 ハンドリングまで確認する | [`backend_server,frontend_web,frontend_avatar,JWT認証フロー.md`](./backend_server,frontend_web,frontend_avatar,JWT認証フロー.md) |
| どの操作でトークンを延長するか確認する | [`backend_server,frontend_web,frontend_avatar,認証延長ルール.md`](./backend_server,frontend_web,frontend_avatar,認証延長ルール.md) |
| C利用者のパスワード保存・照合方針を確認する | [`backend_server,C利用者パスワード運用.md`](./backend_server,C利用者パスワード運用.md) |

## Backend API 追加

| 目的 | 参照ファイル |
|------|--------------|
| M系マスタを追加する | [`backend_server,M系マスタ追加手順.md`](./backend_server,M系マスタ追加手順.md) |
| M系マスタにカラムを追加する | [`backend_server,M系マスタカラム追加手順.md`](./backend_server,M系マスタカラム追加手順.md) |
| T系トランザクションを追加する | [`backend_server,T系トランザクション追加手順.md`](./backend_server,T系トランザクション追加手順.md) |
| V系 JOIN / 集計エンドポイントを追加する | [`backend_server,V系エンドポイント追加手順.md`](./backend_server,V系エンドポイント追加手順.md) |
| S系スケジューラを追加する | [`backend_server,S系スケジューラ追加手順.md`](./backend_server,S系スケジューラ追加手順.md) |

## Backend 起動・運用

| 目的 | 参照ファイル |
|------|--------------|
| backend_server / backend_tools / backend_taskteam を起動・再起動する | [`backend_server,command_hermes,backend_tools,バックエンド起動.md`](./backend_server,command_hermes,backend_tools,バックエンド起動.md) |
| 開発環境の起動、依存関係、DB、API確認、問題切り分けを行う | [`共通,開発環境運用手順.md`](./共通,開発環境運用手順.md) |
| Docker / Nginx 構成で起動する | [`backend_server,frontend_web,Docker構成.md`](./backend_server,frontend_web,Docker構成.md) |
| MCP サーバー構成を確認する | [`backend_tools,構成.md`](./backend_tools,構成.md) |
| backend_tools の起動、stdio bridge、環境変数を確認する | [`backend_tools,backend_server,運用手順.md`](./backend_tools,backend_server,運用手順.md) |
| MCP ツールをコードエージェントから使う | [`backend_server,backend_tools,MCP活用手順.md`](./backend_server,backend_tools,MCP活用手順.md) |
| MCP バックアップツールでファイル検証・差分確認をする | [`command_hermes,共通,MCPバックアップ検証手順.md`](./command_hermes,共通,MCPバックアップ検証手順.md) |

## Frontend 共通

| 目的 | 参照ファイル |
|------|--------------|
| Electron全アプリ・関連パネルの0.5秒長押しドラッグと、透明パネルで領域確保する表示開始ズーム | [`共通,Electronウィンドウ基本方針.md`](./共通,Electronウィンドウ基本方針.md) |
| Avatar / VS Code の Electron を事前導入し、バイナリ・ZIP を再利用する | [`共通,開発環境運用手順.md`](./共通,開発環境運用手順.md)（「Electron の共通セットアップ」） |
| Vite proxy / CORS / ポートを調整する | [`frontend_web,frontend_avatar,backend_server,Viteプロキシ設定.md`](./frontend_web,frontend_avatar,backend_server,Viteプロキシ設定.md) |
| Axios API クライアントのパターン・token 付与・401 ハンドリングを確認する | [`frontend_web,frontend_avatar,共通APIクライアントパターン.md`](./frontend_web,frontend_avatar,共通APIクライアントパターン.md) |
| Monaco Editor / qAlert / qConfirm など共通ユーティリティを修正する | [`frontend_web,frontend_avatar,共通ユーティリティ.md`](./frontend_web,frontend_avatar,共通ユーティリティ.md) |
| 両プロジェクトの package.json / tsconfig / vite.config の差異と同期ルールを確認する | [`frontend_web,frontend_avatar,プロジェクト設定と依存関係.md`](./frontend_web,frontend_avatar,プロジェクト設定と依存関係.md) |

## Frontend Web

| 目的 | 参照ファイル |
|------|--------------|
| Vue 3 の業務画面を追加する | [`frontend_web,画面追加手順.md`](./frontend_web,画面追加手順.md) |
| qTubler、UI ルール、明細型編集を既存パターンへ合わせる | [`frontend_web,実装パターン.md`](./frontend_web,実装パターン.md) |
| X系の静的画面・ゲーム・デモを追加する | [`frontend_web,X系静的画面追加.md`](./frontend_web,X系静的画面追加.md) |

## Frontend Avatar / Electron

| 目的 | 参照ファイル |
|------|--------------|
| Electron IPC を追加する | [`frontend_avatar,ElectronIPC追加手順.md`](./frontend_avatar,ElectronIPC追加手順.md) |
| Electron / Web 両モードの変更チェックを行う | [`frontend_avatar,変更チェック.md`](./frontend_avatar,変更チェック.md) |
| VRM モデル・VRMA モーションを追加する | [`frontend_avatar,VRM_VRMA追加手順.md`](./frontend_avatar,VRM_VRMA追加手順.md) |
| アバター表示・VRMA 連続再生・表示選択 UI を調整する | [`frontend_avatar,frontend_web,アバター表示とVRMA.md`](./frontend_avatar,frontend_web,アバター表示とVRMA.md) |
| xneko / xeyes 系ウィジェットを追加する | [`frontend_avatar,xneko_xeyesウィジェット追加手順.md`](./frontend_avatar,xneko_xeyesウィジェット追加手順.md) |
| マイク入力・音声再生・エコー抑制を調整する | [`backend_server,frontend_avatar,AI音声処理.md`](./backend_server,frontend_avatar,AI音声処理.md) |
| AiDiy.vue の全体構成・状態・初期化フローを確認する | [`frontend_avatar,AiDiy.vue全体構成と状態管理.md`](./frontend_avatar,AiDiy.vue全体構成と状態管理.md) |
| Electron ウィンドウの位置・サイズ・IPC・ライフサイクルを変更する | [`frontend_avatar,Electronウィンドウ管理.md`](./frontend_avatar,Electronウィンドウ管理.md) |
| 3D アバター描画・VRMA 再生・視線補助・カメラワークを調整する | [`frontend_avatar,3Dアバター制御(Three.js VRM).md`](<./frontend_avatar,3Dアバター制御(Three.js VRM).md>) |

## aidiy_diag 環境診断

| 目的 | 参照ファイル |
|------|--------------|
| aidiy_diag の診断・Vue 画面・配布物・起動を変更・検証する | [`backend_diag,環境診断運用.md`](./backend_diag,環境診断運用.md) |

## Frontend IDE

| 目的 | 参照ファイル |
|------|--------------|
| Console / Code / Live / IDE の日本語機能フォルダ・共通 Vue 部品・配布・検証を確認する | [`frontend_ide,Vue共通画面変更手順.md`](./frontend_ide,Vue共通画面変更手順.md) |
| Code / Live の画面隅・複数窓、Console の縦横別サイズを調整する | [`frontend_ide,初期ウィンドウ配置.md`](./frontend_ide,初期ウィンドウ配置.md) |
| IDE の今日・本日最新の強調、電子の周回、描画負荷を確認する | [`frontend_ide,更新の目印と電子表示.md`](./frontend_ide,更新の目印と電子表示.md) |
| IDE の文書表示（Word / Excel / PowerPoint / PDF）を変更する | [`frontend_ide,文書ビューア.md`](./frontend_ide,文書ビューア.md) |

## Frontend Discord

| 目的 | 参照ファイル |
|------|--------------|
| Discord の Code / Live 接続・Vue パネル・配布物を変更・検証する | [`frontend_discord,Discord接続変更手順.md`](./frontend_discord,Discord接続変更手順.md) |

## Frontend VS Code

| 目的 | 参照ファイル |
|------|--------------|
| VS Code 拡張（Code / Live）と単独起動版を変更・検証・VSIX 配布する | [`frontend_ide,VSCodeチャット拡張変更手順.md`](./frontend_ide,VSCodeチャット拡張変更手順.md) |
| Code の生成物と生成元を `write: false` で照合し、現行生成物を対象テストで確認する | [`frontend_ide,VSCodeチャット拡張変更手順.md`](./frontend_ide,VSCodeチャット拡張変更手順.md)（「Code の生成物だけが差分に出た場合」） |
| Code の起動完了JSONの形式・生成箇所・読込を検証する | [`frontend_ide,VSCodeチャット拡張変更手順.md`](./frontend_ide,VSCodeチャット拡張変更手順.md)（「Code の起動完了JSONだけが変更された場合」） |
| 拡張機能をセットアップして VS Code へ配置する | [`共通,開発環境運用手順.md`](./共通,開発環境運用手順.md) |
| 配置済み拡張機能と生成物を解除する | [`共通,クリーンアップ手順.md`](./共通,クリーンアップ手順.md) |

## AI コア

- [backend_server,backend_tools,AI判断追加手順.md](./backend_server,backend_tools,AI判断追加手順.md) — Decisions API / OAuth JSON Schema、共通入出力、MCP、プロバイダ追加。


| 目的 | 参照ファイル |
|------|--------------|
| AIコア WebSocket の接続・パケット形式を確認する | [`backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md`](./backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md) |
| Gemini の thought_signature を tool_calls で中間保持・復元する | [`backend_server,Gemini_thought_signature保持と復元.md`](./backend_server,Gemini_thought_signature保持と復元.md) |
| AIWebSocket クライアントの実装・再接続ポリシー・両フロントエンドの差分を確認する | [`frontend_web,frontend_avatar,共通WebSocketクライアント.md`](./frontend_web,frontend_avatar,共通WebSocketクライアント.md) |
| AIチャット / AIコードに共通パラメータを追加する（片方だけに独自引数を足さない） | [`backend_server,backend_tools,AIチャット・AIコード共通パラメータ.md`](./backend_server,backend_tools,AIチャット・AIコード共通パラメータ.md) |
| AI モデル設定を変更する | [`backend_server,frontend_avatar,frontend_web,AIモデル設定変更手順.md`](./backend_server,frontend_avatar,frontend_web,AIモデル設定変更手順.md) |
| code1〜code6 のコード AI パネルを調整する | [`backend_server,frontend_avatar,frontend_web,AIコードパネル拡張手順.md`](./backend_server,frontend_avatar,frontend_web,AIコードパネル拡張手順.md) |
| backend_server の設定管理（conf_json / conf_model / conf_path）を変更する | [`backend_server,設定管理(conf).md`](<./backend_server,設定管理(conf).md>) |

## Frontend Web ルーター・状態管理

| 目的 | 参照ファイル |
|------|--------------|
| Pinia store のパターン・auth store の動作を確認する | [`frontend_web,Pinia Storeパターン.md`](./frontend_web,Pinia Storeパターン.md) |
| Vue Router の3ファイル分割・認証ガード・ルート追加手順を確認する | [`frontend_web,Vue Routerパターン.md`](./frontend_web,Vue Routerパターン.md) |

## Code CLI

| 目的 | 参照ファイル |
|------|--------------|
| Code CLI を追加する | [`backend_server,command_hermes,frontend_avatar,frontend_web,CodeCLI追加手順.md`](./backend_server,command_hermes,frontend_avatar,frontend_web,CodeCLI追加手順.md) |
| Code CLI の MCP 設定を確認する | [`command_hermes,backend_tools,CodeCLI_MCP設定.md`](./command_hermes,backend_tools,CodeCLI_MCP設定.md) |
| Antigravity CLI の HTTP MCP 設定を確認・更新する | [`command_hermes,backend_tools,Antigravity_CLIのMCP接続設定.md`](./command_hermes,backend_tools,Antigravity_CLIのMCP接続設定.md) |
| aidiy_hermes の MCP SSE 接続を修復・確認する | [`command_hermes,backend_tools,MCP_SSE接続.md`](./command_hermes,backend_tools,MCP_SSE接続.md) |
| Code CLI のプロンプト整形責務を確認する | [`backend_server,CodeCLIプロンプト整形.md`](./backend_server,CodeCLIプロンプト整形.md) |
| CLI 出力の ANSI 制御コードを除去する | [`backend_server,command_hermes,frontend_avatar,CodeCLI表示ANSI制御コード対処.md`](./backend_server,command_hermes,frontend_avatar,CodeCLI表示ANSI制御コード対処.md) |
| upstream hermes-agent の新版へ移植する | [`command_hermes,upstream移植手順.md`](./command_hermes,upstream移植手順.md) |
| Hermes CLI の TUI を調整する | [`command_hermes,TUI調整手順.md`](./command_hermes,TUI調整手順.md) |
| Hermes CLI の Provider 一覧・選択ロジックを確認する | [`command_hermes,Provider一覧と選択ロジック.md`](./command_hermes,Provider一覧と選択ロジック.md) |
| Hermes CLI の Slash Command 一覧・追加手順を確認する | [`command_hermes,Slash Command一覧.md`](./command_hermes,Slash Command一覧.md) |
| command_hermes を単体 CLI として起動・確認する | [`command_hermes,backend_server,運用手順.md`](./command_hermes,backend_server,運用手順.md) |
| hermes を MCP サーバーとして起動・Code CLI から接続する | [`command_hermes,MCP_サーバー起動.md`](./command_hermes,MCP_サーバー起動.md) |
| hermes-agent 新バージョンへ追従・移行する | [`command_hermes,Upstream移行手順.md`](./command_hermes,Upstream移行手順.md) |
| opencode_cli 追加（パス解決・コマンド構築・suffix除去）のパターンを確認する | [`backend_server,opencode_cli追加と実行パターン.md`](./backend_server,opencode_cli追加と実行パターン.md) |
| grok_cli 追加（パス解決・コマンド構築・モデル候補・配線箇所）のパターンを確認する | [`backend_server,grok_cli追加と実行パターン.md`](./backend_server,grok_cli追加と実行パターン.md) |
| antigravity_cli のタイムアウト延長・継続フラグの調整パターンを確認する | [`backend_server,antigravity_cliタイムアウトと継続オプション.md`](./backend_server,antigravity_cliタイムアウトと継続オプション.md) |
| Windows ネイティブ実行の OS 分岐規則・落とし穴を確認する | [`command_hermes,Windows対応規則.md`](./command_hermes,Windows対応規則.md) |

## メディア生成

| 目的 | 参照ファイル |
|------|--------------|
| MCP（TTS / OBS / ffmpeg / Chrome devtools）で紹介動画を自動生成する | [`共通,mcp利用による自動ビデオ生成手順.md`](./共通,mcp利用による自動ビデオ生成手順.md) |
| 紹介ビデオ（take）またはアバター版プレゼンターを新規作成・改版する | [`frontend_web,X系紹介ビデオとアバター作成手順.md`](./frontend_web,X系紹介ビデオとアバター作成手順.md) |
| ニュース型掛け合いビデオ（female+male 2アバター・1ページ複数ターン）を作成・改版する | [`frontend_web,X系ニュース型掛け合いビデオ.md`](./frontend_web,X系ニュース型掛け合いビデオ.md) |
| AI で画像素材を生成する（シーン背景・アイキャッチ） | `POST /imageGen`（`aidiy_image_generation` MCP）— 詳細は [`共通,mcp利用による自動ビデオ生成手順.md`](./共通,mcp利用による自動ビデオ生成手順.md) |
| AI で動画クリップ素材を生成する（Gemini Veo） | `POST /movieGen`（`aidiy_movie_generation` MCP）— 詳細は [`共通,mcp利用による自動ビデオ生成手順.md`](./共通,mcp利用による自動ビデオ生成手順.md) |

## ドキュメント・共通

| 目的 | 参照ファイル |
|------|--------------|
| Markdown を現行実装へ追従させる | [`共通,Markdown現状追従チェック.md`](./共通,Markdown現状追従チェック.md) |
| `AGENTS.md` 系ドキュメントを概要と HowTo に分離する | [`共通,AGENTS整理手順.md`](./共通,AGENTS整理手順.md) |
| `_AIDIY/knowledge` を更新する | [`共通,ナレッジ更新手順.md`](./共通,ナレッジ更新手順.md) |
| フォルダ確認後に知見のみ整理し、本体修正と区別する | [`共通,ナレッジ更新手順.md`](./共通,ナレッジ更新手順.md)（「確認依頼と自己改善書き込みの区別」） |
| 確認結果の根拠、索引・最終参照の整合性、未実施の検証を区別する | [`共通,ナレッジ更新手順.md`](./共通,ナレッジ更新手順.md)（「フォルダ確認結果の根拠と記録の整合性」） |
| UTF-8 BOM を検出・除去する | [`共通,UTF8BOM問題対処.md`](./共通,UTF8BOM問題対処.md) |
| 一時ファイル・バックアップを整理する | [`共通,クリーンアップ手順.md`](./共通,クリーンアップ手順.md) |
| Git 未管理フォルダにローカル履歴を用意する | [`共通,ローカルGit管理.md`](./共通,ローカルGit管理.md) |
| GitHub issue を確認・close する | [`共通,GitHubIssue運用手順.md`](./共通,GitHubIssue運用手順.md) |
| バグ修正と整理案を区別して提案する | [`共通,変更提案時の区別.md`](./共通,変更提案時の区別.md) |

## 明日のための改善検討

- [共通,明日のために,改善提案.md](./共通,明日のために,改善提案.md): 既存機能を踏まえた改善提案10件、判断基準と検証方法。
- [共通,明日のために,改善課題.md](./共通,明日のために,改善課題.md): 再現条件・影響・検証限界を伴う主な課題10件と予備候補。

## 記録ルール

- ファイル名は `モジュール,トピック名.md` 形式にする（上記「ファイル命名規則」参照）。
- 同じテーマの知見は既存ファイルへ統合する。
- 残すのは HowTo、判断基準、注意点、確認方法だけにする。
- 日付つき履歴、担当者メモ、経緯説明、完了報告、編集対象の列挙だけの記録は残さない。
- 現行実装と同期が必要な値は、同期元のファイルパスを併記する。
- `_AIDIY/knowledge` 更新とアプリ本体の仕様変更は混同しない。

## Tools主要メソッドのセルフテスト

[主要メソッド編](./セルフテスト,backend_tools,主要メソッド編.md) — 実行した18 MCP、環境依存のPASS、パラメータと結果のSVG図解。
