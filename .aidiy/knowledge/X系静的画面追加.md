# X系静的画面追加

## 参照する場面

`frontend_web` の `Xその他` 配下に、ゲーム・デモ・マスコットなどの実験的な静的画面を追加するときに参照する。

## 関連ファイル

- `frontend_web/src/router/index.ts`
- `frontend_web/src/components/Xその他.vue`
- `frontend_web/src/components/Xテスト/<画面名>.vue`
- `frontend_web/public/<画面名>/index.html`
- `frontend_web/public/<画面名>/index.js`
- `frontend_web/public/<画面名>/NOTICE.md`（外部アセットを置く場合）

## 実装の結論

- ゲーム系の X画面は、Vue コンポーネントを薄い iframe ラッパーにして、実体を `frontend_web/public/<画面名>/` 配下の静的HTML/JSへ置く。
- マスコット系のように Vue 画面内で完結できるものは、iframe を使わず `frontend_web/src/components/Xテスト/<画面名>.vue` に直接実装してよい。
- ルートは `frontend_web/src/router/index.ts` の `baseRoutes` に追加する。
- メニュー導線は `frontend_web/src/components/Xその他.vue` のカードへ追加する。
- iframe ラッパーは既存の `Xテトリス.vue` / `Xインベーダー.vue` / `Xリバーシ.vue` と同じ戻URL処理を使う。
- `react-neko` という npm パッケージは 2026-04-23 時点で npm registry に存在しない。近いものとして `neko-ts` があるが `UNLICENSED` なので、このプロジェクトへ依存追加する場合はライセンス確認を優先する。
- `Xネコ` は `oneko.js` 互換の 32px スプライト方式へ変更した。`oneko.gif` は `adryd325/oneko.js` の MIT ライセンス資産なので、`public/Xネコ/NOTICE.md` に出典とライセンスを残す。
- Vue 直実装で確実に表示したい画像は `public` 直参照ではなく `src/assets` へ置いて import する。日本語 `public` パスや base URL の影響を受けにくい。
- `X立体リバーシ` は `frontend_web/public/X立体リバーシ/` に静的 HTML/CSS/JS を置き、`src/components/Xその他/X立体リバーシ.vue` を iframe ラッパーとして追加した。ルートは `/Xその他/X立体リバーシ/ゲーム`、メニュー導線は `Xその他.vue` に追加する。盤は 6面×4x4。現在は 6面ネットを表示せず、Three.js の 3D キューブを直接クリックしてプレイする。
- `X立体リバーシ` の自動カメラワークは、反転対象面が現在の視点で見えていない場合だけ発火する。`FACE_NORMALS` と `isFaceVisible()` で面法線の Z 成分を見て判定し、見えている反転はカメラ移動を挟まずその場で反転させる。
- `X立体リバーシ` の面別カメラ目標角は、左右・上下で符号を取り違えると反対面を映す。右面は Y が負方向、左面は Y が正方向、上面は X が正方向、下面は X が負方向になる。
- `X立体リバーシ` のチャレンジモード突入時は、即時に中央24枚を消さず、`start3dFlipAnimation()` が返すモーション所要時間後に合法手を判定する。突入確定後、`challengeTransitioning` で操作を止めてから透過気味の大きな突入メッセージを3Dビュー中央へ出す。`startChallengeClearAnimation()` で中央24枚を順に点滅・消去し、消去時にも見えていない面へカメラを向ける。
- `X立体リバーシ` のチャレンジモードでは、合法手は中央24マスだけに限定するが、反転判定は通常モードと同じにする。`getLegalMoves()` は `isChallengeCell()` で着手位置だけを絞り、`collectAllFlips()` は端列や面またぎも含めた通常ルールの結果を返す。
- `X立体リバーシ` の着手コマは `place` アニメーションで表示する。消去モーションの逆方向として、小さく発光した状態から浮き上がりつつ通常サイズへ戻す。着手面が見えていない場合は、反転前だけでなく着手表示前にもカメラを向ける。
- `X立体リバーシ` のルール欄は「特別ルール」ではなく「立体リバーシルール」として、目的、通常モード、面またぎ判定、チャレンジモード、終了条件をゲームルールとして読める順序で書く。
- `X立体リバーシ` のCPU操作は色ごとのトグルで判定する。青は `blackCpuEnabled` / `black-cpu-toggle`、赤は既存の `cpuEnabled` / `cpu-toggle` を使い、現在手番がCPU対象かどうかは `isCpuControlled(player)` に集約する。
- `Xインベーダー` は `requestAnimationFrame` の多重起動を避けるため `startLoop()` / `stopLoop()` でフレームIDを管理する。敵全滅後は `waveTransitioning` を立て、次ウェーブ配置待ち中に `nextWave()` が毎フレーム再実行されないようにする。
- `Xインベーダー` の移動・弾・タイマーは固定 16.67ms 前提にせず、`dt / 16.67` で補正する。被弾時は敵弾を消して短い無敵時間を入れ、同一フレームや連続弾でライフが一気に減らないようにする。
- `Xインベーダー` の `setTimeout` は `clearTimers()` に集約して、新規開始・メニュー・ゲームオーバーで必ず消す。射撃クールダウンと連射パワーアップのタイマーが次ゲームへ残ると、ポーズ中射撃や連射状態の持ち越しが起きる。
- `Xテトリス` はピース固定後から次ピース出現まで `pieceLocked` で入力・落下・二重固定を止める。ライン消去や次ピース出現の `setTimeout` は `setManagedTimeout()` に集約し、リセット・ゲームオーバー時に `clearPendingTimers()` で消す。
- `Xテトリス` の複数ライン消去は、行ごとに `splice()` と `unshift()` を繰り返すとインデックスがずれる。削除対象行を `Set` にして残行を再構成し、空行を上にまとめて追加する。
- `Xテトリス` の I ミノは横一列だけでなく縦向き回転も定義する。ライン消去アニメーションは、固定ピースを消して `renderBoard()` した後に `animateLineClear()` を付ける。
- `Xハローワールド` は `frontend_web/public/Xハローワールド/` に Leaflet + OpenStreetMap の静的地図アプリを置く。Vue 側は `src/components/Xその他/Xハローワールド.vue` の全画面 iframe ラッパーにし、戻るボタンだけ重ねる。
- `Xハローワールド` は地図CDNとOSMタイル、Wikipedia REST API / Wikimedia Commons の写真へ実行時アクセスする。`NOTICE.md` に Leaflet / OpenStreetMap / Wikipedia / Wikimedia Commons の利用元を残し、オフラインや外部ネットワーク制限では地図や写真が出ない可能性を明記する。
- `Xハローワールド` は Xその他メニューから静的HTMLを別タブで直接開く。写真表示時は地図レイヤーを薄くして写真を主役にし、自動巡回は 24 秒間隔にする。ブラウザ全画面はユーザー操作が必要なので、アプリ内に全画面ボタンを置く。
- `Xハローワールド` の絶景地点は100件以上を持たせ、巡回は単純な `Math.random()` 連発ではなくシャッフル済みキューを使う。キューを使い切るまで重複しにくくなり、長時間の自動巡回でも同じ地点へ偏りにくい。
- `Xハローワールド` の訪問履歴は画面を邪魔しやすいので、右下に直近3件だけ表示する。写真クレジットは右上へ逃がし、地図・写真・ログが重ならないようにする。
- `Xハローワールド` の場所名は大きいまま1行で見せる。`hero-panel` の幅を画面端近くまで広げ、`h1` は `white-space: nowrap` にする。地図転換中の画面上部バナーは出さず、メイン場所名側で現在地を見せる。
- `Xハローワールド` で写真を主役にするため `photo-active` 時に地図を薄くする場合、次地点への転換開始時に必ず `photo-active` を外す。外さないと写真だけ消えて地図も薄いままになり、黒い転換画面に見える。
- `Xハローワールド` の写真は地図移動完了後にフェードインさせる。画像取得やキャッシュが早くても即表示せず、ズームアウト・移動・ズームインの時間を待ってから `photo-layer.visible` を付ける。
- `Xハローワールド` の地図がタイル状に見える場合は、時間待ちだけでは不十分。Leaflet の `moveend` と tile layer の `load` を待ってから次のズームや写真フェードへ進める。
- `Xハローワールド` の地図拡大は、表示中の Leaflet map を直接ズームするとタイル差し替えが目立つ。表と裏の2枚の Leaflet map を用意し、裏側で目的地タイルを先読みしてから、読み込み済み地図を CSS の opacity/scale でフェードインさせる。
- `Xハローワールド` の地図表示中は、メインの場所名にも国名を含める。写真フェードイン後は場所名だけに戻すと写真表示時の見出しが短く保てる。
- 6面立方体のように特殊なゲームルールを実装する場合は、ルール説明を画面内に明記し、合法手ハイライト・CPU対戦・終局/特殊モード遷移のログを同時に実装して、単なる盤面だけにしない。
- Three.js を `frontend_web` に依存追加しない静的ページでは、CDN の ES module import を使うと `node --check` は通るが、オフライン環境では 3D 表示だけ失敗する。3D 表示が必須の画面は、可能ならローカル依存化も検討する。

## 注意点

- `public` 配下の日本語ディレクトリは Vite でそのまま配信できるが、ブラウザ確認では URL エンコードされたパスでも取得できることを確認する。
- Vue 側の新規コンポーネントタグは日本語タグで直接書かず、今回のようなルート lazy import なら問題ない。
- X系の静的ページはバックエンドAPIを使わないため、基本確認は `npm run type-check`、必要に応じた `node --check public/<画面名>/index.js`、Vite 経由の HTTP 取得で足りる。
- Vue 直実装の場合は `node --check` 対象がないので、`npm run type-check` を優先する。
- 画面表示が出ない場合は、親レイアウトの高さ継承だけに頼らず、ステージ側に `min-height` を持たせる。
- DevTools MCP が使える場合は、最終的に `http://localhost:8090/<画面名>/index.html` を開いてコンソールエラーと描画を確認する。

## 最低限の確認方法

```powershell
cd frontend_web
npm run type-check
node --check .\public\<画面名>\index.js
Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8090/<URLエンコード済み画面名>/index.html'
```
