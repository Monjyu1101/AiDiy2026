# aidiy_slack 実装準備

> 実装準備の設計書。基点: `8cc0cd7acac2c9b74f72b60fd8a3d6159194f812`。
> 公式文書確認: 2026-10-30。
>
> 今回の実装範囲は共通設定のSlack接続5欄、Diag既存処理の秘密値除去、回帰試験、
> lifecycle入口の通常「Discord / Slack」表記、Diag外部連携のSlack Bot認証確認とDiagランチャー登録。Slack runtime・reader・設定画面/API・
> 実接続・Discordフォルダ移動はまだ行っていない。以下は次段階の設計と受入条件。

## 1. 独立したDiscord / Slackモジュール

目標は `frontend_channels/discord/` と `frontend_channels/slack/` の対称な2モジュール。
SlackだけをDiscordの従属サブモジュールにしない。両者が各自の次の実体を持つ。

```text
frontend_channels/
  discord/
    package.json / package-lock.json / node_modules/
    src/ / panel/ / out/ / checks/ / scripts/ / assets/
    _setup.py / _start.py / _cleanup.py / launcher.py
  slack/
    package.json / package-lock.json / node_modules/
    src/ / panel/ / out/ / checks/ / scripts/ / assets/
    _setup.py / _start.py / _cleanup.py / launcher.py
```

- コマンドは `aidiy_discord` と `aidiy_slack`。依存導入・再構築・起動・停止・cleanupは各モジュール単位。
- 各モジュールのlock/依存/生成物を相手のsetupやcleanupで変更しない。認証情報はcleanupで削除しない。
- 共通設定ファイル `_config/AiDiy_key.json` は維持。名前空間は `discord_*` と `slack_*` に分離する。
- Code/Hermes、モデル候補、履歴の契約は既存連携を調査して共用するが、SlackからDiscord内部をimportしない。
- UI素材は各モジュール内の **ローカルコピー** を持つ。build/test/runtimeで兄弟のassetを読むことを禁止する。
  シンボリックリンク、実行時コピー、兄弟`node_modules`探索、外部CDNへのfallbackも作らない。
- 素材の元データ・ライセンス・生成手順を同梱し、配布manifestとsourceの照合を行う。
- Windows/POSIXのパス、`__file__`/`import.meta.url`からのroot解決を明示し、cwdに依存させない。

## 2. 初版の接続・会話範囲

Socket Mode + Bot Web APIを採用する設計。1 workspace・1専用テキストチャンネル・
許可ユーザー1人の通常投稿をCode/Hermesへ渡す。初版ではDM、複数workspace、
チャンネル全体への任意反応、Slack Connect外部参加者、Huddle/音声Liveを扱わない。

- `aidiy_slack` は接続パネルを開く。将来の `--connect` だけ明示的に接続する。
- Slackの通常表示はDiscordと同じ粒度。lifecycle画面へ特別な準備中ラベルを付けない。
- 初期表示・setup・cleanup・headlessでSlack API認証や投稿を自動実行しない。Diagの外部連携「状況確認」「テスト」「全テスト」は、利用者の明示操作でBot認証だけを確認する。
- 接続開始/停止、状態、設定確認、Codeモデル、会話停止/リセットを同じパネルから操作する。
- 1親投稿を1会話とし、応答と継続投稿は同じスレッドへ返す。キーはteam/channel/threadの組合せ。
  threadのイベント順序を維持し、重複イベントで同じHermes実行/投稿を増やさない。
- 停止は当該会話の実行だけを止め、別threadやDiscordのプロセスを巻き込まない。

