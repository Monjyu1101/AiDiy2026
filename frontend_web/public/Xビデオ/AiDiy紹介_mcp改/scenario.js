window.SCENARIO = {
  "project_name": "AiDiy紹介_mcp改",
  "version": "duo-v2",
  "title": "AiDiy MCP Hub - FastAPI + HTTP Transport で広がるエージェント連携",
  "assets_policy": {
    "male_avatar": "../vrm/VRM_male.vrm",
    "female_avatar": "../vrm/VRM_female.vrm",
    "tts_male": "edge:male",
    "tts_female": "edge:female",
    "audio_output_dir": "frontend_web/public/Xビデオ/AiDiy紹介_mcp改/audio"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "この動画で紹介すること",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41,216,255,0.18)",
      "layout": "hero",
      "kicker": "INTRODUCTION",
      "headline": "AiDiy MCP Hub\nHTTP Transport で広がる可能性",
      "image": "images/scene_000.png",
      "source_documents": [
        "backend_mcp/AGENTS.md",
        ".aidiy/knowledge/backend_server,backend_mcp,MCP活用手順.md"
      ],
      "source_summary": "AiDiy MCPハブはポート8095で動くFastAPIアプリ。14のFastMCPサーバーを同居させ、SSE・HTTP Transport・stdioの3トランスポートを提供。HTTP Transport追加によりWeb・Pythonから直接ツールを呼べるようになった。",
      "factual_bullets": [
        "ポート8095でFastAPIが稼働",
        "14種類のFastMCPサーバーを同居",
        "SSE / HTTP Transport / stdio の3トランスポート対応",
        "HTTP Transport追加で応用範囲が拡大",
        "このビデオはAiDiyのビデオ生成機能で作成"
      ],
      "forbidden_elements": [
        "MCPサーバーの数を14以外で言及すること",
        "HTTP Transportが旧来の全機能を完全に置き換えるという誤解",
        "AiDiyが商用製品として販売されているという誤情報"
      ],
      "image_prompt": "Futuristic AI hub control panel with 14 glowing server nodes connected by neon-blue data streams. Central FastAPI logo surrounded by MCP server icons. Dark background with cyan accent colors. Professional and clean design.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AiDiy MCPハブにHTTP Transportが加わり応用範囲が劇的拡大！この動画はAiDiyのビデオ生成機能で作られています。",
          "naration_text": "こんにちは！本日はAiDiyのMCPハブに新しく加わったHTTP Transportと、14種類のMCPサーバーをまとめて紹介します。MCPとはAIエージェントが外部の道具を呼び出すための共通ルールで、AiDiyにはブラウザ操作から動画制作まで14種類の強力なツールが揃っています。なお、この動画はAiDiyのビデオ生成機能を使って自動的に作られています。AIが台本を書き、音声を合成し、画像を生成して動画に仕上げました。",
          "audio": "audio/dlg_000_01_female.mp3",
          "duration_sec": 32.28
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "HTTP Transport追加でPythonやブラウザから直接MCPを呼べるようになり、活用の幅が大きく広がりましたね。",
          "naration_text": "そうなんです！従来はSSEというストリーミング接続が主流でしたが、HTTP Transportが加わったことで普通のHTTPリクエストでMCPツールを呼び出せるようになりました。PythonのrequestsライブラリやJavaScriptのfetchで直接エージェントを動かせる点が革新的で、既存のシステムへのAI機能組み込みが格段に楽になっています。",
          "audio": "audio/dlg_000_02_male.mp3",
          "duration_sec": 20.64
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "14のMCPサーバーはブラウザ操作からDB確認、音声処理、画像・動画生成まで多彩なカバー範囲を持ちます！",
          "naration_text": "AiDiyのMCPハブには、ブラウザの自動操作・デスクトップのスクリーンショット・データベースへのアクセス・コードの品質チェック・差分バックアップ・AI画像生成・AI動画生成・音声認識・音声合成・OBS制御・FFmpeg操作まで、実に多彩な14種類のツールが揃っています。組み合わせることで強力な自動化パイプラインが実現します。",
          "audio": "audio/dlg_000_03_female.mp3",
          "duration_sec": 25.008
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "MCPの基本からHTTP Transportの革新、各サーバーの役割まで順番に見ていきましょう！",
          "naration_text": "それでは早速、MCPとは何かという基本から始めて、HTTP Transportが何を変えたか、そして14のMCPサーバーそれぞれの役割まで、グループ別に順番に見ていきます。実際の使い方の例も交えながら解説しますので、AiDiyを初めて知る方にも分かりやすくお届けします。",
          "audio": "audio/dlg_000_04_male.mp3",
          "duration_sec": 18.456
        }
      ],
      "duration_sec": 96.384,
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3"
    },
    {
      "id": "scene_001",
      "title": "MCP とは何か / 位置づけ",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123,140,255,0.18)",
      "kicker": "WHAT IS MCP",
      "headline": "Model Context Protocol\nAI が道具を呼び出す標準規格",
      "image": "images/scene_001.png",
      "source_documents": [
        "backend_mcp/AGENTS.md",
        "AGENTS.md（プロジェクト全体）"
      ],
      "source_summary": "MCPはModel Context Protocolの略で、AIエージェントが外部ツールやデータを呼び出すための標準規格。AiDiyではmcp_main.pyが14のFastMCPインスタンスをStarletteでマウントしポート8095で提供する。",
      "factual_bullets": [
        "MCP = Model Context Protocol（Anthropic提案の標準規格）",
        "mcp_main.py が FastAPI / Starlette 上で動作",
        "14個のFastMCPインスタンスをマウント",
        "ポート8095で統一提供",
        "AiDiy_mcp.json 一つで全ツールを有効化"
      ],
      "forbidden_elements": [
        "MCPがOpenAI独自規格であるという誤情報",
        "AiDiyが唯一のMCP実装であるという誤解",
        "設定なしで自動的に使えるという誇張"
      ],
      "image_prompt": "Architecture diagram showing FastAPI server on port 8095 with 14 MCP nodes arranged in a hub pattern. Glowing blue connections between AI agent (Claude Code) and MCP tools. Clean technical illustration. Dark theme with purple accents.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "MCPは難しそうに聞こえますが、要はAIエージェントが外部の道具を使うための共通ルールです。",
          "naration_text": "MCPは『Model Context Protocol』の略で、AIエージェントが外部のツールやデータを利用するための標準規格です。難しく聞こえますが、要は『AIが使える道具箱の共通ルール』です。たとえばブラウザを操作したり、データベースを確認したりという作業を、AIが自分の判断で呼び出せるようにします。Anthropicが提案してClaudeを通じて広まったこの規格は、今やAI開発の重要な標準になっています。",
          "audio": "audio/dlg_001_01_female.mp3",
          "duration_sec": 28.92
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "AiDiyではポート8095の1本のサーバーに14種類のMCPツールをすべてまとめています。",
          "naration_text": "AiDiyでは、mcp_main.pyという1本のFastAPIアプリが14個のFastMCPインスタンスをStarletteのMountで合成してポート8095番で動いています。外部からはURLひとつでアクセスでき、AiDiy_mcp.jsonという設定ファイルにURLを書くだけで、Claude CodeやAIエージェントがすべての道具を使えるようになります。この一カ所にまとめる設計のおかげで管理がシンプルです。",
          "audio": "audio/dlg_001_02_male.mp3",
          "duration_sec": 24.168
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "SSE・HTTP Transport・stdioの3接続方式を同じポートで使い分けられるのが便利ですよね！",
          "naration_text": "AiDiyのMCPハブは同じポート8095で3つの接続方式に対応しています。SSEはClaude Codeなど従来のAI開発ツールが使う方式です。Streamable HTTP Transportは普通のHTTPリクエストでMCPツールを呼べる新方式で、今回の目玉機能です。stdioはコマンドラインからMCPを使うための標準入出力方式です。用途に合わせて最適な方式を選べます。",
          "audio": "audio/dlg_001_03_female.mp3",
          "duration_sec": 30.048
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Claude Code など AI 開発ツールからは設定ファイル一つで14種類のツールが全部使えます。",
          "naration_text": "Claude Codeなどのエージェント開発環境では、AiDiy_mcp.jsonという設定ファイルにMCPサーバーのURLを記述するだけで、14種類のツールがすべて使えるようになります。エージェントは必要なときに適切なツールを自動的に選んで呼び出せます。これがMCPの大きな魅力で、開発者はツールを個別に統合する手間なく、AIの能力を大幅に拡張できるわけです。",
          "audio": "audio/dlg_001_04_male.mp3",
          "duration_sec": 23.04
        }
      ],
      "duration_sec": 106.176,
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3"
    },
    {
      "id": "scene_002",
      "title": "HTTP Transport が変えたこと",
      "accent": "#ff7043",
      "accent_soft": "rgba(255,112,67,0.18)",
      "kicker": "HTTP TRANSPORT",
      "headline": "FastAPI × HTTP Transport\nWeb・Python から直接エージェント実行",
      "image": "images/scene_002.png",
      "source_documents": [
        "backend_mcp/AGENTS.md",
        ".aidiy/knowledge/backend_server,backend_mcp,MCP活用手順.md"
      ],
      "source_summary": "Streamable HTTP Transportの追加により、Python requestsやJavaScript fetchなどの通常HTTPクライアントからMCPツールを呼び出せるようになった。GET /list でツール一覧も取得可能。",
      "factual_bullets": [
        "requests.post('http://localhost:8095/aidiy_sqlite/query') でSQLite呼び出し可能",
        "GET http://localhost:8095/{mcp_name}/list でツール一覧をJSON取得",
        "SSE・HTTP Transport・stdio が同一ポート8095で動作",
        "バックエンドルーターやPythonスクリプトからも直接利用可能",
        "AI専用ツール不要でMCP機能にアクセス可能"
      ],
      "forbidden_elements": [
        "HTTP TransportがSSEより高性能であるという根拠のない断定",
        "セキュリティ設定なしで外部公開しても安全だという誤解",
        "全MCPツールがHTTP Transportで完全に動作するという過度な断定"
      ],
      "image_prompt": "Split diagram showing Python script and web browser on left, connected via HTTP arrows to AiDiy MCP Hub on right. Code snippet showing requests.post example. Glowing connection lines in orange-red. Modern dark UI style with code annotations.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "HTTP Transport追加で、AI開発ツールなしでも普通のHTTPリクエストだけでMCPが使えます！",
          "naration_text": "今回の最大のポイントです。Streamable HTTP Transportが追加されたことで、Claude CodeなどのAI専用開発ツールを使わなくても、普通のHTTPリクエストだけでMCPのツールを呼び出せるようになりました。これは開発の幅を大きく広げるアップデートで、PythonのrequestsライブラリやJavaScriptのfetchで直接MCP機能にアクセスできます。",
          "audio": "audio/dlg_002_01_female.mp3",
          "duration_sec": 24.72
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "requests.post でMCPを直接呼べるので、既存のPythonスクリプトへのAI機能追加が格段に楽になります。",
          "naration_text": "まさにそこが革新的なところです。requests.post('http://localhost:8095/aidiy_sqlite/query')のようなシンプルなコードで、AiDiyのSQLiteデータベースにアクセスしたり、画像を生成したり、音声を合成したりできます。既存のPythonスクリプトや業務システムに数行追加するだけでAIツールが使えるようになるので、エージェントのフル実装なしに強力な機能を活用できます。",
          "audio": "audio/dlg_002_02_male.mp3",
          "duration_sec": 26.112
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "WebブラウザのfetchからもMCPツールが叩けるので、フロントエンドから直接AI機能が呼べますね！",
          "naration_text": "ブラウザのJavaScriptからもfetch APIで直接MCPツールを呼び出せます。VueやReactで作ったWebアプリから直接AiDiyの画像生成や音声合成を呼べるということです。バックエンドを経由せずにフロントエンドから直接AI機能にアクセスできるので、プロトタイピングのスピードも大幅に上がります。",
          "audio": "audio/dlg_002_03_female.mp3",
          "duration_sec": 20.904
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "GET /list でツール一覧が動的に取得できるので、プログラムが使える機能を自分で発見できます。",
          "naration_text": "http://localhost:8095/aidiy_chrome_devtools/listへのGETリクエストで、そのMCPサーバーが持つツール一覧をJSON形式で取得できます。自動化スクリプトが利用可能なツールを動的に発見して使うことができるわけです。この自己記述的な仕組みのおかげで、ドキュメントを事前に調べなくてもプログラムが賢く動いてくれます。",
          "audio": "audio/dlg_002_04_male.mp3",
          "duration_sec": 21.96
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "SSE・HTTP・stdioが同一ポートで共存する設計は管理コストを最小化するスマートな選択です！",
          "naration_text": "3つのトランスポートが同じポート8095で動いている点は、運用上とても重要です。ファイアウォールで開けるポートは一つで済み、管理が楽になります。AIエージェントはSSEで、PythonスクリプトはHTTP Transportで、コマンドラインツールはstdioで、それぞれが最適な方式を選べます。この柔軟性こそがAiDiy MCPハブの強みのひとつです。",
          "audio": "audio/dlg_002_05_female.mp3",
          "duration_sec": 25.464
        }
      ],
      "duration_sec": 119.16,
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3"
    },
    {
      "id": "scene_003",
      "title": "14 MCP サーバー全体俯瞰",
      "accent": "#4caf50",
      "accent_soft": "rgba(76,175,80,0.18)",
      "kicker": "14 MCP SERVERS",
      "headline": "14 の MCP サーバー\nブラウザ操作から動画制作まで",
      "image": "images/scene_003.png",
      "source_documents": [
        "backend_mcp/AGENTS.md",
        "AGENTS.md（プロジェクト全体）"
      ],
      "source_summary": "AiDiyのMCPハブは14のサーバーを4カテゴリに分類できる。①ブラウザ・デスクトップ系2つ、②データ確認・開発補助系4つ、③コード支援・バックアップ・音声系4つ、④メディア生成・制作系4つ。",
      "factual_bullets": [
        "ブラウザ系: chrome_devtools, desktop_capture（2台）",
        "データ系: sqlite, postgres, logs, code_check（4台）",
        "音声・保全系: backup, speech_to_text, text_to_speech（3台）",
        "メディア系: image_generation, movie_generation, obs_studio_control, ffmpeg_control（4台）",
        "合計14台"
      ],
      "forbidden_elements": [
        "各サーバーの機能範囲を誇張した記述",
        "無料プロバイダーのみで全機能が使えるという誤解",
        "サーバー数を14以外で表記すること"
      ],
      "image_prompt": "Visual map of 14 MCP servers organized in 4 color-coded groups. Each server shown as an icon with Japanese label. Connected to central AiDiy MCP Hub with glowing lines. Groups: Browser/Desktop (cyan), Data/Dev (blue), Audio/Backup (purple), Media (orange). Clean infographic style.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "14のMCPサーバーを機能別に分けると大きく4カテゴリになります！",
          "naration_text": "AiDiyのMCPハブには合計14種類のサーバーが揃っています。機能別に分けると、ブラウザ・デスクトップ操作系、データ確認・開発補助系、バックアップ・音声処理系、メディア生成・制作系という4カテゴリになります。それぞれが異なるニーズに対応しており、組み合わせると強力な自動化パイプラインが作れます。",
          "audio": "audio/dlg_003_01_female.mp3",
          "duration_sec": 22.824
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "ブラウザ・デスクトップ系は2つ。Chromeの自動操作と画面キャプチャです。",
          "naration_text": "まずブラウザ・デスクトップ系は2サーバーです。aidiy_chrome_devtoolsはChrome DevTools Protocolを使ってブラウザを自在に操作できるサーバーです。URLへの移動・クリック・フォーム入力・スクリーンショットなどが使えます。aidiy_desktop_captureはPCの画面全体や特定ウィンドウをキャプチャするサーバーです。Chromeに限らずあらゆるアプリの画面を取得できます。",
          "audio": "audio/dlg_003_02_male.mp3",
          "duration_sec": 22.752
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "データ確認・開発補助系は4つ。SQLite・PostgreSQL・ログ確認・コードチェックが揃います。",
          "naration_text": "データ確認・開発補助系には4サーバーがあります。aidiy_sqliteはAiDiyのSQLiteデータベースを読み書きできます。aidiy_postgresは外部PostgreSQLへの接続・確認ができます。aidiy_logsはバックエンドサーバーのログをリアルタイムで確認できます。aidiy_code_checkはPythonのruffリントとTypeScriptの型チェックを実行できます。",
          "audio": "audio/dlg_003_03_female.mp3",
          "duration_sec": 23.688
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "コード支援・バックアップ・音声処理系は4つ。コードエージェント・差分バックアップ・音声認識・音声合成が揃います。",
          "naration_text": "コード支援・バックアップ・音声処理系には4つのサーバーがあります。aidiy_code_agentsがAIコードエージェントをCLI経由で実行します。aidiy_backupが差分バックアップを自動保存し、aidiy_speech_to_textが音声をテキストに変換、aidiy_text_to_speechがテキストを音声に合成します。",
          "audio": "audio/dlg_003_04_male.mp3",
          "duration_sec": 18.288
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "メディア生成・制作系は4つ。画像・動画生成にOBS・FFmpegが加わりAIが動画を丸ごと作れます！",
          "naration_text": "最後のカテゴリはメディア生成・制作系で4サーバーあります。aidiy_image_generationでAIが画像を生成、aidiy_movie_generationでAI動画を生成、aidiy_obs_studio_controlでOBS Studioの録画・配信・シーン切り替えを制御、aidiy_ffmpeg_controlで動画編集・変換・字幕付加を行えます。この4つを組み合わせるとAIが台本から完成動画まで自動で作れる強力なパイプラインが実現します。",
          "audio": "audio/dlg_003_05_female.mp3",
          "duration_sec": 29.16
        }
      ],
      "duration_sec": 116.712,
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3"
    },
    {
      "id": "scene_004",
      "title": "ブラウザ・デスクトップ・DB・ログ系",
      "accent": "#2196f3",
      "accent_soft": "rgba(33,150,243,0.18)",
      "kicker": "BROWSER & DATA",
      "headline": "ブラウザ操作・画面取得・DB 確認\nAI がデータを自在に扱う",
      "image": "images/scene_004.png",
      "source_documents": [
        "backend_mcp/mcp_proc/各ファイル",
        "backend_mcp/AGENTS.md"
      ],
      "source_summary": "chrome_devtoolsはCDPでChromeを完全制御。desktop_captureはOS全体の画面キャプチャ。sqliteはAiDiy DB読み書き（allow_write要明示）、postgresは外部PostgreSQL確認、logsはbackend_serverとbackend_mcpのログ末尾・エラー抽出に対応。",
      "factual_bullets": [
        "chrome_devtools: CDP経由でのクリック・入力・スクリーンショット・コンソール・ネットワーク監視",
        "desktop_capture: 全モニター / ウィンドウタイトル / カーソル周辺 / 領域指定のキャプチャモード",
        "sqlite: allow_write=True のときのみ書き込み許可",
        "postgres: 外部DSN指定可能",
        "logs: grep正規表現でのフィルタ・最新エラーのTraceback付き抽出"
      ],
      "forbidden_elements": [
        "chrome_devtoolsがFirefoxなど他ブラウザにも対応するという誤情報",
        "sqliteが本番環境での大容量処理に最適という過大評価",
        "postgresが任意の外部サービスにデフォルトで接続できるという誤解"
      ],
      "image_prompt": "Four panels showing: Chrome browser being controlled by code (DevTools), desktop screenshot tool with multi-monitor display, SQLite and PostgreSQL database icons with query results, server log terminal with highlighted error lines. Blue tech theme with dark background.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_chrome_devtoolsはChromeをAIが直接操作するサーバー。クリックから音声取得まで何でもできます！",
          "naration_text": "aidiy_chrome_devtoolsは、Chrome DevTools Protocolを通じてブラウザをプログラムから完全制御できるMCPサーバーです。URLへのアクセス・要素のクリック・テキスト入力・スクリーンショット撮影・コンソールログの取得・ネットワークリクエストの監視など、ブラウザでできることのほとんどをAIから実行できます。Webアプリのテスト自動化や、サイトからの情報収集に特に有効です。",
          "audio": "audio/dlg_004_01_female.mp3",
          "duration_sec": 26.904
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "aidiy_desktop_captureはChromeに限らず画面全体や特定ウィンドウを高精度でキャプチャできる強みがあります。",
          "naration_text": "aidiy_desktop_captureは、OSレベルのスクリーンショット機能を提供するMCPサーバーです。全モニター・特定モニター・カーソル周辺の矩形領域・特定ウィンドウタイトルによる絞り込みなど、柔軟なキャプチャモードを持っています。AIが自分の目で現在の画面状態を確認したいときに使います。Chromeに限らずあらゆるアプリの画面をキャプチャできる点がchrome_devtoolsとの大きな違いです。",
          "audio": "audio/dlg_004_02_male.mp3",
          "duration_sec": 23.568
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_sqliteとaidiy_postgresはDBの確認ツール。書き込み時は明示的な許可フラグが必要で安全設計です。",
          "naration_text": "aidiy_sqliteはAiDiyが使うSQLiteデータベースへのアクセスを提供します。テーブル一覧・列情報・外部キー・SELECTクエリの実行などができます。書き込みはallow_write=Trueを明示したときだけ許可される安全な設計です。aidiy_postgresは外部のPostgreSQLサーバーへのアクセスに使います。DSN文字列で接続先を指定でき、本番データベースの内容確認やデバッグに活用できます。",
          "audio": "audio/dlg_004_03_female.mp3",
          "duration_sec": 28.272
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "aidiy_logsはサーバーのログをリアルタイム確認でき、AIが自律的にデバッグを進められます。",
          "naration_text": "aidiy_logsは、backend_serverとbackend_mcpのログファイルをリアルタイムで取得できるMCPサーバーです。最新のエラーをTraceback付きで抽出する機能や、正規表現でログを絞り込む機能があります。AIエージェントがコードを変更した後に自分でログを確認してエラーの原因を特定し、デバッグ作業をAIが自律的に進める際に非常に役立ちます。",
          "audio": "audio/dlg_004_04_male.mp3",
          "duration_sec": 21.96
        }
      ],
      "duration_sec": 100.704,
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3"
    },
    {
      "id": "scene_005",
      "title": "コード支援・バックアップ・音声系",
      "accent": "#9c27b0",
      "accent_soft": "rgba(156,39,176,0.18)",
      "kicker": "CODE & AUDIO",
      "headline": "品質確認・バックアップ・音声処理\n開発を支える縁の下の力持ち",
      "image": "images/scene_005.png",
      "source_documents": [
        "backend_mcp/mcp_proc/各ファイル",
        "backend_mcp/AGENTS.md"
      ],
      "source_summary": "aidiy_code_check(ruff/TypeScript型チェック)、aidiy_code_agents(コードエージェント実行)、aidiy_backup(差分バックアップ)、aidiy_speech_to_text(音声認識)、aidiy_text_to_speech(音声合成)の5サーバー。",
      "factual_bullets": [
        "aidiy_code_check: ruff / TypeScript 型チェックでコード品質を即時確認",
        "aidiy_code_agents: copilot_cli / codex_cli 等の CLI 経由でエージェント実行",
        "aidiy_backup: 差分バックアップ方式で変更ファイルを日時付き自動保存",
        "aidiy_speech_to_text: speech_recognition / OpenAI Whisper で音声認識",
        "aidiy_text_to_speech: Edge / OpenAI / Gemini / FreeAI で音声合成"
      ],
      "forbidden_elements": [
        "code_checkがすべてのプログラミング言語に対応するという誇張",
        "backupが完全なGit版管理を提供するという誤解",
        "speech_to_textの認識精度に関する保証的な表現"
      ],
      "image_prompt": "Four tool panels: Python code with ruff lint check marks, file backup timeline with diff statistics, waveform audio input converted to text, text synthesized to sound wave. Purple accent theme. Clean developer tool aesthetic.",
      "dialogue": [
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "aidiy_code_agentsはCLI経由でAIコードエージェントを実行できる、AiDiy独自の強力なサーバーです！",
          "naration_text": "aidiy_code_agentsは、copilot_cli・codex_cli・antigravity_cli・opencode_cliなど複数のコードエージェントCLIをMCP経由で呼び出せるサーバーです。プロジェクトパスや最大ターン数・使用モデルを指定して実行でき、AIがコードを自律的に書き・確認・修正するエージェントループをMCPツールとして完結できます。",
          "audio": "audio/dlg_005_01_male.mp3",
          "duration_sec": 19.152
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_code_checkはAIが書いたコードをすぐチェックできるサーバー。まるで自動校正機能ですね！",
          "naration_text": "aidiy_code_checkは、PythonとTypeScriptのコード品質チェックを実行できるMCPサーバーです。Pythonはpy_compileによる構文チェックとruffによるリントチェックの2種類があります。TypeScriptはvue-tscを使った型チェックが実行できます。AIがコードを書いた直後に自動でチェックをかけ、問題があれば修正するサイクルが自律的に回せます。コード品質を人間が確認する前にAIが自分で担保できます。",
          "audio": "audio/dlg_005_02_female.mp3",
          "duration_sec": 28.848
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "aidiy_backupは差分バックアップ方式で、AIが変更したファイルを日時付きで自動保存していきます。",
          "naration_text": "aidiy_backupは、AiDiyプロジェクトの差分バックアップを管理するMCPサーバーです。初回は全件スナップショットを取り、以降は変更があったファイルだけを日時フォルダに保存します。どのファイルが変更されたかの一覧取得・特定期間の変更確認・ファイルのビフォーアフター比較・変更行数の統計取得などの機能があります。AIコードエージェントが複数ファイルを変更した前後で何が変わったかを追跡するのに役立ちます。",
          "audio": "audio/dlg_005_03_male.mp3",
          "duration_sec": 25.584
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_speech_to_textとaidiy_text_to_speechはセットで使うことが多い音声処理の2兄弟ですね！",
          "naration_text": "aidiy_speech_to_textは音声ファイルやマイク入力をテキストに変換するMCPサーバーです。Python標準のspeech_recognitionとOpenAI Whisperの2プロバイダーに対応し、WAVファイルパスまたはbase64エンコードで渡せます。一方aidiy_text_to_speechはテキストを音声MP3ファイルに変換します。Edge TTS・OpenAI・Google Gemini・FreeAIの4プロバイダーから選べ、声の種類・言語・速度も指定できます。",
          "audio": "audio/dlg_005_04_female.mp3",
          "duration_sec": 32.064
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "この2つを組み合わせると、音声入力を処理して音声で返すボイスアシスタントが手軽に実現できますね。",
          "naration_text": "aidiy_speech_to_textとaidiy_text_to_speechを組み合わせると、マイクで話しかけた内容をテキスト化し、AIが処理して音声で回答するボイスアシスタントのフローが、シンプルなHTTP呼び出しだけで構築できます。AiDiyのアバター機能やAIコア機能とも連携しており、テキスト・音声・画像が統合された豊かなインタラクションを実現しています。",
          "audio": "audio/dlg_005_05_male.mp3",
          "duration_sec": 19.752
        }
      ],
      "duration_sec": 125.4,
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3"
    },
    {
      "id": "scene_006",
      "title": "メディア生成・OBS・FFmpeg 系",
      "accent": "#ff5722",
      "accent_soft": "rgba(255,87,34,0.18)",
      "kicker": "MEDIA CREATION",
      "headline": "AI 画像・動画生成・OBS・FFmpeg\n創作の可能性が無限に広がる",
      "image": "images/scene_006.png",
      "source_documents": [
        "backend_mcp/mcp_proc/各ファイル",
        "backend_mcp/AGENTS.md"
      ],
      "source_summary": "image_generationはOpenAI/Gemini/FreeAI対応の画像生成。movie_generationはGoogle Gemini Veo対応の動画生成（4〜8秒）。obs_studio_controlはWebSocket APIでOBS Studio制御。ffmpeg_controlはffmpeg/ffprobe/ffplayをMCPから呼び出し可能。",
      "factual_bullets": [
        "image_generation: OpenAI gpt-image-2/DALL-E 3・Gemini・FreeAI対応",
        "movie_generation: Veo 3.1 / Veo 2.0対応・4〜8秒・720p/1080p",
        "obs_studio_control: 録画・配信・シーン切り替え・ソース表示/非表示・音声ミュート",
        "ffmpeg_control: 動画切り出し・字幕焼き込み・発話区間自動検出・プレビュー再生",
        "動画生成はポーリング最大10分で完了待機"
      ],
      "forbidden_elements": [
        "動画生成が秒単位で完了するという誇張",
        "OBS制御がOBS以外の配信ソフトにも対応するという誤情報",
        "FFmpegが商用コンテンツを制限なく利用できるという誤解"
      ],
      "image_prompt": "Four creative panels: AI generating colorful scene image from prompt, short video clip being created by AI, OBS Studio interface with scene switching, FFmpeg command line video editing. Warm orange-red theme. Dynamic and creative visual style.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_image_generationはプロンプトを送るだけでAIが画像を自動生成してくれます！",
          "naration_text": "aidiy_image_generationは、テキストプロンプトからAIが画像を生成するMCPサーバーです。OpenAI（gpt-image-2やDALL-E 3）・Google Gemini・FreeAIの3プロバイダーに対応しています。サイズや品質の指定もでき、参照画像を渡して似た画像を作る機能もあります。この動画の各シーンの背景画像も、aidiy_image_generationで自動生成されています。",
          "audio": "audio/dlg_006_01_female.mp3",
          "duration_sec": 25.896
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "aidiy_movie_generationはGoogle Gemini VeoでAIが動画を自動生成できる最先端ツールです！",
          "naration_text": "aidiy_movie_generationは、Google Gemini Veoを使ってテキストプロンプトから動画を生成するMCPサーバーです。4〜8秒の短尺動画を16:9や9:16のアスペクト比で生成できます。720pや1080pの解像度に対応し、参照画像から動画を作るimage-to-video機能もあります。動画生成には数分かかりますが、AIが自律的に待機してポーリングを行うため人間が待つ必要がありません。",
          "audio": "audio/dlg_006_02_male.mp3",
          "duration_sec": 26.352
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_obs_studio_controlはOBS Studioを外部から制御できるサーバーで配信・録画の自動化に最適！",
          "naration_text": "aidiy_obs_studio_controlは、OBS Studio WebSocket APIを通じてOBSを外部からコントロールできるMCPサーバーです。録画の開始・停止・配信のオン・オフ・シーンの切り替え・ソースの表示・非表示・音声ミュートの制御などができます。AIが動画の台本に従って自動的にシーンを切り替えながら録画するといった高度な自動化が実現できます。",
          "audio": "audio/dlg_006_03_female.mp3",
          "duration_sec": 26.232
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "aidiy_ffmpeg_controlはffmpegをAIから直接呼べるので、動画切り出し・変換・字幕付加が自在にできます。",
          "naration_text": "aidiy_ffmpeg_controlは、ffmpeg・ffprobe・ffplayをMCPから直接呼び出せるサーバーです。動画の特定区間の切り出し・形式変換・字幕の焼き込み・画像と音声の合成・音声の波形解析による発話区間の自動検出など、動画編集のあらゆる操作をAIが自律的に実行できます。この動画自体も、aidiy_ffmpeg_controlを使ってシーン動画と音声を合成して完成させています。",
          "audio": "audio/dlg_006_04_male.mp3",
          "duration_sec": 24.0
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "画像・音声・動画生成にOBS・FFmpegが揃い、AIが動画を完全自動で作れる環境が完成しました！",
          "naration_text": "image_generation・text_to_speech・movie_generation・obs_studio_control・ffmpeg_controlの5つを組み合わせると、AIが台本を受け取りシーンごとに画像を生成し、ナレーション音声を合成し、ffmpegで映像と音声を組み合わせて最終的な動画ファイルを出力するという完全自動の動画制作パイプラインが実現します。まさにAIクリエイターの誕生です。",
          "audio": "audio/dlg_006_05_female.mp3",
          "duration_sec": 25.152
        }
      ],
      "duration_sec": 127.632,
      "short_audio": "audio/short_scene_006.mp3",
      "long_audio": "audio/long_scene_006.mp3"
    },
    {
      "id": "scene_999",
      "title": "まとめ",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41,216,255,0.18)",
      "layout": "hero",
      "kicker": "SUMMARY",
      "headline": "AiDiy MCP Hub\n14 のツールで AI 開発を加速",
      "image": "images/scene_999.png",
      "source_documents": [
        "backend_mcp/AGENTS.md",
        ".aidiy/knowledge/backend_server,backend_mcp,MCP活用手順.md"
      ],
      "source_summary": "AiDiy MCPハブは14のFastMCPサーバーとFastAPI+HTTP Transportによる3トランスポート対応で、AIエージェントからPythonスクリプト・Webアプリまで幅広い活用が可能。",
      "factual_bullets": [
        "14サーバーを4カテゴリに整理（ブラウザ・データ・音声・メディア）",
        "HTTP Transport追加でPython/Webから直接MCPを呼び出し可能",
        "このビデオはAiDiyのビデオ生成機能で自動生成",
        "AiDiyはオープンソースプロジェクト"
      ],
      "forbidden_elements": [
        "AiDiyが有償サービスであるという誤情報",
        "将来機能を確定事項として断定すること",
        "チャンネル登録数や利用者数に関する根拠のない数値"
      ],
      "image_prompt": "Summary scene with AiDiy MCP Hub at center, 14 glowing server nodes arranged in circular orbit pattern. Background shows completed video creation pipeline with all tools connected. Cyan blue glow. Celebratory and forward-looking atmosphere.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "今回はAiDiy MCPハブの14サーバーとHTTP Transport追加による革新をご紹介しました！",
          "naration_text": "本日はAiDiyのMCPハブについて詳しくご紹介しました。Model Context Protocolの基本から始まり、FastAPIとHTTP Transportを組み合わせた新しいインターフェースの追加、そしてブラウザ操作・データベース確認・コードチェック・バックアップ・音声処理・AI画像生成・動画生成・OBS制御・FFmpeg操作まで、14種類のMCPサーバーそれぞれの役割を解説しました。",
          "audio": "audio/dlg_999_01_female.mp3",
          "duration_sec": 27.648
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "HTTP Transport追加が大きな転換点でした。AI専用ツール不要で普通のHTTPからMCPが使えるようになった。",
          "naration_text": "今回の最大のポイントを改めて強調したいと思います。Streamable HTTP Transportの追加により、Claude CodeなどのAI専用開発ツールがなくても、PythonのrequestsやJavaScriptのfetchという普通のHTTPクライアントだけでMCPツールを呼び出せるようになりました。これは既存のWebアプリや業務システムへのAI機能の組み込みを劇的に簡単にするアップデートです。",
          "audio": "audio/dlg_999_02_male.mp3",
          "duration_sec": 22.08
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "14のサーバーを組み合わせると、ブラウザ操作から完全自動動画制作まで本当に幅広いことができますね！",
          "naration_text": "AiDiyのMCPハブが持つ14のサーバーを組み合わせれば、AIエージェントがブラウザを操作しながらデータを収集し、データベースに保存して、コードを書いてチェックし、結果を画像・音声・動画にまとめて自動配信するというエンドツーエンドの自動化パイプラインが実現できます。個々のツールの力もさることながら、組み合わせることで生まれるシナジーが本当の強みです。",
          "audio": "audio/dlg_999_03_female.mp3",
          "duration_sec": 23.928
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "まるでAIに14人のスペシャリストがいる感覚ですね！しかも24時間休まず働いてくれます。",
          "naration_text": "そうですね！ブラウザ操作の専門家・データベースの専門家・コード品質の番人・バックアップ担当者・音声処理エンジニア・画像クリエイター・動画制作スタッフ・放送技術担当者と、それぞれの分野のスペシャリストが14人集まって、AIの指示に従って動いてくれるようなイメージです。しかも全員が24時間365日休まず働いてくれます！",
          "audio": "audio/dlg_999_04_male.mp3",
          "duration_sec": 20.568
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "この動画もAiDiyが全部作りました！チャンネル登録して、あなたもAiDiyを試してみませんか？",
          "naration_text": "実はこの動画、全部AiDiyが作っています！台本はAIが書き、各シーンの画像はaidiy_image_generationが生成し、ナレーション音声はaidiy_text_to_speechが合成し、映像はaidiy_ffmpeg_controlが編集しました。14のMCPサーバーが連携して生まれた作品です。気に入っていただけたらチャンネル登録をお願いします！AiDiyはオープンソースプロジェクトですので、あなたも今すぐ試せます。ブラウザ操作から動画制作まで、AIと一緒に何でも作れる体験をぜひご自身で味わってみてください。ワクワクしませんか？AiDiyで、あなたの創造力を解き放ちましょう！",
          "audio": "audio/dlg_999_05_female.mp3",
          "duration_sec": 40.968
        }
      ],
      "duration_sec": 135.192,
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3"
    }
  ],
  "total_duration_sec": 927.36,
  "short_duration_sec": 0.0,
  "long_duration_sec": 0.0
};
