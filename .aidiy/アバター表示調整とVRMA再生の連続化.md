# アバター表示調整とVRMA再生の連続化

アバターの表示サイズ、向き、およびアニメーション再生の挙動を調整した際の知見を整理します。

## 場面
- アバターが画面に対して大きすぎる（または小さすぎる）場合の調整
- アバターが初期状態で背中を向けている場合の修正
- VRMA アニメーションが 1 回で止まってしまい、連続して再生されない場合の対応

## 関連ファイル
- `frontend_avatar/src/components/AIコア_アバター.vue`（Electron/Web アバターコンポーネント）
- `frontend_web/public/X自己紹介/index.html`（静的HTMLページ内埋め込みアバター）

## 調整内容と実装の結論

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

## 再発しやすい注意点
- **カメラワークとの干渉**: `fitCamera` で計算した距離は、自動カメラワーク（`AIコア_自動カメラワーク.ts`）の基準値として利用されるため、ここを極端に変えると回転半径などにも影響する。
- **モーション補間**: 連続再生時、`action.crossFadeFrom` を適切に設定しないと、モーションの切り替わりでモデルが瞬時に初期姿勢に戻る（ガクつく）現象が発生する。
- **BOM付きファイル**: `VRMA` ファイルや設定 JSON が BOM 付き UTF-8 だと、一部の環境で読み込みエラーになる可能性がある（今回の修正範囲ではないが、過去の知見として留意）。

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
4. 静的HTMLの場合は、ブラウザのリロードで即時反映されるか確認。
