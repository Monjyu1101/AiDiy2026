# 環境診断の運用

`backend_diag` は、Node.js の診断サーバーを Electron / Web で表示する任意起動の診断ツールです。起動・認証・Codespaces・検証の詳細は [backend_diag/README.md](../../backend_diag/README.md) を参照してください。

- セットアップとクリーンアップでは最初の選択項目に置き、既定 `[y]/n`、全体の a=auto でも対象にします。
- 通常は `aidiy_diag` で Electron 起動、`aidiy_diag --browser` で Web 起動します。Codespaces / GUI なしでは Web です。Electron は既存 `scripts/_setup_electron.py` の共有 ZIP / 同版 dist を使ってセットアップします。Node.js 自体が無い場合はランチャーが理由と公式導入先を表示します。Python は診断アプリ起動には不要です。
- `aidiy_diag --headless` は画面を開かず全診断をコマンドラインで最速実行し、`_AIDIY/aidiy_diag/install_info.json` へ保存します。画面の「書込」「全テスト」も同じ形式で保存します。実行に失敗した場合は既存の結果を書き換えません。
- ルート `_start.py` はToolsを実際に起動する直前（自動再起動時も含む）に必ず `aidiy_diag --headless` を1回実行し、モデル合成JSONの生成完了を待ちます。Tools未選択・クリーンアップによる起動スキップ時は実行しません。失敗時はToolsを起動せず終了し、すでに起動した管理対象プロセスを停止します。DiagのGUI起動を選ぶ質問はありません。
- ルート `_setup.py` のDiagは `[y]` の表示だけで選択入力を受けず、ランチャー配置とElectronの準備を必ず行います。終盤は「キャッシュクリア」の見出し、import由来キャッシュの削除、headless診断の順で実行します。診断失敗は既存の「エラーが発生しても続行」の選択に従います。単独の `aidiy_diag` は従来どおりGUIで使えます。
- Python、uv、Node.js、npm、npx、Electron、その他のコア周辺、機能別の任意依存の順に確認します。任意機能の未検出をシステム全体の故障と判断しないでください。
- 固定 version 引数に副作用が無いことを確認できない項目は、存在確認のみにします。Ollama の `--version` はサーバーへ接続するため実行しません。
- Ollama のモデル取得はローカル `127.0.0.1:11434/api/tags` 固定です。画面・headless とも、今回のインストール確認で「未検出」なら通信せず「未実施」とスキップ理由を保存します。未確認・検出エラーを未導入とは見なさず、従来の取得を続けます。
- Web 版でも全機能を使えます。Codespaces の転送ポートは Private にし、起動時の認証 URL を共有しないでください。確認対象はブラウザ端末ではなく診断サーバーです。
- カタログ追加ではソース参照と必要な機能を必ず記載します。設定ファイルのキー、ログイン情報、環境変数全体を返す診断は追加しません。

## 内部ファイルの配置

- ルートには公開入口 `diag_main.mjs` / `aidiy_diag` / `aidiy_diag.cmd` と `_setup.py` / `_start.py` / `_cleanup.py`、パッケージ設定・案内を残します。
- `起動/` は Electron・IPC・停止監視、`診断/` は導入確認・headless・カタログ、`モデル情報/` はキー確認・モデル/音声合成を担当します。
- OpenRouter の同梱 ZIP は `backend_diag/モデル情報/openrouter_models/openrouter_models.zip`。対応するローダーと同じ機能の配下に置き、静的公開する `static/` へは入れません。
- モジュール移動時は import、`import.meta.url`、Electron の package main / preload、fixture の差し替え先を追従させます。Electron の依存物・安全ログ・停止要求は従来の `backend_diag/` 基準、出力は従来の `_AIDIY/aidiy_diag/` 基準を維持します。
- `node --test backend_diag/checks/*.check.mjs backend_diag/checks/*.check.cjs` の layout / bundled-models / launcher / startup / headless テストでパスと起動の回帰を確認します。UI・runtime を変更しない配置変更では配布物を無用に再生成せず、`node backend_diag/ui/verify.mjs` で一致を確認します。

## ソース調査の基準

`backend_diag/診断/coverage.json` の基準コミットに対し、対象ソース・設定 3,333 件を全件全文静的走査し、246 候補へ整理した調査履歴を保持しています。現在の診断対象は 19 件（ベース 6、CLI群 7、その他拡張 6）です。AiDiy 起動コマンド、Hermes 専用、Mac 音声、GStreamer、Edge、Brave、OS・任意スキル・開発導入補助等 227 件は確認対象から除外しています。通常の Markdown 本文や画像・音声・モデル等は除外です。各詳細の行番号、`reference/source-manifest.json` の blob SHA、README の調査範囲を照合してください。実行時の導入・認証・接続成功の保証とは別です。

