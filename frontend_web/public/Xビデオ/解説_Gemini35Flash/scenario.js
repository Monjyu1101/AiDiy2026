window.SCENARIO = {
  "project_name": "Gemini 3.5 Flash 解説 (掛け合い版)",
  "version": "duo-v2",
  "title": "Gemini 3.5 Flash — Google DeepMind 最新モデル解説",
  "assets_policy": {
    "male_avatar": "../vrm/VRM_male.vrm",
    "female_avatar": "../vrm/VRM_female.vrm",
    "tts_male": "edge:male",
    "tts_female": "edge:female",
    "audio_output_dir": "frontend_web/public/Xビデオ/解説_Gemini3-5Flash/audio"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "Gemini 3.5 Flash とは",
      "accent": "#1a73e8",
      "accent_soft": "rgba(26, 115, 232, 0.18)",
      "layout": "hero",
      "kicker": "GOOGLE DEEPMIND 2026",
      "headline": "Gemini 3.5 Flash\nFlashレベルのレイテンシで\nフロンティア性能を実現",
      "lead": "Google DeepMind が 2026年5月に公開した最新モデル。速さと賢さを両立した Gemini 3.5 Flash を解説します。",
      "image": "images/scene_000.png",
      "source_summary": "Google DeepMind が 2026年5月に公開した Gemini 3.5 Flash は、Flash レベルの低レイテンシを維持しながらフロンティア性能を実現した最新モデル（現在プレビュー状態）。1M トークンの長文コンテキスト、ネイティブマルチモーダル処理、エージェントベンチマークトップクラスのスコアを特徴とする。AiDiy の AIコア / Code AI に gemini-3.5-flash として組み込み可能。",
      "factual_bullets": [
        "モデルID: gemini-3.5-flash（2026年5月、現在プレビュー状態）",
        "Flash レベルのレイテンシを維持しながらフロンティア性能を実現",
        "1M トークンの長文コンテキスト対応",
        "テキスト・画像・動画・音声・PDF のネイティブマルチモーダル処理",
        "SWE-Bench Pro 55.1%、Terminal-bench 76.2%、MCP Atlas 83.6%",
        "Function Calling・Structured Output・Code Execution 対応",
        "AiDiy AIコア / Code AI に gemini-3.5-flash として組み込み可能"
      ],
      "forbidden_elements": [
        "未確認のベンチマーク数値を断言しない",
        "他社モデルの具体的スコアを比較表示しない",
        "正式リリース済みであるかのように誇張しない"
      ],
      "image_prompt": "Futuristic AI concept illustration: A glowing blue-green Gemini constellation symbol with dual orbiting rings representing speed and intelligence, dark gradient background with Google color accents (blue, red, yellow, green). Neural network pathways radiate outward from the center. Clean modern tech aesthetic suitable for AI explainer video intro.",
      "source_documents": [
        "Google DeepMind Gemini 3.5 Flash 公式発表 (2026年5月)",
        "gemini-3.5-flash モデルカード / プレビュー情報"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Google DeepMind の最新モデル Gemini 3.5 Flash を解説します。この動画は AiDiy で自動生成されました。",
          "naration_text": "今回は、Google DeepMind が 2026年5月に公開した最新モデル、Gemini 3.5 Flash を解説します。Flash レベルの速さを保ちながら、フロンティア性能を実現した注目のモデルです。なお、この動画は AiDiy の video_generation機能 を使って自動生成されました。ぜひ最後までご覧ください。",
          "audio": "audio/dlg_000_01_female.mp3",
          "duration_sec": 22.464
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "長文コンテキスト・マルチモーダル・エージェント性能・ツール機能の順に紹介します。",
          "naration_text": "今回の解説では、1M トークンの長文コンテキスト、ネイティブマルチモーダル処理、エージェントベンチマーク、ツール活用機能の順に紹介します。後半では AiDiy への組み込み方法と具体的な活用シナリオもお伝えします。",
          "audio": "audio/dlg_000_02_male.mp3",
          "duration_sec": 13.896
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "速さと賢さを両立したモデルが、なぜ注目されているのか一緒に見ていきましょう。",
          "naration_text": "これまでの AI モデルは「速いけど性能が低い」か「性能は高いけど遅い」という二択が多かったのですが、Gemini 3.5 Flash はその両方を高いレベルで実現したとして注目を集めています。どんな仕組みで実現しているのか、一緒に見ていきましょう。",
          "audio": "audio/dlg_000_03_female.mp3",
          "duration_sec": 16.872
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "現在はプレビュー状態ですが、AiDiy にも今すぐ組み込んで試せます。",
          "naration_text": "Gemini 3.5 Flash は 2026年5月時点でプレビュー状態ですが、AiDiy の設定を少し変えるだけですぐに使い始めることができます。実際にどう組み込むかも後半で詳しく紹介しますので、ぜひ参考にしてください。",
          "audio": "audio/dlg_000_04_male.mp3",
          "duration_sec": 13.92
        }
      ],
      "duration_sec": 67.152
    },
    {
      "id": "scene_001",
      "title": "1M トークンの長文コンテキスト対応",
      "accent": "#34a853",
      "accent_soft": "rgba(52, 168, 83, 0.18)",
      "kicker": "LONG CONTEXT",
      "headline": "1M トークンの\n長文コンテキスト対応",
      "lead": "100万トークンの文脈を一度に扱い、長大なコードベースや文書も丸ごと処理できます。",
      "image": "images/scene_001.png",
      "source_summary": "Gemini 3.5 Flash は 1M（100万）トークンのコンテキストウィンドウを持つ。これにより大規模コードベースの全体把握、長文ドキュメントの一括解析、長時間の会話履歴の維持が可能になる。",
      "factual_bullets": [
        "コンテキストウィンドウ: 1M（100万）トークン",
        "大規模コードベースを丸ごとコンテキストに投入可能",
        "長文 PDF・ドキュメントの一括解析に対応",
        "長時間エージェントセッションの会話履歴を保持",
        "Flash レベルのレイテンシを維持したまま長文を処理"
      ],
      "forbidden_elements": [
        "トークン数を Gemini 2.0 以前と混同しない",
        "すべてのユースケースで同等の精度を保証しない"
      ],
      "image_prompt": "Abstract data visualization: A massive cylindrical structure filled with flowing text tokens and document pages, glowing green at the top representing the 1M token boundary. Dark background with green accent tones. Streams of data spiral around the cylinder. Clean tech illustration style.",
      "source_documents": [
        "Google DeepMind Gemini 3.5 Flash 公式発表 (2026年5月)"
      ],
      "chips": [
        "1M トークン",
        "長文ドキュメント",
        "大規模コードベース",
        "会話履歴"
      ],
      "metrics": [
        {
          "label": "コンテキスト",
          "value": "1M tokens"
        },
        {
          "label": "用途",
          "value": "コード・文書・履歴"
        }
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Gemini 3.5 Flash は 1M トークン、つまり 100万トークンのコンテキストを扱えます。",
          "naration_text": "Gemini 3.5 Flash は、1M トークン、つまり 100万トークンのコンテキストウィンドウを持ちます。これにより、大規模なコードベースや長文のドキュメントを丸ごとモデルに渡して解析させることができます。",
          "audio": "audio/dlg_001_01_female.mp3",
          "duration_sec": 13.656
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "長時間のエージェントセッションでも会話の文脈をずっと保持できます。",
          "naration_text": "長時間にわたるエージェントセッションでも、会話の文脈をずっと保持できるのが大きな強みです。途中で文脈が切れる心配がなく、複雑なタスクを安心して任せられます。Flash レベルのレイテンシを維持したままこれを実現しているのも注目ポイントです。",
          "audio": "audio/dlg_001_02_male.mp3",
          "duration_sec": 15.456
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "100万トークンって、具体的にどのくらいの量なのでしょう？",
          "naration_text": "100万トークンというと少し分かりにくいかもしれません。おおよその目安として、日本語なら 50万〜80万字分、英語の文章なら 750ページほどの書籍に相当すると言われています。つまり、かなりの分量のドキュメントやコードをまとめて渡せるわけです。",
          "audio": "audio/dlg_001_03_female.mp3",
          "duration_sec": 17.928
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "チームのコードベース全体を一発でレビューするような使い方もできますね。",
          "naration_text": "たとえばチームで開発しているプロジェクト全体のコードを一度に投入して「このコードのどこに問題がある？」と聞くような使い方ができます。これまでファイルを分割して何度もやり取りしていた作業が、一回の問い合わせで完結するようになります。",
          "audio": "audio/dlg_001_04_male.mp3",
          "duration_sec": 14.088
        }
      ],
      "duration_sec": 61.128
    },
    {
      "id": "scene_002",
      "title": "ネイティブマルチモーダル処理",
      "accent": "#ea4335",
      "accent_soft": "rgba(234, 67, 53, 0.18)",
      "kicker": "MULTIMODAL",
      "headline": "テキスト・画像・動画・音声・PDF\nネイティブマルチモーダル処理",
      "lead": "追加変換なしに、多様な形式の入力を直接扱える真のマルチモーダル基盤モデルです。",
      "image": "images/scene_002.png",
      "source_summary": "Gemini 3.5 Flash はテキスト・画像・動画・音声・PDF をネイティブで処理するマルチモーダルモデル。外部変換ツール不要で、さまざまな形式の入力をそのままモデルに渡せる。",
      "factual_bullets": [
        "テキスト: 自然言語の読解・生成・要約",
        "画像: 写真・図表・スクリーンショットの解析",
        "動画: 映像コンテンツの内容理解・要約",
        "音声: 音声入力の認識・内容理解",
        "PDF: 文書のネイティブ解析（OCR 不要）",
        "すべての入力形式を単一モデルで統一処理"
      ],
      "forbidden_elements": [
        "動画・音声の生成機能があるかのように誤解させない",
        "すべての言語・方言の音声認識精度を均一に主張しない"
      ],
      "image_prompt": "Futuristic multimodal AI illustration: Five glowing orbs arranged in a pentagon representing text, image, video, audio, and PDF inputs, all connected by light beams to a central Gemini-style dual-ring logo. Red accent tones on dark gradient background. Data flowing between each modality.",
      "source_documents": [
        "Google DeepMind Gemini 3.5 Flash 公式発表 (2026年5月)"
      ],
      "chips": [
        "テキスト",
        "画像",
        "動画",
        "音声",
        "PDF"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Gemini 3.5 Flash はテキスト・画像・動画・音声・PDF をネイティブで処理できます。",
          "naration_text": "Gemini 3.5 Flash は、テキスト、画像、動画、音声、PDF のすべてをネイティブで処理できるマルチモーダルモデルです。外部の変換ツールを介さずに、さまざまな形式の入力をそのままモデルに渡して扱えます。",
          "audio": "audio/dlg_002_01_female.mp3",
          "duration_sec": 14.928
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "PDF の OCR 変換なしに、文書をそのまま解析できるのは実務で大きな強みです。",
          "naration_text": "たとえば PDF の場合、OCR 変換を挟まずに文書をそのまま解析できます。スクリーンショットや動画の内容理解も単一モデルで行えるので、業務システムへの組み込みがシンプルになります。これが実務において非常に大きな強みです。",
          "audio": "audio/dlg_002_02_male.mp3",
          "duration_sec": 15.144
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "「ネイティブ」というのが重要なポイントで、変換コストが一切かかりません。",
          "naration_text": "「ネイティブ」という言葉が重要で、画像や音声を文字に直してからテキストとして処理するのではなく、最初からそれぞれの形式をそのまま理解できる設計になっています。変換の手間がない分、精度や速度にもよい影響があります。",
          "audio": "audio/dlg_002_03_female.mp3",
          "duration_sec": 15.6
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "会議の録音とスライドを一緒に渡して議事録を自動生成、という活用も期待できます。",
          "naration_text": "実用的な例として、会議の音声録音と資料のスライド画像を一緒にモデルに渡して、議事録を自動生成するような使い方が考えられます。これまでは別々の処理が必要だった作業を、一つのモデルへの問い合わせで完結できるのは大きなメリットです。",
          "audio": "audio/dlg_002_04_male.mp3",
          "duration_sec": 15.408
        }
      ],
      "duration_sec": 61.08
    },
    {
      "id": "scene_003",
      "title": "エージェントベンチマーク — SWE・Terminal・MCP でトップクラス",
      "accent": "#fbbc04",
      "accent_soft": "rgba(251, 188, 4, 0.18)",
      "kicker": "AGENT BENCHMARKS",
      "headline": "エージェントタスクで\nトップクラスのベンチマーク",
      "lead": "SWE-Bench Pro 55.1%・Terminal-bench 76.2%・MCP Atlas 83.6% を達成（発表時点の報告値）。",
      "image": "images/scene_003.png",
      "source_summary": "Gemini 3.5 Flash はエージェントタスクの主要ベンチマークでトップクラスのスコアを記録（発表時点の報告値）。SWE-Bench Pro 55.1%（実世界 GitHub Issue 解決）、Terminal-bench 76.2%（ターミナル操作エージェント）、MCP Atlas 83.6%（MCP ツール呼び出しエージェント）。",
      "factual_bullets": [
        "SWE-Bench Pro: 55.1%（実世界 GitHub Issue の自動解決率、報告値）",
        "Terminal-bench: 76.2%（ターミナル操作エージェントのベンチマーク、報告値）",
        "MCP Atlas: 83.6%（MCP ツール呼び出しエージェントのベンチマーク、報告値）",
        "Flash レベルのレイテンシでこれらのスコアを達成",
        "エージェントタスクにおいてフロンティアモデルと同等の性能を示す"
      ],
      "forbidden_elements": [
        "ベンチマーク数値を他社モデルと直接比較しない",
        "すべての実業務タスクで同等の成功率を保証しない",
        "ベンチマーク条件の詳細を確認せずに断言しない"
      ],
      "image_prompt": "Data dashboard illustration: Three large circular progress meters on a dark background with yellow accent tones. First shows 55.1% labeled SWE-Bench Pro with GitHub-style icons. Second shows 76.2% labeled Terminal-bench with terminal prompt symbols. Third shows 83.6% labeled MCP Atlas with tool connection icons. Futuristic AI benchmark visualization.",
      "source_documents": [
        "Google DeepMind Gemini 3.5 Flash 公式発表 (2026年5月)",
        "SWE-Bench Pro / Terminal-bench / MCP Atlas ベンチマーク結果"
      ],
      "chips": [
        "SWE-Bench Pro",
        "Terminal-bench",
        "MCP Atlas",
        "エージェント性能"
      ],
      "metrics": [
        {
          "label": "SWE-Bench Pro",
          "value": "55.1%"
        },
        {
          "label": "Terminal-bench",
          "value": "76.2%"
        },
        {
          "label": "MCP Atlas",
          "value": "83.6%"
        }
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Gemini 3.5 Flash はエージェントタスクで非常に高いベンチマーク結果を出しています。",
          "naration_text": "Gemini 3.5 Flash は、エージェントタスクの主要ベンチマークでトップクラスのスコアを記録しています。実世界の GitHub Issue を自動解決する SWE-Bench Pro では 55.1%、ターミナル操作エージェントの Terminal-bench では 76.2% を達成したと報告されています。",
          "audio": "audio/dlg_003_01_female.mp3",
          "duration_sec": 19.8
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "MCP Atlas では 83.6% で、MCP ツールを使ったエージェント性能の高さを示しています。",
          "naration_text": "さらに MCP ツール呼び出しエージェントのベンチマーク MCP Atlas では 83.6% というスコアを達成しています。AiDiy でも MCP を多用しているので、この高いスコアは非常に心強いですね。Flash レベルの速さでこれらを実現している点が際立っています。",
          "audio": "audio/dlg_003_02_male.mp3",
          "duration_sec": 16.464
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "そもそもエージェントベンチマークって、何を測っているのでしょうか？",
          "naration_text": "エージェントベンチマークとは、AI が人間のような形で複数ステップのタスクを自律的にこなせるかどうかを測る指標です。SWE-Bench Pro は実際の GitHub のバグ修正課題を AI が自力で解けるかどうかをテストするもので、実世界に近い難易度が特徴です。",
          "audio": "audio/dlg_003_03_female.mp3",
          "duration_sec": 18.456
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "高スコアはそのまま「自動化できる仕事の幅が広い」ことを意味します。",
          "naration_text": "これらのスコアが高いということは、AI が自律的にこなせるタスクの幅が広いということを意味します。開発作業、ターミナル操作、外部ツールの呼び出しなど、実際の業務に近い作業を任せやすくなるわけです。コスト削減や生産性向上に直結する指標と言えます。",
          "audio": "audio/dlg_003_04_male.mp3",
          "duration_sec": 17.184
        }
      ],
      "duration_sec": 71.904
    },
    {
      "id": "scene_004",
      "title": "Function Calling・Structured Output・Code Execution",
      "accent": "#1a73e8",
      "accent_soft": "rgba(26, 115, 232, 0.18)",
      "kicker": "TOOL FEATURES",
      "headline": "Function Calling・Structured Output\nCode Execution で豊富なツール活用",
      "lead": "外部システムとの連携・構造化データの出力・コードの直接実行を標準でサポートします。",
      "image": "images/scene_004.png",
      "source_summary": "Gemini 3.5 Flash は Function Calling（外部 API・ツール呼び出し）、Structured Output（JSON など構造化形式での出力）、Code Execution（コードの直接実行と結果返却）を標準搭載。これらはエージェントシステム構築の基盤となる。",
      "factual_bullets": [
        "Function Calling: 外部 API・ツールをモデルから直接呼び出せる",
        "Structured Output: JSON など構造化形式でレスポンスを得られる",
        "Code Execution: Python コードをモデルが実行し結果を返せる",
        "MCP との組み合わせでエージェントシステムを効率的に構築",
        "複数ツールの並列呼び出しにも対応"
      ],
      "forbidden_elements": [
        "対応している関数の種類に制限がないかのように誇張しない",
        "Code Execution の実行環境の詳細を確認せずに断言しない"
      ],
      "image_prompt": "Tech diagram illustration: Three interconnected modules on a dark background with blue accent tones. First module labeled 'Function Calling' shows API call arrows. Second labeled 'Structured Output' displays JSON tree structures. Third labeled 'Code Execution' shows Python code snippets running. Clean modern software architecture diagram style.",
      "source_documents": [
        "Google DeepMind Gemini 3.5 Flash 公式発表 (2026年5月)",
        "Gemini API ドキュメント"
      ],
      "chips": [
        "Function Calling",
        "Structured Output",
        "Code Execution",
        "MCP連携"
      ],
      "cards": [
        {
          "title": "Function Calling",
          "lines": [
            "外部 API やツールをモデルから直接呼び出せる",
            "MCP との組み合わせで強力なエージェントを構築",
            "並列ツール呼び出しにも対応"
          ]
        },
        {
          "title": "Structured Output",
          "lines": [
            "JSON などの構造化形式でレスポンスを得られる",
            "後段処理との連携がシンプルになる",
            "スキーマを指定した精密な出力制御が可能"
          ]
        },
        {
          "title": "Code Execution",
          "lines": [
            "Python コードをモデルが実行して結果を返す",
            "計算・データ処理・グラフ生成をその場で完結",
            "エージェントの自律的な問題解決に活用"
          ]
        }
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Function Calling・Structured Output・Code Execution の3機能を標準装備しています。",
          "naration_text": "Gemini 3.5 Flash は、外部ツールを呼び出す Function Calling、構造化データを出力する Structured Output、コードを直接実行する Code Execution を標準でサポートしています。これらはエージェントシステムを構築する際の基盤となる機能です。",
          "audio": "audio/dlg_004_01_female.mp3",
          "duration_sec": 16.752
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "AiDiy の MCP との組み合わせで、さらに強力なエージェントを構築できます。",
          "naration_text": "AiDiy では MCP を多用しているので、Function Calling との組み合わせがとても相性がいいです。Structured Output で JSON を確実に得られるのでシステム連携も安定しますし、Code Execution で計算やデータ処理をその場で完結させる使い方も広がります。",
          "audio": "audio/dlg_004_02_male.mp3",
          "duration_sec": 15.816
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Structured Output があると、AI の返答をそのままシステムに渡せるのが便利ですね。",
          "naration_text": "Structured Output は業務システムとの連携で特に役立ちます。AI に対して「JSON 形式で回答してください」と指定すれば、そのまま後段のシステムに渡せる形で返ってきます。パース処理の手間が省けるだけでなく、形式がずれることによるエラーも防ぎやすくなります。",
          "audio": "audio/dlg_004_03_female.mp3",
          "duration_sec": 18.936
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Code Execution を使うと、計算やグラフ生成もその場で完結させられます。",
          "naration_text": "Code Execution を使うと、たとえば「このデータを集計してグラフを作って」という依頼に対して、モデル自身が Python コードを書いて実行し、結果の数字やグラフをそのまま返してくれます。試行錯誤しながら進めるデータ分析作業に特に向いています。",
          "audio": "audio/dlg_004_04_male.mp3",
          "duration_sec": 15.6
        }
      ],
      "duration_sec": 67.104
    },
    {
      "id": "scene_005",
      "title": "AiDiy AIコア / Code AI への組み込み",
      "accent": "#34a853",
      "accent_soft": "rgba(52, 168, 83, 0.18)",
      "kicker": "AIDIY INTEGRATION",
      "headline": "AiDiy の AIコア / Code AI に\ngemini-3.5-flash を組み込む",
      "lead": "設定ファイルを数行変えるだけで、Gemini 3.5 Flash をチャット・コード支援に活用できます。",
      "image": "images/scene_005.png",
      "source_summary": "AiDiy では AIコア設定の CHAT_AI_NAME に gemini_chat（または gemini 系の _chat サフィックスのモデル）を、CODE_AI 系に gemini_cli を指定することで Gemini 3.5 Flash を利用できる。backend_server/_config/ 内の設定ファイルを更新するだけで切り替え可能。",
      "factual_bullets": [
        "AIコアの CHAT_AI_NAME: gemini 系モデルを指定（_chat サフィックス）",
        "CODE_AI1_NAME〜CODE_AI6_NAME: gemini_cli を指定",
        "設定ファイル: backend_server/_config/AiDiy_key.json などを更新",
        "Google AI Studio / Vertex AI の API キーが必要",
        "gemini-3.5-flash は Flash レベルのレイテンシなので Code AI に最適"
      ],
      "forbidden_elements": [
        "設定ファイルの正確なキー名を確認せずに断言しない",
        "すべての AiDiy バージョンで同じ設定手順を保証しない"
      ],
      "image_prompt": "Software integration diagram: AiDiy dashboard interface on the left with flowing data streams connecting to a glowing Gemini logo on the right. Green accent tones on dark background. Configuration file icons and API connection symbols between the two systems. Clean tech illustration style.",
      "source_documents": [
        "AiDiy 実装コード backend_server/_config/",
        "AiDiy AGENTS.md / CLAUDE.md"
      ],
      "chips": [
        "CHAT_AI_NAME",
        "gemini_cli",
        "AiDiy_key.json",
        "API連携"
      ],
      "facts": [
        "AIコアの設定を gemini 系モデルに切り替えるだけで即座に利用を開始できます。",
        "Code AI パネルで gemini_cli を使うと、Flash のレイテンシの低さがコード補完のレスポンスに直結します。"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AiDiy の設定ファイルを更新するだけで Gemini 3.5 Flash を使い始められます。",
          "naration_text": "AiDiy の AIコアでは、CHAT_AI_NAME に gemini 系のモデルを指定し、CODE_AI 系のパネルに gemini_cli を設定するだけで Gemini 3.5 Flash を使い始められます。難しい実装変更は必要ありません。",
          "audio": "audio/dlg_005_01_female.mp3",
          "duration_sec": 17.136
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Flash のレイテンシの低さが Code AI のレスポンスに直接活きてきます。",
          "naration_text": "特に Code AI パネルでの活用がおすすめです。Gemini 3.5 Flash は Flash レベルのレイテンシの低さを持つので、コード補完や説明を求めたときのレスポンスがとても速く、開発体験が向上します。",
          "audio": "audio/dlg_005_02_male.mp3",
          "duration_sec": 12.456
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "API キーを取得して設定ファイルに書き加えるだけで、すぐに使えるのは嬉しいですね。",
          "naration_text": "Google AI Studio から API キーを取得して、AiDiy の設定ファイルに書き加えるだけで使い始められます。複雑なセットアップは不要で、すでに AiDiy を使っている方なら数分で切り替えが完了します。",
          "audio": "audio/dlg_005_03_female.mp3",
          "duration_sec": 13.848
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "チャット AI と Code AI の両方に Gemini を使うことで、一貫した体験が得られます。",
          "naration_text": "CHAT_AI_NAME と CODE_AI の両方に Gemini 3.5 Flash を設定すれば、チャットでの相談からコード支援まで一貫して同じモデルを使えます。モデルの特性を把握しやすくなりますし、長文コンテキストのメリットも両方の場面で活かせます。",
          "audio": "audio/dlg_005_04_male.mp3",
          "duration_sec": 15.96
        }
      ],
      "duration_sec": 59.4
    },
    {
      "id": "scene_006",
      "title": "活用シナリオ — 長文解析・マルチモーダル業務・エージェント自動化",
      "accent": "#ea4335",
      "accent_soft": "rgba(234, 67, 53, 0.18)",
      "kicker": "USE CASES",
      "headline": "長文解析・マルチモーダル業務\nエージェント自動化に活用",
      "lead": "1M トークン・マルチモーダル・高エージェント性能の三拍子が揃ったユースケースを紹介します。",
      "image": "images/scene_006.png",
      "source_summary": "Gemini 3.5 Flash の主な活用シナリオ: 大規模コードベースの一括レビュー（1M トークン活用）、会議録音・議事録 PDF の一括処理（マルチモーダル）、MCP を活用した自律エージェント自動化（エージェント性能）。AiDiy との組み合わせで業務システムに組み込める。",
      "factual_bullets": [
        "大規模コードベースレビュー: 1M トークンで全コードを一括投入して解析",
        "ドキュメント処理: PDF・画像・音声を混在させて一括処理",
        "エージェント自動化: MCP ツールと組み合わせた自律タスク処理",
        "AiDiy Code AI: Flash のレイテンシでコード補完・説明を高速提供",
        "業務システム連携: Structured Output で JSON を取得して後段処理に渡す"
      ],
      "forbidden_elements": [
        "すべての業務タスクで完璧な結果を保証しない",
        "コスト・レート制限の詳細を確認せずに断言しない"
      ],
      "image_prompt": "Three-panel use case illustration: Left panel shows code files flowing into a large container representing 1M token context. Center panel shows PDF, audio wave, and image icons merging into a single processing node. Right panel shows an autonomous agent network with MCP tool icons. Blue, red, and green accent tones. Dark background, clean tech style.",
      "source_documents": [
        "Google DeepMind Gemini 3.5 Flash 公式発表 (2026年5月)",
        "AiDiy 活用事例"
      ],
      "chips": [
        "コードレビュー",
        "ドキュメント処理",
        "エージェント自動化",
        "業務システム連携"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "1M トークンを活かした大規模コードベースの一括レビューが実用的なユースケースです。",
          "naration_text": "1M トークンのコンテキストを活かせば、大規模なコードベース全体を一度に投入してレビューや解析を依頼できます。これまで分割して処理していた作業が、一発で完結するようになります。",
          "audio": "audio/dlg_006_01_female.mp3",
          "duration_sec": 12.888
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "MCP と組み合わせたエージェント自動化も、MCP Atlas の高スコアが示す通り得意分野です。",
          "naration_text": "MCP ツールと組み合わせたエージェント自動化も得意分野です。MCP Atlas で 83.6% を達成しているだけあって、実際のツール呼び出しがとても安定しています。AiDiy の MCP 基盤と組み合わせることで、業務の自動化を一段階進められると感じています。",
          "audio": "audio/dlg_006_02_male.mp3",
          "duration_sec": 17.256
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "会議録音と資料 PDF を一緒に渡して、要約や課題抽出をまとめて頼めます。",
          "naration_text": "マルチモーダルの強みを活かした使い方として、会議の録音ファイルと資料の PDF を一緒に渡して、議事録の作成と課題の抽出をまとめて依頼するというものが考えられます。これまで複数の手順が必要だった作業を一つの依頼で済ませられます。",
          "audio": "audio/dlg_006_03_female.mp3",
          "duration_sec": 16.728
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "AiDiy と Gemini 3.5 Flash の組み合わせは、業務自動化の幅を大きく広げます。",
          "naration_text": "AiDiy の業務システムテンプレートと Gemini 3.5 Flash の高い性能を組み合わせることで、配車管理、生産管理、在庫管理といった業務システムに AI を組み込む際のハードルがぐっと下がります。試してみたい方は、ぜひ AiDiy のドキュメントを参照してみてください。",
          "audio": "audio/dlg_006_04_male.mp3",
          "duration_sec": 15.912
        }
      ],
      "duration_sec": 62.784
    },
    {
      "id": "scene_999",
      "title": "まとめ",
      "accent": "#1a73e8",
      "accent_soft": "rgba(26, 115, 232, 0.18)",
      "layout": "hero",
      "kicker": "GOOGLE DEEPMIND 2026",
      "headline": "Gemini 3.5 Flash\n速さとフロンティア性能を両立した\n新しいスタンダード",
      "lead": "Flash レベルのレイテンシで 1M トークン・マルチモーダル・高エージェント性能を実現した次世代モデルです。",
      "image": "images/scene_999.png",
      "dialogue": [
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Gemini 3.5 Flash は、速さとフロンティア性能を両立した注目モデルです。",
          "naration_text": "Gemini 3.5 Flash は、Flash レベルの速さを保ちながら、1M トークンの長文処理、ネイティブマルチモーダル、トップクラスのエージェント性能、豊富なツール機能を実現した次世代モデルです。プレビュー段階ながら、すでに多くの可能性を感じさせてくれます。",
          "audio": "audio/dlg_999_01_male.mp3",
          "duration_sec": 16.056
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AiDiy への組み込みも設定を変えるだけなので、ぜひすぐに試してみてください。",
          "naration_text": "AiDiy への組み込みは設定ファイルを変えるだけで完了するので、すでに AiDiy を使っている方は今すぐ試せます。チャット AI としても Code AI としても活用でき、業務効率の改善にすぐつながります。",
          "audio": "audio/dlg_999_02_female.mp3",
          "duration_sec": 13.776
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "速さ・賢さ・多才さ・エージェント性能、四つの強みが揃ったモデルとして今後の活躍が楽しみです。",
          "naration_text": "速さ、賢さ、マルチモーダルの多才さ、高いエージェント性能という四つの強みが揃ったモデルとして、Gemini 3.5 Flash は業務活用の場でも大きな可能性を持っています。正式リリースに向けてさらなる改善も期待できます。",
          "audio": "audio/dlg_999_03_male.mp3",
          "duration_sec": 14.16
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "この動画は AiDiy の自動生成機能で作りました。ぜひチャンネル登録をお願いします！",
          "naration_text": "この動画は AiDiy の video_generation機能 を使って自動生成しました。シナリオ作成から画像・音声の生成まで、AiDiy が一連の工程を自動でこなしています。動画を気に入っていただけたら、ぜひチャンネル登録をお願いします。皆さんも AiDiy を使って、AI と一緒に楽しく仕事を自動化してみませんか？きっと「自分でも作れる！」という発見がありますよ。",
          "audio": "audio/dlg_999_04_female.mp3",
          "duration_sec": 26.136
        }
      ],
      "duration_sec": 70.128
    }
  ],
  "total_duration_sec": 520.68
};
