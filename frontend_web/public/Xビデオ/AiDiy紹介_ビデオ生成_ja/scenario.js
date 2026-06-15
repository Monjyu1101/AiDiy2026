window.SCENARIO = {
  "project_name": "AiDiy紹介_ビデオ生成_ja",
  "version": "mcp",
  "title": "AiDiy ビデオページ生成機能 - topic から HTML まで 9 ステップ全自動化",
  "source": {
    "type": "agents_and_knowledge",
    "summary": "AiDiy のビデオページ生成機能（ビデオページ生成_紹介.py / ビデオページ生成_解説.py）の仕組みと 9 ステップ全自動化の実態を紹介する。"
  },
  "target": {
    "language": "ja-JP",
    "format": "html_css_scene_player_with_media",
    "tone": "事実ベース、簡潔、根拠付き、親しみやすく前向き",
    "goal": "ビデオページ生成機能の全体像を、2 スクリプト・設定管理・9 ステップ・MCP と CodeAgents の役割まで正確かつ楽しく伝える。"
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
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "background_word": "",
      "kicker": "INTRODUCTION",
      "headline": "AiDiy ビデオページ生成機能を\n7つのシーンで紹介します",
      "lead": "topic を渡すだけで scenario.js 生成・画像生成・音声合成・HTML 組み立てまで 9 ステップを全自動化するビデオページ生成機能の全体像をお届けします。",
      "subtitle": "2 スクリプト・設定管理・MCP と CodeAgents の役割まで、仕組みごとわかりやすく解説します。",
      "image": "images/scene_000.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "image_prompt": "Square 1:1 hero poster for AiDiy Video Page Generation feature. Central bold text 'AiDiy Auto Video', futuristic film-reel and code-stream motif, glowing cyan and electric blue on dark background, premium tech branding aesthetic, no clutter, no dense paragraphs, clean composition.",
      "short_narration": "AiDiy のビデオページ生成機能は、topic を渡すだけで動画ページを 9 ステップで全自動生成します。",
      "long_narration": "この動画は、AiDiy のビデオページ生成機能で自動生成されました。シナリオ作成から画像生成、音声合成、HTML 組み立てまで、すべてを MCP と CodeAgents が担当しています。今回紹介するのは、AiDiy が持つビデオページ生成機能そのものです。テーマ（topic）を設定ファイルに書くだけで、scenario.js の生成から始まり、各シーンの画像生成、ナレーション音声の合成、HTML の組み立てまでを 9 ステップで全自動化します。ひとりアバター向けのスクリプトと、二人掛け合い向けのスクリプトの 2 種類があり、用途に合わせて使い分けられます。このビデオでは、機能の概要、設定ファイルと状況管理、各ステップの役割、そして MCP と CodeAgents がどう連携するかを順番に説明します。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 6.84,
      "long_start_sec": 0.0,
      "long_duration_sec": 50.064
    },
    {
      "id": "scene_001",
      "title": "ビデオページ生成機能の概要",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.18)",
      "kicker": "OVERVIEW",
      "headline": "2 スクリプトで\ntopic から HTML まで全自動",
      "lead": "ビデオページ生成_紹介.py（ひとりアバター）と ビデオページ生成_解説.py（二人掛け合い）の 2 本が、9 ステップを自動実行します。",
      "subtitle": "topic を与えるだけで、シナリオ・画像・音声・HTML が一括生成される。",
      "image": "images/scene_001.png",
      "image_prompt": "Vertical 2:3 poster showing two Python scripts side by side, one labeled narrator single avatar and one labeled dual discussion, both connected to a nine-step pipeline flowing down to a completed HTML video page, dark background, clean cyan accent, professional flow diagram, no mascots",
      "chips": [
        "ビデオページ生成_紹介.py",
        "ビデオページ生成_解説.py",
        "9 ステップ全自動",
        "topic → HTML"
      ],
      "metrics": [
        {
          "label": "スクリプト数",
          "value": "2"
        },
        {
          "label": "自動化ステップ",
          "value": "9"
        },
        {
          "label": "成果物",
          "value": "HTML動画ページ"
        }
      ],
      "cards": [
        {
          "title": "ビデオページ生成_紹介.py",
          "lines": [
            "ひとりアバター向け",
            "単独ナレーションスタイル",
            "シンプルな紹介動画に最適"
          ]
        },
        {
          "title": "ビデオページ生成_解説.py",
          "lines": [
            "二人掛け合い向け",
            "対話スタイルの解説動画",
            "技術説明や比較に最適"
          ]
        },
        {
          "title": "自動化の流れ",
          "lines": [
            "topic 設定 → scenario.js 生成",
            "画像生成 → 音声合成",
            "HTML 組み立て → 完成"
          ]
        },
        {
          "title": "実行方法",
          "lines": [
            "設定ファイルに topic を記述",
            "スクリプトを実行するだけ",
            "途中再開・特定ステップ再実行も可能"
          ]
        }
      ],
      "facts": [
        "ビデオページ生成_紹介.py はひとりアバター向け、ビデオページ生成_解説.py は二人掛け合い向け。",
        "topic から scenario.js 生成・画像生成・音声合成・HTML 組み立てまで 9 ステップを全自動化する。",
        "途中再開・特定ステップ再実行が可能な状況管理機能を持つ。"
      ],
      "evidence": [
        {
          "source": "共通,mcp利用による自動ビデオ生成手順.md",
          "text": "ビデオページ生成_紹介.py（ひとりアバター）と ビデオページ生成_解説.py（二人掛け合い）の 2 スクリプトで 9 ステップを全自動化する。"
        }
      ],
      "short_narration": "2 本のスクリプトが、topic から HTML ビデオページまでを 9 ステップで全自動生成します。",
      "long_narration": "AiDiy のビデオページ生成機能は、2 本の Python スクリプトで構成されています。ビデオページ生成_紹介.py はひとりのアバターがナレーションするスタイル、ビデオページ生成_解説.py は二人が掛け合いで解説するスタイルです。どちらも topic を設定ファイルに書いてスクリプトを実行するだけで、scenario.js の生成から始まり、各シーンの画像生成、ナレーション音声の合成、そして HTML ビデオページの組み立てまでを自動で行います。全体は 9 ステップに分かれており、Step 00 の初期確認から Step 99 の完成案内まで順番に処理されます。途中で止まっても再開でき、特定のステップだけ再実行することも可能です。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 6.648,
      "long_start_sec": 0.0,
      "long_duration_sec": 43.848
    },
    {
      "id": "scene_002",
      "title": "設定ファイルと状況管理",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125, 255, 179, 0.18)",
      "kicker": "CONFIGURATION",
      "headline": "_設定.json と _状況.json で\n実行を柔軟にコントロール",
      "lead": "topic・folder_name・language・API URL などの設定は _設定.json で管理し、どのステップまで完了したかを _状況.json が記録します。",
      "subtitle": "設定ファイルで動作を制御し、状況ファイルで途中再開を実現。",
      "image": "images/scene_002.png",
      "image_prompt": "Vertical 2:3 configuration file diagram showing two JSON files, one labeled settings with fields topic folder_name language api_url, one labeled status with step number, connected by arrows to a pipeline of nine steps, dark green accent, enterprise blueprint style, clean technical illustration",
      "chips": [
        "_ビデオページ生成_*_設定.json",
        "_ビデオページ生成_*_状況.json",
        "topic / folder_name",
        "language / API URL",
        "途中再開対応"
      ],
      "metrics": [
        {
          "label": "設定ファイル",
          "value": "1本/スクリプト"
        },
        {
          "label": "状況ファイル",
          "value": "1本/スクリプト"
        },
        {
          "label": "途中再開",
          "value": "対応"
        }
      ],
      "cards": [
        {
          "title": "_設定.json の主な項目",
          "lines": [
            "topic: 動画のテーマ",
            "folder_name: 出力先フォルダ名",
            "language: 出力言語 (例: ja)"
          ]
        },
        {
          "title": "_設定.json の続き",
          "lines": [
            "template_dir: テンプレートフォルダ",
            "shared API URL: CodeAgents 等の接続先",
            "その他オプション設定"
          ]
        },
        {
          "title": "_状況.json の役割",
          "lines": [
            "現在の完了ステップ番号を記録",
            "途中再開時に次のステップから開始",
            "特定ステップだけ再実行も可能"
          ]
        },
        {
          "title": "実行フロー",
          "lines": [
            "_設定.json を編集して topic 設定",
            "スクリプトを実行",
            "_状況.json が進捗を自動追跡"
          ]
        }
      ],
      "facts": [
        "_ビデオページ生成_*_設定.json に topic / folder_name / template_dir / language / shared API URL 等を記述する。",
        "_ビデオページ生成_*_状況.json がステップ番号を記録し、途中再開・特定ステップ再実行を実現する。"
      ],
      "evidence": [
        {
          "source": "共通,mcp利用による自動ビデオ生成手順.md",
          "text": "設定は _ビデオページ生成_*_設定.json（topic / folder_name / template_dir / language / shared API URL 等）で管理。状況は _ビデオページ生成_*_状況.json でステップ番号を記録し、途中再開・特定ステップ再実行が可能。"
        }
      ],
      "short_narration": "_設定.json で topic などを指定し、_状況.json が進捗を管理して途中再開を可能にします。",
      "long_narration": "ビデオページ生成の動作は 2 種類の JSON ファイルで制御します。_ビデオページ生成_設定.json には topic、folder_name、template_dir、language、shared API URL などの基本設定を記述します。この設定ファイルを編集してスクリプトを実行するだけで、あとは自動的に処理が進みます。もうひとつの _ビデオページ生成_状況.json は実行の進捗を記録するファイルです。どのステップまで完了したかをステップ番号で管理しており、途中でエラーが起きても次回実行時に続きから再開できます。また、特定のステップだけを再実行したい場合にも活用できます。この 2 ファイルのシンプルな設計が、柔軟な実行制御を実現しています。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 7.368,
      "long_start_sec": 0.0,
      "long_duration_sec": 44.496
    },
    {
      "id": "scene_003",
      "title": "前半ステップ（Step 00〜03）",
      "expression": "neutral",
      "accent": "#ff6bd6",
      "accent_soft": "rgba(255, 107, 214, 0.18)",
      "kicker": "STEPS 00-03",
      "headline": "初期確認・フォルダ作成から\nシナリオと HTML を整える",
      "lead": "Step 00 で疎通確認、Step 01 でフォルダ準備、Step 02 で CodeAgents が scenario.js を生成、Step 03 で HTML の表示文言を更新します。",
      "subtitle": "前半 4 ステップで、動画の骨格となるシナリオと HTML が出来上がる。",
      "image": "images/scene_003.png",
      "image_prompt": "Vertical 2:3 pipeline diagram showing four steps labeled Step 00 initial check, Step 01 folder creation, Step 02 scenario generation, Step 03 HTML update, connected with arrows, dark magenta accent, clean enterprise flow chart, realistic software pipeline illustration",
      "chips": [
        "Step 00: 初期確認",
        "Step 01: フォルダ作成",
        "Step 02: シナリオ生成",
        "Step 03: HTML 更新"
      ],
      "metrics": [
        {
          "label": "前半ステップ数",
          "value": "4"
        },
        {
          "label": "scenario.js",
          "value": "Step 02"
        },
        {
          "label": "HTML 更新",
          "value": "Step 03"
        }
      ],
      "cards": [
        {
          "title": "Step 00: 初期確認",
          "lines": [
            "設定ファイルの存在確認",
            "テンプレート・API の疎通確認",
            "CodeAgents の接続確認"
          ]
        },
        {
          "title": "Step 01: フォルダ作成",
          "lines": [
            "テンプレートフォルダをコピー",
            "出力フォルダを新規作成",
            "audio / images サブフォルダも準備"
          ]
        },
        {
          "title": "Step 02: シナリオ生成",
          "lines": [
            "CodeAgents が scenario.js を生成",
            "scenes 配列・short/long narration 含む",
            "画像パス・音声パスも設定済み"
          ]
        },
        {
          "title": "Step 03: HTML 更新",
          "lines": [
            "CodeAgents が index.html を更新",
            "表示文言をテーマに合わせる",
            "タイトル・説明文を修正"
          ]
        }
      ],
      "facts": [
        "Step 00 は設定・テンプレート・API・CodeAgents の疎通を確認する。",
        "Step 02 で CodeAgents が scenario.js を生成する（scenes 配列・short/long narration・画像パス・音声パス）。",
        "Step 03 で CodeAgents が index.html の表示文言をテーマに合わせて更新する。"
      ],
      "evidence": [
        {
          "source": "共通,mcp利用による自動ビデオ生成手順.md",
          "text": "Step 00: 初期確認（設定・テンプレート・API・CodeAgents の疎通）。Step 01: テンプレートフォルダをコピーして出力フォルダを作成。Step 02: CodeAgents が scenario.js を生成（scenes 配列・short/long narration・画像パス・音声パス）。Step 03: CodeAgents が index.html の表示文言をテーマに合わせて更新。"
        }
      ],
      "short_narration": "Step 00〜03 で疎通確認・フォルダ準備・シナリオ生成・HTML 更新を順番に行います。",
      "long_narration": "ビデオページ生成の前半は 4 ステップです。Step 00 では設定ファイルの内容、テンプレートの存在、API への疎通、CodeAgents の接続をまとめて確認します。問題がなければ Step 01 に進み、テンプレートフォルダをコピーして出力フォルダと audio・images の各サブフォルダを準備します。Step 02 では CodeAgents が scenario.js を生成します。scenes 配列、short narration と long narration のテキスト、各シーンの画像パスと音声パスがすべて書き込まれた状態で出力されます。Step 03 では再び CodeAgents が動き、index.html の表示文言をテーマに合わせて書き換えます。タイトルや説明文がテンプレートから今回のトピックに差し替えられて、動画の骨格が完成します。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 7.92,
      "long_start_sec": 0.0,
      "long_duration_sec": 49.968
    },
    {
      "id": "scene_004",
      "title": "後半ステップ（Step 04〜99）",
      "expression": "neutral",
      "accent": "#ffbf47",
      "accent_soft": "rgba(255, 191, 71, 0.18)",
      "kicker": "STEPS 04-99",
      "headline": "画像・音声を生成して\n完成まで一気に仕上げる",
      "lead": "Step 04 で画像生成、Step 05 で中間確認、Step 06 で音声合成、Step 07 で再生時間更新、Step 08 で最終確認、Step 99 で完成案内です。",
      "subtitle": "後半 5 ステップで画像・音声が揃い、MCP が全自動で動画ページを完成させる。",
      "image": "images/scene_004.png",
      "image_prompt": "Vertical 2:3 pipeline diagram showing five steps labeled Step 04 image generation, Step 05 intermediate check, Step 06 voice synthesis, Step 07 duration update, Step 08 final check, ending at completed video page, warm amber accent, dark background, clean enterprise flow chart",
      "chips": [
        "Step 04: 画像生成",
        "Step 05: 中間確認",
        "Step 06: 音声合成",
        "Step 07: 再生時間更新",
        "Step 08 / 99: 確認・完成"
      ],
      "metrics": [
        {
          "label": "後半ステップ数",
          "value": "5+完成"
        },
        {
          "label": "画像生成MCP",
          "value": "aidiy_image"
        },
        {
          "label": "音声合成MCP",
          "value": "aidiy_tts"
        }
      ],
      "cards": [
        {
          "title": "Step 04: 画像生成",
          "lines": [
            "aidiy_image_generation MCP を使用",
            "各シーンの image_prompt から自動生成",
            "images/scene_NNN.png に保存"
          ]
        },
        {
          "title": "Step 05: 中間確認",
          "lines": [
            "シナリオ・HTML・画像の内容を検証",
            "問題があれば修正",
            "すべて問題なければ次へ"
          ]
        },
        {
          "title": "Step 06: 音声合成",
          "lines": [
            "aidiy_text_to_speech MCP を使用",
            "edge TTS で short/long 各ナレーション",
            "audio/short_scene_NNN.mp3 等に保存"
          ]
        },
        {
          "title": "Step 07〜99",
          "lines": [
            "ffmpeg で実再生時間を計測",
            "scenario.js の duration_sec を更新",
            "最終確認 → 完成案内"
          ]
        }
      ],
      "facts": [
        "Step 04 は aidiy_image_generation MCP で各シーン画像を image_prompt から自動生成する。",
        "Step 06 は aidiy_text_to_speech MCP（edge TTS）で short/long ナレーション音声を生成する。",
        "Step 07 は ffmpeg で生成音声の実再生時間を計測し scenario.js の duration_sec を更新する。"
      ],
      "evidence": [
        {
          "source": "共通,mcp利用による自動ビデオ生成手順.md",
          "text": "Step 04: aidiy_image_generation MCP で各シーン画像を自動生成。Step 06: aidiy_text_to_speech MCP で short/long ナレーション音声を生成（edge TTS）。Step 07: ffmpeg で実再生時間を計測し duration_sec を更新。"
        }
      ],
      "short_narration": "Step 04〜07 で画像生成・中間確認・音声合成・再生時間更新を経て、Step 08 で完成します。",
      "long_narration": "後半の Step 04 では、aidiy_image_generation MCP が各シーンの image_prompt を読んで PNG 画像を自動生成します。images フォルダに scene_000.png から順番に保存されます。Step 05 は中間確認ステップで、シナリオ、HTML、生成された画像の内容を検証し、問題があれば修正します。Step 06 では aidiy_text_to_speech MCP が edge TTS を使い、short narration と long narration のテキストをそれぞれ MP3 音声ファイルに変換します。Step 07 では ffmpeg を使って生成した音声ファイルの実際の再生時間を計測し、scenario.js の duration_sec フィールドを正確な値に更新します。Step 08 で必須ファイル・画像数・音声数の最終確認を行い、すべて揃っていれば Step 99 の完成案内に進みます。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 9.048,
      "long_start_sec": 0.0,
      "long_duration_sec": 56.112
    },
    {
      "id": "scene_005",
      "title": "MCP と CodeAgents の役割",
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123, 140, 255, 0.18)",
      "kicker": "MCP + CODEAGENTS",
      "headline": "MCP が生成し\nCodeAgents が組み立てる",
      "lead": "画像・音声・動画計測は MCP が担当し、シナリオ生成・HTML 修正は CodeAgents が担当します。それぞれの得意領域を活かして全自動化を実現しています。",
      "subtitle": "MCP の生成能力と CodeAgents の推論能力が組み合わさって全自動化が完成する。",
      "image": "images/scene_005.png",
      "image_prompt": "Vertical 2:3 architecture diagram showing MCP tools on the left including image generation, text to speech, ffmpeg, and CodeAgents on the right handling scenario and HTML, connected by workflow arrows to completed video page, blue-violet accent, dark background, professional technical illustration",
      "chips": [
        "aidiy_image_generation",
        "aidiy_text_to_speech",
        "aidiy_ffmpeg_control",
        "CodeAgents (Step 02/03)",
        "aidiy_code_agents"
      ],
      "metrics": [
        {
          "label": "生成系MCP",
          "value": "3種"
        },
        {
          "label": "CodeAgents担当",
          "value": "2ステップ"
        },
        {
          "label": "連携方式",
          "value": "SSE/HTTP"
        }
      ],
      "cards": [
        {
          "title": "MCP の担当",
          "lines": [
            "aidiy_image_generation: シーン画像生成",
            "aidiy_text_to_speech: 音声合成 (edge TTS)",
            "aidiy_ffmpeg_control: 再生時間計測"
          ]
        },
        {
          "title": "CodeAgents の担当",
          "lines": [
            "Step 02: scenario.js 生成",
            "Step 03: index.html 更新",
            "推論能力でテーマに合わせて作成"
          ]
        },
        {
          "title": "aidiy_code_agents MCP",
          "lines": [
            "CodeAgents の実行を MCP 経由で呼び出し",
            "claude_sdk / copilot_cli 等を選択可能",
            "プロンプトとプロジェクトパスを渡す"
          ]
        },
        {
          "title": "連携のポイント",
          "lines": [
            "MCP は HTTP POST で呼び出せる",
            "CodeAgents はファイルを直接編集",
            "それぞれが自分の得意領域を担当"
          ]
        }
      ],
      "facts": [
        "画像生成・音声合成・再生時間計測は MCP（aidiy_image_generation / aidiy_text_to_speech / aidiy_ffmpeg_control）が担当する。",
        "scenario.js 生成・index.html 更新は CodeAgents（aidiy_code_agents MCP 経由）が担当する。",
        "MCP は SSE / Streamable HTTP / stdio の 3 トランスポートで port 8095 から利用できる。"
      ],
      "evidence": [
        {
          "source": "共通,mcp利用による自動ビデオ生成手順.md",
          "text": "Step 02/03 は CodeAgents が担当。Step 04/06/07 は MCP（image_generation / text_to_speech / ffmpeg_control）が担当。"
        },
        {
          "source": "AGENTS.md",
          "text": "backend_tools は 14 個の MCP サーバーを SSE / Streamable HTTP / stdio の 3 トランスポートで同一ポート 8095 に集約します。"
        }
      ],
      "short_narration": "画像・音声・計測は MCP が、シナリオ・HTML は CodeAgents が担当し、全自動化を実現します。",
      "long_narration": "ビデオページ生成の全自動化は、MCP と CodeAgents の役割分担で成り立っています。MCP は決まった処理を高速に実行する担当です。aidiy_image_generation が各シーンの画像を生成し、aidiy_text_to_speech が edge TTS でナレーション音声を合成し、aidiy_ffmpeg_control が音声ファイルの実際の再生時間を計測します。一方、CodeAgents はテーマを理解して創造的なテキストを生成する担当です。Step 02 では scenario.js のシーン構成とナレーションを、Step 03 では index.html の表示文言をテーマに合わせて書き起こします。CodeAgents は aidiy_code_agents MCP を通じて呼び出され、claude_sdk や copilot_cli など複数の AI から選択できます。この MCP の確実性と CodeAgents の推論能力の組み合わせが、高品質な動画ページの全自動生成を可能にしています。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 8.64,
      "long_start_sec": 0.0,
      "long_duration_sec": 58.536
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
      "headline": "ご視聴ありがとうございました。\nあなたなら AiDiy で何を作りますか？",
      "lead": "topic を書くだけで動画ページが全自動生成される AiDiy のビデオページ生成機能、ぜひ手元で試してみてください。",
      "subtitle": "チャンネル登録で応援してください。次の動画でまた会いましょう！",
      "image": "images/scene_999.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "image_prompt": "Square 1:1 ending visual for AiDiy Video Page Generation. Beautiful typography centered on 'Thank you for Watching', refined luxury tech style with film reel and code motif, dark blue-violet gradient background, subtle glow, clean centered layout, premium and readable, polished square closing card for a feature introduction video.",
      "short_narration": "ご視聴ありがとうございました。チャンネル登録をぜひお願いします。AiDiy を使って自分だけのビデオを作ってみませんか？",
      "long_narration": "ご視聴ありがとうございました。この動画自体が、AiDiy のビデオページ生成機能で作られています。シナリオ作成から画像生成、音声合成、HTML 組み立てまで、MCP と CodeAgents が全自動で担当しました。AiDiy のビデオページ生成機能は、topic を設定ファイルに書いてスクリプトを実行するだけで、プロ品質の動画ページが出来上がります。自社紹介、技術解説、製品デモ、チュートリアルなど、あらゆるテーマに応用できます。ひとりアバター向けと二人掛け合い向けの 2 スクリプトで、表現の幅も広がります。気に入っていただけたら、チャンネル登録でぜひ応援してください。新機能や活用事例を続々とお届けします。AiDiy を使えば、次の動画もあなた自身の手で全自動生成できます。さあ、あなたならどんなテーマで動画を作りますか？",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 8.832,
      "long_start_sec": 0.0,
      "long_duration_sec": 53.808
    }
  ],
  "total_short_duration_sec": 55.296,
  "total_long_duration_sec": 356.832
};
