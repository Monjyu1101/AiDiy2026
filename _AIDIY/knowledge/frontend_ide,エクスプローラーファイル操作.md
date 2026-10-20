# エクスプローラーファイル操作

> 文書: `frontend_ide,エクスプローラーファイル操作.md` | 実装: `frontend_ide/src/ファイル閲覧/ファイル一覧.vue`, `frontend_ide/src/ファイル閲覧/エクスプローラー操作.js`, `frontend_ide/src/ファイル閲覧/エクスプローラー操作表示.vue`, `frontend_ide/ファイル機能/explorer-files.mjs`, `frontend_ide/ファイル機能/explorer-native.mjs`, `frontend_ide/ファイル機能/explorer-windows.ps1`

## このメモを使う場面

- Explorerの右クリック・インライン名前変更・コピー・ゴミ箱移動を変更するとき。
- OS差分、パス境界、競合、利用終了中のファイル操作を検証するとき。

## 境界

`ファイル一覧.vue` は本体とピン留め別窓で同じVue／DOMを使う。操作状態は `エクスプローラー操作.js` に持ち、OSのファイルクリップボードとは分離する。パスの文字コピーだけはOSクリップボードを使い、拒否時は手動コピー欄を表示する。名前変更はEnter適用／Esc取消、IME変換中のEnter・Escは確定・取消として扱わない。メニューの `selection-popup` とダイアログの `role="dialog"` は既存のネイティブ長押し窓移動を止めるため維持する。

変更APIは `POST /api/explorer/actions`。JSONと `X-AiDiy-Explorer: 1` の両方を必須にし、既存のHost／Origin／利用セッション検証を通す。読み取りAPIやViewerの本文編集機能は増やさない。操作を直列化し、利用終了と接続世代の変更で待機要求を無効化する。

パスはプロジェクト相対の `/` 区切りだけ。ルート変更、絶対パス、親への脱出、リンクを通るパス、予約名、別ドライブ、ADSを拒否する。作成は排他的、コピーは衝突時に別名、名前変更はOSの上書き禁止機能を使う。フォルダコピーは全対象を検査し、リンク・自己／子孫コピー・容量／件数超過を拒否する。コピー中に問題があれば元を保持し、途中コピーを勝手に消さず場所を通知する。

ゴミ箱はLinuxの `gio trash`、macOSのFoundation、WindowsのIFileOperationを使う。Windowsは `PreDeleteItem` でもリサイクル処理だけを許可する。完全削除へのfallbackは禁止。OS処理の結果が不明な場合は再実行せず、元の場所とOSゴミ箱の確認を案内する。Windowsは8以降のローカル固定ドライブに限定し、ネットワーク／リムーバブルドライブは拒否する。Windows/macOSの実動作は各OSで別途確認する。

なお、同一サーバー内では操作を直列化するが、別プロセスが最終検査とOS呼出しの間に祖先フォルダを差し替える攻撃まで防ぐOSレベルのサンドボックスではない。信頼できないプロセスが同じプロジェクトを同時に書き換える環境では利用しない。

## 再検証

`frontend_ide` で次を実行する。

- `node --test checks/explorer-actions.test.mjs checks/explorer-files.test.mjs checks/explorer-navigation.test.mjs checks/workflow-components.test.mjs checks/native-window-move.test.mjs checks/panel-lifecycle.test.mjs`
- `npm test` と `node --test viewer/checks/*.test.mjs`。
- `node scripts/check-explorer-component.mjs` は実Vueとsandbox有効のElectronをdata:画面に載せる隔離fixture。APIは固定データで、通常のメニュー／名前変更／確認／キーボード／別窓／長押し除外を確認する。headlessの1×1または空画像は視覚確認済みとは扱わない。
- UIの表示確認用に `node scripts/build.mjs` を実行した後、`node scripts/check-explorer-menu.mjs`。これは通常のChrome／Edgeが利用できる環境用で、実ファイルは専用一時fixture、ゴミ箱は専用一時フォルダへの移動で代替する。ブラウザーの接続／sandbox拒否を弱いフラグで回避しない。

Linuxのゴミ箱テストも専用の一時HOMEとXDG_DATA_HOMEだけを使う。既存のユーザーデータや通常のゴミ箱を使わず、復元可能なファイルが作成されたことを確認する。実機ではファイル／フォルダ、同名衝突、消えたコピー元、権限拒否、シンボリックリンク、ルート背景、別窓、モーダル中の窓移動禁止、Enter／Esc／IME、途中の終了・再接続を確認する。
