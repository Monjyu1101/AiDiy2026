# X系静的画面追加

> 文書: `frontend_web,X系静的画面追加.md` | 実装: `frontend_web/src/router/index.ts`, `frontend_web/src/components/Xその他.vue`

## このメモを使う場面
- `frontend_web` の `Xその他` 配下にゲーム、デモ、マスコットなどの実験画面を追加する
- Vue ルートから `public/<画面名>/index.html` を iframe 表示する
- 既存の X系画面で静的 JS / Canvas / Three.js の不具合を直す

## 関連ファイル
- `frontend_web/src/router/index.ts` — X系ルートを `baseRoutes` に追加
- `frontend_web/src/components/Xその他.vue` — メニューカード
- `frontend_web/src/components/Xその他/<画面名>.vue` — iframe ラッパー
- `frontend_web/src/components/Xテスト/<画面名>.vue` — Vue 直実装の場合
- `frontend_web/public/<画面名>/index.html`
- `frontend_web/public/<画面名>/index.js`
- `frontend_web/public/<画面名>/style.css`
- `frontend_web/public/<画面名>/NOTICE.md` — 外部アセットや外部APIを使う場合

## 実装方式の判断

| 方式 | 使う場面 | 配置 |
|------|----------|------|
| 静的HTML + iframe | Canvasゲーム、Three.js単体デモ、外部CDNを使う実験 | `public/<画面名>/` + `components/Xその他/<画面名>.vue` |
| Vue 直実装 | 認証済みレイアウト内で完結し、Vue状態管理や既存部品を使う画面 | `components/Xテスト/<画面名>.vue` など |
| 別タブ直接表示 | 全画面体験を優先し、認証済みメニューから実験ページを開くだけの画面 | `public/<画面名>/index.html` |

業務データを表示・更新する画面は X系静的HTMLにせず、通常の Vue 画面として実装する。

## 追加手順
1. 静的HTML型か Vue 直実装型かを決める。
2. 静的HTML型では `frontend_web/public/<画面名>/index.html` / `index.js` / `style.css` を作る。
3. iframe 型では `src/components/Xその他/<画面名>.vue` を作る。
4. `src/router/index.ts` の `baseRoutes` に `/Xその他/<画面名>/ゲーム` または `/Xその他/<画面名>/表示` を追加し、`meta.requiresAuth: true` と `title` を設定する。
5. `src/components/Xその他.vue` にメニューカードを追加する。通常は `router-link` で `?URLメニュー=/Xその他` を渡す。
6. 外部ライブラリ、画像、音源、地図、フォント、外部APIを使う場合は `NOTICE.md` に出典、ライセンス、ネットワーク制限時の挙動を残す。

## iframe ラッパーの基準
- `frameSrc` は `const baseUrl = import.meta.env.BASE_URL || '/'` を使って `${baseUrl}<画面名>/index.html` とする。
- `URLメニュー` は `route.query.URLメニュー`、必要に応じて `URL戻り先` は `route.query.URL戻り先` から読み、全角 `？＆＝` を半角へ正規化してから `router.push()` する。
- ラッパーは `height: 100%`, `display: flex`、iframe は `flex: 1` または `height: 100%` を持たせる。
- iframe 内から親アプリの認証ストアや router へ直接触らない。戻る操作は Vue ラッパー側で担当し、`URL戻り先` があれば優先して戻る。
- 静的HTML本体は `/core` `/apps` API に依存させない。API が必要なら通常 Vue 画面に寄せる。

## 静的 JS の実装基準
- `requestAnimationFrame`、`setTimeout`、`setInterval` は開始 / 停止関数に集約し、リセット、ゲームオーバー、ページ離脱相当の処理で解除する。
- 固定フレーム前提にせず、`timestamp` 差分や `dt` で時間補正する。
- 画像や音声の読み込み失敗時も真っ白にならないよう、エラーメッセージやフォールバック描画を用意する。
- キーボード操作は必要なキーだけ `preventDefault()` し、入力欄やボタン操作と衝突させない。
- UI から変更する設定値は `const` にせず、`let` か状態オブジェクトで管理する。
- 停止復旧の watchdog は毎 tick で再生要求を連打しない。再開要求は一度だけ出し、タイムアウトで次状態へ進める。

## 既存 X画面別の注意点

### Xピンボール
- ピンボール系デモで見習うべき実装は `public/Xピンボールsol/` に集約する。類似実装を増やさず、ゲームループ、入力、デモ動作、停止処理、デバッグ方法を改善するときは `Xピンボールsol` を更新する。
- 本体は `index.html`、`style.css`、`game.js` に分離し、Vue 側は `components/Xその他/Xピンボールsol.vue` の iframe ラッパーに留める。
- `requestAnimationFrame` とタイマーは `pagehide` で停止し、タブ非表示時は一時停止する。キーボード、ポインター、画面ボタンの状態は同じゲーム状態へ集約する。
- 無操作デモと通常プレイを同じ `startGame()` から開始できるようにし、自動確認用の読み取り API は `window.XPinballSol` にまとめる。
- `Xピンボールsol` のギミックは装飾だけにせず、SOL CORE の重力場、ECLIPSE MOON の重力反転、UMBRA / AURORA の空間転移、PHOTON SAIL の可動衝突判定のように、描画・物理・得点・効果音を一つの状態へ接続する。
- ORBIT LOOM は直前のボール軌跡を `wovenRails` の物理レールへ変換する。描画だけの軌跡にせず、線分衝突、寿命、得点、記憶率 UI を同じ rail 状態から更新する。左右同時押しは押下中の連続発火を `dualFlipLatched` で防ぐ。
- 落球軌跡を残す MEMORY SCAR は盤内座標へ絞り、次球を救える位置に物理レールとして残す。手動レールと区別できる色、ラベル、反発、得点を持たせる。
- 発射レーン付近の装飾線や障害物は、待機球から盤面進入までの経路を横切らない。見た目の確認だけでなく `window.XPinballSol.launch()` 後に `entered: true` になることを確認する。
- 自動描画確認は `index.html?demo=1`、状態確認は `window.XPinballSol.getState()` を使う。軌道織りの狙い撃ち確認は `probeWeave()`、失敗記憶は `probeFailureMemory()` を使い、`wovenRails[].hits` と `scar` を確認する。

