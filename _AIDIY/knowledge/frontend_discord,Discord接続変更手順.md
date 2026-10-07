# Discord 接続変更手順

> 文書: `frontend_discord,Discord接続変更手順.md` | 実装: `frontend_discord/src/audio.ts`, `frontend_discord/checks/audio.test.ts`, `frontend_discord/src/`, `frontend_vscode/src/runner.ts`, `frontend_vscode/src/protocol.ts`, `frontend_vscode/aidiy_live/src/protocol.ts`, `backend_server/conf/conf_json.py`

## このメモを使う場面

- Discord の Code / Live 接続や Bot コマンドを変更する。
- `AiDiy_key.json` の Discord 設定を追加する。
- 音声変換、同時操作、切断回収を検証する。
- 全体のセットアップ・起動・cleanup への組み込みを変更する。

## 変更箇所

1. `frontend_discord/AGENTS.md` で構成を確認し、導入・操作は `frontend_discord/README.md` を参照する。
2. Discord 専用設定はトークン、サーバー ID、`DISCORD_ALLOWED_USER_ID`、`DISCORD_TEXT_CHANNEL_ID`、`DISCORD_VOICE_CHANNEL_ID` の5項目とする。ID は配列ではなく単一文字列で指定する。`backend_server/conf/conf_json.py` の `DEFAULT_CONFIG`、`frontend_discord/src/config.ts`、README を揃える。旧1件配列は `LEGACY_DISCORD_IDS` で移行し、複数件なら新キーを明示するまで元ファイルを保持する。旧上書きキーは `REMOVED_DISCORD_KEYS` で読み込み・保存時に除去し、共通設定は変更しない。実トークンの内容は出力しない。
3. CLI 実行・停止・resume は `frontend_vscode` の共通実装を使用する。CommonJS の日本語 export は `src/vscode.ts` を通す。初回のモデルは共通 `CODE_AIDIY_HERMES_MODEL`（`openai_oauth/gpt-6.1-sol`）、実行回数は `CODE_MAX_TURNS`、作業フォルダは `CODE_BASE_PATH` を使う。パネルで選んだコード AI（Provider）とモデルは `~/.aidiy/aidiy_discord_code_model.json` に保存し、単独起動・全体起動の両方で優先する。候補は `frontend_vscode/scripts/model-catalog.py` を共用する。OAuth の provider は CLI に明示し、認証切れを別 provider への退避で隠さない。
4. Live は既存の input / 0 / audio 接続を使用する。入力レートは `init` のモデル設定に追従する。
   接続先はローカルの `PORT_CORE`、初回の AI とモデル・音声は共通の `LIVE_AI_NAME` / `LIVE_*_MODEL` / `LIVE_*_VOICE` を使う。手動選択は `~/.aidiy/aidiy_discord_model.json` に保存し、次回以降は優先する。検証・原子的保存は `frontend_vscode/src/model-preferences.ts` を `src/vscode.ts` 経由で共用する。共通キー JSON に Discord 専用のモデル項目を追加しない。
5. 専用チャンネルの通常投稿をチャットとして受け付ける。`commands.ts` と `bot.ts` の許可判定より前に外部操作・返信を行わない。既存コマンドは互換用として残すが、通常の利用手順に要求しない。
6. 音声の自動接続は Bot 起動・Gateway 復旧・許可ユーザーの入退室で参加状態を照合する。接続準備中の退出を直ちに反映し、接続処理と通知先の取得が遅れても退出済みの利用者に対して開始しない。ミュート切替や Bot 自身の参加で重複接続しない。

## 確認

`frontend_discord` で `npm run check` と `npm test` を実行する。ビルドは不要。

- `checks/code.test.ts`: stdin、ユーザー別・チャンネル別の resume、停止・終了。
- `checks/bot.test.ts`: 通常投稿→CLI→返信、連続投稿の順序、許可拒否、長文添付、起動・入室時の自動接続と準備中の退出、手動操作との競合。
- `checks/live.test.ts`: localhost の模擬 AIコアを使った3ソケットの接続順、音声入力、再生予約破棄、接続拒否・切断回収。
- `checks/audio.test.ts`: 実 Opus コーデック、レート変換、無音、話者混合と上限。
- `checks/config.test.ts` / `commands.test.ts`: 設定検証、利用許可、本文分割。
- `checks/launch.test.ts`: 一時作業コピーで、空欄・1文字・`<` で始まるトークンが単独起動・自動接続とも Electron 起動前に拒否されることを確認する。実際のキーは変更しない。
- `checks/panel.test.ts`: 初回の共通モデル、選択の永続化・復元、重複開始、接続途中の停止、終了、失敗とタイムアウトの回収。

