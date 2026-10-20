# Electronウィンドウ基本方針

> 文書: `共通,Electronウィンドウ基本方針.md` | 実装: `frontend_ide/デスクトップ/長押し窓移動.cjs`, `frontend_ide/デスクトップ/code-drag.cjs`, `frontend_ide/host/scripts/window-opening.cjs`, `frontend_ide/desktop.cjs`, `frontend_ide/デスクトップ/panel-windows.cjs`, `frontend_avatar/electron/main.ts`, `backend_diag/起動/electron-main.cjs`, `frontend_channels/panel/desktop.cjs`

## このメモを使う場面

- AiDiy の Electron アプリ・関連パネルを追加、変更する。
- 長押しによる窓移動や、表示開始時のズームに適用漏れがないか確認する。
- Windows の白い縁・ちらつき・DPIによるサイズ変化を防ぐ。

## 共通の基本動作

AiDiy が所有する Electron の操作画面は、**通常画面の背景を同じ位置で左ボタンで0.5秒長押しした後のドラッグ移動**と、**表示開始時のズーム**を基本とする。選択欄・入力欄などの操作と、ポップアップ中のモデル選択を窓移動より優先する。新規のアプリ・別窓にも最初から組み込む。光沢・影が走る追加の登場演出は入れない。

対象は aidiy_diag、Avatar、Term、Code、Live、IDE、Discord と、その機能別ウィンドウ。IDE の Explorer、Viewer、ソース比較、軌跡バー、Browser 本文、Avatar の設定・タスク・チームも含む。Webブラウザ版・VS Code拡張の埋め込み画面にはOS窓移動を導入しない。演出用の短命な透明キャンバスは操作画面ではないため、長押しを取り付けない。

## タイトル操作と最前面ピン

- 操作の並びは **ー □ 📌 Ｘ**。既存のタイトル位置・高さ・窓寸法は維持する。Diagのミニ表示では最大化を理由付きで無効化する。軌跡バーは通常タイトルバーを持たない例外で、最小化・最大化を追加せず、元のバーガー・ドラッグハンドル・分類ラベルを保持する。
- 最前面の管理は `frontend_ide/デスクトップ/最前面ピン.cjs` の `createWindowPins` を全アプリで共用する。通常起動はOFF、沈んだ表示。再起動を越えてON状態を保存しない。Diagのミニ表示への切替・復帰も、その時点のユーザー選択を維持する。
- IDEから開くTerm / Code / Live / Viewer / Browser / Explorer / 比較 / 軌跡だけはONで生成する。現在これらはIDEと同じElectronプロセスで、main側の `record.owner` が起動元の根拠となる。CLIの `--linked`、URL、rendererからの任意フラグを根拠にしない。
- Diagからのアプリ起動、単独Avatar（設定・タスク・チームを含む）、単独DiscordはIDE由来ではないためOFF。現行IDEにこれらの別プロセス起動経路はない。今後IDEから外部Electronを起動する場合は、mainが管理する起動元とVR状態の通知・切断処理を加え、単に別プロセスだからOFFと判断しない。
- ONは全OS・全アプリで同じ `floating` 層。選択されたON窓だけ `focus` 時に `moveTop` する。`focus()` の奪い返し、タイマー再固定、IDE選択時の子窓一括持上げ、`pop-up-menu` 等の上位層は使わない。これにより別プロセスのON窓同士も通常のOS選択順に従う。OFF窓の選択では持上げ処理をしない。
- IDEのVR中は、本体と所属する既存・新規子窓をONにロックする。UIは `aria-pressed` と理由付きdisabledで表示し、mainでもOFF要求を拒否する。F11・VR再押下・最大化によるVR終了後は、各窓のVR直前のユーザー選択へ戻す。VR中にIDEから新規生成した窓はONへ戻り、その後OFFにできる。
- IDEの子窓の寿命・セッションは `record.owner` で管理する。OSの `parent` / `setParentWindow(owner)` は、OFFでも親より常に手前になるため設定しない。元のDOMを移す別窓は `setParentWindow(null)` で外し、終了時の回収は従来の所有記録で行う。
- ページ内のExplorer・軌跡・Viewer・比較は従来の **📌** で別ウィンドウを開く。Explorer・軌跡の切離し📌は右端に置く。Explorer別窓のタイトル操作と本文の↙本体復帰は既存位置のまま維持する。軌跡別窓だけは右端の切離し操作を重複させず、最前面📌と↙本体復帰を元のドラッグハンドル付近にまとめる。Web popupの復帰、別窓API・セッション・元DOMの保持は変えない。
- rendererは自分の状態取得・切替・状態変更購読だけをpreload経由で使用する。DOM別窓は親IDEの限定 `panelAction` と、所属する `panelName` の通知を使う。他窓IDや任意IPCを公開せず、mainで所有者・フレーム・セッション世代を照合する。

