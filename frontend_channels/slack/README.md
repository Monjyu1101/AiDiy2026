# AiDiy Slack

> Discord 版（`frontend_channels/`、`aidiy_discord`）から音声会話を除いた双子のプログラムです。ファイル構成・画面・起動引数・試験をそろえ、接続部品とモデル設定だけが異なります。

自分と AiDiy の専用チャンネルに普通に投稿すると、`aidiy_hermes` がスレッドで返信します。スレッド内の続きは同じ会話として続きます。チャットは `frontend_ide/host` の Code と同じ CLI 実行処理を使います。

## ウィンドウ操作

Electron のタイトルバーは「ー □ 📌 ×」で最小化・最大化／復元・最前面ピン・終了を操作します。Discord 版と同じです。ブラウザ版はブラウザ側のウィンドウ操作を使います。

## 導入

- Node.js 22.12 以降。
- `command_hermes` をセットアップし、使う Provider を認証しておきます。
- `frontend_ide/host` のソースを同じプロジェクトに保持します。

プロジェクトルートで実行します。

```powershell
python frontend_channels/slack/_setup.py
```

`npm ci` → `npm run update:electron` → `npm run build:panel` → `npm run check:panel` → Electron 本体の配置 → `~/.local/bin/aidiy_slack`（Windows は `.cmd`）の登録、の順に Discord 版と同じ手順で導入します。Electron 本体は他のフロントエンドの配置・共有 ZIP を再利用します。ルート `_setup.py` の「Slack」からも導入できます。

## プロキシが必要なネットワーク

WebSocket（Socket Mode）は使わず、外向き HTTPS の Web API（`auth.test` / `conversations.history` / `conversations.replies` / `chat.postMessage` / `chat.update`）だけで送受信します。`HTTP(S)_PROXY` / `NO_PROXY`（大小文字とも）を参照します。429 は `Retry-After` に従って最大3回、最長30秒待って再試行します。

## Slack 側の準備

1. Slack アプリを作成し、Bot Token Scopes に `chat:write` と `channels:history` を付けてワークスペースへインストールします。
2. 専用のパブリックチャンネル（例: `#aidiy`）を作り、アプリ（Bot）をチャンネルに追加します。

## 接続情報

`_config/AiDiy_key.json` に設定します。

| キー | 内容 |
|------|------|
| `slack_bot_token` | Bot User OAuth Token（`xoxb-` で始まる） |
| `slack_team_id` | ワークスペースの ID（`T…`） |
| `slack_allowed_user_id` | 利用を許可するユーザーの ID（`U…`） |
| `slack_text_channel_id` | 専用チャンネルの ID（`C…`） |

`slack_app_token` は使いません。Hermes のモデル・作業フォルダは共通の `CODE_AIDIY_HERMES_MODEL` / `CODE_MAX_TURNS` / `CODE_BASE_PATH` を使います。

## 起動と操作

```powershell
aidiy_slack
```

画面中央上部に小さなパネルが開き、前回のモデルで Slack へ自動接続します。初回（接続時の設定が未保存）は自動接続せず、モデル設定画面から始まります。モデルを選んで「接続」を押すと設定が保存され、次回から自動接続します（Discord 版と同じ動き）。「切断」を押すとモデル選択の画面に戻り、モデルを選び直して「接続」で再接続できます。コードは「aidiy_hermes」の固定表示で、モデルを `auto`（自動判定）／`same`（変更なし）／`codex_cli/same` などの CLI 名付き／`openai_oauth/gpt-…` などの一覧から選びます（aidiy_code と同じ指定）。候補は AIコアのモデル情報APIから取得し、停止中は `_AIDIY/aidiy_diag/code_models_info.json` を読みます。未保存時の初期表示は共通設定の `CODE_AIDIY_HERMES_MODEL` です。接続中に「×」で閉じると「接続中です。終了しますか？」と確認し、「キャンセル」なら接続を続けます。切断中はそのまま終了します。接続に失敗した場合も、エラーの案内と詳細を表示したモデル選択の画面に戻ります。

接続中は AiDiy の絵と、最後のやり取り（「あなた」の投稿と「AiDiy」の回答）を1件だけ表示し、約1分で消します。プロジェクト行の下には「CODE ON」を表示します。

