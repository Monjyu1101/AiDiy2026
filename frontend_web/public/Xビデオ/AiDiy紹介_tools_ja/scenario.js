window.SCENARIO = {
  "project_name": "AiDiy紹介_ToolHub",
  "version": "mcp",
  "title": "AiDiy TOOL HUB - 14 の MCP が繋がるツール基盤",
  "source": {
    "type": "agents_and_knowledge",
    "summary": "backend_tools の 14 MCP と 3 トランスポート構成を AGENTS.md / backend_tools/AGENTS.md から抜粋し、ToolHub 紹介として構成する。"
  },
  "target": {
    "language": "ja-JP",
    "format": "html_css_scene_player_with_media",
    "tone": "親しみやすく楽しい、軽薄すぎないトーン",
    "goal": "backend_tools が AiDiy のツール基盤として整備され、Web・Python・AI エージェントいずれからも統一的に呼び出せる点を伝える。"
  },
  "assets_policy": {
    "visual_style": "left_avatar_38_right_content_62",
    "audio_dir": "audio",
    "image_dir": "images",
    "avatar": "../_vrm/VRM_AiDiy.vrm",
    "tts_provider": "freeai:female"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "AiDiy TOOL HUB とは",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.2)",
      "kicker": "INTRODUCTION",
      "headline": "14 のツールが集まる\nAiDiy の TOOL HUB",
      "image": "images/scene_000.png",
      "chips": [
        "14 MCP",
        "ポート 8095",
        "3 トランスポート",
        "HTTP API 直接呼び出し"
      ],
      "metrics": [],
      "cards": [],
      "facts": [
        "backend_tools はポート 8095 で 14 個の MCP サーバーを同居させる。",
        "SSE / Streamable HTTP / stdio の 3 トランスポートを同一ポートで提供する。",
        "Web ブラウザ、Python スクリプト、AI エージェントいずれからも統一的に呼び出せる。"
      ],
      "evidence": [
        {
          "source": "backend_tools/AGENTS.md",
          "text": "backend_tools はポート 8095 上で 14 個の MCP サーバーを同居させる FastMCP アプリケーション。"
        },
        {
          "source": "AGENTS.md",
          "text": "backend_tools の 14 個の MCP は SSE / Streamable HTTP / stdio の 3 トランスポートを同一ポートで提供する。"
        }
      ],
      "image_prompt": "Square 1:1 hero poster for AiDiy TOOL HUB. Central hub icon with 14 connected tool nodes glowing in cyan and electric blue, dark background, futuristic tech aesthetic, clean lines, text 'AiDiy TOOL HUB' in bold premium typography, professional software branding, no fake logos, no clutter.",
      "short_narration": "AiDiy の backend_tools は 14 の MCP が集まる TOOL HUB です。",
      "long_narration": "この動画は AiDiy の video_generation 機能によって自動生成されました。今回は AiDiy のツール基盤である backend_tools、つまり「AiDiy TOOL HUB」を紹介します。ポート 8095 に 14 個の MCP サーバーが同居しており、ブラウザ操作からデータ確認、AI による画像・動画・音声の生成、コードエージェントまで、あらゆる自動化ツールが一カ所にまとまっています。Web、Python、AI エージェントのどこからでも同じ方法で呼び出せる点が TOOL HUB の大きな特徴です。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_duration_sec": 4.68,
      "long_duration_sec": 28.584
    },
    {
      "id": "scene_001",
      "title": "14 の MCP サーバー一覧",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.18)",
      "kicker": "MCP CATALOG",
      "headline": "ブラウザからコードエージェントまで\n14 ツールがひとつの基盤に",
      "image": "images/scene_001.png",
      "chips": [
        "Chrome DevTools",
        "Desktop Capture",
        "SQLite / PostgreSQL",
        "Image / Movie / TTS / STT",
        "OBS / FFmpeg / Code Agents"
      ],
      "metrics": [
        {
          "label": "MCP サーバー数",
          "value": "14"
        },
        {
          "label": "ポート",
          "value": "8095"
        },
        {
          "label": "実装言語",
          "value": "Python"
        }
      ],
      "cards": [
        {
          "title": "ブラウザ & キャプチャ",
          "lines": [
            "aidiy_chrome_devtools（CDP 操作）",
            "aidiy_desktop_capture（OS スクリーンショット）"
          ]
        },
        {
          "title": "データ & 品質",
          "lines": [
            "aidiy_sqlite / aidiy_postgres",
            "aidiy_logs / aidiy_code_check / aidiy_backup"
          ]
        },
        {
          "title": "AI 生成",
          "lines": [
            "aidiy_image_generation / aidiy_movie_generation",
            "aidiy_speech_to_text / aidiy_text_to_speech"
          ]
        },
        {
          "title": "制御 & エージェント",
          "lines": [
            "aidiy_obs_studio_control / aidiy_ffmpeg_control",
            "aidiy_code_agents"
          ]
        }
      ],
      "facts": [
        "14 個の MCP: chrome_devtools, desktop_capture, sqlite, postgres, logs, code_check, backup, image_generation, movie_generation, speech_to_text, text_to_speech, obs_studio_control, ffmpeg_control, code_agents。",
        "すべて tools_main.py に FastMCP として同居する。",
        "各 MCP のツール一覧は GET http://localhost:8095/{mcp_name}/list で確認できる。"
      ],
      "evidence": [
        {
          "source": "backend_tools/AGENTS.md",
          "text": "aidiy_chrome_devtools, aidiy_desktop_capture, aidiy_sqlite, aidiy_postgres, aidiy_logs, aidiy_code_check, aidiy_backup, aidiy_image_generation, aidiy_movie_generation, aidiy_speech_to_text, aidiy_text_to_speech, aidiy_obs_studio_control, aidiy_ffmpeg_control, aidiy_code_agents の 14 個。"
        }
      ],
      "image_prompt": "Vertical 2:3 catalog poster showing 14 MCP server tiles arranged in a clean 4-group grid (browser, data, AI generation, control), each tile with a simple icon and name, dark background, cyan accent lines, enterprise tech style, no fake logos.",
      "short_narration": "14 の MCP が分野別に整理され、ポート 8095 に集まっています。",
      "long_narration": "backend_tools には 14 個の MCP サーバーが搭載されています。ブラウザを Chrome DevTools Protocol で直接操作する chrome_devtools、OS のスクリーンショットを取る desktop_capture、SQLite や PostgreSQL でデータを確認する sqlite と postgres、ログを監視する logs、Python の構文チェックや TypeScript の型チェックを行う code_check、差分バックアップを管理する backup、AI で画像や動画を生成する image_generation と movie_generation、音声認識と音声合成を担う speech_to_text と text_to_speech、OBS Studio を制御する obs_studio_control、動画を編集する ffmpeg_control、そして AI コードエージェントを起動する code_agents です。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_duration_sec": 5.232,
      "long_duration_sec": 37.56
    },
    {
      "id": "scene_002",
      "title": "3 つのトランスポート",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125, 255, 179, 0.18)",
      "kicker": "TRANSPORT LAYER",
      "headline": "SSE / HTTP / stdio の 3 通り\n同じポートから呼び出せる",
      "image": "images/scene_002.png",
      "chips": [
        "SSE Transport",
        "Streamable HTTP",
        "stdio gateway",
        "ポート 8095 に統一"
      ],
      "metrics": [
        {
          "label": "トランスポート数",
          "value": "3"
        },
        {
          "label": "統一ポート",
          "value": "8095"
        },
        {
          "label": "Python 直接呼出",
          "value": "requests"
        }
      ],
      "cards": [
        {
          "title": "SSE Transport",
          "lines": [
            "http://localhost:8095/{mcp_name}/sse",
            "AI エージェント・Claude Code・MCP クライアント向け"
          ]
        },
        {
          "title": "Streamable HTTP",
          "lines": [
            "POST http://localhost:8095/{mcp_name}/{method_name}",
            "Python の requests や curl で直接呼び出せる"
          ]
        },
        {
          "title": "stdio gateway",
          "lines": [
            "mcp_stdio.py --sse-url http://localhost:8095/{mcp_name}/sse",
            "Codex など stdio 専用の Code CLI 向け"
          ]
        }
      ],
      "facts": [
        "SSE Transport: http://localhost:8095/{mcp_name}/sse — AI エージェント・Claude Code・MCP クライアント向け。",
        "Streamable HTTP: POST http://localhost:8095/{mcp_name}/{method_name} — Python の requests や curl で直接利用。",
        "stdio gateway: mcp_stdio.py — stdio 専用 Code CLI（Codex など）向け。",
        "3 トランスポートすべてが同一ポート 8095 で提供される。"
      ],
      "evidence": [
        {
          "source": "backend_tools/AGENTS.md",
          "text": "SSE / Streamable HTTP / stdio の 3 トランスポートを同一ポートで提供。Python から requests.post('http://localhost:8095/aidiy_sqlite/list_tables', json={}) で直接呼び出せる。"
        }
      ],
      "image_prompt": "Vertical 2:3 infographic showing three transport lanes (SSE, HTTP, stdio) all converging into a single hub port 8095, dark background, green accent lines, clean architecture arrows, enterprise tech style, each lane labeled with protocol name and typical user (AI Agent, Python script, Code CLI), no fake logos.",
      "short_narration": "SSE・HTTP・stdio の 3 ルートで同じ MCP ツールを呼び出せます。",
      "long_narration": "backend_tools の特徴のひとつは、すべての MCP が 3 種類のトランスポートに対応していることです。1 つ目は SSE Transport で、AI エージェントや Claude Code などの MCP クライアントが接続するエンドポイントです。2 つ目は Streamable HTTP で、Python の requests ライブラリや curl から POST リクエストとして直接呼び出せます。3 つ目は stdio gateway で、Codex のように stdio しか使えない Code CLI 向けに mcp_stdio.py が橋渡し役を担います。どのルートを選んでも、同じポート 8095 の同じ MCP に繋がるため、用途に応じて使い分けられます。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_duration_sec": 4.968,
      "long_duration_sec": 32.448
    },
    {
      "id": "scene_003",
      "title": "ブラウザ & デスクトップ自動化",
      "expression": "neutral",
      "accent": "#ff9c29",
      "accent_soft": "rgba(255, 156, 41, 0.18)",
      "kicker": "BROWSER & DESKTOP",
      "headline": "Chrome を Python で直接操作\nスクリーンショットも自在に",
      "image": "images/scene_003.png",
      "chips": [
        "Chrome DevTools Protocol",
        "Python CDP",
        "デスクトップキャプチャ",
        "自動テスト"
      ],
      "metrics": [
        {
          "label": "CDP デバッグポート",
          "value": "9222"
        },
        {
          "label": "実装",
          "value": "Python"
        },
        {
          "label": "Node.js 依存",
          "value": "なし"
        }
      ],
      "cards": [
        {
          "title": "aidiy_chrome_devtools",
          "lines": [
            "Chrome を CDP で自動操作",
            "Node.js 非依存の Python 実装",
            "ChromeManager で単一プロセス管理"
          ]
        },
        {
          "title": "aidiy_desktop_capture",
          "lines": [
            "OS のスクリーンショット取得",
            "モニター指定 / 領域指定 / ウィンドウ指定",
            "PNG / JPEG 対応"
          ]
        }
      ],
      "facts": [
        "aidiy_chrome_devtools は Node.js 版ではなく Python 実装の CDP client。",
        "Chrome は ChromeManager が単一 subprocess として管理し --remote-debugging-port=9222 で起動。",
        "aidiy_desktop_capture は OS のスクリーンショットをモニター番号・領域・ウィンドウタイトルで取得できる。"
      ],
      "evidence": [
        {
          "source": "backend_tools/AGENTS.md",
          "text": "Chrome DevTools は Node.js 版ではなく Python 実装の CDP client を使う。Chrome は ChromeManager が単一 subprocess として管理し、必要時に --remote-debugging-port=9222 で起動する。"
        }
      ],
      "image_prompt": "Vertical 2:3 poster showing browser automation: Python code block connecting to Chrome browser via CDP port 9222, with screenshot output panel, dark background, orange accent glow, clean flow arrows, enterprise tech style, no fake logos.",
      "short_narration": "Python から Chrome を操作し、画面キャプチャも自動化できます。",
      "long_narration": "aidiy_chrome_devtools は Chrome DevTools Protocol を使ってブラウザを Python から直接操作する MCP です。Node.js に依存せず、Python だけで動きます。Chrome は ChromeManager がプロセスを一元管理し、デバッグポート 9222 で起動します。ナビゲーション、クリック、テキスト入力、JavaScript の実行、コンソールログ取得、ネットワークキャプチャなど、E2E テストや画面自動化に必要な操作がそろっています。aidiy_desktop_capture は OS レベルのスクリーンショットを撮るツールで、モニター番号や座標指定、ウィンドウタイトルによるキャプチャが可能です。この 2 つを組み合わせると、ブラウザ内外を問わず画面操作と確認を自動化できます。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_duration_sec": 3.648,
      "long_duration_sec": 35.016
    },
    {
      "id": "scene_004",
      "title": "データ & コード品質管理",
      "expression": "neutral",
      "accent": "#c47dff",
      "accent_soft": "rgba(196, 125, 255, 0.18)",
      "kicker": "DATA & QUALITY",
      "headline": "DB 確認・ログ監視・コードチェック\nバックアップまでひとつの基盤で",
      "image": "images/scene_004.png",
      "chips": [
        "SQLite / PostgreSQL",
        "ログ監視",
        "ruff / vue-tsc",
        "差分バックアップ"
      ],
      "metrics": [
        {
          "label": "DB 対応",
          "value": "2種"
        },
        {
          "label": "コードチェック",
          "value": "3種"
        },
        {
          "label": "バックアップ方式",
          "value": "差分"
        }
      ],
      "cards": [
        {
          "title": "aidiy_sqlite / aidiy_postgres",
          "lines": [
            "AiDiy SQLite DB の read-only 中心クエリ",
            "外部 PostgreSQL への接続・確認"
          ]
        },
        {
          "title": "aidiy_logs",
          "lines": [
            "backend_server / backend_tools のログ観測",
            "ERROR / Traceback の自動抽出"
          ]
        },
        {
          "title": "aidiy_code_check",
          "lines": [
            "Python 構文チェック（py_compile）",
            "ruff による lint チェック",
            "TypeScript 型チェック（vue-tsc / tsc）"
          ]
        },
        {
          "title": "aidiy_backup",
          "lines": [
            "差分バックアップ保存 / 確認",
            "HTTP で save / check に分岐",
            "バージョン履歴管理"
          ]
        }
      ],
      "facts": [
        "aidiy_sqlite は AiDiy DB (backend_server/_data/AiDiy/database.db) の read-only 中心クエリを提供する。",
        "aidiy_logs は backend_server / backend_tools のログ末尾と ERROR 抽出を提供する。",
        "aidiy_code_check は Python 構文 / ruff / TypeScript 型チェックの 3 種類に対応する。",
        "aidiy_backup は差分バックアップで HTTP の save / check に分岐する。"
      ],
      "evidence": [
        {
          "source": "backend_tools/AGENTS.md",
          "text": "aidiy_sqlite: AiDiy SQLite DB の read-only 中心クエリ。aidiy_logs: backend_server / backend_tools のログ観測。aidiy_code_check: Python 構文、ruff、TypeScript 型チェック。aidiy_backup: 差分バックアップ保存 / 確認（HTTP は save / check に分岐）。"
        }
      ],
      "image_prompt": "Vertical 2:3 poster showing data and quality management: database cylinders (SQLite and PostgreSQL) connected to log monitor panels, code lint check indicators and green/red result badges, backup version timeline, dark background, purple accent, clean enterprise diagram, no fake logos.",
      "short_narration": "DB、ログ、コード品質、バックアップを AI から一括管理できます。",
      "long_narration": "データと品質管理に関する MCP も充実しています。aidiy_sqlite は AiDiy の SQLite データベースをクエリで確認でき、aidiy_postgres は外部の PostgreSQL にも接続できます。aidiy_logs はバックエンドサーバーのログを末尾から取得したり、エラーと例外を自動で抽出したりします。aidiy_code_check は Python ファイルの構文チェック、ruff による linting、TypeScript の型チェックの 3 種類に対応しています。aidiy_backup は差分バックアップで変更ファイルだけを保存し、バージョン履歴の確認や前後の差分表示もできます。これらを AI エージェントから組み合わせることで、コーディングと品質確認を自動化できます。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_duration_sec": 4.776,
      "long_duration_sec": 36.576
    },
    {
      "id": "scene_005",
      "title": "AI メディア生成",
      "expression": "neutral",
      "accent": "#ff6bd6",
      "accent_soft": "rgba(255, 107, 214, 0.18)",
      "kicker": "AI MEDIA GENERATION",
      "headline": "画像・動画・音声の生成を\n複数プロバイダで統一 API に",
      "image": "images/scene_005.png",
      "chips": [
        "OpenAI / Gemini / FreeAI",
        "Veo 動画生成",
        "Edge TTS / Whisper",
        "MP3 出力"
      ],
      "metrics": [
        {
          "label": "画像プロバイダ",
          "value": "3"
        },
        {
          "label": "動画モデル",
          "value": "Veo"
        },
        {
          "label": "TTS プロバイダ",
          "value": "4"
        }
      ],
      "cards": [
        {
          "title": "aidiy_image_generation",
          "lines": [
            "OpenAI gpt-image / DALL-E",
            "Gemini / FreeAI 対応",
            "プロンプトと保存先を指定するだけ"
          ]
        },
        {
          "title": "aidiy_movie_generation",
          "lines": [
            "Google Gemini Veo で動画生成",
            "MP4 ファイルとして保存",
            "4〜8 秒 / 16:9 or 9:16"
          ]
        },
        {
          "title": "aidiy_text_to_speech",
          "lines": [
            "Edge / OpenAI / Gemini / FreeAI",
            "MP3 出力・発音辞書変換",
            "local_play でその場再生も可能"
          ]
        },
        {
          "title": "aidiy_speech_to_text",
          "lines": [
            "speech_recognition（オフライン）",
            "OpenAI Whisper（高精度）",
            "WAV ファイルまたは base64 入力"
          ]
        }
      ],
      "facts": [
        "aidiy_image_generation は OpenAI（gpt-image-2 / DALL-E-3）、Gemini、FreeAI の 3 プロバイダに対応する。",
        "aidiy_movie_generation は Google Gemini Veo で動画を生成し MP4 として保存する。",
        "aidiy_text_to_speech は Edge / OpenAI / Gemini / FreeAI の 4 プロバイダで MP3 を出力する。",
        "aidiy_speech_to_text は speech_recognition（オフライン）と OpenAI Whisper に対応する。"
      ],
      "evidence": [
        {
          "source": "backend_tools/AGENTS.md",
          "text": "aidiy_image_generation: AI 画像生成（OpenAI gpt-image / DALL-E、Gemini、FreeAI）。aidiy_movie_generation: AI 動画生成（Google Gemini Veo、MP4 保存）。aidiy_text_to_speech: テキスト音声合成（Edge / OpenAI / Gemini / FreeAI、MP3 出力）。aidiy_speech_to_text: 音声認識（speech_recognition、OpenAI Whisper）。"
        }
      ],
      "image_prompt": "Vertical 2:3 poster showing AI media generation workflow: image generation panel showing a generated image, video clip frame, audio waveform and speech bubble, connected by flowing lines, multiple provider labels (OpenAI, Gemini, FreeAI), dark background, pink accent glow, creative technology style, no fake logos.",
      "short_narration": "画像・動画・音声の生成を複数プロバイダでまとめて扱えます。",
      "long_narration": "AI によるメディア生成も TOOL HUB に統合されています。aidiy_image_generation は OpenAI の gpt-image や DALL-E-3、Gemini、FreeAI の 3 プロバイダを切り替えて使えます。aidiy_movie_generation は Google の Gemini Veo を使って 4 秒〜8 秒の動画を MP4 として生成します。音声合成の aidiy_text_to_speech は Edge TTS、OpenAI、Gemini、FreeAI の 4 プロバイダに対応し、MP3 ファイルとして出力できるほか、local_play オプションでその場で再生することもできます。発音辞書による自動読み替えも搭載済みです。音声認識の aidiy_speech_to_text はオフラインで動く speech_recognition と高精度な OpenAI Whisper の両方に対応しています。実はこの動画の音声ナレーションも TTS MCP によって生成されています。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_duration_sec": 3.48,
      "long_duration_sec": 43.944
    },
    {
      "id": "scene_006",
      "title": "制御 & コードエージェント連携",
      "expression": "neutral",
      "accent": "#ffd700",
      "accent_soft": "rgba(255, 215, 0, 0.18)",
      "kicker": "CONTROL & AGENTS",
      "headline": "OBS・FFmpeg・コードエージェントを\nAI から直接コントロール",
      "image": "images/scene_006.png",
      "chips": [
        "OBS Studio WebSocket",
        "ffmpeg / ffprobe",
        "Code AI 7種",
        "自動ビデオ生成"
      ],
      "metrics": [
        {
          "label": "Code AI 種類",
          "value": "7"
        },
        {
          "label": "ffmpeg 操作",
          "value": "フル対応"
        },
        {
          "label": "OBS WebSocket",
          "value": "v5"
        }
      ],
      "cards": [
        {
          "title": "aidiy_obs_studio_control",
          "lines": [
            "OBS Studio WebSocket v5 制御",
            "配信・録画・シーン・ソース・音声を操作",
            "AI からの全自動配信ワークフローへ"
          ]
        },
        {
          "title": "aidiy_ffmpeg_control",
          "lines": [
            "ffmpeg / ffprobe / ffplay を薄くラップ",
            "動画合成・字幕焼き込み・トリム・プレビュー",
            "音声区間の自動検出にも対応"
          ]
        },
        {
          "title": "aidiy_code_agents",
          "lines": [
            "claude_sdk / copilot_cli / codex_cli など 7 種類",
            "AI コードエージェントを subprocess で起動",
            "プロジェクトパス・モデル・ターン数を指定できる"
          ]
        }
      ],
      "facts": [
        "aidiy_obs_studio_control は OBS Studio WebSocket v5 で配信・録画・シーン・ソース・音声を制御する。",
        "aidiy_ffmpeg_control は ffmpeg / ffprobe / ffplay の薄いランナーで、動画合成・字幕・トリム・プレビューに対応する。",
        "aidiy_code_agents は claude_sdk、claude_cli、copilot_cli、codex_cli、antigravity_cli、opencode_cli、aidiy_hermes の 7 種類の Code AI CLI を起動できる。"
      ],
      "evidence": [
        {
          "source": "backend_tools/AGENTS.md",
          "text": "aidiy_obs_studio_control: OBS Studio WebSocket 制御。aidiy_ffmpeg_control: ffmpeg / ffprobe / ffplay の薄いランナー。aidiy_code_agents: AI コードエージェント実行（CodeAI CLI 経由）。"
        },
        {
          "source": "AGENTS.md",
          "text": "Code AI の有効値は claude_sdk、claude_cli、copilot_cli、codex_cli、antigravity_cli、opencode_cli、aidiy_hermes を想定する。"
        }
      ],
      "image_prompt": "Vertical 2:3 poster showing three control nodes: OBS Studio recording panel with REC indicator, ffmpeg video processing pipeline with waveform and timeline, code agent execution console showing AI assistant output, all connected by gold accent lines on dark background, professional automation workflow diagram, no fake logos.",
      "short_narration": "OBS や FFmpeg の制御から、AI コードエージェントの起動まで可能です。",
      "long_narration": "TOOL HUB には外部ツールの制御系 MCP も揃っています。aidiy_obs_studio_control は OBS Studio の WebSocket v5 を通じて、配信・録画の開始停止、シーンの切り替え、ソースの表示非表示、音声ミュートを AI から操作できます。aidiy_ffmpeg_control は ffmpeg、ffprobe、ffplay の薄いラッパーで、動画の合成や字幕焼き込み、指定区間のトリム、音声区間の自動検出、プレビュー再生に対応しています。そして aidiy_code_agents は claude_sdk、copilot_cli、codex_cli など 7 種類の AI コードエージェント CLI を subprocess として起動し、プロジェクトパスやモデル、最大ターン数を指定して実行できます。これら 3 つを組み合わせることで、コード生成から動画制作までを一連のワークフローとして自動化できます。",
      "short_audio": "audio/short_scene_006.mp3",
      "long_audio": "audio/long_scene_006.mp3",
      "short_duration_sec": 5.232,
      "long_duration_sec": 46.92
    },
    {
      "id": "scene_999",
      "title": "まとめ",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.2)",
      "kicker": "SUMMARY",
      "headline": "AiDiy TOOL HUB で\nあなたの自動化を次のレベルへ",
      "image": "images/scene_999.png",
      "chips": [
        "14 MCP",
        "3 トランスポート",
        "ポート 8095",
        "全自動化対応"
      ],
      "metrics": [
        {
          "label": "MCP 総数",
          "value": "14"
        },
        {
          "label": "トランスポート",
          "value": "3"
        },
        {
          "label": "ポート",
          "value": "8095"
        }
      ],
      "cards": [
        {
          "title": "今回紹介したこと",
          "lines": [
            "14 MCP が一箇所に集まる TOOL HUB",
            "SSE / HTTP / stdio の 3 トランスポート",
            "ブラウザ・データ・AI 生成・制御すべてを統一 API で"
          ]
        },
        {
          "title": "AiDiy を使ってみよう",
          "lines": [
            "backend_tools を起動するだけで 14 ツールが使える",
            "Python の requests で今すぐ試せる",
            "AI エージェントから自動化ワークフローを組める"
          ]
        }
      ],
      "facts": [
        "backend_tools の 14 MCP は SSE / Streamable HTTP / stdio の 3 トランスポートで同一ポート 8095 から提供される。",
        "Python からは requests.post('http://localhost:8095/{mcp_name}/{method}', json={}) で直接呼び出せる。",
        "この動画自体が AiDiy TOOL HUB の video_generation 機能と TTS MCP によって自動生成された成果物。"
      ],
      "evidence": [
        {
          "source": "backend_tools/AGENTS.md",
          "text": "14 個の MCP サーバーが同一ポート 8095 に同居し、SSE / Streamable HTTP / stdio の 3 トランスポートを提供する。"
        }
      ],
      "image_prompt": "Square 1:1 summary poster for AiDiy TOOL HUB. Central glowing hub with 14 connected nodes, bold text '14 MCP TOOL HUB' in cyan typography, dark background, celebratory but professional mood, clean composition, inspiring call-to-action feel, no clutter, no fake logos.",
      "short_narration": "AiDiy TOOL HUB で、あらゆる自動化をひとつの基盤から始めましょう。",
      "long_narration": "今回は AiDiy の TOOL HUB、つまり backend_tools が提供する 14 個の MCP サーバーを紹介しました。ブラウザ自動化からデータ確認、AI 画像・動画・音声生成、OBS や FFmpeg の制御、そして AI コードエージェントまで、すべてがポート 8095 ひとつに集まっています。SSE、HTTP、stdio の 3 つのトランスポートに対応しているので、Python スクリプトからでも AI エージェントからでも、同じツールを同じ感覚で呼び出せます。そしてこの動画自体が、AiDiy の video_generation 機能と TTS MCP を使って自動生成された成果物です。自分のプロジェクトでも試してみたいと思ったら、ぜひ AiDiy を手元で起動してみてください。きっと「あ、これ自分でもできる」という発見が待っています。参考になったらチャンネル登録と高評価をよろしくお願いします。次の動画でまた新しい AiDiy の機能をお届けします！",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_duration_sec": 3.648,
      "long_duration_sec": 78.552
    }
  ],
  "short_duration_sec": 35.664,
  "long_duration_sec": 339.6,
  "total_short_duration_sec": 35.664,
  "total_long_duration_sec": 339.6
};
