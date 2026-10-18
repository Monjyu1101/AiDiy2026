# 環境診断の運用

`backend_diag` は、Node.js の診断サーバーを Electron / Web で表示する任意起動の診断ツールです。起動・認証・Codespaces・検証の詳細は [backend_diag/README.md](../../backend_diag/README.md) を参照してください。

- セットアップとクリーンアップでは最初の選択項目に置き、既定 `[y]/n`、全体の a=auto でも対象にします。
- 通常は `aidiy_diag` で Electron 起動、`aidiy_diag --browser` で Web 起動します。Codespaces / GUI なしでは Web です。Electron は既存 `scripts/_setup_electron.py` の共有 ZIP / 同版 dist を使ってセットアップします。Node.js 自体が無い場合はランチャーが理由と公式導入先を表示します。Python は診断アプリ起動には不要です。
- `aidiy_diag --headless` は画面を開かず全診断をコマンドラインで最速実行し、`_AIDIY/aidiy_diag/install_info.json` へ保存します。画面の「書込」「全テスト」も同じ形式で保存します。画面の「全テスト」は外部連携（Hugging Face / Discord）の読み取り専用の認証確認と `integration_info.json` への保存も行いますが、headless では外部連携を確認しません。実行に失敗した場合は既存の結果を書き換えません。
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

キー設定・モデル一覧と、Tools 接続中だけ表示する「設定モデル」を分離します。試行は利用者の開始操作で15役割を順番に確認し、同一設定だけ実行内で共有します。Chat / Code は MCP、Live は非公開の固定 loopback アダプターを使用します。Chat / Code は既存 MCP の通常ツールを呼び、診断専用の CLI・認証・provider 経路は作りません。キーの値は表示せず、外部送信・課金があり得る試行を起動・headless・全テストから自動実行しません。詳細な API と mock 検証手順は backend_diag/README.md の「設定モデル」を参照してください。

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

## 判断用モデル一覧

`モデル情報/decisions_info.mjs` が `_AIDIY/aidiy_diag/decisions_models_info.json` を生成する。既存の `*_models_info.json` 命名を使用し、`desisions_model_info.json` は作成しない。スキーマは `{openai_oauth: {models: {モデルID: 表示名}}, openai_decisions: ..., freeai_chat: ..., gemini_chat: ...}`。表示名は `YYYY/MM/DD - ID`、取得日が不明なら `yyyy/mm/dd - ID`。認証付き一覧を取得できた方式だけを含める。

- 既存のキー確認と同じGET・ページング・proxy/TLS・制限時間・キャンセルを使い、追加の生成API試行は行わない。判断用の元一覧は公開補完前に分離する。OpenAIは既存の240日・廃止モデル除外、OAuthはAPIが返した表示対象IDのみ、GoogleはgenerateContent対応モデルから候補を作る。明らかな音声・画像・Live・埋込などの専用モデルを除く。JSON/Decisions対応の保証ではなく、実行可否はToolsの既存起動チェックで確認する。
- 公開OpenRouter一覧・同梱キャッシュ・OAuthの固定候補・将来版や900kの合成候補・設定モデルからの補完は行わない。認証の証跡は実行中のメモリだけに保持し、キー値や指紋をJSONへ保存しない。
- 書込時に現在のキー（OpenAIは組織も）またはOAuthトークン・アカウントが取得時と一致することを確認する。キー変更・削除、一覧取得失敗、旧JSONだけが残っている状態は候補にしない。個別確認後は同じDiag実行内で保持する他方式の有効な取得結果を使うが、再起動や設定再読込後は再確認が必要。
- FreeAI/Geminiは判断実行と同じ優先キーを使い、優先キー未設定時だけ他方の認証付き取得結果を代用する。キーが設定済みで認証に失敗した場合は代用しない。
- 空の方式は省略し、全方式が空なら `{}` を保存する。設定・autoの選択順・方式別既定値は書き換えない。生成確認済みの利用可能モデルとこの候補一覧を混同しない。
- headlessと画面のモデル書込は共通処理で生成し、保存先一覧にもファイル名を含める。Pythonの読込口は `conf_models.get_decisions_models()`。Web/Avatar設定画面もこの一覧を利用し、取得済み候補と設定保持値を区別して表示する。
- モック検証: `node --test backend_diag/checks/decisions-info.check.mjs`。4方式、認証変更、公開/固定/旧保存候補の排除、キー代用、失敗・空一覧、共通書込とheadlessの保存先を確認する。

