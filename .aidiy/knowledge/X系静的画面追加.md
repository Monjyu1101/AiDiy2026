# X系静的画面追加

## 参照する場面

`frontend_web` の `Xその他` 配下に、ゲーム・デモ・マスコットなどの実験的な静的画面を追加するときに参照する。

## 関連ファイル

- `frontend_web/src/router/index.ts`
- `frontend_web/src/components/Xその他.vue`
- `frontend_web/src/components/Xその他/<画面名>.vue`
- `frontend_web/src/components/Xテスト/<画面名>.vue`
- `frontend_web/public/<画面名>/index.html`
- `frontend_web/public/<画面名>/index.js`
- `frontend_web/public/<画面名>/style.css`
- `frontend_web/public/<画面名>/NOTICE.md`（外部アセットを置く場合）

## 実装パターン

- ゲーム系の X画面は、Vue コンポーネントを薄い iframe ラッパーにして、実体を `frontend_web/public/<画面名>/` 配下の静的 HTML/CSS/JS へ置く。
- マスコット系のように Vue 画面内で完結できるものは、iframe を使わず `frontend_web/src/components/Xテスト/<画面名>.vue` に直接実装してよい。
- ルートは `frontend_web/src/router/index.ts` の `baseRoutes` に追加する。
- メニュー導線は `frontend_web/src/components/Xその他.vue` のカードへ追加する。
- iframe ラッパーは既存の `Xテトリス.vue` / `Xインベーダー.vue` / `Xリバーシ.vue` と同じ戻URL処理を使う。
- Vue 直実装で確実に表示したい画像は `public` 直参照ではなく `src/assets` へ置いて import する。日本語 `public` パスや base URL の影響を受けにくい。

## 新規X画面の追加手順

1. 静的HTML型かVue直実装型かを決める。
   - Canvasゲーム、Three.js単体デモ、外部CDNを使う実験は `public/<画面名>/index.html` に寄せる。
   - 認証済みレイアウト内で小さく完結するUI、Vueの状態管理や既存部品を使う画面は `.vue` 直実装にする。
2. 静的HTML型では `src/components/Xその他/<画面名>.vue` を iframe ラッパーとして作る。
3. `src/router/index.ts` の `baseRoutes` に `/Xその他/<画面名>/ゲーム` または `/Xその他/<画面名>/表示` を追加し、`meta.requiresAuth: true` と `title` を設定する。
4. `src/components/Xその他.vue` にメニューカードを追加する。通常は `router-link` で `?戻URL=/Xその他` を渡す。全画面体験を優先する静的ページだけ、既存 `Xハローワールド` のように `public` の HTML を別タブで直接開く。
5. 外部ライブラリ、画像、音源、地図、フォントなどを同梱または参照する場合は `public/<画面名>/NOTICE.md` を作り、出典、ライセンス、ネットワーク制限時の挙動を残す。

## iframe ラッパーの基準

- `frameSrc` は `const baseUrl = import.meta.env.BASE_URL || '/'` を使って `${baseUrl}<画面名>/index.html` とする。Vite の base URL 変更に追随できる。
- `戻URL` は `route.query.戻URL` から読み、全角 `？＆＝` を半角へ正規化してから `router.push()` する。
- 親の高さ継承に失敗すると iframe が 0px になる。ラッパーは `height: 100%`, `display: flex`, iframe は `flex: 1` または `height: 100%` を持たせる。
- iframe 内から親アプリの認証ストアや router へ直接触らない。戻るボタンや画面遷移は Vue ラッパー側で担当する。
- 静的HTML本体は `/core` `/apps` API に依存させないのが原則。APIを使うなら通常のVue画面として実装する方が保守しやすい。

## 静的JSの実装基準

- `requestAnimationFrame`、`setTimeout`、`setInterval` は開始/停止関数に集約し、リセット、ゲームオーバー、ページ離脱相当の処理で必ず解除する。
- 経過時間は固定フレーム前提にせず、`timestamp` 差分や `dt` で補正する。
- 画像や音声の読み込み失敗時も画面が真っ白にならないよう、最低限のエラーメッセージやフォールバック描画を用意する。
- キーボード操作は入力欄やボタン操作と衝突しないよう、必要なキーだけ `preventDefault()` する。
- 画面内説明文は長くしすぎず、ゲーム/デモとして最初の画面から操作可能な状態にする。

