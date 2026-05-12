# MCP 利用による自動ビデオ生成手順

> 文書: `共通,mcp利用による自動ビデオ生成手順.md` | 実装: `backend_mcp/mcp_proc/text_to_speech.py`, `backend_mcp/mcp_proc/ffmpeg_control.py`, `backend_mcp/mcp_proc/obs_studio_control.py`, `backend_mcp/mcp_proc/chrome_devtools.py`, `scripts/cdp_user_gesture.py`, `backend_server/_config/aidiy_text_to_speech.json`

## このメモを使う場面

- AiDiy 自身に紹介・解説動画を自動生成させたい
- 「シナリオ JSON → 音声付き HTML → 画面録画 → MP4 トリム」までを既存 MCP だけで通したい
- ブラウザの autoplay ポリシーで `Audio.play()` が拒否される、OBS の `StartRecord` が反映されないなど、本手順で踏んだ落とし穴を再発させたくない

## 生成サンプル（実例）

最小成功例の成果物一式は次のフォルダにそのまま残してある。台本・音声・HTML・MP4 トリム後ファイルの粒度感、命名、`scenario.json` / `assets.json` の項目をそのまま流用できる。

```
frontend_web/public/X自己紹介/AiDiy自己紹介ビデオtake1/
├─ scenario.json    # 10シーン構成、合計 146.27 秒
├─ script.md        # 人間確認用台本
├─ assets.json      # 画像/音声の生成状態と発音置換ログ
├─ index.html       # 音声付き自動再生 HTML（MP3 ベース）
├─ audio/scene_001.mp3 〜 scene_010.mp3
└─ aidiy_intro_take1_trim.mp4 など
```

元 OBS 録画は `C:/Users/admin/Videos/<日時>.mp4`、トリム済み MP4 は同じ Videos フォルダか上記サンプルフォルダに置く。

## 全体フロー

```
[scenario.json] ─┐
                 ├─► [audio/scene_NNN.mp3] (TTS MCP)
[index.html]  ─┐ │
               ▼ ▼
   [Chrome 表示 + MP3 再生]  ──► [画面録画 MP4] (OBS MCP)
                                              │
                                              ▼
                                    [トリム済み MP4] (ffmpeg MCP)
```

| 段階 | 使う MCP（13機能のうち） | 役割 |
|------|--------------------------|------|
| 1. 台本生成 | （AI コア） | `scenario.json` / `script.md` を作る |
| 2. 音声合成 | `aidiy_text_to_speech` | `audio/scene_*.mp3` を出力。発音辞書経由 |
| 3. 尺確定 | `aidiy_ffmpeg_control` (`ffprobe_run`) | 各 MP3 の `duration` を取得し HTML/JSON へ反映 |
| 4. ブラウザ自動再生 | `aidiy_chrome_devtools` + `scripts/cdp_user_gesture.py` | HTML を開き、ユーザー操作扱いで `play()` 起動 |
| 5. 録画 | `aidiy_obs_studio_control` | OBS で画面 + システム音声を一括録画 |
| 6. 撮影中の人間ガイド | `aidiy_text_to_speech` (`local_play:true`) | 最前面化・手動録画開始など GUI 操作を音声で依頼、合図ワードで同期 |
| 7. トリム / 整形 | `aidiy_ffmpeg_control` (`ffmpeg_run`) | 前後の余白カット、再エンコード |

## 1. シナリオと HTML の構造

`scenario.json` は 1 シーン = 1 MP3 = 1 表示単位。`start_sec` / `duration_sec` は **生成後に MP3 実尺で再計算する**。HTML には `<audio>` を DOM に配置せず `new Audio()` をスクリプト保持し、シーン進行は次の二重トリガで保証する。

- `audioPlayer.addEventListener("ended", …)` — 主タイマー
- `setTimeout(advanceFromScene, (duration_sec + 0.8) * 1000)` — 保険タイマー（`ended` を取りこぼした場合）

`?scene=N` クエリで任意シーンから検証起動できるようにしておく（狭いビューポート時の表示崩れを 1 シーンずつ確認できる）。

