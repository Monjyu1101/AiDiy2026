window.SCENARIO = {
  "project_name": "AiDiy紹介mcp",
  "version": "mcp",
  "title": "AiDiy MCP Hub - 13 サーバー紹介",
  "source": {
    "type": "agents_and_knowledge",
    "summary": "backend_mcp/AGENTS.md、mcp_main.py、mcp_proc/ 各ファイル、.aidiy/knowledge から実装実態を抜粋して構成。"
  },
  "target": {
    "language": "ja-JP",
    "format": "html_css_scene_player_with_media",
    "tone": "事実ベース、簡潔、根拠付き",
    "goal": "backend_mcp の位置づけ・13 MCP サーバーの役割・接続方式を正確に伝える。"
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
      "accent_soft": "rgba(41,216,255,0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "INTRODUCTION",
      "headline": "この動画では、AiDiy MCP Hub の\n13 サーバーを紹介します",
      "lead": "ポート 8095 に同居する 13 個の MCP サーバー、SSE 接続、stdio bridge、各ツールの役割を順に見ていきます。",
      "subtitle": "この動画では、backend_mcp の位置づけ、13 MCP サーバーの役割、接続方式を紹介します。",
      "image": "images/scene_000.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "short_narration": "AiDiy には AI が使える 13 のツールが揃っています。ブラウザ操作から動画制作まで紹介します。",
      "long_narration": "この動画では、AiDiy の MCP ハブを詳しく紹介します。MCP とは AI が道具として直接呼び出せる機能のまとまりで、AiDiy には 13 種類の MCP サーバーが用意されています。ブラウザの自動操作、データベースの中身の確認、バックアップの管理、AI による画像・音声の生成、動画の制作まで、AI エージェントが使えるツールとして一か所に集められています。ポート 8095 番で動く 1 本のサーバーに 13 のツールが同居しており、Claude Code や AI エージェントから設定ファイル 1 つで使い始められます。各グループの役割を実際の実装に沿って順番に見ていきます。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 7.464,
      "long_start_sec": 0.0,
      "long_duration_sec": 40.632
    },
    {
      "id": "scene_001",
      "title": "位置づけとアーキテクチャ",
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123,140,255,0.18)",
      "kicker": "ARCHITECTURE",
      "headline": "ポート 8095 に 13 FastMCP を\nStarlette Mount で合成",
      "lead": "mcp_main.py が FastAPI/Starlette 上に 13 個の FastMCP インスタンスを Mount し、uvicorn で起動します。Claude Code CLI や Claude Agent SDK が SSE で接続します。",
      "subtitle": "FastMCP × 13 を Starlette でマウント。SSE transport と stdio bridge の二経路。",
      "image": "images/scene_001.png",
      "chips": [
        "FastMCP × 13",
        "Starlette Mount",
        "SSE transport",
        "stdio bridge"
      ],
      "metrics": [
        {
          "label": "ポート",
          "value": "8095"
        },
        {
          "label": "MCP 数",
          "value": "13"
        },
        {
          "label": "フレームワーク",
          "value": "FastMCP"
        }
      ],
      "cards": [
        {
          "title": "起動構成",
          "lines": [
            "`mcp_main.py` が 13 FastMCP を Mount",
            "`uvicorn mcp_main:app --port 8095`",
            "`_start.py` 経由で起動・管理"
          ]
        },
        {
          "title": "接続方式",
          "lines": [
            "SSE: `http://localhost:8095/{name}/sse`",
            "stdio bridge: `mcp_stdio.py --sse-url`",
            "Claude Agent SDK: `AiDiy_mcp.json` で定義"
          ]
        },
        {
          "title": "再起動",
          "lines": [
            "`temp/reboot_mcp.txt` を作成で再起動",
            "`_setup_reboot_watcher()` が監視",
            "ファイル検知後 `os._exit(0)` で再起動"
          ]
        }
      ],
      "facts": [
        "`mcp_main.py` が 13 本の `FastMCP` インスタンスを Starlette の `Mount` で合成する。",
        "SSE エンドポイントは `http://localhost:8095/{name}/sse` の形式。",
        "stdio クライアントは `mcp_stdio.py --sse-url` を経由して接続する。",
        "再起動ウォッチャーは `backend_mcp/temp/reboot_mcp.txt` を監視する。"
      ],
      "evidence": [
        {
          "source": "backend_mcp/AGENTS.md",
          "text": "`backend_mcp` はポート `8095` 上で 13 個の MCP サーバーを同居させる FastMCP アプリケーションです。"
        },
        {
          "source": "backend_mcp,構成.md",
          "text": "`mcp_main.py` は 13 本の `FastMCP` インスタンスを Starlette の `Mount` で合成し、`mcp_main:app` として uvicorn に渡す。"
        }
      ],
      "short_narration": "13 のツールは 1 本のサーバーにまとまっていて、Claude や AI エージェントからまとめて使えます。",
      "long_narration": "13 のツールは、mcp_main.py という 1 本のサーバーで管理されています。Python の FastMCP というフレームワークを使い、13 個の MCP インスタンスを Starlette の Mount という仕組みで 1 つのアプリに合成しています。uvicorn というサーバーでポート 8095 番に起動します。AI からツールを呼び出すときは、SSE という方式でこのサーバーに接続します。接続先の URL は http://localhost:8095/ツール名/sse の形式です。Claude Agent SDK や Claude Code CLI は設定ファイル AiDiy_mcp.json にこの URL を書いておくだけで自動的に接続します。stdio クライアントは mcp_stdio.py を経由して接続します。サーバーを更新したとき、backend_mcp/temp フォルダに特定のファイルを置くと自動で再起動する仕組みも備わっています。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_start_sec": 7.464,
      "short_duration_sec": 6.552,
      "long_start_sec": 40.632,
      "long_duration_sec": 58.728
    },
    {
      "id": "scene_002",
      "title": "13 MCP サーバー一覧",
      "expression": "neutral",
      "accent": "#00e0b8",
      "accent_soft": "rgba(0,224,184,0.18)",
      "kicker": "13 SERVERS",
      "headline": "5 カテゴリ 13 サーバー、\n役割ごとに整理",
      "lead": "ブラウザ系・DB 系・観測系・バックアップ系・メディア系・制作系に分類。すべて localhost 限定アクセスです。",
      "subtitle": "13 MCP を 6 カテゴリに分類。全て localhost アクセス限定。",
      "image": "images/scene_002.png",
      "chips": [
        "ブラウザ系 ×2",
        "DB系 ×2",
        "観測系 ×2",
        "バックアップ系 ×2",
        "メディア系 ×3",
        "制作系 ×2"
      ],
      "metrics": [
        {
          "label": "合計 MCP",
          "value": "13"
        },
        {
          "label": "カテゴリ",
          "value": "6"
        },
        {
          "label": "アクセス",
          "value": "localhost 限定"
        }
      ],
      "cards": [
        {
          "title": "ブラウザ / デスクトップ",
          "lines": [
            "`aidiy_chrome_devtools` — Chrome CDP 操作",
            "`aidiy_desktop_capture` — OS スクリーンショット"
          ]
        },
        {
          "title": "DB / 観測 / バックアップ",
          "lines": [
            "`aidiy_sqlite` / `aidiy_postgres` — DB 確認",
            "`aidiy_logs` / `aidiy_code_check` — 観測",
            "`aidiy_backup_check` / `aidiy_backup_save` — バックアップ"
          ]
        },
        {
          "title": "メディア / 制作",
          "lines": [
            "`aidiy_image_generation` — AI 画像生成",
            "`aidiy_speech_to_text` / `aidiy_text_to_speech`",
            "`aidiy_obs_studio_control` / `aidiy_ffmpeg_control`"
          ]
        }
      ],
      "facts": [
        "13 個の MCP サーバーがポート 8095 に同居している。",
        "アクセスは localhost 限定。",
        "SQLite / PostgreSQL は read-only 中心で扱う。"
      ],
      "evidence": [
        {
          "source": "backend_mcp/AGENTS.md",
          "text": "ブラウザ操作、デスクトップキャプチャ、DB確認、ログ確認、コードチェック、バックアップ確認、画像生成、音声認識/合成、OBS / ffmpeg 制御を AI エージェントから利用できるようにします。"
        },
        {
          "source": "backend_mcp,構成.md",
          "text": "アクセスは localhost 限定です。SQLite / PostgreSQL は read-only 中心で扱い、書き込みが必要な場合もまずアプリ API で再現できないか確認します。"
        }
      ],
      "short_narration": "13 のツールはブラウザ・データベース・バックアップ・音声・画像・動画の 6 グループに分かれます。",
      "long_narration": "13 のツールは役割ごとに 6 つのグループに分類されています。ブラウザ操作グループは Chrome を操作する chrome_devtools とデスクトップ全体の画面を取得する desktop_capture の 2 本です。DB 確認グループは AiDiy の SQLite データベースを参照する sqlite と外部の PostgreSQL データベースを参照する postgres の 2 本です。観測グループはサーバーのログを解析する logs とコードの品質を確認する code_check の 2 本です。バックアップグループは変更前後を比較する backup_check と差分保存を実行する backup_save の 2 本です。メディア生成グループは画像生成・音声認識・音声合成の 3 本です。制作グループは OBS Studio 制御と FFmpeg 制御の 2 本です。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_start_sec": 14.016,
      "short_duration_sec": 7.032,
      "long_start_sec": 99.36,
      "long_duration_sec": 48.624
    },
    {
      "id": "scene_003",
      "title": "ブラウザ・デスクトップ系",
      "expression": "neutral",
      "accent": "#ff8a6b",
      "accent_soft": "rgba(255,138,107,0.18)",
      "kicker": "BROWSER & DESKTOP",
      "headline": "Python 実装の CDP クライアントで\nChrome を直接操作",
      "lead": "chrome_devtools は Node.js 版ではなく Python 純正の CDP クライアント実装。ChromeManager が --remote-debugging-port=9222 で Chrome を管理します。",
      "subtitle": "chrome_devtools は Python CDP 実装。ChromeManager が Chrome を単一 subprocess で管理。",
      "image": "images/scene_003.png",
      "chips": [
        "Python CDP 実装",
        "ChromeManager",
        "port 9222",
        "OS スクリーンショット"
      ],
      "metrics": [
        {
          "label": "Chrome 管理",
          "value": "単一 subprocess"
        },
        {
          "label": "デバッグポート",
          "value": "9222"
        },
        {
          "label": "実装言語",
          "value": "Python 純正"
        }
      ],
      "cards": [
        {
          "title": "aidiy_chrome_devtools",
          "lines": [
            "Python 純正 CDP client（Node.js 版ではない）",
            "`ChromeManager` が Chrome を subprocess 管理",
            "ナビゲーション、DOM 取得、クリック、スクリーンショット"
          ]
        },
        {
          "title": "Chrome 自動起動",
          "lines": [
            "`_ensure_chrome()` で起動状態を確認",
            "未起動なら `ChromeManager.ensure_running()` が起動",
            "`CHROME_EXECUTABLE` / `CHROME_DEBUG_PORT` で上書き可"
          ]
        },
        {
          "title": "aidiy_desktop_capture",
          "lines": [
            "OS レベルのスクリーンショット取得",
            "ウィンドウ指定やデスクトップ全体に対応",
            "Electron 含むブラウザ外の画面確認に使う"
          ]
        }
      ],
      "facts": [
        "`aidiy_chrome_devtools` は Node.js 版 chrome-devtools-mcp ではなく Python 実装の CDP client。",
        "`ChromeManager` が Chrome を単一 subprocess として管理し、`--remote-debugging-port=9222` で起動する。",
        "`_start.py` も起動時に Chrome を先行起動する。",
        "ブラウザ外の画面確認は `aidiy_desktop_capture` を使う。"
      ],
      "evidence": [
        {
          "source": "backend_mcp/AGENTS.md",
          "text": "Chrome DevTools は Node.js 版ではなく Python 実装の CDP client を使います。Chrome は `ChromeManager` が単一 subprocess として管理し、必要時に `--remote-debugging-port=9222` で起動します。"
        },
        {
          "source": "backend_mcp,構成.md",
          "text": "Chrome DevTools MCP は Python CDP 実装。Node.js 版 `chrome-devtools-mcp` 前提で復旧しない。"
        }
      ],
      "short_narration": "aidiy_chrome_devtools は Python だけで Chrome を操作できるツールです。Node.js は不要です。",
      "long_narration": "aidiy_chrome_devtools は Chrome ブラウザを AI から操作するためのツールです。特徴は、よくある Node.js ベースのブラウザ自動化ツールではなく、Python だけで実装されている点です。ChromeManager というプログラムが Chrome をプロセスとして管理し、リモートデバッグポートの 9222 番を使って接続します。Chrome が起動していなければ自動で起動し、起動済みなら既存のプロセスを再利用します。できる操作はページの移動、テキストや HTML の取得、要素のクリック、フォームへの入力、スクリーンショットの取得です。E2E テストの自動化や画面の動作確認に活用できます。Chrome ではなくデスクトップ全体を取得したいときは、aidiy_desktop_capture を使います。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_start_sec": 21.048,
      "short_duration_sec": 7.344,
      "long_start_sec": 147.984,
      "long_duration_sec": 46.896
    },
    {
      "id": "scene_004",
      "title": "DB・ログ・コードチェック系",
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196,155,255,0.18)",
      "kicker": "DB / OBSERVE / CHECK",
      "headline": "SQLite・PostgreSQL・ログ・\nコード品質を MCP で確認",
      "lead": "sqlite は AiDiy SQLite DB の read-only 中心クエリ。postgres は psycopg で外部 DB に接続（DSN 任意、遅延初期化）。logs はログ tail と ERROR 抽出。code_check は Python 構文・ruff・TypeScript 型チェック。",
      "subtitle": "4 MCP で DB・ログ・コード品質を統合観測。PostgreSQL は DSN 未設定でも他 MCP を妨げない。",
      "image": "images/scene_004.png",
      "chips": [
        "SQLite read-only",
        "PostgreSQL 遅延初期化",
        "ログ tail/ERROR抽出",
        "ruff / tsc"
      ],
      "metrics": [
        {
          "label": "DB MCP",
          "value": "2"
        },
        {
          "label": "ログ / チェック MCP",
          "value": "2"
        },
        {
          "label": "Postgres 依存",
          "value": "遅延初期化"
        }
      ],
      "cards": [
        {
          "title": "aidiy_sqlite",
          "lines": [
            "AiDiy SQLite DB を read-only 中心で参照",
            "テーブル一覧、件数、監査フィールド確認",
            "確認は SELECT / describe / count を優先"
          ]
        },
        {
          "title": "aidiy_postgres",
          "lines": [
            "`psycopg` で外部 PostgreSQL に接続",
            "DSN 未設定でも起動を妨げない遅延初期化",
            "スキーマ・件数確認を read-only 中心で実施"
          ]
        },
        {
          "title": "aidiy_logs / aidiy_code_check",
          "lines": [
            "`logs`: backend_server / backend_mcp のログ tail・ERROR 抽出",
            "`code_check`: Python 構文チェック・ruff・TypeScript 型チェック",
            "コードチェックは MCP 経由でパス指定して実行"
          ]
        }
      ],
      "facts": [
        "`aidiy_sqlite` は AiDiy SQLite DB を read-only 中心で参照する。",
        "`aidiy_postgres` は `psycopg` 未導入や DSN 未設定でも他 MCP の起動を妨げない遅延初期化を採用。",
        "`aidiy_logs` は backend_server / backend_mcp のログ tail と ERROR 抽出を行う。",
        "`aidiy_code_check` は Python 構文チェック、ruff、TypeScript 型チェックに対応。"
      ],
      "evidence": [
        {
          "source": "backend_mcp/AGENTS.md",
          "text": "`aidiy_postgres` は `psycopg` 未導入や DSN 未設定でも他 MCP の起動を妨げない。起動時の `PgQuery()` 例外を保存し、PostgreSQL ツール呼び出し時にだけ `_get_pg()` でエラー化する。"
        },
        {
          "source": "backend_mcp,構成.md",
          "text": "SQLite / PostgreSQL は既定 read-only。検証は SELECT / describe / count を優先する。"
        }
      ],
      "short_narration": "データベースの参照、ログのエラー検索、コードの品質チェックが 4 本のツールでできます。",
      "long_narration": "DB 確認系は 4 本あります。aidiy_sqlite は AiDiy の SQLite データベースをテーブル一覧・件数確認・クエリ実行の 3 操作で参照します。データの書き込みより読み取りを優先する運用で、確認作業に使います。aidiy_postgres は外部の PostgreSQL データベースに接続するツールです。PostgreSQL の接続情報 DSN が設定されていなくても起動時にエラーにならず遅延初期化で対応するため、他の 12 本のツールの動作を妨げません。aidiy_logs はバックエンドサーバーと MCP サーバーのログファイルを tail して、エラーメッセージを自動で抽出します。aidiy_code_check は Python の構文チェック・ruff によるスタイルチェック・TypeScript の型チェックを MCP 経由でパス指定して実行できます。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_start_sec": 28.392,
      "short_duration_sec": 6.528,
      "long_start_sec": 194.88,
      "long_duration_sec": 49.392
    },
    {
      "id": "scene_005",
      "title": "バックアップ・メディア生成系",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125,255,179,0.18)",
      "kicker": "BACKUP & MEDIA",
      "headline": "差分バックアップの確認・保存と\nAI メディア生成を MCP で実行",
      "lead": "backup_check が変更前後ソースを抽出し、backup_save が AiDiy ネイティブ差分バックアップを実行。image_generation・speech_to_text・text_to_speech が AI メディア生成を担当します。",
      "subtitle": "バックアップ系 2 + メディア系 3。複数プロバイダーに対応。",
      "image": "images/scene_005.png",
      "chips": [
        "差分バックアップ",
        "OpenAI / Gemini / FreeAI",
        "Whisper STT",
        "Edge TTS / MP3出力"
      ],
      "metrics": [
        {
          "label": "バックアップ MCP",
          "value": "2"
        },
        {
          "label": "メディア MCP",
          "value": "3"
        },
        {
          "label": "画像プロバイダー",
          "value": "3種"
        }
      ],
      "cards": [
        {
          "title": "バックアップ系",
          "lines": [
            "`backup_check`: 差分から変更前後ソースを抽出",
            "`backup_save`: AiDiy ネイティブ差分バックアップ実行",
            "自己検証の補助として活用"
          ]
        },
        {
          "title": "aidiy_image_generation",
          "lines": [
            "OpenAI gpt-image / DALL-E で画像生成",
            "Gemini / FreeAI にも対応",
            "プロンプト → PNG で出力"
          ]
        },
        {
          "title": "音声系",
          "lines": [
            "`speech_to_text`: speech_recognition / OpenAI Whisper",
            "`text_to_speech`: Edge / OpenAI / Gemini / FreeAI",
            "TTS は MP3 ファイルとして出力"
          ]
        }
      ],
      "facts": [
        "`aidiy_image_generation` は OpenAI gpt-image / DALL-E、Gemini、FreeAI に対応。",
        "`aidiy_speech_to_text` は speech_recognition と OpenAI Whisper を使用。",
        "`aidiy_text_to_speech` は Edge / OpenAI / Gemini / FreeAI で MP3 を出力。",
        "バックアップ系 MCP はツール不調時も対象ファイルと検索結果で変更範囲を説明できる補助として機能する。"
      ],
      "evidence": [
        {
          "source": "backend_mcp/AGENTS.md",
          "text": "`aidiy_image_generation`: AI 画像生成（OpenAI gpt-image / DALL-E、Gemini、FreeAI）。`aidiy_speech_to_text`: 音声認識（speech_recognition、OpenAI Whisper）。`aidiy_text_to_speech`: テキスト音声合成（Edge / OpenAI / Gemini / FreeAI、MP3 出力）。"
        },
        {
          "source": "backend_mcp,MCP活用手順.md",
          "text": "バックアップ保存/確認系 MCP は自己検証の補助。ツール不調時も、対象ファイル、実行コマンド、検索結果で変更範囲を説明できる状態にする。"
        }
      ],
      "short_narration": "バックアップの確認・保存と、AI による画像生成・音声認識・音声合成ができます。",
      "long_narration": "バックアップ系の aidiy_backup_check は AiDiy のバックアップ機能と連携して変更前後のソースファイルを抽出します。コードを修正した後、どのファイルが変わったかを比較するのに使います。aidiy_backup_save は AiDiy ネイティブの差分バックアップを AI が直接実行するツールです。メディア系は 3 本あります。aidiy_image_generation は OpenAI の DALL-E や gpt-image、Google の Gemini、FreeAI に対応した画像生成ツールで、テキストでプロンプトを渡すと PNG 画像が生成されます。aidiy_speech_to_text は speech_recognition ライブラリと OpenAI の Whisper を使って音声をテキストに変換します。aidiy_text_to_speech は Edge TTS・OpenAI・Gemini・FreeAI を使って MP3 音声ファイルを生成します。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_start_sec": 34.92,
      "short_duration_sec": 7.224,
      "long_start_sec": 244.272,
      "long_duration_sec": 51.408
    },
    {
      "id": "scene_006",
      "title": "OBS・FFmpeg 制作系",
      "expression": "neutral",
      "accent": "#ffd166",
      "accent_soft": "rgba(255,209,102,0.18)",
      "kicker": "PRODUCTION",
      "headline": "OBS Studio 制御と ffmpeg 実行を\nMCP ツールとして公開",
      "lead": "obs_studio_control は OBS WebSocket で配信・録画・シーン・ソース・音声を制御。ffmpeg_control は ffmpeg / ffprobe / ffplay の薄いランナーで動画合成・字幕焼き込み・プレビュー再生を実行します。",
      "subtitle": "OBS WebSocket 制御と ffmpeg 薄いランナー。動画制作の自動化に活用。",
      "image": "images/scene_006.png",
      "chips": [
        "OBS WebSocket",
        "配信/録画/シーン制御",
        "ffmpeg / ffprobe / ffplay",
        "動画合成・字幕焼き込み"
      ],
      "metrics": [
        {
          "label": "OBS 制御項目",
          "value": "配信/録画/シーン/ソース/音声"
        },
        {
          "label": "ffmpeg ツール",
          "value": "3種"
        },
        {
          "label": "制作系 MCP",
          "value": "2"
        }
      ],
      "cards": [
        {
          "title": "aidiy_obs_studio_control",
          "lines": [
            "OBS Studio WebSocket で制御",
            "配信開始・停止、録画、シーン切替",
            "ソース制御、音声調整"
          ]
        },
        {
          "title": "aidiy_ffmpeg_control",
          "lines": [
            "ffmpeg / ffprobe / ffplay の薄いランナー",
            "動画合成、字幕焼き込み",
            "ffplay でプレビュー再生"
          ]
        },
        {
          "title": "活用シーン",
          "lines": [
            "このビデオ自体も ffmpeg + OBS MCP で制作",
            "シーン切替・音声同期を自動化",
            "字幕・BGM を ffmpeg で合成"
          ]
        }
      ],
      "facts": [
        "`aidiy_obs_studio_control` は OBS Studio WebSocket で配信、録画、シーン、ソース、音声を制御する。",
        "`aidiy_ffmpeg_control` は ffmpeg / ffprobe / ffplay の薄いランナー。動画合成、字幕焼き込み、プレビュー再生に使う。"
      ],
      "evidence": [
        {
          "source": "backend_mcp/AGENTS.md",
          "text": "`aidiy_obs_studio_control`: OBS Studio WebSocket 制御（配信、録画、シーン、ソース、音声）。`aidiy_ffmpeg_control`: ffmpeg / ffprobe / ffplay 実行（動画合成、字幕焼き込み、プレビュー再生）。"
        },
        {
          "source": "backend_mcp,構成.md",
          "text": "`mcp_proc/obs_studio_control.py` — OBS Studio WebSocket 制御。`mcp_proc/ffmpeg_control.py` — ffmpeg / ffprobe / ffplay の薄いランナー。"
        }
      ],
      "short_narration": "OBS Studio の録画操作と ffmpeg の動画変換を、AI からコマンド一本で動かせます。",
      "long_narration": "aidiy_obs_studio_control は動画配信ソフト OBS Studio を AI から操作するツールです。OBS Studio の WebSocket 機能を経由して、配信の開始・停止、録画の開始・停止、シーンの切り替え、ソースの表示・非表示の制御、マイクやスピーカーの音量調整を AI が自動で行えます。aidiy_ffmpeg_control は動画変換ツールの ffmpeg・ffprobe・ffplay を AI から実行するためのツールです。ffmpeg で動画を合成したり字幕を焼き込んだり、ffprobe で動画の長さや形式を調べたり、ffplay でプレビュー再生したりできます。スペースを含むファイルパスは引数に渡すとき 8.3 形式の短縮名を使う必要があります。この紹介ビデオの制作もこれらのツールを活用しています。",
      "short_audio": "audio/short_scene_006.mp3",
      "long_audio": "audio/long_scene_006.mp3",
      "short_start_sec": 42.144,
      "short_duration_sec": 6.576,
      "long_start_sec": 295.68,
      "long_duration_sec": 48.72
    },
    {
      "id": "scene_999",
      "title": "ご視聴ありがとうございました",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41,216,255,0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "AIDIY MCP HUB",
      "headline": "ご視聴ありがとうございました。\nMCP で、何を自動化しますか？",
      "lead": "13 サーバーが SSE × ポート 8095 に集約。ブラウザ操作から動画制作まで、AI エージェントが使えるツールとして公開されています。",
      "subtitle": "AiDiy MCP Hub — 13 サーバー、SSE、localhost 限定、Claude Agent SDK 対応。",
      "image": "images/scene_999.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "short_narration": "AI に何を任せてみたいですか。ブラウザ操作も動画制作も、AI と一緒に試してみませんか。",
      "long_narration": "AiDiy の 13 のツールを組み合わせると、開発の繰り返し作業を AI に任せられます。chrome_devtools でブラウザを操作して画面テストを自動化する、logs でサーバーのエラーを自動検知する、text_to_speech でナレーションを生成する、obs_studio_control で録画を自動化する。小さな自動化から始めて、少しずつ AI に任せる範囲を広げていけます。Claude Code や AI エージェントを AiDiy に接続する設定は、設定ファイル AiDiy_mcp.json に SSE の URL を書くだけです。まず 1 本のツールを試して、自分の開発に合った使い方を見つけてみてください。AiDiy の MCP ツールで、AI とともに開発する体験をやってみませんか。",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_start_sec": 48.72,
      "short_duration_sec": 7.536,
      "long_start_sec": 344.4,
      "long_duration_sec": 43.896
    }
  ],
  "short_duration_sec": 56.256,
  "long_duration_sec": 388.296
};