## X立体リバーシ

- 本体は `frontend_web/public/X立体リバーシ/`、iframe ラッパーは `src/components/Xその他/X立体リバーシ.vue`。
- ルートは `/Xその他/X立体リバーシ/ゲーム`、メニュー導線は `Xその他.vue` に追加する。
- 盤は 6面×4x4。6面ネットは表示せず、Three.js の 3D キューブを直接クリックしてプレイする。
- 6面立方体のように特殊なゲームルールを実装する場合は、ルール説明、合法手ハイライト、CPU対戦、終局/特殊モード遷移ログを同時に実装し、単なる盤面だけにしない。
- 反転対象面が現在の視点で見えていない場合だけ自動カメラワークを発火する。`FACE_NORMALS` と `isFaceVisible()` で面法線の Z 成分を見て判定する。
- 面別カメラ目標角は、右面は Y が負方向、左面は Y が正方向、上面は X が正方向、下面は X が負方向。
- チャレンジモード突入時は即時に中央24枚を消さず、`start3dFlipAnimation()` のモーション所要時間後に合法手を判定する。
- 突入確定後は `challengeTransitioning` で操作を止め、透過気味の大きな突入メッセージを3Dビュー中央へ出す。
- `startChallengeClearAnimation()` で中央24枚を順に点滅・消去し、消去時にも見えていない面へカメラを向ける。
- チャレンジモードでは着手位置だけ中央24マスに限定する。`getLegalMoves()` は `isChallengeCell()` で絞り、`collectAllFlips()` は通常ルールと同じ反転結果を返す。
- 着手コマは `place` アニメーションで表示する。見えていない面への着手時は、反転前だけでなく着手表示前にもカメラを向ける。
- ルール欄は「立体リバーシルール」として、目的、通常モード、面またぎ判定、チャレンジモード、終了条件の順に書く。
- CPU操作は色ごとのトグルで判定する。青は `blackCpuEnabled` / `black-cpu-toggle`、赤は `cpuEnabled` / `cpu-toggle`、判定は `isCpuControlled(player)` に集約する。
- Three.js を `frontend_web` に依存追加しない静的ページでは CDN の ES module import を使えるが、オフライン環境では 3D 表示だけ失敗する。必須画面ではローカル依存化も検討する。

## Xハローワールド

- 本体は `frontend_web/public/Xハローワールド/`、Vue 側は `src/components/Xその他/Xハローワールド.vue` の全画面 iframe ラッパー。
- Leaflet + OpenStreetMap の静的地図アプリとして実装し、Wikipedia REST API / Wikimedia Commons の写真へ実行時アクセスする。
- `NOTICE.md` に Leaflet / OpenStreetMap / Wikipedia / Wikimedia Commons の利用元と、オフラインや外部ネットワーク制限では地図・写真が出ない可能性を残す。
- Xその他メニューから静的HTMLを別タブで直接開く。ブラウザ全画面はユーザー操作が必要なので、アプリ内に全画面ボタンを置く。
- 絶景地点は100件以上を持たせ、巡回は `Math.random()` 連発ではなくシャッフル済みキューを使う。
- 自動巡回は 24 秒間隔。訪問履歴は右下に直近3件だけ表示し、写真クレジットは右上へ逃がす。
- 場所名は大きいまま1行で見せる。`hero-panel` の幅を画面端近くまで広げ、`h1` は `white-space: nowrap` にする。
- 写真表示時は地図レイヤーを薄くして写真を主役にする。次地点への転換開始時に必ず `photo-active` を外し、黒い転換画面に見える状態を避ける。
- 写真は地図移動完了後にフェードインさせる。画像取得やキャッシュが早くても即表示しない。
- Leaflet の `moveend` と tile layer の `load` を待ってから次のズームや写真フェードへ進める。
- 地図拡大時は、表と裏の2枚の Leaflet map を用意し、裏側で目的地タイルを先読みしてから、読み込み済み地図を CSS の opacity/scale でフェードインさせる。
- 地図表示中はメインの場所名にも国名を含め、写真フェードイン後は場所名だけに戻す。