### HTML の分割構成（iframe 方式）

シーンが増えると `index.html` 1 ファイルに全シーン HTML を埋め込むと肥大化するため、**iframe 分割**を推奨する。

```
takex/
├── index.html          # プレイヤー本体。シーン切替で iframe の src を差し替える
├── scenario.js         # scenario.json をJSとして export（index.html から参照）
├── scene.css           # 全シーン共通スタイル
├── scene_001.html      # 各シーン個別 HTML（シンプルに保つ）
├── scene_002.html
├── ...
├── audio/scene_001.mp3 〜
└── images/scene_001.png 〜
```

`index.html` 側のシーン切替:

```js
sceneFrame.src = `scene_${String(sceneIndex + 1).padStart(3, "0")}.html`;
```

各 `scene_NNN.html` のひな型（共通 CSS を link するだけ）:

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>シーンタイトル</title>
  <link rel="stylesheet" href="scene.css">
</head>
<body>
  <div class="stage fade-in">
    <section class="visual">
      <img class="bg-img" src="images/scene_NNN.png" alt=""
           onload="this.classList.add('loaded')">
    </section>
    <div class="overlay">
      <p class="overlay-title">シーンタイトル</p>
      <p class="overlay-narration">ナレーション本文</p>
    </div>
  </div>
</body>
</html>
```

Python で一括生成するのが効率的:

```python
import os, json

base = r"D:/.../takex"
with open(f"{base}/scenario.json", encoding="utf-8") as f:
    sc = json.load(f)

TMPL = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <link rel="stylesheet" href="scene.css">
</head>
<body>
  <div class="stage fade-in">
    <section class="visual">
      <img class="bg-img" src="{image}" alt="" onload="this.classList.add('loaded')">
    </section>
    <div class="overlay">
      <p class="overlay-title">{title}</p>
      <p class="overlay-narration">{narration}</p>
    </div>
  </div>
