window.SCENARIO = {
  "project_name": "解説_Ollama統合_AiDiy_ja",
  "version": "duo-v2",
  "title": "AiDiy における Ollama 統合の解説 — ローカル LLM でプライバシーとコスト削減を両立するハイブリッド AI 戦略",
  "assets_policy": {
    "male_avatar": "../_vrm/VRM_male.vrm",
    "female_avatar": "../_vrm/VRM_female.vrm",
    "tts_male": "edge:male",
    "tts_female": "edge:female",
    "audio_output_dir": "frontend_web/public/Xビデオ/解説_Ollama統合_AiDiy_ja/audio"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "イントロ — AiDiy で Ollama を使うメリット",
      "accent": "#1a6ea0",
      "accent_soft": "rgba(26, 110, 160, 0.18)",
      "layout": "hero",
      "kicker": "LOCAL LLM × AIDIY",
      "headline": "ローカル LLM (Ollama) を\nAiDiy に統合する",
      "lead": "この動画は AiDiy の video_generation 機能で自動生成されました。Ollama を AiDiy に組み込み、プライバシーとコスト削減を同時に実現するハイブリッド AI 戦略を解説します。",
      "image": "images/scene_000.png",
      "source_summary": "",
      "factual_bullets": [],
      "forbidden_elements": [],
      "image_prompt": "",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "",
          "naration_text": "",
          "audio": "audio/dlg_000_01_female.mp3",
          "duration_sec": 20.0
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "",
          "naration_text": "",
          "audio": "audio/dlg_000_02_male.mp3",
          "duration_sec": 20.0
        }
      ],
      "duration_sec": 40.0
    },
    {
      "id": "scene_001",
      "title": "Ollama とは — ローカル LLM の簡単導入と OpenAI 互換 API",
      "accent": "#2e86ab",
      "accent_soft": "rgba(46, 134, 171, 0.18)",
      "kicker": "WHAT IS OLLAMA",
      "headline": "Ollama でローカル LLM を\n簡単セットアップ",
      "lead": "Ollama はローカル環境で LLM (Llama 3, Mistral, Phi-3 等) を簡単に動かせるツールです。OpenAI 互換 API を提供するため既存の AI アプリに組み込みやすいのが特徴です。",
      "image": "images/scene_001.png",
      "source_summary": "",
      "factual_bullets": [],
      "forbidden_elements": [],
      "image_prompt": "",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "",
          "naration_text": "",
          "audio": "audio/dlg_001_01_female.mp3",
          "duration_sec": 20.0
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "",
          "naration_text": "",
          "audio": "audio/dlg_001_02_male.mp3",
          "duration_sec": 20.0
        }
      ],
      "duration_sec": 40.0
    },
    {
      "id": "scene_002",
      "title": "AiDiy 統合 — AI コア / Code AI への Ollama 接続設定",
      "accent": "#3d9970",
      "accent_soft": "rgba(61, 153, 112, 0.18)",
      "kicker": "AIDIY INTEGRATION",
      "headline": "AI コア・Code AI に\nOllama を接続する",
      "lead": "AiDiy のマルチベンダー AI 構成に Ollama を追加する設定方法を解説します。AI コアの WebSocket 通信先や Code AI のプロバイダーに Ollama エンドポイントを設定できます。",
      "image": "images/scene_002.png",
      "source_summary": "",
      "factual_bullets": [],
      "forbidden_elements": [],
      "image_prompt": "",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "",
          "naration_text": "",
          "audio": "audio/dlg_002_01_female.mp3",
          "duration_sec": 20.0
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "",
          "naration_text": "",
          "audio": "audio/dlg_002_02_male.mp3",
          "duration_sec": 20.0
        }
      ],
      "duration_sec": 40.0
    },
    {
      "id": "scene_003",
      "title": "プライバシーとコスト — 外部送信ゼロの安心感と API 料金無料",
      "accent": "#e84855",
      "accent_soft": "rgba(232, 72, 85, 0.18)",
      "kicker": "PRIVACY & COST",
      "headline": "コードを外部に送らない\nセキュリティとコスト削減",
      "lead": "完全オフライン動作によりコードや社内データを外部に送信しません。トークン課金ゼロで大量コンテキストの試行錯誤が可能です。",
      "image": "images/scene_003.png",
      "source_summary": "",
      "factual_bullets": [],
      "forbidden_elements": [],
      "image_prompt": "",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "",
          "naration_text": "",
          "audio": "audio/dlg_003_01_female.mp3",
          "duration_sec": 20.0
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "",
          "naration_text": "",
          "audio": "audio/dlg_003_02_male.mp3",
          "duration_sec": 20.0
        }
      ],
      "duration_sec": 40.0
    },
    {
      "id": "scene_004",
      "title": "活用例 — ローカルコード解析 × MCP 完全自律エージェント",
      "accent": "#8a4fff",
      "accent_soft": "rgba(138, 79, 255, 0.18)",
      "kicker": "USE CASE",
      "headline": "MCP × Ollama で\n完全ローカル AI エージェント",
      "lead": "AiDiy の MCP サーバー群と Ollama を組み合わせることで、ローカル LLM がローカルファイルや DB を操作する完全ローカル AI エージェント環境を構築できます。",
      "image": "images/scene_004.png",
      "source_summary": "",
      "factual_bullets": [],
      "forbidden_elements": [],
      "image_prompt": "",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "",
          "naration_text": "",
          "audio": "audio/dlg_004_01_female.mp3",
          "duration_sec": 20.0
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "",
          "naration_text": "",
          "audio": "audio/dlg_004_02_male.mp3",
          "duration_sec": 20.0
        }
      ],
      "duration_sec": 40.0
    },
    {
      "id": "scene_005",
      "title": "使い分け表 — クラウド AI vs ローカル LLM の適材適所",
      "accent": "#f7931e",
      "accent_soft": "rgba(247, 147, 30, 0.18)",
      "kicker": "HYBRID STRATEGY",
      "headline": "クラウド AI とローカル LLM\nハイブリッド戦略",
      "lead": "クラウド AI を捨てるのではなく使い分けるハイブリッド戦略を整理します。機密性の高い作業は Ollama、高度な推論は Claude/GPT-4o という使い分けを推奨します。",
      "image": "images/scene_005.png",
      "source_summary": "",
      "factual_bullets": [],
      "forbidden_elements": [],
      "image_prompt": "",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "",
          "naration_text": "",
          "audio": "audio/dlg_005_01_female.mp3",
          "duration_sec": 20.0
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "",
          "naration_text": "",
          "audio": "audio/dlg_005_02_male.mp3",
          "duration_sec": 20.0
        }
      ],
      "duration_sec": 40.0
    },
    {
      "id": "scene_999",
      "title": "まとめ — Ollama で AI 開発を自由にする",
      "accent": "#1a6ea0",
      "accent_soft": "rgba(26, 110, 160, 0.18)",
      "layout": "hero",
      "kicker": "WRAP UP",
      "headline": "Ollama × AiDiy で\nAI 開発の自由度を高めよう",
      "lead": "ローカル LLM とクラウド AI のハイブリッド戦略で、セキュリティ・コスト・実験性を同時に手に入れましょう。自分でも AiDiy で Ollama 統合を試してビデオを作ってみてください！",
      "image": "images/scene_999.png",
      "source_summary": "",
      "factual_bullets": [],
      "forbidden_elements": [],
      "image_prompt": "",
      "dialogue": [
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "",
          "naration_text": "",
          "audio": "audio/dlg_999_01_male.mp3",
          "duration_sec": 20.0
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "",
          "naration_text": "",
          "audio": "audio/dlg_999_02_female.mp3",
          "duration_sec": 20.0
        }
      ],
      "duration_sec": 40.0
    }
  ],
  "total_duration_sec": 280.0
};