再検証:

- `node --test frontend_ide/checks/window-pin.test.mjs frontend_ide/checks/window-pin-renderer.test.mjs frontend_ide/checks/code-window-title.test.mjs frontend_ide/checks/panel-windows.test.mjs frontend_ide/checks/all-displays.test.mjs`。OFF/ON初期値、選択順、VR入出、F11、連打・古い通知・閉鎖時の回収、他窓操作拒否を確認する。
- `frontend_avatar/node_modules/.bin/electron frontend_ide/checks/window-pin-desktop.cjs --ozone-platform=headless` は隔離した合成画面だけを使う。Linux headlessでは `setAlwaysOnTop` を受け付けても `isAlwaysOnTop()` がfalseのままの環境がある。コントローラーの状態・API呼出検査と、OS最前面の実測を区別する。
- Windows実機では、別アプリを含むON窓A/Bの交互選択、OFFへ変更したIDE子窓とIDE本体の前後入替、他アプリ選択、VR中の解除拒否、VR終了後の復元を実窓で確認する。headless・モックの成功を実デスクトップのZ順検証として扱わない。

## 0.5秒長押しドラッグ

- `frontend_ide/デスクトップ/長押し窓移動.cjs` と `code-drag.cjs` を共用する。500msの静止判定をアプリごとに複製しない。
- 通常の押下・解放は元のnativeイベントを直ちに通し、保留して再送しない。`select` / `option` / `datalist` / 入力欄・ラベル・ボタン・リンク・編集領域・iframe・ARIA操作部品は窓移動の対象外とする。Shadow DOMの内側と祖先も確認する。通常画面の背景だけを長押し候補にし、判定前に位置が動いたら文字選択・通常ドラッグを優先する。
- モデル選択などの`dialog[open]`、可視のモーダル・一覧・展開中コンボボックスでは、背景も含めて長押し窓移動を開始しない。nativeのselect/datalistにフォーカスがある間も選択操作を優先する。ただし、閉じた選択欄にフォーカスが残った場合でも、明示した `data-aidiy-window-move-handle` の非操作部分だけは次の長押しを受け付ける。開いた選択ポップアップ・モーダルやハンドル内のボタン・入力欄は例外にしない。ポップアップ中に窓をドラッグできなくても、モデル選択を妨げないことを優先する。
- 軌跡のバー・ハンドルは `-webkit-app-region:no-drag` とし、OSの即時dragではなく共通の500ms判定を通す。Explorer別窓のファイル一覧は `data-aidiy-window-move-list` を付けたtree要素のtabindexだけを例外にし、通常行・余白の静止した500ms長押しを受け付ける。展開ボタン・rename入力・メニュー・選択前のドラッグは保護する。Explorerのタイトル操作や他画面の入力判定は変更しない。
- DOMの対象と押下中のgestureは隔離worldで確認し、新しいpreload・IPC権限を追加しない。受動的な入力監視を使い、非同期の確認で元の入力の通過を待たせない。500ms後に同じgesture IDがまだ押下中の場合だけ移動を許可する。確認失敗時は移動を開始せず、解放・移動・フォーカス喪失・遷移・破棄・次の押下後に届いた結果を無視する。
- 背景の移動成立時だけ、元の対象へ`pointercancel`を送り、pointer captureとCanvasなどの操作状態を後始末する。実際の`pointerup` / `mouseup`は成立後もそのまま通し、同じgestureから生じる`click`だけを抑止する。次の押下・キー操作のクリックを抑止しない。選択欄やポップアップにはこの取消も送らない。
- 成立後は移動カーソルと静止した四方向マーカーを表示し、解放をクリックとして渡さない。解放・Esc・フォーカス喪失・遷移・破棄で解除する。最大化・全画面では窓移動を開始しない。IDEのVR時は既存の中心点移動へ分岐する。
- 他アプリは、mainが生成して所有する窓に `attachNativeWindowMove(window, screen, kind)` を一度だけ取り付ける。現在の外部アプリ種別は `diag` / `avatar` / `discord`。新種別を足す場合は両共通ファイルの許可リストを揃える。
- rendererから任意の窓ID・座標を受け取るIPCを追加しない。Electronのカーソルと窓位置を同じDIP座標で扱い、既存の端数DPI補正・サイズ維持・購読解除を使う。