本物の Bot の疎通には `AiDiy_key.json` に接続情報が必要。`npm run config:check` は外部に接続しない。実接続では専用チャンネルへの通常投稿、ボイス参加→自動接続→発話→退出による自動終了を確認する。mock の成功だけで Discord Gateway / DAVE / AI Provider まで検証済みとは扱わない。

全体スクリプトの検証はルートで `python -X utf8 -m unittest discover -s frontend_discord/checks -p "test_*.py"` を実行する。プロセス停止はモック、削除は一時ディレクトリで確認し、実環境の `_cleanup.py` を検証目的で実行しない。全体 `_setup.py` は Discord 既定 Yes、`_start.py` の Discord 選択は既定 No、`_cleanup.py` の削除選択は既定 Yes。

`aidiy_discord` / `npm start` は `panel/launch.mjs` から Electron の小型パネルを開く。画面位置はマウスのあるディスプレイの workArea 上部中央とする。単独起動は未接続、全体 `_start.py` で Yes の場合は `--wait --connect` を渡して自動接続する。接続開始時に共通設定を再読込し、前回のモデルを適用する。接続・再接続中でも停止でき、終了時は worker に shutdown を送り、Code CLI・Live・Gateway を回収する。正常終了に応答しない場合だけ worker の子孫を停止する。Electron はセットアップで事前配置し、起動中にはダウンロードしない。

起動引数のソースパスは絶対パスにし、`discord_processes.py` の照合と同期する。動作確認は `aidiy_discord --check` で行う（Discord への接続なし）。

## 接続に失敗する場合

- パネルのエラー詳細欄を選択してコピーし、失敗段階（設定読込 / Hermes確認 / モデル確認 / Bot作成 / Discord接続 / 準備完了待ち）、経過時間、エラー名・コード・本文・入れ子の原因を確認する。同じ情報を `frontend_discord/out/aidiy_discord/*.stderr.log` にも出力する。
- `src/connection-error.ts` は Bot トークンなどの認証情報を伏せ字にし、HTTP要求オブジェクト全体・本文・スタックを出力しない。エラーを拡張する場合もこの範囲を維持する。
- `TokenInvalid` / `Authentication failed` はトークン認証、`Used disallowed intents` は Message Content Intent、`ENOTFOUND` はDNS、`UND_ERR_CONNECT_TIMEOUT` / `ETIMEDOUT` は通信タイムアウトの切り分けに使う。経過時間だけで原因を断定しない。パネルの接続待ち上限は40秒で、それ以前にもSDK側のエラーが返る。
- `Hermes確認` の失敗は、実際に動かしているPCで `aidiy_discord --check` を実行してPython・CLIの起動パスを確認する。開発環境の不足を別PCの原因とみなさない。
- `checks/connection-error.test.ts` / `checks/panel.test.ts` で原因別の案内、詳細の伏せ字、失敗後の回収、再試行で詳細が消えることを確認する。Windows実機の接続可否は別途確認する。

### REST / Gateway のプロキシ経路を確認する

