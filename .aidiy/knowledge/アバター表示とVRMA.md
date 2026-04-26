# アバター表示とVRMA再生

アバターの表示サイズ、向き、およびアニメーション再生の挙動を調整した際の知見を整理する。

## このメモを使う場面
- アバターが画面に対して大きすぎる（または小さすぎる）場合の調整
- アバターが初期状態で背中を向けている場合の修正
- VRMA アニメーションが 1 回で止まってしまい、連続して再生されない場合の対応

## 関連ファイル
- `frontend_avatar/src/components/AIコア.vue`（表示選択、アバターへの `controls-visible` 受け渡し）
- `frontend_avatar/src/components/AIコア_xeyes.vue`（Electron では OS カーソル位置、Web では画面内 pointermove を追う目線表示。CPU 使用率で血走り演出も行う）
- `frontend_avatar/src/components/AIコア_アバター.vue`（Electron/Web アバターコンポーネント、実験的制御設定 UI）
- `frontend_avatar/src/components/AIコア_アナログ時計.vue`（表示選択用のアナログ時計）
- `frontend_avatar/src/components/AIコア_デジタル時計.vue`（表示選択用のデジタル時計）
- `frontend_avatar/src/components/AIコア_カレンダー.vue`（表示選択用のカレンダー）
- `frontend_avatar/electron/main.ts` / `frontend_avatar/electron/preload.ts` / `frontend_avatar/src/env.d.ts`（ウィンドウ role とカーソル位置、CPU 使用率を返す IPC）
- `frontend_web/public/X自己紹介/index.html`（静的HTMLページ内埋め込みアバター）

## 実装の結論

### 1. アバターの表示サイズ（カメラ距離）
アバターのサイズ自体を小さくするのではなく、カメラの引き距離（distance）を調整することで、相対的な表示サイズを制御します。
- **箇所**: `fitCamera` 関数内の `distance` 計算。
- **結論**: 距離倍率を `0.54` から `1.08` へ変更（倍増）することで、アバターの表示を約半分のサイズ（全身が見える程度）に調整。
- **コード例**:
  ```typescript
  const distance = Math.max(distanceForHeight, distanceForWidth) * padding * 1.08
  ```

### 2. アバターの向き（初期回転）
VRM モデルが読み込まれた際の初期の向きを調整します。
- **箇所**: `initScene` 内の `container.rotation.y`。
- **結論**: `Math.PI`（180度）になっていたものを `0` に変更し、正面を向くように修正。
- **コード例**:
  ```typescript
  const container = new THREE.Group()
  container.rotation.y = 0 // 正面向き
  ```

### 3. アニメーションの連続再生（ループ）
VRMA が終了した後に次のモーションへ移行、または繰り返す挙動を保証します。
- **仕様**: 単一ファイルのループ再生（`THREE.LoopRepeat`）ではなく、`finished` イベントをフックして次のモーションを選択・再生する方式を採用。
- **箇所**: `モーション終了時処理` および `VRMA再生実行`。
- **結論**: `vrma連続再生有効` が true の場合、終了イベントで再度 `VRMA再生開始` を呼び出し、キューから次のモーションを取得して再生を継続する。
- **注意**: 前回の作業ログでは `THREE.LoopRepeat` への変更が言及されていたが、最終的な実装は `finished` イベント経由の連続再生（巡回再生）となっている。これにより、待機モーションが固定されず、多様な動きをループさせることが可能。

