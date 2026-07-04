window.SCENARIO = {
  "project_name": "AiDiy紹介hermes",
  "version": "hermes",
  "title": "AiDiy Hermes - コードエージェント CLI 紹介",
  "source": {
    "type": "agents_and_knowledge",
    "summary": "command_hermes/AGENTS.md と .aidiy/knowledge から実装実態を抜粋して構成。"
  },
  "target": {
    "language": "ja-JP",
    "format": "html_css_scene_player_with_media",
    "tone": "事実ベース、簡潔、根拠付き",
    "goal": "aidiy_hermes の位置づけ・Provider・Slash Command・AiDiy 連携を正確に伝える。"
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
      "title": "この動画で紹介すること",
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196,155,255,0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "INTRODUCTION",
      "headline": "この動画では、aidiy_hermes の\n位置づけと使い方を紹介します",
      "lead": "位置づけ・起動方式、技術スタック、31 Provider、60 Slash Command、AiDiy 連携までを短く見ていきます。",
      "subtitle": "この動画では、aidiy_hermes の位置づけ、技術、Provider、Slash Command、AiDiy 連携を紹介します。",
      "image": "images/scene_000.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "short_narration": "aidiy_hermes は本家 hermes-agent の CLI 機能を切り出し、AiDiy 専用に再設計したコードエージェントです。必要なときだけ起動する使い切り型のツールです。",
      "long_narration": "この動画では、AiDiy 専用のコードエージェント、aidiy_hermes を紹介します。aidiy_hermes は本家 hermes-agent の CLI 機能を切り出し、AiDiy 専用に再設計した AI エージェントです。常時起動するサーバーではなく、必要なときだけ呼び出す使い切り型のツールです。Claude や ChatGPT・Gemini など主要な AI サービスに対応し、スラッシュコマンドで操作を制御できます。Windows にもネイティブ対応しています。AiDiy の AI コードパネルと連携して、コードの相談・自動修正・ファイル操作ができます。使い切り型の位置づけ、技術の仕組み、AI への接続、Windows 対応、AiDiy との連携まで順に見ていきます。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_duration_sec": 11.304,
      "long_duration_sec": 43.464
    },
    {
      "id": "scene_001",
      "title": "位置づけと起動方式",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41,216,255,0.18)",
      "kicker": "AGENT CLI",
      "headline": "常駐しない、\n呼ばれたとき動くエージェント",
      "lead": "aidiy_hermes は HTTP サーバーとして常駐せず、AiDiy のコードパネルから subprocess で呼び出される on-demand な実行体です。",
      "subtitle": "常駐しない。コードパネルから subprocess で起動される on-demand CLI。",
      "image": "images/scene_001.png",
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
        "`command_hermes` は常駐 HTTP サーバーではない。",
        "`_start.py` の常駐起動対象ではない。",
        "`backend_server/AIコア/AIコード_cli.py` から subprocess で起動される。"
      ],
      "evidence": [
        {
          "source": "command_hermes/AGENTS.md",
          "text": "`command_hermes` は AiDiy に統合された on-demand のコードエージェント CLI です。常駐 HTTP サーバーではない。"
        },
        {
          "source": "command_hermes/AGENTS.md",
          "text": "`_start.py` の常駐起動対象ではない。`_setup.py` / `_cleanup.py` の対象。"
        }
      ],
      "short_narration": "aidiy_hermes は常時起動するサーバーではなく、AI コードパネルから必要なときだけ呼び出されるコマンドラインツールです。",
      "long_narration": "aidiy_hermes は HTTP サーバーとして常時起動しません。AiDiy のシステム全体を起動したとき、hermes は自動では立ち上がらず、AI コードパネルで必要になった瞬間だけ、バックエンドが内部で subprocess として呼び出す使い切り型のコードエージェントです。この設計のおかげで、使わないときは一切リソースを消費しません。ターミナルから直接 python cli_main.py と入力して、対話モードで手動で動かすこともできます。Windows では Git Bash があれば優先して使い、ない場合は PowerShell でフォールバックします。Linux・Mac ではネイティブシェルを自動で使い分けます。ファイル操作・コマンド実行・ウェブ検索・コード編集など、コード開発に必要な道具が一式揃った状態で起動します。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_duration_sec": 7.848,
      "long_duration_sec": 47.664
    },
    {
      "id": "scene_002",
      "title": "技術スタックと構成",
      "expression": "neutral",
      "accent": "#00e0b8",
      "accent_soft": "rgba(0,224,184,0.18)",
      "kicker": "TECH STACK",
      "headline": "Python + prompt_toolkit で\n作られた TUI エージェント",
      "lead": "cli_main.py を起点に、core/ ・ base/ ・ hermes_cli/ ・ tools/ ・ skills/ の5層で構成されます。",
      "subtitle": "cli_main.py が起点。5 層構成で provider・TUI・tools を分担。",
      "image": "images/scene_002.png",
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
          "source": "command_hermes/AGENTS.md",
          "text": "TUI: `prompt_toolkit`。通信: `requests`、`httpx`、OpenAI 互換 client、Claude API 連携。"
        },
        {
          "source": "command_hermes/AGENTS.md",
          "text": "`cli_main.py` — CLI エントリ、provider/model picker、slash command 処理。"
        }
      ],
      "short_narration": "Python 製のターミナルアプリです。cli_main.py を起点に、5 つの役割に分かれた構造で動きます。",
      "long_narration": "aidiy_hermes は Python で作られたターミナルアプリです。エントリポイントは cli_main.py で、ここから全体の処理が始まります。コードは役割ごとに 5 つのフォルダに整理されています。エージェントのループや推論・リトライを担う core、共通の定数やユーティリティをまとめた base、スラッシュコマンドや TUI 補助の hermes_cli、ファイル・ターミナル・ウェブ・メディアなどのツールをまとめた tools、そして skill 資産の skills です。画面の入力補助には prompt_toolkit というライブラリを使い、コマンドの入力候補や補完が TUI 上でリアルタイムに表示されます。AI サービスとの通信は Claude API・OpenAI 互換クライアント・HTTP リクエストなど複数の方法に対応しています。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_duration_sec": 7.848,
      "long_duration_sec": 47.376
    },
    {
      "id": "scene_003",
      "title": "31 Provider Overlay",
      "expression": "neutral",
      "accent": "#ff8a6b",
      "accent_soft": "rgba(255,138,107,0.18)",
      "kicker": "MULTI PROVIDER",
      "headline": "31 の provider overlay と\n50 以上のエイリアス",
      "lead": "OpenRouter、Anthropic、Google、Microsoft、DeepSeek など幅広い AI プロバイダーに対応。`--provider` フラグまたは config / 環境変数で切り替えます。",
      "subtitle": "31 overlays、50+ aliases。auto 検出または --provider で解決。",
      "image": "images/scene_003.png",
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
          "source": "command_hermes/AGENTS.md",
          "text": "31 の provider overlay と 50 以上のエイリアスがあり、`--provider` / config / 環境変数 / `auto` の優先順位で解決します。"
        },
        {
          "source": ".aidiy/knowledge/command_hermes,Provider一覧と選択ロジック.md",
          "text": "`hermes_cli/providers.py` の `HERMES_OVERLAYS` で 31 の provider が定義されています。"
        }
      ],
      "short_narration": "Claude・ChatGPT・Gemini など主要な AI サービスに対応しています。設定やフラグで使う AI を切り替えられます。",
      "long_narration": "hermes にはさまざまな AI サービスを切り替えて使う仕組みがあります。Claude・ChatGPT・Gemini・DeepSeek のような主要な AI に対応しています。どの AI サービスを使うかは優先順位で決まります。まず起動時の --provider オプション、次に設定ファイルの指定、次に環境変数、そして auto モードによる自動検出の順番です。auto モードでは、API キーが設定済みの provider を自動的に検出して使える状態にします。API キーのある AI だけが選択肢として表示されるため、使えない AI を誤って選ぶことがありません。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_duration_sec": 9.168,
      "long_duration_sec": 37.392
    },
    {
      "id": "scene_004",
      "title": "60 Slash Commands",
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123,140,255,0.18)",
      "kicker": "TUI COMMANDS",
      "headline": "/model から /kanban まで\n5 カテゴリ 60 コマンド",
      "lead": "セッション管理 23・設定変更 13・ツール操作 11・情報表示 12・終了 1。`/` を入力すると TUI 補完が起動します。",
      "subtitle": "60 slash commands。/ 補完で一覧が出る。",
      "image": "images/scene_004.png",
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
          "source": ".aidiy/knowledge/command_hermes,Slash Command一覧.md",
          "text": "Session 23 コマンド、Configuration 13 コマンド、Tools & Skills 11 コマンド、Info 12 コマンド、Exit 1 コマンド。"
        },
        {
          "source": ".aidiy/knowledge/command_hermes,Slash Command一覧.md",
          "text": "`COMMAND_REGISTRY` は `CommandDef` dataclass のリストです。正規名 + alias で検索します。"
        }
      ],
      "short_narration": "スラッシュコマンドも使えます。モデルの切り替えや設定を対話的に操作できます。",
      "long_narration": "hermes にはスラッシュで始まるコマンドが用意されています。セッションのリセットや保存、モデルの切り替えや設定変更などを対話的に操作できます。スラッシュキーを入力すると候補が自動で表示され、タブで補完できます。/model コマンドでは AI サービスとモデルを 2 段階で対話的に選べます。/goal コマンドで目標を設定すると、その目標が達成されるまで処理を続ける自律的な動作モードになります。全てのコマンドを AiDiy 環境でテストしているわけではありませんが、基本的な操作は問題なく使えます。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_duration_sec": 6.072,
      "long_duration_sec": 34.464
    },
    {
      "id": "scene_005",
      "title": "AiDiy システム連携",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125,255,179,0.18)",
      "kicker": "INTEGRATION",
      "headline": "backend_server が subprocess で起動し、\nconf_model.py がモデル一覧を動的生成",
      "lead": "CODE_AI*_NAME = \"aidiy_hermes\" を設定すると、AI コードパネルが AIコード_cli.py 経由で Hermes を起動します。",
      "subtitle": "CODE_AI*_NAME = aidiy_hermes で AI コードパネルと連携。",
      "image": "images/scene_005.png",
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
          "source": "command_hermes/AGENTS.md",
          "text": "`aidiy_hermes` は `backend_server/AIコア/AIコード_cli.py` から subprocess で起動されます。モデル設定は `CODE_AIDIY_HERMES_MODEL` を使います。"
        },
        {
          "source": "command_hermes/AGENTS.md",
          "text": "Windows では対応する `*_win.py`、非 Windows では `*_linux.py` のどちらか一方だけを import します。"
        }
      ],
      "short_narration": "Windows にネイティブ対応しています。AI コードパネルで hermes を選ぶだけで自動的に起動します。",
      "long_narration": "aidiy_hermes は Windows にネイティブ対応しています。Windows 用の実装（*_win.py）と Mac/Linux 用の実装（*_linux.py）を分けて持ち、OS を自動判定して適切な方で動きます。POSIX コマンドに依存しない設計なので、Windows 環境でも違和感なく動作します。AI コードパネルの設定で aidiy_hermes を選ぶと、バックエンドの AIコード_cli.py が hermes を自動起動します。コードパネルには 6 つのスロットがあり、それぞれに異なる AI を割り当てられます。使わせる AI モデルは設定ファイルか AI 設定画面からいつでも変更できます。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_duration_sec": 7.272,
      "long_duration_sec": 40.464
    },
    {
      "id": "scene_999",
      "title": "ご視聴ありがとうございました",
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196,155,255,0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "AIDIY HERMES",
      "headline": "ご視聴ありがとうございました。\naidiy_hermes で、なにを作りますか？",
      "lead": "on-demand CLI として、31 providers × 60 slash commands × AiDiy 連携。あなたのコード作業をエージェントに任せてみてください。",
      "subtitle": "aidiy_hermes — on-demand、31 providers、60 slash commands。",
      "image": "images/scene_999.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "short_narration": "AI に相談しながら開発する体験、やってみませんか。コードパネルから hermes を選ぶだけで、すぐ試せます。",
      "long_narration": "aidiy_hermes は、AI に相談しながらコードを書くという体験を、AiDiy のなかに直接持ち込むツールです。本家 hermes-agent の CLI 機能を切り出し、AiDiy 専用に再設計したツールとして、ファイルの読み書きや端末操作、AiDiy のコードパネルとのシームレスな連携ができます。コードを書く、ファイルを調べる、エラーを直す、テストを実行する、そのすべてを AI と一緒に進められます。Claude Code のような AI コーディングツールを AiDiy 環境の中で動かすイメージです。難しい設定は不要で、コードパネルの設定から hermes を選ぶだけですぐ試せます。AI とペアプログラミングする体験を、AiDiy でやってみませんか。",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_duration_sec": 8.304,
      "long_duration_sec": 42.264
    }
  ],
  "short_duration_sec": 57.816,
  "long_duration_sec": 293.088
};
