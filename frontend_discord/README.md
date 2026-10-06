# AiDiy Discord

自分と AiDiy の専用テキストチャンネルに普通に話しかけると、`aidiy_hermes` が返信します。専用ボイスチャンネルに参加すると、AIコアの LiveAI と音声会話できます。チャットは `frontend_vscode` の Code と同じ CLI 実行処理、ライブは同じ Live WebSocket 処理を使います。

## 導入

- Node.js 22.12 以降（この作業環境では 24.18 で検証）。
- `command_hermes` をセットアップし、使う Provider を認証しておきます。
- ライブを使う場合は `backend_server` の Core と LiveAI の設定が必要です。
- `frontend_vscode` のソースを同じプロジェクトに保持します。VS Code 本体、拡張の導入、VSIX 生成は不要です。

プロジェクトルートで実行します。

```powershell
python frontend_discord/_setup.py
```

ルート `_setup.py` の「フロントエンド(Discord)」からも導入できます。セットアップは既定 Yes（`[y]/n`）で、Electron の事前配置と `~/.local/bin/aidiy_discord`（Windows は `.cmd`）の登録も行います。ルート `_start.py` の Discord 起動は既定 No（`[n]/y`）で、Yes を選ぶとパネルを開いて自動接続します。

## Discord 側の準備