### 判断系4方式の候補管理（2026-10-18）

autoの優先順は `openai_oauth` → `freeai_chat` → `openai_decisions` → `gemini_chat`。起動チェックに成功した方式だけを優先対象にする。

判断系の低コスト方針は `backend_diag/モデル情報/decisions_info.mjs` の `DECISION_MODEL_CANDIDATES` で書き出す候補を絞って管理する。現在はOpenAI両方式が `gpt-6-luna`、FreeAI/Geminiが `gemini-flash-lite-latest`。将来別モデルへ変更するときはこの候補配列を調整し、認証付き一覧を再取得・書き出しする。実行側や画面にモデル固定・恒久的な選択禁止は置かない。

[Google公式alias説明](https://developers.googleblog.com/en/continuing-to-bring-you-our-latest-models-with-an-improved-gemini-2-5-flash-and-flash-lite-release/) でIDを確認した。最新への追従はGoogle側のalias更新を利用し、番号を推測・並べ替えしてモデルを生成しない。[公式モデル一覧](https://ai.google.dev/gemini-api/docs/models) では現時点の安定版Flash-Liteは `gemini-3.5-flash-lite`。latestは安定版専用aliasではなくプレビュー等を指す場合もあるため、現在の解決先バージョンはこの実装で断定しない。

Diagは認証付きGET一覧に候補配列のIDそのものがある方式だけを掲載する。GoogleはgenerateContent対応を要求する。公開一覧・設定値・別バージョンから候補を捏造しない。未取得・認証なし・失敗・対象ID不在なら方式を省略し、全方式が空なら `{}`。モデル一覧は実行の許可リストではなく、設定画面の候補として扱う。

## OpenCode / Copilot のCode候補

`code_models_info.json` の `opencode_cli.models` はCopilot候補を共通元とし、OpenCode出力側だけClaude系を除外する。残るID・表示名・順序は保持する。取得モデルが空なら共通の `COPILOT_FALLBACK_MODELS` から同じClaude除外で補完する。Copilot側の取得候補・固定8候補は変更しない。OpenCodeは独自認証を使う前提で、出力可否は自身の導入検出だけで決め、Copilot未導入でも出力できる。補完はモデル候補の書き出しだけで、認証・実行成功のステータスへ変更しない。検証は `checks/models-info.check.mjs` のOpenCode各ケースで行う。

## 判断モデルの手動試行

設定モデル動作確認のLIVE直後に `DECISION / 挨拶の丁寧さ` を表示する。個別「テスト」と全体「動作確認」の両方で、既存MCP `/aidiy_decisions_check/mcp` の `decisions_check` を呼ぶ。HTTP `/check` への代替直結は行わない。Tools接続中の明示操作に限定し、headless・起動・全診断では実行しない。

`DECISION_AI_NAME` と方式別 `DECISION_OPENAI_MODEL` / `DECISION_OAUTH_MODEL` / `DECISION_GEMINI_MODEL` / `DECISION_FREEAI_MODEL` が不足時はauto。方式が明示されている試行行は対応する方式別値を使い、キー未存在時だけ旧 `DECISION_AI_MODEL` を参照する。方式autoの行はモデルもautoで送り、Toolsで方式とモデルを解決する。autoの方式順はOAuth → FreeAI → Decisions API → Gemini。結果には実効モデルを表示し、設定ファイルへは書き戻さない。

入力は「おはよう」、質問は挨拶としての丁寧さ、choice名は `politeness`、選択肢は `high / medium / low`。3値すべてを正常な選択として受け付け、特定値を正解とはしない。MCPのJSON内のstatus、回答名・型・選択値、3候補の確率分布・合計、confidenceを検証する。不正JSON・欠落・未知選択肢・通信エラーはNG。結果詳細に選択値と検証済みJSON、実際の実行モデルを表示する。

Chat/Live/Codeと判断結果は共有しない。MCPの初期化・セッション破棄、設定変更による結果破棄、既存のタイムアウトを共用する。判断の行期限を超えた場合はNGと理由を表示し、その全体実行を終了する。ユーザーによる中止は従来の中止表示を維持する。

検証は `checks/decision-trials.check.mjs`、既存モデル試行/API/音声/UIテスト、`DIAG_TEST_PYTHON` を指定する実MCP SDK fixtureで行う。fixtureの生成APIはMockTransportへ置換し、外部の生成サービスを使わない。Web/Avatarの設定画面とDiag試行UIは同じ候補と通常のモデル解決を使う。


## AIモデルの手動試行

「AIモデル」はChat / Live / Decision / Codeの4画面です。初期値はconfigのCHAT・LIVE・DECISION各設定とCODE1を使います。Decisionの方式autoはモデルもautoとしてTools側で解決します。入力の「おはよう」とDecisionのpoliteness / high・medium・lowは `モデル試行/defaults.mjs` を既存設定モデル試行と共用し、手動画面では自由に編集できます。

候補は `_AIDIY/aidiy_diag/{chat,live,decisions,code}_models_info.json` と `live_voices_info.json` の保存済み内容だけです。画面初期読込・再読込は認証付きローカルDiag APIを使い、外部モデル取得は行いません。プロバイダ変更は画面内で候補を連動し、一覧外の設定保持値を未確認として残します。候補の存在は認証・モデル利用成功の保証ではありません。選択や入力をconfigへ書き戻しません。

試行はTools接続中の明示操作だけです。既存 `モデル試行/trials.mjs` のMCP初期化・呼出し・セッション終了、逐次実行ロック、設定変更検知、期限、音声保存を共用します。Chatは `chat_llms_run`、Codeは `code_agents_run`、Decisionは `decisions_check` をHTTP MCPで呼び、Liveだけは既存 `/internal/live_model_check` へ明示した方式・モデル・音声・入力を渡します。Liveの接続後10秒待機とアダプター終了処理は共通です。空JSONの従来Live試行は従来のconfigと固定挨拶を使います。

AIモデルタブのタイトルバー「一括試行」は4画面の入力を開始時に固定し、Chat→Live→Decision→Codeを1実行として順に呼びます。NG・行タイムアウトでも次へ進みます。連打は抑止し、入力変更・実行中の画面移動・Tools切断で中止して古い結果を破棄します。全診断・headless・起動ではAI試行しません。設定モデルの15項目試行とAIモデルの4種試行は別の操作です。

Decisionは1問ずつpredicate / choice / scoreを選び、質問名・質問文と、必要な選択肢／段階（2〜32件、重複不可）を編集します。戻り値全体はJSONを読めればインデント付き、読めなければ元文字列を安全なテキストとして表示します。表示できることと回答スキーマの成功判定は別です。既知の秘密値は伏せます。

Liveの応答テキストと1秒以上のWAVを表示し、認証付き音声APIからBlobを取得してネイティブプレーヤーで再生します。自動再生しません。一括試行中はLiveの一時音声を保持し、完了後も再読込可能です。再試行・画面移動では再生を停止し、Object URLを解放します。短い音声・音声なし・取得失敗は明示し、音声だけを再読込できます。

検証は実AIを使わず、`checks/manual-models.check.mjs`、`ui/src/AIモデル/checks/manual-state.check.mjs`、`backend_tools/tests/test_live_model_check.py` を使います。`DIAG_TEST_PYTHON` をTools依存環境のPythonへ設定すると `checks/model-trials-sdk.check.mjs` が実MCP SDKと合成AIで経路を確認します。`checks/manual-models-browser.mjs` は既存Chrome/Edgeの隔離プロファイルで4画面・幅1280/720/390・合成音声再生・破棄・一括試行・非JSON表示を確認します。UI変更後は依頼に応じて `backend_diag/ui` のビルドと `node backend_diag/ui/verify.mjs` で配布物を同期します。
