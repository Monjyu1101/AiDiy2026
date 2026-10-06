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

## 音声変更時の注意

- Discord 音声は Opus / 48kHz / stereo。AI 入力は PCM16LE / mono / 16kHz または24kHz、出力は24kHz。
- 出力の20ms送出間隔は `@discordjs/voice` の AudioPlayer に任せる。Readable 側でも20ms待つとエンコード時間分の遅れが累積して無音が挿入されるため、要求時に即座に1フレームを渡し、highWaterMark で先読み量を制限する。
- AI 出力チャンクは20ms（24kHz mono PCM16で960バイト）単位とは限らない。端数を到着ごとに無音で埋めると、連続音声の途中に無音が混ざる。端数は次のチャンクと結合し、追加が60ms止まったときだけ発話末尾として無音で埋める。`checks/audio.test.ts` で分割受信時のOpusが連続PCMから生成したOpusと一致すること、および末尾の端数が失われないことを確認する。実通話でのざらつきが解消したかは別途試聴する。
- 音声間の無音を省くと AI の発話終了判定が止まる場合がある。
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
