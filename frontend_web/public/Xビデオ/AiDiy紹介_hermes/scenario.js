window.SCENARIO = {
  "project_name": "AiDiy紹介hermes",
  "version": "hermes",
  "title": "AiDiy Hermes - コードエージェント CLI 紹介",
  "source": {
    "type": "agents_and_knowledge",
    "summary": "backend_hermes/AGENTS.md と .aidiy/knowledge から実装実態を抜粋して構成。"
  },
  "target": {
    "language": "ja-JP",
    "duration_sec": 95.52,
    "format": "html_css_scene_player_with_media",
    "tone": "事実ベース、簡潔、根拠付き",
    "goal": "aidiy_hermes の位置づけ・Provider・Slash Command・AiDiy 連携を正確に伝える。"
  },
  "assets_policy": {
    "visual_style": "left_avatar_38_right_content_62",
    "audio_dir": "audio",
    "image_dir": "images",
    "avatar": "vrm/AiDiy_Sample_M.vrm"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "この動画で紹介すること",
      "start_sec": 0.0,
      "duration_sec": 11.304,
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196,155,255,0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "INTRODUCTION",
      "headline": "この動画では、aidiy_hermes の\n位置づけと使い方を紹介します",
      "lead": "位置づけ・起動方式、技術スタック、31 Provider、60 Slash Command、AiDiy 連携までを短く見ていきます。",
      "subtitle": "この動画では、aidiy_hermes の位置づけ、技術、Provider、Slash Command、AiDiy 連携を紹介します。",
      "narration": "この動画では、AiDiy 専用のコードエージェント CLI、aidiy_hermes を紹介します。位置づけ、技術スタック、Provider、Slash Command、そして AiDiy との連携まで、短く見ていきます。",
      "image": "images/scene_000.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "audio": "audio/scene_000.mp3",
      "short_narration": "aidiy_hermes は AiDiy 専用のコードエージェント CLI です。必要なときだけ起動する on-demand 型です。",
      "long_narration": "この動画では、AiDiy 専用のコードエージェント CLI、aidiy_hermes を紹介します。HTTP サーバーとして常駐しない独自の位置づけ、技術スタック、31 の AI Provider 対応、60 の Slash Command、そして AiDiy システムとの連携まで、見ていきます。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 8.784,
      "long_start_sec": 0.0,
      "long_duration_sec": 18.96
    },
    {
      "id": "scene_001",
      "title": "位置づけと起動方式",
      "start_sec": 11.304,
      "duration_sec": 11.136,
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41,216,255,0.18)",
      "kicker": "AGENT CLI",
      "headline": "常駐しない、\n呼ばれたとき動くエージェント",
      "lead": "aidiy_hermes は HTTP サーバーとして常駐せず、AiDiy のコードパネルから subprocess で呼び出される on-demand な実行体です。",
      "subtitle": "常駐しない。コードパネルから subprocess で起動される on-demand CLI。",
      "narration": "aidiy_hermes は常駐 HTTP サーバーではありません。_start.py の起動対象でもない。AiDiy の AI コードパネルが必要なときだけ subprocess で呼び出す、on-demand なコードエージェント CLI です。",
      "image": "images/scene_001.png",
      "audio": "audio/scene_001.mp3",
      "chips": [
        "on-demand",
        "subprocess 起動",
        "_start.py 非対象",
        "_setup.py 対象"
      ],
      "metrics": [
        {
          "label": "常駐",
          "value": "なし"
        },
        {
          "label": "実行名",
          "value": "aidiy_hermes"
        },
        {
          "label": "起動元",
          "value": "AIコード_cli.py"
        }
      ],
      "cards": [
        {
          "title": "位置づけ",
          "lines": [
            "常駐 HTTP サーバーではない",
            "`_start.py` の常駐起動対象ではない",
            "`_setup.py` / `_cleanup.py` の対象"
          ]
        },
        {
          "title": "起動方式",
          "lines": [
            "AiDiy コードパネル → subprocess",
            "`CODE_AI*_NAME = \"aidiy_hermes\"` で呼び出し",
            "単体 CLI としても直接実行可能"
          ]
        }
      ],
      "facts": [
        "`backend_hermes` は常駐 HTTP サーバーではない。",
        "`_start.py` の常駐起動対象ではない。",
        "`backend_server/AIコア/AIコード_cli.py` から subprocess で起動される。"
      ],
      "evidence": [
        {
          "source": "backend_hermes/AGENTS.md",
          "text": "`backend_hermes` は AiDiy に統合された on-demand のコードエージェント CLI です。常駐 HTTP サーバーではない。"
        },
        {
          "source": "backend_hermes/AGENTS.md",
          "text": "`_start.py` の常駐起動対象ではない。`_setup.py` / `_cleanup.py` の対象。"
        }
      ],
      "short_narration": "HTTP サーバーとして常駐しない on-demand 型の CLI エージェントです。_start.py の起動対象にはなりません。",
      "long_narration": "aidiy_hermes は HTTP サーバーとして常駐しません。_start.py の起動対象でもありません。AiDiy の AI コードパネルが必要なときだけ、backend_server の AIコード_cli.py が subprocess として呼び出す、on-demand なコードエージェント CLI です。単体で cli_main.py を直接起動してコマンドラインから動かすこともできます。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_start_sec": 8.784,
      "short_duration_sec": 8.904,
      "long_start_sec": 18.96,
      "long_duration_sec": 25.344
    },
    {
      "id": "scene_002",
      "title": "技術スタックと構成",
      "start_sec": 22.44,
      "duration_sec": 13.464,
      "expression": "neutral",
      "accent": "#00e0b8",
      "accent_soft": "rgba(0,224,184,0.18)",
      "kicker": "TECH STACK",
      "headline": "Python + prompt_toolkit で\n作られた TUI エージェント",
      "lead": "cli_main.py を起点に、core/ ・ base/ ・ hermes_cli/ ・ tools/ ・ skills/ の5層で構成されます。",
      "subtitle": "cli_main.py が起点。5 層構成で provider・TUI・tools を分担。",
      "narration": "aidiy_hermes は Python で実装されており、TUI には prompt_toolkit を使います。cli_main.py がエントリで、core、base、hermes_cli、tools、skills の5層で役割を分担します。",
      "image": "images/scene_002.png",
      "audio": "audio/scene_002.mp3",
      "chips": [
        "Python",
        "prompt_toolkit",
        "requests / httpx",
        "OpenAI 互換 / Claude API"
      ],
      "metrics": [
        {
          "label": "エントリ",
          "value": "cli_main.py"
        },
        {
          "label": "通信",
          "value": "4 クライアント"
        },
        {
          "label": "実行方式",
          "value": "CLI / subprocess"
        }
      ],
      "cards": [
        {
          "title": "TUI 基盤",
          "lines": [
            "`prompt_toolkit` ベース",
            "slash command 補完",
            "spinner / 色表示対応"
          ]
        },
        {
          "title": "ディレクトリ構成",
          "lines": [
            "`cli_main.py` — CLI エントリ、provider/model picker",
            "`core/` — agent loop、display、retry",
            "`base/` — 定数、utils、toolsets"
          ]
        },
        {
          "title": "tools / skills",
          "lines": [
            "`tools/` — file / terminal / web / media / planning",
            "`hermes_cli/` — slash command、TUI 補助",
            "`skills/` / `optional-skills/` — skill 資産"
          ]
        }
      ],
      "facts": [
        "TUI は `prompt_toolkit` で実装されている。",
        "通信は `requests`、`httpx`、OpenAI 互換 client、Claude API 連携の4種。",
        "ディレクトリ構成は `cli_main.py`, `core/`, `base/`, `hermes_cli/`, `tools/`, `skills/` 。"
      ],
      "evidence": [
        {
          "source": "backend_hermes/AGENTS.md",
          "text": "TUI: `prompt_toolkit`。通信: `requests`、`httpx`、OpenAI 互換 client、Claude API 連携。"
        },
        {
          "source": "backend_hermes/AGENTS.md",
          "text": "`cli_main.py` — CLI エントリ、provider/model picker、slash command 処理。"
        }
      ],
      "short_narration": "Python の TUI アプリとして実装された 5 層構成の CLI エージェントです。cli_main.py がエントリポイントで、prompt_toolkit を UI に使います。",
      "long_narration": "aidiy_hermes は Python で実装された TUI アプリケーションです。ユーザーインターフェースには prompt_toolkit を使います。cli_main.py がエントリポイントで、core、base、hermes_cli、tools、skills の 5 層で役割を分担します。AI サービスとの通信は requests、httpx、OpenAI 互換クライアント、Claude API 連携の 4 種類の方法に対応しています。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_start_sec": 17.688,
      "short_duration_sec": 12.312,
      "long_start_sec": 44.304,
      "long_duration_sec": 27.792
    },
    {
      "id": "scene_003",
      "title": "31 Provider Overlay",
      "start_sec": 35.904,
      "duration_sec": 14.16,
      "expression": "neutral",
      "accent": "#ff8a6b",
      "accent_soft": "rgba(255,138,107,0.18)",
      "kicker": "MULTI PROVIDER",
      "headline": "31 の provider overlay と\n50 以上のエイリアス",
      "lead": "OpenRouter、Anthropic、Google、Microsoft、DeepSeek など幅広い AI プロバイダーに対応。`--provider` フラグまたは config / 環境変数で切り替えます。",
      "subtitle": "31 overlays、50+ aliases。auto 検出または --provider で解決。",
      "narration": "hermes_cli/providers.py の HERMES_OVERLAYS に 31 の provider が定義されており、50 以上のエイリアスでフレンドリ名から canonical ID へマッピングします。優先順位は --provider フラグ、config.yaml、環境変数、auto の順です。",
      "image": "images/scene_003.png",
      "audio": "audio/scene_003.mp3",
      "chips": [
        "31 provider overlay",
        "50+ aliases",
        "auto 検出",
        "--provider フラグ"
      ],
      "metrics": [
        {
          "label": "provider overlay",
          "value": "31"
        },
        {
          "label": "alias",
          "value": "50+"
        },
        {
          "label": "選択優先順位",
          "value": "4段階"
        }
      ],
      "cards": [
        {
          "title": "Provider カテゴリ",
          "lines": [
            "汎用 API: `openrouter`, `openai-codex`, `nous`",
            "Anthropic / Google / Microsoft",
            "中国系: `deepseek`, `qwen`, `minimax`, `alibaba` など"
          ]
        },
        {
          "title": "選択優先順位",
          "lines": [
            "1. `--provider` CLI フラグ",
            "2. config.yaml の model.provider",
            "3. `HERMES_INFERENCE_PROVIDER` 環境変数",
            "4. `auto`（runtime 自動検出）"
          ]
        },
        {
          "title": "Interactive Picker",
          "lines": [
            "`/model` を引数なしで起動",
            "Step 1: 認証済み provider 選択",
            "Step 2: curated model 一覧から選択"
          ]
        }
      ],
      "facts": [
        "`hermes_cli/providers.py` の `HERMES_OVERLAYS` で 31 の provider が定義されている。",
        "50 以上のエイリアスが `ALIASES` 辞書に定義されている。",
        "Provider 解決優先順位: `--provider` > config.yaml > `HERMES_INFERENCE_PROVIDER` > `auto`。"
      ],
      "evidence": [
        {
          "source": "backend_hermes/AGENTS.md",
          "text": "31 の provider overlay と 50 以上のエイリアスがあり、`--provider` / config / 環境変数 / `auto` の優先順位で解決します。"
        },
        {
          "source": ".aidiy/knowledge/backend_hermes,Provider一覧と選択ロジック.md",
          "text": "`hermes_cli/providers.py` の `HERMES_OVERLAYS` で 31 の provider が定義されています。"
        }
      ],
      "short_narration": "31 の AI プロバイダーと 50 以上のエイリアスを providers.py の HERMES_OVERLAYS で管理しています。",
      "long_narration": "hermes_cli/providers.py の HERMES_OVERLAYS に 31 の AI Provider が定義されています。OpenRouter、Anthropic、Google、Microsoft、DeepSeek など幅広いサービスをカバーし、ALIASES 辞書に 50 以上のフレンドリ名から canonical ID へのマッピングが定義されています。Provider の解決優先順位は --provider フラグ、config.yaml、HERMES_INFERENCE_PROVIDER 環境変数、auto の順です。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_start_sec": 30.0,
      "short_duration_sec": 8.592,
      "long_start_sec": 72.096,
      "long_duration_sec": 28.272
    },
    {
      "id": "scene_004",
      "title": "60 Slash Commands",
      "start_sec": 50.064,
      "duration_sec": 14.616,
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123,140,255,0.18)",
      "kicker": "TUI COMMANDS",
      "headline": "/model から /kanban まで\n5 カテゴリ 60 コマンド",
      "lead": "セッション管理 23・設定変更 13・ツール操作 11・情報表示 12・終了 1。`/` を入力すると TUI 補完が起動します。",
      "subtitle": "60 slash commands。/ 補完で一覧が出る。",
      "narration": "hermes_cli/commands.py の COMMAND_REGISTRY に 60 の slash command が登録されています。Session、Configuration、Tools and Skills、Info、Exit の5カテゴリに分かれ、/model で provider と model を interactive に切り替えられます。",
      "image": "images/scene_004.png",
      "audio": "audio/scene_004.mp3",
      "chips": [
        "Session 23",
        "Configuration 13",
        "Tools & Skills 11",
        "Info 12"
      ],
      "metrics": [
        {
          "label": "Slash Command",
          "value": "60"
        },
        {
          "label": "カテゴリ",
          "value": "5"
        },
        {
          "label": "/model picker",
          "value": "2段階"
        }
      ],
      "cards": [
        {
          "title": "Session (23)",
          "lines": [
            "`/new`, `/retry`, `/undo`, `/rollback`",
            "`/snapshot`, `/compress`, `/branch`",
            "`/goal`, `/agents`, `/background`"
          ]
        },
        {
          "title": "Configuration (13)",
          "lines": [
            "`/model` — provider + model 切替",
            "`/yolo` — YOLO モード",
            "`/personality`, `/skin`, `/verbose`"
          ]
        },
        {
          "title": "Tools & Skills (11)",
          "lines": [
            "`/tools`, `/toolsets`, `/skills`",
            "`/cron`, `/kanban`, `/browser`",
            "`/reload-mcp`, `/plugins`"
          ]
        }
      ],
      "facts": [
        "`COMMAND_REGISTRY` に 60 の slash command が登録されている（Session 23、Configuration 13、Tools & Skills 11、Info 12、Exit 1）。",
        "`/model` を引数なしで実行すると 2 段階の interactive picker が起動する。",
        "`/` 入力で TUI 補完が起動し、コマンド一覧が表示される。"
      ],
      "evidence": [
        {
          "source": ".aidiy/knowledge/backend_hermes,Slash Command一覧.md",
          "text": "Session 23 コマンド、Configuration 13 コマンド、Tools & Skills 11 コマンド、Info 12 コマンド、Exit 1 コマンド。"
        },
        {
          "source": ".aidiy/knowledge/backend_hermes,Slash Command一覧.md",
          "text": "`COMMAND_REGISTRY` は `CommandDef` dataclass のリストです。正規名 + alias で検索します。"
        }
      ],
      "short_narration": "60 の Slash Command を COMMAND_REGISTRY に登録し対話的に操作できます。/model コマンドで provider と model を 2 段階で選べます。",
      "long_narration": "hermes_cli/commands.py の COMMAND_REGISTRY に 60 の slash command が登録されています。セッション管理 23、設定変更 13、ツール操作 11、情報表示 12、終了 1 の 5 カテゴリに分かれています。スラッシュを入力すると TUI の補完が起動してコマンド一覧が表示されます。/model を引数なしで実行すると provider と model を対話的に選べる 2 段階の interactive picker が起動します。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_start_sec": 38.592,
      "short_duration_sec": 10.872,
      "long_start_sec": 100.368,
      "long_duration_sec": 35.184
    },
    {
      "id": "scene_005",
      "title": "AiDiy システム連携",
      "start_sec": 64.68,
      "duration_sec": 15.624,
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125,255,179,0.18)",
      "kicker": "INTEGRATION",
      "headline": "backend_server が subprocess で起動し、\nconf_model.py がモデル一覧を動的生成",
      "lead": "CODE_AI*_NAME = \"aidiy_hermes\" を設定すると、AI コードパネルが AIコード_cli.py 経由で Hermes を起動します。",
      "subtitle": "CODE_AI*_NAME = aidiy_hermes で AI コードパネルと連携。",
      "narration": "AI コードパネルで CODE_AI アスタリスク NAME を aidiy_hermes に設定すると、backend_server の AIコード_cli.py が Hermes を subprocess で起動します。モデル一覧は conf_model.py が動的生成し、モデル設定は CODE_AIDIY_HERMES_MODEL を使います。",
      "image": "images/scene_005.png",
      "audio": "audio/scene_005.mp3",
      "chips": [
        "CODE_AI*_NAME",
        "subprocess 起動",
        "conf_model.py 動的生成",
        "CODE_AIDIY_HERMES_MODEL"
      ],
      "metrics": [
        {
          "label": "起動元",
          "value": "AIコード_cli.py"
        },
        {
          "label": "設定キー",
          "value": "CODE_AI*_NAME"
        },
        {
          "label": "モデル設定",
          "value": "conf_model.py"
        }
      ],
      "cards": [
        {
          "title": "呼び出し経路",
          "lines": [
            "`CODE_AI*_NAME = \"aidiy_hermes\"` を設定",
            "`backend_server/AIコア/AIコード_cli.py` が subprocess 起動",
            "標準入出力でコードパネルと通信"
          ]
        },
        {
          "title": "設定ファイル",
          "lines": [
            "`backend_server/conf/conf_json.py`",
            "`backend_server/conf/conf_model.py` — モデル一覧動的生成",
            "`CODE_AIDIY_HERMES_MODEL` でモデル指定"
          ]
        },
        {
          "title": "Windows 対応",
          "lines": [
            "`*_win.py` / `*_linux.py` で OS 分岐",
            "file_operations / terminal_tool がセレクタ",
            "POSIX コマンド非依存の実装"
          ]
        }
      ],
      "facts": [
        "`aidiy_hermes` は `backend_server/AIコア/AIコード_cli.py` から subprocess で起動される。",
        "モデル設定は `CODE_AIDIY_HERMES_MODEL` を使い、`conf_model.py` 側で動的生成する。",
        "Windows では `*_win.py`、非 Windows では `*_linux.py` を import するプラットフォームセレクタ構造。"
      ],
      "evidence": [
        {
          "source": "backend_hermes/AGENTS.md",
          "text": "`aidiy_hermes` は `backend_server/AIコア/AIコード_cli.py` から subprocess で起動されます。モデル設定は `CODE_AIDIY_HERMES_MODEL` を使います。"
        },
        {
          "source": "backend_hermes/AGENTS.md",
          "text": "Windows では対応する `*_win.py`、非 Windows では `*_linux.py` のどちらか一方だけを import します。"
        }
      ],
      "short_narration": "AI コードパネルで NAME を aidiy_hermes に設定すると、subprocess で起動して使えます。",
      "long_narration": "AI コードパネルで CODE_AI の NAME を aidiy_hermes に設定すると、backend_server の AIコード_cli.py が Hermes を subprocess で起動します。モデルの設定は CODE_AIDIY_HERMES_MODEL を使い、conf_model.py が動的に一覧を生成します。Windows では _win.py、非 Windows では _linux.py を import するプラットフォームセレクタ構造になっており、OS の差異を吸収しています。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_start_sec": 49.464,
      "short_duration_sec": 6.672,
      "long_start_sec": 135.552,
      "long_duration_sec": 29.304
    },
    {
      "id": "scene_999",
      "title": "ご視聴ありがとうございました",
      "start_sec": 80.304,
      "duration_sec": 15.216,
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196,155,255,0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "AIDIY HERMES",
      "headline": "ご視聴ありがとうございました。\naidiy_hermes で、なにを作りますか？",
      "lead": "on-demand CLI として、31 providers × 60 slash commands × AiDiy 連携。あなたのコード作業をエージェントに任せてみてください。",
      "subtitle": "aidiy_hermes — on-demand、31 providers、60 slash commands。",
      "narration": "ご視聴ありがとうございました。aidiy_hermes は on-demand のコードエージェントとして、31 の provider と 60 の slash command を持ちます。AiDiy のコードパネルからも単体 CLI としても動きます。あなたのコード作業をエージェントに任せてみてください。",
      "image": "images/scene_999.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "audio": "audio/scene_999.mp3",
      "short_narration": "31 プロバイダー・60 コマンド・5 層構成のコードエージェントです。AiDiy の業務開発にぜひ活かしてください。",
      "long_narration": "ご視聴ありがとうございました。aidiy_hermes は on-demand なコードエージェントとして、31 の AI Provider と 60 の Slash Command を持ちます。AiDiy のコードパネルからも、単体の CLI としても動作します。コードを書く作業、調べる作業を AI エージェントに任せてみてください。",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_start_sec": 56.136,
      "short_duration_sec": 7.944,
      "long_start_sec": 164.856,
      "long_duration_sec": 21.792
    }
  ],
  "duration_sec": 95.52,
  "short_duration_sec": 64.08,
  "long_duration_sec": 186.648
};