## 拡張予定（未実装）

キー設定・モデル一覧と、Tools 接続中だけ表示する「設定モデル」を分離します。試行は利用者の開始操作で14役割を順番に確認し、同一設定だけ実行内で共有します。Chat / Code は MCP、Live は非公開の固定 loopback アダプターを使用します。Chat / Code は既存 MCP の通常ツールを呼び、診断専用の CLI・認証・provider 経路は作りません。キーの値は表示せず、外部送信・課金があり得る試行を起動・headless・全テストから自動実行しません。詳細な API と mock 検証手順は backend_diag/README.md の「設定モデル」を参照してください。

## 状態インジケーター

一覧・詳細・集計・絞り込み・凡例は同じ 5 種類で表示します。
- 未確認（黒）: 未実施。OS 対象外の場合も未確認とし、詳細に対象外の理由を表示します。
- 未検出（黄）: 登録した探索先に見つかりません。
- OK（緑）: 存在確認、または固定バージョンコマンドの正常終了。存在のみ・版未取得の場合は詳細で区別します。認証や実機能の動作保証ではありません。
- NG（赤）: バージョンコマンドの非ゼロ終了、または確認した最低バージョン要件の不足。検出対象とは別の仮想環境まで否定しません。
- ERR（赤）: 起動・探索例外、タイムアウト、出力上限等により確認できません。

確認中は進行メッセージを表示し、別の判定状態にはしません。色に加えて必ず状態名も表示します。

## モデル合成が空のときの確認

- 合成 JSON はモデル0件のプロバイダを除外します。chat の local 固定候補は残り、Ollama は取得モデルがある場合だけ残ります。
- OpenRouter の匿名公開一覧は補完用です。選択候補にするには設定キーの `/api/v1/key` 確認が必要です。保存済みの認証確認だけでは合成せず、今回の認証成功結果が必要です（設定再読込後は再テスト）。キー削除・今回の確認失敗後も古い候補を引き継ぎません。
- chat が空、または候補が `local_chat` のみなら、`AiDiy_key.json` の `CHAT_AI_NAME` と対応する `CHAT_*_MODEL` を「仮設定（未検証）」として補完します。config 候補は local より前に保存し、既存 local の候補と順序を保持します。同一候補は重複させません。local 以外が1件でもあれば補完せず、設定未作成・空値・未対応プロバイダなら現状を保持します。認証成功や取得成功としては扱いません。
- live 全体が空なら `AiDiy_key.json` の `LIVE_AI_NAME` と対応する `LIVE_*_MODEL` を「仮設定（未検証）」として補完します。設定未作成・空値・未対応プロバイダなら空のままです。既存候補が1件でもあれば補完しません。code 全体が空なら従来どおり `aidiy_hermes / auto` を補います。config 自体は変更しません。
- `live_voices_info.json` は取得・認証状態にかかわらず `freeai_live`、`gemini_live`、`openai_live` の3区分を常に保存します。既存の音声定義と順序を使用し、FreeAI/Gemini は各30件、OpenAI は13件です。
- 仮モデルや音声候補の表示は、認証成功・モデル取得成功・利用可否の保証ではありません。
- OpenAI OAuth の一覧取得失敗・空一覧は、Copilot 既定の OpenAI 系4モデル（`gpt-6-astra`、`gpt-6.1-sol`、`gpt-5.6-terra`、`gpt-6-luna`）を未検証候補として補い、診断状態を PASS とします。Chat の `openai_oauth` と Hermes の `openai_oauth/` 経路に使用し、成功時は取得結果を優先します。未設定は未実施のままで4候補を補わず、明示的なログアウト後は保存済みOAuth候補を合成しません。通信失敗とHTTP認証失敗はモデル取得処理ではともに NG ですが、4候補の補完後は既存の PASS を使います。失敗理由・未検証の警告は保持し、認証確認や実モデル応答を成功にはしません。
- 回帰確認は `node --test backend_diag/checks/*.check.mjs backend_diag/checks/*.check.cjs`。実キーを使わず、未設定・無効・有効キー、旧保存結果、全区分の空プロバイダ除外、固定仮補完を合成データと設定ファイル未作成の実 headless 起動で検証します。runtime 変更後は README の配布物再生成と一致確認も行います。
