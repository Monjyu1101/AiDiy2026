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

## プロキシが必要なネットワーク

Discord への直接接続が制限される環境では、パネルを起動する親プロセスに `HTTPS_PROXY` を設定します。例のURLは、利用環境のHTTP(S)プロキシへ置き換えてください。

```powershell
$env:HTTPS_PROXY = 'http://proxy.example:8080'
$env:NO_PROXY = 'localhost,127.0.0.1,::1'
aidiy_discord
```

`HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY` と小文字版に対応します。同じ変数が両方ある場合は空でない小文字版を優先し、HTTPS用が無ければHTTP用を使います。プロキシ未設定なら従来の直接接続です。`NO_PROXY` はカンマ・空白区切りのホスト名、ポート指定、`.example.com` / `*.example.com`、全除外の `*` を使えます。localhost・127系・IPv6ループバックは常に直接接続します。

REST、Gateway（再接続・resumeを含む）、音声用 WebSocket をそれぞれプロキシ対応します。音声用はDiscordが通知したホスト・ポートへ接続します。環境変数を変更したら **パネルを閉じ、環境変数を設定した端末から起動し直してください**。既存パネルを呼び出すだけでは新しい環境は継承されません。OSのGUIから起動する場合も、その起動元に設定が必要です。プロキシURLを共通キーJSONやソースに追加する必要はありません。

認証不要の疎通確認は `frontend_discord` で次を実行します。環境変数の存在有無、公開RESTのHTTP状態、Gatewayの認証前HELLOを確認し、URLや認証情報は表示しません。外部通信を使うため `npm test` とは分けて実行します。

```text
node checks/network-diagnostic.mjs
```

診断結果はBot認証や音声の成功を保証しません。HTTPプロキシではDiscord音声のUDP通信を運べないため、Live音声は対象ネットワークでボイス入室・双方向音声・退出まで確認してください。

音声接続に失敗した場合は、エラー詳細の「音声通信」と「音声接続先」を確認します。「WebSocket接続中」でタイムアウトする場合は、表示されたホスト・ポートへの直接接続またはプロキシのCONNECT許可を確認してください。「UDP接続・IP検出中」で失敗する場合は、別途UDPが通るネットワーク経路を確認してください。接続先にはホスト・ポートと「プロキシ経由／直接接続」を表示し、プロキシURLや認証情報は表示しません。

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

旧 Discord 専用の Live / Code / URL / 接頭辞設定は廃止しました。セットアップまたは backend の設定読み込みで除去し、共通設定には転記しません。接続情報・Code 設定の変更は、パネルで切断して再度接続すると読み直します。

許可したユーザーは Bot 実行ユーザーの権限で Hermes のコード・ツールを利用できます。信頼する利用者を登録し、返信や音声を共有してよいチャンネルを指定してください。音声入力は許可ユーザーのみを取り込みますが、AI の発言は同じボイスチャンネルの参加者に聞こえます。

## 起動と操作

```powershell
aidiy_discord
```

画面中央上部に小さなパネルが開きます。Live の AI・モデル・音声と、コード AI（Hermes の Provider）・モデルを選び、右上の「接続」で Discord に接続します。左上には作業フォルダを「プロジェクト: フォルダ名」で表示します。作業フォルダは aidiy_code / aidiy_live と同じく、`aidiy_discord [作業フォルダ]`（または `--project`）で指定し、省略時は起動したフォルダです。Live のモデル・音声は `_config/AiDiy_live_gemini.json`（Gemini / FreeAI）と `_config/AiDiy_live_openai.json` の候補から選択します。コードモデルは直接入力もできます。コードの候補取得は `aidiy_code` と同じカタログを使います。「切断」でチャット・音声を終了して切断し、パネルを閉じた場合も Bot と実行中の CLI を終了します。接続中のモデル変更は切断してから行います。パネルを重ねて起動すると既存の画面を表示します。終了処理中のパネルに重ねて起動した場合は、終了を待ってから開き直します。

「音声会話」「コード」の見出し右にある OFF / ON スイッチで、接続する機能を選びます。音声会話（Live）は切り替えでき、OFF で接続するとボイスチャンネルに入室しても音声会話を開始せず、Live のモデル確認も行いません。コードは現在 ON 固定で、スイッチは操作できません。両方 OFF では接続しません。切り替えは切断中だけ行えます。

接続中のパネルは設定欄の代わりに、AiDiy の絵と、最後のやり取り（発言者と本文）を1件だけ表示し、約1分で消します。プロジェクト行の下の右寄せに「LIVE ON/OFF」「CODE ON/OFF」を表示し、Live が ON の間は背景に入力（赤）と AI の声（水色）の円型インジケーターを描きます。左下の「モニター」を ON にすると、通過する音声（許可ユーザーの入力と AI の声）をこの PC で聞けます。スピーカーの音を Discord のマイクが拾うとエコーになるため、モニターは接続ごとに OFF から始まります。Live が OFF の間はインジケーターとモニターを表示しません。

単独の `aidiy_discord` は未接続で開きます。ルート `_start.py` で Discord を Yes にした場合（または明示的な `aidiy_discord --connect`）は、前回のモデルで自動接続します。全体起動からのパネルも手動で停止・終了でき、閉じたパネルを監視ループで再表示しません。全体の Ctrl+C・cleanup では Discord のプロセスも停止します。

どちらの起動方法でも、パネルを開く前に共通設定・Hermes の起動パスを確認します。トークンが空欄・1文字・`<` で始まる仮設定の場合は、設定項目名を示すエラーを表示して終了コード1で中止します。トークンそのものは表示せず、この確認で Discord には接続しません。

