# X系紹介ビデオとアバター作成手順

> 文書: `frontend_web,X系紹介ビデオとアバター作成手順.md` | 実装: `frontend_web/public/X自己紹介/AiDiy紹介ビデオtake4/`, `frontend_web/public/X自己紹介/AiDiy紹介アバター/`

## このメモを使う場面

- 新しい紹介ビデオ（take N）を作成するとき
- アバター版プレゼンターを新しく作成・改版するとき
- シーンの追加・修正をするとき
- index.html の `sceneFrame.src` 参照方式を確認したとき

---

## ディレクトリ構造

### 紹介ビデオ（take）

```
X自己紹介/AiDiy紹介ビデオtakeN/
  index.html        プレイヤー（iframe + 音声制御）
  scenario.js       window.SCENARIO 定義（scenes 配列）
  scene.css         全シーン共通スタイル
  scene.html        旧クエリパラメータ方式の残骸（使用しない）
  scene_000.html    ヒーローシーン（個別ページ）
  scene_001.html    …
  scene_NNN.html    各シーン（個別ページ）
  scene_999.html    エンディングヒーロー（個別ページ）
  images/           MCP 画像生成で作成した scene_NNN.png
  audio/            MCP TTS で作成した scene_NNN.mp3
```

### アバター版

```
X自己紹介/AiDiy紹介アバター/
  index.html        プレイヤー（VRM アバター左 38% + iframe 右 62%）
  scenario.js       take4 の音声・画像を ../AiDiy紹介ビデオtake4/ で参照
  scene.css         take4 から流用（変更なし）
  scene_000.html    …
  scene_NNN.html    各シーン（個別ページ）
  aidiy_sozai/      アバター関連素材のみ（下記ルール参照）
```

---

## 重要ルール：シーンはページ単位（個別 HTML）

`index.html` の `sceneFrame.src` は **`scene.id + ".html"`** で読み込む。
クエリパラメータ方式（`scene.html?n=N`）は使用しない。

```javascript
// ✅ 正しい
sceneFrame.src = scene.id + ".html";   // → "scene_001.html"

// ❌ 古い方式（使ってはいけない）
sceneFrame.src = `scene.html?n=${sceneIndex + 1}`;
```

各 `scene_NNN.html` は完全な HTML ファイルとして個別に作成する。
`scene.css` を `<link rel="stylesheet" href="scene.css">` で読み込む。

---

## scenario.js の構造

```javascript
window.SCENARIO = {
  "project_name": "...",
  "version": "take4",          // "avatar" の場合もある
  "assets_policy": {
    "audio_dir": "audio",      // アバター版は "../AiDiy紹介ビデオtake4/audio"
    "image_dir": "images",     // アバター版は "../AiDiy紹介ビデオtake4/images"
    "avatar": "../AiDiy_Sample_M.vrm"  // アバター版のみ
  },
  "scenes": [
    {
      "id": "scene_000",       // HTML ファイル名と一致させる
      "start_sec": 0.0,
      "duration_sec": 11.616,
      "expression": "neutral", // アバター表情
      "accent": "#29d8ff",     // CSS --accent に適用
      "layout": "hero",        // hero の場合は stage-hero クラス
      "hero_image_focus": true,
      "audio": "audio/scene_000.mp3",  // フルパスか相対パス
      "image": "images/scene_000.png",
      // ... chips / metrics / cards / facts / evidence
    }
  ],
  "duration_sec": 90.912       // 全シーン合計
}
```

---

## シーン HTML の構造

### 通常シーン（左ビジュアル + 右コンテンツ）

```html
<div id="stage" class="stage fade-enter"
     style="--accent:#29d8ff;--accent-soft:rgba(41,216,255,0.18);">
  <section class="visual-panel">
    <div class="visual-meta">
      <div class="kicker">KICKER TEXT</div>
      <div class="scene-id">scene_001 / 2 of 10</div>
    </div>
    <div class="image-shell">
      <img class="scene-image" src="images/scene_001.png" ...>
      <div class="image-placeholder">画像を読み込み中...</div>
      <div class="image-overlay">
        <div class="image-overlay-copy">
          <div class="image-title">タイトル</div>
          <p class="image-subtitle">サブタイトル</p>
        </div>
      </div>
    </div>
  </section>
  <section class="content-panel">
    <div class="content-scroll">
      <!-- header-row / chip-row / metric-row / card-grid / detail-grid -->
    </div>
  </section>
</div>
```

