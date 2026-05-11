// AiDiy 自己紹介 take2 共有シナリオ。index.html と scene.html の両方から参照する。
// scenario.json と同じ内容を保つ。
window.SCENARIO = {
  "project_name": "AiDiy自己紹介",
  "title": "AiDiy - 日本語で設計し、音声でもコードでも動かす",
  "assets_policy": {
    "narration_voice": "freeai:female",
    "audio_timing": "generated_mp3_duration"
  },
  "scenes": [
    {
      "id": "scene_001",
      "title": "はじめに",
      "start_sec": 0.0,
      "duration_sec": 4.92,
      "visual_type": "title",
      "source_hint": "Hero: AiDiy / 日本語で設計し、音声でもコードでも動かす。",
      "screen_text": "AiDiy\n日本語で設計し、音声でもコードでも動かす",
      "narration": "AiDiy は、日本語を第一言語にしたフルスタック業務システム開発フレームワークです。",
      "subtitle": "AiDiy は、日本語を第一言語にしたフルスタック業務システム開発フレームワークです。",
      "expression": "happy"
    },
    {
      "id": "scene_002",
      "title": "日本語ファースト",
      "start_sec": 4.92,
      "duration_sec": 10.01,
      "visual_type": "diagram",
      "source_hint": "日本語ファースト: DB、API、JSON、画面、Vueコンポーネントまで日本語で統一。",
      "screen_text": "DB / API / UI / Code\n業務語彙と実装名を揃える",
      "narration": "特徴の中心は、日本語ファースト設計です。テーブル名、API、JSON キー、画面名、コード上の変数名まで、業務語彙と実装を直接対応させます。",
      "subtitle": "日本語ファースト設計で、業務語彙と実装を直接対応させます。",
      "expression": "relaxed"
    },
    {
      "id": "scene_003",
      "title": "マルチサーバー構成",
      "start_sec": 14.93,
      "duration_sec": 12.12,
      "visual_type": "architecture",
      "source_hint": "backend_server core/apps、backend_mcp、frontend_web、frontend_avatar。",
      "screen_text": "backend_server / backend_mcp / frontend_web / frontend_avatar",
      "narration": "構成は、Core API、Apps API、MCP サーバー、Web UI、Avatar UI に分かれています。分かれていても、Vite proxy と WebSocket で、ひとつの体験としてつながります。",
      "subtitle": "Core、Apps、MCP、Web、Avatar が連携し、ひとつの体験を作ります。",
      "expression": "neutral"
    },
    {
      "id": "scene_004",
      "title": "実務サンプル",
      "start_sec": 27.05,
      "duration_sec": 10.9,
      "visual_type": "business_samples",
      "source_hint": "配車管理、生産管理、資材在庫管理。",
      "screen_text": "配車管理 / 生産管理 / 資材在庫管理",
      "narration": "テンプレートの核は、実際に動く業務サンプルです。配車、生産、資材在庫管理を通じて、マスタ、トランザクション、ビュー、スケジューラの実装パターンを確認できます。",
      "subtitle": "配車、生産、在庫管理で、業務システムの実装パターンを確認できます。",
      "expression": "relaxed"
    },
    {
      "id": "scene_005",
      "title": "AI + 音声 + アバター",
      "start_sec": 37.95,
      "duration_sec": 11.42,
      "visual_type": "avatar_flow",
      "source_hint": "Gemini Live / OpenAI Realtime、VRM / VRMA、音声入出力、口パク同期。",
      "screen_text": "Chat / Voice / Image / Avatar",
      "narration": "AiDiy は、チャットだけではありません。音声入力、AI 音声応答、画像、VRM アバター、VRMA モーションを組み合わせて、対話型の AI 体験を作ります。",
      "subtitle": "音声、画像、VRM アバターを組み合わせ、対話型の AI 体験を作ります。",
      "expression": "happy"
    },
    {
      "id": "scene_006",
      "title": "MCP Hub",
      "start_sec": 49.37,
      "duration_sec": 16.2,
      "visual_type": "mcp_hub",
      "source_hint": "13 MCP: chrome_devtools, desktop_capture, sqlite, postgres, logs, code_check, backup_check, backup_save, image_generation, speech_to_text, text_to_speech, obs_studio_control, ffmpeg_control。",
      "screen_text": "MCP Hub × 13\nobserve / generate / verify",
      "narration": "ポート 8095 には、13 個の MCP サーバーが同居します。ブラウザ操作、画面キャプチャ、DB 観測、ログ確認、型チェック、バックアップ、画像生成、音声認識、音声合成、画面録画、動画変換を、AI エージェントから利用できます。",
      "subtitle": "13 個の MCP が、観測、生成、検証を AI エージェントに提供します。",
      "expression": "neutral"
    },
    {
      "id": "scene_007",
      "title": "Code CLI と Hermes",
      "start_sec": 65.57,
      "duration_sec": 12.12,
      "visual_type": "code_agents",
      "source_hint": "claude_sdk, claude_cli, copilot_cli, codex_cli, gemini_cli, opencode_cli, aidiy_hermes。",
      "screen_text": "Multi Code CLI\nClaude / Copilot / Codex / Gemini / OpenCode / Hermes",
      "narration": "コード支援は、複数の Code CLI を並走できます。Claude、Copilot、Codex、Gemini、OpenCode、そして AiDiy 独自の aidiy_hermes を、用途ごとに切り替えられます。",
      "subtitle": "複数の Code CLI を並走し、用途ごとに切り替えられます。",
      "expression": "relaxed"
    },
    {
      "id": "scene_008",
      "title": "自己改善機構",
      "start_sec": 77.69,
      "duration_sec": 10.08,
      "visual_type": "loop",
      "source_hint": ".aidiy/knowledge、edit → observe → verify → backup、使うほど育つ。",
      "screen_text": "edit → observe → verify → backup\n.aidiy/knowledge",
      "narration": "修正して終わりではありません。AiDiy は、変更、観測、検証、バックアップの流れを記録し、.aidiy/knowledge に再利用できる知見を積み上げます。",
      "subtitle": "変更、観測、検証、バックアップを通じて、再利用できる知見を積み上げます。",
      "expression": "neutral"
    },
    {
      "id": "scene_009",
      "title": "広がるテンプレート",
      "start_sec": 87.77,
      "duration_sec": 9.31,
      "visual_type": "roadmap",
      "source_hint": "MCP 拡張、CLI エコシステム、業務領域の横展開、多言語対応。",
      "screen_text": "MCP拡張 / CLI追加 / 業務領域の横展開",
      "narration": "今後は、MCP の追加、Code CLI の追加、業務領域の横展開によって、会計、HR、CRM などにも同じ設計を広げられます。",
      "subtitle": "MCP、CLI、業務テンプレートを追加し、より多くの領域へ広げられます。",
      "expression": "relaxed"
    },
    {
      "id": "scene_010",
      "title": "まとめ",
      "start_sec": 97.08,
      "duration_sec": 8.42,
      "visual_type": "launch",
      "source_hint": "Launch: AiDiy を開く。frontend_web、/AiDiy、frontend_avatar。",
      "screen_text": "AiDiy\n日本語で、業務とAIをつなぐ。",
      "narration": "AiDiy は、日本語で業務と AI をつなぐための実験基盤です。まずは Web UI、AI コア、Avatar から触ってみてください。",
      "subtitle": "AiDiy は、日本語で業務と AI をつなぐための実験基盤です。",
      "expression": "happy"
    }
  ],
  "duration_sec": 105.5
};

window.SCENARIO_DIAGRAM_NODES = {
  title: ["AiDiy", "日本語", "AI"],
  diagram: ["Database", "API", "Frontend", "Code"],
  architecture: ["Core API", "Apps API", "MCP", "Web", "Avatar"],
  business_samples: ["配車", "生産", "在庫"],
  avatar_flow: ["Chat", "Voice", "Image", "Avatar"],
  mcp_hub: ["browser", "capture", "db", "logs", "image", "tts"],
  code_agents: ["Claude", "Copilot", "Codex", "Gemini", "Hermes"],
  loop: ["edit", "observe", "verify", "backup", "knowledge"],
  roadmap: ["MCP", "CLI", "業務", "多言語"],
  launch: ["Web UI", "AI Core", "Avatar"]
};
