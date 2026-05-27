window.SCENARIO = {
  "project_name": "解説_AiDiy_mcp改",
  "version": "duo-v2",
  "title": "AiDiy MCP ハブ解説 — FastAPI + HTTP Transport で広がる 14 MCP の応用範囲",
  "assets_policy": {
    "male_avatar": "../vrm/VRM_male.vrm",
    "female_avatar": "../vrm/VRM_female.vrm",
    "tts_male": "edge:male",
    "tts_female": "edge:female",
    "audio_output_dir": "frontend_web/public/Xビデオ/解説_AiDiy_mcp改/audio"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "イントロ — AiDiy MCP ハブの全体像",
      "accent": "#1a6ea0",
      "accent_soft": "rgba(26, 110, 160, 0.18)",
      "layout": "hero",
      "kicker": "AIDIY MCP HUB",
      "headline": "FastAPI + HTTP Transport で\n14 MCP の応用範囲が劇的に広がった",
      "image": "images/scene_000.png",
      "source_summary": "AiDiy MCPハブにFastAPI + Streamable HTTP Transportが追加。14のMCPサーバーをWebやPythonから直接呼び出せるようになった。この動画自体もAiDiyのvideo_generation機能で自動生成されている。",
      "factual_bullets": [
        "AiDiy MCPハブ: backend_mcp、ポート 8095",
        "14のMCPサーバーが同一ポートで提供",
        "3トランスポート: stdio gateway / SSE / Streamable HTTP Transport",
        "この動画はAiDiyのvideo_generation機能で自動生成"
      ],
      "forbidden_elements": [
        "誇張した未来予測",
        "AiDiyが商用完成品であるかのような表現"
      ],
      "image_prompt": "Dark-theme software architecture dashboard. Central hub labeled 'AiDiy MCP HUB port:8095' connected to exactly 14 modules arranged in a circle, each labeled with its real name: aidiy_chrome_devtools, aidiy_desktop_capture, aidiy_sqlite, aidiy_postgres, aidiy_logs, aidiy_code_check, aidiy_backup, aidiy_image_generation, aidiy_movie_generation, aidiy_speech_to_text, aidiy_text_to_speech, aidiy_obs_studio_control, aidiy_ffmpeg_control, aidiy_code_agents. Glowing blue and teal connection lines. Japanese tech product announcement style, wide 16:9. No generic placeholder names.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AiDiy MCPハブが大幅アップデート。この動画もAiDiy video_generation機能で自動生成しました。",
          "naration_text": "はじめに、今回の動画についてお伝えします。この動画は、AiDiy の video_generation 機能によって自動生成されました。シナリオの作成から、シーンごとの画像、そして今お聞きのナレーション音声まで、すべてを AiDiy が自動で生成しています。今回は、AiDiy の MCP ハブに FastAPI と Streamable HTTP Transport が追加されたことで、Web アプリや Python スクリプトから AI エージェントを直接実行できるようになり、開発の応用範囲がどれほど広がったかをご紹介します。",
          "audio": "audio/dlg_000_01_female.mp3",
          "duration_sec": 33.288
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "ブラウザ操作から AI 生成まで、14 の MCP サーバーが 1 つのポートに集約されています。",
          "naration_text": "AiDiy の MCP ハブには、現在 14 種類の MCP サーバーが同居しています。Chrome 操作、デスクトップキャプチャ、SQLite・PostgreSQL DB 確認、ログ解析、コードチェック、バックアップ、画像・動画・音声生成、OBS 制御、ffmpeg 処理、コードエージェント実行と、開発と自動化に必要な機能がひとまとめになっています。これらすべてが、ポート 8095 番の単一エンドポイントから利用できます。",
          "audio": "audio/dlg_000_02_male.mp3",
          "duration_sec": 26.112
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "新しく追加された HTTP Transport で、Python や Web から MCP を直接呼び出せます。",
          "naration_text": "今回の最大のポイントは、Streamable HTTP Transport のサポートです。これまでの MCP は stdio や SSE での接続が中心でしたが、HTTP Transport が加わったことで、Python の requests ライブラリや JavaScript の fetch API を使って MCP を直接呼び出せるようになりました。コードエージェントを介さなくても、スクリプトや Web アプリから MCP の機能を自由に使えます。",
          "audio": "audio/dlg_000_03_female.mp3",
          "duration_sec": 26.904
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "ツール一覧は GET、実行は POST で、シンプルな REST API として扱えます。",
          "naration_text": "使い方はとてもシンプルです。GET リクエストで「http://localhost:8095/aidiy_image_generation/list」のようにツール一覧を確認し、POST リクエストで機能を実行します。REST API と同じ感覚で使えるので、既存のコードへの組み込みもスムーズです。Python の requests はもちろん、curl でも呼び出せます。",
          "audio": "audio/dlg_000_04_male.mp3",
          "duration_sec": 22.008
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "今日はブラウザ操作・データ管理・AI生成・運用の 4 カテゴリーで 14 MCP を紹介します。",
          "naration_text": "今日は 14 の MCP サーバーを、ブラウザ・画面操作系、データ・開発補助系、AI 生成系、運用・自動化系の 4 つのカテゴリーに分けてご紹介します。それぞれがどんな場面で役立つのか、具体的に見ていきましょう。",
          "audio": "audio/dlg_000_05_female.mp3",
          "duration_sec": 16.152
        }
      ],
      "duration_sec": 124.464
    },
    {
      "id": "scene_001",
      "title": "MCP ハブの仕組み — 3 種のトランスポート",
      "accent": "#2e86ab",
      "accent_soft": "rgba(46, 134, 171, 0.18)",
      "kicker": "MCP TRANSPORT",
      "headline": "stdio / SSE / HTTP Transport\n3 種類のトランスポートを同一ポートで提供",
      "image": "images/scene_001.png",
      "source_summary": "AiDiy MCPハブはstdio gateway・SSE Transport・Streamable HTTP Transportの3種を同一ポート8095で提供。FastAPI上で実装。mcp_main.pyがエントリポイント。",
      "factual_bullets": [
        "backend_mcp/mcp_main.py がエントリポイント",
        "ポート: 8095",
        "stdio gateway (mcp_stdio.py): Claude Desktopなどのstdio MCPクライアント向け",
        "SSE Transport: Server-Sent Events によるリアルタイム接続",
        "Streamable HTTP Transport: REST API 形式でPython/fetchから直接利用可能"
      ],
      "forbidden_elements": [
        "stdioとSSEとHTTPが別々のポートで動いているような誤解を招く表現"
      ],
      "image_prompt": "Technical architecture diagram showing three transport layers (stdio, SSE, HTTP) converging into a single FastAPI server node at port 8095. Clean network topology visualization with blue and green data flow lines on dark background. Shows mcp_main.py as central hub.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AiDiy の MCP ハブは FastAPI で実装され、ポート 8095 で動作しています。",
          "naration_text": "AiDiy の MCP ハブは、Python の FastAPI フレームワークを使って実装されています。backend_mcp フォルダにある mcp_main.py がエントリポイントで、ポート 8095 で起動します。ここに 14 種類の MCP サーバーがすべて集約されており、接続方式に応じた 3 種類のトランスポートが利用できます。",
          "audio": "audio/dlg_001_01_female.mp3",
          "duration_sec": 21.936
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "stdio gateway は Claude Desktop などの MCP クライアントと接続する際に使います。",
          "naration_text": "1 つ目のトランスポートは stdio gateway です。mcp_stdio.py を経由することで、Claude Desktop や VS Code など、stdio 接続を前提とした MCP クライアントから AiDiy のすべての MCP を利用できます。既存のクライアント設定をそのまま活かせる点が便利で、Claude への MCP 接続設定もこの方式で行います。",
          "audio": "audio/dlg_001_02_male.mp3",
          "duration_sec": 20.4
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "SSE Transport は Server-Sent Events によるリアルタイム接続を実現します。",
          "naration_text": "2 つ目は SSE Transport です。Server-Sent Events を使ったリアルタイム接続で、ブラウザや対応クライアントからの持続的な接続に向いています。イベントの流れをストリームとして受け取れるため、長時間かかる処理の進捗をリアルタイムに確認するような用途にも適しています。",
          "audio": "audio/dlg_001_03_female.mp3",
          "duration_sec": 18.96
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Streamable HTTP Transport が今回の目玉。Python の requests で直接 POST できます。",
          "naration_text": "3 つ目が今回の目玉、Streamable HTTP Transport です。REST API と同じ感覚で POST リクエストを送るだけで MCP の機能を呼び出せます。Python の requests ライブラリや fetch API など、HTTP を使えるあらゆる環境から利用できるため、スクリプト自動化や Web アプリとの連携が大幅に簡単になりました。これが今回のアップデートで最も大きな変化です。",
          "audio": "audio/dlg_001_04_male.mp3",
          "duration_sec": 23.736
        }
      ],
      "duration_sec": 85.032
    },
    {
      "id": "scene_002",
      "title": "HTTP Transport 追加の意義 — Web・Python から直接実行",
      "accent": "#e84855",
      "accent_soft": "rgba(232, 72, 85, 0.18)",
      "kicker": "HTTP TRANSPORT",
      "headline": "HTTP Transport で\nWeb・Python から MCP を直接実行",
      "image": "images/scene_002.png",
      "source_summary": "Streamable HTTP TransportによりPython requestsやfetch APIからMCPを直接呼び出せる。AIコードエージェント不要で自動化スクリプトやWebアプリから活用可能。バックエンドサーバーからの呼び出しも可能。",
      "factual_bullets": [
        "POST http://localhost:8095/{mcp_name}/{method} で実行",
        "GET http://localhost:8095/{mcp_name}/list でツール一覧確認",
        "Python requests.post() で直接呼び出し可能",
        "バックエンドサーバー（FastAPI）からMCPを呼び出し可能",
        "コードエージェントを介さず直接利用できる"
      ],
      "forbidden_elements": [
        "HTTPTransportが唯一の使い方であるかのような表現",
        "stdio/SSEが非推奨になったような表現"
      ],
      "image_prompt": "Python code snippet and web browser side by side, both sending POST requests to an AiDiy MCP server at localhost:8095. Arrows showing direct HTTP connections without middleware layer. Clean tech illustration on dark background with red accent color.",
      "dialogue": [
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "HTTP Transport 以前は AI コードエージェント経由が必要でした。",
          "naration_text": "HTTP Transport が追加される前は、MCP の機能を使うには基本的に AI コードエージェントを介す必要がありました。それが今では、Python スクリプトから requests.post() を呼ぶだけで、画像生成や音声合成、DB 確認といった機能を直接実行できます。定型作業の自動化がぐっと手軽になりました。",
          "audio": "audio/dlg_002_01_male.mp3",
          "duration_sec": 20.16
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Python から一行の POST で MCP を呼び出せます。定型作業の自動化に最適です。",
          "naration_text": "Python からの使い方は非常にシンプルです。たとえば requests.post(\"http://localhost:8095/aidiy_text_to_speech/synthesize\", json={\"speech_text\": \"こんにちは\"}) のように書くだけで音声を生成できます。バッチ処理や定時実行スクリプトにそのまま組み込めるので、繰り返し作業の自動化に特に便利です。",
          "audio": "audio/dlg_002_02_female.mp3",
          "duration_sec": 25.944
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Web アプリの fetch から呼べるため、フロントエンドへの AI 機能組み込みも現実的になりました。",
          "naration_text": "Web アプリケーションからも、JavaScript の fetch API を使って MCP を直接呼び出せます。フロントエンドから画像生成 API を呼んで結果を表示する、といった実装がプロキシなしで実現できます。AiDiy の frontend_web からは Vite プロキシを経由して安全に呼び出す構成も可能です。",
          "audio": "audio/dlg_002_03_male.mp3",
          "duration_sec": 18.168
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "バックエンドサーバーから MCP を呼ぶことで、業務 API に AI 機能を直接組み込めます。",
          "naration_text": "さらに、AiDiy のバックエンドサーバー（FastAPI）から MCP を呼び出すことで、通常の業務 API エンドポイントに AI 機能を組み込めます。たとえば、レポート生成エンドポイントの中から MCP の画像生成や TTS を呼ぶといった連携が、コードエージェントなしで実現できます。応用範囲が劇的に広がった理由がここにあります。",
          "audio": "audio/dlg_002_04_female.mp3",
          "duration_sec": 23.256
        }
      ],
      "duration_sec": 87.528
    },
    {
      "id": "scene_003",
      "title": "ブラウザ操作・画面操作 MCP",
      "accent": "#f7931e",
      "accent_soft": "rgba(247, 147, 30, 0.18)",
      "kicker": "BROWSER & SCREEN",
      "headline": "Chrome 操作とデスクトップ操作を\n自動化する 2 つの MCP",
      "image": "images/scene_003.png",
      "source_summary": "aidiy_chrome_devtoolsはChrome DevTools Protocol経由でブラウザを自動操作。aidiy_desktop_captureはOSレベルのスクリーンショットとマウス座標取得。E2Eテストや画面確認自動化に活用。",
      "factual_bullets": [
        "aidiy_chrome_devtools: CDP経由でクリック・入力・スクリーンショット・JS実行・ネットワークキャプチャ",
        "aidiy_desktop_capture: OSレベルスクリーンショット、マルチモニター対応、ウィンドウキャプチャ",
        "E2Eテスト自動化、画面確認、UIデバッグに活用",
        "AiDiyのビデオ生成ワークフローでも中間確認に使用"
      ],
      "forbidden_elements": [
        "不正なスクレイピングや不正アクセスへの応用を示唆する表現"
      ],
      "image_prompt": "Split screen showing Chrome browser with visible automation controls on the left, and desktop screenshot capture interface with monitor grid on the right. Blue and orange tech theme on dark background. Shows CDP connection indicators.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_chrome_devtools は Chrome を CDP 経由で完全に制御できる MCP です。",
          "naration_text": "ブラウザ操作系の 1 つ目は aidiy_chrome_devtools です。Chrome DevTools Protocol を使って、クリック、テキスト入力、スクリーンショット撮影、JavaScript 実行、ネットワークログの取得など、ブラウザに対するほぼすべての操作をプログラムから実行できます。E2E テストの自動化や、開発中の画面確認を自動化するのに活躍します。",
          "audio": "audio/dlg_003_01_female.mp3",
          "duration_sec": 23.736
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "aidiy_desktop_capture は OS レベルのスクリーンショットとウィンドウ情報を取得できます。",
          "naration_text": "2 つ目の aidiy_desktop_capture は、OS レベルでのスクリーンショット取得に特化した MCP です。マルチモニター環境に対応しており、全画面、指定モニター、特定のウィンドウ、カーソル周辺の切り出しなど、さまざまな撮影モードをサポートします。マウスカーソルの座標取得や、表示中のウィンドウ一覧取得もできます。",
          "audio": "audio/dlg_003_02_male.mp3",
          "duration_sec": 20.088
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "このビデオ生成ワークフローの完成確認工程でも、Chrome MCP を実際に使っています。",
          "naration_text": "実際に AiDiy のビデオ生成ワークフローでも、中間確認や完成確認の工程で aidiy_chrome_devtools が活用されています。ブラウザで動画プレイヤーを開き、画像の表示やアバターの動き、字幕のレイアウトを自動でスクリーンショットに収めて確認する、という使い方です。",
          "audio": "audio/dlg_003_03_female.mp3",
          "duration_sec": 18.528
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "2 つを組み合わせると、ブラウザ内側と外側の両方をカバーする自動化環境が整います。",
          "naration_text": "aidiy_chrome_devtools と aidiy_desktop_capture を組み合わせることで、ブラウザの内側で起きていること（DOM、ネットワーク、コンソール）と、外側から見えた画面全体の両方を同時にキャプチャできます。AI エージェントがブラウザを操作しながら自分で結果を目視確認する、という高度な自動化が実現します。",
          "audio": "audio/dlg_003_04_male.mp3",
          "duration_sec": 18.816
        }
      ],
      "duration_sec": 81.168
    },
    {
      "id": "scene_004",
      "title": "データ管理・開発補助 MCP — 5 つのツール",
      "accent": "#44bba4",
      "accent_soft": "rgba(68, 187, 164, 0.18)",
      "kicker": "DATA & DEV TOOLS",
      "headline": "DB 確認からコードチェック、バックアップまで\n5 つの開発補助 MCP",
      "image": "images/scene_004.png",
      "source_summary": "5つのMCP: aidiy_sqlite（AiDiy DB確認）、aidiy_postgres（外部PostgreSQL）、aidiy_logs（エラー抽出）、aidiy_code_check（Python/TypeScript検査）、aidiy_backup（差分バックアップ）",
      "factual_bullets": [
        "aidiy_sqlite: AiDiy DBのテーブル確認・クエリ実行（読み取りデフォルト、書き込みはallow_write=True）",
        "aidiy_postgres: 外部PostgreSQL接続・任意SQLクエリ実行",
        "aidiy_logs: backend_server / backend_mcp のログ末尾取得・ERROR/Traceback抽出",
        "aidiy_code_check: Python構文・ruff lint・TypeScript型チェック（npm run type-check）",
        "aidiy_backup: 差分バックアップ保存（初回は全件スナップショット）・変更ファイル検出・before/after比較"
      ],
      "forbidden_elements": [
        "本番DBへの破壊的操作を推奨する表現",
        "セキュリティを無視した使い方"
      ],
      "image_prompt": "Developer dashboard showing four panels: SQLite database tables, log viewer with highlighted error messages, TypeScript type-check output, and file diff comparison. Clean professional dark UI with teal green accent colors.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_sqlite と aidiy_postgres で、AiDiy DB と外部 PostgreSQL を確認できます。",
          "naration_text": "データ管理系の MCP を見ていきます。aidiy_sqlite は、AiDiy の業務データベースに対してテーブル一覧の確認、スキーマ確認、任意の SQL クエリ実行ができる MCP です。デフォルトは読み取り専用で安全に使えます。aidiy_postgres は外部の PostgreSQL に接続して同様の操作ができ、AI エージェントが実行結果を確認しながら作業を進める際に欠かせないツールです。",
          "audio": "audio/dlg_004_01_female.mp3",
          "duration_sec": 27.048
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "aidiy_logs はサーバーのログから ERROR と Traceback をピンポイントで抽出します。",
          "naration_text": "aidiy_logs は、backend_server と backend_mcp のログファイルを監視して、末尾の取得やエラー抽出ができる MCP です。ERROR や Traceback を前後の文脈付きで取り出してくれるので、AI エージェントがバグの原因を特定するときに素早く動けます。コードを書いて動かしてエラーを確認して直す、というサイクルがスムーズになります。",
          "audio": "audio/dlg_004_02_male.mp3",
          "duration_sec": 20.544
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_code_check は Python と TypeScript の構文・lint・型チェックを MCP 経由で実行します。",
          "naration_text": "aidiy_code_check は、Python ファイルの構文チェックと ruff による lint、TypeScript プロジェクトの型チェックを MCP 経由で実行できるツールです。AI エージェントがコードを書いた後に自分でチェックを走らせてエラーを確認し、修正するという流れを、追加のツール設定なしで完結できます。",
          "audio": "audio/dlg_004_03_female.mp3",
          "duration_sec": 19.176
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "aidiy_backup は差分バックアップを管理し、変更ファイルの検出や before/after 比較ができます。",
          "naration_text": "aidiy_backup は AiDiy プロジェクト専用の差分バックアップ MCP です。初回実行で全件スナップショットを保存し、以降は変更があったファイルだけを差分で記録します。変更ファイルの一覧取得、特定ファイルの変更前後の内容比較、バージョン履歴の確認ができ、AI が作業した後の確認や取り消しに使えます。",
          "audio": "audio/dlg_004_04_male.mp3",
          "duration_sec": 20.28
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "これら 5 つが揃うと、AI エージェントが自律的に開発・確認・修正サイクルを回せます。",
          "naration_text": "DB 確認、ログ解析、コードチェック、バックアップという 5 つのツールが揃うと、AI エージェントが自律的に「コードを書く → 動かす → エラーを確認する → 修正する → バックアップを取る」というサイクルを回せるようになります。人間が毎回指示しなくても、エージェントが自分で判断して動ける環境が整います。",
          "audio": "audio/dlg_004_05_female.mp3",
          "duration_sec": 19.944
        }
      ],
      "duration_sec": 106.992
    },
    {
      "id": "scene_005",
      "title": "AI 生成系 MCP — 画像・動画・音声を自在に",
      "accent": "#9b59b6",
      "accent_soft": "rgba(155, 89, 182, 0.18)",
      "kicker": "AI GENERATION",
      "headline": "画像・動画・音声・テキスト読み上げ\n4 つの AI 生成 MCP",
      "image": "images/scene_005.png",
      "source_summary": "4つのAI生成MCP: aidiy_image_generation（OpenAI/Gemini/FreeAI）、aidiy_movie_generation（Google Gemini Veo、4〜8秒）、aidiy_speech_to_text（speech_recognition/Whisper）、aidiy_text_to_speech（Edge/OpenAI/Gemini/FreeAI）。このビデオ自体が生成例。",
      "factual_bullets": [
        "aidiy_image_generation: OpenAI gpt-image-2・Gemini・FreeAI対応",
        "aidiy_movie_generation: Google Gemini Veo（4〜8秒、720p/1080p、image-to-video対応）",
        "aidiy_speech_to_text: speech_recognitionまたはOpenAI Whisper",
        "aidiy_text_to_speech: Edge TTS・OpenAI・Gemini・FreeAI、発音辞書内蔵、ratio 1.2倍速",
        "このビデオの音声はaidiy_text_to_speech（edge:female/male）で生成"
      ],
      "forbidden_elements": [
        "特定プロバイダーを著しく劣ると断定する表現",
        "生成AIが完璧であるかのような断定"
      ],
      "image_prompt": "Four AI generation capabilities as quadrant panels: top-left colorful image generation artwork, top-right video generation with film frames, bottom-left speech recognition waveform visualization, bottom-right text-to-speech soundwave output. Purple gradient theme on dark background.",
      "dialogue": [
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "aidiy_image_generation は OpenAI・Gemini・FreeAI に対応したマルチプロバイダー画像生成 MCP です。",
          "naration_text": "AI 生成系の最初は aidiy_image_generation です。OpenAI の gpt-image-2、Gemini、FreeAI といった複数のプロバイダーに対応しており、用途やコストに応じてプロバイダーを切り替えられます。プロンプトと保存先パスを指定するだけで画像ファイルが生成されます。このビデオのシーン画像も、この MCP を使って実際に生成しています。",
          "audio": "audio/dlg_005_01_male.mp3",
          "duration_sec": 21.888
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_movie_generation は Google Gemini Veo で 4〜8 秒の動画クリップを自動生成します。",
          "naration_text": "aidiy_movie_generation は Google Gemini Veo を使った動画生成 MCP です。テキストのプロンプトから 4 秒から 8 秒の動画クリップを生成でき、720p と 1080p の解像度、横向きと縦向きのアスペクト比を選べます。参照画像を渡してそこから動き出す image-to-video の機能もあります。生成には数分かかることがありますが、それだけの品質が期待できます。",
          "audio": "audio/dlg_005_02_female.mp3",
          "duration_sec": 26.112
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "aidiy_speech_to_text は音声ファイルをテキストに変換。OpenAI Whisper にも対応しています。",
          "naration_text": "aidiy_speech_to_text は、音声ファイルをテキストに変換する音声認識 MCP です。標準の speech_recognition エンジンに加えて、OpenAI の Whisper も利用できます。WAV ファイルのパスか base64 データを渡すとテキストが返ってきます。会議録の自動文字起こしや、音声入力の処理に活用できます。",
          "audio": "audio/dlg_005_03_male.mp3",
          "duration_sec": 20.04
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_text_to_speech は Edge・OpenAI・Gemini・FreeAI に対応した TTS MCP です。",
          "naration_text": "aidiy_text_to_speech は、テキストから音声を合成する TTS MCP です。Edge TTS、OpenAI、Gemini、FreeAI の 4 つのプロバイダーに対応しています。AiDiy のシステム用語を読み上げやすい形に変換する発音辞書も内蔵されています。実は、今お聞きのこのナレーション音声も、aidiy_text_to_speech の Edge TTS を使って生成されています。",
          "audio": "audio/dlg_005_04_female.mp3",
          "duration_sec": 26.04
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "4 つの AI 生成 MCP を組み合わせると、シナリオから完成した動画素材を自動で作れます。",
          "naration_text": "この 4 つの AI 生成 MCP を組み合わせると、テキストのシナリオから画像を生成し、音声を合成し、動画クリップまで自動で作れます。実際にこのビデオ自体が、そのワークフローの実践例です。シナリオを書いて、画像と音声を MCP で生成し、プレイヤーに組み込むという流れをすべて自動化しています。",
          "audio": "audio/dlg_005_05_male.mp3",
          "duration_sec": 20.112
        }
      ],
      "duration_sec": 114.192
    },
    {
      "id": "scene_006",
      "title": "運用・自動化系 MCP — OBS・FFmpeg・Code Agents",
      "accent": "#c0392b",
      "accent_soft": "rgba(192, 57, 43, 0.18)",
      "kicker": "OPS & AGENTS",
      "headline": "OBS・FFmpeg・コードエージェントで\n開発から配信まで自動化する",
      "image": "images/scene_006.png",
      "source_summary": "aidiy_obs_studio_control（OBS WebSocket制御）、aidiy_ffmpeg_control（ffmpeg/ffprobe/ffplay）、aidiy_code_agents（AI CLIエージェント実行：copilot_cli/codex_cli/opencode_cli/antigravity_cli/aidiy_hermes）",
      "factual_bullets": [
        "aidiy_obs_studio_control: OBS WebSocket v5でシーン切替・録画開始停止・音声ミュート・配信制御",
        "aidiy_ffmpeg_control: ffmpeg変換・ffprobe解析・ffplay再生・音声区間検出・自動トリミング",
        "aidiy_code_agents: copilot_cli・codex_cli・opencode_cli・antigravity_cli・aidiy_hermesを実行可能",
        "video_generationワークフローでOBS録画とffmpegトリミングを使用"
      ],
      "forbidden_elements": [
        "OBSが常に起動している前提の表現",
        "著作権不明なコードの自動生成を推奨する表現"
      ],
      "image_prompt": "Three panels: left shows OBS Studio interface with recording controls highlighted, center shows FFmpeg command processing with video file icons, right shows AI code agent terminal with streaming colored output. Red accent professional dark tech theme.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_obs_studio_control は OBS を WebSocket で制御し、録画やシーン切替を自動化します。",
          "naration_text": "運用自動化系の最初は aidiy_obs_studio_control です。OBS Studio の WebSocket v5 API を通じて、シーンの切替、録画の開始・停止、音声入力のミュート制御、配信の操作などを外部から自動実行できます。AiDiy のビデオ生成ワークフローでは、この MCP を使って画面録画を自動化しています。",
          "audio": "audio/dlg_006_01_female.mp3",
          "duration_sec": 22.896
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "aidiy_ffmpeg_control は動画変換から音声区間検出、自動トリミングまでこなす MCP です。",
          "naration_text": "aidiy_ffmpeg_control は ffmpeg、ffprobe、ffplay の 3 つのツールを MCP 経由で実行できる動画処理 MCP です。動画フォーマットの変換、音声の区間検出、前後余白付きの自動トリミング、字幕の焼き込み、解像度変更など、動画編集の定番作業をコードから呼び出せます。OBS で録画した映像を自動でトリミングする用途で実際に使っています。",
          "audio": "audio/dlg_006_02_male.mp3",
          "duration_sec": 23.112
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "aidiy_code_agents は複数の AI コード CLI をまとめて実行できる MCP です。",
          "naration_text": "aidiy_code_agents は、GitHub Copilot CLI、Codex CLI、OpenCode CLI、Antigravity CLI、AiDiy Hermes などの AI コードエージェントを MCP から実行できるツールです。使用する AI やモデル、権限設定、最大ターン数などを指定して呼び出せます。複数の AI エージェントを組み合わせた処理フローを組める点が大きな特徴です。",
          "audio": "audio/dlg_006_03_female.mp3",
          "duration_sec": 24.984
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "3 つを連携させると、コード生成から動画配信まで一気通貫で自動化できます。",
          "naration_text": "OBS で録画して、ffmpeg でトリミングし、コードエージェントで後処理する、という流れをすべて MCP で自動化できます。さらに HTTP Transport の登場で、これらの操作を Python スクリプトや Web アプリから直接呼び出せるようになりました。開発から配信まで、人手を減らしながら品質を保てる仕組みが整ってきています。",
          "audio": "audio/dlg_006_04_male.mp3",
          "duration_sec": 20.28
        }
      ],
      "duration_sec": 91.272
    },
    {
      "id": "scene_999",
      "title": "まとめ — AiDiy MCP ハブの可能性",
      "accent": "#1a6ea0",
      "accent_soft": "rgba(26, 110, 160, 0.18)",
      "layout": "hero",
      "kicker": "AIDIY MCP HUB",
      "headline": "AiDiy MCP ハブで\n開発と自動化の可能性を広げよう",
      "image": "images/scene_999.png",
      "source_summary": "AiDiy MCPハブのまとめ。14のMCPサーバーとHTTP Transportで応用範囲が拡大。AiDiyは日本語ファーストのフルスタック業務システム開発テンプレート。チャンネル登録と試用を促す。",
      "factual_bullets": [
        "14のMCPサーバーがポート8095で提供",
        "3トランスポート（stdio/SSE/HTTP）で多様な環境から利用可能",
        "HTTP TransportでPython/WebからのAgent実行に対応",
        "AiDiy = 日本語ファーストのフルスタック業務システム開発テンプレート（FastAPI + Vue 3）"
      ],
      "forbidden_elements": [
        "AiDiyが完成された商用製品であるかのような過大表現"
      ],
      "image_prompt": "Celebratory dark-theme infographic. 'AiDiy MCP HUB' logo at the center, surrounded by a circular ring of exactly 14 glow-effect modules each labeled with its real name: aidiy_chrome_devtools, aidiy_desktop_capture, aidiy_sqlite, aidiy_postgres, aidiy_logs, aidiy_code_check, aidiy_backup, aidiy_image_generation, aidiy_movie_generation, aidiy_speech_to_text, aidiy_text_to_speech, aidiy_obs_studio_control, aidiy_ffmpeg_control, aidiy_code_agents. Blue and gold color scheme, radiating glow. Warm inviting Japanese tech finishing visual, wide 16:9. No placeholder or generic names.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "今回は 14 の MCP サーバーと HTTP Transport 追加の意義をご紹介しました。",
          "naration_text": "今回は AiDiy の MCP ハブに含まれる 14 個の MCP サーバーと、FastAPI と HTTP Transport を組み合わせたインターフェースが追加されたことの意義をご紹介しました。ブラウザ操作、データ管理、AI 生成、運用自動化と、開発に必要な機能がひとまとめになっているのが AiDiy MCP ハブの最大の強みです。",
          "audio": "audio/dlg_999_01_female.mp3",
          "duration_sec": 22.296
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "HTTP Transport で Python や Web からの直接呼び出しが可能になり、応用範囲が劇的に広がりました。",
          "naration_text": "特に HTTP Transport の追加は大きなターニングポイントです。これまでコードエージェントを介す必要があった MCP の機能が、Python の requests 一行や fetch API から直接呼び出せるようになりました。自動化スクリプト、Web アプリ、バックエンド API との連携が一気に現実的になったと感じています。",
          "audio": "audio/dlg_999_02_male.mp3",
          "duration_sec": 18.888
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AiDiy は日本語ファーストの業務システム開発テンプレートに AI を統合した開発環境です。",
          "naration_text": "AiDiy は、FastAPI と Vue 3 をベースにした日本語ファーストの業務システム開発テンプレートです。マスタ管理、トランザクション処理、スケジューラといった実用的な業務機能に加え、AI エージェント、MCP、画像・音声・動画生成ツールを統合した開発実験基盤でもあります。今回ご紹介した MCP ハブはその中核的な存在です。",
          "audio": "audio/dlg_999_03_female.mp3",
          "duration_sec": 24.912
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "AiDiy の活用事例はこれからも続々と紹介していきます。次の動画もぜひご覧ください。",
          "naration_text": "AiDiy を使ったビデオ生成ワークフロー、業務システムの自動化、AI エージェントとの連携事例など、これからも実際に動くものを作りながら紹介していく予定です。今回のような MCP ハブの活用例は、まだまだアイデアが尽きません。次の動画もどうぞお楽しみに。",
          "audio": "audio/dlg_999_04_male.mp3",
          "duration_sec": 16.752
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "この動画は AiDiy で自動生成！チャンネル登録して、あなたも AiDiy を試してみてください。",
          "naration_text": "最後までご視聴いただきありがとうございました。この動画は、AiDiy の video_generation 機能を使って自動生成されました。シナリオから画像、音声、プレイヤーまですべてが自動です。気に入っていただけたら、ぜひチャンネル登録をお願いします。AiDiy は誰でも試せるオープンな開発環境です。ぜひあなた自身で動かして、自動化の楽しさをぜひ体験してみてください！",
          "audio": "audio/dlg_999_05_female.mp3",
          "duration_sec": 26.136
        }
      ],
      "duration_sec": 108.984
    }
  ],
  "total_duration_sec": 799.632
};
