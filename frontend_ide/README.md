# AiDiy IDE（Vue）

Code / Live / IDE の画面をVue 3で共通化します。VS Code拡張はCode / Live、単独実行は3種類です。

## 開発スペース — 宇宙をテーマにした IDE 開発環境

AiDiy IDE は、プロジェクトを宇宙に見立てた **開発スペース** です。フォルダは銀河、ファイルは星・惑星として浮かび、1階層ずつ宇宙を渡り歩いてプロジェクトを把握します。

目指すのは「ソースをほぼ触らない IDE」です。

| 役割 | 開発スペースでの姿 |
|---|---|
| 全体を眺める | 宇宙表示。フォルダの大きさ・ファイルの種類・更新の新しさが、銀河の形・星の色・明るさで見える |
| 正確に辿る | 左上の ☰ で開くエクスプローラー（VS Code 風のツリー）、プロジェクト全体の検索・grep 検索 |
| 中身を読む | 読み取り専用のビューア（コードは Monaco Editor、画像・Office 文書・PDF も表示） |
| 変えてもらう | Code（コード支援チャット）と Live（音声会話）に頼み、変更は AI に任せる |
| 変化を見つける | 起点日時より後に更新されたファイルが明滅し、AI が触った場所がひと目でわかる |

人は書かずに、眺めて・辿って・読んで・頼む。その作業の場を、宇宙という一つの空間にまとめています。

Code / Live は、これまでどおり単独起動（`aidiy_code` / `aidiy_live`）と VS Code 拡張として使えます。そのうえで開発スペースの部品としても動作し、IDE の中から同じプロジェクト・利用モード・セッションのまま呼び出せます（Electron 版は「＋ Code」「＋ Live」で別ウィンドウ、Web 版は画面内タブ）。

| 使い方 | 起動 | 向いている場面 |
|---|---|---|
| 単独起動 | `aidiy_code` / `aidiy_live` | 作業フォルダで AI にすぐ頼みたい時 |
| VS Code 拡張 | セカンダリサイドバー | VS Code でコードを開いたまま頼みたい時 |
| 開発スペースの部品 | `aidiy_ide` の「＋ Code」「＋ Live」 | 宇宙で全体を把握しながら、AI に頼んで変化を確かめたい時 |

同じ部品が3つの場所で動くことで、IDE 開発への応用が広がっています。

## 起動

セットアップはリポジトリ直下で `python frontend_ide/_setup.py`。既存の全体セットアップからも共通画面を準備します。
セットアップ済みなら、表示したいフォルダで `aidiy_code`、`aidiy_live`、`aidiy_ide` を実行します。3つのコマンドは共通のVue画面を起動します。IDEの起動名は `aidiy_ide`、アプリ指定は `--app ide` です。

PATH登録なしでも `node <配置先>/frontend_ide/launch.mjs --app ide`（code / liveも可）。引数を省略した作業フォルダは実行時のカレントフォルダです。`--project <フォルダ>`、`--browser`、`--no-open`、`--port <番号>`、`--strict-port` に対応します。ポートの既定は0（自動割り当て）。Electronを使えない環境とCodespacesはWebで開きます。Codeの `--offline` はHermesを直接使用します。Liveの `--connect` は初回だけ接続します。

IDEは画面の「AiDiy接続利用」「オフライン利用」で手動開始します。利用開始後にコアとの接続を失っても、ファイル表示・作業起点・Code子窓を維持し、コア復帰時に再接続します。初回接続失敗は手動で再試行します。オフラインではLiveの起動ボタン・タブを表示しません。

宇宙表示は中心を注視したまま、約75〜105秒を目安に楕円軌道を自動飛行します。接近時は速く、遠点では遅くなるよう、ケプラー方程式で進行速度を求めます。最遠点ごとに反対側への接近方向と軌道の傾きを少し変えます。ファイル選択中・フォルダ移動中は停止し、手動の回転・平行移動・ズーム後は最後の操作から1分停止します。再開時は現在の視点から滑らかに戻ります。スペースキーで自動飛行の有効・無効を切り替えられます。

Electron版IDEは右上の「＋ Code」「＋ Live」で別ウィンドウを開きます。プロジェクト・利用モード・セッションをIDEに連携させます。「終了」はそこから開いたCode / Liveと各通信を終了し、IDEの起動画面へ戻ります。タイトルバーの×は「AiDiy IDE を終了しますか？」と確認し、「終了する」でIDEと子窓をすべて閉じます。「キャンセル」では作業を維持します。利用セッションの切り替えでも別窓を閉じます。`start`のCtrl+Cによるコア停止では別窓を閉じません。別窓のCodeから接続モードは変更できません。Code / Liveだけを個別に閉じることもできます。Web版・Codespacesは従来通り画面内のCode / Liveタブを使います。

Code / Live / IDEの単独Electron起動は、画面表示後にコマンドプロンプトへ戻ります。サーバーと画面は独立して動作し、×で画面を閉じるとサーバーも終了します。起動済みなら既存画面を前面へ出して戻ります。終了までコマンドを待機させる場合は `aidiy_code --foreground` / `aidiy_live --foreground` / `aidiy_ide --foreground`（または `--wait`）。`--browser`、`--no-open`、`--serve` は従来どおりサーバーを前面で動かします。

## 部品

| 部品 | 責務 |
|---|---|
| `CodePanel.vue` | チャット・モデル・履歴・停止・下書き。VS Codeと単独版で共用 |
| `LivePanel.vue` | 音声・文字会話・モデル。VS Codeと単独版で共用 |
| `FileExplorer.vue` | バーガー、階層ツリー、起点検索、grep検索、マーク。`select` / `marks` イベントで外側と連携 |
| `SpaceView.vue` | 宇宙・エクスプローラー・プレビューの配置と選択連動 |
| `FileViewer.vue` | 読み取り専用のコード・画像・Office/PDFプレビュー |
| `StatusBar.vue` / `TerminalWelcome.vue` | 接続表示・ウィンドウ操作・初期ターミナル演出 |

