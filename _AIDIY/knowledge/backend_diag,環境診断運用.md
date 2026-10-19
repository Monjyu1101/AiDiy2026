# 環境診断の運用

`backend_diag` は、Node.js の診断サーバーを Electron / Web で表示する任意起動の診断ツールです。起動・認証・Codespaces・検証の詳細は [backend_diag/README.md](../../backend_diag/README.md) を参照してください。

総合テストの手順・実施結果・エビデンスと、その副産物として残す操作手順書素材は、別冊の[環境確認編](./セルフテスト,aidiy_diag,環境確認編.md)を参照してください。[システム起動編](./セルフテスト,aidiy_diag,システム起動編.md)・[アプリ起動編](./セルフテスト,aidiy_diag,アプリ起動編.md)とは、手順と実施結果を分けます。本書は実装・保守の運用情報を扱います。

Electronの長押し操作と表示開始ズームは [共通の基本方針](./共通,Electronウィンドウ基本方針.md) に従う。初期ミニ表示でも最終位置・寸法を先に確定し、透明パネル内でズームする。表示中の通常・ミニ切替には登場ズームを再実行しない。

「システム起動」と「アプリ起動」のどちらにもミニ表示ボタンを置く。通常表示への復帰は元のタブへ戻り、ミニ内のサービス名を押した場合は「システム起動」の該当ログへ移る。アプリ起動側からミニにした場合もポート状態の更新を続ける。アプリはdetachedで独立起動し、Diag終了時のサービス停止対象には登録しない。終了確認には、停止する管理サービスと継続するアプリの違いを明記する。

総合テストでは、キー未登録・機器未接続・任意サービス未起動を `PASS (別途環境調整必要)` として報告する。診断画面が実際に検出したNGの記録は保持し、環境条件と製品不具合を区別する。総合評価は `✅ OK (PASS n件含む)` とし、nの内訳を併記する。

専用Electron窓は通常・ミニ表示とも左ボタンを同じ位置で0.5秒押すとドラッグ移動できる。`起動/electron-main.cjs` が窓の生成時に `frontend_ide/デスクトップ/長押し窓移動.cjs` の `attachNativeWindowMove(window,screen,'diag')` を一度取り付ける。短押しはクリック、0.5秒前の移動は通常のログ選択・ドラッグとして扱い、移動後の解放でボタンを押さない。解放・Esc・フォーカス喪失・破棄で解除し、最大化・全画面では開始しない。ミニ状態の位置・最前面指定や通常表示への復元処理は既存の `ミニ表示.cjs` が保持する。Web / headlessには適用しない。`node backend_diag/checks/initial-mini-desktop.mjs` は合成Tools状態と隔離プロファイルで初期ミニ表示・通常復元に加え、実Electron入力による両表示の長押し移動とサイズ維持・誤クリック防止・Esc解除を確認する。