</body>
</html>
"""

for scene in sc["scenes"]:
    html = TMPL.format(
        title=scene["title"],
        image=scene.get("image", f'images/{scene["id"]}.png'),
        narration=scene.get("narration", ""),
    )
    with open(f"{base}/{scene['id']}.html", "w", encoding="utf-8") as f:
        f.write(html)
```

### scene.css レイアウトパターン

**フルスクリーン画像 + フローティングテキストパネル** が基本レイアウト。

```css
.stage  { position: relative; width: 100%; height: 100%; }
.visual { width: 100%; height: 100%; overflow: hidden; background: #060c16; }
.bg-img {
  width: 100%; height: 100%;
  object-fit: contain;          /* ← contain で見切れ防止。左右に黒余白が入る */
  object-position: center center;
  opacity: 0; transition: opacity 400ms ease; display: block;
}
.bg-img.loaded { opacity: 1; }
.overlay {
  position: absolute; left: 32px; bottom: 32px; max-width: 60%;
  padding: 16px 22px; border-radius: 10px;
  background: rgba(4,10,20,0.72); backdrop-filter: blur(10px);
  border: 1px solid rgba(160,220,255,0.2);
}
.overlay-title   { font-size: 18px; font-weight: 900; color: #9fe8ff; margin: 0 0 6px; }
.overlay-narration { font-size: 15px; line-height: 1.75; color: #dbe9f4; margin: 0; }
```

**`object-fit` の選び方:**

| 設定 | 効果 | 推奨ケース |
|------|------|------------|
| `contain` | 縦横比を保ち全体を表示。余白は背景色で埋まる | 生成画像（余白が出ても画像全体を見せたい） |
| `cover` | 枠全体を埋める。端が切れる | 写真・風景など切れてもよいもの |

生成画像 (1792×1024) を動画プレイヤー枠 (≒ 16:9) に表示するときは **`contain` 推奨**（`cover` だと左右が大きく見切れる）。

## 2. ナレーション生成（aidiy_text_to_speech）

```
mcp__aidiy_text_to_speech__synthesize_speech
  speech_text  : シーンのナレーション原文
  provider     : "edge"
  voice        : "ja-JP-NanamiNeural"
  save_path    : 絶対パス（例: D:/.../audio/scene_001.mp3）
```

- 発音辞書は **`backend_server/_config/aidiy_text_to_speech.json`** が単一の正本。`AiDiy → アイディー`, `MCP → エムシーピー`, `横展開 → よこてんかい` など。辞書を更新したら **必ず全シーンを取り直す**（シーン尺も変わる可能性あり）。
- レスポンスには base64 audio が含まれ、トークン上限を超えてエラー扱いに見えることがあるが、`save_path` を指定していればファイルは正常保存されている。`save_path` 指定時はレスポンス本文を読み返す必要はなく、**ファイルサイズと尺だけ確認**する。
- `local_play: true` を使えば、生成と同時に **MCP ホスト側のスピーカーで読み上げ**ができる。人間オペレーター向け案内（「Chrome を最前面にしてください」等）に使う。

## 3. 尺の確定（ffprobe）

`save_path` で固まった MP3 の実尺を `ffprobe_run` で取り、`scenario.json` / `assets.json` / `index.html` 内のシナリオに反映する。

```
mcp__aidiy_ffmpeg_control__ffprobe_run
  args_str: -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 D:/path/to/scene_001.mp3
```

落とし穴:

- **`args_str` の引用符**: 内部で空白スプリットされるため、Windows パスを `"…"` で囲むと `ffprobe` 側に `"…"` ごと渡って `Invalid argument` になる。**スペースを含まないパスにし、引用符は付けない**。スペース必須なら一時ファイル名にコピー (`aidiy_intro_take1.mp4` など) してから渡す。

`start_sec` は累積で再計算し、ルートの `duration_sec` も合計値で更新する。


## 目標尺の設定と尺調整ループ

### 目標尺の決め方

動画全体の目標秒数を最初に決め、シーンごとの配分も大まかに決めておく。

| 動画用途 | 推奨目標尺 |
|----------|------------|
| SNS / X 動画 | 60 秒以下（**余裕をもって 55 秒以下を目安**） |
| YouTube ショート | 60 秒以下 |
| 一般紹介動画 | 90〜120 秒 |

**余裕を 5 秒程度持たせる**（映像余白・録画前後のトリム誤差を吸収するため）。
例: 目標 60 秒 → ナレーション合計 55 秒以下を目指す。

### 尺調整ループ

音声合成後に合計尺が目標を超えた場合、以下の手順で調整する。

1. ffprobe で全シーンの実尺を取得し合計する
2. 目標秒数との差分を確認する
3. 長いシーン（差分が大きいもの）のナレーションを短縮して再合成する
4. 再び ffprobe で合計を確認する
5. 目標内に収まるまで繰り返す

**短縮のコツ:**

- 「でも中身は本格設計です」→「本格設計です」のように末尾の言い換えを削る
- 「〜に〜、〜に〜、〜に〜」の列挙を 2〜3 項目に絞る
- 「〜することができます」→「〜できます」などの短縮形を使う
- 1 シーンで 2〜3 秒削れば複数シーン不要になることが多い

**scenario.json の narration も同時に更新する**（音声ファイルとの乖離防止）。

### 尺確定後の一括更新

全シーンの尺が確定したら Python でまとめて反映する。

```python
durations = [6.12, 8.28, 9.14, ...]  # ffprobe の実測値
starts = []
s = 0.0
for d in durations:
    starts.append(round(s, 3))
    s += d
total = round(s, 3)  # 合計が目標以下か確認

# scenario.json の start_sec / duration_sec / narration を更新
# assets.json の audio[].duration_sec / bytes を更新
```


## 画像生成（aidiy_image_generation）

各シーンの `image_prompt` をもとに PNG を生成する。

### 推奨設定

| 設定 | 推奨値 | 備考 |
|------|--------|------|
| provider | openai | 品質・安定性のバランスが良い |
| model | gpt-image-2 | 現時点の最新 |
| size | 1792x1024 | 16:9 横長（動画向け） |
| quality | medium | コスト削減しつつ十分な品質 |
| save_path | images/scene_001.png〜 | PNG 拡張子で自動保存 |

### ツール呼び出し例

```
mcp__aidiy_image_generation__generate_image
  prompt: <image_prompt の内容>
  provider: openai
  model: gpt-image-2
  size: 1792x1024
  quality: medium
  save_path: D:/path/to/images/scene_001.png
```

### 注意点

- `save_path` 先が存在しない場合はエラーになるため、事前に `os.makedirs()` で作成する
- 1 枚あたり 10〜30 秒かかるため、シーン数が多い場合は **逐次実行**（並列不可）
- `save_path` に既存ファイルがあると上書きされる
- 生成完了後に `assets.json` の `images[].status` を `"generated"` に更新する

## 4. ブラウザ自動再生（autoplay 回避）

`aidiy_chrome_devtools` の `click` / `eval_js` から `play()` を呼ぶと、Chrome の autoplay ポリシーで `audioPlayer.play()` が拒否され、`.catch` 経由で `pause()` が走り、ボタンが「再生」のまま止まる（`audioSrc` はセットされるが `audioPaused: true`）。

**対処**: CDP `Runtime.evaluate` を **`userGesture: true`** で投げる。MCP の `cdp_command` は `params` を JSON 文字列で受け付けず（pydantic が dict に自動パースしてしまう）この経路は使えないので、付属スクリプトで直接 WebSocket を叩く。

```bash
D:/OneDrive/_sandbox/AiDiy2026/backend_mcp/.venv/Scripts/python.exe ^
  D:/OneDrive/_sandbox/AiDiy2026/scripts/cdp_user_gesture.py ^
  <tab_id> "play()"
```

スクリプトは `http://localhost:9222/json` から `webSocketDebuggerUrl` を引き、`Runtime.evaluate` を `userGesture:true, awaitPromise:false, returnByValue:true` で送る。`websockets` ライブラリは `backend_mcp/.venv` に入っている（システム Python には無い）。

確認は `eval_js` で次の状態が取れていれば成功:

```js
JSON.stringify({sceneIndex, playing, audioPaused: audioPlayer.paused, playBtnText: document.getElementById('playBtn').textContent})
// → {"sceneIndex":0,"playing":true,"audioPaused":false,"playBtnText":"再生中"}
```

## 5. OBS 録画（aidiy_obs_studio_control）

| 操作 | 呼び出し |
|------|----------|
| 状態確認 | `obs_status` / `obs_request request_type=GetRecordStatus` |
| 録画開始 | `obs_record action=start` |
| 録画停止 | `obs_record action=stop` |

落とし穴:

- **`StartRecord` の応答 `{}` ≠ 録画中**: 直後の `GetRecordStatus.outputActive` を必ず確認する。`outputActive: false` のまま固まる場合は OBS 側設定（プロファイル、出力先、ソース）が原因。シーン「シーン」に `画面キャプチャ` 等のソースが入っていること、`adv_file_output`（ffmpeg_muxer / 1920×1080）が選択されていることを OBS GUI で確認する。
- **`obs_request` の `request_data` パラメータ**: tool 仕様は string だが、harness が `{...}` を JSON object に自動パースしてしまい pydantic が型エラーを返す。引数を要するリクエスト（`GetSceneItemList` 等）は現状この経路では送れない。**追加引数なしで通る `StartRecord` / `StopRecord` / `GetRecordStatus` / `GetOutputList` などに留める**。
- 録画ファイル既定パスは `C:\Users\admin\Videos\YYYY-MM-DD HH-MM-SS.mp4`。スペースを含むためその後の ffprobe / ffmpeg はスペースなし名にコピーしてから扱う。

## 6. 音声ナレーションで人間とコラボ実行（local_play:true）

**撮影手順の一部**。ブラウザ再生 → 録画 → 録画停止 までの間、自動化できない GUI 操作（OBS の手動録画開始ボタン、Chrome ウィンドウの最前面化、視聴採否）を、TTS の音声指示でオペレーターに依頼するパターン。録画後のトリムや後処理ではなく、**録画タイミングを揃えるための撮影中ガイド**として使う。

`mcp__aidiy_text_to_speech__synthesize_speech` に **`local_play: true`** を渡すと、合成と同時に **MCP ホスト側のスピーカーで読み上げる**。チャットの戻り値を待つ前に音だけが届くため、人間オペレーターの目を画面から離した状態でも次の操作を知らせられる。

### 何をしゃべらせるか

| タイミング | しゃべる内容（例） |
|------|------|
| 自動化開始時 | 「これから AiDiy 自己紹介の録画を開始します。Chrome ウィンドウを最前面にしてください。音声が終わると、自動で録画と再生が始まります。」 |
| MCP 自動化が詰まった時 | 「録画の自動開始ができませんでした。OBS の画面で、録画開始ボタンを手動で押してください。準備ができたら、こちらのチャットで開始と入力してください。」 |
| 完了時 | 「録画が完了しました。ファイルは ユーザーフォルダのビデオに、aidiy_intro_take1.mp4 として保存されています。確認してください。」 |

### 進め方の型

1. **アシスタント側**: 自動化を試行 → 失敗を検知 → `local_play:true` で「何をしてほしいか」「どう合図するか」を 1 メッセージで読み上げ
2. **人間側**: 指示通りに OBS 録画開始 / Chrome 最前面 / その他手作業
3. **人間側**: チャットに合図ワード（「開始」「OK」など）を 1 語入力
4. **アシスタント側**: 合図を受けて残りの自動化（再生クリック、待機、停止）を実行
5. **アシスタント側**: 録画停止後に再び `local_play:true` で完了通知

### 注意点

- `local_play:true` のレスポンスは base64 audio を含み、トークン上限超でエラー扱いに見えるが、**ホスト側の再生は通常通り進む**。本文を読み返さない。
- 読み上げは非同期で、MCP 呼び出しは音声完了を待たずに戻ることがある。**人間に「聞かせる時間」を取りたい場合は、MCP 呼び出し後に `Bash sleep N` を挟む**（5 秒前後）。
- 短い指示文は速度 1.2 倍（既定の `local_rate`）でも 5〜10 秒。長文を読ませる場合は文を分割して `local_play:true` を 2 回呼ぶか、合図ワード受領を「テキスト読了の代わり」に使う。
- 合図ワードは **アシスタント側がチャット文字列として受信できるもの**にする。「開始」「OK」「準備完了」など 1〜数文字。アシスタント側は音声では聞けないので、必ずチャット入力で同期する。
- 重要操作（録画停止、削除、コミット）の前後は **音声 + 画面状態確認の二重チェック**にする。音声だけだと聞き逃す。

### 自動化と手動の切り替え判断

| 状況 | 自動化 | 手動（音声ガイド） |
|------|--------|------------------|
| ブラウザ再生（autoplay） | `cdp_user_gesture.py` で自動 | 自動が効かない場合のみ手動クリック |
| OBS 録画開始 | `obs_record action=start` で自動 | `outputActive=false` 固定の時は手動 |
| Chrome ウィンドウ最前面 | `chrome_devtools.activate_tab` を試行 | エラー時は音声ガイドで手動最前面 |
| 録画後の確認・採否判断 | 不可 | 必ず人間が視聴して判断 |
| トリム秒数決定 | 不可 | 人間が「先頭18秒、末尾5秒」と指定 |

「人間が必要な操作」は **採否判断・微調整・GUI 必須操作** に絞り、その他は MCP 自動化に寄せる。判断が要らない単純作業をいちいち音声で頼まない。

## 7. ffmpeg トリム（aidiy_ffmpeg_control）

OBS 録画は前後に「録画開始 → 再生クリックまでの数秒」「ナレーション後 → 停止までの数秒」が含まれる。再エンコードして CRF で品質固定する。

```
mcp__aidiy_ffmpeg_control__ffmpeg_run
  args_str: -y -ss 18 -i C:/Users/admin/Videos/aidiy_intro_take1.mp4 -t 171.3 \
            -c:v libx264 -crf 20 -preset medium \
            -c:a aac -b:a 192k \
            -movflags +faststart \
            C:/Users/admin/Videos/aidiy_intro_take1_trim.mp4
```

- `-ss` を `-i` の **前** に置くと高速シーク。冒頭のキーフレームずれが気になる場合は `-i` の後ろに移し、再エンコードで吸収する。
- `+faststart` を必ず付けて `moov` を先頭に移動（Web 配信時の即時再生用）。
- 失敗したらまず `returncode` を見る。`returncode == 0` なら長い stderr ログは encoder の進捗情報なので無視してよい。

## 自動化シーケンス（人間 1 操作だけ残す現実解）

1. `aidiy_text_to_speech` で全シーン MP3 を生成・尺反映
2. `chrome_devtools.navigate` で HTML を Chrome タブにロード
3. `aidiy_text_to_speech.synthesize_speech` を `local_play:true` で **「Chrome を最前面にしてください。準備ができたらチャットに合図を」を肉声案内**
4. 人間から合図（「準備完了」など）を受け取る
5. `aidiy_text_to_speech.synthesize_speech` を `local_play:true` で **「10秒後に録画と再生を開始します」を読み上げ**
6. **10秒待機**（`Start-Sleep -Seconds 10` 等）— 人間が Chrome を最前面・OBS を確認する猶予
7. `obs_record action=start` → `GetRecordStatus.outputActive=true` を確認
8. `python scripts/cdp_user_gesture.py <tab_id> "sceneIndex=0; renderBaseForScene(); play()"` で先頭から再生開始
9. `eval_js` で `playing=true` / `audioPaused=false` を確認
10. 合計尺 + 余白（例: 合計54秒なら60秒）待機
11. `obs_record action=stop` → `outputActive=false` を確認、最新 mp4 を取得
12. `ffmpeg_run` で前後トリム、必要なら別フォルダへコピーして納品

> **ステップ 5〜6 は省略禁止。** 合図を受けてすぐ録画・再生を始めると、  
> 人間が画面を切り替えている最中に録画が走り「操作中の画面」が映り込む。  
> 「10秒後に開始します」のアナウンスを必ず挟み、人間に構える時間を与えること。
>
> **実際の失敗例（take3 一回目）:** 「開始」の合図を受けた直後に OBS 録画と CDP 再生を  
> 実行したため、ブラウザが scene 2 に進んでいる状態から録画が始まり撮り直しになった。  
> 必ず「10秒後」アナウンス → `Start-Sleep -Seconds 10` → 録画開始 → CDP 再生 の順を守る。

## 注意点

- TTS の発音辞書を変えたら **シーン全体を再生成**し、`scenario.json` / `assets.json` / HTML 内シナリオの `start_sec` / `duration_sec` / `pronunciation_dictionary` 参照を一度に更新する。シーン 1 つだけ取り直すと尺がずれて最終シーンが切れる。
- ブラウザでの再生は **常に CDP `userGesture:true`** で起動する。`mcp__aidiy_chrome_devtools__click` は user activation 扱いにならない（Chrome のバージョン依存）。再生コマンドは `play()` 単体ではなく **`sceneIndex=0; renderBaseForScene(); play()`** にして先頭リセットを確実に行う。
- OBS の手動操作（録画開始ボタンを GUI で押す）に切り替える場合は、`local_play:true` の音声案内で **「OBS の録画開始ボタンを押し、Chrome を最前面に」→ 完了したらチャットに合図** という対話パターンに揃える。手動と自動の混在を想定して MP3 を全シーン揃えておけば、いつ録画開始しても損失は前後トリムで吸収できる。
- ファイルパスにスペースが入ると `ffprobe_run` / `ffmpeg_run` の `args_str` 経由で破綻する。**OBS 出力 `2026-... .mp4` は必ずスペースなし名にコピー**してから扱う。
- レスポンスがトークン上限超でエラー扱いになっても、`save_path` 指定の TTS と `returncode==0` の ffmpeg は成功している。本文を読み返さず、**ファイルシステム側で結果確認**する。