## Xインベーダー

- `requestAnimationFrame` の多重起動を避けるため、`startLoop()` / `stopLoop()` でフレームIDを管理する。
- 敵全滅後は `waveTransitioning` を立て、次ウェーブ配置待ち中に `nextWave()` が毎フレーム再実行されないようにする。
- 移動・弾・タイマーは固定 16.67ms 前提にせず、`dt / 16.67` で補正する。
- 被弾時は敵弾を消して短い無敵時間を入れ、同一フレームや連続弾でライフが一気に減らないようにする。
- `setTimeout` は `clearTimers()` に集約し、新規開始・メニュー・ゲームオーバーで必ず消す。
- 射撃クールダウンと連射パワーアップのタイマーが次ゲームへ残ると、ポーズ中射撃や連射状態の持ち越しが起きる。

## Xテトリス

- ピース固定後から次ピース出現まで `pieceLocked` で入力・落下・二重固定を止める。
- ライン消去や次ピース出現の `setTimeout` は `setManagedTimeout()` に集約し、リセット・ゲームオーバー時に `clearPendingTimers()` で消す。
- 複数ライン消去は、行ごとに `splice()` と `unshift()` を繰り返すとインデックスがずれる。削除対象行を `Set` にして残行を再構成し、空行を上にまとめて追加する。
- I ミノは横一列だけでなく縦向き回転も定義する。
- ライン消去アニメーションは、固定ピースを消して `renderBoard()` した後に `animateLineClear()` を付ける。

## Xネコ / xneko 系

- `react-neko` という npm パッケージは 2026-04-23 時点で npm registry に存在しない。近いものとして `neko-ts` があるが `UNLICENSED` なので、依存追加する場合はライセンス確認を優先する。
- `Xネコ` は `oneko.js` 互換の 32px スプライト方式へ変更した。`oneko.gif` は `adryd325/oneko.js` の MIT ライセンス資産なので、`public/Xネコ/NOTICE.md` に出典とライセンスを残す。
- `frontend_avatar/public/xneko_*.gif` は `256x128`（32px タイル 8×4）の透過スプライトシートとして扱う。
- 色違い猫を作る場合は、既存 `oneko.gif` の輪郭・透明部分を保持して色だけ置換する方が、`AIコア_xneko.vue` の `background-position` 指定とズレにくい。
- 白背景画像から透過GIFを作る場合、白い毛を温存するため単純閾値ではなく四隅フラッドフィルで背景を除去する。

## 注意点

- `public` 配下の日本語ディレクトリは Vite でそのまま配信できるが、ブラウザ確認では URL エンコードされたパスでも取得できることを確認する。
- Vue 側の新規コンポーネントタグは日本語タグで直接書かず、ルート lazy import や `<component :is="...">` を使う。
- X系の静的ページはバックエンドAPIを使わないため、基本確認は `npm run type-check`、必要に応じた `node --check public/<画面名>/index.js`、Vite 経由の HTTP 取得で足りる。
- Vue 直実装の場合は `node --check` 対象がないので、`npm run type-check` を優先する。
- 画面表示が出ない場合は、親レイアウトの高さ継承だけに頼らず、ステージ側に `min-height` を持たせる。
- DevTools MCP が使える場合は、最終的に `http://localhost:8090/<画面名>/index.html` を開いてコンソールエラーと描画を確認する。
- 静的HTMLを別タブで直接開く導線は認証ガードを通らない。認証済みメニューからの実験導線として扱い、業務データ表示や更新には使わない。
- `npm run build` は指示なしに実行しない。X系の通常確認は `npm run type-check`、静的JSの `node --check`、Vite経由の描画確認に留める。

## 最低限の確認方法

```powershell
cd frontend_web
npm run type-check
node --check .\public\<画面名>\index.js
Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8090/<URLエンコード済み画面名>/index.html'
```

Vue ラッパー経由でも確認する。

```powershell
Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8090/Xその他/<画面名>/ゲーム'
```
