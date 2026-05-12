# AiDiy自己紹介 document_to_html 試作経緯

## 目的

`frontend_web/public/X自己紹介/index.html` の内容をもとに、`document_to_html` の最初の成果物を作る。

今回の完成条件は、MP4 ではなく、ブラウザで再生できる音声付き `index.html`。

## 実施済み

1. `X自己紹介/index.html` の主要見出しと説明文を確認した。
2. 約100秒、10シーン構成の `scenario.json` を作成した。
3. 人間確認用の `script.md` を作成した。
4. テンプレート化前の試作として、`scenario.json` を埋め込んだ `index.html` を作成した。
5. 画像・音声の生成状態を管理する `assets.json` を作成した。
6. `127.0.0.1:8765` の一時HTTP配信で `index.html` をブラウザ確認した。
7. 初期表示、`次へ` によるシーン遷移、`再生` による読み上げ開始、ブラウザコンソールのエラーなしを確認した。
8. 動画画面に `image_prompt` が表示されていたため、生成用プロンプトは画面から外し、シナリオデータ内だけに残す形へ修正した。
9. 狭い表示でタイマーが詰まり気味だったため、下部コントロールのレスポンシブ配置を調整した。
10. シーン2の大見出しを短くし、動画画面で読みやすい表示にした。
11. 修正後に再読み込みし、シーン遷移、`image_prompt` 非表示、`再生中` 状態、コンソールエラーなしを確認した。
12. ブラウザ `speechSynthesis` の音質が動画用途に不十分だったため、`backend_mcp/mcp_proc/text_to_speech.py` の `TextToSpeech` を使い、Edge TTS `ja-JP-NanamiNeural` で `audio/scene_001.mp3` 〜 `audio/scene_010.mp3` を生成した。
13. `assets.json` の音声10件を `generated` に更新し、provider、voice、bytes、duration_sec を記録した。
14. `index.html` の再生処理を `speechSynthesis` から MP3 ファイル再生へ切り替えた。
15. 生成MP3の実尺に合わせ、`scenario.json` と HTML 内シナリオの `start_sec` / `duration_sec` を再計算した。合計尺は 146.98 秒。
16. `http://127.0.0.1:8765/AiDiy自己紹介/index.html?v=mp3-tts` で再確認し、`02:27` 表示、`再生中` 状態、現在URLのブラウザエラーなしを確認した。
17. シーン2の `screen_text` が PowerShell 経由更新で `????????????` に文字化けしていたため、Unicodeエスケープ経由で `DB / API / UI / Code\n業務語彙と実装名を揃える` に修復した。
18. `http://127.0.0.1:8765/AiDiy自己紹介/index.html?v=mp3-fix2` で再確認し、シーン2の文字化け解消、`再生` クリック後の `再生中` 状態、現在URLのブラウザエラーなしを確認した。
19. シーン6で止まる問題を確認した。原因は、狭い表示で本文が下部操作バーに重なり、操作が不安定になっていたことと、次シーン遷移が音声 `ended` イベント依存だったこと。
20. 狭い表示では上部コンテンツだけをスクロールさせ、下部操作バーを常に表示するレイアウトへ修正した。
21. 音声 `ended` イベントが拾えない場合でも、生成MP3の実尺 + 0.8秒で次シーンへ進む保険タイマーを追加した。
22. `scene=6` クエリで任意シーンから確認できるようにした。
23. `http://127.0.0.1:8765/AiDiy自己紹介/index.html?v=mp3-fix6&scene=6` で確認し、6ページ目の操作バー表示、`再生中` 状態、6ページ目から7ページ目への自動遷移、現在URLのブラウザエラーなしを確認した。
24. `aidiy_text_to_speech` に読み上げ用変換辞書を追加した。`AiDiy` / `aidiy` は `アイディー`、`横展開` は `よこてんかい`、`DB` は `データベース` として合成する。
25. 追加で `API`、`MCP`、`JSON`、`HTML`、`URL`、`FastAPI`、`SQLite`、`PostgreSQL`、`Code CLI`、`OpenAI`、`Claude`、`Copilot`、`Codex`、`Gemini`、`Hermes`、`VRM`、`VRMA` などのシステム用語も辞書化した。
26. 辞書適用後に `audio/scene_001.mp3` 〜 `audio/scene_010.mp3` を再生成し、`assets.json` と `scenario.json` の尺を更新した。合計尺は 143.94 秒。
27. `http://127.0.0.1:8765/AiDiy自己紹介/index.html?v=mp3-dict1&scene=6` で確認し、6ページ目の `再生中` 状態、現在URLのブラウザエラーなしを確認した。
28. `aidiy_text_to_speech` の変換辞書は、初回に `backend_server/_config/aidiy_text_to_speech.json` へ書き出し、次回以降はその JSON があれば内蔵辞書ではなく JSON 側を使う形へ変更した。
29. ナレーション音声を `provider=freeai` / `voice=female`（実体は Gemini TTS `Zephyr`）で再生成した。`backend_mcp` の `TextToSpeech` を直接呼び出し、`audio/scene_001.mp3` 〜 `audio/scene_010.mp3` を上書きした。
30. 再生成後の実尺を `ffprobe` で取得し、`scenario.json` と `index.html` 埋め込みシナリオの `start_sec` / `duration_sec` / 合計尺を再計算した。合計尺は 105.5 秒。`assets.json` の `policy.audio_provider` / `audio_voice` / 各シーンの `provider` / `voice` / `bytes` / `duration_sec` も更新した。
31. ベースフォーム + iframe 差し替え構造へ変更。`scenario.js`（共有データ）と `scene.html`（iframe テンプレート、`?n=N` で対象シーン表示）を新設。`index.html` はベースフォームに専念し、シーン変更時に `iframe.src = scene.html?n=N` を差し替える形にした。
32. ベースフォームに VRM アバタービューアを追加。take2 配下の `./AiDiy_Sample_M.vrm` と `./vrma/VRMA_0X.vrma` を参照する。Three.js + @pixiv/three-vrm を importmap でロード、VRMA を 5 本連続再生、自動瞬きを実装。
33. アバターのリップシンクを追加。Web Audio API の Analyser で `audioPlayer` の周波数振幅を取得し、平滑化して BlendShape `aa` に流す。`AudioContext` は「再生」ボタン押下時に resume する（ユーザージェスチャ要件）。
34. シーンに `expression`（happy / relaxed / neutral）を付与し、シーン切替時にアバターの表情 BlendShape を 0.6 でフェード切替する形にした。シーン番号は右下の `avatar-tag` にも表示。
35. アバターを `.app` の外へ移動し、画面右下に固定表示（200×340、`pointer-events: none`、`z-index: 100`）するよう変更。親 `X自己紹介/index.html` と同じフローティング配置に揃えた。狭幅では右上に逃がす。
36. アバターの VRMA 連続再生を廃止し、T ポーズが時々見える問題を解消。`@pixiv/three-vrm-animation` の import を外し、ロード後に `applyIdlePose` で上腕・前腕・肩を一度だけ回して自然な立ち姿に固定。毎フレーム `updateIdleSway` で胸と頭に微小な呼吸・揺らぎを乗せる。表情切替・瞬き・リップシンクはそのまま継続。
37. 初回 T ポーズ瞬き対策。`applyIdlePose` 直後に `vrm.update(0)` を呼んで normalized bone の回転を skeleton に伝搬させ、`renderer.render` で 1 フレーム描画してから canvas に `ready` クラスを付けてフェードイン表示する形に変更。canvas はデフォルト `opacity: 0` で、ready 付与で 0→1。

