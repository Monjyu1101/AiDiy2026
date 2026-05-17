window.SCENARIO = {
  "project_name": "AiDiy web版紹介",
  "version": "take2",
  "title": "web版 AiDiy 紹介",
  "source": {
    "type": "agents_and_knowledge",
    "summary": "AiDiy の frontend_web（Vue 3 + Vite + TypeScript）の主要画面・機能を実装実態から紹介する。"
  },
  "target": {
    "language": "ja-JP",
    "format": "html_css_scene_player_with_media",
    "tone": "Web UIシステム紹介、実用的、使いたくなる",
    "goal": "frontend_web の主要画面（ログイン、業務画面、AIコア）を実際に使いたくなるように紹介する。"
  },
  "assets_policy": {
    "visual_style": "left_image_30_right_explanation_70",
    "audio_dir": "audio",
    "image_dir": "images",
    "avatar": "vrm/AiDiy_Sample_M.vrm",
    "tts_provider": "edge:female"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "web版 AiDiy 紹介",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "WEB FRONTEND",
      "headline": "web版 AiDiy の\n主要画面を紹介します",
      "lead": "Vue 3 + Vite + TypeScript で構築した AiDiy の Web UI。ログイン画面から業務画面、AI コアまで順番にご覧ください。",
      "subtitle": "web版 AiDiy の主要画面と機能を順番にご紹介します。",
      "image": "images/scene_000.png",
      "image_prompt": "Square 1:1 hero poster for a web frontend application. Bold typography 'AiDiy Web' with modern Vue.js UI and dashboard elements, dark background, strong cyan glow, professional enterprise web application aesthetic.",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "short_narration": "web版 AiDiy の主要画面をご紹介します。Vue 3 と TypeScript で構築した日本語ファーストの業務管理 Web UI です。",
      "long_narration": "この動画では、AiDiy の Web フロントエンドをご紹介します。Vue 3・Vite・TypeScript で構築した業務管理 Web UI で、ポート 8090 で動作します。ログイン・認証からメニュー遷移、qTubler テーブルによる業務データ管理、権限・利用者の管理画面、そして AI コアまで、主要な画面を順番にご覧ください。コンポーネントのファイル名からルートパスまで、日本語で統一した設計が特徴です。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 8.736,
      "long_start_sec": 0.0,
      "long_duration_sec": 28.152
    },
    {
      "id": "scene_001",
      "title": "frontend_web の概要",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.18)",
      "kicker": "TECH STACK",
      "headline": "Vue 3 + Vite + TypeScript で\n日本語ファーストの Web UI を実現",
      "lead": "ファイル名からルートパスまで日本語で統一。Vue Router + Pinia + qTubler で業務 UI を構築します。",
      "subtitle": "Vue 3 + Vite + TypeScript + Vue Router + Pinia + qTubler が基盤です。",
      "image": "images/scene_001.png",
      "image_prompt": "Vertical 2:3 technology stack infographic for a Vue.js enterprise web application, showing Vue 3, Vite, TypeScript, Vue Router, Pinia layers with Japanese UI examples, dark blueprint style, cyan accent.",
      "chips": [
        "Vue 3",
        "Vite",
        "TypeScript",
        "Vue Router",
        "Pinia",
        "qTubler"
      ],
      "metrics": [
        {
          "label": "ポート",
          "value": "8090"
        },
        {
          "label": "Proxy",
          "value": "8091/8092"
        }
      ],
      "cards": [
        {
          "title": "フロントエンド基盤",
          "lines": [
            "Vue 3 + Vite + TypeScript",
            "Vue Router でページ遷移管理",
            "Pinia で状態管理"
          ]
        },
        {
          "title": "日本語ファースト",
          "lines": [
            "コンポーネント名: C利用者一覧.vue",
            "ルートパス: /C管理/C利用者/一覧",
            "Pinia Store も日本語識別子"
          ]
        }
      ],
      "facts": [
        "frontend_web は Vue 3 + Vite + TypeScript で構築。",
        "Vite proxy で /core/* を 8091、/apps/* を 8092 にルーティング。",
        "コンポーネント名、ルートパス、JSON キーはすべて日本語で統一する。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "frontend_web: Vue 3 + Vite + TypeScript。Vue Router と Pinia を使用。"
        }
      ],
      "short_narration": "Vue 3 + TypeScript の基盤で、コンポーネント名からルートパスまで日本語で統一。日本語ネイティブな開発環境として、コードとドメインが直接対応します。",
      "long_narration": "frontend_web は Vue 3、Vite、TypeScript を基盤とした Web UI です。ポート 8090 で動作し、Vite proxy が /core/* を 8091 の Core API、/apps/* を 8092 の Apps API にルーティングします。コンポーネントのファイル名はC利用者一覧.vueのように日本語で、ルートパスも /C管理/C利用者/一覧 のように日本語で統一しています。Pinia で状態管理、Vue Router でページ遷移を管理し、独自開発の qTubler テーブルコンポーネントが業務データの一覧表示を担います。日本語話者が業務ドメインとコードを直接対応づけられる、日本語ファーストな開発体験を実現しています。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_start_sec": 8.736,
      "short_duration_sec": 11.544,
      "long_start_sec": 28.152,
      "long_duration_sec": 43.272
    },
    {
      "id": "scene_002",
      "title": "ログイン・認証・メニュー",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125, 255, 179, 0.18)",
      "kicker": "AUTH & NAVIGATION",
      "headline": "JWT 認証でログインし、\nトップメニューから各画面へ",
      "lead": "JWT ベースのログイン認証後、共通レイアウトとトップメニューで業務画面へ遷移します。",
      "subtitle": "ログイン → JWT認証 → _Layout + _TopMenu → 業務画面の流れです。",
      "image": "images/scene_002.png",
      "image_prompt": "Vertical 2:3 screenshot-style mockup of a Japanese enterprise web application login screen followed by a main menu navigation, showing authentication form and top navigation bar, green accent, clean modern design.",
      "chips": [
        "JWT認証",
        "_Layout",
        "_TopBar",
        "_TopMenu",
        "401自動ログアウト"
      ],
      "metrics": [
        {
          "label": "認証",
          "value": "JWT"
        },
        {
          "label": "共通",
          "value": "3コンポーネント"
        }
      ],
      "cards": [
        {
          "title": "認証フロー",
          "lines": [
            "ログイン画面でID・パスワード入力",
            "JWT トークンを localStorage 保存",
            "401 エラーで自動ログアウト"
          ]
        },
        {
          "title": "共通レイアウト",
          "lines": [
            "_Layout: ページ全体の枠組み",
            "_TopBar: ブランドロゴ・ユーザー情報",
            "_TopMenu: ナビゲーションメニュー"
          ]
        }
      ],
      "facts": [
        "認証は JWT を使い、トークンは localStorage に保存する。",
        "Axios interceptor が 401 レスポンスを検知して自動ログアウト処理を行う。",
        "_Layout、_TopBar、_TopMenu が共通レイアウトコンポーネント。"
      ],
      "evidence": [
        {
          "source": "frontend_web/AGENTS.md",
          "text": "JWT 認証。401 は Axios interceptor でログアウト処理へ自動誘導。"
        }
      ],
      "short_narration": "JWT 認証でログインすると、Axios interceptor が 401 エラーを自動検知。セッション管理を意識せず業務画面に集中できます。",
      "long_narration": "ログイン画面でIDとパスワードを入力すると、JWT トークンが発行されて localStorage に保存されます。Axios の interceptor が 401 エラーを自動検知してログアウト処理を行うため、トークンの期限切れや不正アクセスに対して自動で対応します。ログイン後は _Layout、_TopBar、_TopMenu の共通レイアウトコンポーネントでナビゲーションします。_TopMenu には権限に基づいたメニュー表示制御が組み込まれており、利用者の権限コードに応じて表示される項目が変わります。認証・認可を意識せず業務画面の開発に集中できる基盤です。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_start_sec": 20.28,
      "short_duration_sec": 10.248,
      "long_start_sec": 71.424,
      "long_duration_sec": 37.272
    },
    {
      "id": "scene_003",
      "title": "業務画面（qTubler テーブル）",
      "expression": "neutral",
      "accent": "#ffbf47",
      "accent_soft": "rgba(255, 191, 71, 0.18)",
      "kicker": "BUSINESS UI",
      "headline": "qTubler テーブルで\n業務データをグリッド表示",
      "lead": "AiDiy 独自の qTubler コンポーネントが、マスタ・トランザクション画面のメインテーブルとして機能します。",
      "subtitle": "qTublerFrame.vue が業務画面の主要グリッドコンポーネントです。",
      "image": "images/scene_003.png",
      "image_prompt": "Vertical 2:3 screenshot-style mockup of a Japanese enterprise business data grid screen, showing a master data table with qTubler-style rows, columns, sorting and filtering, amber accent, clean professional table design.",
      "chips": [
        "qTubler",
        "ソート",
        "フィルタ",
        "ページング",
        "列カスタマイズ"
      ],
      "metrics": [
        {
          "label": "共有",
          "value": "_share/qTublerFrame.vue"
        },
        {
          "label": "用途",
          "value": "全業務画面"
        }
      ],
      "cards": [
        {
          "title": "qTubler の特徴",
          "lines": [
            "カラム定義でテーブルを柔軟に構成",
            "ソート・フィルタ・ページング対応",
            "行選択・インライン編集など豊富な機能"
          ]
        },
        {
          "title": "業務画面での使い方",
          "lines": [
            "M系マスタ画面での一覧表示",
            "T系トランザクション画面での検索結果",
            "V系 JOIN 結果の表示にも利用"
          ]
        }
      ],
      "facts": [
        "qTubler は AiDiy 独自のテーブルコンポーネントで、_share/qTublerFrame.vue が正本。",
        "マスタ・トランザクション・V系ビュー画面のほぼすべてで qTubler を使用する。",
        "カラム定義を渡すだけでソート・フィルタ・ページングが自動的に有効になる。"
      ],
      "evidence": [
        {
          "source": "CLAUDE.md",
          "text": "qTubler（独自テーブル: _share/qTublerFrame.vue）が主要グリッド"
        }
      ],
      "short_narration": "AiDiy 独自の qTubler はカラム定義を渡すだけでソート・フィルタ・ページングが有効に。全業務画面で統一した操作感を提供します。",
      "long_narration": "AiDiy の業務画面の中心は、独自開発の qTubler テーブルコンポーネントです。_share/qTublerFrame.vue が共有の正本で、マスタ・トランザクション・V系ビューのほぼすべての画面で使用しています。カラム定義を渡すだけでソート、フィルタ、ページングが自動的に有効になり、行選択やインライン編集など豊富な機能を低コストで実装できます。M商品の商品一覧でも T配車の配車指示一覧でも、同じ qTubler コンポーネントを使うため、画面間の操作感が統一されます。新しい業務画面を追加するときも、qTubler にカラム定義を渡すだけでプロ品質の一覧画面ができあがります。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_start_sec": 30.528,
      "short_duration_sec": 10.2,
      "long_start_sec": 108.696,
      "long_duration_sec": 42.336
    },
    {
      "id": "scene_004",
      "title": "管理画面（権限・利用者）",
      "expression": "neutral",
      "accent": "#ff6bd6",
      "accent_soft": "rgba(255, 107, 214, 0.18)",
      "kicker": "ADMIN",
      "headline": "権限管理と利用者管理で\nセキュアな運用を実現",
      "lead": "C権限と C利用者が認証・認可の基盤です。権限に基づいてメニューの表示・非表示を制御します。",
      "subtitle": "C権限とC利用者で利用者管理とアクセス制御を実現します。",
      "image": "images/scene_004.png",
      "image_prompt": "Vertical 2:3 screenshot-style mockup of a user and permission management screen in Japanese enterprise software, showing user list and permission assignment grid, magenta accent, clean admin panel design.",
      "chips": [
        "C権限",
        "C利用者",
        "権限コード",
        "JWT認証",
        "パスワード変更"
      ],
      "metrics": [
        {
          "label": "C権限",
          "value": "権限マスタ"
        },
        {
          "label": "C利用者",
          "value": "利用者管理"
        }
      ],
      "cards": [
        {
          "title": "C権限",
          "lines": [
            "権限コード・権限名を定義",
            "メニューや機能のアクセス制御",
            "C利用者に権限を割り当て"
          ]
        },
        {
          "title": "C利用者",
          "lines": [
            "利用者ID・名前・パスワード管理",
            "JWT 認証の基盤",
            "権限コードで機能を制限"
          ]
        }
      ],
      "facts": [
        "C権限は権限マスタで、メニューや機能のアクセス制御に使用する。",
        "C利用者は JWT 認証付き利用者マスタ。パスワードはハッシュ化して保存する。",
        "C系テーブルは core_main.py が管理し、ポート 8091 の Core API で提供する。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "C権限: 権限マスタ。C利用者: JWT認証つき利用者マスタ。"
        }
      ],
      "short_narration": "C権限でアクセス制御を定義してC利用者に割り当て。パスワードはハッシュ化保存で、権限コードに応じてメニュー表示を自動制御します。",
      "long_narration": "AiDiy の管理画面は C権限と C利用者の2つのテーブルで構成されています。C権限でシステムの機能ごとにアクセス権を定義し、C利用者に権限コードを割り当てることで、利用者ごとのアクセス制御を実現します。パスワードはハッシュ化して保存され、JWT トークンで認証する安全な設計です。利用者の追加・編集・削除、パスワード変更も画面から操作できます。権限コードに応じてメニューの表示・非表示を切り替える仕組みも標準で実装されており、複数の役割を持つ組織での利用にも対応できます。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_start_sec": 40.728,
      "short_duration_sec": 10.392,
      "long_start_sec": 151.032,
      "long_duration_sec": 36.528
    },
    {
      "id": "scene_005",
      "title": "AI コア画面",
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123, 140, 255, 0.18)",
      "kicker": "AI CORE",
      "headline": "チャット・音声・画像・コード支援を\nひとつの UI で使う",
      "lead": "AIコアはテキスト、音声、画像、ファイル、コード支援を統合した多パネル UI です。Web版でもフル機能を利用できます。",
      "subtitle": "AIコア画面でチャット、音声、コード支援をフル活用できます。",
      "image": "images/scene_005.png",
      "image_prompt": "Vertical 2:3 screenshot-style mockup of an AI core interface in Japanese web application, showing chat panel, voice waveform, image panel and multiple code assistance panels, blue-violet accent, modern AI interface design.",
      "chips": [
        "CHAT_AI",
        "LIVE_AI",
        "CODE_AI1〜6",
        "音声処理",
        "画像生成"
      ],
      "metrics": [
        {
          "label": "コードパネル",
          "value": "6"
        },
        {
          "label": "AI種別",
          "value": "3系統"
        }
      ],
      "cards": [
        {
          "title": "AI 機能",
          "lines": [
            "CHAT_AI: テキストチャット",
            "LIVE_AI: 音声リアルタイム対話",
            "CODE_AI1〜6: コード支援パネル"
          ]
        },
        {
          "title": "WebSocket 接続",
          "lines": [
            "backend_server の A系 API と接続",
            "A会話履歴に会話を自動保存",
            "Claude・Copilot・Gemini など切替可能"
          ]
        }
      ],
      "facts": [
        "AIコアは WebSocket + マルチベンダー AI + Code CLI パネルを統合する多パネル UI。",
        "CHAT_AI、LIVE_AI、CODE_AI1〜6 の Code AI は設定で切り替え可能。",
        "A会話履歴テーブルに会話内容が自動保存される。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "AIコアは、テキスト、音声、画像、ファイル、コード支援を統合する多パネルUI。"
        }
      ],
      "short_narration": "AI コア画面は CHAT_AI・LIVE_AI・CODE_AI の3系統を統合。使用する AI モデルは設定から切り替えられ、会話は A会話履歴に自動保存されます。",
      "long_narration": "AI コア画面は AiDiy のフロントエンドで最も多機能な画面です。CHAT_AI でテキストチャット、LIVE_AI で音声リアルタイム対話、CODE_AI1〜6 の6パネルでコード支援を同時に利用できます。使用する AI モデルは設定から切り替えられ、Claude、Copilot、Gemini、Codex など複数のベンダーに対応しています。会話内容は A会話履歴テーブルに自動保存されるため、後から見返すことも可能です。すべての AI 機能が WebSocket で backend_server とリアルタイム接続しており、応答の遅延なく快適に対話できます。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_start_sec": 51.12,
      "short_duration_sec": 12.024,
      "long_start_sec": 187.56,
      "long_duration_sec": 36.648
    },
    {
      "id": "scene_999",
      "title": "ご視聴ありがとうございました",
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196, 155, 255, 0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "THANK YOU",
      "headline": "ご視聴ありがとうございました。\nあなたなら web版 AiDiy で何を創りますか？",
      "lead": "Vue 3 + TypeScript + qTubler の基盤に、業務画面と AI コアを組み合わせて、あなたの業務システムを構築してください。",
      "subtitle": "あなたなら web版 AiDiy で何を創りますか？",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "image": "images/scene_999.png",
      "image_prompt": "Square 1:1 elegant closing card for web AiDiy introduction. Clean typography 'Thank you for Watching', dark blue gradient background, subtle cyan glow, professional enterprise style.",
      "short_narration": "ご視聴ありがとうございました。日本語ファーストの web版 AiDiy で、業務管理と AI 活用を一体化したシステムを構築してください。",
      "long_narration": "ご視聴ありがとうございました。web版 AiDiy は Vue 3、TypeScript、qTubler を基盤に、業務管理画面と AI コアをひとつのシステムに統合したテンプレートです。qTubler テーブルと JWT 認証の基盤は最初から実装済みなので、新しい業務画面の追加もスムーズです。AI コアでチャット・音声・コード支援を活用しながら、業務システムを育てていく開発スタイルを体験できます。あなたの業務に合わせてカスタマイズし、ぜひ活用してください。",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_start_sec": 63.144,
      "short_duration_sec": 9.264,
      "long_start_sec": 224.208,
      "long_duration_sec": 31.968
    }
  ],
  "short_duration_sec": 72.408,
  "long_duration_sec": 256.176
};
