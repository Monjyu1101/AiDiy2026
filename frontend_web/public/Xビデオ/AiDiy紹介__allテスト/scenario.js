window.SCENARIO = {
  "project_name": "AiDiy自己紹介",
  "version": "take4",
  "title": "AiDiy - 実態ベース自己紹介",
  "source": {
    "type": "agents_and_knowledge",
    "summary": "AiDiy の実装実態を AGENTS.md と .aidiy/knowledge から抜粋し、事実ベース紹介として再構成する。"
  },
  "target": {
    "language": "ja-JP",
    "format": "html_css_scene_player_with_media",
    "tone": "事実ベース、簡潔、根拠付き",
    "goal": "AiDiy の実態を、構成・命名・サンプル・AI・MCP・ナレッジ入口まで正確に伝える。"
  },
  "assets_policy": {
    "visual_style": "left_image_30_right_explanation_70",
    "image_output_dir": "frontend_web/public/X自己紹介/AiDiy自己紹介ビデオtake4/images",
    "audio_output_dir": "frontend_web/public/X自己紹介/AiDiy自己紹介ビデオtake4/audio",
    "avatar": "../vrm/VRM_AiDiy.vrm",
    "image_provider": "openai:gpt-image-2",
    "tts_provider": "edge:female"
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
      "headline": "この動画では、AiDiy の全体像と\n設計の考え方を紹介します",
      "lead": "日本語ファースト設計、3常駐サーバー + 1 CLI、業務サンプル、AI コア、MCP、knowledge の入口までを短く見ていきます。",
      "subtitle": "この動画では、AiDiy の全体像、設計方針、業務サンプル、AI・MCP 連携を紹介します。",
      "image": "images/scene_000.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "image_prompt": "Square 1:1 hero poster for AiDiy. Make the word AiDiy itself the coolest central visual, with premium futuristic typography, strong cyan and electric blue glow, elegant Japanese enterprise AI platform mood, dark background, clean composition, high readability, polished technology branding aesthetic, no clutter, no extra fake logos, no dense paragraphs. Keep the stylish upper feeling from the reference image but simplify it into a bold square cover image.",
      "short_narration": "AiDiy は日本語ファーストの業務テンプレートです。全体像を紹介します。",
      "long_narration": "この動画では、AiDiy の全体像と設計の考え方を紹介します。日本語ファースト設計から始まり、3 つの常駐サーバーと複数の AI CLI、業務サンプル、AI コア、MCP ハブ、そしてナレッジシステムの入口まで、実装に沿って順番に見ていきます。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_start_sec": 0,
      "short_duration_sec": 5.784,
      "long_start_sec": 0,
      "long_duration_sec": 18.504
    },
    {
      "id": "scene_001",
      "title": "AiDiyとは",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.18)",
      "kicker": "PROJECT OVERVIEW",
      "headline": "日本語ファーストの\nフルスタック業務管理テンプレート",
      "lead": "FastAPI + SQLite + Vue 3 を軸に、業務システム実装例と AI 実験基盤をひとつにまとめたのが AiDiy です。",
      "subtitle": "日本語識別子と業務サンプルを土台に、AI / 音声 / MCP まで一体化した基盤。",
      "image": "images/scene_001.png",
      "image_prompt": "Vertical 2:3 key visual for a Japanese enterprise AI development platform, accurate architecture mood, modular blocks suggesting backend_server, backend_mcp, frontend_web, frontend_avatar, dark blueprint background, clean cyan and magenta lighting, no brand logos, realistic software diagram poster, high clarity, professional not playful",
      "chips": [
        "日本語識別子",
        "FastAPI + SQLite + Vue 3",
        "3常駐サーバー + 1 CLI",
        "業務サンプル同梱"
      ],
      "metrics": [
        {
          "label": "常駐サーバー",
          "value": "3"
        },
        {
          "label": "MCP",
          "value": "13"
        },
        {
          "label": "Code AI 候補",
          "value": "7"
        }
      ],
      "cards": [
        {
          "title": "目的",
          "lines": [
            "日本語ネイティブな開発環境",
            "実用的な業務管理テンプレート",
            "AI・音声・画像・MCP の実験基盤"
          ]
        },
        {
          "title": "中核スタック",
          "lines": [
            "backend_server / backend_mcp / frontend_web / frontend_avatar",
            "SQLite 共有 DB",
            "Vue 3 + Vite + TypeScript"
          ]
        }
      ],
      "facts": [
        "AiDiy は日本語を第一言語とするフルスタック業務管理システム開発フレームワーク / テンプレート。",
        "権限、マスタ、トランザクション、スケジューラ、在庫管理の実装例を含む。",
        "AI、音声、画像、Code CLI、MCP を統合する実験基盤でもある。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "AiDiy は、日本語を第一言語とするフルスタック業務管理システムの開発フレームワーク / テンプレート。"
        },
        {
          "source": "AGENTS.md",
          "text": "FastAPI + SQLite + Vue 3 による実用的な業務管理テンプレートを提供する。"
        }
      ],
      "short_narration": "テーブル名、API パス、ファイル名まで日本語で統一します。",
      "long_narration": "AiDiy は、日本語を第一言語として設計されたフルスタック業務管理テンプレートです。FastAPI と SQLite と Vue 3 を中核に、権限管理、マスタ管理、トランザクション、スケジューラ、在庫管理などの業務サンプルを実装済みで含んでいます。さらに AI チャット、音声、画像、コード支援、MCP ハブを統合した実験基盤でもあります。バックエンドは core_main と apps_main の 2 サーバー構成で、フロントエンドは Web と Electron 対応のアバターアプリ、そして 13 個の MCP ツールサーバーで全体が構成されています。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_start_sec": 5.784,
      "short_duration_sec": 4.872,
      "long_start_sec": 18.504,
      "long_duration_sec": 35.904
    },
    {
      "id": "scene_002",
      "title": "日本語ファースト設計",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125, 255, 179, 0.18)",
      "kicker": "JAPANESE FIRST",
      "headline": "DB / API / UI / Code を\n日本語で一直線につなぐ",
      "lead": "AiDiy では業務語彙と実装名をできるだけ一致させ、日本語話者がコードと画面を直接対応づけられるようにしています。",
      "subtitle": "業務語彙と実装名を揃え、読めるまま保守できる構成。",
      "image": "images/scene_002.png",
      "image_prompt": "Vertical 2:3 infographic of Japanese-first software design, layered database API UI code connection, enterprise blueprint poster, strong arrows, clean boxes, realistic development system diagram, dark background with green accent, no garbled logo emphasis, professional Japanese software architecture mood",
      "chips": [
        "UTF-8 固定",
        "URL も日本語",
        "JSON キーも日本語",
        "一般名 request/query は英字可"
      ],
      "metrics": [
        {
          "label": "例レイヤー",
          "value": "4"
        },
        {
          "label": "原則",
          "value": "一致重視"
        }
      ],
      "cards": [
        {
          "title": "Database",
          "lines": [
            "テーブル名 `C権限`",
            "カラム名 `利用者ID`",
            "監査フィールド標準"
          ]
        },
        {
          "title": "API / JSON",
          "lines": [
            "`/core/利用者/一覧`",
            "`{\"利用者名\": \"admin\"}`",
            "POST 中心の統一レスポンス"
          ]
        },
        {
          "title": "Frontend",
          "lines": [
            "`C利用者一覧.vue`",
            "`/C管理/C利用者/一覧`",
            "Vue Router / Pinia 運用"
          ]
        },
        {
          "title": "Code",
          "lines": [
            "`利用者名`",
            "`配車日付`",
            "`商品名`"
          ]
        }
      ],
      "facts": [
        "画面、URL、JSON キー、識別子は日本語を原則とする。",
        "DB 項目名、API 項目名、フロントエンド変数名はできるだけ一致させる。",
        "HowTo や検証手順は AGENTS.md ではなく .aidiy/knowledge に置く。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "全レイヤーで日本語識別子を使います。Database / API / Frontend / Code の例が明示されています。"
        },
        {
          "source": "frontend_web/AGENTS.md",
          "text": "日本語ファイル名、日本語 route、日本語 JSON key を使う。template の component tag は ASCII にする。"
        }
      ],
      "short_narration": "画面から FastAPI まで、日本語識別子で書きます。",
      "long_narration": "AiDiy の最大の特徴は日本語ファースト設計です。データベースのテーブル名は C権限や T配車、API パスは /core/利用者/一覧、JSON キーは 利用者名や配車日付、Vue コンポーネントのファイル名まで、すべてのレイヤーで日本語識別子を使います。これにより業務語彙とコードの識別子が直接対応し、日本語話者が設計意図を保守の場面でもそのまま読み取れるようになっています。ただし request、query、items といったシステム用語や英字ライブラリ名はそのまま英語で使います。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_start_sec": 10.656,
      "short_duration_sec": 4.32,
      "long_start_sec": 54.408,
      "long_duration_sec": 34.248
    },
    {
      "id": "scene_003",
      "title": "3常駐サーバー + マルチCLI",
      "expression": "neutral",
      "accent": "#ff6bd6",
      "accent_soft": "rgba(255, 107, 214, 0.18)",
      "kicker": "ARCHITECTURE",
      "headline": "複数の CLI を並べて使い、\nHermes は独自エンジンでつなぐ",
      "lead": "AiDiy は Core / Apps / MCP を常駐分離しつつ、AIコアの Code AI では複数 CLI を切り替えられます。backend_hermes はその中でも AiDiy 専用に組み込まれた独自実装です。",
      "subtitle": "Code AI はひとつではなく、複数CLI + 独自実装 Hermes を切り替える。",
      "image": "images/scene_003.png",
      "image_prompt": "Vertical 2:3 architecture poster showing AiDiy as a multi-CLI coding platform, not a single CLI. Show three resident backend blocks for core 8091, apps 8092, mcp 8095 feeding one AI core panel, and from that panel branch multiple command lanes labeled Claude CLI, Copilot CLI, Codex CLI, Gemini CLI, OpenCode CLI, and aidiy_hermes. Emphasize aidiy_hermes as a custom Python engine with TUI, provider overlay, and subprocess integration, distinct from the external CLIs. Dark enterprise blueprint style, magenta accent, clear system diagram, no mascots, no fake products.",
      "chips": [
        "3常駐サーバー",
        "Code AI 候補 7",
        "aidiy_hermes 独自実装",
        "subprocess 起動"
      ],
      "metrics": [
        {
          "label": "常駐",
          "value": "3"
        },
        {
          "label": "Code AI",
          "value": "7"
        },
        {
          "label": "Hermes overlay",
          "value": "31"
        }
      ],
      "cards": [
        {
          "title": "常駐サーバー",
          "lines": [
            "`core_main.py` 8091",
            "`apps_main.py` 8092",
            "`backend_mcp/mcp_main.py` 8095"
          ]
        },
        {
          "title": "マルチCLI",
          "lines": [
            "`claude_sdk` / `claude_cli`",
            "`copilot_cli` / `codex_cli` / `gemini_cli` / `opencode_cli`",
            "`aidiy_hermes`"
          ]
        },
        {
          "title": "Hermes engine",
          "lines": [
            "on-demand のコードエージェント CLI",
            "常駐 HTTP サーバーではない",
            "AI コードパネルから subprocess 起動"
          ]
        },
        {
          "title": "独自実装ポイント",
          "lines": [
            "`cli_main.py` が API provider と CLI bridge の両方を扱う",
            "31 の provider overlay と 50 以上の alias",
            "Windows 差分を `*_win.py` へ分離"
          ]
        }
      ],
      "facts": [
        "Code AI の有効値には `claude_sdk`、`claude_cli`、`copilot_cli`、`codex_cli`、`gemini_cli`、`opencode_cli`、`aidiy_hermes` が含まれる。",
        "`backend_hermes` は AiDiy に統合された on-demand のコードエージェント CLI で、常駐 HTTP サーバーではない。",
        "`cli_main.py` の provider は API provider と CLI bridge の両方を扱い、31 の provider overlay と 50 以上の alias を持つ。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "Code AI の有効値は `claude_sdk`、`claude_cli`、`copilot_cli`、`codex_cli`、`gemini_cli`、`opencode_cli`、`aidiy_hermes` を想定します。"
        },
        {
          "source": "backend_hermes/AGENTS.md",
          "text": "`backend_hermes` は AiDiy に統合された on-demand のコードエージェント CLI です。`cli_main.py` の provider は API provider と CLI bridge の両方を扱います。"
        }
      ],
      "short_narration": "3 サーバーと Code CLI で AI を使います。",
      "long_narration": "AiDiy は core_main が 8091 番ポート、apps_main が 8092 番ポート、backend_mcp が 8095 番ポートで常駐する 3 サーバー構成です。AI コードパネルでは claude_sdk、claude_cli、copilot_cli、codex_cli、gemini_cli、opencode_cli、そして aidiy_hermes まで、複数の Code CLI を 6 スロットに割り当てて使い分けられます。backend_hermes は HTTP サーバーとして常駐せず、AI コードパネルから必要なときだけ subprocess で呼び出される on-demand なコードエージェントです。31 の provider overlay と 50 以上のエイリアスを持つ AiDiy 専用の CLI エンジンになっています。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_start_sec": 14.976,
      "short_duration_sec": 3.696,
      "long_start_sec": 88.656,
      "long_duration_sec": 42.36
    },
    {
      "id": "scene_004",
      "title": "業務サンプルと命名規則",
      "expression": "neutral",
      "accent": "#ffbf47",
      "accent_soft": "rgba(255, 191, 71, 0.18)",
      "kicker": "BUSINESS PATTERNS",
      "headline": "配車・生産・在庫を\n実装パターンごと持っている",
      "lead": "AiDiy は見た目だけのデモではなく、業務サンプルと命名規則をセットで持つテンプレートです。",
      "subtitle": "サンプル名と実装パターンが一致しているので、横展開しやすい。",
      "image": "images/scene_004.png",
      "image_prompt": "Vertical 2:3 collage of Japanese business software modules for dispatch, production, inventory, with clean enterprise dashboards and taxonomy badges C M T V S A X, warm amber accent, realistic ERP style, precise and practical, no cartoon look",
      "chips": [
        "C / M / T / V / S / A / X",
        "明細型パターン",
        "JOIN / 集計 V系",
        "Scheduler 付き"
      ],
      "metrics": [
        {
          "label": "接頭辞",
          "value": "7"
        },
        {
          "label": "業務例",
          "value": "3"
        },
        {
          "label": "明細型",
          "value": "単一表"
        }
      ],
      "cards": [
        {
          "title": "接頭辞",
          "lines": [
            "C=Core / Common",
            "M=Master, T=Transaction",
            "V=View endpoint, S=Scheduler"
          ]
        },
        {
          "title": "業務サンプル",
          "lines": [
            "配車管理",
            "生産管理",
            "資材在庫管理"
          ]
        },
        {
          "title": "明細型",
          "lines": [
            "`明細SEQ=0` がヘッダー",
            "`明細SEQ>=1` が明細",
            "`M商品構成` と `T生産` が代表例"
          ]
        },
        {
          "title": "V系の実態",
          "lines": [
            "DB VIEW ではない",
            "Router 内の生 SQL JOIN / 集計",
            "`V商品推移表` など"
          ]
        }
      ],
      "facts": [
        "配車管理は `M配車区分`、`M車両`、`T配車`、`V配車`、`S配車_*` で構成される。",
        "生産管理は `M商品構成` と `T生産` を含み、明細型パターンの実例になっている。",
        "V系は DB VIEW オブジェクトではなく、生 SQL による JOIN / 集計エンドポイント。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "テーブル命名規則として C / M / T / V / S / A / X が定義されています。"
        },
        {
          "source": "AGENTS.md",
          "text": "業務サンプル概要として、配車管理、生産管理、資材在庫管理が明示されています。"
        }
      ],
      "short_narration": "C・M・T の接頭辞で役割を分け、横展開します。",
      "long_narration": "AiDiy の業務サンプルは、配車管理、生産管理、在庫管理など実務に近い内容で構成されています。テーブルには C、M、T、V、S、A、X の接頭辞があり、それぞれ共通、マスタ、トランザクション、ビュー、スケジューラ、AI 系、実験系を表します。M 系 9 テーブル、T 系 5 テーブル、S 系 4 エンドポイントが実装済みで、明細型パターンも最初から実例付きです。V 系はデータベースの VIEW オブジェクトではなく、Router ファイルに直接書く生 SQL による JOIN エンドポイントです。この命名規則に沿えば、新機能を既存パターンへ横展開しやすくなっています。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_start_sec": 18.672,
      "short_duration_sec": 5.016,
      "long_start_sec": 131.016,
      "long_duration_sec": 41.352
    },
    {
      "id": "scene_005",
      "title": "AIコアとアバター",
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123, 140, 255, 0.18)",
      "kicker": "AI CORE + AVATAR",
      "headline": "チャット、音声、画像、コード支援を\nアバター体験までつなぐ",
      "lead": "AiDiy の AI コアは多パネル UI で、frontend_avatar は Electron と Web の両方に対応します。",
      "subtitle": "AIコアの多パネル体験を、VRM アバターまで含めて運用できる。",
      "image": "images/scene_005.png",
      "image_prompt": "Vertical 2:3 interface illustration of AI core with chat panel, voice waveform, image panel, code panels, and a realistic VRM style avatar beside them, dual mode idea of web and desktop, blue-violet accent, professional Japanese software interface aesthetic",
      "chips": [
        "CHAT_AI_NAME",
        "LIVE_AI_NAME",
        "CODE_AI1〜6",
        "VRM / VRMA"
      ],
      "metrics": [
        {
          "label": "Code パネル",
          "value": "6"
        },
        {
          "label": "UI モード",
          "value": "2"
        },
        {
          "label": "同期",
          "value": "BroadcastChannel"
        }
      ],
      "cards": [
        {
          "title": "AIコア",
          "lines": [
            "テキスト、音声、画像、ファイル、コード支援を統合",
            "`CHAT_AI_NAME` / `LIVE_AI_NAME`",
            "`CODE_AI1_NAME`〜`CODE_AI6_NAME`"
          ]
        },
        {
          "title": "Avatar Web",
          "lines": [
            "左アバター + 右タブ",
            "Web モードは `sessionStorage`",
            "role / query で画面を表現"
          ]
        },
        {
          "title": "Avatar Electron",
          "lines": [
            "複数 BrowserWindow",
            "Electron モードは `localStorage`",
            "`window.desktopApi` で判定"
          ]
        },
        {
          "title": "3D / 同期",
          "lines": [
            "Three.js + `@pixiv/three-vrm`",
            "`public/vrm/` と `public/vrma/`",
            "`avatar-desktop-sync` で状態同期"
          ]
        }
      ],
      "facts": [
        "AIコアは WebSocket + マルチベンダー AI + Code CLI パネルを統合する。",
        "frontend_avatar は Electron デスクトップアプリと通常 Web ブラウザの両方で動作する。",
        "Electron / Web 間の状態同期は BroadcastChannel `avatar-desktop-sync` を使う。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "AIコアは、テキスト、音声、画像、ファイル、コード支援を統合する多パネル UI です。"
        },
        {
          "source": "frontend_avatar/AGENTS.md",
          "text": "`frontend_avatar` は AIコア専用の Avatar クライアントで、Electron と Web の両対応です。"
        }
      ],
      "short_narration": "AI コア、音声、コード支援、VRM アバターを統合しています。",
      "long_narration": "AI コアはチャット、ライブ、コード支援、音声処理の 4 モードを WebSocket で統合しています。frontend_avatar は Electron デスクトップアプリと通常の Web ブラウザの両方で動作する AI アバタークライアントです。VRM モデルと VRMA モーションで表情と動きを制御し、アバター、xneko、xeyes、アナログ時計、デジタル時計、カレンダー、表示無しの 7 種類の表示を選択できます。Electron と Web の間のパネル表示やセッション状態は BroadcastChannel の avatar-desktop-sync で同期します。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_start_sec": 23.688,
      "short_duration_sec": 5.352,
      "long_start_sec": 172.368,
      "long_duration_sec": 35.136
    },
    {
      "id": "scene_006",
      "title": "Code CLI と Hermes",
      "expression": "neutral",
      "accent": "#ff8a6b",
      "accent_soft": "rgba(255, 138, 107, 0.18)",
      "kicker": "MULTI CODE CLI",
      "headline": "ひとつの AI に固定せず、\n用途ごとに相棒を切り替える",
      "lead": "AiDiy は code1〜code6 パネルへ複数の Code AI を流し込み、独自 CLI の aidiy_hermes まで含めて運用します。",
      "subtitle": "複数 CLI を使い分ける設計そのものが、AiDiy の実態。",
      "image": "images/scene_006.png",
      "image_prompt": "Vertical 2:3 multi terminal development workspace poster, several clean command panels for Claude Copilot Codex Gemini OpenCode Hermes, labels as tool lanes rather than logos, warm orange accent, professional code operations environment, realistic developer desk mood",
      "chips": [
        "claude_sdk",
        "claude_cli",
        "copilot_cli",
        "codex_cli",
        "gemini_cli",
        "opencode_cli",
        "aidiy_hermes"
      ],
      "metrics": [
        {
          "label": "有効値",
          "value": "7"
        },
        {
          "label": "code パネル",
          "value": "6"
        },
        {
          "label": "provider overlay",
          "value": "31+"
        }
      ],
      "cards": [
        {
          "title": "Code AI 候補",
          "lines": [
            "root AGENTS に 7 つの有効値",
            "code1〜code6 に割当",
            "用途別に切替"
          ]
        },
        {
          "title": "aidiy_hermes",
          "lines": [
            "on-demand のコードエージェント CLI",
            "常駐 HTTP サーバーではない",
            "`backend_server` から subprocess 呼び出し"
          ]
        },
        {
          "title": "Hermes の幅",
          "lines": [
            "31 の provider overlay",
            "50 以上のエイリアス",
            "`prompt_toolkit` ベース TUI"
          ]
        }
      ],
      "facts": [
        "Code AI の有効値として `claude_sdk`〜`aidiy_hermes` が想定されている。",
        "`backend_hermes` は `_start.py` の常駐起動対象ではない。",
        "`aidiy_hermes` は `backend_server/AIコア/AIコード_cli.py` から subprocess で起動される。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "Code AI の有効値は `claude_sdk`、`claude_cli`、`copilot_cli`、`codex_cli`、`gemini_cli`、`opencode_cli`、`aidiy_hermes` を想定します。"
        },
        {
          "source": "backend_hermes/AGENTS.md",
          "text": "`aidiy_hermes` は AiDiy に統合された on-demand のコードエージェント CLI です。"
        }
      ],
      "short_narration": "Claude、Copilot、Codex などを目的別に切り替えます。",
      "long_narration": "Code AI は code1 から code6 の 6 スロットに異なる CLI を割り当てられます。有効な設定値は claude_sdk、claude_cli、copilot_cli、codex_cli、gemini_cli、opencode_cli、そして aidiy_hermes です。backend_hermes は _start.py の常駐起動対象ではなく、backend_server の AIコード_cli.py から必要なときだけ subprocess で起動される on-demand なエージェントです。31 の provider と多くのスラッシュコマンドを持ち、/model コマンドで対話的に AI を切り替えられます。",
      "short_audio": "audio/short_scene_006.mp3",
      "long_audio": "audio/long_scene_006.mp3",
      "short_start_sec": 29.04,
      "short_duration_sec": 4.824,
      "long_start_sec": 207.504,
      "long_duration_sec": 35.448
    },
    {
      "id": "scene_007",
      "title": "MCP Hub × 13",
      "expression": "neutral",
      "accent": "#00e0b8",
      "accent_soft": "rgba(0, 224, 184, 0.18)",
      "kicker": "MCP HUB",
      "headline": "観測・生成・検証を\nAI エージェントの手足にする",
      "lead": "backend_mcp は port 8095 上に 13 個の MCP を同居させ、ブラウザ操作から音声合成、OBS、ffmpeg まで扱います。",
      "subtitle": "MCP は飾りではなく、AI の観測・生成・検証を支える実働ツール群。",
      "image": "images/scene_007.png",
      "image_prompt": "Vertical 2:3 MCP hub infographic poster, center AI agent node with thirteen connected utility nodes for browser, desktop, sqlite, postgres, logs, code check, backup, image, speech, OBS, ffmpeg, clean green-cyan enterprise network diagram, modern technical style",
      "chips": [
        "FastMCP",
        "port 8095",
        "localhost 限定",
        "read-only 中心"
      ],
      "metrics": [
        {
          "label": "MCP",
          "value": "13"
        },
        {
          "label": "カテゴリ",
          "value": "3"
        },
        {
          "label": "Chrome CDP",
          "value": "Python 実装"
        }
      ],
      "cards": [
        {
          "title": "観測",
          "lines": [
            "`aidiy_chrome_devtools`",
            "`aidiy_desktop_capture`",
            "`aidiy_sqlite` / `aidiy_postgres` / `aidiy_logs`"
          ]
        },
        {
          "title": "検証・保全",
          "lines": [
            "`aidiy_code_check`",
            "`aidiy_backup_check`",
            "`aidiy_backup_save`"
          ]
        },
        {
          "title": "生成・制御",
          "lines": [
            "`aidiy_image_generation`",
            "`aidiy_speech_to_text` / `aidiy_text_to_speech`",
            "`aidiy_obs_studio_control` / `aidiy_ffmpeg_control`"
          ]
        }
      ],
      "facts": [
        "`backend_mcp` は 13 個の MCP サーバーを同居させる FastMCP アプリケーション。",
        "Chrome DevTools は Node.js 版ではなく Python 実装の CDP client を使う。",
        "SQLite / PostgreSQL は read-only 中心で扱い、アクセスは localhost 限定。"
      ],
      "evidence": [
        {
          "source": "backend_mcp/AGENTS.md",
          "text": "`backend_mcp` はポート 8095 上で 13 個の MCP サーバーを同居させる FastMCP アプリケーションです。"
        },
        {
          "source": "backend_mcp/AGENTS.md",
          "text": "ブラウザ操作、DB確認、ログ確認、コードチェック、画像生成、音声認識/合成、OBS / ffmpeg 制御を AI エージェントから利用できます。"
        }
      ],
      "short_narration": "13 個の MCP が支援し、この動画も AI と MCP で自動生成しています。",
      "long_narration": "backend_mcp はポート 8095 に 13 個の MCP サーバーを同居させた FastMCP アプリケーションです。ブラウザ操作、デスクトップキャプチャ、SQLite と PostgreSQL のデータベース参照、ログ観測、コードチェック、バックアップ管理、画像生成、音声認識、音声合成、OBS Studio 制御、FFmpeg 制御と、幅広いツールを AI エージェントに提供します。この紹介ビデオ自体も、台本調整、TTS 音声合成、尺計測、素材確認を AI と MCP で自動生成しています。SSE エンドポイントは http://localhost:8095/{name}/sse の形式で、Claude Agent SDK や Claude Code CLI から接続できます。Chrome DevTools は Node.js ではなく Python 純正の CDP クライアントで実装されています。",
      "short_audio": "audio/short_scene_007.mp3",
      "long_audio": "audio/long_scene_007.mp3",
      "short_start_sec": 33.864,
      "short_duration_sec": 6.192,
      "long_start_sec": 242.952,
      "long_duration_sec": 57.984
    },
    {
      "id": "scene_008",
      "title": "ナレッジと入口",
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196, 155, 255, 0.18)",
      "kicker": "KNOWLEDGE FIRST",
      "headline": "HowTo は knowledge、\n全体像は AGENTS に分けて残す",
      "lead": "AiDiy の紹介を正確に作り直すなら、まず AGENTS.md と .aidiy/knowledge/_index.md を見る、というルール自体が明文化されています。",
      "subtitle": "この紹介ページは、knowledge-first ルールに沿って、根拠付きで組み直しています。",
      "image": "images/scene_008.png",
      "image_prompt": "Vertical 2:3 documentation architecture poster, AGENTS markdown overview linked to knowledge index and implementation files, structured documentation flow, elegant purple accent, realistic technical documentation art, clean folders and file cards, enterprise development handbook aesthetic",
      "chips": [
        ".aidiy/knowledge/_index.md",
        "各サブプロジェクト AGENTS.md",
        "docs/",
        "X自己紹介"
      ],
      "metrics": [
        {
          "label": "入口",
          "value": "knowledge"
        },
        {
          "label": "概要",
          "value": "AGENTS"
        },
        {
          "label": "紹介資料",
          "value": "public/X自己紹介"
        }
      ],
      "cards": [
        {
          "title": "knowledge",
          "lines": [
            "HowTo、判断基準、確認方法を集約",
            "最初の入口は `_index.md`",
            "作業ログ置き場ではない"
          ]
        },
        {
          "title": "AGENTS",
          "lines": [
            "全体方針とアーキテクチャの入口",
            "各サブプロジェクトの概要",
            "一時メモは追記しない"
          ]
        },
        {
          "title": "人向け入口",
          "lines": [
            "`frontend_web/public/X自己紹介/index.html`",
            "`frontend_web` / `frontend_avatar` / `backend_*` の AGENTS",
            "`docs/` の詳細ガイド"
          ]
        }
      ],
      "facts": [
        "ファイル操作や実装作業を伴う場合は、まず `.aidiy/knowledge/_index.md` を確認する。",
        "HowTo、検証手順、失敗対処は AGENTS.md ではなく `.aidiy/knowledge/` に置く。",
        "人間向けの紹介資料は `frontend_web/public/X自己紹介/index.html`。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "ファイル操作や実装作業を伴う場合は、まず `.aidiy/knowledge/_index.md` を確認してください。"
        },
        {
          "source": ".aidiy/knowledge/_index.md",
          "text": "残す内容は、次回の修正で使える HowTo、判断基準、注意点、確認方法だけにします。"
        }
      ],
      "short_narration": "AGENTS.md と knowledge に知見を蓄積します。",
      "long_narration": "AiDiy の実装を始める前に必ず確認すべき入口が 2 つあります。AGENTS.md は全体のアーキテクチャと設計方針を記述したファイルで、.aidiy/knowledge/_index.md は全 HowTo の入口です。新機能を追加するときも、バグを修正するときも、まずこの 2 つを確認することがルールとして明文化されています。HowTo や検証手順、失敗の対処法は AGENTS.md ではなく .aidiy/knowledge/ に置くという分担も決まっています。",
      "short_audio": "audio/short_scene_008.mp3",
      "long_audio": "audio/long_scene_008.mp3",
      "short_start_sec": 40.056,
      "short_duration_sec": 4.056,
      "long_start_sec": 300.936,
      "long_duration_sec": 31.656
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
      "headline": "ご視聴ありがとうございました。\nあなたなら AiDiy でなにを創りますか？",
      "lead": "Web UI、Avatar、Backend、MCP、Hermes まで、AiDiy には一緒に試しながら形にできる部品がそろっています。",
      "subtitle": "あなたなら AiDiy でなにを創りますか？",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "image": "images/scene_999.png",
      "image_prompt": "Square 1:1 ending visual for AiDiy based on the reference image. Keep the composition very simple and elegant. Main content should be only beautiful typography reading 'Thank you for Watching' in a refined luxury tech style, dark blue gradient background, subtle violet glow, clean centered layout, premium and readable, no extra UI, no character, no clutter. Use the reference image's mood and typographic feeling, but regenerate as a polished square closing card suitable for a product introduction ending.",
      "short_narration": "ご視聴ありがとうございました。あなたなら AiDiy で何を創りますか。",
      "long_narration": "ご視聴ありがとうございました。AiDiy には Web UI、アバタークライアント、バックエンド、MCP ハブ、独自 CLI エージェントまで、業務システムと AI 実験基盤をひとつにまとめた部品がそろっています。日本語ファースト設計と豊富な業務サンプルを足がかりに、あなたの業務に合わせてカスタマイズしてみてください。あなたなら AiDiy で、なにを創りますか。",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_start_sec": 44.112,
      "short_duration_sec": 5.424,
      "long_start_sec": 332.592,
      "long_duration_sec": 24.48
    }
  ],
  "short_duration_sec": 49.536,
  "long_duration_sec": 357.072
};