## 判断

- いきなり画像生成と MP3 生成へ進むと、HTML の構成が悪い場合に手戻りが大きい。
- 先に `scenario.json` だけで成立する HTML を作り、シーンの切り替え、字幕、読み上げ、尺感を確認する。
- 音声は `aidiy_text_to_speech` と同じ `TextToSpeech` 実装で生成した MP3 に差し替えた。
- 画像は暫定的に CSS 図解で表現する。後で `aidiy_image_generation` の PNG に差し替える。
- 日本語文字列をスクリプトで再生成するときは、PowerShell の文字コード変換で壊れないよう、UnicodeエスケープまたはUTF-8ファイル入力を使う。
- 音声付きHTMLは、音声イベントだけに依存せず、シナリオの `duration_sec` による保険タイマーを持つ。
- TTS では原文を直接合成せず、`TextToSpeech.PRONUNCIATION_DICTIONARY` で読み上げ用テキストへ正規化してから合成する。レスポンスには `original_speech_text`、変換後の `speech_text`、`pronunciation_replacements` を含める。
- TTS 辞書の編集場所は `backend_server/config/aidiy_text_to_speech.json`。ファイルがない場合は `TextToSpeech.DEFAULT_PRONUNCIATION_DICTIONARY` から初期生成する。

## 未実施

- `aidiy_image_generation` による画像生成。
- Chrome DevTools MCP 相当の自動再生確認は、一時HTTP配信 + in-app browser で初回確認済み。MCP サーバー経由の正式確認は未実施。
- `html_to_video` の録画・MP4 化。

## 次の作業候補

1. ナレーションが 146.98 秒で長めなので、必要なら台本を短くする。
2. `assets.json` の `image_prompt` を使って画像生成 MCP を実行する。
3. 生成した PNG を `index.html` から参照する形へ更新する。
4. MCP サーバー経由で `index.html` を自動再生確認する。
5. `html_to_video` の録画・MP4 化へ進む。