JSON の候補から削除されたモデル・音声は自動使用せず、選び直すまで接続を止めます。Discord はパネル表示・保存・開始時に JSON を読み込みます。候補を編集したらパネルを開き直してください。

最後に手動選択した Live モデル・音声は `~/.aidiy/aidiy_discord_model.json`、コード AI・モデルは `~/.aidiy/aidiy_discord_code_model.json`、Live の ON/OFF は `~/.aidiy/aidiy_discord_features.json`（未保存時は ON）に保存します。単独起動でも全体起動からの自動接続でも、これらを復元して適用します。保存処理は `aidiy_live` / `aidiy_code` と共用し、保存ファイルは Discord 専用です。未保存・破損時は共通 `LIVE_*` / `CODE_AIDIY_HERMES_MODEL` を使います。API キー・トークン・ID はモデル保存ファイルには含めません。

`cd frontend_discord` 後の `npm start`、`python frontend_discord/_start.py` でも同じパネルが開きます。`aidiy_discord --check` / `npm run config:check` は設定と Hermes の実行パスだけを確認し、Discord には接続しません。Code だけなら Core は不要で、Live を利用する場合はルート `_start.py` などで Core を起動してください。Core 停止中は保存済み・共通設定のモデルを表示します。起動ログは `frontend_discord/out/aidiy_discord/` に保存します。

### ブラウザ版（Codespaces など）

`aidiy_discord --browser` で、Electron の代わりにブラウザでパネルを開きます。画面・操作は Electron 版と同じで、パネルのサーバー（`src/web-server.ts`）と WebSocket でやり取りします。GitHub Codespaces（`CODESPACES=true`）と画面のない Linux（`DISPLAY` / `WAYLAND_DISPLAY` なし）では、`--browser` を省略してもブラウザ版で開きます。ブラウザは VS Code / Codespaces が設定する `$BROWSER` を優先して手元の PC で開き、Codespaces の `$BROWSER` には元の localhost URL を渡し、VS Code にポート転送と外部 URI の解決を任せます。手動用にはトークン付き転送先 URL（`https://<名前>-<ポート>.app.github.dev/…`）を表示します。開けない場合は URL を表示します。判定と起動は `frontend_vscode/scripts/launch-project.mjs`、接続元の許可は `frontend_vscode/src/forwarded-origin.ts` で aidiy_code / aidiy_live / aidiy_discord 共通です。Electron 版でパネルを閉じた時と同じく、画面を閉じると60秒後（初回は120秒後、Codespaces では初回接続まで終了しない）に Bot も終了します。3本（aidiy_code / aidiy_live / aidiy_discord）の起動規則は `frontend_vscode/scripts/launch-project.mjs` の冒頭に一覧し、そこで共通化しています。Electron の専用ウィンドウを開けない場合（未セットアップ・起動失敗）は、理由を表示してブラウザ版に切り替えます。通常のブラウザ版は初回120秒、最後の画面切断後60秒で終了します。Codespaces では初回接続まで終了しません。Bot の音声は Discord の UDP 通信を使うため、Codespaces で音声会話がつながるかは環境によります。

## クリーンアップ

ルート `python _cleanup.py` の Discord 項目は既定 Yes です。削除前にこの作業コピーの Bot を子孫プロセスごと停止し、終了できない場合は削除を中止します。Discord の削除を選ばない場合でも、全体 cleanup の開始時には他サービスと同じく Bot を停止します。

削除対象は `frontend_discord` 内の `node_modules`、生成物、temp、Python キャッシュと、この作業コピーを指す `aidiy_discord` ランチャーです。ソース、`package-lock.json`、共通 `_config/AiDiy_key.json`、前回のモデル・機能の選択は残ります。単独 cleanup は `python frontend_discord/_cleanup.py` です。

## 会話のしかた

| 操作 | 動作 |
|--------|------|
| 専用テキストチャンネルに「おはよう」と投稿 | Hermes が返信 |
| 続けて普通に投稿 | 前の会話を引き継いで、送信順に返信 |
| 専用ボイスチャンネルに参加 | AiDiy も参加し、音声会話を開始 |
| ボイスチャンネルから退出 | 指定ユーザーが退出すると、AiDiy も音声会話を終了 |

パネルで音声会話を OFF にして接続した場合、ボイスチャンネルの入退室には反応せず、互換用の `!aidiy live` / `!aidiy leave` も「Live は OFF のため利用できません。」と返します。

Code の会話は「サーバー・テキストチャンネル・ユーザー」ごとに分かれ、プロセス内で最新200会話まで保持します。Bot 再起動後は新規会話です。Hermes 自身の保存セッションは削除しません。続けて届いたメッセージは同じ会話内で順番に処理し、実行中を含む待機数は10件まで、全体の並行実行は4件までです。長文回答は添付テキストにし、回答内の `@everyone` などは通知を発生させません。

Live は指定ユーザーが指定ボイスチャンネルへ入室すると自動接続します。Bot 起動時も参加状態を確認します。音声の文字起こしはパネルに表示し、指定テキストチャンネルには AI の応答が終わるごとに「あなたの最後の発言＋AI の応答」を1件にまとめて送ります。指定ユーザーの退出、Discord / AIコアの切断で終了します。別のユーザーやチャンネルでは開始しません。接続失敗時はボイスチャンネルに入り直してください。DM、Stage チャンネル、画面共有・映像には対応しません。

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