1. [Discord Developer Portal](https://discord.com/developers/applications) で Application / Bot を作成します。
2. Bot の **Message Content Intent** を有効にします。投稿本文の受信に必要です。
3. Bot トークンを下記 `DISCORD_BOT_TOKEN` に保存します。通常ユーザーのトークンは使いません。
4. OAuth2 の `bot` スコープでサーバーへ招待します。テキスト側に「チャンネルを見る」「メッセージを送信」「メッセージ履歴を読む」「ファイルを添付」、ボイス側に「チャンネルを見る」「接続」「発言」の権限を付けます。スレッドで利用するときは「スレッドでメッセージを送信」も必要です。
5. Discord の開発者モードで、サーバー ID、利用者 ID、テキスト・ボイスチャンネル ID をコピーします。スレッドの場合はスレッド自身の ID を許可します。

自分と Bot が利用できるプライベートのテキスト・ボイスチャンネルを指定します。アプリコマンド登録、接頭辞、Bot メンションは不要です。

## 接続情報

既存の **`_config/AiDiy_key.json`** に設定します。新しい別名のキー管理ファイルは作りません。セットアップと Core 起動時に不足する `DISCORD_*` の初期値が補完されます。既存の AI キーや他の設定はそのまま残し、以下の項目を編集してください。

```json
{
  "DISCORD_BOT_TOKEN": "Bot のトークン",
  "DISCORD_GUILD_ID": "111111111111111111",
  "DISCORD_ALLOWED_USER_ID": "222222222222222222",
  "DISCORD_TEXT_CHANNEL_ID": "333333333333333333",
  "DISCORD_VOICE_CHANNEL_ID": "444444444444444444"
}
```

| 設定 | 意味 |
|------|------|
| `DISCORD_BOT_TOKEN` | Bot トークン。空欄・1文字（`<` など）・`<` で始まる仮設定ではパネルを起動しません |
| `DISCORD_GUILD_ID` | 利用する1つのサーバー ID |
| `DISCORD_ALLOWED_USER_ID` | 操作・音声入力を許可する利用者1人の ID |
| `DISCORD_TEXT_CHANNEL_ID` | 普通の投稿に返信する専用テキストチャンネルの ID。音声会話の字幕・接続通知も送ります |
| `DISCORD_VOICE_CHANNEL_ID` | 入室に合わせて自動接続する専用ボイスチャンネルの ID |

Discord 専用設定はこの5項目だけです。すべて必須で、ID は配列や数値ではなく1つの文字列で指定します。それ以外は同じファイルの共通設定を使います。旧 `*_IDS` の1件配列はセットアップまたは backend 起動時に `*_ID` へ自動移行します。複数件が残る場合は、使う ID を新しいキーへ指定してください。

| 共通設定 | Discord での用途 |
|----------|------------------|
| `LIVE_AI_NAME`、`LIVE_*_MODEL`、`LIVE_*_VOICE` | 初回の LiveAI、モデル、音声。手動選択後は前回の選択を優先 |
| `PORT_CORE` | ローカル AIコアの接続先ポート |
| `CODE_BASE_PATH` | Code / Live 共通の作業フォルダ。相対パスは `backend_server` 基準 |
| `CODE_AIDIY_HERMES_MODEL` | Hermes のモデル。`openai_oauth/gpt-6.1-sol` を使用 |
| `CODE_MAX_TURNS` | Hermes の最大実行ターン数 |

Hermes と Python は VS Code と同じ起動探索で自動解決します。OpenAI OAuth の指定は CLI の provider と model に分けて渡し、認証エラー時に別 provider へ切り替えません。CLI の無応答タイムアウトは15分です。

旧 Discord 専用の Live / Code / URL / 接頭辞設定は廃止しました。セットアップまたは backend の設定読み込みで除去し、共通設定には転記しません。接続情報・Code 設定の変更は、パネルで停止して再度開始すると読み直します。

許可したユーザーは Bot 実行ユーザーの権限で Hermes のコード・ツールを利用できます。信頼する利用者を登録し、返信や音声を共有してよいチャンネルを指定してください。音声入力は許可ユーザーのみを取り込みますが、AI の発言は同じボイスチャンネルの参加者に聞こえます。

## 起動と操作

```powershell
aidiy_discord
```

画面中央上部に小さなパネルが開きます。Live の AI・モデル・音声と、コード AI（Hermes の Provider）・モデルを選び、「開始」で Discord に接続します。モデルは候補から選択するか直接入力できます。コードの候補取得は `aidiy_code` と同じカタログを使います。「停止」でチャット・音声を終了して切断し、パネルを閉じた場合も Bot と実行中の CLI を終了します。接続中のモデル変更は停止してから行います。パネルを重ねて起動すると既存の画面を表示します。

単独の `aidiy_discord` は未接続で開きます。ルート `_start.py` で Discord を Yes にした場合（または明示的な `aidiy_discord --connect`）は、前回のモデルで自動接続します。全体起動からのパネルも手動で停止・終了でき、閉じたパネルを監視ループで再表示しません。全体の Ctrl+C・cleanup では Discord のプロセスも停止します。

どちらの起動方法でも、パネルを開く前に共通設定・Hermes の起動パスを確認します。トークンが空欄・1文字・`<` で始まる仮設定の場合は、設定項目名を示すエラーを表示して終了コード1で中止します。トークンそのものは表示せず、この確認で Discord には接続しません。

最後に手動選択した Live モデル・音声は `~/.aidiy/aidiy_discord_model.json`、コード AI・モデルは `~/.aidiy/aidiy_discord_code_model.json` に保存します。単独起動でも全体起動からの自動接続でも、両方を復元して適用します。保存処理は `aidiy_live` / `aidiy_code` と共用し、保存ファイルは Discord 専用です。未保存・破損時は共通 `LIVE_*` / `CODE_AIDIY_HERMES_MODEL` を使います。API キー・トークン・ID はモデル保存ファイルには含めません。

`cd frontend_discord` 後の `npm start`、`python frontend_discord/_start.py` でも同じパネルが開きます。`aidiy_discord --check` / `npm run config:check` は設定と Hermes の実行パスだけを確認し、Discord には接続しません。Code だけなら Core は不要で、Live を利用する場合はルート `_start.py` などで Core を起動してください。Core 停止中は保存済み・共通設定のモデルを表示します。起動ログは `frontend_discord/out/aidiy_discord/` に保存します。

## クリーンアップ

ルート `python _cleanup.py` の Discord 項目は既定 Yes です。削除前にこの作業コピーの Bot を子孫プロセスごと停止し、終了できない場合は削除を中止します。Discord の削除を選ばない場合でも、全体 cleanup の開始時には他サービスと同じく Bot を停止します。

削除対象は `frontend_discord` 内の `node_modules`、生成物、temp、Python キャッシュと、この作業コピーを指す `aidiy_discord` ランチャーです。ソース、`package-lock.json`、共通 `_config/AiDiy_key.json`、前回のモデル選択は残ります。単独 cleanup は `python frontend_discord/_cleanup.py` です。

## 会話のしかた

| 操作 | 動作 |
|--------|------|
| 専用テキストチャンネルに「おはよう」と投稿 | Hermes が返信 |
| 続けて普通に投稿 | 前の会話を引き継いで、送信順に返信 |
| 専用ボイスチャンネルに参加 | AiDiy も参加し、音声会話を開始 |
| ボイスチャンネルから退出 | 指定ユーザーが退出すると、AiDiy も音声会話を終了 |

Code の会話は「サーバー・テキストチャンネル・ユーザー」ごとに分かれ、プロセス内で最新200会話まで保持します。Bot 再起動後は新規会話です。Hermes 自身の保存セッションは削除しません。続けて届いたメッセージは同じ会話内で順番に処理し、実行中を含む待機数は10件まで、全体の並行実行は4件までです。長文回答は添付テキストにし、回答内の `@everyone` などは通知を発生させません。

Live は指定ユーザーが指定ボイスチャンネルへ入室すると自動接続します。Bot 起動時も参加状態を確認します。AI の文字回答は指定テキストチャンネルに送ります。指定ユーザーの退出、Discord / AIコアの切断で終了します。別のユーザーやチャンネルでは開始しません。接続失敗時はボイスチャンネルに入り直してください。DM、Stage チャンネル、画面共有・映像には対応しません。

## 検証・音声仕様

```powershell
npm run check
npm test
```

テストは模擬 CLI と localhost の WebSocket を使い、Discord や AI Provider へ接続しません。実 Bot の確認にはトークンと ID の設定が必要です。

- Discord の48kHzステレオ Opus を PCM16 に復号し、LiveAI へ16kHzモノラル（Gemini / FreeAI）または24kHzモノラル（OpenAI）で送ります。
- AIコアからの24kHzモノラル PCM16 を48kHzステレオ Opus にして再生します。FFmpeg は不要です。
- 指定ユーザーの音声を20ms単位で送り、無音も送って発話終了を検出します。
- `cancel_audio` で再生予約を破棄します。音声・通知キューには上限を設けています。
- DAVE 対応の `@discordjs/voice` と同梱の `@snazzah/davey` を使います。Discord 音声受信は Discord 側の公式 API 仕様が公開されていないため、Discord の変更時には接続の再確認が必要です。[discord.js 音声ライブラリ](https://discord.js.org/docs/packages/voice/0.19.2)、[Discord Voice 仕様](https://docs.discord.com/developers/topics/voice-connections)

応答がないときは Message Content Intent、許可 ID、チャンネル権限を確認します。ライブだけ接続できないときは Core の起動、`LIVE_*` 設定、UDP 通信、ボイス接続・発言権限を確認してください。