### 4. 実験的アバター設定 UI
`不完全な自立身体制御` と `不完全な自動カメラワーク` は、`AIコア_アバター.vue` の内部 UI として右下へ配置する。
- **結論**: `表示選択` は `AIコア.vue` の左下、実験的制御設定は `AIコア_アバター.vue` の右下。
- **表示選択**: `アバター` / `xneko(猫)` / `無し` の select で切り替える。
- **表示選択の拡張**: `アナログ時計` / `デジタル時計` / `カレンダー` は、`AIコア.vue` で import し、`表示選択型` と select option と表示用 computed を合わせて追加する。
- **xeyes の追加**: `xeyes(目)` も同じ表示選択パターンで追加する。Electron 実行中は renderer だけではウィンドウ外のマウス位置を取れないため、`window:get-pointer-snapshot` IPC で `role` / `bounds` / `mouse` / `insideWindow` を返し、`bounds + stageRect` からローカル座標へ変換する。
- **CPU 血走り演出**: Electron main process 側で `os.cpus()` の前回差分から CPU 使用率を返す `system:get-cpu-usage` IPC を用意し、`AIコア_xeyes.vue` 側で 1 秒ごとに取得する。直近 10 サンプル平均を使い、20% 以下は白、80% 以上は最大血走り、間は `(平均 - 20) / 60` で線色と白目の赤みを連続変化させる。
- **CPU グラフ**: `controls-visible` が true のときだけ、目の下に直近 10 秒分の CPU 使用率棒グラフと平均値を表示する。
- **表示条件**: `表示選択` が `アバター` 以外の場合は `AIコア_アバター.vue` 自体を表示しないため、実験的制御設定も表示しない。
- **ボタン非表示時**: `AIコア.vue` から `controls-visible` を渡し、false の間は `AIコア_アバター.vue` 内の設定 UI・字幕・発光を隠してアバター本体だけにする。
- **注意**: ネコ表示中や `無し` 選択中にアバター固有設定が見えると UI 上の意味が曖昧になるため、アバターコンポーネント内へ閉じ込める。

### 5. xeyes オプションパネル（2026-04-26 追記）

右下に `controls-visible=true` のときのみ表示される半透明パネルを追加。

- **デザイン切替**（通常 / シンプル）: `designMode` ref で管理。シンプルモードは透明背景＋20px白輪郭線＋白瞳のプレーンな目。血走りラインと通常のグラデ・ハイライトは `<template v-if="designMode==='normal'">` で出し分け（`v-if`+`v-for` を同一要素に書かず `<template v-if>` でラップする点に注意）。
- **CPU使用率色変化**（チェックボックス）: `cpuColorEnabled` ref で管理。オフ時は `effectiveCpuColorLevel` / `effectiveBloodshotLineLevel` が常に 0 を返し、目の色変化と血走りを無効化。
- **シンプルモードの色変化**: CSS カスタムプロパティ `--cpu-color-level`（`.xeyes-wrap` に設定済み）を子要素で継承し、`rgb(255, calc(255-(255*var(--cpu-color-level))), calc(255-(255*var(--cpu-color-level))))` で白→赤に変化。

### 6. xneko デザイン切替（2026-04-26 追記）

右下オプションパネルに oneko / 茶トラ / 三毛 のラジオボタンを追加。

- **状態**: `nekoDesign` ref（`'oneko' | 'chatora' | 'mike'`）
- **画像切替**: `nekoImageUrl` computed が GIF パスを返し、`.neko-sprite` の `background-image` に `:style` でバインド。CSS の静的 `background-image: url('/oneko.gif')` は削除済み。
- **GIF ファイル生成**: `public/xneko_chatora.gif` / `public/xneko_mike.gif` は元画像（PNG・白背景）を Python + Pillow で変換。白背景は四隅フラッドフィルで除去し、1024×512 → 256×128 にリサイズ後、パレットインデックス 255 を透過色として GIF 保存。三毛猫は白い毛を持つため単純な閾値除去ではなくフラッドフィル方式を採用した。

