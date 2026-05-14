// AiDiy 自己紹介 take3 共有シナリオ。index.html から参照する。
// scenario.json と同じ内容を保つ。
window.SCENARIO = {
  "project_name": "AiDiy自己紹介",
  "title": "AiDiy - AI × DIY 感覚で、自分の手でシステムを作る。",
  "source": {
    "type": "html",
    "path": "frontend_web/public/X自己紹介/index.html",
    "summary": "AiDiy の日本語ファースト設計、4層アーキテクチャ、マルチエージェント、MCP Hub、VRM Avatar を紹介する自己紹介動画"
  },
  "target": {
    "language": "ja-JP",
    "duration_sec": 60,
    "format": "document_to_html",
    "tone": "軽快で親しみやすく、でも芯は熱い。AI × DIY の楽しさと本格設計の両立。",
    "goal": "AiDiy が「AI × DIY 感覚でシステムづくり」を実現する本格基盤であることを 60 秒で伝える。楽しさを前面に、マルチエージェント・MCP 群・4 層設計の実用性を見せる。"
  },
  "assets_policy": {
    "image_output_dir": "backend_server/temp/output/AiDiy自己紹介/images",
    "audio_output_dir": "backend_server/temp/output/AiDiy自己紹介/audio",
    "html_output_path": "backend_server/temp/output/AiDiy自己紹介/index.html",
    "image_style": "実在 UI のスクリーンショット風と、抽象的な技術イメージを混ぜる。楽しさと本格感のバランス。",
    "narration_voice": "freeai:female",
    "audio_timing": "generated_mp3_duration",
    "pronunciation_dictionary": "backend_server/_config/aidiy_text_to_speech.json"
  },
  "scenes": [
    {
      "id": "scene_001",
      "title": "オープニング",
      "start_sec": 0.0,
      "duration_sec": 6.12,
      "visual_type": "title",
      "source_hint": "Hero: AiDiy / AI × DIY 感覚でシステムを作る。",
      "screen_text": "AiDiy\nAI × DIY 感覚で、自分の手でシステムを作る。",
      "narration": "AiDiy。AI と一緒に、DIY 感覚で業務システムを作る。でも中身は本気です。",
      "subtitle": "AiDiy。AI × DIY 感覚でシステムを作る。でも中身は本気。",
      "image_prompt": "Clean modern title screen with AiDiy logo, 'AI × DIY' tagline in Japanese, warm energetic tech colors, inviting and fun but professional, 16:9",
      "expression": "happy",
      "image": "images/scene_001.png"
    },
    {
      "id": "scene_002",
      "title": "日本語 × 本格設計",
      "start_sec": 6.12,
      "duration_sec": 8.28,
      "visual_type": "diagram",
      "source_hint": "日本語 DB/API/UI/Code の対応図 + 4 層構造。",
      "screen_text": "日本語で書ける。中身は 4 層アーキテクチャ。\nテーブル監査証跡も完備。",
      "narration": "データベースも API も画面も、日本語でそのまま。中身は 4 層アーキテクチャ。全テーブルに監査証跡も入った、本格設計です。",
      "subtitle": "日本語でそのまま。中身は 4 層アーキテクチャ＋監査証跡。",
      "image_prompt": "Diagram showing Japanese DB tables, API, UI connecting naturally, overlaid with 4-layer architecture (Model/Schema/CRUD/Router), audit trail icons, clean enterprise style but warm tone, 16:9",
      "expression": "relaxed",
      "image": "images/scene_002.png"
    },
    {
      "id": "scene_003",
      "title": "ライブ会話 × アバター",
      "start_sec": 14.4,
      "duration_sec": 9.144,
      "visual_type": "avatar_flow",
      "source_hint": "VRM アバター、音声波形、チャット UI、ライブ会話。",
      "screen_text": "話しかければ、応えてくれる。\nVRM アバター × 音声 × AI",
      "narration": "コードを書くだけじゃありません。話しかければ AI が応える。アバターがうなずき、あなたの相棒になる。チャットも音声も、ライブでつながります。",
      "subtitle": "話しかければ AI が応える。アバターが相棒になる。",
      "image_prompt": "VRM anime-style avatar character beside chat interface and voice waveform, live conversation mood, modern desktop, friendly and engaging, warm lighting, 16:9",
      "expression": "neutral",
      "image": "images/scene_003.png"
    },
    {
      "id": "scene_004",
      "title": "本格マルチエージェント",
      "start_sec": 23.544,
      "duration_sec": 10.128,
      "visual_type": "code_agents",
      "source_hint": "Claude / Copilot / Gemini / Codex / OpenCode のアイコン並列。",
      "screen_text": "Claude / Copilot / Gemini / Codex / OpenCode\nあなたの最適な相棒を選べる",
      "narration": "コード支援はひとつじゃない。Claude、Copilot、Gemini、Codex、OpenCode。複数の AI エージェントを用途で使い分け。最適な相棒を選んで、一緒に作れます。",
      "subtitle": "複数の AI エージェントを使い分け、最適な相棒と。",
      "image_prompt": "Five AI agent icons (Claude, Copilot, Gemini, Codex, OpenCode) arranged as selectable tools, Japanese development workspace, multi-agent orchestration feel, modern dark theme, 16:9",
      "expression": "relaxed",
      "image": "images/scene_004.png"
    },
    {
      "id": "scene_005",
      "title": "実用 MCP 道具箱",
      "start_sec": 33.672,
      "duration_sec": 10.08,
      "visual_type": "mcp_hub",
      "source_hint": "13 MCP のハブ図。観測・生成・検証の 3 カテゴリ。",
      "screen_text": "MCP Hub × 13\nブラウザ操作 / 画面キャプチャ / 画像生成\n音声合成 / DB観測 / 動画編集 / バックアップ …\n観測・生成・検証。全部そろってる。",
      "narration": "AI の手足になる 13 の MCP ツール。ブラウザ操作、画像生成、音声合成、動画編集、バックアップ。観測・生成・検証、全部そろってます。",
      "subtitle": "13 の MCP ツール。観測・生成・検証、全部そろってる。",
      "image_prompt": "Hub-and-spoke diagram with 13 MCP tools orbiting an AI agent center, grouped into 観測/生成/検証 categories, icons for browser, database, image, speech, video, backup, dark technical style, Japanese labels, 16:9",
      "expression": "neutral",
      "image": "images/scene_005.png"
    },
    {
      "id": "scene_006",
      "title": "はじめよう",
      "start_sec": 43.752,
      "duration_sec": 10.512,
      "visual_type": "launch",
      "source_hint": "サンプル一覧 → セットアップ → AiDiy 起動。",
      "screen_text": "AiDiy\n動くサンプル完備。一発セットアップ。\n使うほど育つ基盤。",
      "narration": "配車、生産、在庫。動くサンプルは揃ってます。セットアップは一発。使うほど知見が溜まって、あなただけの基盤に育ちます。AiDiy、はじめよう。",
      "subtitle": "動くサンプル完備。一発セットアップ。AiDiy、はじめよう。",
      "image_prompt": "Inviting launch screen showing sample apps (dispatch, production, inventory), setup command, and growing knowledge base, warm call-to-action, friendly energy, 16:9",
      "expression": "happy",
      "image": "images/scene_006.png"
    }
  ],
  "next_steps": [
    "TTS MCP でナレーションを音声化し、実測秒数を確認する",
    "実測に合わせて start_sec / duration_sec を調整する",
    "画像生成 MCP で各シーンの images/ を作る",
    "音声付き index.html の試作へ進む",
    "MP4 変換を検証する"
  ],
  "duration_sec": 54.264
};

window.SCENARIO_DIAGRAM_NODES = {
  title:        ["AiDiy", "AI × DIY", "本気"],
  diagram:      ["DB", "API", "UI", "4層アーキ", "監査証跡"],
  avatar_flow:  ["Chat", "Voice", "Avatar", "Live"],
  code_agents:  ["Claude", "Copilot", "Gemini", "Codex", "OpenCode"],
  mcp_hub:      ["browser", "image", "tts", "video", "backup", "DB"],
  launch:       ["配車", "生産", "在庫", "セットアップ"]
};