## 透明パネルで領域を先に確保するズーム

**最終位置・最終サイズの透明パネルを先に確保し、その内側だけをCSSでズームする。** 実ウィンドウの外枠をアニメーションの各フレームで拡大しない。

1. 実画面は `show: false` で生成し、内容の読込・最小サイズ・最終配置を先に整える。
2. `frontend_ide/host/scripts/window-opening.cjs` の `拡大表示` を使う。実画面の `getContentBounds()` と同じ領域へ、透明なキャンバス窓を作る。`transparent: true`、背景 `#00000000`、枠・影なし、タスクバー非表示を維持する。キャンバスの外枠は確定した領域のまま動かさない。
3. 非表示の実画面を `capturePage`（`stayHidden` / `stayAwake`）で取り込む。登場待ちで隠している不透明度だけを一時解除し、取得後に必ず戻す。HTML / body と画像の外側は透明とし、実画面の画像だけを中央から55%→100%へ750msで拡大する。白や背景色だけの代用面は出さない。倍率と時間の同期元は同ファイルの `開始倍率` / `演出時間`。実画面の位置・サイズを連続変更しない。
4. 実画面を透明度0で表示し、描画を待って透明度1へ戻す。実画面が見えてからキャンバスを破棄する。Windowsの白い縁や未描画フレームを露出させない。
5. キャンバスは `showInactive()` を使う。VR中のIDEなどに演出が隠れないよう、短命な画像だけは実窓の `isAlwaysOnTop()` と同じ層で作る。OFF窓の演出を最前面にしない。Windowsで透明部分が白くなる組合せを避けるため、本番の演出用キャンバスへ `focusable: false` や `setIgnoreMouseEvents` を追加しない。

非表示窓の初回取得はWindowsの描画待ちで失敗する場合があるため、再描画して最大3回取得する。拡大の終了は描画側のanimation.finishedで待つ。

実画面を取得できない場合は、色だけの代用面を出さずに通常表示へ進む。試験用HTMLにも `html` / `body` の透明背景・余白0・全高を指定し、ブラウザ既定の白地を混ぜない。

表示中の窓を手前へ戻す操作、再読込、aidiy_diagの通常・ミニ切替ではズームを重ねない。非表示から機能パネルを開く場合は表示開始として扱う。表示要求の連打はまとめ、ズーム待ちの非表示・破棄を優先する。共通 `拡大表示` の `canShow` は表示直前にも確認し、取り消された窓を遅れて再表示しない。

現時点では「動きを減らす」への専用対応は行わず、OSの設定によって規定のズーム・ページ繰り・更新表示などを省略しない。アプリ側のCSSメディアクエリーや表示入口の分岐を追加しない。第三者ライブラリ内部の実装とは区別し、共通処理から各アプリ・関連パネルまで順に確認する。

## 適用箇所

