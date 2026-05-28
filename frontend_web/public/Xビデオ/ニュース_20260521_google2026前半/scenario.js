window.SCENARIO = {
  "project_name": "Google 2026年ニュース解説 (掛け合い版)",
  "version": "duo-v2",
  "title": "Google 2026年 主要ニュース",
  "assets_policy": {
    "male_avatar": "../vrm/VRM_male.vrm",
    "female_avatar": "../vrm/VRM_female.vrm",
    "tts_male": "edge:male",
    "tts_female": "edge:female",
    "audio_output_dir": "frontend_web/public/Xビデオ/ニュース_20260521_google2026前半/audio"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "Google 2026年ニュース",
      "accent": "#4285F4",
      "accent_soft": "rgba(66, 133, 244, 0.18)",
      "layout": "hero",
      "kicker": "2026 NEWS REVIEW",
      "headline": "Google 2026年前半\n主要ニュース解説",
      "image": "images/scene_000.png",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "皆さん、こんにちは！今日は2026年前半のGoogleの主要ニュースを振り返ります。このニュース解説動画はAiDiyで作られています。",
          "naration_text": "こんにちは！本日は2026年前半、1月から5月にかけてGoogleが世界に打ち出した主要ニュースを一気に振り返ります！毎月重要な発表が続いた怒涛の半年でしたよ。Gemini 3シリーズの大型アップデートから始まって、音楽生成・ロボティクス・科学的発見、そして5月のGoogle I/O 2026まで、業界を驚かせる発表が相次ぎました。なお、この動画はAiDiyを使って作られています。",
          "audio": "audio/dlg_000_01_female.mp3",
          "duration_sec": 29.952
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "2026年前半のGoogleは本当に盛りだくさんでしたね！Geminiモデルの急速な進化、音楽生成、ロボティクス、そしてGoogle I/O 2026まで、驚きの連続でした。",
          "naration_text": "2026年前半のGoogleは本当に盛りだくさんでした。Gemini 3シリーズの大型アップデート群に始まり、Lyria 3による音楽生成の革新、Gemma 4オープンモデルの登場、Gemini Roboticsによるロボティクス応用、AlphaEvolveによる科学的発見の加速、そして5月のGoogle I/O 2026でのGemini 3.5・Gemini Omni・Google Antigravity 2.0の発表まで、毎月重要な発表が矢継ぎ早に続きました。",
          "audio": "audio/dlg_000_02_male.mp3",
          "duration_sec": 24.408
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "特に際立つのは、モデルの進化だけでなく、科学・医療・ロボットなど幅広い分野へのAI応用が本格化していることですね。",
          "naration_text": "特に際立つのは、モデルの性能向上だけでなく、科学研究・医療・ロボティクス・気象予測・量子コンピューティングなど、幅広い実世界の問題へのAI応用が本格化していることです。GoogleのAI戦略は「強力なモデルを作る」だけにとどまらず、「世界の情報を整理し、普遍的にアクセス可能にする」という創業以来のミッションを着実にAIで実現しようとしています。",
          "audio": "audio/dlg_000_03_female.mp3",
          "duration_sec": 26.448
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Google I/O 2026ではサンダー・ピチャイCEOをはじめ、DeepMindのデミス・ハサビスCEOも登壇し、AIと科学の未来を語りました。",
          "naration_text": "Google I/O 2026では、サンダー・ピチャイCEOをはじめ、Google DeepMindのデミス・ハサビスCEOが科学とAIの新時代について語り、チーフサイエンティストのジェフ・ディーンがエージェントAI時代の定義を議論しました。量子コンピューティングとAIの融合についてはハルトムート・ネーベン氏が解説するなど、Google全体の知見が結集した内容でした。それでは各ニュースを詳しく見ていきましょう！",
          "audio": "audio/dlg_000_04_male.mp3",
          "duration_sec": 23.016
        }
      ],
      "duration_sec": 103.824
    },
    {
      "id": "scene_001",
      "title": "Gemini 3 モデル群 / 1月〜2月",
      "accent": "#EA4335",
      "accent_soft": "rgba(234, 67, 53, 0.18)",
      "kicker": "JANUARY - FEBRUARY 2026",
      "headline": "Gemini 3 モデル群\nVeo 3.1 & Nano Banana 2",
      "image": "images/scene_001.png",
      "chips": [
        "Veo 3.1",
        "Project Genie",
        "Nano Banana 2",
        "Gemini 3.1 Pro",
        "Gemini 3 Deep Think"
      ],
      "metrics": [
        {
          "label": "新モデル数",
          "value": "4+"
        },
        {
          "label": "Veo 3.1",
          "value": "動画生成"
        },
        {
          "label": "Deep Think",
          "value": "科学・研究"
        }
      ],
      "cards": [
        {
          "title": "Veo 3.1 Ingredients to Video",
          "lines": [
            "より一貫性・創造性・制御性が向上",
            "素材から映像を高精度に生成",
            "クリエイター向け機能を強化"
          ]
        },
        {
          "title": "Nano Banana 2",
          "lines": [
            "Proクラスの能力と高速性を両立",
            "画像生成AIの新たな基準",
            "テキストから即座に高品質画像"
          ]
        },
        {
          "title": "Gemini 3.1 Pro / Deep Think",
          "lines": [
            "複雑タスク向けの主力モデル",
            "科学・研究・エンジニアリングに特化",
            "高度な数学的・論理的推論"
          ]
        }
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "2026年1月最初の注目ニュースはVeo 3.1です。「Ingredients to Video」として、より一貫性・創造性・制御性が向上しました！",
          "naration_text": "2026年1月最初の注目ニュースは、GoogleのAI動画生成モデル「Veo 3.1」の大幅アップデートです。「Ingredients to Video」というコンセプトのもと、素材画像やテキストから映像を生成する際の一貫性、創造性、そして制御性が大きく向上しました。映像内のオブジェクトの見た目や動作がより自然になり、クリエイターが意図した映像をより正確に生成できるようになっています。",
          "audio": "audio/dlg_001_01_female.mp3",
          "duration_sec": 27.6
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "同じく1月にはProject Genieも発表されました。AIが無限のインタラクティブ世界を生成するという、まったく新しい概念の実験プロジェクトです。",
          "naration_text": "同じく1月には「Project Genie」も発表されました。AIが無限のインタラクティブな世界をリアルタイムで生成するという、これまでにない概念の実験プロジェクトです。静止画や動画からプレイ可能なゲーム世界を自動生成する能力を持ち、ゲーム業界や教育分野への応用が期待されています。5月のGoogle I/Oでは、Street Viewとの連携によりリアルな場所をシミュレートする機能にも拡張されました。",
          "audio": "audio/dlg_001_02_male.mp3",
          "duration_sec": 24.36
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "2月にはNano Banana 2が登場！Proクラスの能力と超高速処理を両立した画像生成AIです。",
          "naration_text": "2月には「Nano Banana 2」が発表されました。前世代と比較してProモデルクラスの高品質を保ちながら、超高速処理を実現した画像生成AIです。テキストプロンプトから瞬時に高品質な画像を生成でき、Geminiアプリから直接利用可能です。細部の描写精度が大幅に向上し、写実的な表現からイラスト調まで幅広いスタイルに対応しています。",
          "audio": "audio/dlg_001_03_female.mp3",
          "duration_sec": 25.536
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "そしてGemini 3.1 ProとGemini 3 Deep Thinkも2月に登場。複雑なタスクと科学・研究分野に特化した強力なモデルです。",
          "naration_text": "2月にはGemini 3.1 ProとGemini 3 Deep Thinkも発表されました。Gemini 3.1 Proは複雑なタスクと独創的なコンセプトを実現するためのスマートなモデルとして位置づけられています。一方のGemini 3 Deep Thinkは、科学・研究・エンジニアリング分野における高度な課題に特化したモデルで、数学的推論や多段階の問題解決において特に優れた性能を発揮しています。",
          "audio": "audio/dlg_001_04_male.mp3",
          "duration_sec": 22.752
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "1月〜2月でモデルラッシュが続いたGoogleですが、これはまだまだ序章に過ぎませんでした！この後も毎月重要な発表が続きます。",
          "naration_text": "1月〜2月にかけてのモデルラッシュは、2026年のGoogleのペースを象徴するものでした。Veoによる動画生成、Project Genieによるインタラクティブ世界生成、Nano Bananaによる高速画像生成、そしてGeminiモデルの性能向上と、わずか2ヶ月でAIの各分野を網羅する発表が相次ぎました。そしてこれはまだ序章に過ぎず、この後も毎月重要な発表が続くことになります。",
          "audio": "audio/dlg_001_05_female.mp3",
          "duration_sec": 26.712
        }
      ],
      "duration_sec": 126.96
    },
    {
      "id": "scene_002",
      "title": "音楽生成・Flash-Lite / 2月〜3月",
      "accent": "#FBBC04",
      "accent_soft": "rgba(251, 188, 4, 0.18)",
      "kicker": "FEBRUARY - MARCH 2026",
      "headline": "Lyria 3 音楽生成\nGemini 3.1 Flash-Lite も登場",
      "image": "images/scene_002.png",
      "chips": [
        "Lyria 3",
        "Lyria 3 Pro",
        "Gemini 3.1 Flash-Lite",
        "AGIフレームワーク",
        "AlphaGo 10周年"
      ],
      "metrics": [
        {
          "label": "Lyria 3",
          "value": "音楽生成"
        },
        {
          "label": "Flash-Lite",
          "value": "大量処理"
        },
        {
          "label": "AlphaGo",
          "value": "10周年"
        }
      ],
      "cards": [
        {
          "title": "Lyria 3 (Gemini 音楽生成)",
          "lines": [
            "Geminiアプリから音楽を直接生成",
            "テキストプロンプトでオリジナル楽曲",
            "多様なジャンル・スタイルに対応"
          ]
        },
        {
          "title": "Lyria 3 Pro",
          "lines": [
            "より長尺のトラック生成に対応",
            "高品質な楽曲制作を支援",
            "クリエイター向けプロ機能"
          ]
        },
        {
          "title": "Gemini 3.1 Flash-Lite",
          "lines": [
            "大量処理に最適化した軽量モデル",
            "高効率・高インテリジェンスを両立",
            "スケールするAIシステム向け"
          ]
        }
      ],
      "dialogue": [
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "2月のビッグニュースは、GeminiアプリでAIが音楽を生成できるようになったことです！Lyria 3の登場で、テキストから音楽が作れるようになりました。",
          "naration_text": "2月のビッグニュースは、GeminiアプリでAIが音楽を生成できるようになったことです。Googleの音楽生成AI「Lyria 3」がGeminiアプリに統合され、テキストプロンプトを入力するだけでオリジナルの楽曲が生成できるようになりました。ジャズ、クラシック、ポップ、エレクトロニックなど多様なジャンルに対応しており、プロのミュージシャンからアマチュアのクリエイターまで幅広く活用できる機能です。",
          "audio": "audio/dlg_002_01_male.mp3",
          "duration_sec": 23.448
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "3月にはLyria 3 Proも登場。より長尺のトラック生成に対応し、本格的な楽曲制作にも使えるレベルになりました！",
          "naration_text": "3月にはさらに進化した「Lyria 3 Pro」も発表されました。従来版が短いトラックの生成に特化していたのに対し、Lyria 3 Proはより長尺の楽曲生成に対応し、イントロ・サビ・アウトロを含む構成のある音楽を作成できるようになっています。BGM制作、ポッドキャストのオープニング、動画コンテンツのサウンドトラックなど、実際のクリエイター業務での活用が本格化しています。",
          "audio": "audio/dlg_002_02_female.mp3",
          "duration_sec": 26.832
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "3月にはGemini 3.1 Flash-Liteも発表。大量処理に特化した高効率モデルで、スケールするAIシステムの構築が可能になりました。",
          "naration_text": "3月には「Gemini 3.1 Flash-Lite」も発表されました。高効率かつ高インテリジェンスを両立させた、大量処理向けに最適化された軽量モデルです。コスト効率よく大量のリクエストを処理する必要がある企業向けシステムや、AIを組み込んだWebサービスの構築に最適です。Geminiエコシステムの中でFlash-Liteは、エントリーレベルの用途から高スループットのビジネスアプリケーションまでカバーする重要な位置を占めています。",
          "audio": "audio/dlg_002_03_male.mp3",
          "duration_sec": 25.68
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "また3月にはAGI進捗測定の認知フレームワークも発表されました。AIの知的能力をどう測るかという根本的な問いへの挑戦です。",
          "naration_text": "また3月にはGoogleが「AGI進捗を測定するための認知フレームワーク」を発表しました。AIの知的能力をどのように測定・評価するかという根本的な問いへの挑戦で、単純なベンチマークスコアを超えた包括的な評価基準を提唱しています。知覚・記憶・学習・推論・実行という認知機能の各軸でAIの能力を可視化するアプローチは、AI研究の方向性を定める重要な貢献として学術界でも注目を集めています。",
          "audio": "audio/dlg_002_04_female.mp3",
          "duration_sec": 31.656
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "3月はAlphaGoの論文発表から10周年。AIが囲碁世界チャンピオンに勝った歴史的な瞬間から10年、AI技術は想像を超える速さで進化しています。",
          "naration_text": "また3月には、AIが初めて囲碁の世界チャンピオンを破ったAlphaGoの論文発表から10周年を記念する振り返りが発表されました。2016年に世界を驚かせたその瞬間から、深層強化学習はAlphaFold・AlphaEvolveへと進化し、科学的発見のエンジンへと変貌しています。10年間でAI技術が想像をはるかに超える速さで進化してきたことを改めて実感させる、感慨深い記念日となりました。",
          "audio": "audio/dlg_002_05_male.mp3",
          "duration_sec": 24.864
        }
      ],
      "duration_sec": 132.48
    },
    {
      "id": "scene_003",
      "title": "Gemma 4 & Gemini Robotics / 4月",
      "accent": "#34A853",
      "accent_soft": "rgba(52, 168, 83, 0.18)",
      "kicker": "APRIL 2026",
      "headline": "Gemma 4 & Gemini Robotics\nオープンモデルとロボット応用",
      "image": "images/scene_003.png",
      "chips": [
        "Gemma 4",
        "Gemini Robotics-ER 1.6",
        "Gemini 3.1 Flash TTS",
        "Gemini 3.1 Flash Live",
        "AI Co-Clinician"
      ],
      "metrics": [
        {
          "label": "Gemma 4",
          "value": "最高OSSモデル"
        },
        {
          "label": "Robotics",
          "value": "ER 1.6"
        },
        {
          "label": "医療AI",
          "value": "Co-Clinician"
        }
      ],
      "cards": [
        {
          "title": "Gemma 4",
          "lines": [
            "バイト単位で最高性能のオープンモデル",
            "クラウド・デスクトップ・モバイル対応",
            "商用・研究に広く利用可能"
          ]
        },
        {
          "title": "Gemini Robotics-ER 1.6",
          "lines": [
            "強化された身体的推論能力",
            "実世界のロボット作業を実行",
            "製造・物流・医療での応用"
          ]
        },
        {
          "title": "AI Co-Clinician",
          "lines": [
            "医師を支援するAI共同研究者",
            "診断支援・文献検索を高速化",
            "医療の新モデルを実現"
          ]
        }
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "4月の最大の注目はGemma 4の登場です！バイト単位で最高性能を誇るオープンモデルが登場し、AI民主化が大きく前進しました。",
          "naration_text": "4月の最大の注目は「Gemma 4」の登場です。キャッチコピーは「バイト単位で最高性能のオープンモデル」。Googleが提供するオープンウェイトモデルファミリーの最新版で、同等サイズの他のオープンモデルと比較して圧倒的な性能を発揮します。クラウド・デスクトップ・モバイルと幅広い環境で動作し、商用・研究利用ともに制限が少なく、世界中の開発者がAIアプリケーションを構築しやすい環境を提供しています。",
          "audio": "audio/dlg_003_01_female.mp3",
          "duration_sec": 30.336
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Gemini Robotics-ER 1.6も4月に登場。強化された身体的推論能力により、実世界のロボット作業をより確実にこなせるようになりました。",
          "naration_text": "4月にはGemini Roboticsシリーズの最新版「Gemini Robotics-ER 1.6」も発表されました。ERはEnhanced Embodied Reasoning（強化された身体的推論）の略で、ロボットが物理的な環境を理解し、複雑な作業を計画・実行する能力が大幅に向上しています。製造ラインでの組み立て作業、物流倉庫でのピッキング、そして医療現場での補助など、実際の産業応用を見据えた性能強化が進んでいます。",
          "audio": "audio/dlg_003_02_male.mp3",
          "duration_sec": 26.496
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "4月にはGemini 3.1 Flash TTSとGemini 3.1 Flash Liveも登場。次世代の表現力豊かなAI音声と、よりリアルな音声AIが実現しました。",
          "naration_text": "4月にはGemini 3.1 Flash TTSと、少し前の3月には Gemini 3.1 Flash Liveも発表されました。Gemini 3.1 Flash TTSは「次世代の表現力豊かなAI音声合成」として、感情・抑揚・ペースを自然に調整できる音声を生成します。一方のGemini 3.1 Flash Liveは、リアルタイム音声AIをより自然で信頼性の高いものにする技術で、音声対話AIアシスタントの品質が格段に向上しています。",
          "audio": "audio/dlg_003_03_female.mp3",
          "duration_sec": 31.2
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "医療分野でも画期的な発表がありました。AI Co-Clinicianは、医師と連携して診断支援や研究加速を行う、医療AIの新たなモデルです。",
          "naration_text": "医療分野では「AI Co-Clinician（AI共同臨床医）」という画期的な概念が発表されました。これは医師に代わるのではなく、医師と並走してリアルタイムで診断を支援するAIです。方針の提案、文献の高速検索、鑑別診断の提示などを行うことで、医師がより質の高い医療を提供するための意思決定を強力にサポートします。AIと人間の専門家が協働する医療の新しいモデルとして、医療業界から大きな注目を集めています。",
          "audio": "audio/dlg_003_04_male.mp3",
          "duration_sec": 28.56
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "4月にはGemini Roboticsがさらに韓国・シンガポールなど各国政府とのAIパートナーシップも締結。Googleの戦略的な国際展開も加速しています。",
          "naration_text": "また4月には韓国政府とのAIパートナーシップも締結されました。また翌5月にはシンガポールとのAI国家パートナーシップも発表されています。各国政府との連携を通じてAI技術の責任ある展開を推進するこの取り組みは、GoogleがAI安全性・規制・社会実装の各面で国際社会と積極的に協働しようとする姿勢を示しています。AI大国をリードするGoogleの戦略的な国際展開が加速しています。",
          "audio": "audio/dlg_003_05_female.mp3",
          "duration_sec": 29.712
        }
      ],
      "duration_sec": 146.304
    },
    {
      "id": "scene_004",
      "title": "AlphaEvolve & AI Pointer / 5月初旬",
      "accent": "#4285F4",
      "accent_soft": "rgba(66, 133, 244, 0.18)",
      "kicker": "MAY 2026 PRE-I/O",
      "headline": "AlphaEvolve & AI Pointer\nI/O前夜の革新発表",
      "image": "images/scene_004.png",
      "chips": [
        "AlphaEvolve",
        "TPU設計最適化",
        "数学的発見",
        "AI Pointer",
        "Googlebook"
      ],
      "metrics": [
        {
          "label": "物流効率",
          "value": "+10.4%"
        },
        {
          "label": "量子回路",
          "value": "誤り10分の1"
        },
        {
          "label": "AI Pointer",
          "value": "Chrome対応"
        }
      ],
      "cards": [
        {
          "title": "AlphaEvolve 成果",
          "lines": [
            "次世代TPUの回路設計を最適化",
            "Spanner Write Amplificationを20%削減",
            "FM Logisticで1.5万km/年の削減"
          ]
        },
        {
          "title": "科学・数学での発見",
          "lines": [
            "テレンス・タオと共同でエルデシュ問題を解決",
            "量子回路誤り10分の1に削減",
            "DNA塩基配列エラーを30%削減"
          ]
        },
        {
          "title": "AI Pointer",
          "lines": [
            "指差しだけでAIに意図を伝える",
            "Chromeでウェブページの任意部分を指示",
            "Googlebook Magicポインター搭載"
          ]
        }
      ],
      "dialogue": [
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "5月7日にAlphaEvolveの成果報告が発表されました。Gemini搭載のコーディングエージェントが科学・産業・インフラ全域で驚異的な成果を出しています！",
          "naration_text": "5月7日、AlphaEvolveの広範な成果報告が発表されました。AlphaEvolveはGeminiを搭載したコーディングエージェントで、アルゴリズムを自律的に進化させることで各種問題を最適化します。最も注目すべきは次世代TPUの回路設計に応用されたことで、ジェフ・ディーンがいう「TPUの脳がTPUの本体を設計する」という画期的な取り組みです。Google Spannerのストレージ書き込み増幅率を20%削減するなど、Googleの基幹インフラの改善にも直接貢献しています。",
          "audio": "audio/dlg_004_01_male.mp3",
          "duration_sec": 29.832
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "産業界への応用も目覚ましく、Klarnaではトレーニング速度が2倍に、物流会社FM Logisticでは年間1.5万km以上の走行距離削減を達成しました！",
          "naration_text": "産業界への応用も目覚ましい成果を上げています。決済大手Klarnaはトランスフォーマーモデルの最適化にAlphaEvolveを活用し、学習速度を2倍に向上させました。物流会社FM Logisticは複雑なルーティング問題に適用し、年間15,000キロメートル以上の走行距離削減を実現しています。また半導体メーカーのSubstrateは計算リソグラフィの高速化に成功し、広告大手WPPはAIモデルの精度を10%向上させました。",
          "audio": "audio/dlg_004_02_female.mp3",
          "duration_sec": 31.848
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "科学分野でも驚きの成果。数学者テレンス・タオと共同でエルデシュ問題を解決し、量子コンピュータの回路誤りを10分の1に削減しました。",
          "naration_text": "科学分野でも驚きの成果が続いています。フィールズ賞受賞の数学者テレンス・タオと共同でエルデシュ問題を解決し、旅行セールスマン問題の下界改善など古典的な数学的課題でも新記録を達成しました。量子コンピューティングの分野では、GoogleのWillowプロセッサで動作する量子回路の誤りを従来比10分の1に削減することに成功。さらにゲノム研究では、DNA塩基配列のエラー検出精度を30%向上させています。",
          "audio": "audio/dlg_004_03_male.mp3",
          "duration_sec": 27.192
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "5月12日にはAIポインターが発表されました。マウスポインターを半世紀ぶりに進化させる、Gemini搭載の革命的なUI技術です！",
          "naration_text": "5月12日には「AI Pointer」が発表されました。マウスポインターは半世紀以上ほぼ変わっていませんでしたが、GeminiのAI能力と組み合わせることで革命的に進化します。「指差して話す」だけで複雑な意図をAIに伝えられる4つの原則を提唱：「フローを維持する」「見せて話す」「これ・あれの力を活かす」「ピクセルを実体に変える」。既にChromeでウェブページの任意部分を指してGeminiに質問できる機能が提供開始されています。",
          "audio": "audio/dlg_004_04_female.mp3",
          "duration_sec": 30.528
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "またGooglebookという新しいGoogle製ノートPCが発表され、AI PointerのMagicPointer機能が搭載されます。AIと人間の新しい協働形態が始まります！",
          "naration_text": "AI Pointerは、Googleが発表した新ラップトップ「Googlebook」にも「Magic Pointer」として搭載される予定です。Googlebookは画面のどこでも指差すだけでGeminiのAI能力を呼び出せる直感的な体験を提供します。またGoogle AI Studioでも実験的なAIポインターのデモが公開され、画像編集や地図での場所検索を指差しと音声で操作する未来のUIが体験できるようになっています。",
          "audio": "audio/dlg_004_05_male.mp3",
          "duration_sec": 24.336
        }
      ],
      "duration_sec": 143.736
    },
    {
      "id": "scene_005",
      "title": "Google I/O 2026 - Gemini 3.5 & Gemini Omni",
      "accent": "#EA4335",
      "accent_soft": "rgba(234, 67, 53, 0.18)",
      "kicker": "MAY 2026 GOOGLE I/O",
      "headline": "Google I/O 2026\nGemini 3.5 & Gemini Omni",
      "image": "images/scene_005.png",
      "chips": [
        "Gemini 3.5 Flash",
        "Gemini 3.5 Pro",
        "Gemini Omni",
        "Co-Scientist",
        "Gemini for Science"
      ],
      "metrics": [
        {
          "label": "SWE-Bench Pro",
          "value": "55.1%"
        },
        {
          "label": "ARC-AGI-2",
          "value": "72.1%"
        },
        {
          "label": "Terminal-bench",
          "value": "76.2%"
        }
      ],
      "cards": [
        {
          "title": "Gemini 3.5 Flash",
          "lines": [
            "エージェントとコーディングの最前線",
            "SWE-Bench Pro 55.1%を達成",
            "マルチモーダル・長文コンテキスト対応"
          ]
        },
        {
          "title": "Gemini Omni",
          "lines": [
            "自然な会話で動画を段階的に編集",
            "物理法則を理解したリアルな映像",
            "SynthID透かし・C2PAによる安全設計"
          ]
        },
        {
          "title": "Co-Scientist",
          "lines": [
            "マルチエージェントAI研究パートナー",
            "研究仮説の生成・文献検索を自動化",
            "ALS・肝疾患・感染症研究に貢献"
          ]
        }
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "いよいよGoogle I/O 2026！5月19〜20日に開催され、サンダー・ピチャイCEO、デミス・ハサビス、ジェフ・ディーンらが登壇しました。",
          "naration_text": "いよいよ2026年最大のイベント、Google I/O 2026の発表内容を見ていきましょう。5月19日から20日にかけて開催されたこのイベントでは、サンダー・ピチャイCEO、Google DeepMindのデミス・ハサビスCEO、チーフサイエンティストのジェフ・ディーン、Google検索トップのリズ・リードらが登壇しました。AIの未来を定義する数多くの発表が相次ぎ、AI業界全体に大きな波紋を呼びました。",
          "audio": "audio/dlg_005_01_female.mp3",
          "duration_sec": 29.04
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "最大の目玉はGemini 3.5の発表です！SWE-Bench Pro 55.1%、Terminal-bench 76.2%、ARC-AGI-2 72.1%と各ベンチマークでトップクラスの成績を記録！",
          "naration_text": "I/O最大の目玉は「Gemini 3.5」の発表です。「フロンティアインテリジェンスとアクション」をキャッチフレーズに、エージェントワークフローの最前線を走るモデルとして登場しました。エージェントコーディングベンチマークのSWE-Bench Proで55.1%、端末操作のTerminal-bench 2.1で76.2%を達成。さらに高度な抽象推論テストのARC-AGI-2でも72.1%と驚異的なスコアを記録し、競合他社を上回る場面も多く見られました。",
          "audio": "audio/dlg_005_02_male.mp3",
          "duration_sec": 28.416
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Gemini 3.5は3.5 Flash（公開中）と3.5 Pro（間もなく）の2本立て。エージェントコーディング・マルチモーダル・長文コンテキストで群を抜く性能です！",
          "naration_text": "Gemini 3.5シリーズは「3.5 Flash」（現在提供中）と「3.5 Pro」（間もなく提供予定）の2本立てとなっています。Gemini 3.5 Flashはエージェントコーディング・高度なマルチモーダル理解・長期タスク実行・マルチステップ問題解決において群を抜く性能を発揮します。特にMCP Atlas（マルチステップワークフロー）で83.6%、OSWorld-Verified（PC操作）で78.4%というスコアは実用的なエージェントAIの実現を証明しています。",
          "audio": "audio/dlg_005_03_female.mp3",
          "duration_sec": 33.912
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "もう一つの大注目がGemini Omniです！動画編集を自然な会話で段階的に行える革新的なAIで、物理法則も理解した映像生成が可能です。",
          "naration_text": "I/Oのもう一つの大注目は「Gemini Omni」です。動画編集や生成を自然な会話で段階的に行える革新的なAIで、「Nano Bananaの動画版」と表現されています。「ヴァイオリン奏者を別の場所に移して」「カメラ角度を変えて」「ヴァイオリンを消して」といった自然言語での指示に従い、一貫性を保ちながら動画を段階的に編集できます。物理法則・世界史・科学知識を理解したリアルな映像生成が可能で、SynthID透かしによる安全設計も施されています。",
          "audio": "audio/dlg_005_04_male.mp3",
          "duration_sec": 29.856
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Co-Scientistも発表されました。マルチエージェントAIが研究者の相棒として機能し、ALS・肝疾患・感染症などの難病研究に貢献しています。",
          "naration_text": "「Co-Scientist」も重要な発表です。複数のAIエージェントが協力して科学研究を加速するマルチエージェントシステムで、研究者の真の相棒として機能します。ALS（筋萎縮性側索硬化症）・肝線維症・感染症などの難病研究において、仮説の生成・文献の高速検索・実験計画の立案を支援します。また「Gemini for Science」として、タンパク質設計・気候変動・数学的発見など科学全域でのAI活用を加速するツールと実験環境も提供開始されました。",
          "audio": "audio/dlg_005_05_female.mp3",
          "duration_sec": 37.416
        }
      ],
      "duration_sec": 158.64
    },
    {
      "id": "scene_006",
      "title": "Google I/O 2026 - Antigravity & 量子AI",
      "accent": "#FBBC04",
      "accent_soft": "rgba(251, 188, 4, 0.18)",
      "kicker": "MAY 2026 GOOGLE I/O",
      "headline": "Google Antigravity 2.0\nエージェント時代の到来",
      "image": "images/scene_006.png",
      "chips": [
        "Google Antigravity 2.0",
        "エージェントAI時代",
        "量子×AI",
        "Android XR",
        "WeatherNext"
      ],
      "metrics": [
        {
          "label": "Antigravity",
          "value": "Vibe Coding"
        },
        {
          "label": "量子+AI",
          "value": "次世代基盤"
        },
        {
          "label": "Android XR",
          "value": "新体験"
        }
      ],
      "cards": [
        {
          "title": "Google Antigravity 2.0",
          "lines": [
            "AIファーストの開発プラットフォーム",
            "誰でもビルダーになれる「Vibe Coding」",
            "Flutterと組み合わせてどこでも動作"
          ]
        },
        {
          "title": "量子 × AI",
          "lines": [
            "AIが量子コンピュータの設計を支援",
            "量子がAIの学習・推論を加速",
            "Willowプロセッサとの相乗効果"
          ]
        },
        {
          "title": "Android XR & WeatherNext",
          "lines": [
            "拡張現実の新体験をAndroidで",
            "AI気象モデルでハリケーン予測精度向上",
            "社会インフラへのAI応用が加速"
          ]
        }
      ],
      "dialogue": [
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "開発者向けの大注目はGoogle Antigravity 2.0の発表です。「誰でもビルダーになれる」AIファースト開発プラットフォームが本格始動！",
          "naration_text": "開発者向けの大注目はGoogle Antigravity 2.0の正式発表です。「誰でもビルダーになれる」をスローガンとしたAIファーストの開発プラットフォームで、いわゆる「Vibe Coding（感覚的コーディング）」を実現します。自然言語でアプリの動作を指示するだけで、AIが必要なコードを生成・修正・最適化します。Flutterと組み合わせることで、生成されたアプリをWebからモバイル、デスクトップまであらゆるプラットフォームで動作させることができます。",
          "audio": "audio/dlg_006_01_male.mp3",
          "duration_sec": 27.312
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "I/Oでは「エージェントAI時代の定義」というセッションも注目を集めました。ジェフ・ディーン、リズ・リードら豪華メンバーが語った、AIの次のステップとは？",
          "naration_text": "Google I/O 2026では「エージェントAI時代の定義」というセッションも大きな注目を集めました。ジェフ・ディーン、Google DeepMindのCTO コライ・カブチョグル、Google検索トップのリズ・リード、そしてログン・キルパトリックが参加したこのセッションでは、AIの能力向上が生産性と情報アクセスをどう変革するかが議論されました。単なるチャットAIを超えた、能動的・エージェント的AIが日常業務をどう変えるかという問いに対する答えが示されました。",
          "audio": "audio/dlg_006_02_female.mp3",
          "duration_sec": 32.112
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "量子コンピューティングとAIの融合についても重要な発表がありました。量子AIチームのハルトムート・ネーベン氏が、量子とAIの相互強化について解説しました。",
          "naration_text": "量子コンピューティングとAIの融合についても重要な発表がありました。Google量子AIチームの創設者ハルトムート・ネーベン氏と、Googleのリサーチ担当プレジデントのジェームズ・マニカ氏が登壇しました。AIが量子コンピュータの設計・運用を支援し、逆に量子技術がAIモデルの学習・推論・科学的発見を加速するという相互強化の関係が強調されました。AlphaEvolveによる量子回路最適化もその好例として紹介されています。",
          "audio": "audio/dlg_006_03_male.mp3",
          "duration_sec": 26.352
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Android XRも大きな注目を集めました。シャーラム・イザディ副社長が語った、AndroidによるXR（拡張現実）の新体験とは？",
          "naration_text": "Android XRも大きな注目を集めました。GoogleのAndroid XR担当副社長シャーラム・イザディ氏が登壇し、拡張現実の新体験を語りました。Androidエコシステムを活用したXRデバイスへの取り組みで、GeminiのAI能力とXRを組み合わせることで、現実世界の中にデジタル情報を自然に重ねる体験を実現します。スマートグラスやヘッドセット向けの新しいAndroid XRプラットフォームが、開発者向けに提供されることが発表されています。",
          "audio": "audio/dlg_006_04_female.mp3",
          "duration_sec": 32.88
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "WeatherNextによるハリケーン予測の精度向上も注目の成果です。AIが気象予測に革命をもたらし、防災・気候変動対策での活躍が始まっています。",
          "naration_text": "社会インフラへのAI応用という点では、WeatherNextの成果も注目されました。GoogleのAI気象モデルWeatherNextが、アメリカ国立ハリケーンセンターによるハリケーン・メリッサの歴史的な上陸予測を大幅に改善したことが報告されています。また科学との融合という観点では、デミス・ハサビスCEOがAIと科学の新時代を語るセッションも行われ、AlphaFoldから続くAI科学応用の次なるフロンティアが示されました。",
          "audio": "audio/dlg_006_05_male.mp3",
          "duration_sec": 25.512
        }
      ],
      "duration_sec": 144.168
    },
    {
      "id": "scene_999",
      "title": "Google 2026年前半 総まとめ",
      "accent": "#34A853",
      "accent_soft": "rgba(52, 168, 83, 0.18)",
      "layout": "hero",
      "kicker": "2026 SUMMARY",
      "headline": "Google 2026年前半\n総まとめ",
      "image": "images/scene_999.png",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "以上が2026年前半のGoogleの主要ニュースです。Geminiモデルの急速な進化が今年の最大のテーマでした。",
          "naration_text": "以上が2026年前半のGoogleの主要ニュースです。Gemini 3 Flashから始まり、3.1 Pro、3.1 Flash-Lite、そしてGoogle I/O 2026でのGemini 3.5 Flashと、モデルの急速な進化が今年最大のテーマでした。エージェントコーディング・マルチモーダル・長文コンテキストの3軸での性能向上が特に顕著で、実際の業務での活用が本格化しています。",
          "audio": "audio/dlg_999_01_female.mp3",
          "duration_sec": 26.808
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Lyria 3での音楽生成、Gemini Omniでの動画編集、Nano Banana 2での画像生成と、マルチモーダル生成AIのすべての領域でGoogleの存在感が際立ちました。",
          "naration_text": "生成AIの各分野でもGoogleの存在感が際立ちました。Lyria 3でのテキストから音楽の生成、Gemini Omniでの自然会話による動画編集、Nano Banana 2での高速画像生成、そしてVeo 3.1での映像生成と、テキスト・画像・動画・音楽のすべての生成AIモーダルで革新的な機能が提供されました。マルチモーダルAIの総合力という点でGoogleは他を圧倒するポジションを確立しています。",
          "audio": "audio/dlg_999_02_male.mp3",
          "duration_sec": 24.432
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AlphaEvolveによる科学的発見の加速、AI Co-Clinicianによる医療革新など、実世界の難題を解くAI応用も着実に前進しています。",
          "naration_text": "AlphaEvolveによる科学的発見の加速も大きなハイライトです。テレンス・タオとの数学的発見から、TPU回路設計の最適化、物流効率化まで、アルゴリズムを自律的に進化させる能力が幅広い分野に応用されています。医療ではAI Co-Clinicianが医師との新しい協働モデルを実現し、気象ではWeatherNextがハリケーン予測精度を大幅に改善しました。AIが実世界の難題を解く力が着実に高まっています。",
          "audio": "audio/dlg_999_03_female.mp3",
          "duration_sec": 30.336
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Gemma 4オープンモデルの進化やGoogle Antigravity 2.0の登場で、誰もがAIを使って価値あるものを作れる時代が本格到来しています！",
          "naration_text": "民主化の観点でも重要な進展がありました。Gemma 4オープンモデルにより、企業や研究者が高性能なAIを自由に活用できる環境が整い、Google Antigravity 2.0の登場でプログラミング知識がなくてもAIを活用してアプリを作れる時代が到来しました。AI Pointerは「指差すだけで意図が伝わる」インターフェースの革新をもたらし、量子AIはさらなる未来への扉を開いています。誰もがAIを使って価値あるものを作れる時代が本格的に始まっています。",
          "audio": "audio/dlg_999_04_male.mp3",
          "duration_sec": 29.088
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "このビデオはAiDiyが情報収集・音声合成・画像生成・ffmpeg制御などを組み合わせて作成しました！",
          "naration_text": "まさに、この動画もAiDiyが各種メディアや公式サイトから情報を収集し、AiDiyの音声合成・画像生成・ffmpeg制御などを使って作成したものです。AiDiyを活用すればだれでも簡単に映像コンテンツを作ることができます！",
          "audio": "audio/dlg_999_05_female.mp3",
          "duration_sec": 15.864
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "あなたも作ってみませんか？",
          "naration_text": "AiDiyを使って、あなたも作ってみませんか？",
          "audio": "audio/dlg_999_06_female.mp3",
          "duration_sec": 3.432
        }
      ],
      "duration_sec": 129.96
    }
  ],
  "total_duration_sec": 1086.072
};
