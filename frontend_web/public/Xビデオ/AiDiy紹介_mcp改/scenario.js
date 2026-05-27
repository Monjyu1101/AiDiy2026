window.SCENARIO = {
  "project_name": "AiDiy紹介_mcp改",
  "version": "mcp",
  "title": "AiDiy MCP Hub - HTTP Transportで応用範囲が広がる14サーバー紹介",
  "source": {
    "type": "agents_and_knowledge",
    "summary": "FastAPI と HTTP Transport を合わせた MCP ハブインターフェースを中心に、14 個の MCP サーバーを紹介する。Web や Python からの agent 実行にも対応し、応用範囲が劇的に広がった点を強調する。"
  },
  "target": {
    "language": "ja-JP",
    "format": "html_css_scene_player_with_media",
    "tone": "親しみやすく前向き、事実ベース、根拠付き",
    "goal": "AiDiy の MCP ハブへの HTTP Transport 追加と 14 個の MCP サーバーの実態を、応用範囲の広がりとともに正確に伝える。"
  },
  "assets_policy": {
    "visual_style": "left_avatar_38_right_content_62",
    "audio_dir": "audio",
    "image_dir": "images",
    "avatar": "../vrm/VRM_AiDiy.vrm",
    "tts_provider": "freeai:female"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "この動画で紹介すること",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "background_word": "",
      "kicker": "INTRODUCTION",
      "headline": "MCP ハブが HTTP Transport を加え\n応用範囲が劇的に広がりました",
      "lead": "FastAPI と HTTP Transport を組み合わせた新インターフェースにより、Web ブラウザや Python から直接 MCP ツールを呼べるようになりました。14 のサーバーとともに紹介します。",
      "subtitle": "HTTP Transport 追加で Web・Python から直接 MCP ツールを呼べる。14 サーバーの役割を順に見ていきます。",
      "image": "images/scene_000.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "image_prompt": "Square 1:1 hero poster for AiDiy MCP Hub upgrade. Central visual is a glowing hub node labeled 'MCP HUB 8095' connected to 14 satellite nodes. Prominent labels 'HTTP TRANSPORT' and 'FastAPI' on connecting lines. Cyan and electric blue palette, dark background, premium futuristic enterprise AI style, strong typography, clean composition, no clutter.",
      "short_narration": "AiDiy の MCP ハブが FastAPI と HTTP Transport で進化しました。Web や Python からも AI ツールを直接呼べます。14 サーバーを紹介します。",
      "long_narration": "この動画は AiDiy の video_generation 機能で自動生成されました。AiDiy の MCP ハブに FastAPI と Streamable HTTP Transport を合わせた新インターフェースが追加されました。従来の SSE に加えて HTTP Transport が加わることで、Web ブラウザや Python の requests から MCP ツールを直接呼べるようになっています。AI エージェントの応用範囲が劇的に広がったこの仕組みと、ブラウザ操作からコードエージェント実行まで幅広い 14 のツールを順番に紹介します。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 9.864,
      "long_start_sec": 0.0,
      "long_duration_sec": 29.328
    },
    {
      "id": "scene_001",
      "title": "MCP Hub × 14 全体像",
      "expression": "neutral",
      "accent": "#00e0b8",
      "accent_soft": "rgba(0, 224, 184, 0.18)",
      "kicker": "MCP HUB OVERVIEW",
      "headline": "14 個の MCP サーバーが\nAI の目と手と声になる",
      "lead": "AiDiy の backend_mcp はポート 8095 に 14 個の MCP サーバーを同居させています。観測・生成・制御の 3 カテゴリで AI エージェントが現実世界を操作できます。",
      "subtitle": "ブラウザ操作からコードエージェント実行まで、14 のツールが AI の能力を広げる。",
      "image": "images/scene_001.png",
      "image_prompt": "Vertical 2:3 MCP hub infographic poster. Central AI agent node labeled 'MCP HUB port 8095' connected to 14 labeled satellite nodes arranged in a circle: chrome_devtools, desktop_capture, sqlite, postgres, logs, code_check, backup, image_generation, movie_generation, speech_to_text, text_to_speech, obs_studio_control, ffmpeg_control, code_agents. Green-cyan enterprise network diagram, modern technical style, dark background, clean layout.",
      "chips": [
        "port 8095",
        "14サーバー同居",
        "観測・生成・制御",
        "FastMCP 実装"
      ],
      "metrics": [
        {
          "label": "MCP数",
          "value": "14"
        },
        {
          "label": "カテゴリ",
          "value": "3"
        },
        {
          "label": "ポート",
          "value": "8095"
        }
      ],
      "cards": [
        {
          "title": "観測 (5)",
          "lines": [
            "Chrome DevTools / Desktop Capture",
            "SQLite / PostgreSQL",
            "Logs"
          ]
        },
        {
          "title": "生成・合成 (4)",
          "lines": [
            "Image Generation / Movie Generation",
            "Text-to-Speech / Speech-to-Text"
          ]
        },
        {
          "title": "制御・検証 (5)",
          "lines": [
            "Code Check / Backup",
            "OBS Studio Control / FFmpeg",
            "Code Agents"
          ]
        }
      ],
      "facts": [
        "backend_mcp はポート 8095 に 14 個の MCP サーバーを同居させた FastMCP アプリケーション。",
        "各 MCP は SSE / Streamable HTTP / stdio の 3 トランスポートを同一ポートで提供する。",
        "Claude Agent SDK、Python requests、stdio ホストのいずれからでも接続できる。"
      ],
      "evidence": [
        {
          "source": "backend_mcp/AGENTS.md",
          "text": "backend_mcp はポート 8095 上で 14 個の MCP サーバーを同居させる FastMCP アプリケーションです。"
        },
        {
          "source": "CLAUDE.md",
          "text": "各 MCP は SSE Transport、Streamable HTTP Transport、stdio gateway の 3 トランスポートを同一ポートで提供。Python の requests でそのまま呼び出せる。"
        }
      ],
      "short_narration": "ポート 8095 に 14 の MCP サーバーが同居し、観測・生成・制御の 3 分野で AI をサポートします。",
      "long_narration": "AiDiy の backend_mcp はポート 8095 に 14 個の MCP サーバーを集約した FastMCP アプリケーションです。役割は大きく 3 つに分かれます。まず観測系は Chrome ブラウザの自動操作、デスクトップキャプチャ、SQLite と PostgreSQL のデータ確認、ログ監視の 5 ツール。次に生成・合成系は画像生成、動画生成、音声認識、音声合成の 4 ツール。そして制御・検証系はコード構文チェック、差分バックアップ、OBS Studio 録画制御、FFmpeg 動画処理、コードエージェント実行の 5 ツールです。これらすべてを AI エージェントが呼び出せるため、観察して判断して実行するという一連の流れを自動化できます。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_start_sec": 9.864,
      "short_duration_sec": 7.512,
      "long_start_sec": 29.328,
      "long_duration_sec": 38.736
    },
    {
      "id": "scene_002",
      "title": "HTTP Transport の追加",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.18)",
      "kicker": "NEW INTERFACE",
      "headline": "SSE・HTTP・stdio を\n同一ポートで同時提供",
      "lead": "FastAPI に Streamable HTTP Transport を加えたことで、MCP ハブは 3 つのアクセス方法を 1 つのポートで提供できるようになりました。",
      "subtitle": "SSE + HTTP + stdio の 3 モードが 8095 番ポートひとつで動く。",
      "image": "images/scene_002.png",
      "image_prompt": "Vertical 2:3 architecture diagram showing 3 transport lanes converging into one FastAPI port 8095. Three labeled arrows: SSE (Server-Sent Events), Streamable HTTP (HTTP Transport), stdio (gateway mcp_stdio.py). Professional blueprint style, cyan accent, dark background, clean technical diagram, no mascots, no brand logos.",
      "chips": [
        "SSE Transport",
        "Streamable HTTP",
        "stdio gateway",
        "FastAPI + FastMCP"
      ],
      "metrics": [
        {
          "label": "トランスポート",
          "value": "3"
        },
        {
          "label": "ポート",
          "value": "1"
        },
        {
          "label": "実装",
          "value": "FastMCP"
        }
      ],
      "cards": [
        {
          "title": "SSE Transport",
          "lines": [
            "`/{mcp_name}/sse` エンドポイント",
            "Claude Agent SDK から接続",
            "従来からのアクセス方法"
          ]
        },
        {
          "title": "Streamable HTTP",
          "lines": [
            "`/{mcp_name}/{method}` エンドポイント",
            "requests.post() で直接呼べる",
            "Web フロントやスクリプトからも利用可"
          ]
        },
        {
          "title": "stdio gateway",
          "lines": [
            "`mcp_stdio.py` 経由",
            "Claude Code / MCP Host から接続",
            "標準入出力ブリッジ方式"
          ]
        }
      ],
      "facts": [
        "各 MCP は SSE Transport、Streamable HTTP Transport、stdio gateway の 3 トランスポートを同一ポートで提供する。",
        "ツール一覧は `GET http://localhost:8095/{mcp_name}/list` で取得できる。",
        "Python から `requests.post('http://localhost:8095/{mcp_name}/{method}')` で直接呼び出せる。"
      ],
      "evidence": [
        {
          "source": "CLAUDE.md",
          "text": "各 MCP は SSE Transport、Streamable HTTP Transport、stdio gateway（mcp_stdio.py）の 3 トランスポートを同一ポートで提供。Python の requests でそのまま呼び出せる。"
        },
        {
          "source": "CLAUDE.md",
          "text": "curl http://localhost:8095/aidiy_code_check/list でツール一覧確認、curl -X POST ... でツール実行"
        }
      ],
      "short_narration": "SSE・Streamable HTTP・stdio の 3 つのアクセス方法が 8095 番ポートひとつで使えます。",
      "long_narration": "AiDiy の MCP ハブに Streamable HTTP Transport が追加され、3 つのアクセス方法が 1 つのポートで提供されるようになりました。ひとつ目の SSE Transport は /{mcp_name}/sse エンドポイントで Claude Agent SDK などから接続する従来方式です。ふたつ目の Streamable HTTP は /{mcp_name}/{method} のパスに requests.post を送るだけで、Python スクリプトや自動化処理から直接 MCP ツールを呼べます。みっつ目の stdio gateway は mcp_stdio.py を経由して Claude Code や MCP ホストアプリと標準入出力でやり取りする方式です。この 3 モードを 8095 番ポートひとつで同時に提供しているのが、このアーキテクチャの最大の特徴です。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_start_sec": 17.376,
      "short_duration_sec": 6.744,
      "long_start_sec": 68.064,
      "long_duration_sec": 43.848
    },
    {
      "id": "scene_003",
      "title": "Web・Python からの直接呼び出し",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125, 255, 179, 0.18)",
      "kicker": "OPEN ACCESS",
      "headline": "ブラウザや Python から\nMCP ツールを直接呼べる",
      "lead": "Streamable HTTP Transport の追加により、Web フロントや Python スクリプトが MCP ツールを SDK なしで直接呼べるようになり、応用範囲が劇的に広がりました。",
      "subtitle": "SDK 不要。requests.post ひとつで AI ツールが動く時代へ。",
      "image": "images/scene_003.png",
      "image_prompt": "Vertical 2:3 developer workflow diagram. Three source boxes (Web Browser, Python Script, Automation) send HTTP POST arrows directly to a central 'MCP HUB port 8095' node. Green accent, dark blueprint style, 'requests.post()' code label visible, 'No SDK Required' badge, clean technical illustration.",
      "chips": [
        "SDK 不要",
        "requests.post 直接呼び出し",
        "Web フロントからも可",
        "自動化スクリプト対応"
      ],
      "metrics": [
        {
          "label": "必要なもの",
          "value": "requests のみ"
        },
        {
          "label": "パス形式",
          "value": "/{name}/{method}"
        },
        {
          "label": "応用範囲",
          "value": "劇的に拡大"
        }
      ],
      "cards": [
        {
          "title": "Python から呼ぶ",
          "lines": [
            "`import requests`",
            "`requests.post('http://localhost:8095/aidiy_sqlite/query', json={...})`",
            "SDK ライブラリ不要"
          ]
        },
        {
          "title": "curl / Web から呼ぶ",
          "lines": [
            "`curl -X POST http://localhost:8095/aidiy_logs/tail`",
            "Vite proxy 経由でフロントからも利用可",
            "ブラウザの fetch() でも呼び出せる"
          ]
        },
        {
          "title": "ツール一覧の確認",
          "lines": [
            "`GET /aidiy_code_check/list`",
            "curl でもブラウザでも確認可",
            "利用可能なメソッド一覧を返す"
          ]
        }
      ],
      "facts": [
        "Python の requests.post で `http://localhost:8095/{mcp_name}/{method}` を呼ぶだけで MCP ツールが使える。",
        "ツール一覧は `GET http://localhost:8095/{mcp_name}/list` で取得できる。",
        "自動化スクリプトやバックエンドルーターから直接利用できる。"
      ],
      "evidence": [
        {
          "source": "CLAUDE.md",
          "text": "Python の requests でそのまま呼び出せるため、自動化スクリプトやバックエンドルーターからも利用できます。"
        },
        {
          "source": "CLAUDE.md",
          "text": "curl -X POST http://localhost:8095/aidiy_code_check/check -H 'Content-Type: application/json' -d '{\"path\": \"...\"}'"
        }
      ],
      "short_narration": "requests.post ひとつで MCP ツールが動きます。SDK 不要で応用範囲が劇的に広がりました。",
      "long_narration": "HTTP Transport の最大の恩恵は、MCP ツールを SDK なしで呼び出せるようになったことです。Python なら requests.post を 1 行書くだけで、データベースを照会したり、ログを取得したり、画像を生成したりできます。エンドポイントのパスは /{mcp_name}/{method} という形式で統一されており、ツール一覧は GET /list で確認できます。Web フロントエンドからも fetch や axios を使って Vite プロキシ経由で呼び出せます。Claude Agent SDK が入っていない環境でも、あるいはバックエンドの自動化スクリプトからでも、MCP ツールをフル活用できるようになりました。AI エージェントの応用範囲が劇的に広がったと言えます。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_start_sec": 24.12,
      "short_duration_sec": 6.0,
      "long_start_sec": 111.912,
      "long_duration_sec": 41.088
    },
    {
      "id": "scene_004",
      "title": "観測・監視系 MCP 5ツール",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.18)",
      "kicker": "OBSERVE & MONITOR",
      "headline": "ブラウザ・デスクトップ・DB・ログを\nAI が直接見られる",
      "lead": "Chrome の自動操作、デスクトップキャプチャ、SQLite / PostgreSQL のデータ確認、ログ監視の 5 ツールが AI の観測能力を担います。",
      "subtitle": "Chrome を操れる。画面を見られる。DB とログをリアルタイムに読める。",
      "image": "images/scene_004.png",
      "image_prompt": "Vertical 2:3 monitoring tools collage. Five distinct panels arranged in a grid: Chrome DevTools automation window, desktop screenshot capture panel, SQLite database table viewer, PostgreSQL schema view, and log tail ERROR output. Cyan accent, dark professional enterprise dashboard style, realistic monitoring tools aesthetic, clean layout.",
      "chips": [
        "Chrome DevTools",
        "Desktop Capture",
        "SQLite / PostgreSQL",
        "Logs",
        "Python CDP 実装"
      ],
      "metrics": [
        {
          "label": "観測ツール",
          "value": "5"
        },
        {
          "label": "Chrome 実装",
          "value": "Python CDP"
        },
        {
          "label": "DB",
          "value": "SQLite + PG"
        }
      ],
      "cards": [
        {
          "title": "aidiy_chrome_devtools",
          "lines": [
            "Chrome ブラウザの自動操作",
            "クリック・入力・スクリーンショット・JS 実行",
            "Python 実装の CDP クライアント"
          ]
        },
        {
          "title": "aidiy_desktop_capture",
          "lines": [
            "OS 全体の静止画取得",
            "マルチモニター・ウィンドウ指定対応",
            "クロスヘア・ラベルのアノテーション付き"
          ]
        },
        {
          "title": "aidiy_sqlite / aidiy_postgres",
          "lines": [
            "AiDiy の SQLite DB を参照",
            "外部 PostgreSQL も接続可",
            "テーブル一覧・スキーマ・SQL クエリ実行"
          ]
        },
        {
          "title": "aidiy_logs",
          "lines": [
            "backend_server / backend_mcp のログ確認",
            "ERROR / Traceback を自動抽出",
            "tail / grep でリアルタイムデバッグ"
          ]
        }
      ],
      "facts": [
        "aidiy_chrome_devtools は Node.js 版ではなく Python 純正の CDP クライアントで実装されている。",
        "aidiy_desktop_capture はマルチモニター対応で、ウィンドウタイトル指定キャプチャも可能。",
        "aidiy_sqlite / aidiy_postgres は read-only 中心で扱い、アクセスは localhost 限定。",
        "aidiy_logs は ERROR/Traceback を自動抽出し、前後 2 行のコンテキスト付きで返す。"
      ],
      "evidence": [
        {
          "source": "backend_mcp,MCP活用手順.md",
          "text": "aidiy_chrome_devtools: ブラウザ操作、DOM 取得、ナビゲーション。Python 実装 CDP クライアント。"
        },
        {
          "source": "AGENTS.md",
          "text": "aidiy_sqlite: AiDiy SQLite DB 確認。aidiy_logs: backend_server / backend_mcp ログ確認。"
        }
      ],
      "short_narration": "ブラウザを操って、画面を撮って、DB とログを読む。5 ツールが AI の観測力を支えます。",
      "long_narration": "観測・監視系の 5 ツールは AI エージェントの目と耳の役割を果たします。aidiy_chrome_devtools は Python 実装の Chrome DevTools Protocol クライアントで、ブラウザのクリック、テキスト入力、スクリーンショット、JavaScript 実行まで自動操作できます。aidiy_desktop_capture は OS 全体の画面をキャプチャし、マルチモニターやウィンドウ指定にも対応します。aidiy_sqlite と aidiy_postgres は AiDiy の SQLite データベースと外部 PostgreSQL を参照でき、テーブル一覧からスキーマ確認、SQL クエリ実行まで行えます。aidiy_logs はバックエンドのログファイルを監視し、ERROR や Traceback を自動抽出してコンテキスト付きで返します。これら 5 ツールが連携することで、AI はブラウザ画面を見て判断し、データを確認し、エラーを発見するという人間と同じような観測と診断ができるようになります。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_start_sec": 30.12,
      "short_duration_sec": 7.008,
      "long_start_sec": 153.0,
      "long_duration_sec": 47.472
    },
    {
      "id": "scene_005",
      "title": "生成・合成系 MCP 4ツール",
      "expression": "neutral",
      "accent": "#ff6bd6",
      "accent_soft": "rgba(255, 107, 214, 0.18)",
      "kicker": "GENERATE & SYNTHESIZE",
      "headline": "画像・動画・音声・音声認識を\nMCP ひとつで AI に生成させる",
      "lead": "画像生成、動画生成、音声合成、音声認識の 4 ツールが AI エージェントに豊かな生成能力を与えます。この紹介ビデオの素材も実際に生成系 MCP で作られています。",
      "subtitle": "画像・動画・音声生成をひとつの MCP 呼び出しで実現。",
      "image": "images/scene_005.png",
      "image_prompt": "Vertical 2:3 creative generation tools collage. Four panels: colorful AI-generated image with generation prompt overlay, video frame from Veo generation with play button, audio waveform visualization for text-to-speech, microphone icon with speech recognition text output. Magenta and violet accent, modern AI creative tools style, dark background, exciting creative mood.",
      "chips": [
        "Image Generation",
        "Movie Generation",
        "Text-to-Speech",
        "Speech-to-Text"
      ],
      "metrics": [
        {
          "label": "生成系ツール",
          "value": "4"
        },
        {
          "label": "画像プロバイダ",
          "value": "3"
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
            "OpenAI / Gemini / FreeAI で画像生成",
            "プロンプト → PNG ファイル保存",
            "参照画像あり/なし両対応"
          ]
        },
        {
          "title": "aidiy_movie_generation",
          "lines": [
            "Google Gemini Veo による動画生成",
            "4〜8 秒 MP4、16:9 / 9:16 対応",
            "参照画像から image-to-video も可"
          ]
        },
        {
          "title": "aidiy_text_to_speech",
          "lines": [
            "Edge / OpenAI / Gemini / FreeAI",
            "発音辞書で AiDiy 等を自動補正",
            "このビデオのナレーションも生成済み"
          ]
        },
        {
          "title": "aidiy_speech_to_text",
          "lines": [
            "WAV ファイル / base64 WAV 入力",
            "speech_recognition / OpenAI Whisper",
            "音声をテキストに変換"
          ]
        }
      ],
      "facts": [
        "aidiy_image_generation は OpenAI gpt-image-2、Gemini gemini-3.1-flash-image-preview、FreeAI に対応する。",
        "aidiy_movie_generation は Google Gemini Veo を使い、4〜8 秒の MP4 動画を生成する。",
        "aidiy_text_to_speech は Edge / OpenAI / Gemini / FreeAI の 4 プロバイダに対応し、発音辞書で AiDiy 等の読み上げを補正する。",
        "aidiy_speech_to_text は speech_recognition と OpenAI Whisper の 2 エンジンを切り替えられる。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "aidiy_image_generation: AI 画像生成（OpenAI / Gemini / FreeAI）。aidiy_movie_generation: AI 動画生成（Google Gemini Veo）。"
        },
        {
          "source": "AGENTS.md",
          "text": "aidiy_text_to_speech: テキスト音声合成（Edge / OpenAI / Gemini / FreeAI）。AiDiy、DB、API、MCP などのシステム用語は発音辞書で自動変換する。"
        }
      ],
      "short_narration": "AI が画像・動画・音声・音声認識を担います。このビデオの素材も生成系 MCP で作られています。",
      "long_narration": "生成・合成系の 4 ツールは AI に豊かな表現力を与えます。aidiy_image_generation は OpenAI の gpt-image-2、Google の Gemini、FreeAI の 3 プロバイダに対応し、テキストプロンプトや参照画像から PNG を生成して保存します。aidiy_movie_generation は Google Gemini Veo を使い、4 から 8 秒の MP4 動画を生成します。参照画像から動画を作る image-to-video にも対応しています。aidiy_text_to_speech は Edge、OpenAI、Gemini、FreeAI の 4 プロバイダに対応した音声合成ツールで、AiDiy などのシステム用語を発音辞書で自動補正する機能も持っています。aidiy_speech_to_text は WAV ファイルや base64 音声データを speech_recognition または OpenAI Whisper でテキストに変換します。この紹介ビデオのナレーション音声も、実際に TTS MCP を使って生成されています。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_start_sec": 37.128,
      "short_duration_sec": 6.768,
      "long_start_sec": 200.472,
      "long_duration_sec": 51.936
    },
    {
      "id": "scene_006",
      "title": "制御・検証系 MCP 5ツール",
      "expression": "neutral",
      "accent": "#ffbf47",
      "accent_soft": "rgba(255, 191, 71, 0.18)",
      "kicker": "CONTROL & VERIFY",
      "headline": "コード検証・バックアップ・録画・\n動画編集・エージェント実行まで AI が担う",
      "lead": "コードチェック、差分バックアップ、OBS Studio 制御、FFmpeg による動画処理、コードエージェント実行の 5 ツールが AI ワークフローを完結させます。",
      "subtitle": "品質保証から動画制作・エージェント実行まで、5 ツールが AI の作業を締めくくる。",
      "image": "images/scene_006.png",
      "image_prompt": "Vertical 2:3 control and verification tools collage. Four panels: Python ruff linting terminal output showing code issues, file backup diff comparison view, OBS Studio recording interface with scene panel, FFmpeg waveform analysis with trim markers. Amber and orange accent, dark professional automation workflow poster, realistic developer operations style.",
      "chips": [
        "Code Check (ruff / tsc)",
        "Backup (差分方式)",
        "OBS Studio",
        "FFmpeg",
        "Code Agents"
      ],
      "metrics": [
        {
          "label": "制御・検証ツール",
          "value": "5"
        },
        {
          "label": "コードチェック",
          "value": "ruff + vue-tsc"
        },
        {
          "label": "バックアップ",
          "value": "差分方式"
        }
      ],
      "cards": [
        {
          "title": "aidiy_code_check",
          "lines": [
            "Python: py_compile + ruff",
            "TypeScript: vue-tsc",
            "MCP 経由でコード品質を自動確認"
          ]
        },
        {
          "title": "aidiy_backup",
          "lines": [
            "差分バックアップを自動保存",
            "before/after の差分比較",
            "変更ファイル一覧の履歴確認も可"
          ]
        },
        {
          "title": "aidiy_obs_studio_control",
          "lines": [
            "OBS WebSocket v5 で制御",
            "録画 Start/Stop、シーン切替",
            "このビデオの録画もここから制御"
          ]
        },
        {
          "title": "aidiy_ffmpeg_control",
          "lines": [
            "ffmpeg / ffprobe / ffplay を実行",
            "音声 RMS 検出による自動トリム",
            "字幕焼き込み・オーバーレイ対応"
          ]
        },
        {
          "title": "aidiy_code_agents",
          "lines": [
            "copilot_cli / codex_cli / aidiy_hermes など複数 CLI 対応",
            "MCP 経由でコードエージェントをキック",
            "プロジェクトパス・プロンプトを指定して実行"
          ]
        }
      ],
      "facts": [
        "aidiy_code_check は Python の py_compile/ruff と TypeScript の vue-tsc を MCP 経由で実行する。",
        "aidiy_backup は差分バックアップ方式で、初回全件スナップショット後は差分のみ保存する。",
        "aidiy_obs_studio_control は OBS WebSocket v5 を使い、録画・配信・シーン・ソース・音声ミュートを制御する。",
        "aidiy_ffmpeg_control は音声起点・終点の RMS 検出から余白付きトリムまで自動化できる。",
        "aidiy_code_agents は copilot_cli / codex_cli / aidiy_hermes など複数の AI コード CLI を MCP 経由で実行する。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "aidiy_code_check: Python 構文 / ruff / TypeScript 型チェック。aidiy_backup: 差分バックアップ保存 / 確認。"
        },
        {
          "source": "AGENTS.md",
          "text": "aidiy_obs_studio_control: OBS Studio WebSocket 制御（配信、録画、シーン、ソース、音声）。aidiy_ffmpeg_control: ffmpeg / ffprobe / ffplay 実行（動画合成、字幕焼き込み、プレビュー再生）。"
        },
        {
          "source": "AGENTS.md",
          "text": "aidiy_code_agents: AI コードエージェント実行（CodeAI CLI 経由）。copilot_cli / codex_cli / antigravity_cli / opencode_cli / aidiy_hermes に対応。"
        }
      ],
      "short_narration": "コード検証からバックアップ、OBS 録画、FFmpeg 編集、コードエージェント実行まで、5 ツールがワークフローを締めくくります。",
      "long_narration": "制御・検証系の 5 ツールは AI エージェントの作業を完結させます。aidiy_code_check は Python の ruff と vue-tsc を MCP 経由で実行し、構文エラーや型エラーをコード変更直後に自動確認できます。aidiy_backup は差分バックアップ方式を採用し、変更ファイルの保存と before/after の比較を MCP ひとつで行えます。aidiy_obs_studio_control は OBS WebSocket v5 でシーン切替や録画の Start/Stop を AI が直接制御します。aidiy_ffmpeg_control は音声の RMS レベルから発話の開始と終了を自動検出し、前後に余白をつけた状態でトリムまで完結します。そして aidiy_code_agents は copilot_cli や codex_cli、aidiy_hermes といった AI コード CLI を MCP 経由でキックできるツールです。コーディング作業をエージェントに委ねながら、観測から検証・実行まで一気通貫の自動化ループを回せます。",
      "short_audio": "audio/short_scene_006.mp3",
      "long_audio": "audio/long_scene_006.mp3",
      "short_start_sec": 43.896,
      "short_duration_sec": 9.456,
      "long_start_sec": 252.408,
      "long_duration_sec": 51.912
    },
    {
      "id": "scene_999",
      "title": "ご視聴ありがとうございました",
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196, 155, 255, 0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "background_word": "",
      "kicker": "THANK YOU",
      "headline": "ご視聴ありがとうございました。\nあなたなら MCP で何を作りますか？",
      "lead": "14 の MCP ツールと HTTP Transport を組み合わせれば、観測・生成・制御の自動化ループがあなたの手元でも動き始めます。",
      "subtitle": "AiDiy で、あなたの AI エージェントワークフローを育ててみませんか？",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "image": "images/scene_999.png",
      "image_prompt": "Square 1:1 ending visual for AiDiy MCP Hub video. Elegant typography reading 'Thank you for Watching' in refined luxury tech style. Subtle violet glow with cyan network node accents. Dark blue gradient background, clean centered layout, premium and readable, no extra UI, no character, no clutter. Polished closing card for a product introduction video.",
      "short_narration": "ご視聴ありがとうございました。AiDiy の MCP ハブで、あなただけの AI エージェントワークフローを育ててみてください。",
      "long_narration": "最後までご視聴いただきありがとうございました。この動画は AiDiy の video_generation 機能を使い、シナリオ作成・音声生成・画面録画・動画トリムまでを AI と MCP で自動化して作りました。FastAPI と HTTP Transport の組み合わせが、AI エージェントの応用範囲をどれだけ広げるか、少しでも伝わったら嬉しいです。AiDiy の 14 の MCP ツールを組み合わせれば、ブラウザ操作、画像生成、音声合成、動画処理、コード検証、コードエージェント実行を連携させた自分だけの AI エージェントワークフローが作れます。Python の requests.post ひとつから始められます。ぜひ AiDiy を試して、あなただけのエージェントワークフローを育ててみてください。あなたなら MCP で、いったい何を作りますか？",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_start_sec": 53.352,
      "short_duration_sec": 6.216,
      "long_start_sec": 304.32,
      "long_duration_sec": 39.192
    }
  ],
  "short_duration_sec": 59.568,
  "long_duration_sec": 343.512,
  "total_short_duration_sec": 59.568,
  "total_long_duration_sec": 343.512
};