| 対象 | 長押しの取り付け | 表示開始 |
|------|------------------|----------|
| aidiy_diag 通常・ミニ | `backend_diag/起動/electron-main.cjs` | 内容読込と初期ミニ寸法の確定後に共通 `拡大表示` |
| Avatar 全17種類 | `createBaseWindow`、`openSettingsWindow`、`openTeamWindow` | `electron/main.ts` の `ウィンドウ表示` に集約。読込待ち、連打抑制、非表示要求を共用 |
| Term / Code / Live / IDE / 独立Viewer / Browser | `frontend_ide/desktop.cjs` の `attachWindowMove`。BrowserのWebContentsView本文にも取り付ける | `createWindow` で内容・配置確定後に共通 `拡大表示` |
| Explorer / 比較・Viewer / 軌跡の別窓 | `frontend_ide/デスクトップ/panel-windows.cjs` の `created` | `show` から共通 `拡大表示`。元DOM・状態・表示の保持を崩さない |
| Discord | `frontend_channels/panel/desktop.cjs` | 内容・配置確定後に共通 `拡大表示`。Botの実接続は演出と独立 |

## 再確認

リポジトリルートで実行する。画面検証は隔離プロファイル・合成データを使い、ユーザーのアプリやサーバーを停止しない。

- `node --test frontend_ide/checks/native-window-move.test.mjs frontend_ide/checks/code-drag.test.mjs frontend_ide/checks/panel-windows.test.mjs`：500ms、通常入力を遮断・再送しないこと、操作部品・ポップアップ除外、遅いDOM確認の取消、解除、DPI、所有元・表示境界。
- `node frontend_ide/scripts/check-panel-controls.mjs`：実Vue部品を隔離データで描画し、ページ内の📌、Explorerの既存タイトルと復帰、軌跡の一行表示、繰返し切離し、入力保持、VRロックを確認する。外部通信は行わず、結果と描画画像を一時フォルダへ保存する。
- `frontend_ide/host/node_modules/.bin/electron frontend_ide/checks/panel-hold-drag-desktop.cjs --ozone-platform=headless`：合成パネルへのtrusted入力で、一覧の行・余白、軌跡ハンドルの500ms長押しと、通常選択・rename・部品・ポップアップの保護を確認する。headlessの結果をWindows実機の位置・重なり確認とは扱わない。
- `node --test frontend_avatar/checks/window-opening.test.cjs frontend_channels/checks/desktop.test.ts backend_diag/checks/desktop.check.mjs`：全17種類の表示経路、連打・取消、Discordへの取り付け、aidiy_diagの初期表示・終了処理。
- 隔離した実Electron入力: `frontend_avatar/node_modules/.bin/electron frontend_ide/checks/native-input-desktop.cjs`。sandboxを維持した合成画面で、元のtrusted down/up、背景のpointercancelとclick抑止、取消・次の通常クリック、native selectのキー選択、2行listboxのマウス選択、dialog内の背景移動禁止を確認する。Linuxの画面なし環境では`--ozone-platform=headless`を指定できるが、OS固有dropdown popupの実機確認は別途必要。結果はOSの一時フォルダへ出力し、画面を取得できた場合だけPNGも残す。
- Avatarのmain変更後は `frontend_avatar` の `npm run build:electron` で `dist-electron` を同期する。`node frontend_avatar/checks/window-move-desktop.mjs` は全17種類の実生成関数と共通ズーム・長押しを検査する。本文だけを無害な合成画面へ置き換える。
- `node backend_diag/checks/initial-mini-desktop.mjs`：実Vueの通常・ミニ表示、長押し、位置・サイズ・最前面・復元。
- `node frontend_channels/checks/window-behavior-desktop.mjs`：Discordの本番Vue・preload・ズーム・背景の長押し・選択欄と入力欄のnative操作。Bot workerだけを合成し、接続・保存・外部送信をしない。
- `node frontend_ide/scripts/check-module-move.mjs`：Code / Live / Termの単独・IDE連携、独立Viewer。`node frontend_ide/scripts/check-panel-desktop.mjs`：Explorer、Viewer、比較、iframe、軌跡。Monacoを含む既定の依存物を先にセットアップする。導入済みElectronの指定は各スクリプトの実装を確認する。
- ズームの画像確認では、キャンバスの透明領域と内側の拡大、実画面のサイズ維持、終了後のキャンバス回収を区別する。光沢の掃引を追加しない。