画面下部には aidiy_code と同じ「モデル ▾」と現在のモデル（`AI - モデル`）を表示します。未接続で押すと設定欄へ移り、接続中に押すと設定欄を開いて「適用して再接続」で切断・保存・再接続、「キャンセル」で変更を戻して接続を続けます。

起動引数は `aidiy_discord` と同じです。

| 引数 | 内容 |
|------|------|
| `[作業フォルダ]` / `--project` | コードの作業フォルダ（省略時は起動したフォルダ） |
| `--no-connect` | 自動接続せずに開く（`--connect` は従来の指定として受け付ける） |
| `--browser` | ブラウザ版で開く（Codespaces・画面のない Linux では自動） |
| `--check` | 設定と Hermes の起動パスだけを確認し、Slack には接続しない |
| `--wait` | パネルの終了まで待つ |

Diag の Slack ボタン、ルート `_start.py` で Slack を Yes にした場合も同じパネルを開いて自動接続します。全体の終了後もパネルは継続し、停止はパネルの「×」か `_cleanup.py` で行います。パネルを重ねて起動すると既存の画面を表示します。

モデルの選択は `~/.aidiy/aidiy_slack.json` の1ファイルに、コードの実行環境（`code_name`、現在は `aidiy_hermes` 固定。将来の別ハーネス用）とモデル（`code_model`）として保存します。このファイルがあれば起動時に自動接続します。旧形式の `aidiy_slack_code_model.json` は、初回の読込で1回だけ移して削除します。起動ログは配置先リポジトリの `temp/aidiy_slack/logs/`、起動完了通知は `temp/aidiy_slack/runtime/` に保存します。

画面を使わずに Bot だけを前面で動かす場合は、`frontend_channels/slack` で `npm run bot` を実行します（Ctrl+C で停止）。

### ブラウザ版（Codespaces など）

`aidiy_slack --browser` で、Electron の代わりにブラウザでパネルを開きます。画面・操作は Electron 版と同じで、パネルのサーバー（`src/web-server.ts`）と WebSocket でやり取りします。規則は Discord 版と共通です（`frontend_ide/host/scripts/launch-project.mjs`）。

## クリーンアップ

ルート `python _cleanup.py` の Slack 項目、または単独の `python frontend_channels/slack/_cleanup.py` で、この作業コピーのパネル・Bot を子孫プロセスごと停止してから、`node_modules`・`out`・`temp`・Python キャッシュと `aidiy_slack` ランチャーを削除します。ソース、`package-lock.json`、`_config/AiDiy_key.json`、前回のモデル選択は残ります。

## 会話のしかた

- 専用チャンネルに投稿すると、その投稿へのスレッドで返信します（先に「考えています…」と投稿し、回答で書き換えます）。
- スレッド内の続きは同じ Hermes 会話として続きます（直近 20 スレッド、2 時間やり取りがなければ外れます）。
- `!aidiy stop` で停止、`!aidiy new` で会話のやり直し、`!aidiy status` で状態、`!aidiy help` で使い方を表示します。
- 長い回答は 3500 文字ずつに分けて投稿します。

## 接続パネルの Vue ソースと配布物

`panel/画面/接続パネル.vue` が画面、`機能切替.vue` が共通トグル、`panel/接続/パネル状態.js` が状態管理です（Discord 版から Live・音声表示を除いた同じ構成）。`panel/view.js` は事前コンパイルした配布物として同梱します。

画面ソース・依存関係を変更した場合だけ、次を実行します。

```powershell
npm ci
npm run build:panel
npm run check
npm test
```

`npm test` は Discord 版と同じ観点の試験（画面・窓・起動入口・Web サーバー・配置・配布物・通信・コマンド・設定）を実行します。Python 側は `python -m unittest frontend_channels/slack/checks/test_lifecycle.py` です。

## 著作権・ライセンス

独自実装には Discord 版と同じ定型文を使用します。ライセンス全文は [../LICENSE](../LICENSE) を参照してください。第三者ライブラリ（Vue など）の表記は `panel/THIRD_PARTY_NOTICES.txt` にあります。
