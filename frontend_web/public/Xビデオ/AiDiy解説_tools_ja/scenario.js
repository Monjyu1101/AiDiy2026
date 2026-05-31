window.SCENARIO = {
  "project_name": "AiDiy解説_tools_ja",
  "version": "duo-v2",
  "title": "AiDiy TOOL HUB 解説 — 14 MCP サーバーを Web・Python・AI エージェントから統一的に呼び出す",
  "assets_policy": {
    "male_avatar": "../_vrm/VRM_male.vrm",
    "female_avatar": "../_vrm/VRM_female.vrm",
    "tts_male": "edge:male",
    "tts_female": "edge:female",
    "audio_output_dir": "frontend_web/public/Xビデオ/AiDiy解説_tools_ja/audio"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "イントロ — AiDiy TOOL HUB の全体像",
      "accent": "#1a6ea0",
      "accent_soft": "rgba(26, 110, 160, 0.18)",
      "layout": "hero",
      "kicker": "AIDIY TOOL HUB",
      "headline": "backend_tools が\nAiDiy TOOL HUB として進化した",
      "lead": "14 の MCP サーバーが SSE / Streamable HTTP / stdio の 3 トランスポートで提供され、Web・Python・AI エージェントいずれからも統一的に呼び出せます。",
      "image": "images/scene_000.png",
      "source_summary": "AiDiy の backend_tools が AiDiy TOOL HUB として整備され、14 の MCP サーバーが 3 つのトランスポートと HTTP API で統一的に利用可能になった全体概要。この動画は video_generation 機能で自動生成。",
      "factual_bullets": [
        "14 の MCP サーバーがポート 8095 に集約",
        "SSE / Streamable HTTP / stdio の 3 トランスポートを同一ポートで提供",
        "HTTP POST で直接利用でき MCP クライアント不要",
        "Web・Python・AI エージェントから同じインターフェースで呼び出せる",
        "この動画は AiDiy の video_generation 機能で自動生成"
      ],
      "forbidden_elements": [
        "具体的な料金や商用サービスとしての断定",
        "AiDiy が公式リリースされた製品であるかのような誇張"
      ],
      "image_prompt": "A modern tech hub visualization showing 14 connected MCP server nodes surrounding a central glowing hub labeled AiDiy TOOL HUB, with three colored connection lines representing SSE, HTTP, and stdio transports. Clean flat design with blue tones, port 8095 label visible, dark background.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AiDiy TOOL HUB を紹介します。この動画は AiDiy の video_generation 機能で自動生成されました。",
          "naration_text": "今回の動画では、AiDiy の backend_tools が進化して誕生した「AiDiy TOOL HUB」について紹介します。ブラウザ操作から AI による画像・音声・動画の生成、録画制御、コードエージェントまで、開発と自動化に必要なツールが 14 種類まとまったツール基盤です。MCP の 3 つのトランスポートに対応しているので、AI エージェント、Python スクリプト、Web ブラウザのどこからでも統一的に呼び出せます。なお、この動画は AiDiy の video_generation 機能によって自動生成されました。シナリオ作成、画像生成、音声合成まで、すべて AiDiy が担当しています。",
          "audio": "audio/dlg_000_01_female.mp3",
          "duration_sec": 39.936
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "14 の MCP サーバーが 3 つのトランスポートで提供され、どこからでも統一的に使えます。",
          "naration_text": "AiDiy TOOL HUB の大きな特徴は、14 の MCP サーバーを SSE、Streamable HTTP、stdio の 3 つのトランスポートで同時に提供していることです。Claude や Copilot などの AI エージェントから MCP プロトコルで呼び出したり、Python の requests でシンプルな HTTP リクエストを送ったりと、用途に合わせた方法でアクセスできます。すべてポート 8095 のひとつにまとまっているので、管理もシンプルです。",
          "audio": "audio/dlg_000_02_male.mp3",
          "duration_sec": 25.152
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "14 の MCP は 4 つのカテゴリに分類されています。",
          "naration_text": "14 の MCP サーバーは、大きく 4 つのカテゴリで整理できます。まず、Chrome とデスクトップを操作するブラウザ・画面操作系。次に、SQLite、PostgreSQL、ログ、コードチェック、バックアップを扱うデータ管理・開発補助系。続いて、画像・動画・音声を生成する AI 生成系。最後に、OBS、FFmpeg、コードエージェントによる運用自動化系です。今日はこの 4 カテゴリを順番に見ていきます。",
          "audio": "audio/dlg_000_03_female.mp3",
          "duration_sec": 32.136
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "HTTP POST だけで使えるので、MCP クライアントがなくても始められます。",
          "naration_text": "もうひとつ便利な点として、MCP クライアントがなくても HTTP POST でツールを直接呼び出せることがあります。Python の requests.post でリクエストを送るだけでよく、特別なライブラリのセットアップは不要です。ツールの一覧は GET リクエストで確認できるので、どんな機能があるかをすぐ把握できます。自動化スクリプトへの組み込みも手軽に始められるのが嬉しいところです。",
          "audio": "audio/dlg_000_04_male.mp3",
          "duration_sec": 23.472
        }
      ],
      "duration_sec": 120.696
    },
    {
      "id": "scene_001",
      "title": "3 つのトランスポート — SSE / Streamable HTTP / stdio",
      "accent": "#2e86ab",
      "accent_soft": "rgba(46, 134, 171, 0.18)",
      "kicker": "3 TRANSPORTS",
      "headline": "SSE / Streamable HTTP / stdio\n3 トランスポートを同一ポートで提供",
      "lead": "tools_main.py がエントリポイント。ポート 8095 で 3 種の接続方式を同時に受け付けます。",
      "image": "images/scene_001.png",
      "source_summary": "AiDiy TOOL HUB が同一ポート 8095 で SSE、Streamable HTTP、stdio の 3 トランスポートを提供する仕組みの解説",
      "factual_bullets": [
        "tools_main.py が uvicorn でポート 8095 を起動するエントリポイント",
        "stdio gateway は mcp_stdio.py 経由で AI エージェントと標準入出力でやりとり",
        "SSE は Server-Sent Events でリアルタイム通知に対応",
        "Streamable HTTP は最もシンプルな HTTP POST 方式",
        "3 つの方式が同じツール群にアクセスできる"
      ],
      "forbidden_elements": [
        "特定のプロバイダーの料金や SLA の断定",
        "WebSocket と SSE を混同した説明"
      ],
      "image_prompt": "A technical diagram showing three transport protocols: SSE (blue arrow), Streamable HTTP (green arrow), and stdio (orange arrow) all connecting to a single server hub on port 8095. Each protocol labeled with its name. Clean dark background with glowing connection lines, minimalist tech style.",
      "chips": [
        "stdio gateway",
        "SSE Transport",
        "Streamable HTTP Transport",
        "ポート 8095"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "tools_main.py を起動するだけで、3 つのトランスポートが同時に有効になります。",
          "naration_text": "backend_tools の起動には tools_main.py を使います。uvicorn でポート 8095 に立ち上げると、SSE トランスポート、Streamable HTTP トランスポート、stdio ゲートウェイという 3 つの接続方式が同時に有効になります。どの方式を選んでも同じ 14 のツール群にアクセスできるので、呼び出し側の環境に合わせて接続方法を選ぶだけでよいのがポイントです。",
          "audio": "audio/dlg_001_01_female.mp3",
          "duration_sec": 26.304
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "stdio ゲートウェイは Claude Desktop などの AI ツールとの接続に使います。",
          "naration_text": "stdio ゲートウェイは、mcp_stdio.py を経由して AI エージェントと標準入出力でやりとりする方式です。Claude Desktop のような MCP 対応ツールへ設定として登録すれば、そのまま AiDiy TOOL HUB のすべてのツールを AI 側から呼び出せるようになります。セットアップは JSON の設定ファイルにコマンドを書くだけで完了します。",
          "audio": "audio/dlg_001_02_male.mp3",
          "duration_sec": 20.184
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "SSE は長時間の処理やリアルタイム通知に向いています。",
          "naration_text": "SSE トランスポートは、Server-Sent Events を使ってサーバーからクライアントへリアルタイムにデータを送れる方式です。処理に時間がかかるツール、たとえば動画生成や大量の画像生成の途中経過を受け取りたい場合に特に有効です。MCP のストリーミング応答を活用したい場合も、SSE を選ぶのが自然な選択です。",
          "audio": "audio/dlg_001_03_female.mp3",
          "duration_sec": 21.984
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Streamable HTTP は Python の requests.post で直接使える最もシンプルな方式です。",
          "naration_text": "Streamable HTTP は、通常の HTTP POST リクエストでツールを呼び出す最もシンプルな方式です。Python なら requests.post、ブラウザなら fetch を使うだけでよく、MCP クライアントのセットアップが不要なため、自動化スクリプトへの組み込みが手軽です。バックエンドのルーターやスケジューラーから直接ツールを呼び出す場合にも向いています。",
          "audio": "audio/dlg_001_04_male.mp3",
          "duration_sec": 21.408
        }
      ],
      "duration_sec": 89.88
    },
    {
      "id": "scene_002",
      "title": "14 の MCP サーバー一覧",
      "accent": "#e84855",
      "accent_soft": "rgba(232, 72, 85, 0.18)",
      "kicker": "14 MCP SERVERS",
      "headline": "14 の MCP サーバーが\n1 つのポートに集約",
      "lead": "ブラウザ操作・データ管理・AI 生成・運用自動化まで、開発に必要な機能をひとまとめにしました。",
      "image": "images/scene_002.png",
      "source_summary": "AiDiy TOOL HUB に含まれる 14 の MCP サーバーの全体一覧と、4 カテゴリへの分類",
      "factual_bullets": [
        "ブラウザ・画面操作系: aidiy_chrome_devtools, aidiy_desktop_capture",
        "データ管理・開発補助系: aidiy_sqlite, aidiy_postgres, aidiy_logs, aidiy_code_check, aidiy_backup",
        "AI 生成系: aidiy_image_generation, aidiy_movie_generation, aidiy_speech_to_text, aidiy_text_to_speech",
        "運用自動化系: aidiy_obs_studio_control, aidiy_ffmpeg_control, aidiy_code_agents",
        "ツール一覧は GET http://localhost:8095/{mcp_name}/list で確認できる"
      ],
      "forbidden_elements": [
        "MCP サーバーの数を 14 以外で断言すること",
        "カテゴリ分類が公式仕様であるかのような断言"
      ],
      "image_prompt": "A clean grid layout showing 14 MCP server icons organized in 4 color-coded categories: browser tools (blue), data tools (green), AI generation (purple), and automation (orange). Each server has a small icon and label. Modern flat design on dark background.",
      "chips": [
        "aidiy_chrome_devtools",
        "aidiy_desktop_capture",
        "aidiy_sqlite",
        "aidiy_postgres",
        "aidiy_logs",
        "aidiy_code_check",
        "aidiy_backup",
        "aidiy_image_generation",
        "aidiy_movie_generation",
        "aidiy_speech_to_text",
        "aidiy_text_to_speech",
        "aidiy_obs_studio_control",
        "aidiy_ffmpeg_control",
        "aidiy_code_agents"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AiDiy TOOL HUB には合計 14 の MCP サーバーが揃っています。",
          "naration_text": "AiDiy TOOL HUB には、合計 14 の MCP サーバーが用意されています。すべてポート 8095 から利用でき、ツール一覧は GET リクエストで確認できます。Chrome 操作からコードエージェント実行まで、開発と自動化に必要な機能をひとまとめにしたツール集です。それぞれがどんな役割を持っているか、カテゴリ別に見ていきましょう。",
          "audio": "audio/dlg_002_01_female.mp3",
          "duration_sec": 23.52
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "ブラウザと画面を操作する 2 つの MCP があります。",
          "naration_text": "ブラウザ操作・画面操作系には、Chrome DevTools Protocol を使う aidiy_chrome_devtools と、OS のスクリーンショットやウィンドウ操作を担う aidiy_desktop_capture の 2 つがあります。E2E テストや画面の自動確認に活躍するカテゴリです。AI エージェントが自分でブラウザを操作して結果を確認するような使い方もできます。",
          "audio": "audio/dlg_002_02_male.mp3",
          "duration_sec": 19.68
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "データ管理と開発補助には 5 つの MCP があります。",
          "naration_text": "データ管理・開発補助系には 5 つの MCP があります。SQLite の DB 操作を行う aidiy_sqlite、外部 PostgreSQL への接続に対応する aidiy_postgres、バックエンドのログを確認する aidiy_logs、Python と TypeScript の構文チェックを行う aidiy_code_check、そして差分バックアップを管理する aidiy_backup です。開発中に頻繁に使う確認作業を自動化できます。",
          "audio": "audio/dlg_002_03_female.mp3",
          "duration_sec": 26.712
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "AI 生成系の 4 つが画像・動画・音声を自動で作ります。",
          "naration_text": "AI 生成系には 4 つの MCP があります。OpenAI や Gemini を使う aidiy_image_generation、Veo による動画生成の aidiy_movie_generation、Whisper を使う aidiy_speech_to_text、Edge TTS や OpenAI TTS を使う aidiy_text_to_speech です。この動画も、aidiy_text_to_speech で音声を生成し、aidiy_image_generation でシーン画像を作っています。",
          "audio": "audio/dlg_002_04_male.mp3",
          "duration_sec": 22.296
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "OBS・FFmpeg・コードエージェントの 3 つが運用自動化を担います。",
          "naration_text": "運用自動化系には 3 つの MCP があります。OBS Studio を WebSocket で制御する aidiy_obs_studio_control、ffmpeg と ffprobe を実行する aidiy_ffmpeg_control、そして複数の AI コード CLI をまとめて実行できる aidiy_code_agents です。録画から動画処理、コード生成まで、一連の作業を自動化できる頼もしいカテゴリです。",
          "audio": "audio/dlg_002_05_female.mp3",
          "duration_sec": 23.448
        }
      ],
      "duration_sec": 115.656
    },
    {
      "id": "scene_003",
      "title": "ブラウザ操作・画面操作系 MCP",
      "accent": "#f7931e",
      "accent_soft": "rgba(247, 147, 30, 0.18)",
      "kicker": "BROWSER & SCREEN",
      "headline": "Chrome・デスクトップ操作を\n自動化する 2 つの MCP",
      "lead": "aidiy_chrome_devtools と aidiy_desktop_capture で E2E テストや画面確認を自動化します。",
      "image": "images/scene_003.png",
      "source_summary": "aidiy_chrome_devtools と aidiy_desktop_capture の機能、活用方法、組み合わせによる E2E テスト自動化",
      "factual_bullets": [
        "aidiy_chrome_devtools は Chrome DevTools Protocol (CDP) でブラウザを直接制御",
        "navigate, click, fill, screenshot, eval_js, get_console_logs, get_network_logs などのツールが利用可能",
        "aidiy_desktop_capture は OS 全体のスクリーンショット、ウィンドウキャプチャ、カーソル周辺の部分取得に対応",
        "複数モニター対応",
        "2 つを組み合わせることで E2E テストとビジュアル確認を自動化できる"
      ],
      "forbidden_elements": [
        "Selenium や Playwright と同等の機能があるという断言",
        "すべてのブラウザ操作が自動化できるという過度な誇張"
      ],
      "image_prompt": "A split screen visualization: left side shows a Chrome browser window being controlled by code with CDP connection arrows, right side shows a desktop screenshot being captured with a camera icon overlay. Connected by a central AI agent robot icon. Modern tech illustration style with orange accent.",
      "chips": [
        "aidiy_chrome_devtools",
        "aidiy_desktop_capture",
        "CDP",
        "E2E テスト"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_chrome_devtools は Chrome DevTools Protocol でブラウザを直接操作します。",
          "naration_text": "aidiy_chrome_devtools は、Chrome DevTools Protocol を使ってブラウザを直接制御する MCP です。ページへの移動、要素のクリック、テキスト入力、スクリーンショット取得、JavaScript の実行、コンソールログの取得など、ブラウザで行える操作のほぼすべてをコードから自動化できます。AI エージェントが自分でブラウザを操作しながら作業を進めることが可能です。",
          "audio": "audio/dlg_003_01_female.mp3",
          "duration_sec": 24.84
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "ネットワークログやコンソールログを AI がリアルタイムで確認できます。",
          "naration_text": "特に便利なのが、ネットワークリクエストのキャプチャとコンソールログの取得です。install_network_capture や install_console_capture をページに設置しておくと、AI エージェントがエラーや API レスポンスをリアルタイムで読みながら次の操作を判断できます。ブラウザの動作確認や API のデバッグを自動化するのに非常に役立ちます。",
          "audio": "audio/dlg_003_02_male.mp3",
          "duration_sec": 19.272
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_desktop_capture は OS 全体のスクリーンショットを撮ることができます。",
          "naration_text": "aidiy_desktop_capture は、OS 全体のスクリーンショットを撮る MCP です。複数モニターへの対応、特定ウィンドウのキャプチャ、カーソル周辺の部分取得など、用途に合わせた柔軟な撮影が可能です。ブラウザに限らず、デスクトップアプリや外部ツールの状態を確認したいときにも使えます。マウスの現在位置や画面情報の取得も行えます。",
          "audio": "audio/dlg_003_03_female.mp3",
          "duration_sec": 24.456
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "2 つを組み合わせると、見た目まで含めた E2E テストを自動化できます。",
          "naration_text": "aidiy_chrome_devtools と aidiy_desktop_capture を組み合わせると、画面の見た目まで含めた E2E テストが自動化できます。AI が「ボタンをクリックして、スクリーンショットで結果を目視確認して、次のアクションを決める」という流れをそのまま実行できるのが、このツール組み合わせの大きな魅力です。人間の代わりに AI が画面を見ながら作業するイメージです。",
          "audio": "audio/dlg_003_04_male.mp3",
          "duration_sec": 21.504
        }
      ],
      "duration_sec": 90.072
    },
    {
      "id": "scene_004",
      "title": "データ管理・開発補助系 MCP",
      "accent": "#34a853",
      "accent_soft": "rgba(52, 168, 83, 0.18)",
      "kicker": "DATA & DEV",
      "headline": "SQLite・PostgreSQL・ログ・\nコードチェック・バックアップ",
      "lead": "5 つの MCP が開発とデータ管理を支援します。DB 確認からコードチェック、差分バックアップまで。",
      "image": "images/scene_004.png",
      "source_summary": "aidiy_sqlite、aidiy_postgres、aidiy_logs、aidiy_code_check、aidiy_backup の 5 つのデータ管理・開発補助系 MCP の機能解説",
      "factual_bullets": [
        "aidiy_sqlite: AiDiy の SQLite DB に SQL を直接発行、allow_write で書き込みも可能",
        "aidiy_postgres: 外部 PostgreSQL への接続、DSN パラメータで接続先を指定",
        "aidiy_logs: backend_server / backend_tools のログ末尾取得、エラー抽出、正規表現フィルタ",
        "aidiy_code_check: Python 構文チェック、ruff lint、TypeScript 型チェックを MCP 経由で実行",
        "aidiy_backup: 差分バックアップ保存・確認、変更ファイル一覧取得、before/after 比較"
      ],
      "forbidden_elements": [
        "特定の DB バージョンや ruff バージョンに依存した断言",
        "PostgreSQL への接続がすべての環境で動作するという保証"
      ],
      "image_prompt": "Five developer tool cards in a grid: SQLite database icon (green), PostgreSQL elephant logo (blue), log viewer with scrolling text (teal), code checker with checkmarks (lime), and backup shield with diff arrows (olive). Green accent color theme, clean developer tool UI on dark background.",
      "chips": [
        "aidiy_sqlite",
        "aidiy_postgres",
        "aidiy_logs",
        "aidiy_code_check",
        "aidiy_backup"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_sqlite は AiDiy の DB に SQL を直接発行できます。",
          "naration_text": "aidiy_sqlite は、AiDiy の SQLite データベースに対して SQL を直接発行できる MCP です。SELECT でのデータ確認だけでなく、allow_write フラグを付ければ INSERT や UPDATE も実行できます。テーブル一覧やスキーマ情報、件数取得など便利なショートカットも揃っています。AI エージェントが DB の状態を自分で確認しながら作業を進める場面で特に活躍します。",
          "audio": "audio/dlg_004_01_female.mp3",
          "duration_sec": 25.992
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "aidiy_postgres は外部 PostgreSQL への接続に対応しています。",
          "naration_text": "aidiy_postgres は、外部の PostgreSQL データベースへの接続をサポートする MCP です。接続先の DSN を引数で渡すことができ、テーブル一覧、スキーマ確認、SQL 実行を同じインターフェースで行えます。SQLite と PostgreSQL を用途によって使い分けるプロジェクトでも、AI エージェントから一貫した操作が可能なのが利点です。",
          "audio": "audio/dlg_004_02_male.mp3",
          "duration_sec": 21.912
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_logs はエラーの抽出や正規表現フィルタでログを確認できます。",
          "naration_text": "aidiy_logs は、backend_server と backend_tools のログをリアルタイムで確認できる MCP です。ログの末尾取得、エラーの自動抽出、正規表現を使った絞り込みができます。AI エージェントがエラーログを読んで自動的に修正箇所を特定する、というデバッグ自動化のフローに組み込むと特に便利です。ログと DB 確認を組み合わせると、問題の原因追跡が格段にスムーズになります。",
          "audio": "audio/dlg_004_03_female.mp3",
          "duration_sec": 27.072
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "aidiy_code_check は Python と TypeScript の構文チェックを MCP 経由で実行します。",
          "naration_text": "aidiy_code_check は、Python の構文チェックと ruff による lint、TypeScript の型チェックを MCP 経由で実行できます。コードを修正した後に、AI エージェント自身がチェックツールを呼び出して結果を確認し、エラーがあれば修正するサイクルを自動化できます。人間がターミナルで手動実行するのと同じことを、AI が自動で繰り返してくれます。",
          "audio": "audio/dlg_004_04_male.mp3",
          "duration_sec": 21.192
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_backup は差分バックアップで変更ファイルを安全に管理します。",
          "naration_text": "aidiy_backup は、プロジェクトの差分バックアップを自動で取得・管理する MCP です。変更されたファイルだけを記録するため、コードの編集前後を比較したり、特定の日時のファイル状態を確認したりすることが簡単にできます。何かを壊してしまったときでも、バックアップの差分を見れば何が変わったかすぐわかるので、作業中の安心感が格段に上がります。",
          "audio": "audio/dlg_004_05_female.mp3",
          "duration_sec": 24.432
        }
      ],
      "duration_sec": 120.6
    },
    {
      "id": "scene_005",
      "title": "AI 生成系 MCP — 画像・動画・音声",
      "accent": "#8a4fff",
      "accent_soft": "rgba(138, 79, 255, 0.18)",
      "kicker": "AI GENERATION",
      "headline": "画像・動画・音声を\nAI で自動生成する MCP",
      "lead": "aidiy_image_generation / aidiy_movie_generation / aidiy_speech_to_text / aidiy_text_to_speech の 4 つが AI 生成を担います。",
      "image": "images/scene_005.png",
      "source_summary": "aidiy_image_generation、aidiy_movie_generation、aidiy_speech_to_text、aidiy_text_to_speech の 4 つの AI 生成系 MCP の機能と対応プロバイダー",
      "factual_bullets": [
        "aidiy_image_generation: OpenAI (gpt-image-2, DALL-E 3), Gemini, FreeAI に対応",
        "aidiy_movie_generation: Google Veo モデルで最大 8 秒の動画生成、image-to-video にも対応",
        "aidiy_speech_to_text: speech_recognition (無料) と OpenAI Whisper に対応",
        "aidiy_text_to_speech: Edge TTS, OpenAI TTS, Gemini TTS, FreeAI に対応",
        "この動画の画像と音声も AiDiy の生成系 MCP で作られている"
      ],
      "forbidden_elements": [
        "生成品質を保証するような断言",
        "特定のプロバイダーの料金を断言すること",
        "AI 生成コンテンツが常に高品質であるという誇張"
      ],
      "image_prompt": "Four AI generation tool cards arranged in a 2x2 grid: a paintbrush generating a colorful image (blue-purple), a film camera producing video frames (purple), a microphone with sound wave for speech-to-text (teal-green), and a speaker synthesizing text-to-speech audio waves (violet). AI sparkle effects on each card. Dark background with purple accent.",
      "chips": [
        "aidiy_image_generation",
        "aidiy_movie_generation",
        "aidiy_speech_to_text",
        "aidiy_text_to_speech"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_image_generation は複数のプロバイダーで画像を生成できます。",
          "naration_text": "aidiy_image_generation は、OpenAI の gpt-image や DALL-E、Google の Gemini、FreeAI といった複数のプロバイダーに対応した画像生成 MCP です。プロンプトを渡すだけで指定フォルダへの保存まで行ってくれるので、シナリオに沿ったシーン画像を AI が自動で作ることができます。参照画像を渡してスタイルを引き継ぐこともできます。",
          "audio": "audio/dlg_005_01_female.mp3",
          "duration_sec": 23.016
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "aidiy_movie_generation は Google の Veo モデルで動画を自動生成します。",
          "naration_text": "aidiy_movie_generation は、Google の Veo モデルを使って動画を生成する MCP です。テキストプロンプトから最大 8 秒の動画を作れるほか、参照画像を渡す image-to-video 生成にも対応しています。4 秒から 8 秒の長さ、横向き・縦向きのアスペクト比、720p・1080p の解像度など、細かい設定をパラメータで制御できます。動画生成は数分かかる場合があります。",
          "audio": "audio/dlg_005_02_male.mp3",
          "duration_sec": 25.152
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_speech_to_text は音声ファイルをテキストに変換します。",
          "naration_text": "aidiy_speech_to_text は、音声ファイルをテキストに変換する MCP です。speech_recognition ライブラリを使う無料モードと、OpenAI の Whisper を使う高精度モードがあります。ファイルパスを渡すだけで変換結果が返ってくるので、録音した音声の内容確認や字幕生成の素材作成、会議録の自動作成などに活用できます。",
          "audio": "audio/dlg_005_03_female.mp3",
          "duration_sec": 22.872
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "aidiy_text_to_speech はこの動画のナレーション音声も生成しています。",
          "naration_text": "aidiy_text_to_speech は、テキストを音声ファイルに変換する MCP です。Edge TTS、OpenAI TTS、Gemini TTS、FreeAI に対応しており、日本語の female と male 2 つの声を使い分けられます。このビデオのナレーション音声も Edge の female と male を使って生成しています。save_path を指定すれば、指定したファイルへの保存まで一度に行えます。",
          "audio": "audio/dlg_005_04_male.mp3",
          "duration_sec": 23.664
        }
      ],
      "duration_sec": 94.704
    },
    {
      "id": "scene_006",
      "title": "運用自動化系 MCP — OBS・FFmpeg・コードエージェント",
      "accent": "#b8860b",
      "accent_soft": "rgba(184, 134, 11, 0.18)",
      "kicker": "AUTOMATION",
      "headline": "OBS・FFmpeg・コードエージェントで\n運用を完全自動化",
      "lead": "aidiy_obs_studio_control / aidiy_ffmpeg_control / aidiy_code_agents が録画・動画処理・AI コード実行を担います。",
      "image": "images/scene_006.png",
      "source_summary": "aidiy_obs_studio_control、aidiy_ffmpeg_control、aidiy_code_agents の 3 つの運用自動化系 MCP の機能と連携ワークフロー",
      "factual_bullets": [
        "aidiy_obs_studio_control: OBS Studio を WebSocket v5 で制御、録画・配信・シーン切替・音声ミュート",
        "aidiy_ffmpeg_control: ffmpeg / ffprobe / ffplay を MCP 経由で実行、動画トリミング・変換・字幕焼き込み",
        "aidiy_code_agents: claude_sdk, copilot_cli, codex_cli, opencode_cli など複数の AI コード CLI を統一的に実行",
        "3 つを組み合わせると、コード生成→動作確認→録画→編集のサイクルを自動化できる"
      ],
      "forbidden_elements": [
        "OBS を使った配信の収益化や商用利用を断言すること",
        "FFmpeg の特定バージョンに依存した説明"
      ],
      "image_prompt": "Three automation tools connected in a workflow chain: OBS Studio recording interface with red recording indicator (left), FFmpeg video processing pipeline with trim markers and waveform (center), and a code agent robot typing code (right). Connected by gold arrows showing the automation chain. Dark background with amber/gold accent.",
      "chips": [
        "aidiy_obs_studio_control",
        "aidiy_ffmpeg_control",
        "aidiy_code_agents"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_obs_studio_control は OBS Studio を WebSocket で制御できます。",
          "naration_text": "aidiy_obs_studio_control は、OBS Studio を WebSocket v5 プロトコルで制御する MCP です。録画の開始と停止、配信の制御、シーンの切り替え、ソースの表示・非表示、入力音声のミュート操作などを、Python スクリプトや AI エージェントから直接コントロールできます。OBS を手動で操作する必要がなくなるため、録画ワークフローの自動化が大幅に進みます。",
          "audio": "audio/dlg_006_01_female.mp3",
          "duration_sec": 26.232
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "ブラウザ再生と OBS 録画を組み合わせると、動画制作が自動化できます。",
          "naration_text": "実際の使い方としては、ブラウザで動画プレイヤーを開いて自動再生を始めた後、OBS の録画を開始し、再生が終わったら録画を停止するという流れを、すべてスクリプトから自動化できます。aidiy_chrome_devtools と組み合わせれば、ブラウザ操作から録画制御まで一連の流れを人の手を介さずに実行できます。この動画の制作でも同様の仕組みを活用しています。",
          "audio": "audio/dlg_006_02_male.mp3",
          "duration_sec": 22.848
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_ffmpeg_control は ffmpeg・ffprobe・ffplay を MCP 経由で実行できます。",
          "naration_text": "aidiy_ffmpeg_control は、ffmpeg、ffprobe、ffplay を MCP 経由で実行できるツールです。動画のトリミング、フォーマット変換、字幕焼き込み、動画上へのオーバーレイといった処理が可能です。さらに、音声の有無から開始・終了点を自動検出する機能もあり、OBS で録画した素材の余白を自動でカットするワークフローに自然につながります。",
          "audio": "audio/dlg_006_03_female.mp3",
          "duration_sec": 24.288
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "aidiy_code_agents は複数の AI コード CLI をまとめて実行できます。",
          "naration_text": "aidiy_code_agents は、Claude SDK、Copilot CLI、Codex CLI、OpenCode CLI など、複数の AI コードエージェント CLI をまとめて実行できる MCP です。プロンプトと作業ディレクトリを渡すだけで、指定した AI エージェントがコード作業を実行し結果を返してくれます。Claude や Copilot といった複数の AI を、状況に合わせて使い分けられる点が魅力です。",
          "audio": "audio/dlg_006_04_male.mp3",
          "duration_sec": 24.12
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "3 つの MCP を組み合わせると、コード生成から動画完成まで自動化できます。",
          "naration_text": "OBS 制御、FFmpeg 処理、コードエージェントの 3 つを組み合わせると、撮影・編集・コード生成のサイクルを一貫して自動化できます。コードエージェントが実装を完了し、OBS が動作画面を録画し、FFmpeg がトリミングして完成動画を出力するという流れを、人の手を最小限に抑えて回すことができます。これが AiDiy TOOL HUB の真の自動化パワーです。",
          "audio": "audio/dlg_006_05_female.mp3",
          "duration_sec": 24.888
        }
      ],
      "duration_sec": 122.376
    },
    {
      "id": "scene_999",
      "title": "まとめ — AiDiy TOOL HUB で開発と自動化の壁を越える",
      "accent": "#1a6ea0",
      "accent_soft": "rgba(26, 110, 160, 0.18)",
      "layout": "hero",
      "kicker": "AIDIY TOOL HUB",
      "headline": "AiDiy TOOL HUB で\n開発と自動化の壁を越える",
      "lead": "14 の MCP サーバーを Web・Python・AI エージェントいずれからも統一的に呼び出せる AiDiy TOOL HUB。あなたなら何を自動化しますか？",
      "image": "images/scene_999.png",
      "source_summary": "AiDiy TOOL HUB のまとめ：14 MCP・3 トランスポートの概要振り返りと、AiDiy 利用への誘導",
      "factual_bullets": [
        "14 の MCP サーバーがポート 8095 に集約",
        "SSE / Streamable HTTP / stdio の 3 トランスポートを同一ポートで提供",
        "Web・Python・AI エージェントどこからでも統一的に利用可能",
        "tools_main.py の起動だけでツール群がすぐ使える状態になる",
        "AiDiy は日本語ファーストの業務システム開発テンプレート + AI 自動化基盤"
      ],
      "forbidden_elements": [
        "AiDiy が商用製品として公式リリースされているかのような断言",
        "チャンネル登録数や視聴数への言及"
      ],
      "image_prompt": "A triumphant hero visualization of AiDiy TOOL HUB: a central glowing blue hub with 14 tool icons orbiting it connected by light streams. Two avatar silhouettes (female right, male left) standing beside the hub. Text area for AiDiy TOOL HUB title. Inspiring futuristic aesthetic with blue and gold color scheme.",
      "dialogue": [
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "AiDiy TOOL HUB は 14 の MCP を 1 か所に集めたツール基盤です。",
          "naration_text": "今回紹介した AiDiy TOOL HUB は、ブラウザ操作、画面キャプチャ、SQLite と PostgreSQL のデータ管理、ログ確認、コードチェック、バックアップ、画像・動画・音声の AI 生成、OBS 録画制御、FFmpeg 動画処理、コードエージェントという 14 の MCP サーバーを、ポート 8095 のひとつに集約したツール基盤です。SSE・Streamable HTTP・stdio の 3 トランスポートにより、あらゆる環境から利用できます。",
          "audio": "audio/dlg_999_01_male.mp3",
          "duration_sec": 26.304
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Web、Python、AI エージェントから同じ方法でツールを呼び出せます。",
          "naration_text": "この仕組みの一番の魅力は、Web フロントエンド、Python スクリプト、AI エージェントのどこからでも、同じ API インターフェースでツールを呼び出せることです。MCP クライアントがなくても、シンプルな HTTP POST だけで利用を始められるので、導入の敷居がとても低くなっています。自動化したいアイデアさえあれば、すぐに試せる環境が整っています。",
          "audio": "audio/dlg_999_02_female.mp3",
          "duration_sec": 23.856
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "tools_main.py を起動するだけで、14 のツールがすぐ使えます。",
          "naration_text": "backend_tools の tools_main.py を uvicorn で起動するだけで、14 のツール群がすぐ使える状態になります。Claude Desktop や Copilot CLI の MCP 設定に追加すれば、AI エージェントがそのままブラウザを操作したり、画像を生成したり、コードを書いたりできるようになります。最初の一歩はとても簡単です。",
          "audio": "audio/dlg_999_03_male.mp3",
          "duration_sec": 20.16
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AiDiy TOOL HUB を実際に動かして、自動化の可能性を体験してみてください！",
          "naration_text": "この動画は AiDiy の video_generation 機能で自動生成しました。AiDiy は、業務システム開発テンプレートと AI 自動化ツールを組み合わせた、日本語ファーストの開発環境です。AiDiy TOOL HUB を実際に動かしてみると、自動化の可能性がどんどん広がっていくのを感じられます。皆さんもぜひ試してみてください。きっと、開発がもっと楽しくなりますよ！",
          "audio": "audio/dlg_999_04_female.mp3",
          "duration_sec": 24.6
        }
      ],
      "duration_sec": 94.92
    }
  ],
  "total_duration_sec": 848.904
};