## 再発しやすい注意点
- **カメラワークとの干渉**: `fitCamera` で計算した距離は、自動カメラワーク（`AIコア_自動カメラワーク.ts`）の基準値として利用されるため、ここを極端に変えると回転半径などにも影響する。
- **モーション補間**: 連続再生時、`action.crossFadeFrom` を適切に設定しないと、モーションの切り替わりでモデルが瞬時に初期姿勢に戻る（ガクつく）現象が発生する。
- **BOM付きファイル**: `VRMA` ファイルや設定 JSON が BOM 付き UTF-8 だと、一部の環境で読み込みエラーになる可能性がある。
- **Electron の目線制御**: `mousemove` は BrowserWindow 内に入ったときしか取れない。常駐ウィンドウ外のカーソルを追う表示は、Electron main process 側で `screen.getCursorScreenPoint()` と対象 `BrowserWindow.getBounds()` を返す IPC を追加する。
- **CPU 使用率の初回値**: `os.cpus()` は前回サンプルとの差分で使用率を出すため、初回は 0% になり得る。1 秒後以降の値を直近 10 秒平均に入れて演出する。

## 静的HTMLページ（X自己紹介/index.html）での調整

静的HTMLページ内に Three.js + VRM を直接埋め込む場合は、Vue コンポーネントとは別の調整箇所がある。

### サイズ調整
- **箇所**: CSS の `#avatar-container` の `width` / `height` と、`getStageSize()` → `renderer.setSize(..., false)` によるキャンバス追従
- **結論**: CSS コンテナを `200px × 340px` へ半減し、レンダラーは `clientWidth/clientHeight` を読む方式にして見た目と描画サイズをずらさない。必要ならモバイル用 media query も合わせて入れる。

### 向き調整
- **箇所**: `camera.position.set(...)` と `camera.lookAt(...)`
- **結論**: `frontend_avatar` と同じく、カメラを `-Z` 側に置いて正面を見る構成に寄せる。静的HTML側で無理に `container.rotation.y` を回して合わせるより、カメラ位置を本体実装に合わせた方が向きの差異が出にくい。

### ループ再生
- **箇所**: `playNext()` / `setTimeout()` / `action.crossFadeFrom(...)`
- **結論**: 静的HTML側では `LoopOnce` で 1 本ずつ再生し、`clip.duration - XFADE` を基準に次クリップを予約して巡回再生させる。これで 1 本目の終了後に止まらず、複数 VRMA を切り替え続けられる。

### コード例（静的HTML向け）
```javascript
const getStageSize = () => ({
  width: Math.max(1, avatarContainer?.clientWidth || 200),
  height: Math.max(1, avatarContainer?.clientHeight || 340),
});
renderer.setSize(getStageSize().width, getStageSize().height, false);

camera.position.set(0, h * 0.78, -h * 1.05);
camera.lookAt(0, h * 0.78, 0);

const action = mixer.clipAction(clip);
action.reset();
action.setLoop(THREE.LoopOnce, 1);
action.clampWhenFinished = false;
action.play();
nextClipTimer = window.setTimeout(playNext, Math.max(250, (clip.duration - XFADE) * 1000));
```

## 最低限の確認方法
1. アバター起動時に全身が適切に収まっているか（大きすぎないか）を確認。
2. アバターが最初からこちら（カメラ）を向いているかを確認。
3. モーションが終了した際、止まらずに次のモーション（または同じモーションの再開）が始まるかを確認。
4. `表示選択` を `xneko(猫)` または `無し` にしたとき、実験的制御設定が表示されないかを確認。
5. ボタン非表示時に `AIコア_アバター.vue` 内の設定 UI・字幕・発光が消え、アバター本体だけになるかを確認。
6. `表示選択` で `アナログ時計` / `デジタル時計` / `カレンダー` を選び、各表示が画面中央に出るかを確認。
7. `表示選択` で `xeyes(目)` を選び、Electron ではウィンドウ外のマウスにも目線が追従し、Web では画面内の pointermove に追従するかを確認。
8. Electron で `xeyes(目)` 選択中、CPU 平均が上がると目が徐々に赤くなり、ボタン表示中だけ目の下に CPU グラフが出るか確認。
9. 静的HTMLの場合は、ブラウザのリロードで即時反映されるか確認。