### X立体リバーシ
- 本体は `public/X立体リバーシ/`、iframe ラッパーは `components/Xその他/X立体リバーシ.vue`。
- ルートは `/Xその他/X立体リバーシ/ゲーム`。
- 盤は 6面 x 4x4。6面ネットではなく Three.js の 3D キューブをクリックしてプレイする。
- 特殊ルールを入れる場合は、合法手ハイライト、CPU対戦、終局 / 特殊モード遷移ログを同時に用意する。
- 見えていない面の反転や着手では、`FACE_NORMALS` と `isFaceVisible()` で判定して自動カメラワークを発火する。
- チャレンジモード突入時は `challengeTransitioning` で操作を止め、アニメーション完了後に合法手を再判定する。
- Three.js を依存追加しない静的ページでは CDN import を使えるが、オフライン環境では 3D 表示だけ失敗する。

### X世界の絶景
- 本体は `public/X世界の絶景/`、Vue 側は `components/Xその他/X世界の絶景.vue`。
- 地点リストは `list.js` に分離し、`index.html` では `list.js` を `index.js` より先に読む。
- Leaflet / OpenStreetMap / Wikipedia / Wikimedia Commons を使う場合は `NOTICE.md` に利用元とオフライン時の制約を残す。
- 巡回は `Math.random()` 連発ではなくシャッフル済みキューを使う。
- 写真表示時は地図レイヤーを薄くし、次地点への転換開始時に `photo-active` を必ず外す。
- 地図移動、tile load、写真フェードの順序を分け、黒い転換画面や未読込タイルを見せない。

### Xインベーダー
- `startLoop()` / `stopLoop()` で `requestAnimationFrame` の多重起動を防ぐ。
- 敵全滅後は `waveTransitioning` を立て、次ウェーブ生成が毎フレーム走らないようにする。
- 移動、弾、タイマーは `dt / 16.67` で補正する。
- 被弾時は短い無敵時間を入れ、同一フレームや連続弾でライフが一気に減らないようにする。
- `setTimeout` は `clearTimers()` に集約し、新規開始、メニュー、ゲームオーバーで消す。

### Xテトリス
- ピース固定後から次ピース出現までは `pieceLocked` で入力、落下、二重固定を止める。
- ライン消去や次ピース出現の timer は `setManagedTimeout()` に集約し、リセット時に `clearPendingTimers()` で消す。
- 複数ライン消去は削除対象行を `Set` にし、残行を再構成して空行を上に追加する。
- I ミノは横一列だけでなく縦向き回転も定義する。
- ライン消去アニメーションは固定ピースを消して `renderBoard()` した後に付ける。

### Xネコ / xneko
- npm パッケージを追加する場合は、存在確認とライセンス確認を先に行う。
- `oneko.gif` のような外部アセットは `NOTICE.md` に出典とライセンスを残す。
- `frontend_avatar/public/xneko_*.gif` は `256x128`、32px タイル 8 x 4 の透過スプライトシートとして扱う。
- 色違いを作る場合は、輪郭と透明部分を維持して色だけ置換する方が `background-position` とズレにくい。
- 白背景画像から透過GIFを作る場合は四隅フラッドフィルで背景を除去する。

## 注意点
- `public` 配下の日本語ディレクトリは Vite で配信できるが、URL エンコードされたパスでも取得できることを確認する。
- Vue 側の新規コンポーネントタグは日本語タグで直接書かず、ルート lazy import や `<component :is="...">` を使う。
- Vue 直実装で確実に表示したい画像は `src/assets` へ置いて import する。`public` の日本語パスや base URL の影響を受けにくい。
- 静的HTMLを別タブで直接開く導線は認証ガードを通らない。認証済みメニューからの実験導線として扱う。
- `npm run build` は指示なしに実行しない。通常確認は type-check、静的JS構文確認、Vite 経由の描画確認に留める。

## 確認方法

```powershell
cd frontend_web
npm run type-check
node --check .\public\<画面名>\index.js
Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8090/<URLエンコード済み画面名>/index.html'
Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8090/Xその他/<画面名>/ゲーム'
```

- Vue 直実装の場合は `node --check` 対象がないため、`npm run type-check` を優先する。
- DevTools が使える場合は Console エラー、Network 404、描画サイズ、操作系イベントを確認する。