- セットアップとクリーンアップでは最初の選択項目に置き、既定 `[y]/n`、全体の a=auto でも対象にします。
- 通常は `aidiy_diag` で Electron 起動、`aidiy_diag --browser` で Web 起動します。Codespaces / GUI なしでは Web です。Electron は既存 `scripts/_setup_electron.py` の共有 ZIP / 同版 dist を使ってセットアップします。Node.js 自体が無い場合はランチャーが理由と公式導入先を表示します。Python は診断アプリ起動には不要です。
- Mac / Linux の Electron 導入失敗は共通セットアップを確認します。Python の証明書検証失敗時は検証を有効にした curl へ切り替え、ZIP は unzip に依存せずリンクと補助プログラムの実行権限を保持します。修復は `python3 backend_diag/_setup.py` で行います。ランチャー専用の修復では Electron 本体を直しません。詳細は [共通の Electron セットアップ](./共通,開発環境運用手順.md#electron-の共通セットアップ) を参照してください。
- `aidiy_diag --headless` は画面を開かず全診断をコマンドラインで最速実行し、`_AIDIY/aidiy_diag/install_info.json` へ保存します。画面の「書込」「全テスト」も同じ形式で保存します。画面の「全テスト」は外部連携（Hugging Face / Discord）の読み取り専用の認証確認と `integration_info.json` への保存も行いますが、headless では外部連携を確認しません。実行に失敗した場合は既存の結果を書き換えません。
- ルート `_start.py` はToolsを実際に起動する直前（自動再起動時も含む）に必ず `aidiy_diag --headless` を1回実行し、モデル合成JSONの生成完了を待ちます。Tools未選択・クリーンアップによる起動スキップ時は実行しません。失敗時はToolsを起動せず終了し、すでに起動した管理対象プロセスを停止します。aidiy_diagのGUI起動を選ぶ質問はありません。
- ルート `_setup.py` のaidiy_diagは `[y]` の表示だけで選択入力を受けず、ランチャー配置とElectronの準備を必ず行います。終盤は「キャッシュクリア」の見出し、import由来キャッシュの削除、headless診断の順で実行します。診断失敗は既存の「エラーが発生しても続行」の選択に従います。単独の `aidiy_diag` は従来どおりGUIで使えます。
- Python、uv、Node.js、npm、npx、Electron、その他のコア周辺、機能別の任意依存の順に確認します。任意機能の未検出をシステム全体の故障と判断しないでください。
- 固定 version 引数に副作用が無いことを確認できない項目は、存在確認のみにします。Ollama の `--version` はサーバーへ接続するため実行しません。
- Ollama のモデル取得はローカル `127.0.0.1:11434/api/tags` 固定です。画面・headless とも、今回のインストール確認で「未検出」なら通信せず「未実施」とスキップ理由を保存します。未確認・検出エラーを未導入とは見なさず、従来の取得を続けます。
- Web 版でも全機能を使えます。Codespaces の転送ポートは Private にし、起動時の認証 URL を共有しないでください。確認対象はブラウザ端末ではなく診断サーバーです。
- カタログ追加ではソース参照と必要な機能を必ず記載します。設定ファイルのキー、ログイン情報、環境変数全体を返す診断は追加しません。

## システム起動管理

ミニ表示への切り替えはユーザーが行います。設定起動では自動で切り替えず、通常表示では今までどおり起動に合わせてタブとコンソールを切り替えます。ミニ表示を選んだ場合はその表示を保ちます。起動処理中、または1つでもTCPポートが開放されている間は、「起動対象」がONでポートが未開放の機能を赤く脈動させます。ポートが開けば緑の脈動へ戻ります。通常タブとミニ表示で同じ判定を使い、内部再起動中の一時的なポート閉鎖も赤で示します。起動対象外・未確認だけの場合・全停止後は赤くしません。通常表示は約800ms、ミニ表示は約5秒ごとに確認します。

右上の一括操作は、全6機能のTCPポートが未開放かつ管理プロセスも停止済みのときだけ「設定起動」を有効にする。未確認時は起動させず、稼働中・起動処理中は「強制停止」へ切り替える。認証付き `POST /api/起動/強制停止` は空JSONのみを受け付け、`サービス管理.mjs` が後続起動を取り消してタブの逆順（Web → Task / Team → Apps → Core → Tools / MCP → Local）に生存プロセス・開放ポートを再確認して停止する。停止済みはスキップし、失敗時も残りを続行して理由を表示する。管理外のサービスは固定IDだけを受け付ける `scripts/_diag_stop.py` で、通常監視への停止通知・既存Diagの実行ID更新・既存の停止処理を使用する。設定起動のAPIでも稼働中・未確認を拒否する。個別の再起動と停止は従来どおり。検証は `checks/start-manager.check.mjs`、`checks/start-bulk-state.check.mjs`、`checks/start-browser.mjs`、`scripts/checks/test_diag_stop.py`。


Webの「ブラウザで開く」の右に「手動で開く」を置く。Tools / MCPとWebの両TCPポートが開放されているときだけ有効とし、通常表示でも全6機能のポート確認を使う。チェック欄のON/OFFと独立した一時操作で、サービスや設定は変更しない。一括起動の自動ブラウザ表示にもTools / MCPが必要。手動操作の認証付き `POST /api/起動/ブラウザ` は空JSONだけを受け付け、押下時に両ポートを再確認してから `起動/Webブラウザ.mjs` が既存の `POST /aidiy_chrome_devtools/new_page` を呼び、固定の `http://localhost:8090/` とページIDを確認する。URL・コマンド・起動対象は受け付けず、連打は抑止する。検証は `checks/web-browser.check.mjs` と `checks/start-browser.mjs`。

- 専用窓の初期表示は `起動/electron-main.cjs` が一度だけ127.0.0.1:8095へTCP接続して判定する。開放時は非表示の窓をミニへ整え、主ディスプレイのworkArea左上・最前面で初表示する。未開放・確認不可は通常のシステム起動画面。TCP接続は `起動/ポート接続.cjs` を周期的なサーバー確認と共用し、500msで打ち切る。
- 初期ミニの真偽だけを固定のadditionalArgumentsからsandbox preloadへ渡し、`aidiyWindow.initialMini` として公開する。Vueは最初の描画から同じモードを使う。認証失敗時は通常表示へ戻す。画面再読込は通常表示へ戻し、初期ポート判定を繰り返さない。ミニ中は最前面とし、通常へ戻す時に元の位置・寸法・最大化・最前面設定を復元する。任意座標や最前面レベルのIPCは追加しない。
- headlessはElectron経路へ入らず、起動時の8095確認・UI・HTTP待受も実行しない。`checks/node-only-startup.check.mjs` は実headlessのポート確認とlistenを禁止して、診断・書込が従来どおり完了することを確認する。`checks/desktop.check.mjs` / `checks/start-mini.check.mjs` は開放・未開放・確認不可の分岐と位置・最前面の復元を検証する。`node backend_diag/checks/initial-mini-desktop.mjs` は合成Tools稼働・実Electronの初期描画、左上座標、最前面、通常復元を確認する。実サービスには接続せず、テスト窓はフォーカスとマウスを奪わない。
- 画面は `backend_diag/ui/src/起動/`、認証付き API は `diag_main.mjs` の `/api/起動*`、管理は `起動/サービス管理.mjs`。プロセス起動は Node の `spawn` で固定の `python -u -X utf8 <各フォルダ>/_start.py --diag-start <ID>` を実行する。HTTP でコマンド・引数・作業フォルダは指定させない。
- `scripts/起動対象.json` は順番、フォルダ、既定値の共通元。ルート `_start.py` の auto と aidiy_diag の初期値を両方確認する。aidiy_diag の対象は local / tools / core / apps / taskteam / web の6機能。`起動管理: false` の Avatar 以降はルート起動の既定値だけを残し、システム起動の表示・起動 API・専用経路から除外する（アプリ起動は別機能）。aidiy_diag 自身と on-demand の Hermes も対象に含めない。
- 設定は `_config/AiDiy_diag_start.json` に原子的に保存する。機能ごとに既知の真偽値だけを受け付ける。起動時に設定のコピーを固定し、処理中に変更した設定は次回へ適用する。ページ再読込・別タブへの移動ではプロセスを停止しない。
- `scripts/_diag_start.py` は既存の `check_environment` / `start` / `kill_ports` を共用する。Core / Apps は対応するポートだけを停止する。Tools は固定の `diag_main.mjs --headless` を先に実行する。設定不足・事前診断失敗・待受失敗時は後続の起動を中止する。
- Web の表示設定は「ブラウザで開く」の1項目（保存キー `ブラウザ表示`、既定 ON）。保存ファイルに統合前の `chrome_devtoolsで開く` があれば読込時だけ取り除き、`ブラウザ表示` の ON / OFF は維持する。設定 API は引き続き既知の真偽値だけを受け付ける。ON 時はポート開通後も HTTP 200 が20秒間継続するまで待ち、失敗応答で安定時間を数え直す（最大90秒）。安定後に Tools の既存 `POST /aidiy_chrome_devtools/new_page` を呼び、戻り値のページ ID を確認する。OFF 時は画面を開かず Web だけ起動する。Tools / Chrome の失敗は理由をコンソールに出して Web を稼働継続し、HTTP 安定待機の失敗は起動失敗とする。loopback 通信はプロキシを経由させず、安定待機中の停止ではページを開かない。外部サービスを操作しない Python 試験で応答失敗・継続安定・停止・タイムアウト・呼出順・Tools 失敗を確認する。
- 通常の `_start.py` 監視には既存の `cleanup_stop_request` を通知し、旧インスタンスの自動復活を防ぐ。aidiy_diag 同士の入替は `_AIDIY/aidiy_diag/起動/<ID>.json` の実行IDと OS ファイルロックを使い、旧監視が停止処理を終えるまで新監視は待つ。PID だけを保存して後から停止する方式にはしない。
- キーボードの Ctrl+C / ⌘C はログの選択コピーに使い、停止 API へ接続しない。起動画面は通常のテキスト選択を許可する。「停止（Ctrl+C）」ボタンは Python の制御入力に停止要求を送り、`scripts/_diag_console.py` が対象へ実際の割り込みを送る。POSIX は対象のプロセスグループへ SIGINT、Windows は aidiy_diag 経路だけ隠した専用コンソールへ分離し、短命の補助プロセスから CTRL_C_EVENT を送る。専用コンソールとして生成した印がないプロセスには送らず、他のターミナルを巻き込まない。5秒で終了しない場合や送信失敗時は従来の強制停止へ進み、各機能の子・孫プロセスも既存停止 API で回収する。起動中の停止、異常終了時の再起動待ちの停止、aidiy_diag 終了による標準入力 EOF も同じ停止要求として処理する。自動再起動 ON の明示停止は再起動させない。
- Windows で一瞬コマンド画面が出る場合は、診断本体だけでなく環境確認・ポート整理・強制停止の子プロセスも確認する。Tools の事前 headless 診断は本サービスと同じ `ConsoleSubprocess` で隠した専用コンソールへ起動し、停止時の Ctrl+C を維持する。各フォルダの `subprocess.run` は aidiy_diag 経路の間だけ `HiddenSubprocess` を介し、`CREATE_NO_WINDOW` と既定の標準入力 EOF を指定する。診断単独の Node バージョン確認・headless 実行も同様に非表示にする。Node 側の診断コマンドは `windowsHide: true` を維持する。Electron や利用者が選んだ Web ブラウザには非表示指定を適用しない。`scripts/checks/test_diag_start.py` は実プロセスのコンソール有無・非表示・出力取得と Ctrl+C を確認する。
- コンソールは機能別にメモリ上で最大120,000文字を保持し、ログ位置を指定して差分を取得する。個別再起動の受理時は対象のログをクリアし、位置の基点を以前の末尾より先へ進めて古いカーソルにも置換を通知する。UIも対象のキャッシュとカーソルを消し、取得中の古い応答を無効にする。一括起動では履歴を維持する。ANSI 制御文字を除去し、画面はテキスト補間で表示する。HTTP の起動要求を全診断・headless・画面初期表示から呼ばない。起動画面の表示だけでは Python を探索・起動しない。
- ログは `white-space: pre` で折り返さず横スクロールできるようにする。幅は画面内に収め、ページ全体を横へ広げない。新着ログ・対象切替・起動画面の再表示時は描画後にコンソールを最下部へスクロールする。手動で上へスクロールしても新着時は最下部へ戻す。実ブラウザ試験は長い合成ログで縦横の内部スクロールを発生させ、手動スクロール後の追従も確認する。
- 専用窓の終了確認は `起動/終了確認.cjs` と Electron の `close` イベントで扱う。タイトルバー・OS の閉じる・ミニ表示に共通で、renderer の表示タブやポーリング済み状態には依存させない。固定 loopback の認証付き `api/起動` を3秒以内に再取得し、`終了時停止あり` が true のときだけ停止の確認を表示する。この値は順次起動の実行中または未終了の管理子プロセスがある間 true とし、起動処理の完了後も稼働中なら true のまま。状態取得失敗時も確認し、既定と Escape はキャンセルとする。連打中は同じ確認を共有する。親サーバーの切断は既存の自動終了を継続する。検証は `close-confirm.check.cjs` と `desktop.check.mjs` で、未起動・稼働中・キャンセル・承認・二重操作・状態取得失敗・認証・外部 redirect の非追従を確認する。
- Mac のアプリ名とメニューは `起動/MacOS-Menu.cjs` から全7アプリ共通の `frontend_ide/host/scripts/MacOS-Menu.cjs` を使う。`electron-main.cjs` が ready 前に `app.setName('AiDiy 診断')`、ウィンドウと終了確認の作成後に最小メニューと Dock のアイコンを設定する。独自メニューの閉じる・⌘Q / ⌘W は `window.close()` を呼び、確認を飛ばす `app.exit()` は呼ばない。編集メニューを表示せず、非表示の native role と `acceleratorWorksWhenHidden` でコピー・貼付・選択・元に戻す等を維持する。`before-input-event` でキー入力を横取りしない。Windows / Linux へは適用しない。`desktop.check.mjs` で終了キャンセル・承認と編集メニュー構成を確認する。`app.setName` は OS 側の Dock 名を変更しない。Dock 名の変更にはアプリバンドルの名称・Info.plist 等の配布設定が必要で、[Electron 公式のパッケージ化手順](https://www.electronjs.org/docs/latest/tutorial/application-distribution)を参照する。
- 順次起動の表示追従は `api/起動` の `起動表示: {対象, 実行ID}` を使う。サーバーは各機能の再起動開始前に実行IDを更新し、完了・失敗後も最後の対象を保持する。UI は未反映の実行IDだけでタブを選択し、同じ対象の再起動にも対応する。通知文の解析や状態配列の先頭検索で対象を推測しない。定期取得のたびに選択を上書きせず、手動で別タブを見た場合は次の開始まで維持する。ミニ表示を解除せず、表示追従から起動・停止 API を呼ばない。単体確認は `start-follow.check.mjs`、実画面は `start-browser.mjs` で6機能の準備完了を順に保留・解放し、途中の自動表示と手動選択の保持を確認する。
- 起動画面のミニ表示は `ui/src/起動/起動ミニパネル.vue`、切替状態は `ui/src/ウィンドウ/起動ミニ表示.mjs`、専用窓の寸法管理は `起動/ミニ表示.cjs` が担当する。上部に6アプリの起動アイコンと下部に6機能の状態を約240×130に表示し、通常表示で元の位置・寸法・最大化状態を戻す。ミニ中はログの取得を止め、管理状態とポート開放状態を約5秒ごとに取得する。画面切替は起動・停止 API を呼ばない。起動以外へのタブ切替や画面再読込では通常の窓寸法を復元する。IPC は主フレームからの真偽値だけを受け付け、任意の寸法は公開しない。検証は `start-mini.check.mjs` と既存 `desktop.check.mjs`、実ブラウザの `start-browser.mjs` で行う。
- ミニのサーバー表示は管理プロセスの状態に依存させず、認証付き `GET /api/起動/ポート` と `起動/ポート状態.mjs` を使う。`scripts/起動対象.json` の管理対象6機能のポートだけを127.0.0.1へ並列TCP接続し、1接続500msで打ち切る。任意のホスト・ポート・入力は受け付けず、HTTP本文や認証情報を送らない。開放は緑、未開放・確認不可は灰色。tooltipにポート番号と状態を出す。確認不可を過去の開放結果で補わない。
- `ui/src/起動/起動状態.mjs` は通常表示の更新を800ms、ミニ表示は5秒に分ける。ミニ退出・切断でタイマーと取得中のリクエストを破棄する。管理状態は終了確認・コンソール・停止の所有権に引き続き使い、外部 `_start.py` のサーバーを検出しても所有・停止対象へ加えない。アプリ起動のAvatar / Live / Discordの二重起動確認は押下時だけのまま。
- ポートの検証は `checks/port-status.check.mjs` の無害なTCP待受で開放・終了・再開、無送信、タイムアウト・キャンセル・固定対象・認証を確認する。`checks/start-mini.check.mjs` は5秒の更新間隔・退出時の停止・未管理サーバーの検出を確認する。`checks/start-browser.mjs` は管理状態とポート状態を独立して変化させ、5秒ごとの色の更新とログ取得停止を実画面で確認する。
- 検証は `node --test backend_diag/checks/start-manager.check.mjs`、`python -B -X utf8 scripts/checks/test_diag_start.py`、`node backend_diag/checks/start-browser.mjs`。実サービスを起動せず、合成プロセス・模擬フォルダと既存 Chrome / Edge で順番、保存・再読込、二重実行、Ctrl+C でのコピーと停止 API の非呼出、停止ボタン、横幅1280 / 390、パス型 proxy を確認する。Python の合成サブプロセス試験は監視プロセスの入替、Ctrl+C による子の終了処理、共有コンソールへの誤送信防止、停止タイムアウト時の強制停止も確認する。
- UI 変更後は今回の画面反映を目的として `backend_diag/ui` の `npm run build`、続けて `node backend_diag/ui/verify.mjs` で配布物を同期する。

## 保存済み結果の初期表示

導入状況・モデル一覧・外部連携は `診断/前回結果.mjs` から既存の保存ファイルを読み、実行ボタン左側に前回実行日時を表示します。通常の確認・再取得では画面上だけ更新し、自動保存はしません。保存は headless と確認後の書込ボタン（全テスト内の書込を含む）です。保存前に再起動すれば最後に保存した内容へ戻ります。

タブ移動では今回の結果・実行日時・書込済み表示を保持します。モデル一覧と外部連携の再確認はそれぞれ `api/キー設定/モデル一覧` / `api/キー設定/外部連携` を使い、対象側だけ結果と書込済みを解除します。サーバーの書込対象も同じ範囲で破棄し、別タブの未保存結果を失わないようにします。

欠損・破損JSONは未確認として扱い、表示用の結果を今回の認証証跡や書込対象へ戻しません。回帰確認は `node --test backend_diag/checks/previous-results.check.mjs`、実ブラウザの位置・表示・再起動確認は `node backend_diag/checks/previous-results-browser.mjs`（既存Chrome/Edgeを使用、外部APIを呼ばない合成データ）です。

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
- 書込時に現在のキー（OpenAIは組織も）またはOAuthトークン・アカウントが取得時と一致することを確認する。キー変更・削除、一覧取得失敗、旧JSONだけが残っている状態は候補にしない。個別確認後は同じaidiy_diag実行内で保持する他方式の有効な取得結果を使うが、再起動や設定再読込後は再確認が必要。
- FreeAI/Geminiは判断実行と同じ優先キーを使い、優先キー未設定時だけ他方の認証付き取得結果を代用する。キーが設定済みで認証に失敗した場合は代用しない。
- 空の方式は省略し、全方式が空なら `{}` を保存する。設定・autoの選択順・方式別既定値は書き換えない。生成確認済みの利用可能モデルとこの候補一覧を混同しない。
- headlessと画面のモデル書込は共通処理で生成し、保存先一覧にもファイル名を含める。Pythonの読込口は `conf_models.get_decisions_models()`。Web/Avatar設定画面もこの一覧を利用し、取得済み候補と設定保持値を区別して表示する。
- モック検証: `node --test backend_diag/checks/decisions-info.check.mjs`。4方式、認証変更、公開/固定/旧保存候補の排除、キー代用、失敗・空一覧、共通書込とheadlessの保存先を確認する。

### 判断系4方式の候補管理（2026-10-18）

autoの優先順は `openai_oauth` → `freeai_chat` → `openai_decisions` → `gemini_chat`。起動チェックに成功した方式だけを優先対象にする。

判断系の低コスト方針は `backend_diag/モデル情報/decisions_info.mjs` の `DECISION_MODEL_CANDIDATES` で書き出す候補を絞って管理する。現在はOpenAI両方式が `gpt-6-luna`、FreeAI/Geminiが `gemini-flash-lite-latest`。将来別モデルへ変更するときはこの候補配列を調整し、認証付き一覧を再取得・書き出しする。実行側や画面にモデル固定・恒久的な選択禁止は置かない。

[Google公式alias説明](https://developers.googleblog.com/en/continuing-to-bring-you-our-latest-models-with-an-improved-gemini-2-5-flash-and-flash-lite-release/) でIDを確認した。最新への追従はGoogle側のalias更新を利用し、番号を推測・並べ替えしてモデルを生成しない。[公式モデル一覧](https://ai.google.dev/gemini-api/docs/models) では現時点の安定版Flash-Liteは `gemini-3.5-flash-lite`。latestは安定版専用aliasではなくプレビュー等を指す場合もあるため、現在の解決先バージョンはこの実装で断定しない。

aidiy_diagは認証付きGET一覧に候補配列のIDそのものがある方式だけを掲載する。GoogleはgenerateContent対応を要求する。公開一覧・設定値・別バージョンから候補を捏造しない。未取得・認証なし・失敗・対象ID不在なら方式を省略し、全方式が空なら `{}`。モデル一覧は実行の許可リストではなく、設定画面の候補として扱う。

## OpenCode / Copilot のCode候補

`code_models_info.json` の `opencode_cli.models` はCodex用に合成した候補を共通元とし、OpenCode側のIDと表示名のモデル部分に `openai/` を付ける（例: `openai/gpt-6.1-sol`）。日付・順序は保持し、既存の接頭辞は二重に付けない。Codex候補が0件ならCopilotと同じ `COPILOT_FALLBACK_MODELS` の規定8モデルに同じ `openai/` を付けて補完する。Copilot側の取得候補・規定値は変更しない。OpenCodeの出力条件は自身の導入検出だけで、Codex / Copilotの導入には依存しない。補完はモデル候補の書き出しだけで、認証・実行成功を意味しない。検証は `checks/models-info.check.mjs` で行う。

## 判断モデルの手動試行

設定モデル動作確認のLIVE直後に `DECISION / 挨拶の丁寧さ` を表示する。個別「テスト」と全体「動作確認」の両方で、既存MCP `/aidiy_decisions_check/mcp` の `decisions_check` を呼ぶ。HTTP `/check` への代替直結は行わない。Tools接続中の明示操作に限定し、headless・起動・全診断では実行しない。

`DECISION_AI_NAME` と方式別 `DECISION_OPENAI_MODEL` / `DECISION_OAUTH_MODEL` / `DECISION_GEMINI_MODEL` / `DECISION_FREEAI_MODEL` が不足時はauto。方式が明示されている試行行は対応する方式別値を使い、キー未存在時だけ旧 `DECISION_AI_MODEL` を参照する。方式autoの行はモデルもautoで送り、Toolsで方式とモデルを解決する。autoの方式順はOAuth → FreeAI → Decisions API → Gemini。結果には実効モデルを表示し、設定ファイルへは書き戻さない。

入力は「おはよう」、質問は挨拶としての丁寧さ、choice名は `politeness`、選択肢は `high / medium / low`。3値すべてを正常な選択として受け付け、特定値を正解とはしない。MCPのJSON内のstatus、回答名・型・選択値、3候補の確率分布・合計、confidenceを検証する。不正JSON・欠落・未知選択肢・通信エラーはNG。結果詳細に選択値と検証済みJSON、実際の実行モデルを表示する。

Chat/Live/Codeと判断結果は共有しない。MCPの初期化・セッション破棄、設定変更による結果破棄、既存のタイムアウトを共用する。判断の行期限を超えた場合はNGと理由を表示し、その全体実行を終了する。ユーザーによる中止は従来の中止表示を維持する。

検証は `checks/decision-trials.check.mjs`、既存モデル試行/API/音声/UIテスト、`DIAG_TEST_PYTHON` を指定する実MCP SDK fixtureで行う。fixtureの生成APIはMockTransportへ置換し、外部の生成サービスを使わない。Web/Avatarの設定画面とaidiy_diag試行UIは同じ候補と通常のモデル解決を使う。


## AIモデルの手動試行

Gemini系Live（`freeai_live` 経由を含む）は接続直後の初回送信で失敗する場合があります。診断では接続確立後に15秒待って初回送信し、送信後の応答・音声ターン完了を最大60秒待つ設定です。この条件で実回答を確認したLive試験は通過とし、初回失敗は注意事項・経過の証跡として残します。

「AIモデル」はChat / Live / Decision / Codeの4画面です。初期値はconfigのCHAT・LIVE・DECISION各設定とCODE1を使います。Decisionの方式autoはモデルもautoとしてTools側で解決します。入力の「おはよう」とDecisionのpoliteness / high・medium・lowは `モデル試行/defaults.mjs` を既存設定モデル試行と共用し、手動画面では自由に編集できます。

候補は `_AIDIY/aidiy_diag/{chat,live,decisions,code}_models_info.json` と `live_voices_info.json` の保存済み内容を使います。Codeのモデル候補には、Web / Avatarの「AI設定・再起動」と同じ実行方法 `auto (自動判定)`、`same (変更なし)` をこの順で先頭に補い、重複を除きます。これらはモデル一覧JSONへ書き戻しません。画面初期読込・再読込は認証付きローカルaidiy_diag APIを使い、外部モデル取得は行いません。プロバイダ変更は画面内で候補を連動し、一覧外の設定保持値を未確認として残します。 Code初回表示はCODE1の設定を使い、プロバイダ切替時は `CODE_<プロバイダ大文字>_MODEL`（例: `CODE_GROK_CLI_MODEL`）を優先します。そのキーがない場合だけCODE1〜6の同プロバイダ設定、次に候補の先頭へ戻します。画面内で手動選択した値は再読込まで優先して保持します。候補の存在は認証・モデル利用成功の保証ではありません。選択や入力をconfigへ書き戻しません。

試行はTools接続中の明示操作だけです。既存 `モデル試行/trials.mjs` のMCP初期化・呼出し・セッション終了、逐次実行ロック、設定変更検知、期限、音声保存を共用します。Chatは `chat_llms_run`、Codeは `code_agents_run`、Decisionは `decisions_check` をHTTP MCPで呼び、Liveだけは既存 `/internal/live_model_check` へ明示した方式・モデル・音声・入力を渡します。設定モデル・AIモデルのLiveは、試行ごとに新規セッションを作り、接続確立後の初回送信前に15秒自動待機してから送信します。同じセッションの毎送信に課す待機ではなく、利用者の追加待機も不要です。長い返答の生成・音声ターン完了に余裕を持たせ、送信後の応答待ちは最大60秒です。接続準備20秒・初回待機15秒・終了処理9秒と通信余裕を含め、内部HTTPは135秒、1試行は150秒、全実行は45分を上限とします。アダプター終了処理も共通です。空JSONの従来Live試行は従来のconfigと固定挨拶を使います。

AIモデルタブのタイトルバー「一括試行」は4画面の入力を開始時に固定し、Chat→Live→Decision→Codeを1実行として順に呼びます。NG・行タイムアウトでも次へ進みます。連打は抑止し、入力変更・実行中の画面移動・Tools切断で中止して古い結果を破棄します。全診断・headless・起動ではAI試行しません。設定モデルの15項目試行とAIモデルの4種試行は別の操作です。

Decisionは1問ずつpredicate / choice / scoreを選び、質問名・質問文と、必要な選択肢／段階（2〜32件、重複不可）を編集します。戻り値全体はJSONを読めればインデント付き、読めなければ元文字列を安全なテキストとして表示します。表示できることと回答スキーマの成功判定は別です。既知の秘密値は伏せます。

Liveの応答テキストと1秒以上のWAVを表示し、受信時に認証付き音声APIからBlobを自動取得してネイティブプレーヤーで再生できる状態にします。自動再生しません。AIモデル・設定モデルとも、完了後のタブ移動では再生だけを停止し、結果と取得済み音声を保持します。再実行・設定再読込・切断・終了ではObject URLを解放します。通常は音声再読込の操作を求めず、取得・再生失敗時だけ「音声取得を再試行」を表示します。短い音声・音声なしは明示します。

検証は実AIを使わず、`checks/manual-models.check.mjs`、`ui/src/AIモデル/checks/manual-state.check.mjs`、`backend_tools/tests/test_live_model_check.py` を使います。`DIAG_TEST_PYTHON` をTools依存環境のPythonへ設定すると `checks/model-trials-sdk.check.mjs` が実MCP SDKと合成AIで経路を確認します。`checks/manual-models-browser.mjs` は既存Chrome/Edgeの隔離プロファイルで4画面・幅1280/720/390・合成音声再生・破棄・一括試行・非JSON表示を確認します。UI変更後は依頼に応じて `backend_diag/ui` のビルドと `node backend_diag/ui/verify.mjs` で配布物を同期します。

## アプリ起動

- ミニ表示は `ui/src/アプリ起動/ミニアプリ起動.vue` を使い、Appの同じアプリ状態（選択フォルダ・処理中・結果）を共有する。aidiy_diag起動・再読込時は毎回フォルダ未選択で始める。稼働数の集計行を置かず、「↗」の復帰操作はタイトルバーから同じミニ解除イベントを呼ぶ。ミニの6起動ボタンはアイコンのみ、名称はtitleとaria-labelへ残す。サービス状態は3列2行の短い名称と色で表示し、詳細はtitleで確認する。稼働中はミニの項目全体（`起動ミニ.css` の `mini-blink`）と通常画面のタブ下線（`起動.css` の `start-bar-blink`）を緑で非線形に明滅させる。表示灯の丸印は置かない。周期（約4.5秒、項目ごとに4.32〜4.68秒）と開始位置は `ui/src/起動/明滅.mjs` が項目ごとにずらし、表示のたびに乱数の揺らぎを加える。明るさはタイトルバーのシアン帯と同じ |sin(πt)| を2.5%刻みで直線補間する。ミニはポート確認が未確認のとき直前の表示を保つ。プロジェクト未選択時は赤字の英語案内「SELECT YOUR PROJECT ▸▸ READY FOR LAUNCH」を電光掲示板風に右端から左端へ流し（`mini-marquee`、黒い格子線を `::after` で重ねたドット文字、titleは「プロジェクト選択してね」）、無効な6起動ボタンを表示する。通常画面のプロジェクト欄も未選択時は赤い枠で選択を促す（`アプリ起動.css` の `app-project-alert`）。アプリ一覧の読込だけを表示時に行い、タスク確認・起動は押下時だけ。ミニと通常で起動経路を複製しない。
- アイコンは Avatar の `frontend_avatar/public/icons/`、IDE / Term / Code / Live の `frontend_ide/public/`、Discord の `frontend_channels/panel/` から `ui/src/アプリ起動/アイコン/` へコピーしたPNG。ビルドでstaticへ同梱し、認証情報を含まない固定6ファイルだけをHTTP公開する。ソースと配布PNGをmanifestで照合し、起動時に他アプリのフォルダを配信しない。アイコン更新後はUIビルドと一致確認を行う。`app-launch-browser.mjs` が6画像の読込、ミニ240×130の収まり、赤字・不活性、選択フォルダの共有、ミニからの起動・排他を確認する。
- 画面は `ui/src/アプリ起動/`、固定起動対象・タスク確認・プロセス生成は `起動/アプリ起動.mjs`、認証付き API は `/api/アプリ起動` と `/api/アプリ起動/{開始,フォルダ}`。システム起動の管理・停止・終了確認に参加させない。
- 起動には存在する絶対パスのフォルダが必要。Avatar にも選択を必須とするが、Avatar 自体の作業パスは AiDiy 本体にする。他の5種類は選択したパスを `cwd` と `--project` の単一引数に渡す。シェル文字列や任意コマンド・引数は受け付けない。共有設定の `CODE_BASE_PATH` を書き換えない。
- Electron の `selectProject` は主ウィンドウの主フレームだけが呼べる固定フォルダダイアログ。Web はサーバー側フォルダだけを列挙する。選択は画面内だけで保持し、再読込時は未選択とする。
- Avatar / Live / Discord だけ、押下後に PowerShell CIM（Windows）または ps（macOS / Linux）でタスクを1回取得し、既知の実行入口と照合する。タスク内容は画面へ返さない。確認失敗時は起動しない。起動直前の同時クリックを排除し、各アプリ既存の排他も残す。起動後のタイマー・状態監視・PID保存による後日停止を追加しない。
- 起動は `detached: true` / 標準入力 EOF / ログファイル出力 / `unref()`。aidiy_diag と IPC で所有関係を結ばない。ログは `_AIDIY/aidiy_diag/アプリ起動/` に起動ごとに分ける。画面の通知は「起動要求」とし、表示成功として扱わない。
- IDE / Code は既存 `frontend_ide/launch.mjs --new-window` から一時プロファイルで別窓を開く。通常起動の既存窓再利用や Live の排他は変えない。Term は従来から複数起動を許可する。一時プロファイルはアプリ終了時に回収する。
- 検証は `checks/app-launch.check.mjs`（実フォルダ・パス・タスク判定・認証・入力制限・aidiy_diag終了後の無害な子プロセス継続）、`checks/desktop.check.mjs`（フォルダ選択の限定IPC）、`frontend_ide/checks/project-instance.test.mjs`（通常起動と複数窓）。`checks/app-launch-browser.mjs` は合成プロセスで390/1280pxの実画面、フォルダ必須、押下時だけの確認、起動先、定時監視がないことを確認する。


## 総合テストの補足確認

`checks/initial-mini-probe.cjs` は、本体が `appData/aidiy_diag` をuserDataに使う前に、検証用の `appData` 自体も隔離します。userDataだけを先に指定すると本体に上書きされ、実行中のDiagの単一起動ロックへ接続してしまいます。`checks/initial-mini-desktop.mjs` で実画面の位置・最前面・通常復帰、長押し成立時間、750msズームのアニメーション時間と透明領域の寸法維持を確認できます。

`checks/start-browser.mjs` は合成サービスを使い、ミニ表示の約5秒周期・ログの最下部追従・コピーで停止しないこと・停止ボタン・小画面を検証します。実際のログコピーはComputer Useで文字を選択してCtrl+Cを送り、OSのクリップボードを選択行と照合します。通常停止が5秒以内に完了しない場合は既定のプロセス回収へ進むため、停止信号の送信・ポート閉鎖・他機能の継続・明示停止後の自動再起動抑止を分けて記録します。

設定モデルの結果説明は、正常応答で説明文が空でも「応答を確認しました。」と表示します。バッジがOKなのに詳細を未実施と表示しないことを `checks/model-trials-browser.mjs` で確認します。

AIチャット・AIコードの最終応答が空文字・空白だけ、または前後の空白を除いて`!`で始まる場合はNGです。`!`単独は無応答、`! エラーメッセージ`は理由付きエラーです。MCP側の`status`が誤ってOKでも、本文がこの形式なら成功扱いにしません。旧版の「応答なし」や既知のエラー文の判定も互換性のため残します。共通規約は[AIコアWebSocket仕様](./backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md#aiチャットaiコードのエラー応答)を参照します。

完了した冊子のPDFは `node scripts/checks/総合テストPDF.mjs <md名>` で作成できます。元のMarkdownと同じフォルダへ同名で保存し、本文の修正後は再生成します。本文の折りたたみ欄も開いて出力し、説明と画像を同じ図として配置します。生成後はPoppler等で全ページを画像化し、日本語・表・画像・改ページを確認してください。