実Electronの入力とOSの窓位置・寸法を使う検証でも、無操作のためカーソル位置・フォーカス判定だけを模擬する場合がある。Windowsでの結果をMac / Linuxの実機確認として扱わない。異なるDPIの画面間移動やMac / Linuxの描画は各実機でも確認する。

nativeのモデル選択ポップアップはWindows実機で、クリックで開く→別候補を選ぶ→閉じて選択値を確認するところまで検証する。通常窓・最大化、マウス・キーボードの両方を確認し、Code / Live / Discord / Diag / Avatarのモデル・音声選択を含める。headless環境でnative popup自体が表示されない場合、イベント通過やVueの選択テストの合格をWindowsのpopup実機合格として扱わない。

## アプリごとの保存先と排他

単体ファイルをElectronへ渡す起動では、既定のアプリ名がElectronとなり、別アプリのuserDataと排他ロックが重なる場合がある。aidiy_diagは ready・requestSingleInstanceLock より前に、appData配下の `aidiy_diag` を専用userDataへ指定する。Avatarの既存保存先は変更しない。IDE共通とDiscordの既存アプリ別保存先も維持する。全アプリのMacメニューだけを確認して、Windowsの同時起動確認を省略しない。保存先APIは [Electron公式app API](https://www.electronjs.org/docs/latest/api/app) を参照する。

再検証は `node --test backend_diag/checks/desktop.check.mjs`（3OS分岐と排他前の保存先指定、既存終了確認等）と、aidiy_diagとAvatarを同時に表示する実画面試験を分ける。

## 大きな修正後の総合テスト

[システム起動編](./セルフテスト,aidiy_diag,システム起動編.md) → [アプリ起動編](./セルフテスト,aidiy_diag,アプリ起動編.md) → [IDE操作編](./セルフテスト,aidiy_ide,操作編.md)の順に行う。IDE編に起動部分は再掲載しない。実画面と実モデルの結果を記録し、良好な結果は✅ OK、未到達は未実施とする。

主目的は総合テストと実施記録であり、記録した操作と画面は副産物として操作手順書の素材に再利用する。各冊のテスト通過後、元のMarkdownと同じフォルダへ同名のPDFを作成し、本文の修正後は再生成する。

aidiy_diagの環境診断機能は別冊の[環境確認編](./セルフテスト,aidiy_diag,環境確認編.md)で試験する。起動が成功しても、導入確認・モデル取得・外部連携・モデル試行の合格には置き換えない。

## 起動時のコマンド画面を出さない

Windowsで画面を持たない子プロセスは、Pythonでは `CREATE_NO_WINDOW`、Nodeでは `windowsHide: true` を指定する。環境確認・プロセス一覧・taskkillなどの短命な処理にも適用する。Electron本体はGUI形式の実行ファイルなので通常表示を許可し、窓そのものを隠す指定と混同しない。

AvatarのGUI起動は `electron/dev-start.cjs` がVite・TypeScript監視・Electron監視を直接管理する。npm/concurrentlyの入れ子のシェルを避ける。開発用の `npm run dev` も同じ入口を使う。

回帰試験は `node scripts/checks/Electron表示統合確認.cjs`。Pythonの実子プロセス、GUIバイナリ、各Electron画面と関連パネルを順に確認し、実施ごとのフォルダへログと結果を保存する。`AIDIY_ELECTRON_AUDIT_DIR` で保存先を指定できる。

試験用のクリック透過や1%不透明度を、共通ズームの `isAiDiyOpeningCanvas` が付いた窓へ適用しない。Windowsでは白い面になる条件がある。`capturePage`の透明な画像だけを根拠にせず、`Electron透明表示目視.cjs` とComputer UseでOS上の表示も確認する。目視用スクリプトへは、起動中IDEのURLを `AIDIY_PREVIEW_URL` で渡す。読み込み表示が消え、出航準備中を抜け、Canvasに星が描画されてから撮影する。撮影対象を前面に出し、別窓の重なりも確認する。ズーム途中を静止する試験なので、750msの時間測定には使わない。
