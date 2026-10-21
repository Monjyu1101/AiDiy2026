# frontend_channels 実装概要

## 役割

外部接続チャンネルを配置するフォルダです。現在は Discord 接続を提供し、内部モジュール名と `aidiy_discord` コマンドは維持します。

Discord Bot を AiDiy の Code / Live へ接続する Node.js / TypeScript クライアントです。
Code は `aidiy_hermes` CLI を直接起動し、Live は既存 AIコアの WebSocket へ接続します。
接続情報はプロジェクト共通の `_config/AiDiy_key.json` に保存します。

## 構成

| ファイル | 役割 |
|----------|------|
| `src/main.ts` | 起動、設定確認、終了処理 |
| `panel/` | `aidiy_live` に合わせた接続パネル（`desktop.cjs` の Electron 起動・安全な IPC、`launch.mjs` の起動入口、`画面/接続パネル.vue` の Vue 画面、`接続/パネル状態.js` の状態管理、`ライブ/音声表示.js` の円型インジケーター、ブラウザ版用の `web-bridge.js`） |
| `src/接続パネル/パネル操作.ts` | 開始・停止、モデル選択と Live ON/OFF の永続化、モニター切替 |
| `src/接続パネル/パネル中継.ts` | Electron 版（`src/panel-worker.ts`）とブラウザ版（`src/web-server.ts`）共通のパネル操作・通知の中継 |
| `src/接続/接続設定.ts` | 共通 JSON の読込・検証、パスと接続先の解決 |
| `src/ライブ/ライブモデル候補.ts` / `src/モデル情報/モデル情報.ts` | モデル情報APIを優先し、取得失敗時はdiagのモデル・音声合成JSONを読む。共通初期値の補正 |
| `src/接続/ネットワーク接続.ts` / `src/gateway-worker.mjs` | REST / Gateway / 音声 WebSocket のプロキシ対応 |
| `src/接続/接続エラー.ts` | 接続失敗の段階別案内と、秘密値を伏せたエラー詳細 |
| `src/接続/コマンド処理.ts` | コマンド解析、利用許可、回答分割 |
| `src/接続/Bot接続.ts` | Discord イベント、Code / Live 操作、返信 |
| `src/コード/コード会話.ts` | ユーザー・チャンネルごとの Hermes 会話継続、停止 |
| `src/ライブ/ライブ会話.ts` | ボイスチャンネルと AIコアの双方向中継、切断回収 |
| `src/ライブ/音声処理.ts` | PCM 変換、話者混合、Opus 再生 |
| `src/共通連携/IDE連携.ts` | `frontend_ide/host` の既存 CLI / Live protocol の直接共有 |
| `checks/` | Discord に接続せずに行う動作検証 |
| `_setup.py` | 依存導入と共通設定の不足キー補完 |
| `_start.py` / `launcher.py` | パネル単独起動、PATH コマンド登録、cleanup 用停止 API |
| `_cleanup.py` / `discord_processes.py` | 実行パスによる対象 Bot の停止確認と依存物・キャッシュ削除 |

## 基本方針

- Bot トークン、サーバー・チャンネル・ユーザー ID は `AiDiy_key.json` の `DISCORD_*` を参照する。
- `discord_allowed_user_id`、`discord_text_channel_id`、`discord_voice_channel_id` はそれぞれ単一の文字列で指定し、利用者1人・テキスト1チャンネル・ボイス1チャンネルに限定する。
- Discord 専用設定は接続情報の5項目だけとし、Live は `LIVE_*`、接続先は `PORT_CORE`、Code / Live の作業フォルダは `CODE_BASE_PATH`、Hermes は `CODE_AIDIY_HERMES_MODEL` と `CODE_MAX_TURNS` を共用する。
- `frontend_ide/host/src/runner.ts`、`src/protocol.ts`、`aidiy_live/src/protocol.ts` を再利用し、CLI 実行・通信仕様を複製しない。
- CommonJS の日本語 export は `src/共通連携/IDE連携.ts` の `createRequire` 経由で読み込む。
- Code はシェルを介さず UTF-8 stdin で渡す。`--yolo` を追加しない。
- Discord の受信イベントはサーバー・チャンネル・ユーザーの許可を確認してから処理する。
- 専用テキストチャンネルの通常投稿を Hermes に渡し、同じ会話の連続投稿は送信順に処理する。接頭辞やメンションを必須にしない。
- Live はサーバーにつき1接続。許可ユーザーの入退室に合わせて自動接続・終了し、Bot 起動時にも参加状態を確認する。音声は許可された参加者のみを取り込み、切断時は関連リソースをすべて終了する。
- 設定値や Discord API エラーオブジェクト全体をログに出さない。
- Bot は `tsx` で起動し、VSIX を必要としない。Vue 画面は事前コンパイル済み `panel/view.js` を同梱し、通常起動時のビルドを前提にしない。ソースと配布物の一致は `scripts/verify-panel.mjs` で確認する。
- `aidiy_discord` は画面中央上部に小さな未接続のパネルを開く。ルート `_start.py` の Discord 選択は既定 No とし、Yes の場合は同じパネルを開いて自動接続する。停止・終了はパネルから操作できる。
- Live の最後の選択は `~/.aidiy/aidiy_discord_model.json`、コード AI・モデルは `~/.aidiy/aidiy_discord_code_model.json` に保存し、両方の起動方法で共通設定より優先する。読込・検証・原子的保存は `frontend_ide/host/src/model-preferences.ts`、コード候補は `frontend_ide/host/scripts/model-catalog.py` を共用する。
- Live の ON/OFF は `~/.aidiy/aidiy_discord_features.json` に保存し、Bot へは `Discord設定.liveEnabled` / `codeEnabled` で渡す。Code は現在 ON 固定（`src/接続パネル/パネル操作.ts` の `コード固定ON`）。OFF の機能は接続前の確認も Bot 側の処理も行わず、両方 OFF では接続しない。
- 接続中のパネルへは音量と帯域分布だけを送る。PCM は「モニター」を ON にした間だけ渡し、モニターは接続ごとに OFF から始める（スピーカー音のエコー防止）。
- Renderer は sandbox と contextIsolation を有効にし、Node API やトークンを渡さない。パネル終了時は worker 内の Code / Live 接続も回収する。

導入・操作は [README.md](./README.md)、変更と検証は [接続機能の変更手順](../_AIDIY/knowledge/frontend_discord,Discord接続変更手順.md) を参照してください。