Socket Modeはapp-level tokenからWebSocket接続を確立し、イベントのenvelopeへackを返す。
AI完了までackを待たず、受信検証・重複排除後に処理キューへ渡す設計にする。
[公式Socket Mode](https://docs.slack.dev/apis/events-api/using-socket-mode/)、
[connections:write](https://docs.slack.dev/reference/scopes/connections.write/)。

## 3. 設定契約

Discord欄の直後に次の5項目を置く。今回追加したのはこの初期値定義まで。

| キー | 初期値 | 役割 |
|---|---|---|
| `slack_bot_token` | `< your slack bot token >` | Bot Web API |
| `slack_app_token` | `< your slack app-level token >` | Socket Mode |
| `slack_team_id` | `< your slack workspace id >` | workspace固定 |
| `slack_allowed_user_id` | `< your slack user id >` | 利用者1人固定 |
| `slack_text_channel_id` | `< your slack text channel id >` | 専用チャンネル固定 |

将来readerは非文字列を拒否する。tokenはtrim後length<=1、`<`で始まる仮設定、内部空白を拒否する。
型・IDを検証するときに実値をエラーへ埋め込まない。Slack IDをDiscord数値IDルールで検証しない。
接続時はtokenの形式推測だけを信用せず、返されたworkspace/Bot情報と固定team/channel/userを照合する。
IDや権限が空・未知ならfail closed。Discord値へのfallbackは設けない。

保存クラスは不足キーを補い、既存値を保持する。既存の不正値を黙って正常化しない。
実接続readerは別工程とし、今回のPython試験が接続検証済みを意味しない。
Code作業フォルダ・Hermesモデル・ターン上限などは既存共通設定を利用し、Slack専用コピーを増やさない。

## 4. 受信・送信の安全境界

1. workspace、channel、userを許可値と完全照合する。権限確認より前にCLI/LLMを起動しない。
2. Bot自身・他Botの投稿、編集/削除通知、対応外subtype、重複配信を通常入力として扱わない。
3. イベントID・スレッド状態の保存は境界と上限を持ち、再接続後の再配信でも二重実行しない。
4. メッセージ本文はデータとしてstdinへ渡し、シェル文字列へ連結しない。
5. エラー本文、APIオブジェクト、URL、headers、WebSocket URL、添付download URLにtokenを残さない。
6. token2種をDiag既存secret sanitizer対象に保持する。外部連携には `slack` / `Slack Bot` を登録し、固定POST `auth.test` でBot認証だけを確認する。App token・ID設定・Socket Mode・投稿可否は確認しない。認証OKを接続済み表示に流用しない。
7. 再接続・レート制限はbounded retryとし、認証失敗を別providerへ隠蔽しない。
8. 回答はチャンネル＋`thread_ts`を固定する。長文は分割し、意図しないchannel全体通知を作らない。

受信messageにはsubtypeがあるため分岐を明示し、返信には元のthread識別子を使う。
[messageイベント](https://docs.slack.dev/reference/events/message/)、
[chat.postMessage](https://docs.slack.dev/reference/methods/chat.postMessage/)。
必要scopeは専用チャンネルの種別と機能に限定する。Bot投稿の`chat:write`、
通常投稿受信のイベント購読に対応するhistory権限を確認し、public/privateの両方を無条件に広げない。
app tokenの`connections:write`とBot tokenのscopeを混同しない。

## 5. ファイルと音声

初版でファイルを扱わない場合は未対応を明示し、本文中のURLを自動取得しない。
後続対応では容量・種類・取得先・保存先を制限し、Slackの認可済みfile情報から取得する。
秘密URLをログに出さず、ユーザーが指定していない任意ローカルファイルを送信しない。

ファイル送信を追加する場合は外部upload URL取得→アップロード→completeの現行手順を使う。
[files.getUploadURLExternal](https://docs.slack.dev/reference/methods/files.getUploadURLExternal/)、
[files.completeUploadExternal](https://docs.slack.dev/reference/methods/files.completeUploadExternal/)。
音声/HuddleをDiscord Liveと同一仕様で実装できるとは扱わず、別途公式APIと権限を調査する。

## 6. Discord移動時の確認一覧

フォルダ移動は一括文字列置換だけで完了としない。次の参照を移動commit内で照合する。

| 対象 | 確認すること |
|---|---|
| ルート `_setup.py` / `_start.py` / `_cleanup.py` | モジュール読込、選択、プロセス識別、停止・保護対象 |
| `scripts/_diag_start.py` / 起動対象定義 | 新しいモジュールrootと引数 |
| Diag起動・アプリ起動・CLI登録 | Discord/Slack別entry、PID/session、cwd、表示 |
| 各 `_setup.py` / `_start.py` / `_cleanup.py` / launcher | 自分のモジュールだけへ導入・削除・登録 |
| 既存Discord `src/共通連携/IDE連携.ts` 等 | rootからIDE/Hermes/shared configへの相対参照 |
| `panel/` / build / verify / manifest | local assetsだけを使用、配布物とsourceを一致 |
| README / AGENTS / knowledge / tests | 起動手順、fixture root、copy配置、旧パス依存 |
| `.gitignore` / package / lock / out | 独立依存、生成物の漏れ、重複lockとnode_modulesの混入 |

移動前にDiscord回帰を取得し、移動後に無接続パネル・起動/停止・再起動・cleanup保護を再確認する。
Slack導入失敗がDiscordを壊さないこと、片側削除がもう片側の依存・資産・設定を消さないことを試験する。

## 7. 段階と受入条件

- **今回:** default5欄、secret2欄、fixture試験、通常lifecycle表記。実秘密ファイルは読書きしない。
- **移動:** Discordを独立フォルダへ移動し現状機能を維持、Slack空モジュールの責務を定義。
- **実装:** Slack reader/Socket Mode/キュー/Hermes/投稿/パネル/終了処理を追加。
- **検証:** mockで認証・allowlist・bot除外・重複・再接続・429・停止・同時thread・秘密除去を網羅。
- **実機:** 明示承認されたworkspaceと専用channelでだけ接続・投稿。Windows/POSIXを区別して結果を記録する。

今回の確認コマンドは `python -m unittest discover -s backend_server/checks -p test_slack_config_defaults.py`、
Channelsのconfig試験、Diagのkey-status/model-probe/ai-settings-api回帰。
Slack実APIを呼ぶ試験は今回行わない。ネイティブSlack起動コマンドや成功表示だけを先に捏造しない。

## Discord grep による対応箇所の確認

| 分類 | 対応箇所 / 結果 |
|---|---|
| 共通設定・秘密値除去 | `backend_server/conf/conf_json.py` の接続5欄、`backend_diag/runtime/model_probe.ts` の2token秘匿は両者に対応 |
| Diag診断・表示・保存 | 同runtimeのprovider/probe、`キー設定共通/キー設定表示.mjs`、外部連携SFC、`モデル情報/integration_info.mjs` はSlack追加済み。モデル一覧とは分離 |
| 配布asset | 各module正本SVG/PNGとDiagローカルPNGコピー。兄弟moduleのassetを実行・build・verify・testから読まない |
| root/module lifecycleの説明 | 既存6入口は「Discord / Slack」。実処理のSlack登録とは区別する |
| Diagランチャー | 通常・ミニ・マイクロ・右クリックにDiscord直後のSlackを登録。固定入口 `frontend_channels/slack/panel/launch.mjs` がない現状は「未導入」で起動不可、APIも503。入口の検出と明示起動の再検証だけで、本体やPATH wrapperを作った意味ではない |
| 実行・停止・接続・会話 | `frontend_channels/launcher.py`、`discord_processes.py`、`src/接続`、`src/コード`、`panel` は現在Discord実装。Slack runtime、Socket Mode、起動コマンド、終了処理への対応はこの計画の後続工程 |
| Discord固有 | voice channel / Opus / Gateway / guild数値ID規則はSlackへ機械的に複製しない。Slackのworkspace/user/channel IDは独自規則で検証する |

Diag確認は [公式 auth.test](https://docs.slack.dev/reference/methods/auth.test/) の認証確認のみ。設定画面・新規設定API・メッセージ送信・Socket Mode接続は追加していない。


### runtime導入時のgrep確認先（Diagの登録だけでは完了しない）

- PATH: `frontend_channels/launcher.py` のwrapper生成・所有者確認・削除、root `_setup.py` の依存/build/refresh/`--launchers-only`/完了一覧。独立Slackの入口が実在する段階で登録する。
- 起動: `_start.py` のchoices/環境/起動/一覧、`scripts/起動対象.json`、`scripts/_diag_start.py`。現在の6入口の「Discord / Slack」は案内表記で、Slackサービス登録とは別。
- 停止: `_cleanup.py`、`scripts/_setup_processes.py`、`frontend_channels/discord_processes.py`。Slack独自PID/子プロセス/keep条件/owner付きwrapper除去を実装し、Discord削除や親フォルダ全体の再帰掃除に巻き込まない。
- Native: 共有helperを採用するなら `frontend_ide/host/scripts/single-instance.cjs` の対象名/lock/port、`frontend_ide/デスクトップ/{長押し窓移動,code-drag}.cjs` の `movableKinds` へSlackの独立名を設計する。Discordの識別子を流用しない。
- 独立module: own package/deps/lock/setup/start/cleanup/panelを用意し、今の親packageやDiscord出力を共有しない。`.gitignore` の現node_modules/temp指定だけでは将来の `slack/out` を除外しないため、実際の生成物/profileだけを精密に追加する。
- `command_hermes` 自身のDiscord/Slack pluginは別製品境界の既存adapterであり、`frontend_channels/slack` の完成を意味しない。過去資料・診断catalogの固定inventory・voice/Opus等のDiscord固有語を一括置換しない。

回帰は未導入/入口がdirectory/入口削除直後/連打/別Discord process/未認証/API直呼びを含む。通常・ミニ・マイクロのローカルPNG/順序と、未導入Slackの右クリック無効化も確認する。mock入口を実行せずspawn引数だけを検証し、実Slack接続やGUI確認とは区別する。