- `src/network.ts` は起動時の HTTP(S)_PROXY / NO_PROXY を読み、REST は Undici の安定API `Agent.factory` / `ProxyAgent`、Gateway は `https-proxy-agent` を使う。REST dispatcher を指定しただけで Gateway 対応済みとしない。
- 現行の `@discordjs/ws` 1.2.3 は Node で `ws` を使用し、`ws` が `createConnection` を指定するため `https.globalAgent` の変更だけではプロキシが適用されない。正規の `ws.buildStrategy` / `WorkerShardingStrategy` と `src/gateway-worker.mjs` で Gateway を専用スレッドへ分離し、その中の `https.request` に Gateway と resume の `*.discord.gg` だけ agent を渡す。停止時はSDKによる worker 終了まで待ち、CONNECT待ち・再接続タイマー・ソケットをまとめて回収する。RESTはBot本体の dispatcher をdestroyする。通常のBot workerの通信関数やローカルAIコアには適用しない。SDK更新時は、この経路とSDKの正規拡張点の有無を再確認する。node_modulesは編集しない。
- ローカルAIコアは常に直接接続する。プロキシURL・資格情報をIPCやログへ渡さず、`connection-error.ts` でも環境プロキシURLを伏せる。
- 音声用WebSocketは通常Gatewayとは別経路。`src/live.ts` のvoice adapterは `onVoiceServerUpdate` のendpointを `src/network.ts` の `Discord音声通信.接続先登録` へ渡してからSDKへ通知する。voice 0.19.2にはagent指定APIがないため、通知されたホスト・ポートへの `https.request` だけを捕捉する。非443ポート、NO_PROXY、音声サーバー変更・再接続を維持し、Live終了時にrequest関数・CONNECT待ち・ソケットを回収する。SDK更新時は正規のagent指定APIの有無を再確認する。
- 「WebSocket接続中」のタイムアウトでは「音声接続先」のホスト・ポートと「プロキシ経由／直接接続」を照合し、プロキシのCONNECT許可も確認する。HTTPプロキシ対応はUDP中継を含まない。「UDP接続・IP検出中」の失敗はUDP経路を別途確認する。音声のトークン・セッションID・暗号鍵・プロキシURLはログへ出さない。
- 設定方法は `frontend_discord/README.md` を参照する。環境変更後は旧パネルを閉じ、設定済みの起動元から開き直す。`panel/desktop.cjs` の fork は親環境を標準で継承する。GUIの起動元が端末と同じ環境を持つかは実機で確認する。
- `checks/network.test.ts` は外部通信なしで大小文字・NO_PROXY・直接経路・失敗後の回収を検証する。模擬HTTP CONNECTプロキシとHTTPS/Gatewayを用い、実際の discord.js ClientReady と resume、認証付きプロキシ、ローカル通信の除外、実SDKの接続途中停止とスレッド終了も確認する。`checks/fixtures/network-*.fixture` はテスト専用の自己署名証明書・秘密鍵であり、製品には使用しない。子プロセスの `NODE_EXTRA_CA_CERTS` だけで信頼し、TLS検証を無効化しない。
- `node checks/network-diagnostic.mjs` はBot設定を読まず、直接経路と環境経路の公開REST・認証前Gateway HELLOを比較する。通常テストから分離し、経路の失敗だけでは非ゼロ終了しない。Bot認証、対象PCのGUI接続、Hermes返信、音声UDPと実通話は別途確認する。
- `checks/fixtures/network-runner.ts` は実際のLive adapterとvoice SDKを使い、模擬CONNECTプロキシ経由の非443ポートへの音声WSS接続、ローカル通信の除外、接続待ち中の停止も確認する。模擬音声WSSの成功を、UDP・DAVE・実通話の成功とは扱わない。

## 音声変更時の注意

- 音声開始の成功判定にはソケット登録の `init` とProviderの待受準備を区別する。Discordはaudioの `connect` に `Live準備確認: true` を付け、同じセッションの `live_ready` を待ってからマイク中継・接続成功通知を開始する。バックエンドの `AIライブ.py` の `待受準備確認` は、Gemini / FreeAI のLiveセッション確立、OpenAIの `session.updated` による設定反映を確認する。要求しない旧クライアントは従来のinit完了方式を維持する。変更反映にはcoreとDiscordの両方を再起動する。
- 「接続しました」後に無応答なら、`[Discord Live]` の「待受準備が完了」「Discordの受信音声を復号」「AIの音声応答を受信」を順に確認する。最初の音声フレームだけを記録し、PCMや話者ID・設定値をログに出さない。Providerの拒否理由・コードは `connection-error.ts` で秘密値を伏せ、開始失敗時はBot、開始後はLive接続から一度だけ通知する。Discordの音声接続待ちは停止時にAbortSignalで解除する。
- 「Discord のボイス接続でエラー」はVoiceConnectionの例外であり、BotのGateway接続成功やLiveAIの準備完了とは別に確認する。通知の「ボイス状態」「音声通信」（WebSocket接続・認証、UDP接続・IP検出、暗号方式選択、Ready、再接続）と、後続の「原因 / 種類・コード・内容」を照合する。汎用案内だけではネットワーク障害や暗号化の失敗を断定しない。受信ストリームの暗号化例外とOpus復号例外も元の原因を保持する。SDKのdebugやnetworking全体にはボイストークン・暗号鍵が含まれるため出力せず、状態名と伏せ字済み例外だけを残す。`checks/live.test.ts` で接続後のボイスエラー・受信エラーの原因保持、秘密値除外、一度だけの終了通知を確認する。
- `checks/live.test.ts` と `checks/bot.test.ts` でinitのみでは入力を始めないこと、待受完了後の入力、準備中の終了、拒否理由の保持と伏せ字を確認する。バックエンドは `tests.test_live_text_response` と `tests.test_live_project_connection` でProvider設定受理と `live_ready` / `error` の通知順を検証する。

