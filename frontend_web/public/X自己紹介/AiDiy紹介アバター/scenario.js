window.SCENARIO = {
  "project_name": "AiDiy自己紹介",
  "version": "avatar",
  "title": "AiDiy - アバター自己紹介",
  "source": {
    "type": "agents_and_knowledge",
    "summary": "AiDiy の実装実態を AGENTS.md と .aidiy/knowledge から抜粋し、アバタープレゼンター形式で再構成する。"
  },
  "target": {
    "language": "ja-JP",
    "duration_sec": 90.912,
    "format": "html_avatar_presenter_with_media",
    "tone": "事実ベース、簡潔、根拠付き",
    "goal": "AiDiy の実態を、アバターが語るプレゼンター形式で正確に伝える。"
  },
  "assets_policy": {
    "visual_style": "left_avatar_40_right_content_60",
    "audio_dir": "../AiDiy紹介ビデオtake4/audio",
    "image_dir": "../AiDiy紹介ビデオtake4/images",
    "avatar": "../AiDiy_Sample_M.vrm"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "この紹介で話すこと",
      "start_sec": 0.0,
      "duration_sec": 11.616,
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "background_word": "",
      "kicker": "INTRODUCTION",
      "headline": "この紹介では、AiDiy の全体像と\n設計の考え方を紹介します",
      "lead": "日本語ファースト設計、3常駐サーバー + 1 CLI、業務サンプル、AI コア、MCP、knowledge の入口までを短く見ていきます。",
      "subtitle": "この紹介では、AiDiy の全体像、設計方針、業務サンプル、AI・MCP 連携を紹介します。",
      "narration": "この動画では、AiDiy の全体像と設計の考え方を紹介します。日本語ファースト設計、業務サンプル、AI コア、MCP、ナレッジの入口まで、実装に沿って見ていきます。",
      "image": "images/scene_000.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "audio": "audio/scene_000.mp3"
    },
    {
      "id": "scene_001",
      "title": "AiDiyとは",
      "start_sec": 11.616,
      "duration_sec": 11.088,
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.18)",
      "kicker": "PROJECT OVERVIEW",
      "headline": "日本語ファーストの\nフルスタック業務管理テンプレート",
      "lead": "FastAPI + SQLite + Vue 3 を軸に、業務システム実装例と AI 実験基盤をひとつにまとめたのが AiDiy です。",
      "subtitle": "日本語識別子と業務サンプルを土台に、AI / 音声 / MCP まで一体化した基盤。",
      "narration": "AiDiy は、日本語を第一言語にしたフルスタック業務管理テンプレートです。FastAPI と SQLite と Vue 3 を軸に、業務サンプルと AI 実験基盤をひとつにまとめます。",
      "image": "images/scene_001.png",
      "audio": "audio/scene_001.mp3",
      "chips": [
        "日本語識別子",
        "FastAPI + SQLite + Vue 3",
        "3常駐サーバー + 1 CLI",
        "業務サンプル同梱"
      ],
      "metrics": [
        { "label": "常駐サーバー", "value": "3" },
        { "label": "MCP", "value": "13" },
        { "label": "Code AI 候補", "value": "7" }
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
      ]
    },
    {
      "id": "scene_002",
      "title": "日本語ファースト設計",
      "start_sec": 22.704,
      "duration_sec": 10.152,
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125, 255, 179, 0.18)",
      "kicker": "JAPANESE FIRST",
      "headline": "DB / API / UI / Code を\n日本語で一直線につなぐ",
      "lead": "AiDiy では業務語彙と実装名をできるだけ一致させ、日本語話者がコードと画面を直接対応づけられるようにしています。",
      "subtitle": "業務語彙と実装名を揃え、読めるまま保守できる構成。",
      "narration": "画面、URL、JSON、コード識別子まで日本語を原則にし、業務語彙と実装名をまっすぐ対応づけます。だから設計意図を日本語のまま保守へ持ち込めます。",
      "image": "images/scene_002.png",
      "audio": "audio/scene_002.mp3",
      "chips": [
        "UTF-8 固定",
        "URL も日本語",
        "JSON キーも日本語",
        "一般名 request/query は英字可"
      ],
      "metrics": [
        { "label": "例レイヤー", "value": "4" },
        { "label": "原則", "value": "一致重視" }
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
      ]
    },
    {
      "id": "scene_003",
      "title": "3常駐サーバー + マルチCLI",
      "start_sec": 32.856,
      "duration_sec": 16.776,
      "expression": "neutral",
      "accent": "#ff6bd6",
      "accent_soft": "rgba(255, 107, 214, 0.18)",
      "kicker": "ARCHITECTURE",
      "headline": "複数の CLI を並べて使い、\nHermes は独自エンジンでつなぐ",
      "lead": "AiDiy は Core / Apps / MCP を常駐分離しつつ、AIコアの Code AI では複数 CLI を切り替えられます。backend_hermes はその中でも AiDiy 専用に組み込まれた独自実装です。",
      "subtitle": "Code AI はひとつではなく、複数CLI + 独自実装 Hermes を切り替える。",
      "narration": "AiDiy の Code AI は、Claude や Copilot や Codex や Gemini や OpenCode など複数の CLI を切り替えて使えます。その上で backend_hermes は、AiDiy 専用に組み込まれた on-demand の独自コードエージェントで、AI コードパネルから subprocess で起動されます。",
      "image": "images/scene_003.png",
      "audio": "audio/scene_003.mp3",
      "chips": [
        "3常駐サーバー",
        "Code AI 候補 7",
        "aidiy_hermes 独自実装",
        "subprocess 起動"
      ],
      "metrics": [
        { "label": "常駐", "value": "3" },
        { "label": "Code AI", "value": "7" },
        { "label": "Hermes overlay", "value": "31" }
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
      ]
    },
    {
      "id": "scene_004",
      "title": "業務サンプルと命名規則",
      "start_sec": 49.632,
      "duration_sec": 14.76,
      "expression": "neutral",
      "accent": "#ffbf47",
      "accent_soft": "rgba(255, 191, 71, 0.18)",
      "kicker": "BUSINESS PATTERNS",
      "headline": "配車・生産・在庫を\n実装パターンごと持っている",
      "lead": "AiDiy は見た目だけのデモではなく、業務サンプルと命名規則をセットで持つテンプレートです。",
      "subtitle": "サンプル名と実装パターンが一致しているので、横展開しやすい。",
      "narration": "C、M、T、V、S、A、X の接頭辞と、配車、生産、在庫の実務サンプルがあるので、新機能を既存パターンに沿って横展開できます。明細型パターンも最初から実例付きです。",
      "image": "images/scene_004.png",
      "audio": "audio/scene_004.mp3",
      "chips": [
        "C / M / T / V / S / A / X",
        "明細型パターン",
        "JOIN / 集計 V系",
        "Scheduler 付き"
      ],
      "metrics": [
        { "label": "接頭辞", "value": "7" },
        { "label": "業務例", "value": "3" },
        { "label": "明細型", "value": "単一表" }
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
      ]
    },
    {
      "id": "scene_005",
      "title": "AIコアとアバター",
      "start_sec": 64.392,
      "duration_sec": 13.2,
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123, 140, 255, 0.18)",
      "kicker": "AI CORE + AVATAR",
      "headline": "チャット、音声、画像、コード支援を\nアバター体験までつなぐ",
      "lead": "AiDiy の AI コアは多パネル UI で、frontend_avatar は Electron と Web の両方に対応します。",
      "subtitle": "AIコアの多パネル体験を、VRM アバターまで含めて運用できる。",
      "narration": "AIコアはチャット、音声、画像、ファイル、コード支援を統合し、frontend_avatar は Electron と Web の両方で VRM アバター体験を支えます。状態同期には BroadcastChannel を使います。",
      "image": "images/scene_005.png",
      "audio": "audio/scene_005.mp3",
      "chips": [
        "CHAT_AI_NAME",
        "LIVE_AI_NAME",
        "CODE_AI1〜6",
        "VRM / VRMA"
      ],
      "metrics": [
        { "label": "Code パネル", "value": "6" },
        { "label": "UI モード", "value": "2" },
        { "label": "同期", "value": "BroadcastChannel" }
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
      ]
    },
    {
      "id": "scene_999",
      "title": "ご視聴ありがとうございました",
      "start_sec": 77.592,
      "duration_sec": 13.32,
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
      "narration": "ご視聴ありがとうございました。AiDiy には、ウェブ、アバター、バックエンド、MCP まで、一緒に試しながら形にできる部品がそろっています。あなたなら AiDiy で、なにを創りますか。",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "image": "images/scene_999.png",
      "audio": "audio/scene_999.mp3"
    }
  ],
  "duration_sec": 90.912
}