### ヒーローシーン（scene_000 / scene_999）

```html
<div id="stage" class="stage stage-hero stage-hero-focus fade-enter"
     style="--accent:#29d8ff;--accent-soft:rgba(41,216,255,0.18);">
  <div class="hero-image-wrap">
    <img class="hero-image" src="images/scene_000.png" ...>
  </div>
  <div class="hero-overlay">
    <div class="hero-kicker">KICKER</div>
    <h1 class="hero-title">タイトル</h1>
    <div class="hero-headline">
      <span class="headline-line">...</span>
    </div>
    <p class="hero-lead">リード文</p>
    <div class="hero-meta">scene_000 / 1 of 10</div>
  </div>
</div>
```

---

## アバター版固有のルール

### VRM アバター統合

- `index.html` の左パネル（38%）に Three.js + `@pixiv/three-vrm` でレンダリング
- VRM ファイル: `../AiDiy_Sample_M.vrm`（アバター版フォルダからの相対パス）
- リップシンク: `window.audioPlayer`（`<audio>` タグ）の AudioContext + AnalyserNode で `aa` 表情を駆動
- `window.__avatarSetExpression?.(scene.expression || "neutral")` でシーン切替時に表情を設定

### 音声・画像の参照先

アバター版は既存 take の音声・画像を再利用する。パスは相対で指定する:

```javascript
"audio": "../AiDiy紹介ビデオtake4/audio/scene_001.mp3"
"image": "../AiDiy紹介ビデオtake4/images/scene_001.png"
```

### aidiy_sozai の使用範囲

`aidiy_sozai/` フォルダはアバター関連の素材のみ使用する。業務画面スクリーンショット（配車管理、生産計画など）は使わない。

| 使う素材 | 用途 |
|---------|------|
| `aidiy_sozai/アイディ.png` | hero シーン（scene_000、scene_999） |
| `aidiy_sozai/frontend_avatar_webモード.png` | scene_005 AIコアとアバターの Web モード説明 |
| `aidiy_sozai/frontend_avator_desktopモード.png` | scene_005 AIコアとアバターの Desktop モード説明 |

上記以外のシーンでは take の `images/scene_NNN.png` を使う。

---

## 新 take 作成の流れ

1. `AiDiy紹介ビデオtakeN/` フォルダを作成
2. `scenario.js` を定義（scenes 配列、audio/image パス）
3. `scene.css` を既存 take からコピー
4. `index.html` を既存 take からコピーし、`sceneFrame.src = scene.id + ".html"` を確認
5. MCP（TTS / 画像生成）で `audio/` と `images/` を生成
6. 各 `scene_NNN.html` を個別に作成（ヒーローは hero 構造、それ以外は visual+content 構造）
7. `assets.json` / `scenario.json` は自動生成または省略可

## アバター版作成の流れ

1. `AiDiy紹介アバター/` フォルダを作成
2. ベースにする take を決め、`scenario.js` でその音声・画像を参照
3. `scene.css` を take からコピー
4. `index.html` を VRM 統合版として作成（左 38% アバター、右 62% iframe）
5. 各 `scene_NNN.html` を個別に作成（avatar 版でも構造は take と同じ）
6. hero シーンと scene_005（アバター説明）だけ `aidiy_sozai/` の画像を使う

---

## よくある間違い

| 間違い | 正しい対処 |
|--------|-----------|
| `scene.html?n=N` で切り替えようとする | `scene.id + ".html"` で個別ファイルを参照する |
| アバター版で全シーンに aidiy_sozai 画像を使う | アバター関連（アイディ、web/desktop モード）のみ使い、他は take の images を使う |
| 通常シーンに `stage-hero` を付ける | `stage-hero` / `stage-hero-focus` はヒーローシーン（000, 999）のみ |
| アバター版で音声を独自生成しようとする | 既存 take の `audio/` を相対パスで参照する |