Canvas描画は `src/engines/space.js`、通信は `src/transports/` に分離します。Web版IDEのCode / LiveはVue部品を直接配置し、Electron版は同じVue部品を別ウィンドウに表示します。Office表示だけは既存の専用iframeを使用します。

ファイルAPI・Office依存物は `viewer/`、Code/Hermes・LiveプロトコルとVS Code拡張ホストは `host/` に統合しています。画面と実行基盤はこの `frontend_ide/` 内で管理します。AIコア・Hermes・共通設定は引き続きプロジェクト共通のものを利用します。

## 配布と検証

- 配布画面更新: このフォルダで `npm run build`。同じbundleをCode / LiveのVS Code配布先にもコピーします。
- 拡張作成: `frontend_ide/host` で `npm run package`。既存の2つの拡張IDとVSIX名を維持します。
- 共通テスト: このフォルダで `npm test`。
- 実画面検証: ルートで `node frontend_ide/scripts/capture.mjs`。Chrome/EdgeとローカルAIコアのヘルス応答が必要です。AIへの依頼・音声送信は行いません。ルートへ `nn-vue-*.png` を保存します。
- Vueホストの操作検証: ルートで `node frontend_ide/scripts/check-host.mjs`（模擬VS Code接続、AI通信なし）。履歴・モデル・検証回数・音声設定引継ぎと遅延応答を確認し、`nn-audit-*.png` を保存します。
- Code / Live の演出確認: ルートで `node frontend_ide/scripts/check-chat-effects.mjs`。初期文字送り、紙ヒコーキ画像、入力枠の飛行、処理中の上下バー、中央回答から履歴への着地、連続受信・会話切替を実ブラウザで検証し、`nn-effects-*.png` を保存します。旧 `frontend_vscode` がある場合は参照画面も読取専用で撮影します。
- 単独窓の二重起動・前面復帰: `node frontend_ide/scripts/check-single-instance.mjs`（実行中の利用者画面とは別の一時プロファイルで確認）。
- Code / Live / IDEランチャーの分離起動: `node frontend_ide/scripts/check-launcher.mjs code` / `node frontend_ide/scripts/check-launcher.mjs live` / `node frontend_ide/scripts/check-launcher.mjs ide`（プロンプト復帰後の画面・サーバー継続、二重起動、×での終了、待機指定、起動失敗の通知を一時プロファイルで確認）。
- IDEの別ウィンドウ検証: `node frontend_ide/scripts/check-windows.mjs`（起動制限・プロジェクト引継ぎ・利用終了・全窓終了・疑似音声）。
- コア停止時の作業継続・IDE終了操作: `node frontend_ide/scripts/check-core-stop.mjs`（検証用コアだけを停止・再起動し、IDEのファイル表示、Codeの窓・下書き、作業起点を維持。「終了」でCode / Liveを閉じて起動画面へ戻り、再利用できることと、×の確認取消・承認・重複防止・後片付けを実Electronで確認。OS確認ダイアログの選択だけはテストで代行）。
- 自動視点の確認: `node frontend_ide/scripts/check-orbit.mjs`（ブラウザ内の描画時計を進め、楕円飛行・選択停止・手動操作後60秒停止を検証し、`nn-orbit-*.png` を撮影）。
- Electron・音声権限の確認: `node frontend_ide/scripts/check-electron.mjs`（疑似音声デバイス）。
- 同じ Electron 確認で、タイトルバーの最大化／元のサイズへの復元も実ウィンドウで検証します。
- 音声・バックエンドの回帰確認: `frontend_ide/host` の `npm test` / `npm run live:test`、`frontend_ide/viewer` の `npm test`。

全体のsetup・cleanupは「IDE群(Code / Live / IDE)」を一括選択します。startは同じIDE群の中でCode → Live → IDEを個別に選び、その後にDiscordを選びます。セットアップで稼働中の画面を停止しません。cleanupはhost → viewer → 共通UIの順に解除し、停止・解除に失敗した場合は共通のnode_modulesとdistを残します。

## ウィンドウ配置

Electron版は現在の画面の作業領域（タスクバーを除く）に合わせ、IDEを余白付きで大きく開きます。Code / Live は幅480 × 高さ600（最小360 × 480、Electronの論理ピクセル）です。寸法は `host/scripts/window-size.cjs` を共用し、収まらない小画面だけ縮小します。単独版は画面上端から8px、Codeを左端から8px、Liveを右端から8pxに開きます。IDEから開くCode / LiveはIDEの左右端から24px内側に置き、上端をどちらもIDEから36px下へずらし、Code / Liveの上端と高さを揃えます。IDE配下のタイトルは「AiDiy IDE / Code」「AiDiy IDE / Live」です。移動済みの窓を再選択しても配置を戻しません。

単独版は種類ごとに二重起動を防ぎ、起動済みの窓を復元して前面に出します。IDEから開いたCode / Liveは常に最前面に表示します。IDE連携の「＋Code」は依頼ごとに別窓を開き、2窓目以降を少しずらして配置します。「＋Live」はオンライン時だけ利用でき、初期化中も含めて1窓に制限します。Live起動後はボタンを隠し、閉じると再表示します。IDEの明示終了に連動して子窓を終了します。

## 利用条件

COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026

自作部分は `LICENSE`、Vue / Markdown等は配布物の `THIRD_PARTY_NOTICES.txt` を参照してください。Office関連の帰属・利用条件は既存ビューアのライセンス情報を引き継ぎます。画面上に著作権リンクは追加しません。