- Discord 音声は Opus / 48kHz / stereo。AI 入力は PCM16LE / mono / 16kHz または24kHz、出力は24kHz。
- 出力の20ms送出間隔は `@discordjs/voice` の AudioPlayer に任せる。Readable 側でも20ms待つとエンコード時間分の遅れが累積して無音が挿入されるため、要求時に即座に1フレームを渡し、highWaterMark で先読み量を制限する。
- AI 出力チャンクは20ms（24kHz mono PCM16で960バイト）単位とは限らない。端数を到着ごとに無音で埋めると、連続音声の途中に無音が混ざる。端数は次のチャンクと結合し、追加が60ms止まったときだけ発話末尾として無音で埋める。`checks/audio.test.ts` で分割受信時のOpusが連続PCMから生成したOpusと一致すること、および末尾の端数が失われないことを確認する。実通話でのざらつきが解消したかは別途試聴する。
- 音声間の無音を省くと AI の発話終了判定が止まる場合がある。
- `backend_server/AIコア/AI音声処理.py` の `音声入力データ処理` は、独自音量判定と切り離して全入力PCMをLiveAIへ渡す。音量判定で転送を絞ると、小声や一定音量の長い発話、発話末尾の無音が欠ける。OpenAI の `server_vad` は受信した無音で発話終了を判定するため、クライアントからの無音をバックエンドでも維持する。独自判定は音声認識バッファと再生割り込みに使う。
- レートの検証はサイズだけでなく実Opusの1秒音声の時間・周波数・音量を比較する。`checks/live.test.ts` では初期選択と異なる `init.LIVE_AI_NAME` でも、OpenAI が20msあたり960バイト、Gemini / FreeAI が640バイトのPCM16 monoを同じaudioソケットへ送ることを確認する。
- バックエンドの連続転送は `backend_server` で `uv run --locked python -X utf8 -m unittest tests.test_live_text_response` を実行する。4秒の一定音量発話と1.6秒の無音を、OpenAI / Gemini の送信アダプターまで欠落なく渡す回帰テストを含む。実Providerの発話終了イベントと実通話は別途確認する。
- 古い受信ストリームの遅延 close で、新しい同一話者のストリームを削除しない。
- 明示的終了、片側切断、途中の接続失敗、参加者全員の退出のすべてでタイマー・ソケット・Opus・プレイヤーを回収する。
- Discord パッケージ更新時は DAVE ライブラリと Node.js 必要版を実際の package.json / 公式資料で確認し、package-lock.json を更新する。
- WebSocket の `init` 成功だけでは AI の音声応答までは確認できない。文字要求後の `output_audio` も確認する。Provider が内容なしの `generation_complete` / `turn_complete` を返す場合は、短い自然な質問と別モデルで比較し、Discord のデコーダー障害と区別する。モデルを変更する場合は、共通の `LIVE_*` が他フロントエンドにも使われる点に注意する。

## 出力チャンク境界と末尾処理の再修正チェック

### 修正内容と関連箇所

