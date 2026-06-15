# X系ニュース型掛け合いビデオ

> 文書: `frontend_web,X系ニュース型掛け合いビデオ.md` | 実装: `frontend_web/public/Xビデオ/ニュース_20260519_anthropic2026前半/index.html`, `frontend_web/public/Xビデオ/ニュース_20260519_anthropic2026前半/scenario.js`, `frontend_web/public/Xビデオ/ニュース_20260519_anthropic2026前半/_gen_dialogue_audio.py`

## このメモを使う場面

- ニュース解説型ビデオを新規作成・改版するとき
- 掛け合い（female/male 2アバター）プレイヤーの仕様を確認するとき
- 音声ファイルを追加・再生成するとき
- 紹介ビデオとニュース型ビデオの違いを確認するとき

---

## 紹介ビデオ vs ニュース型ビデオ：種別の違い

| 項目 | 紹介ビデオ（AiDiy紹介_\*） | ニュース型（ニュース_\*） |
|------|---------------------------|--------------------------|
| 音声 | **edge:female のみ** | **edge:female + edge:male の掛け合い** |
| アバター | 1体（VRM_AiDiy.vrm） | 2体（VRM_female.vrm 左, VRM_male.vrm 右） |
| 1シーン当たりの音声 | **1音声**（short_audio / long_audio） | **複数ターン**（dialogue 配列） |
| short/long モード | あり | **なし** |
| 字幕 | なし（ナレーションは iframe 内） | あり（subtitle フィールド優先） |
| ページ構成 | scene_NNN.html（iframe 読み込み） | 単一 index.html（シーン内容をスクリプトで描画） |

→ 紹介ビデオの詳細は [`frontend_web,X系紹介ビデオとアバター作成手順.md`](./frontend_web,X系紹介ビデオとアバター作成手順.md) を参照。

---

## scenario.js の構造（ニュース型）

```javascript
window.SCENARIO = {
  "version": "duo-v2",
  "assets_policy": {
    "male_avatar": "../vrm/VRM_male.vrm",
    "female_avatar": "../vrm/VRM_female.vrm",
    "tts_male": "edge:male",
    "tts_female": "edge:female"
  },
  "scenes": [
    {
      "id": "scene_001",
      "kicker": "JANUARY 2026",           // 月表示バッジ
      "headline": "見出し\n2行目",
      "accent": "#ff6b35",                // テーマカラー
      "image": "images/scene_001.png",
      "dialogue": [
        {
          "speaker": "female",            // "female" or "male"
          "subtitle": "字幕に出る短文",   // 画面表示用（短い要約）
          "text": "実際に読み上げる全文。音声ファイルの内容と一致させる。",
          "audio": "audio/dlg_001_01_female.mp3",
          "duration_sec": 8.5
        },
        {
          "speaker": "male",
          "subtitle": "相手の短い要約",
          "text": "男性側の発話テキスト。",
          "audio": "audio/dlg_001_02_male.mp3",
          "duration_sec": 9.0
        }
        // ... 1シーン 8〜10 ターン程度
      ],
      "duration_sec": 84.0               // シーン内 dialogue の合計
    }
  ],
  "total_duration_sec": 693.0
};
```

### フィールドの使い分け

| フィールド | 用途 |
|-----------|------|
| `subtitle` | 字幕ボックスに表示する短文（1〜2 文、40〜50 字程度）。`text` より短くまとめる |
| `text` | 音声に読み上げる全文。`_gen_dialogue_audio.py` の DIALOGUES と一致させる |
| `audio` | 音声ファイルパス（相対）。命名規則: `dlg_{scene}_{turn:02d}_{speaker}.mp3` |
| `duration_sec` | TTS 生成後の実尺（秒）。プレーヤーの保険タイマーに使う |

---

## 冒頭ナレーション

- ニュース版では、記事・ニュース内容を案内した直後に「このニュース解説動画は AiDiy のニュース版ビデオ生成機能で作られています」と明言する。
- この文は `scene_000` の最初の発話へ入れ、字幕用の `telop_text` にも短く反映する。
- 既存動画の文面を変更した場合は、該当 `audio/dlg_000_01_female.mp3` を再生成し、`duration_sec`、シーン合計、`total_duration_sec` を実尺へ更新する。

---

## 音声ファイル命名規則

```
audio/dlg_{scene}_{turn:02d}_{speaker}.mp3

例:
  dlg_000_01_female.mp3   ← scene_000 / ターン01 / female
  dlg_001_06_male.mp3     ← scene_001 / ターン06 / male
  dlg_999_09_female.mp3   ← scene_999 / ターン09 / female
```

- ターン番号は 2 桁ゼロパディング（`01`〜`10` など）
- female → `ja-JP-NanamiNeural`（Edge TTS）
- male → `ja-JP-KeitaNeural`（Edge TTS）

---

## 音声生成スクリプト（`_gen_dialogue_audio.py`）

各ビデオフォルダに置く Python スクリプト。既存ファイル（500 bytes 超）は自動スキップ。

