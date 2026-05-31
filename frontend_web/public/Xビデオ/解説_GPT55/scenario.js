window.SCENARIO = {
  "project_name": "GPT-5.5 解説 (掛け合い版)",
  "version": "duo-v2",
  "title": "GPT-5.5 最新機能と AiDiy 活用シナリオ解説",
  "assets_policy": {
    "male_avatar": "../_vrm/VRM_male.vrm",
    "female_avatar": "../_vrm/VRM_female.vrm",
    "tts_male": "edge:male",
    "tts_female": "edge:female",
    "audio_output_dir": "frontend_web/public/Xビデオ/解説_GPT5-5/audio"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "GPT-5.5 とは ― フロンティア性能をそのままのレイテンシで",
      "accent": "#10a37f",
      "accent_soft": "rgba(16, 163, 127, 0.18)",
      "layout": "hero",
      "kicker": "OPENAI GPT-5.5",
      "headline": "GPT-5.5\nフロンティア性能 × GPT-5.4 同等レイテンシ",
      "lead": "OpenAI が2026年4月に公開。速度を犠牲にせず、コーディング・推論・科学研究すべてで大幅な性能向上を実現。",
      "source_summary": "OpenAI が2026年4月に公開した GPT-5.5 は、GPT-5.4 と同等のレイテンシを維持しながらフロンティア性能を大幅に向上させた最新モデル。コーディング・ナレッジワーク・科学研究・長文コンテキスト・セキュリティ・抽象推論の全分野でトップクラスの数値を達成。",
      "factual_bullets": [
        "GPT-5.4 と同等のレイテンシを維持",
        "2026年4月に一般公開",
        "ChatGPT（Plus/Pro/Business/Enterprise）および Codex で提供",
        "API: 入力 $5/1M トークン・出力 $30/1M トークン",
        "AiDiy の AIコア / Code AI への組み込みが可能"
      ],
      "forbidden_elements": [
        "速度が大幅に低下するという表現",
        "完全な AGI だという根拠のない断言"
      ],
      "image_prompt": "A futuristic AI interface with 'GPT-5.5' in glowing teal text on a dark background. Clean modern tech aesthetic showing benchmark score panels, neural network nodes, and OpenAI branding style. Professional, high-tech atmosphere.",
      "image": "images/scene_000.png",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "GPT-5.5 が登場！この動画は AiDiy の video_generation 機能で自動生成されています。",
          "naration_text": "OpenAI が2026年4月に公開した GPT-5.5 は、GPT-5.4 と同等のレイテンシを維持しながら、フロンティア性能を大幅に向上させた最新モデルです。なお、この動画は AiDiy の video_generation 機能で自動生成されました。コーディング支援から科学研究まで、幅広い分野で卓越した性能を誇る GPT-5.5 の全貌を、今日はわかりやすくお伝えしていきます。",
          "audio": "audio/dlg_000_01_female.mp3",
          "duration_sec": 28.464
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "速度を落とさずに精度を上げた、実用的なフロンティアモデルですね。",
          "naration_text": "GPT-5.5 の最大の特徴は、速度と精度の両立にあります。GPT-5.4 と同等の応答速度を保ちながら、エージェント型コーディング・ナレッジワーク・科学研究・長文コンテキスト処理・サイバーセキュリティ・抽象的な推論と、非常に幅広い分野でフロンティア級のスコアを達成しています。速くて賢いという、実用的なモデルの理想形に近い存在です。",
          "audio": "audio/dlg_000_02_male.mp3",
          "duration_sec": 23.496
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "ChatGPT の Plus・Pro・Business・Enterprise と Codex で利用できます。",
          "naration_text": "GPT-5.5 は、ChatGPT の Plus・Pro・Business・Enterprise の各プランと、コーディング特化ツールの Codex でも利用できます。API の料金は、入力トークンが 100万あたり 5 ドル、出力トークンが同 30 ドルです。個人開発者から大企業まで幅広いニーズに対応できる提供体制が整っており、既存の OpenAI API をお使いの方はすぐに試せます。",
          "audio": "audio/dlg_000_03_female.mp3",
          "duration_sec": 27.072
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "ベンチマーク数値と AiDiy 活用例を交えながら、各機能を分野ごとに解説します。",
          "naration_text": "この動画では、具体的なベンチマーク数値を交えながら GPT-5.5 の主要機能を分野ごとにわかりやすく解説します。エージェント型コーディング・ナレッジワーク・科学研究・長文コンテキスト・セキュリティ・推論・提供プランと料金・AiDiy への組み込み活用シナリオまで、順番に見ていきます。ぜひ最後まで一緒にお楽しみください。",
          "audio": "audio/dlg_000_04_male.mp3",
          "duration_sec": 20.4
        }
      ],
      "duration_sec": 99.432
    },
    {
      "id": "scene_001",
      "title": "エージェント型コーディング ― Terminal-Bench・SWE・Expert 各ベンチ",
      "accent": "#0b6ea8",
      "accent_soft": "rgba(11, 110, 168, 0.18)",
      "kicker": "AGENTIC CODING",
      "headline": "エージェント型コーディングで\nトップクラスのベンチマーク",
      "lead": "Terminal-Bench 2.0: 82.7%、SWE-Bench Pro: 58.6%、Expert-SWE: 73.1%",
      "source_summary": "GPT-5.5 はエージェント型コーディング分野で高い性能を示す。Terminal-Bench 2.0（82.7%）・SWE-Bench Pro（58.6%）・Expert-SWE（73.1%）はいずれも現時点のトップクラス。",
      "factual_bullets": [
        "Terminal-Bench 2.0: 82.7%（ターミナル操作自律タスク）",
        "SWE-Bench Pro: 58.6%（実際のバグ修正タスク）",
        "Expert-SWE: 73.1%（専門家レベルの難易度）",
        "AiDiy の Code AI パネルに割り当てて活用可能"
      ],
      "forbidden_elements": [
        "全ての開発作業を完全に自動化できるという過大表現"
      ],
      "image_prompt": "A developer's terminal screen showing AI-generated code with benchmark score overlays: Terminal-Bench 2.0 82.7%, SWE-Bench Pro 58.6%, Expert-SWE 73.1%. Dark theme code editor, professional software development atmosphere, blue tones.",
      "image": "images/scene_001.png",
      "metrics": [
        {
          "label": "Terminal-Bench 2.0",
          "value": "82.7%"
        },
        {
          "label": "SWE-Bench Pro",
          "value": "58.6%"
        },
        {
          "label": "Expert-SWE",
          "value": "73.1%"
        }
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "コーディング系ベンチマークで GPT-5.5 は驚異的なスコアを記録しました。",
          "naration_text": "GPT-5.5 は、エージェント型コーディングの分野で非常に高い性能を示しています。ターミナル操作を自律的にこなす Terminal-Bench 2.0 では 82.7%、実際のソフトウェアバグを修正する SWE-Bench Pro では 58.6%、専門家レベルの難易度を持つ Expert-SWE では 73.1% を達成しました。これらはいずれも、現時点のトップクラスに位置する数値です。",
          "audio": "audio/dlg_001_01_female.mp3",
          "duration_sec": 28.776
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Terminal-Bench 2.0 の 82.7% は、熟練エンジニアの作業を自律的にこなせるレベルです。",
          "naration_text": "Terminal-Bench 2.0 は、AI がターミナル環境でどれだけ複雑なタスクを自律的にこなせるかを測るベンチマークです。GPT-5.5 が記録した 82.7% という数値は、熟練したエンジニアが行うような作業の多くを自動化できるレベルに達していることを示しています。コーディングエージェントとしての実用性が、この数値から強く伝わります。",
          "audio": "audio/dlg_001_02_male.mp3",
          "duration_sec": 21.336
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "SWE-Bench Pro と Expert-SWE でも、現時点で最高水準のスコアです。",
          "naration_text": "SWE-Bench Pro は、実際の GitHub リポジトリから取り出した難易度の高いバグ修正タスクを、どれだけ正確にこなせるかを評価するベンチマークです。GPT-5.5 は 58.6% を記録しています。さらに専門家レベルを想定した Expert-SWE では 73.1% と、より難しいタスクでも安定して高いスコアを出しています。",
          "audio": "audio/dlg_001_03_female.mp3",
          "duration_sec": 24.144
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "AiDiy の Code AI に GPT-5.5 を割り当てれば、エージェント型開発がすぐに始まります。",
          "naration_text": "AiDiy の Code AI パネルには、CODE_AI1 から CODE_AI6 まで最大 6 つの AI エージェントを割り当てられます。ここに GPT-5.5 を指定することで、エージェント型のコーディング支援をすぐに利用できます。コードの生成だけでなく、バグの発見や修正提案、テストの自動化まで、幅広い開発作業を任せることができます。",
          "audio": "audio/dlg_001_04_male.mp3",
          "duration_sec": 21.72
        }
      ],
      "duration_sec": 95.976
    },
    {
      "id": "scene_002",
      "title": "ナレッジワーク ― GDPval・OSWorld・Tau2-bench",
      "accent": "#7b2d8b",
      "accent_soft": "rgba(123, 45, 139, 0.18)",
      "kicker": "KNOWLEDGE WORK",
      "headline": "ナレッジワークでも\n圧倒的な成績",
      "lead": "GDPval: 84.9%、OSWorld-Verified: 78.7%、Tau2-bench Telecom: 98.0%",
      "source_summary": "GPT-5.5 はナレッジワーク系ベンチマークでも優れた数値を示す。複雑なドキュメント処理（GDPval 84.9%）・PC 操作タスク（OSWorld-Verified 78.7%）・通信業の専門対話（Tau2-bench Telecom 98.0%）。",
      "factual_bullets": [
        "GDPval: 84.9%（複雑なドキュメント処理）",
        "OSWorld-Verified: 78.7%（PC 自律操作タスク）",
        "Tau2-bench Telecom: 98.0%（通信業の専門的な対話タスク）",
        "企業の業務自動化に直結する分野での高い性能"
      ],
      "forbidden_elements": [
        "全ての知識業務を人間なしで完全代替できるという断言"
      ],
      "image_prompt": "A modern office workspace with AI assistant interfaces showing document processing, PC screen automation, and telecom support dashboards. Purple and violet tones. Score overlays: GDPval 84.9%, OSWorld 78.7%, Tau2-bench 98.0%. Professional business atmosphere.",
      "image": "images/scene_002.png",
      "metrics": [
        {
          "label": "GDPval",
          "value": "84.9%"
        },
        {
          "label": "OSWorld-Verified",
          "value": "78.7%"
        },
        {
          "label": "Tau2-bench Telecom",
          "value": "98.0%"
        }
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "ナレッジワーク系でも GPT-5.5 は圧倒的な数値を示しています。",
          "naration_text": "ナレッジワークとは、文書作成・情報整理・意思決定支援など、知識を扱う幅広い業務のことです。GPT-5.5 は、複雑なドキュメント処理を評価する GDPval で 84.9%、PC の自律操作タスクを評価する OSWorld-Verified で 78.7%、通信業の専門的な対話を評価する Tau2-bench Telecom で 98.0% という驚異的なスコアを記録しています。",
          "audio": "audio/dlg_002_01_female.mp3",
          "duration_sec": 28.104
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Tau2-bench Telecom の 98.0% は、ほぼ完璧といえる数値ですね。",
          "naration_text": "Tau2-bench Telecom の 98.0% という数値は、通信業の専門的な顧客対応タスクにおいて、GPT-5.5 がほぼ完璧に近い性能を発揮することを示しています。コールセンターの対応や技術サポートなど、高度な知識と柔軟な対話能力が求められる業務に、AI が実用的に投入できるレベルに達していることを意味しています。",
          "audio": "audio/dlg_002_02_male.mp3",
          "duration_sec": 20.832
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "OSWorld では PC の複雑な操作タスクを、高い精度でこなせます。",
          "naration_text": "OSWorld-Verified は、AI が実際のパソコン画面を見ながら、ファイル操作やアプリの操作など複雑なタスクをこなせるかを評価するベンチマークです。GPT-5.5 は 78.7% を達成しており、人間の補助なしでパソコン作業を自律的に行えるエージェントとして、非常に高い完成度を示しています。",
          "audio": "audio/dlg_002_03_female.mp3",
          "duration_sec": 21.0
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "ナレッジワーク系の高スコアは、企業の業務自動化に直結する可能性を示しています。",
          "naration_text": "ナレッジワーク系ベンチマークの高いスコアは、企業の業務自動化に直接つながる可能性を示しています。報告書の作成・メールの整理・複雑な問い合わせへの対応・社内システムの操作など、日常業務の多くを GPT-5.5 ベースのエージェントに任せる未来が現実味を帯びてきています。AiDiy との組み合わせでも、活用の幅がさらに広がります。",
          "audio": "audio/dlg_002_04_male.mp3",
          "duration_sec": 21.336
        }
      ],
      "duration_sec": 91.272
    },
    {
      "id": "scene_003",
      "title": "科学研究 ― GeneBench・BixBench",
      "accent": "#d65a31",
      "accent_soft": "rgba(214, 90, 49, 0.18)",
      "kicker": "SCIENCE RESEARCH",
      "headline": "科学研究の分野でも\n高いスコアを達成",
      "lead": "GeneBench: 25.0%、BixBench: 80.5% ― 生命科学・生物医学で実力を発揮",
      "source_summary": "GPT-5.5 は科学研究分野でも高い性能を示す。生命科学の高難度タスク GeneBench で 25.0%（難易度が非常に高く現時点トップクラス）、生物医学・化学のデータ解析 BixBench で 80.5%。",
      "factual_bullets": [
        "GeneBench: 25.0%（生命科学の高難度タスク、現時点でトップクラス）",
        "BixBench: 80.5%（生物医学・化学のデータ解析と推論）",
        "論文読解・実験データ解析・仮説整理の支援に活用可能",
        "AiDiy の AIコアから科学研究支援ツールとして利用可能"
      ],
      "forbidden_elements": [
        "GeneBench 25.0% を低い数値と断言する表現（難易度が非常に高いベンチマークのため）"
      ],
      "image_prompt": "A scientific laboratory with DNA helix visualization, molecular data analysis screens, and AI-powered research dashboards. Orange and red tones. Score overlays: GeneBench 25.0%, BixBench 80.5%. Clean, modern science research environment.",
      "image": "images/scene_003.png",
      "metrics": [
        {
          "label": "GeneBench",
          "value": "25.0%"
        },
        {
          "label": "BixBench",
          "value": "80.5%"
        }
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "科学研究の分野でも、GPT-5.5 は注目すべきスコアを記録しました。",
          "naration_text": "GPT-5.5 は科学研究の分野でも高い性能を示しています。生命科学関連のタスクを評価する GeneBench では 25.0%、生物医学・化学のデータ解析を問う BixBench では 80.5% を達成しました。GeneBench の 25.0% は一見低く感じるかもしれませんが、このベンチマーク自体が非常に難易度が高く、現時点では最先端の結果にあたります。",
          "audio": "audio/dlg_003_01_female.mp3",
          "duration_sec": 27.792
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "BixBench の 80.5% は、生物医学の専門タスクで高い実力を示しています。",
          "naration_text": "BixBench は、生物医学や化学の分野における複雑なデータ解析と推論を評価するベンチマークです。GPT-5.5 の 80.5% という数値は、薬の候補探索や遺伝子発現の解析といった、研究者が何日もかけて行うような作業を AI がかなりの精度でこなせることを示しています。研究の加速に貢献できる可能性が非常に高いです。",
          "audio": "audio/dlg_003_02_male.mp3",
          "duration_sec": 22.248
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "論文読解や実験設計の支援など、研究者の強力なパートナーになります。",
          "naration_text": "GPT-5.5 を科学研究に活用すると、大量の論文から関連情報を素早く抽出したり、実験データの統計処理を補助したり、仮説の検証ステップを整理するといった作業を効率化できます。専門家の思考を邪魔せず、時間のかかる調査や整理を任せることで、研究者は本来の創造的な仕事に集中しやすくなります。",
          "audio": "audio/dlg_003_03_female.mp3",
          "duration_sec": 22.464
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "AiDiy の AIコアに組み込めば、研究支援ツールとしても活用できます。",
          "naration_text": "AiDiy の AIコアに GPT-5.5 を組み込むことで、科学研究の支援ツールとしても活用できます。チャット AI として論文の内容を質問したり、Code AI を使って実験データを解析するコードを生成したりと、研究作業のさまざまな場面で力を発揮します。AiDiy の柔軟な設定のおかげで、モデルの切り替えも簡単です。",
          "audio": "audio/dlg_003_04_male.mp3",
          "duration_sec": 21.024
        }
      ],
      "duration_sec": 93.528
    },
    {
      "id": "scene_004",
      "title": "長文コンテキスト・セキュリティ・抽象推論",
      "accent": "#3b5ea6",
      "accent_soft": "rgba(59, 94, 166, 0.18)",
      "kicker": "CONTEXT · SECURITY · REASONING",
      "headline": "1M トークン・CyberGym・ARC-AGI-2\nすべてで高水準",
      "lead": "1M トークン長文対応、CyberGym: 81.8%、ARC-AGI-2: 85.0%",
      "source_summary": "GPT-5.5 は 1M トークンの長文コンテキストに対応し、セキュリティ（CyberGym 81.8%）・抽象推論（ARC-AGI-2 85.0%）でも高い数値を記録。",
      "factual_bullets": [
        "最大 1M トークン（長編小説 10 冊分以上）の長文コンテキスト対応",
        "CyberGym: 81.8%（サイバーセキュリティの高度なタスク）",
        "ARC-AGI-2: 85.0%（抽象的パターン推論）",
        "長大なコードベースや法律文書の一括処理が可能"
      ],
      "forbidden_elements": [
        "ARC-AGI-2 の人間平均スコアを正確に断言する表現（諸説あるため）"
      ],
      "image_prompt": "A split screen showing: left side - a long scroll of text representing 1 million tokens; right side - cybersecurity shield with code and abstract geometric pattern puzzle representing ARC-AGI-2. Blue tones, high-tech futuristic design.",
      "image": "images/scene_004.png",
      "metrics": [
        {
          "label": "長文コンテキスト",
          "value": "1M token"
        },
        {
          "label": "CyberGym",
          "value": "81.8%"
        },
        {
          "label": "ARC-AGI-2",
          "value": "85.0%"
        }
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "1M トークンの長文コンテキスト対応で、膨大な情報を一度に処理できます。",
          "naration_text": "GPT-5.5 は、最大 100万トークンの長文コンテキストに対応しています。これは、長編小説 10 冊分以上のテキストや、数百ページの法律文書、大規模なコードベース全体を一度に入力して処理できることを意味します。これまでの AI が苦手としていた、長い文書の全体を理解した上での推論や要約が、大きく改善されています。",
          "audio": "audio/dlg_004_01_female.mp3",
          "duration_sec": 24.216
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "サイバーセキュリティの CyberGym では 81.8% を達成しています。",
          "naration_text": "CyberGym は、サイバーセキュリティに関する高度な知識とスキルを評価するベンチマークです。脆弱性の発見・攻撃手法の分析・防御策の立案といった専門的なタスクで、GPT-5.5 は 81.8% というスコアを記録しました。セキュリティ担当者の調査作業やインシデント対応の補助として、非常に実用的な性能を示しています。",
          "audio": "audio/dlg_004_02_male.mp3",
          "duration_sec": 22.2
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "ARC-AGI-2 の抽象推論で 85.0% は、非常に高い水準です。",
          "naration_text": "ARC-AGI-2 は、パターンの認識と抽象的な推論を問う非常に難しいベンチマークです。このテストで GPT-5.5 は 85.0% を達成しました。これは抽象推論能力として非常に高い水準であり、複雑な問題解決や創造的な思考が必要な場面でも役立てることが期待されています。",
          "audio": "audio/dlg_004_03_female.mp3",
          "duration_sec": 22.824
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "長文・セキュリティ・推論の組み合わせで、難しい業務課題に対応できます。",
          "naration_text": "長文コンテキスト対応・高いセキュリティ知識・抽象推論能力の組み合わせは、実際の業務で複雑な問題に直面した際に大きな力を発揮します。大量のログデータを読み込みながらセキュリティ上の問題を推論したり、長大な契約書から重要条項を抽出して比較検討したりと、高度な業務課題への対応能力が格段に向上しています。",
          "audio": "audio/dlg_004_04_male.mp3",
          "duration_sec": 21.0
        }
      ],
      "duration_sec": 90.24
    },
    {
      "id": "scene_005",
      "title": "提供プランと API 料金",
      "accent": "#e8a020",
      "accent_soft": "rgba(232, 160, 32, 0.18)",
      "kicker": "PRICING & PLANS",
      "headline": "ChatGPT / Codex で提供開始\nAPI 料金は入力 $5・出力 $30 / 1M トークン",
      "lead": "Plus・Pro・Business・Enterprise の各プランで利用可能。API でも即日アクセスできます。",
      "source_summary": "GPT-5.5 は2026年4月に ChatGPT（Plus/Pro/Business/Enterprise）および Codex で提供開始。API 料金は入力 $5/1M トークン・出力 $30/1M トークン。",
      "factual_bullets": [
        "ChatGPT Plus（月額 $20）で利用可能",
        "ChatGPT Pro（月額 $200）でより多くの枠と優先度",
        "Business・Enterprise は組織向け、管理機能付き",
        "Codex でコーディング特化用途にも提供",
        "API: 入力 $5/1M トークン・出力 $30/1M トークン"
      ],
      "forbidden_elements": [
        "具体的なプラン料金の将来変更を断言する表現"
      ],
      "image_prompt": "A pricing dashboard showing GPT-5.5 plan options: Plus, Pro, Business, Enterprise cards and Codex logo. API cost display: $5 input / $30 output per 1M tokens. Clean financial/SaaS interface design, golden amber tones.",
      "image": "images/scene_005.png",
      "chips": [
        "ChatGPT Plus",
        "ChatGPT Pro",
        "Business",
        "Enterprise",
        "Codex",
        "API"
      ],
      "metrics": [
        {
          "label": "入力トークン",
          "value": "$5 / 1M"
        },
        {
          "label": "出力トークン",
          "value": "$30 / 1M"
        }
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "GPT-5.5 は ChatGPT と Codex で利用でき、API も即日提供されています。",
          "naration_text": "GPT-5.5 は、2026年4月の公開と同時に ChatGPT の各プランと Codex で利用できるようになりました。ChatGPT Plus・Pro・Business・Enterprise のいずれのプランでも使用可能で、コーディング特化ツールの Codex でも提供されています。API は公開と同時にアクセスできるため、自分のアプリへすぐに組み込めます。",
          "audio": "audio/dlg_005_01_female.mp3",
          "duration_sec": 24.6
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "API 料金は入力 $5・出力 $30 で、1M トークン単位の課金です。",
          "naration_text": "API の料金体系は、入力トークンが 100万トークンあたり 5 ドル、出力トークンが同 30 ドルです。高性能なフロンティアモデルでありながら、費用対効果の高い設定になっています。特に入力を多く使う検索補強生成や長文要約のユースケースでは、コストを抑えながら高品質な出力を得られます。",
          "audio": "audio/dlg_005_02_male.mp3",
          "duration_sec": 19.344
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "個人なら Plus、組織なら Business・Enterprise が選択肢になります。",
          "naration_text": "ChatGPT Plus は月額 20 ドルで個人が高度な AI を活用できるプランです。より多くの利用枠と優先度が必要な方には Pro が、組織向けにはセキュリティやプライバシーの要件に対応した管理機能が追加される Business・Enterprise が適しています。用途と規模に合わせて選べる柔軟な体制です。",
          "audio": "audio/dlg_005_03_female.mp3",
          "duration_sec": 20.88
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "コスト管理をしながら、GPT-5.5 の能力を最大限に引き出せます。",
          "naration_text": "GPT-5.5 を API で利用する場合、入力プロンプトの設計次第でコストを大きく削減できます。必要な情報だけを効率よく渡し、出力を適切な長さに制限することで、高い品質を維持しながら費用を抑えられます。AiDiy の AIコアでは、プロンプト管理や履歴の仕組みが整っているため、コスト効率よく運用できます。",
          "audio": "audio/dlg_005_04_male.mp3",
          "duration_sec": 21.504
        }
      ],
      "duration_sec": 86.328
    },
    {
      "id": "scene_006",
      "title": "AiDiy × GPT-5.5 活用シナリオ",
      "accent": "#1f8a70",
      "accent_soft": "rgba(31, 138, 112, 0.18)",
      "kicker": "AIDIY INTEGRATION",
      "headline": "AiDiy の AIコア / Code AI に\ngpt-4.1 / gpt-5.5 を組み込む",
      "lead": "CHAT_AI・LIVE_AI・CODE_AI1〜6 の各設定で gpt-5.5 を指定するだけ。チャット・音声・コード支援に即活用。",
      "source_summary": "AiDiy の AIコア設定（CHAT_AI_NAME・LIVE_AI_NAME・CODE_AI1_NAME〜CODE_AI6_NAME）に gpt-5.5 を指定することで、チャット・音声対話・コーディング支援のすべてに GPT-5.5 を活用できる。gpt-4.1 との使い分けでコスト最適化も可能。",
      "factual_bullets": [
        "CHAT_AI_NAME: テキストチャット AI の設定キー",
        "LIVE_AI_NAME: リアルタイム音声対話の設定キー",
        "CODE_AI1_NAME〜CODE_AI6_NAME: 最大 6 つのコード支援エージェント",
        "gpt-4.1 と gpt-5.5 を用途に応じて使い分け可能",
        "設定画面から値を変えるだけ、コード変更不要"
      ],
      "forbidden_elements": [
        "AiDiy の設定変更に専門的なプログラミングが必要だという誤解を招く表現"
      ],
      "image_prompt": "AiDiy application interface showing AI core settings panel with model selection dropdowns for CHAT_AI, LIVE_AI, and CODE_AI1-6 fields. 'gpt-5.5' highlighted in teal green. Modern dashboard UI with avatar panel visible. Clean, professional Japanese software design.",
      "image": "images/scene_006.png",
      "chips": [
        "CHAT_AI_NAME",
        "LIVE_AI_NAME",
        "CODE_AI1〜6",
        "gpt-4.1",
        "gpt-5.5"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AiDiy の AIコア設定で gpt-5.5 を指定するだけで、すぐに使い始められます。",
          "naration_text": "AiDiy の AIコアは、CHAT_AI_NAME・LIVE_AI_NAME・CODE_AI1_NAME から CODE_AI6_NAME までの設定で、使用する AI モデルを切り替えられます。GPT-5.5 を使いたい場合は、これらの設定値に gpt-5.5 と入力するだけです。OpenAI の API キーがあれば、設定変更だけでその恩恵をすぐに受けられます。",
          "audio": "audio/dlg_006_01_female.mp3",
          "duration_sec": 30.168
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Code AI パネルに GPT-5.5 を割り当てれば、高度なコーディング支援が始まります。",
          "naration_text": "AiDiy の Code AI パネルは、最大 6 つの AI エージェントを同時に動かせる設計になっています。CODE_AI1 から CODE_AI6 に gpt-5.5 を割り当てると、エージェント型コーディング支援として活用できます。コードの生成・レビュー・デバッグ・テスト作成を、エージェントが自律的にサポートしてくれます。",
          "audio": "audio/dlg_006_02_male.mp3",
          "duration_sec": 19.8
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "チャット AI や音声 AI にも GPT-5.5 を組み込んで、対話体験を向上できます。",
          "naration_text": "CHAT_AI_NAME に gpt-5.5 を設定すると、テキストチャットで GPT-5.5 の高い理解力と生成能力を活用できます。LIVE_AI_NAME に設定すれば、リアルタイム音声対話にも使えます。日常の質問対応から技術的な相談まで、幅広い場面でより高品質な回答が得られるようになります。",
          "audio": "audio/dlg_006_03_female.mp3",
          "duration_sec": 24.12
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "gpt-4.1 と gpt-5.5 を用途に応じて使い分けるのが、賢い活用法です。",
          "naration_text": "コスト効率を意識するなら、gpt-4.1 と gpt-5.5 を用途に応じて使い分けるのがおすすめです。日常的な質問への回答や単純なコード補完には gpt-4.1 を使い、複雑な推論や高精度な判断が必要な場面では gpt-5.5 を使うという組み合わせが効果的です。AiDiy の設定画面から、パネルごとに異なるモデルを割り当てられます。",
          "audio": "audio/dlg_006_04_male.mp3",
          "duration_sec": 23.976
        }
      ],
      "duration_sec": 98.064
    },
    {
      "id": "scene_999",
      "title": "まとめ ― GPT-5.5 と AiDiy で広がる開発の可能性",
      "accent": "#10a37f",
      "accent_soft": "rgba(16, 163, 127, 0.18)",
      "layout": "hero",
      "kicker": "SUMMARY",
      "headline": "GPT-5.5 と AiDiy で\n開発の可能性を広げよう",
      "lead": "速度と精度を両立したフロンティアモデル GPT-5.5 と、日本語ファーストの開発環境 AiDiy を組み合わせた新しい開発体験。",
      "source_summary": "GPT-5.5 は速度と精度を両立した新世代フロンティアモデル。AiDiy の AIコア・Code AI に組み込むことで、チャット・音声・コーディング支援のすべてで活用できる。この動画は AiDiy の video_generation 機能で自動生成された。",
      "factual_bullets": [
        "エージェント型コーディング・ナレッジワーク・科学研究・長文・セキュリティ・推論の全分野でフロンティア性能",
        "AiDiy の設定変更だけで GPT-5.5 を即活用可能",
        "gpt-4.1 との使い分けでコスト最適化も可能",
        "この動画は AiDiy の video_generation 機能で自動生成"
      ],
      "forbidden_elements": [
        "根拠なく GPT-5.5 が全ての作業を完全に代替できると断言する表現"
      ],
      "image_prompt": "A vibrant summary screen showing GPT-5.5 and AiDiy logos together with benchmark highlights: Terminal-Bench 82.7%, Tau2-bench 98.0%, ARC-AGI-2 85.0%. Teal green tones with celebratory, forward-looking atmosphere. Clean professional design.",
      "image": "images/scene_999.png",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "GPT-5.5 は速度と精度を両立した、新しいフロンティアモデルです。",
          "naration_text": "今回解説した GPT-5.5 は、GPT-5.4 と同等の応答速度を保ちながら、エージェント型コーディング・ナレッジワーク・科学研究・長文処理・セキュリティ・抽象推論のすべてでフロンティア性能を達成した、非常に完成度の高いモデルです。速さと賢さを両立させた、新しい世代の AI モデルといえます。",
          "audio": "audio/dlg_999_01_female.mp3",
          "duration_sec": 23.016
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "ベンチマーク数値が示す通り、多様な実務場面で活躍できます。",
          "naration_text": "Terminal-Bench 2.0 の 82.7%・Tau2-bench Telecom の 98.0%・ARC-AGI-2 の 85.0% など、これほど多様な分野でトップクラスのスコアを記録するモデルはこれまでありませんでした。コーディングから研究、ビジネス業務まで、幅広い実務場面での活躍が期待できます。",
          "audio": "audio/dlg_999_02_male.mp3",
          "duration_sec": 18.024
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AiDiy との組み合わせで、開発体験がさらに豊かになります。",
          "naration_text": "AiDiy の AIコアや Code AI に GPT-5.5 を組み込むことで、日常の開発・業務自動化が一段と進みます。設定画面からモデルを切り替えるだけで高性能な AI の恩恵を受けられる AiDiy は、GPT-5.5 のような最新モデルをいち早く活用するための最適な基盤です。gpt-4.1 との使い分けで、コストも賢くコントロールできます。",
          "audio": "audio/dlg_999_03_female.mp3",
          "duration_sec": 25.248
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "AiDiy は、誰でも最新 AI をすぐに試せる、日本語ファーストの開発環境です。",
          "naration_text": "AiDiy は、AI エージェント・MCP・音声・画像・動画生成ツールを統合した、日本語ファーストの開発環境です。業務システムのテンプレートをベースに、最新の AI モデルをすぐに試せる柔軟な設計になっています。GPT-5.5 のような新モデルが登場するたびに、AiDiy を通じてすぐに活用できる環境が整っています。",
          "audio": "audio/dlg_999_04_male.mp3",
          "duration_sec": 20.976
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AiDiy で自動生成！チャンネル登録して、あなたも AI 開発を始めてみましょう。",
          "naration_text": "この動画は AiDiy の video_generation 機能で自動生成されました。AiDiy を使えば、皆さんもこんな動画を自分で作ることができます。チャンネル登録をしていただくと、今後も AiDiy の活用事例や最新の AI トレンドをお届けします。ぜひ一緒に、AI 開発の新しい可能性を楽しんでいきましょう！あなたも試してみてください。きっと『自分でもできる！』と思えるはずです！",
          "audio": "audio/dlg_999_05_female.mp3",
          "duration_sec": 27.192
        }
      ],
      "duration_sec": 114.456
    }
  ],
  "total_duration_sec": 769.296
};