- `src/audio.ts` の `Discord音声出力.追加` は PCM を結合し、空でない追加だけで `lastAudioAt` を更新する。`_read` は960バイト未満の端数を保持し、最後の追加から60ms未満なら端数を消費せず Opus 無音パケットを返す。60ms以上で末尾を960バイトへゼロ埋めする。数値の同期元は同クラスとする。
- 完全な960バイトのフレームは待機せず変換する。チャンクごとのゼロ埋めをやめることと、AudioPlayer に送出間隔を任せることは別の条件であり、両方を維持する。
- `checks/audio.test.ts` の「20ms未満のチャンクは続きが届くまで保持し…」は `Date.now` をモックし、分割チャンクからの Opus を連続PCMから生成した Opus と比較する。待機中に端数を消費しないこと、60ms後に末尾を一度だけ送出することを確認する。
- 同ファイルの「再生側の要求ごとに20msのOpusを即座に供給し…」は連続フレームの即時取得、実 Opus デコード後のサイズ、バッファ上限と破棄を確認する。エンコーダーは状態を持つため、比較側にも同じ順番でフレームを与える。

### 次回の注意点と確認方法

1. 編集前に `_index.md` と本手順を読み、上記クラス・テストの現行実装を照合する。行番号ではなくクラス名・テスト名を入口にする。
2. 60msは発話末尾を推定する猶予であり、明示的な終了通知でも `_read` 内の待機タイマーでもない。空チャンクで猶予を延長せず、無音パケットの送出とPCM端数の消費を混同しない。
3. 回帰テストを追加する場合は実時間の sleep に依存せず、モック時刻とフレーム比較を使う。59ms/60msの境界や空チャンクも、変更対象に応じて確認候補にする。既存テストが全候補を網羅済みとは扱わない。
4. 本体を変更する作業では `frontend_discord` で `npm run check` と `npm test` を実行する。単体テスト成功と実通話での試聴を区別する。知見整理だけの依頼では、本体・テスト・設定・再起動ファイルを変更しない。

## ライブモデル・声の候補

- `src/live-catalog.ts` が `_config/AiDiy_live_gemini.json` / `AiDiy_live_openai.json` の `models` / `voices` を表示順ごと読み込む。FreeAI は Gemini と同じ一覧を使う。Core 未起動でも候補を表示できる。
- パネルの Live モデル・音声は選択式とし、共通設定や保存済み設定から候補を追加しない。保存時・開始時も候補と照合し、削除されたモデル・音声では接続せず選び直しを促す。読込失敗時は既定候補へ置き換えない。
- `checks/live-catalog.test.ts` / `checks/panel.test.ts` で JSON 読込、順序、FreeAI 共有、削除済み選択による保存・起動の拒否を確認する。候補編集後はパネルを開き直し、Core 側の候補も更新する場合は Core を再起動する。

## 接続中にパネルを閉じる・直後に再起動する場合

- `panel/desktop.cjs` は worker の終了までウィンドウを保持する。閉じる操作が重なっても終了処理は一度だけ開始し、終了待ち中の `before-quit` は毎回キャンセルする。
- worker の終了済み判定には `exitCode` と `signalCode` の両方を使う。シグナル終了時は `exitCode` が `null` のため、この値だけで判定すると、発火済みの `exit` を再び待って重複起動ロックが残る。起動失敗で PID が無い場合も待たない。
- 終了応答が15秒無い場合は対象 worker のプロセスツリーを停止する。強制停止後も最大3秒で待機を終える。通常の Node / Electron や別アプリを名前だけで停止しない。
- 終了待ち中の `second-instance` には `closing` と親 PID を通知する。`panel/launch.mjs` は旧プロセス終了後に起動し直し、表示完了まで確認する。消える予定のウィンドウを起動成功と通知しない。
- Bot の終了は Live・Code・Gateway の回収を並行して開始する。返信先取得などの REST 応答やモデル候補 CLI の完了を待ってから Gateway を切断する順序に戻さない。遅れて戻った音声開始処理は `closing` で拒否する。
- `checks/desktop.test.ts` / `checks/launch-restart.test.ts` で閉じる連打、シグナル終了済み、worker 起動失敗、強制停止、終了中の再起動をモック確認する。`checks/bot.test.ts` / `checks/panel.test.ts` では通信・CLI待ちが切断開始を妨げないことを確認する。実際の Discord 通話と Windows の GUI 再起動は別途確認する。