```python
# DIALOGUES リスト: (scene, turn, speaker, text)
DIALOGUES = [
    ("001",  1, "female", "読み上げテキスト"),
    ("001",  2, "male",   "読み上げテキスト"),
    ...
]

# 実行（backend_tools の .venv を使う）
# & "D:\OneDrive\_sandbox\AiDiy2026\backend_tools\.venv\Scripts\python.exe" "_gen_dialogue_audio.py"
```

- `sys.path.insert(0, r"D:\...\backend_tools")` して `tools_proc.text_to_speech.TextToSpeech` を使用
- `tts.synthesize(speech_text=text, language="ja", provider="edge", voice=speaker)` のように `ratio` は省略する
- ニュース版の再生スピードは `ratio` 指定なし、または `ratio=None` で収録する。現時点の標準速度は 1.2 倍。
- `aidiy_text_to_speech` は `ratio=None`（未指定）を既定の 1.2 倍として扱う。`ratio=0` / `ratio=1` は速度調整なしになるため、ニュース版の通常収録では指定しない
- `voice="female"` → NanamiNeural、`voice="male"` → KeitaNeural
- システム Python では `edge_tts` モジュールがないため、**必ず `backend_tools/.venv` の Python を使う**
- MCP クライアントが不要な場合は HTTP POST でも同等の処理を呼び出せる。
  ```
  POST http://localhost:8095/aidiy_text_to_speech/synthesize
  Body: { "text": "読み上げテキスト", "provider": "edge", "voice": "female",
          "save_path": "D:/.../audio/dlg_001_01_female.mp3" }
  Response: audio/mpeg バイナリ（save_path 指定時はファイルにも同時保存）
  ```

---

## プレイヤー（index.html）の主要仕様

### 2アバター配置

```
左端固定: VRM_male.vrm   → bodyYaw = Math.PI + Math.PI/6 (30°内側向き)
右端固定: VRM_female.vrm → bodyYaw = Math.PI - Math.PI/6 (30°内側向き)
```

- 固定表示（ページスクロールに追従しない `position: fixed`）
- 幅: `36vh`、高さ: `calc(100vh - 146px)`

### 話者切替と暗転

```javascript
// 話者アバターを明るく、非話者アバターを暗転
.avatar-wrap.silent { filter: brightness(0.58) saturate(0.45); }
// opacity は変えない（透過禁止）
```

### ステレオパン

```javascript
// Web Audio API StereoPannerNode
pannerNode.pan.value = speaker === "male" ? -1.0 : 1.0;
// male → 左チャンネル (-1.0)
// female → 右チャンネル (+1.0)
```

### リップシンク

- `AnalyserNode` でマイクレベルを取得し、話者の VRM に `aa` 表情を適用
- 非話者は `lipsyncActive = false` → `mouthSmooth = 0`（即時クローズ）
- 両アバターが共有 `window._analyserNode` を読むが、自分の `lipsyncActive` フラグで適用可否を制御

### 字幕表示

```javascript
// subtitle フィールドを優先、なければ text にフォールバック
subtitleText.textContent = turn.subtitle || turn.text || "";
```

### アバター表情

- `expression` フィールドに何が入っていても常に `"neutral"` で固定
- `window.__maleSetExpression?.("neutral")` / `window.__femaleSetExpression?.("neutral")`

---

## VRM ファイル

ニュース型ビデオは `Xビデオ/vrm/` の共有 VRM を相対パスで参照する（自己完結不要）。

```javascript
// scenario.js の assets_policy
"male_avatar":   "../vrm/VRM_male.vrm",
"female_avatar": "../vrm/VRM_female.vrm"
```

紹介ビデオとは異なり、ニュース型は `vrm/` サブフォルダへの複製不要。

---

## 新しいニュース型ビデオを作る手順

1. `Xビデオ/ニュース_<テーマ>/` フォルダを作成
2. 既存の `ニュース_20260519_anthropic2026前半/` を手本として以下をコピー・修正:
   - `index.html` — プレイヤー本体（ほぼそのまま使える）
   - `scenario.js` — シーン・ダイアログ定義を書き直す
   - `_gen_dialogue_audio.py` — DIALOGUES リストを書き直す
3. `images/` フォルダを作成し、各シーンの背景画像を配置
4. `audio/` フォルダを作成
5. `backend_tools/.venv` の Python で `_gen_dialogue_audio.py` を実行して音声生成
6. `Xビデオ.vue` にメニューカードを追加
7. ブラウザで動作確認（字幕・口パク・暗転切替・ステレオパン）

---

## よくある間違い

| 間違い | 正しい対処 |
|--------|-----------|
| システム Python で `_gen_dialogue_audio.py` を実行する | `backend_tools/.venv/Scripts/python.exe` を使う（`edge_tts` がここにある） |
| `text` と `subtitle` を同じにする | `subtitle` は短い要約（表示用）、`text` は全文（音声用）で分ける |
| 非話者アバターを `opacity` で透かす | `filter: brightness(0.58) saturate(0.45)` のみ使う（opacity は変えない） |
| VRM の向きが外側を向く | left アバターは `Math.PI + Math.PI/6`、right は `Math.PI - Math.PI/6` が内向き |
| `expression` に "happy" などを入れる | ニュース型は常に `"neutral"` 固定。フィールド値は無視される |
| 既存音声を再生成してしまう | スクリプトのスキップ条件（500 bytes 超）で保護されるが、明示的に確認すること |
