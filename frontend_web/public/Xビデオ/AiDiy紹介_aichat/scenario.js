window.SCENARIO = {
  "project_name": "AiDiy紹介aichat",
  "version": "aichat",
  "title": "AiDiy AIコア - チャット・ライブ・コード支援・WebSocket",
  "source": {
    "type": "agents_and_knowledge",
    "summary": "backend_server/AGENTS.md、AIコア/ディレクトリ、AIコアWebSocket仕様.md、AIモデル設定変更手順.md から実装実態を抜粋して構成。"
  },
  "target": {
    "language": "ja-JP",
    "duration_sec": 112.0,
    "format": "html_css_scene_player_with_media",
    "tone": "事実ベース、簡潔、根拠付き",
    "goal": "backend_server AIコアの 4 モード・WebSocket・Provider・A会話履歴・Claude Agent SDK 連携を正確に伝える。"
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
      "duration_sec": 12.0,
      "expression": "neutral",
      "accent": "#ff8a6b",
      "accent_soft": "rgba(255,138,107,0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "INTRODUCTION",
      "headline": "この動画では、AiDiy AIコアの\n4 モードと WebSocket 設計を紹介します",
      "lead": "チャット・ライブ・コード支援・音声処理の 4 モード、WebSocket 通信、複数 AI Provider、A会話履歴、Claude Agent SDK 連携までを見ていきます。",
      "subtitle": "AIコアの 4 モード、WebSocket、Provider、A会話履歴、Claude Agent SDK を紹介します。",
      "narration": "AiDiy の AI 機能を紹介します。チャット、ライブ、コード支援、音声の 4 つのモードがあります。",
      "image": "images/scene_000.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "audio": "audio/scene_000.mp3",
      "short_narration": "AiDiy の AI コアは 4 つのモードで構成されています。チャット・ライブ・コード支援・音声処理を紹介します。",
      "long_narration": "この動画では、AiDiy の AI コア機能を紹介します。チャット、ライブ、コード支援、音声処理の 4 つのモード、WebSocket 通信プロトコル、複数の AI Provider への対応、会話履歴の永続化、そして Claude Agent SDK と MCP の連携まで、実装に沿って順番に見ていきます。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 8.16,
      "long_start_sec": 0.0,
      "long_duration_sec": 22.08
    },
    {
      "id": "scene_001",
      "title": "AIコアの全体構成",
      "start_sec": 12.0,
      "duration_sec": 14.0,
      "expression": "neutral",
      "accent": "#ff8a6b",
      "accent_soft": "rgba(255,138,107,0.18)",
      "kicker": "AI CORE OVERVIEW",
      "headline": "backend_server/AIコア/ と\ncore_router/AIコア.py が中心",
      "lead": "`AIコア.py` が WebSocket エンドポイントを提供し、`AIコア/` ディレクトリの各モジュールが Provider ごとの処理を担当します。AIセッション管理がセッションとモデル設定を保持します。",
      "subtitle": "core_router/AIコア.py が WebSocket 入口。AIコア/ 配下がモード別処理。",
      "narration": "AI の入口は WebSocket サーバーです。モードごとのモジュールが AI Provider と通信して結果を返します。",
      "image": "images/scene_001.png",
      "audio": "audio/scene_001.mp3",
      "chips": [
        "core_router/AIコア.py",
        "AIセッション管理",
        "AIストリーミング処理",
        "AIコア/配下モジュール"
      ],
      "metrics": [
        {
          "label": "WebSocket エンドポイント",
          "value": "/core/ws/AIコア"
        },
        {
          "label": "モジュール数",
          "value": "14+"
        },
        {
          "label": "担当サーバー",
          "value": "core_main:8091"
        }
      ],
      "cards": [
        {
          "title": "コアモジュール構成",
          "lines": [
            "`AIコア.py` — WebSocket エンドポイント",
            "`AIセッション管理.py` — セッション・モデル設定",
            "`AIストリーミング処理.py` — リアルタイム転送"
          ]
        },
        {
          "title": "モード別モジュール",
          "lines": [
            "`AIチャット.py` / `AIチャット_gemini.py` など",
            "`AIライブ.py` / `AIライブ_gemini.py` / `AIライブ_openai.py`",
            "`AIコード.py` / `AIコード_claude.py` / `AIコード_cli.py`"
          ]
        },
        {
          "title": "補助モジュール",
          "lines": [
            "`AI音声処理.py` / `AI音声認識.py`",
            "`AI内部ツール.py`",
            "`AIバックアップ.py`"
          ]
        }
      ],
      "facts": [
        "`core_router/AIコア.py` が WebSocket エンドポイント `/core/ws/AIコア` を提供する。",
        "`backend_server/AIコア/` ディレクトリに 14 以上のモジュールが配置される。",
        "`AIセッション管理.py` がセッションとモデル設定を管理する。"
      ],
      "evidence": [
        {
          "source": "backend_server/AGENTS.md",
          "text": "AIコアは、テキスト、音声、画像、ファイル、コード支援を統合する WebSocket 中心の機能です。主な領域: AIセッション管理、AIストリーミング処理、AI音声処理、AIチャット*、AIコード*、AIコード_cli.py、AIコード_claude.py。"
        },
        {
          "source": "backend_server/AGENTS.md",
          "text": "AIコア変更は `core_router/AIコア.py` と `AIコア/` を起点に見る。"
        }
      ],
      "short_narration": "AI との通信はすべて WebSocket で行います。接続・送受信・切断のプロトコルが統一されています。",
      "long_narration": "AI の通信口は WebSocket です。core_router/AIコア.py が /core/ws/AIコア エンドポイントを提供し、AIコア/ ディレクトリに配置された 14 以上のモジュールが Provider ごとの処理を担当します。AIセッション管理.py がセッションとモデル設定を保持し、AIストリーミング処理.py がリアルタイムの出力転送を担います。担当サーバーは core_main の 8091 番ポートです。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_start_sec": 8.16,
      "short_duration_sec": 6.84,
      "long_start_sec": 22.08,
      "long_duration_sec": 30.864
    },
    {
      "id": "scene_002",
      "title": "チャット・ライブ・コード・音声の 4 モード",
      "start_sec": 26.0,
      "duration_sec": 14.0,
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196,155,255,0.18)",
      "kicker": "4 MODES",
      "headline": "CHAT_AI・LIVE_AI・CODE_AI×6・\n音声処理の 4 モード",
      "lead": "`CHAT_AI_NAME`（`_chat` 終わり）・`LIVE_AI_NAME`（`_live` 終わり）・`CODE_AI1_NAME`〜`CODE_AI6_NAME`（`_sdk` / `_cli`）の命名規約があります。設定は `_config/AiDiy_key.json` で管理します。",
      "subtitle": "CHAT / LIVE / CODE×6 / 音声の 4 モード。AI名に命名規約あり。設定は AiDiy_key.json。",
      "narration": "AI の名前にはルールがあります。チャットは _chat、ライブは _live で終わる名前にします。コード支援は 6 スロットに割り当てられます。",
      "image": "images/scene_002.png",
      "audio": "audio/scene_002.mp3",
      "chips": [
        "CHAT_AI_NAME",
        "LIVE_AI_NAME",
        "CODE_AI1〜6_NAME",
        "AiDiy_key.json"
      ],
      "metrics": [
        {
          "label": "チャット",
          "value": "1スロット"
        },
        {
          "label": "ライブ",
          "value": "1スロット"
        },
        {
          "label": "コード支援",
          "value": "6スロット (code1〜6)"
        }
      ],
      "cards": [
        {
          "title": "AI 名の命名規約",
          "lines": [
            "`CHAT_AI_NAME` — `_chat` で終わる",
            "`LIVE_AI_NAME` — `_live` で終わる",
            "`CODE_AI*_NAME` — `_sdk` / `_cli`、または `aidiy_hermes`"
          ]
        },
        {
          "title": "設定管理",
          "lines": [
            "`backend_server/_config/AiDiy_key.json` で一元管理",
            "`conf_json.py` が読み書きと不足キー補完",
            "`conf_model.py` が AI モデル一覧を動的生成"
          ]
        },
        {
          "title": "Provider 分岐",
          "lines": [
            "チャット: Claude / Gemini / OpenRouter / Ollama",
            "ライブ: Gemini Live / OpenAI Realtime",
            "コード: Claude SDK / Claude CLI / Code CLI 各種"
          ]
        }
      ],
      "facts": [
        "`CHAT_AI_NAME` は `_chat` で終わる名前を使う規約がある。",
        "`LIVE_AI_NAME` は `_live`、`CODE_AI*_NAME` は `_sdk` / `_cli` が原則（例外: `aidiy_hermes`）。",
        "比較は完全一致を前提にし、前方一致へ寄せない。",
        "設定は `backend_server/_config/AiDiy_key.json` で一元管理する。"
      ],
      "evidence": [
        {
          "source": "backend_server/AGENTS.md",
          "text": "AI 名の規約: `CHAT_AI_NAME` — `_chat` で終わる。`LIVE_AI_NAME` — `_live` で終わる。`CODE_AI1_NAME`〜`CODE_AI6_NAME` — 原則 `_sdk` または `_cli`、例外として `aidiy_hermes`。比較は完全一致を前提にし、前方一致へ寄せない。"
        },
        {
          "source": "backend_server/AGENTS.md",
          "text": "設定管理: `conf_json`: `AiDiy_key.json` の読み書き、不足キー補完、即時保存。`conf_models`: AI モデル一覧管理、provider API からの取得とキャッシュ。"
        }
      ],
      "short_narration": "チャット・ライブ・コード支援・音声処理の 4 つのモードが、ひとつの AI コアで動きます。",
      "long_narration": "AI の名前には命名規則があります。チャットモードに使う AI 名は _chat で終わる名前、ライブモードは _live で終わる名前、コード支援は _sdk または _cli で終わる名前を使います。例外として aidiy_hermes も有効です。コード支援は code1 から code6 の 6 スロットに異なる CLI を割り当てられます。設定はすべて backend_server/_config/AiDiy_key.json で一元管理し、AI 名の比較は前方一致ではなく完全一致を前提にします。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_start_sec": 15.0,
      "short_duration_sec": 7.032,
      "long_start_sec": 52.944,
      "long_duration_sec": 37.824
    },
    {
      "id": "scene_003",
      "title": "WebSocket 通信プロトコル",
      "start_sec": 40.0,
      "duration_sec": 14.0,
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41,216,255,0.18)",
      "kicker": "WEBSOCKET",
      "headline": "connect → init でセッション確定し、\nチャンネル別にメッセージを分配",
      "lead": "接続後に `{ type: \"connect\", セッションID, ソケット番号 }` を送信し、`{ メッセージ識別: \"init\" }` でセッションID を確定。チャット・コード・音声をチャンネルで分離します。",
      "subtitle": "connect→init でセッション確定。チャット/code1〜6/audio のチャンネル分離。",
      "narration": "AI と通信するとき WebSocket を使います。接続後に connect を送ると、サーバーから init が返ってセッション ID が決まります。",
      "image": "images/scene_003.png",
      "audio": "audio/scene_003.mp3",
      "chips": [
        "connect→init",
        "input_text/file/audio",
        "output→チャンネル分配",
        "output_end"
      ],
      "metrics": [
        {
          "label": "コードチャンネル",
          "value": "code1〜code6"
        },
        {
          "label": "音声チャンネル",
          "value": "audio 専用"
        },
        {
          "label": "接続確立",
          "value": "init 受信後"
        }
      ],
      "cards": [
        {
          "title": "接続フロー",
          "lines": [
            "open → `{ type: \"connect\", セッションID, ソケット番号 }` 送信",
            "サーバー → `{ メッセージ識別: \"init\", セッションID }` 受信",
            "sessionId 確定後にメッセージ送受信"
          ]
        },
        {
          "title": "送信メッセージ",
          "lines": [
            "`input_text` — テキスト（トークン延長あり）",
            "`input_file` / `input_image` — ファイル・画像",
            "`input_audio` — PCM base64（延長なし・高頻度）"
          ]
        },
        {
          "title": "受信メッセージ",
          "lines": [
            "`output` / `output_end` — テキスト出力・終了",
            "`output_audio` — 音声 PCM base64",
            "`cancel_audio` — 音声停止"
          ]
        }
      ],
      "facts": [
        "接続後に `connect` 送信 → `init` 受信でセッションID を確定する。",
        "`input_audio` はトークン延長対象外（高頻度送信のため）。",
        "出力は `chat` / `code1〜code6` / `audio` チャンネルに分配される。"
      ],
      "evidence": [
        {
          "source": "backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md",
          "text": "接続時は WebSocket open 後に `{ type: \"connect\", セッションID, ソケット番号 }` を送信し、サーバーから `{ メッセージ識別: \"init\", セッションID: \"<確定ID>\" }` を受けて sessionId が確定する。"
        },
        {
          "source": "backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md",
          "text": "トークン延長対象外: `input_audio`（高頻度送信のため）、`operations`、`cancel_run`、`cancel_audio`。"
        }
      ],
      "short_narration": "connect を送信すると init が返り、セッション ID が確立されて会話が始まります。",
      "long_narration": "AI との通信は WebSocket を使います。接続後にまず、type が connect、セッションID、ソケット番号を含むオブジェクトを送信し、サーバーから メッセージ識別が init のオブジェクトが返ってきてセッション ID が確定します。送信できるメッセージは input_text、input_file、input_image、input_audio の 4 種類です。受信側は output と output_end でテキスト、output_audio で音声 PCM を返します。出力はチャット、code1 から code6、audio のチャンネルに分配されます。なお input_audio は高頻度送信のためトークン延長の対象外です。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_start_sec": 22.032,
      "short_duration_sec": 6.36,
      "long_start_sec": 90.768,
      "long_duration_sec": 37.08
    },
    {
      "id": "scene_004",
      "title": "A会話履歴と永続化",
      "start_sec": 54.0,
      "duration_sec": 14.0,
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125,255,179,0.18)",
      "kicker": "CONVERSATION HISTORY",
      "headline": "A会話履歴テーブルで\nセッション単位に会話を DB 永続化",
      "lead": "`A会話履歴` テーブルが SQLite に会話履歴を保存します。セッションIDをキーに取得・保存を行い、core_main のエンドポイントで操作します。",
      "subtitle": "A会話履歴テーブルが SQLite 永続化。セッションID単位。core_main 担当。",
      "narration": "会話の内容はデータベースに保存します。セッション ID で管理するので、ページを再読み込みしても続きから話せます。",
      "image": "images/scene_004.png",
      "audio": "audio/scene_004.mp3",
      "chips": [
        "A会話履歴テーブル",
        "セッションID",
        "SQLite 永続化",
        "セッション復元"
      ],
      "metrics": [
        {
          "label": "担当サーバー",
          "value": "core_main:8091"
        },
        {
          "label": "テーブル接頭辞",
          "value": "A (AI系)"
        },
        {
          "label": "ストレージ",
          "value": "SQLite 共有DB"
        }
      ],
      "cards": [
        {
          "title": "A会話履歴の役割",
          "lines": [
            "セッションIDをキーに会話を SQLite 保存",
            "リロード・再接続後のセッション復元",
            "`A` 接頭辞 = AI系、core_main 担当"
          ]
        },
        {
          "title": "セッション復元フロー",
          "lines": [
            "WebSocket 接続時に既存セッションIDを渡す",
            "サーバーが A会話履歴から過去の文脈を復元",
            "URL の `?セッションID=` も参照（Web モード）"
          ]
        },
        {
          "title": "ストレージの違い",
          "lines": [
            "`frontend_web`: `localStorage` に `avatar_session_id`",
            "`frontend_avatar` Web モード: `sessionStorage`",
            "`frontend_avatar` Electron モード: `localStorage`"
          ]
        }
      ],
      "facts": [
        "`A会話履歴` テーブルが会話をセッションIDをキーに SQLite に永続化する。",
        "A 接頭辞は AI 系、core_main が担当する。",
        "リロード時は既存セッションIDを渡して会話文脈を復元できる。",
        "ストレージは frontend_web が localStorage、avatar Web モードが sessionStorage。"
      ],
      "evidence": [
        {
          "source": "backend_server/AGENTS.md",
          "text": "Core: `A会話履歴`。AI コアは、テキスト、音声、画像、ファイル、コード支援を統合する WebSocket 中心の機能です。"
        },
        {
          "source": "backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md",
          "text": "Electron は `localStorage`、Web は `sessionStorage` に `token` / `user` / `avatar_session_id` を保持する。Web モードは URL の `?セッションID=` も参照し、リロード復帰しやすくする。"
        }
      ],
      "short_narration": "会話はセッション ID に紐づいてデータベースに保存され、履歴を引き継いで続けられます。",
      "long_narration": "会話の内容はデータベースに保存されます。A会話履歴テーブルが SQLite にセッション ID をキーにして会話を永続化します。A の接頭辞は AI 系を意味し、core_main が担当します。ページをリロードしたり再接続したりするときに既存のセッション ID を渡せば、サーバーが A会話履歴から過去の文脈を復元して続きから話せます。セッション ID のストレージは frontend_web が localStorage、frontend_avatar の Web モードが sessionStorage、Electron モードが localStorage です。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_start_sec": 28.392,
      "short_duration_sec": 6.672,
      "long_start_sec": 127.848,
      "long_duration_sec": 40.8
    },
    {
      "id": "scene_005",
      "title": "Claude Agent SDK と MCP 連携",
      "start_sec": 68.0,
      "duration_sec": 14.0,
      "expression": "neutral",
      "accent": "#ffd166",
      "accent_soft": "rgba(255,209,102,0.18)",
      "kicker": "CLAUDE SDK & MCP",
      "headline": "AIコード_claude.py が Claude Agent SDK で\nMCP ツールを AI エージェントに公開",
      "lead": "`AIコード_claude.py` が Claude Agent SDK を使い、`_config/AiDiy_mcp.json` で定義した MCP サーバーをエージェントに渡します。code パネルから Claude に MCP ツールを自動使用させることができます。",
      "subtitle": "AIコード_claude.py が Claude Agent SDK + AiDiy_mcp.json で MCP ツールをエージェント化。",
      "narration": "AIコード_claude.py は Claude Agent SDK を使います。13 個の MCP ツールを AI に渡すことで、ブラウザ操作や DB 確認も AI が自動実行します。",
      "image": "images/scene_005.png",
      "audio": "audio/scene_005.mp3",
      "chips": [
        "Claude Agent SDK",
        "AiDiy_mcp.json",
        "MCP 13サーバー",
        "CODE_AI*_NAME=*_sdk"
      ],
      "metrics": [
        {
          "label": "SDKファイル",
          "value": "AIコード_claude.py"
        },
        {
          "label": "MCP 接続定義",
          "value": "AiDiy_mcp.json"
        },
        {
          "label": "MCP サーバー数",
          "value": "13"
        }
      ],
      "cards": [
        {
          "title": "Claude Agent SDK 経路",
          "lines": [
            "`CODE_AI*_NAME = \"*_sdk\"` で起動",
            "`AIコード_claude.py` が Claude Agent SDK を呼ぶ",
            "`_config/AiDiy_mcp.json` から MCP 設定を読む"
          ]
        },
        {
          "title": "MCP 連携の効果",
          "lines": [
            "Claude が MCP ツールを自動選択して使用",
            "ブラウザ操作、DB 確認、コードチェックを AI が実行",
            "画像生成・音声合成も MCP 経由でエージェント化"
          ]
        },
        {
          "title": "CLI 経路との比較",
          "lines": [
            "`AIコード_cli.py` — subprocess 経由で Code CLI を起動",
            "`AIコード_claude.py` — Python 内で Claude Agent SDK を呼ぶ",
            "`aidiy_hermes` — hermes CLI を subprocess で呼ぶ"
          ]
        }
      ],
      "facts": [
        "`AIコード_claude.py` が Claude Agent SDK を使い MCP ツールをエージェントに渡す。",
        "MCP 接続定義は `backend_server/_config/AiDiy_mcp.json` に集約する。",
        "`CODE_AI*_NAME = \"*_sdk\"` で `AIコード_claude.py` が起動する。"
      ],
      "evidence": [
        {
          "source": "backend_server/AGENTS.md",
          "text": "MCP サーバー本体は `backend_mcp` にあります。`backend_server` では `_config/AiDiy_mcp.json` を読み、Claude Agent SDK などへ MCP 設定を渡します。"
        },
        {
          "source": "backend_server,backend_mcp,MCP活用手順.md",
          "text": "MCP 接続定義は `backend_server/_config/AiDiy_mcp.json` に集約する。`AIコード_claude.py` 側で `conf.models.mcp_servers` を Claude Agent SDK に渡す。"
        }
      ],
      "short_narration": "Claude SDK を経由して 13 の MCP ツールを AI が自律的に使えます。",
      "long_narration": "AIコード_claude.py は Claude Agent SDK を使ってコード支援を行います。_config/AiDiy_mcp.json で定義した 13 個の MCP サーバーをエージェントに渡すことで、Claude がブラウザ操作、データベース確認、コードチェック、画像生成、音声合成を自動で使い分けます。CODE_AI の NAME を _sdk で終わる名前に設定したとき、この AIコード_claude.py が起動します。一方 _cli で終わる名前の場合は subprocess 経由で Code CLI を起動する AIコード_cli.py が担当します。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_start_sec": 35.064,
      "short_duration_sec": 6.24,
      "long_start_sec": 168.648,
      "long_duration_sec": 36.72
    },
    {
      "id": "scene_006",
      "title": "AI Provider の種類",
      "start_sec": 82.0,
      "duration_sec": 14.0,
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123,140,255,0.18)",
      "kicker": "AI PROVIDERS",
      "headline": "チャット・ライブ・コードで\n異なる AI Provider を切り替え",
      "lead": "チャットは Claude / Gemini / OpenRouter / Ollama / FreeAI に対応。ライブは Gemini Live / OpenAI Realtime。コードは Claude SDK / Claude CLI / Gemini CLI / aidiy_hermes / Codex など。",
      "subtitle": "チャット・ライブ・コードそれぞれに対応 Provider が異なる。AiDiy_key.json で設定。",
      "narration": "チャットは Claude、Gemini、OpenRouter など複数の AI サービスに対応しています。設定ファイルで切り替えられます。",
      "image": "images/scene_006.png",
      "audio": "audio/scene_006.mp3",
      "chips": [
        "Claude / Gemini / OpenRouter",
        "Gemini Live / OpenAI Realtime",
        "Code CLI 各種",
        "Ollama (ローカル)"
      ],
      "metrics": [
        {
          "label": "チャット Provider",
          "value": "5種+"
        },
        {
          "label": "ライブ Provider",
          "value": "2種"
        },
        {
          "label": "コード CLI",
          "value": "7種+"
        }
      ],
      "cards": [
        {
          "title": "チャットモード",
          "lines": [
            "Claude (Anthropic SDK)",
            "Gemini / FreeAI (`AIチャット_gemini.py`)",
            "OpenRouter / Ollama (ローカル LLM)"
          ]
        },
        {
          "title": "ライブモード",
          "lines": [
            "Gemini Live (`AIライブ_gemini.py`)",
            "OpenAI Realtime (`AIライブ_openai.py`)",
            "音声 PCM をリアルタイムで送受信"
          ]
        },
        {
          "title": "コード支援 CLI",
          "lines": [
            "Claude CLI / Claude SDK (`*_claude.py`)",
            "aidiy_hermes / Gemini CLI / Codex / OpenCode",
            "Copilot CLI — `CODE_AI*_NAME` で指定"
          ]
        }
      ],
      "facts": [
        "チャットは Claude / Gemini / FreeAI / OpenRouter / Ollama に対応。",
        "ライブは Gemini Live と OpenAI Realtime の 2 Provider。",
        "コード支援は CODE_AI*_NAME で 6 スロットに異なる CLI を割り当て可能。",
        "Ollama でローカル LLM をチャットに使える。"
      ],
      "evidence": [
        {
          "source": "backend_server/AGENTS.md",
          "text": "AI SDKs: Anthropic / OpenAI / Google Gemini / Claude Agent SDK など。"
        },
        {
          "source": "backend_server/AGENTS.md",
          "text": "Code AI は `code1`〜`code6` / `CODE_AI1_NAME`〜`CODE_AI6_NAME` を前提にします。"
        }
      ],
      "short_narration": "Claude・Gemini・OpenAI など複数の AI サービスを画面から切り替えて使えます。",
      "long_narration": "AI Provider は用途によって異なります。チャットモードは Claude、Gemini、FreeAI、OpenRouter、Ollama の 5 種類以上に対応しています。Ollama を使えばローカル LLM でチャットできます。ライブモードは Gemini Live と OpenAI Realtime の 2 Provider でリアルタイム音声通信を行います。コード支援は CODE_AI の NAME の設定で 6 スロットにそれぞれ異なる CLI を割り当てられるため、用途に応じて使い分けられます。",
      "short_audio": "audio/short_scene_006.mp3",
      "long_audio": "audio/long_scene_006.mp3",
      "short_start_sec": 41.304,
      "short_duration_sec": 6.312,
      "long_start_sec": 205.368,
      "long_duration_sec": 30.552
    },
    {
      "id": "scene_999",
      "title": "ご視聴ありがとうございました",
      "start_sec": 96.0,
      "duration_sec": 16.0,
      "expression": "neutral",
      "accent": "#ff8a6b",
      "accent_soft": "rgba(255,138,107,0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "AIDIY AI CORE",
      "headline": "ご視聴ありがとうございました。\nどの AI Provider を使いますか？",
      "lead": "4 モード・WebSocket セッション・A会話履歴・Claude Agent SDK + MCP 連携・複数 Provider。AiDiy を通じて多様な AI をあなたの業務に組み込んでみてください。",
      "subtitle": "AIコア — 4 モード、WebSocket、A会話履歴、Claude SDK + MCP、複数 Provider。",
      "narration": "4 モード、WebSocket、会話保存、Claude SDK と MCP。多様な AI を業務に組み込んでみてください。",
      "image": "images/scene_999.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "audio": "audio/scene_999.mp3",
      "short_narration": "4 モード・WebSocket・MCP ツール連携で業務に深く組み込める AI コアです。多様な AI を活用してみてください。",
      "long_narration": "ご視聴ありがとうございました。4 モード、WebSocket セッション、A会話履歴による永続化、Claude Agent SDK と MCP の連携、そして複数の AI Provider への対応。AiDiy の AI コアは、テキスト、音声、画像、ファイル、コード支援を統合した WebSocket 中心の設計になっています。多様な AI をあなたの業務に組み込んでみてください。",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_start_sec": 47.616,
      "short_duration_sec": 9.552,
      "long_start_sec": 235.92,
      "long_duration_sec": 25.032
    }
  ],
  "duration_sec": 112.0,
  "short_duration_sec": 57.168,
  "long_duration_sec": 260.952
};
