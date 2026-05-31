window.SCENARIO = {
  "project_name": "Claude Opus 4.8 解説 (掛け合い版)",
  "version": "duo-v2",
  "title": "Claude Opus 4.8 — Anthropic 最新フラッグシップモデル解説",
  "assets_policy": {
    "male_avatar": "../_vrm/VRM_male.vrm",
    "female_avatar": "../_vrm/VRM_female.vrm",
    "tts_male": "edge:male",
    "tts_female": "edge:female",
    "audio_output_dir": "frontend_web/public/Xビデオ/解説_Claude_Opus4-8/audio"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "Claude Opus 4.8 とは",
      "accent": "#d97b2b",
      "accent_soft": "rgba(217, 123, 43, 0.18)",
      "layout": "hero",
      "kicker": "ANTHROPIC 2026",
      "headline": "Claude Opus 4.8\nAnthropicの最新フラッグシップモデル",
      "lead": "Opus 4.7 を引き継ぎ各種ベンチマークで改善を果たした最新モデルを、わかりやすく解説します。",
      "image": "images/scene_000.png",
      "source_summary": "Anthropic が 2026年5月に公開した Claude Opus 4.8 は、Opus 4.7 を引き継ぎ各種ベンチマークで改善を果たした最新フラッグシップモデル。Dynamic Workflows・Effort Control・Fast Mode・誠実性強化が四本柱。AiDiy の AIコア・Code AI に組み込んで活用できる。",
      "factual_bullets": [
        "モデル名: claude-opus-4-8（API モデルID）",
        "2026年5月公開、Opus 4.7 の後継最上位モデル",
        "Dynamic Workflows: Claude Code で並列サブエージェント処理",
        "Effort Control: 思考の深さを low / high / extra / max の 4 段階選択",
        "Fast Mode: 2.5倍速・前世代比3倍コスト効率",
        "誠実性強化: コード欠陥見逃し確率を前世代比 1/4 に抑制",
        "AiDiy AIコア / Code AI に claude_sdk として組み込み可能"
      ],
      "forbidden_elements": [
        "未確認のベンチマーク数値を断言しない",
        "他社モデルの具体的スコアを比較表示しない",
        "Opus 4.7 との差を誇張しない"
      ],
      "image_prompt": "Futuristic AI concept illustration: A glowing anthropomorphic neural network with branching thought pathways radiating outward in warm amber and deep orange tones, dark gradient background. Four orbiting symbols represent speed, precision, control, and integrity. Clean modern tech aesthetic suitable for AI explainer video intro.",
      "source_documents": [
        "Anthropic Claude Opus 4.8 公式発表 (2026年5月)",
        "claude-opus-4-8 モデルカード"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Anthropic の最新モデル Claude Opus 4.8 を解説します。この動画は AiDiy で自動生成されました。",
          "naration_text": "今回は、Anthropic が 2026年5月に公開した最新フラッグシップモデル、Claude Opus 4.8 を解説します。前世代の Opus 4.7 を引き継ぎながら、各種ベンチマークで着実な改善を果たしたモデルです。なお、この動画は AiDiy の video_generation機能 を使って自動生成されました。",
          "audio": "audio/dlg_000_01_female.mp3",
          "duration_sec": 20.76
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Dynamic Workflows・Effort Control・Fast Mode・誠実性強化の四本柱を順番に紹介します。",
          "naration_text": "今回の解説では、Dynamic Workflows、Effort Control、Fast Mode、誠実性強化という四つの主要機能を順番に紹介します。後半では AiDiy の AIコアや Code AI に組み込んだ活用シナリオもお伝えします。",
          "audio": "audio/dlg_000_02_male.mp3",
          "duration_sec": 11.952
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "難しい専門用語も丁寧に解説するので、ぜひ最後までご覧ください。",
          "naration_text": "専門用語が多い分野ですが、できるだけわかりやすく解説します。AIを業務に取り入れたい方にも、開発に活かしたいエンジニアにも役立つ内容ですので、ぜひ最後までご覧ください。",
          "audio": "audio/dlg_000_03_female.mp3",
          "duration_sec": 13.368
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "AiDiy への組み込み方法も具体的に紹介します。",
          "naration_text": "AiDiy の設定ファイルを少し変えるだけで Claude Opus 4.8 をすぐ使い始められます。実際の組み込み方も具体的に紹介しますので、ぜひ参考にしてください。",
          "audio": "audio/dlg_000_04_male.mp3",
          "duration_sec": 10.824
        }
      ],
      "duration_sec": 56.904
    },
    {
      "id": "scene_001",
      "title": "Dynamic Workflows — 並列サブエージェントで大規模タスクを処理",
      "accent": "#c0392b",
      "accent_soft": "rgba(192, 57, 43, 0.18)",
      "kicker": "DYNAMIC WORKFLOWS",
      "headline": "Dynamic Workflows\n並列サブエージェントで大規模タスクを一気に処理",
      "lead": "Claude Code が複数のサブエージェントを同時に動かし、大きな仕事を分担して片付けます。",
      "image": "images/scene_001.png",
      "source_summary": "Claude Opus 4.8 の Dynamic Workflows は、Claude Code が大規模タスクを複数の並列サブエージェントに分割して処理する仕組み。巨大なコードベースの解析やリファクタリングも、並列化により大幅に短縮できる。",
      "factual_bullets": [
        "Claude Code が大規模タスクを複数のサブエージェントに自動分割",
        "サブエージェントは並列実行され、処理時間を大幅短縮",
        "大規模コードベースの解析・リファクタリング・テスト生成に対応",
        "エージェント間で中間結果を共有しながら最終結果を統合"
      ],
      "forbidden_elements": [
        "サブエージェント数の上限を断言しない",
        "すべてのタスクが必ず並列化されるかのように誤解させない"
      ],
      "image_prompt": "Futuristic tech illustration: Central orchestrator node branching into multiple parallel sub-agents shown as glowing spheres connected by light trails, dark background with deep red accent tones. Each sub-agent processes a fragment of a large code structure. Clean, modern data flow diagram style.",
      "source_documents": [
        "Anthropic Claude Opus 4.8 公式発表 (2026年5月)",
        "claude-opus-4-8 モデルカード"
      ],
      "chips": [
        "Claude Code",
        "並列処理",
        "サブエージェント",
        "大規模コードベース"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Dynamic Workflows は、大きな仕事を複数のサブエージェントに振り分けて並列処理する仕組みです。",
          "naration_text": "Dynamic Workflows は、Claude Code が大規模なタスクを複数のサブエージェントに自動的に振り分け、並列で処理する仕組みです。これまで時間がかかっていた大きな仕事を、手分けして一気に片付けられるようになります。",
          "audio": "audio/dlg_001_01_female.mp3",
          "duration_sec": 17.712
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "大規模なコードベースの解析やリファクタリングが、大幅に速くなります。",
          "naration_text": "たとえば、数千ファイルある大規模なコードベースを解析したり、プロジェクト全体をリファクタリングしたりする作業が、並列処理によって大幅に速くなります。これまで何時間もかかっていた作業が、実用的な時間内に収まるようになります。",
          "audio": "audio/dlg_001_02_male.mp3",
          "duration_sec": 14.856
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "サブエージェントが中間結果を共有しながら、最終的な答えをまとめます。",
          "naration_text": "サブエージェントたちは中間結果を共有しながら処理を進め、最終的に統合された答えを返します。バラバラに動くのではなく、全体として一つのチームのように連携できるのが特徴です。",
          "audio": "audio/dlg_001_03_female.mp3",
          "duration_sec": 14.856
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "大きなプロジェクトを任せたいエンジニアにとって、頼りになる機能です。",
          "naration_text": "一人のエンジニアでは手に余るような規模のプロジェクトを、Claude Code に任せてしまえる。そんな時代が近づいていることを実感させてくれる機能です。実際の開発現場での活用が楽しみです。",
          "audio": "audio/dlg_001_04_male.mp3",
          "duration_sec": 13.872
        }
      ],
      "duration_sec": 61.296
    },
    {
      "id": "scene_002",
      "title": "Effort Control — 思考の深さを4段階で選択",
      "accent": "#8e44ad",
      "accent_soft": "rgba(142, 68, 173, 0.18)",
      "kicker": "EFFORT CONTROL",
      "headline": "Effort Control\n思考の深さを low / high / extra / max で選択",
      "lead": "問題の難しさに合わせて AI の考え込み具合を調整し、コストと精度を最適化します。",
      "image": "images/scene_002.png",
      "source_summary": "Claude Opus 4.8 の Effort Control は、思考の深さを low / high / extra / max の 4 段階で選択できる仕組み。簡単なタスクには low、高精度が必要な場面には max を使い分けることで、コストと品質を最適化できる。",
      "factual_bullets": [
        "思考レベルは low / high / extra / max の 4 段階",
        "low: 高速・低コスト、簡単な質問や素早い確認に適する",
        "high: バランス型、通常の開発作業や調査に適する",
        "extra / max: 深い推論が必要な複雑問題や重要な判断に使用",
        "API パラメータで簡単に切り替え可能"
      ],
      "forbidden_elements": [
        "各レベルの具体的なコスト比率を断言しない",
        "max が常に最良とは限らないことに注意"
      ],
      "image_prompt": "Futuristic control panel with four glowing level indicators labeled low, high, extra, max arranged vertically like a power meter, deep purple and violet color scheme on dark background. Each level lights up progressively brighter, representing increasing AI thinking depth. Clean modern UI concept art.",
      "source_documents": [
        "Anthropic Claude Opus 4.8 公式発表 (2026年5月)",
        "claude-opus-4-8 モデルカード"
      ],
      "chips": [
        "low",
        "high",
        "extra",
        "max",
        "コスト最適化"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Effort Control は、AI の思考の深さを low・high・extra・max の 4 段階で選べる機能です。",
          "naration_text": "Effort Control は、Claude Opus 4.8 が問題をどれくらい深く考えるかを、low、high、extra、max の 4 段階で選択できる機能です。料理で言えば、さっと炒めるか、じっくり煮込むかを選べるようなイメージです。",
          "audio": "audio/dlg_002_01_female.mp3",
          "duration_sec": 14.928
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "簡単な確認には low、複雑な判断には max を使い分けることでコストを抑えられます。",
          "naration_text": "メールの要約や簡単な質問確認には low を使い、プロジェクトの重要な設計判断や難しいバグ解析には max を使う。こうした使い分けによって、コストを大幅に抑えながら必要な場面だけ最高精度を引き出せます。",
          "audio": "audio/dlg_002_02_male.mp3",
          "duration_sec": 13.344
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "API パラメータを変えるだけで切り替えられるので、実装も簡単です。",
          "naration_text": "実装は API のパラメータを一つ変えるだけです。既存のアプリやワークフローに組み込みやすく、タスクの種類に応じて動的に切り替えることもできます。",
          "audio": "audio/dlg_002_03_female.mp3",
          "duration_sec": 13.032
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "用途に合わせてレベルを変えることで、費用対効果が大きく向上します。",
          "naration_text": "同じモデルを使いながら、用途に応じてレベルを変えるだけで費用対効果が大きく変わります。これまで高精度のモデルはコストが高くて使いにくいという問題がありましたが、Effort Control がその悩みを解消してくれます。",
          "audio": "audio/dlg_002_04_male.mp3",
          "duration_sec": 14.376
        }
      ],
      "duration_sec": 55.68
    },
    {
      "id": "scene_003",
      "title": "Fast Mode — 2.5倍の速度と3倍のコスト効率",
      "accent": "#1abc9c",
      "accent_soft": "rgba(26, 188, 156, 0.18)",
      "kicker": "FAST MODE",
      "headline": "Fast Mode\n2.5倍速度・前世代比3倍のコスト効率",
      "lead": "Opus 4.7 と比べて大幅に速く、より低コストで同等以上の結果を出せます。",
      "image": "images/scene_003.png",
      "source_summary": "Claude Opus 4.8 の Fast Mode は、前世代 Opus 4.7 と比べて 2.5 倍の速度と 3 倍のコスト効率を実現した動作モード。高速化しながらも品質を維持しており、コスト意識の高い本番環境での利用に適している。",
      "factual_bullets": [
        "Opus 4.7 比 2.5倍の処理速度を実現",
        "前世代比 3倍のコスト効率（同品質での費用が 1/3 程度）",
        "高速化しながら品質の維持・改善を両立",
        "本番環境での大量リクエスト処理や低レイテンシ要件に適合"
      ],
      "forbidden_elements": [
        "速度・コスト比率は Anthropic 発表ベースであることを明記",
        "すべてのユースケースで必ず速くなると断言しない"
      ],
      "image_prompt": "Dynamic speed visualization: A streak of light accelerating through a dark tunnel with teal and cyan light trails, digital speedometer showing 2.5x multiplier, cost efficiency graph showing downward trend. Clean modern infographic style with dark background and bright teal accent colors.",
      "source_documents": [
        "Anthropic Claude Opus 4.8 公式発表 (2026年5月)",
        "claude-opus-4-8 モデルカード"
      ],
      "chips": [
        "2.5倍速",
        "3倍コスト効率",
        "Opus 4.7 比",
        "本番環境対応"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Fast Mode では、前世代の Opus 4.7 と比べて 2.5倍速く動き、コストも約3分の1になります。",
          "naration_text": "Fast Mode は、前世代の Opus 4.7 と比べて処理速度が 2.5 倍になり、コスト効率は 3 倍に改善されています。Anthropic の発表ベースの数字ですが、同じ品質の結果を得るのにかかるコストが大幅に下がったことを意味します。",
          "audio": "audio/dlg_003_01_female.mp3",
          "duration_sec": 16.32
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "速くなってもクオリティは落ちていない、というのが重要なポイントです。",
          "naration_text": "ただ速くなっただけでなく、品質を維持・改善しながらコストを下げた点が重要です。これまで最上位モデルは「高品質だけど高コスト」という悩みがありましたが、Opus 4.8 の Fast Mode はその壁を大きく崩しています。",
          "audio": "audio/dlg_003_02_male.mp3",
          "duration_sec": 12.72
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "大量のリクエストをさばく本番環境や、素早い応答が必要なサービスに特に向いています。",
          "naration_text": "本番環境で大量のリクエストを処理するシステムや、ユーザーに素早く応答しなければならないサービスにとって、Fast Mode は非常に魅力的な選択肢です。レスポンス速度が重要なチャットボットや、リアルタイムのコード補完ツールなどに活用できます。",
          "audio": "audio/dlg_003_03_female.mp3",
          "duration_sec": 14.208
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "コスト効率が上がることで、より多くの機能や実験を試しやすくなります。",
          "naration_text": "コスト効率が上がると、今まで費用の問題で試せなかった機能や実験を気軽に試せるようになります。開発中のプロトタイプを何度でも回したり、より多くのユーザーに最上位モデルを提供したりする選択肢が広がります。",
          "audio": "audio/dlg_003_04_male.mp3",
          "duration_sec": 13.104
        }
      ],
      "duration_sec": 56.352
    },
    {
      "id": "scene_004",
      "title": "誠実性強化 — コード欠陥の見逃し確率を1/4に抑制",
      "accent": "#2980b9",
      "accent_soft": "rgba(41, 128, 185, 0.18)",
      "kicker": "INTEGRITY",
      "headline": "誠実性強化\nコード欠陥の見逃し確率を前世代比 1/4 に抑制",
      "lead": "AI が間違いや欠陥を正直に報告する能力が向上し、信頼性の高いコードレビューが実現します。",
      "image": "images/scene_004.png",
      "source_summary": "Claude Opus 4.8 の誠実性強化により、コードの欠陥を見逃す確率が前世代比 1/4 に低下した。AI が不確かなことを不確かとして正直に伝える能力が向上しており、コードレビューや品質保証の場面で信頼性が増している。",
      "factual_bullets": [
        "コード欠陥の見逃し確率が前世代比 1/4 に低下",
        "AI が不確かな情報を正直に伝える誠実性が向上",
        "コードレビュー・品質保証・セキュリティ検査での信頼性向上",
        "ハルシネーション（事実誤認）の発生率も改善傾向"
      ],
      "forbidden_elements": [
        "欠陥を完全にゼロにできるとは断言しない",
        "数値は Anthropic 発表ベースであることを明記"
      ],
      "image_prompt": "Security and integrity concept: A shield with a magnifying glass revealing clean code lines, blue light scanning through code blocks, bugs and defects highlighted and crossed out with blue X marks. Dark background with cool blue tones. Modern cybersecurity meets code quality illustration style.",
      "source_documents": [
        "Anthropic Claude Opus 4.8 公式発表 (2026年5月)",
        "claude-opus-4-8 モデルカード"
      ],
      "chips": [
        "欠陥見逃し 1/4",
        "誠実性向上",
        "コードレビュー",
        "ハルシネーション低減"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "誠実性強化により、コードの欠陥を見逃す確率が前世代比で 4 分の 1 になりました。",
          "naration_text": "Claude Opus 4.8 では誠実性の強化が進み、コードの欠陥を見逃す確率が前世代と比べて 4 分の 1 に抑えられました。Anthropic の発表によるものですが、コードレビューや品質保証の場面で AI をより信頼して使えるようになったことを意味します。",
          "audio": "audio/dlg_004_01_female.mp3",
          "duration_sec": 15.264
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "わからないことをわからないと正直に言える能力が上がった、というのも大きな進化です。",
          "naration_text": "誠実性の向上で特に重要なのは、AI が不確かなことを不確かとして正直に伝えてくれるようになった点です。これまでの AI は自信満々に間違いを言ってしまうことがありましたが、Opus 4.8 ではその傾向が大きく改善されています。",
          "audio": "audio/dlg_004_02_male.mp3",
          "duration_sec": 16.152
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "セキュリティ検査や重要なコードの品質確認で、より頼りになるパートナーになります。",
          "naration_text": "セキュリティ上の脆弱性を見つけたり、重要なシステムのコードを品質確認したりする作業で、AI を信頼して任せられる場面が増えます。欠陥を見逃すリスクが下がることで、エンジニアが最終確認に集中できる環境が作りやすくなります。",
          "audio": "audio/dlg_004_03_female.mp3",
          "duration_sec": 14.376
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "完璧ではないけれど、信頼して使える相棒に近づいてきた、という感覚です。",
          "naration_text": "もちろん AI が完璧になったわけではありませんが、欠陥を素直に報告してくれる信頼できる作業パートナーに、着実に近づいていると感じます。特にコードの品質を重視する現場での活用が期待されます。",
          "audio": "audio/dlg_004_04_male.mp3",
          "duration_sec": 12.336
        }
      ],
      "duration_sec": 58.128
    },
    {
      "id": "scene_005",
      "title": "AiDiy AIコアへの組み込み",
      "accent": "#e67e22",
      "accent_soft": "rgba(230, 126, 34, 0.18)",
      "kicker": "AIDIY AICHAT",
      "headline": "AiDiy AIコアに\nClaude Opus 4.8 を組み込む",
      "lead": "設定ファイルを一行変えるだけで、最新の Opus 4.8 でチャットや画像分析が使えるようになります。",
      "image": "images/scene_005.png",
      "source_summary": "AiDiy の AIコアは CHAT_AI_NAME / LIVE_AI_NAME の設定を変えるだけで、利用するモデルを切り替えられる。claude-opus-4-8 を指定すれば、テキストチャット・画像分析・リアルタイム音声対話に Opus 4.8 が使える。",
      "factual_bullets": [
        "AiDiy AIコアの設定: CHAT_AI_NAME / LIVE_AI_NAME を変更",
        "claude-opus-4-8 を指定するだけで最新モデルに切り替え",
        "テキストチャット・画像分析・リアルタイム音声対話に対応",
        "設定ファイル: backend_server/_config/AiDiy_config.json"
      ],
      "forbidden_elements": [
        "設定変更で全機能が即利用可能と断言しない（APIキーや権限確認が必要な場合あり）"
      ],
      "image_prompt": "Clean UI screenshot concept: AiDiy chat interface showing a modern dark-themed web app with an AI chat panel on the left and a settings panel on the right. Configuration JSON file highlighted with claude-opus-4-8 model name visible. Orange accent color scheme, professional SaaS aesthetic.",
      "source_documents": [
        "Anthropic Claude Opus 4.8 公式発表 (2026年5月)",
        "backend_server/AGENTS.md",
        "AGENTS.md (AIコア設定項目)"
      ],
      "chips": [
        "CHAT_AI_NAME",
        "LIVE_AI_NAME",
        "claude-opus-4-8",
        "設定ファイル変更"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AiDiy の AIコアでは、設定ファイルを変えるだけで Opus 4.8 に切り替えられます。",
          "naration_text": "AiDiy の AIコアは、設定ファイルの CHAT_AI_NAME か LIVE_AI_NAME に claude-opus-4-8 を指定するだけで、最新の Opus 4.8 に切り替えられます。コードの変更は不要で、設定一行で最新モデルが使えるのが AiDiy の強みです。",
          "audio": "audio/dlg_005_01_female.mp3",
          "duration_sec": 18.384
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "テキストチャットだけでなく、画像分析やリアルタイム音声対話にも対応しています。",
          "naration_text": "テキストチャットだけでなく、画像を読み込んで内容を分析したり、マイクで話しかけてリアルタイムに音声で対話したりする機能にも、Opus 4.8 を使えます。AIコアの持つ幅広い機能が、最新モデルの恩恵をすぐに受けられます。",
          "audio": "audio/dlg_005_02_male.mp3",
          "duration_sec": 15.0
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "設定ファイルは backend_server/_config/AiDiy_config.json で管理されています。",
          "naration_text": "設定ファイルは backend_server の _config フォルダにある AiDiy_config.json です。ここで AI モデルの種類や、チャット・コード支援それぞれのモデルを個別に指定できます。環境ごとに使い分けることも可能です。",
          "audio": "audio/dlg_005_03_female.mp3",
          "duration_sec": 14.88
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Effort Control や Fast Mode の恩恵も、設定変更だけでそのまま受けられます。",
          "naration_text": "AIコアを通じて Opus 4.8 を使えば、今回紹介した Effort Control や Fast Mode の恩恵もそのまま受けられます。AiDiy のシステムが API との橋渡しをしてくれるので、利用者は設定変更だけに集中できます。",
          "audio": "audio/dlg_005_04_male.mp3",
          "duration_sec": 12.12
        }
      ],
      "duration_sec": 60.384
    },
    {
      "id": "scene_006",
      "title": "AiDiy Code AI への組み込み",
      "accent": "#27ae60",
      "accent_soft": "rgba(39, 174, 96, 0.18)",
      "kicker": "AIDIY CODE AI",
      "headline": "AiDiy Code AI に\nClaude Opus 4.8 を組み込む",
      "lead": "claude_sdk を選択して Opus 4.8 に向けるだけで、Dynamic Workflows の恩恵をコード作業に活かせます。",
      "image": "images/scene_006.png",
      "source_summary": "AiDiy の Code AI（CODE_AI1_NAME〜CODE_AI6_NAME）に claude_sdk を設定し、モデルとして claude-opus-4-8 を指定することで、Dynamic Workflows による並列サブエージェント処理や誠実性強化されたコードレビューを活用できる。",
      "factual_bullets": [
        "Code AI 設定: CODE_AI1_NAME〜CODE_AI6_NAME に claude_sdk を指定",
        "claude-opus-4-8 モデルを Claude SDK 経由で呼び出す",
        "Dynamic Workflows による並列サブエージェント処理が使える",
        "誠実性強化によりコードレビュー・バグ検出の精度が向上",
        "コード補完・リファクタリング・テスト自動生成に対応"
      ],
      "forbidden_elements": [
        "すべてのコード作業が完全自動化されると誤解させない",
        "claude_sdk の設定方法は公式ドキュメントを参照すること"
      ],
      "image_prompt": "Modern IDE-style illustration: Code editor with green-highlighted AI suggestions appearing in real-time, multiple parallel processing threads shown as green light trails converging into clean code. Dark background with vivid green accents. Dynamic software development visualization, clean tech art style.",
      "source_documents": [
        "Anthropic Claude Opus 4.8 公式発表 (2026年5月)",
        "AGENTS.md (CODE_AI1_NAME〜CODE_AI6_NAME)",
        "backend_server/AGENTS.md"
      ],
      "chips": [
        "claude_sdk",
        "CODE_AI1〜6",
        "Dynamic Workflows",
        "コードレビュー強化"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AiDiy の Code AI に claude_sdk を設定し、モデルを Opus 4.8 に向けるだけです。",
          "naration_text": "AiDiy の Code AI は CODE_AI1_NAME から CODE_AI6_NAME の設定で使うエンジンを選べます。ここに claude_sdk を指定して、モデルとして claude-opus-4-8 を向けることで、最新の Opus 4.8 をコード作業に活用できます。",
          "audio": "audio/dlg_006_01_female.mp3",
          "duration_sec": 15.984
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Dynamic Workflows の並列サブエージェントが、大規模なコード作業を手分けして処理します。",
          "naration_text": "Code AI から Opus 4.8 を使うと、Dynamic Workflows の並列サブエージェントが大規模なコード作業を手分けして処理してくれます。大きなリポジトリの解析やリファクタリングも、短時間で仕上げられるようになります。",
          "audio": "audio/dlg_006_02_male.mp3",
          "duration_sec": 12.0
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "誠実性強化によるコードレビューで、欠陥の見逃しが大幅に減ります。",
          "naration_text": "誠実性強化の効果も、Code AI を通じてそのまま受けられます。コードレビューやバグ検出の精度が上がり、AI が問題を正直に報告してくれるので、見逃しが大幅に減ります。重要なコードの品質確認を任せるシーンで特に効果的です。",
          "audio": "audio/dlg_006_03_female.mp3",
          "duration_sec": 12.648
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "コード補完・リファクタリング・テスト自動生成まで、幅広い作業を Opus 4.8 に任せられます。",
          "naration_text": "コードの補完、リファクタリングの提案、テストコードの自動生成まで、幅広いコード作業を Opus 4.8 に任せられます。AiDiy の Code AI パネルから直接使えるので、開発の流れを止めずにすぐ活用できます。",
          "audio": "audio/dlg_006_04_male.mp3",
          "duration_sec": 10.296
        }
      ],
      "duration_sec": 50.928
    },
    {
      "id": "scene_999",
      "title": "まとめ",
      "accent": "#d97b2b",
      "accent_soft": "rgba(217, 123, 43, 0.18)",
      "layout": "hero",
      "kicker": "ANTHROPIC 2026",
      "headline": "Claude Opus 4.8\nまとめ",
      "lead": "Dynamic Workflows・Effort Control・Fast Mode・誠実性強化という四つの進化を、AiDiy ですぐに活かせます。",
      "image": "images/scene_999.png",
      "source_summary": "Claude Opus 4.8 は Dynamic Workflows・Effort Control・Fast Mode・誠実性強化という四つの主要進化を果たした最新フラッグシップモデル。AiDiy の AIコア・Code AI に claude-opus-4-8 を設定するだけで、これらの恩恵を即座に受けられる。",
      "factual_bullets": [
        "Dynamic Workflows: 並列サブエージェントで大規模タスク処理",
        "Effort Control: low / high / extra / max の 4 段階思考深度選択",
        "Fast Mode: 前世代比 2.5倍速・3倍コスト効率",
        "誠実性強化: コード欠陥見逃し確率 1/4",
        "AiDiy: 設定変更のみで Opus 4.8 をすぐ利用開始可能"
      ],
      "forbidden_elements": [
        "AiDiy が公式の Anthropic 製品であるかのような誤解を与えない"
      ],
      "image_prompt": "Summarizing illustration: Four glowing icons arranged in a 2x2 grid representing speed, control, parallel processing, and integrity, connected by warm amber light lines. Central AiDiy logo or text in the middle. Dark background with warm orange gradient. Professional tech infographic closing slide style.",
      "source_documents": [
        "Anthropic Claude Opus 4.8 公式発表 (2026年5月)",
        "AGENTS.md",
        "backend_server/AGENTS.md"
      ],
      "dialogue": [
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Claude Opus 4.8 は、速度・コスト・品質・信頼性の四つを同時に高めた最新モデルです。",
          "naration_text": "今回紹介した Claude Opus 4.8 は、Dynamic Workflows による並列処理、Effort Control による柔軟な思考深度選択、Fast Mode による 2.5 倍速・3 倍コスト効率、そして誠実性強化によるコード品質向上という、四つの重要な進化を果たしています。",
          "audio": "audio/dlg_999_01_male.mp3",
          "duration_sec": 13.752
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AiDiy の設定を変えるだけで、これらの機能をすぐに使い始められます。",
          "naration_text": "AiDiy を使えば、設定ファイルに claude-opus-4-8 を指定するだけで、これらすべての機能を今日から使い始められます。AIコアでのチャットや画像分析はもちろん、Code AI を通じたコード支援にも最新モデルをすぐに活かせます。",
          "audio": "audio/dlg_999_02_female.mp3",
          "duration_sec": 17.064
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "AiDiy は AI と業務システムを組み合わせた、日本語ネイティブな開発フレームワークです。",
          "naration_text": "AiDiy は、業務システム開発テンプレートをベースに、マルチベンダー AI・MCP・画像や音声・動画生成ツールを統合した、日本語ネイティブな開発フレームワークです。この動画自体も、AiDiy の video_generation機能 で自動生成されました。",
          "audio": "audio/dlg_999_03_male.mp3",
          "duration_sec": 11.904
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "チャンネル登録をして、AiDiy の活用事例をチェックしてください。ぜひ自分でも試してみてください！",
          "naration_text": "動画を気に入っていただけたら、ぜひチャンネル登録をお願いします。AiDiy の活用事例はこれからも続々と紹介していく予定です。設定ファイルを少し変えるだけで最新 AI が使えてしまうって、すごく楽しいと思いませんか？ぜひ皆さんも AiDiy を試してみてください。きっと『自分でも作れる』という感覚を実感していただけると思います！",
          "audio": "audio/dlg_999_04_female.mp3",
          "duration_sec": 27.144
        }
      ],
      "duration_sec": 69.864
    }
  ],
  "total_duration_sec": 469.536
};
