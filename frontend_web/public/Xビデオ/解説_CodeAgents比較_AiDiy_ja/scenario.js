window.SCENARIO = {
  "project_name": "解説_CodeAgents比較_AiDiy_ja",
  "version": "duo-v2",
  "title": "Claude Code / OpenAI Codex / Google Antigravity 比較解説 — AiDiy で試す Coding AI エージェント",
  "assets_policy": {
    "male_avatar": "../_vrm/VRM_male.vrm",
    "female_avatar": "../_vrm/VRM_female.vrm",
    "tts_male": "edge:male",
    "tts_female": "edge:female",
    "audio_output_dir": "frontend_web/public/Xビデオ/解説_CodeAgents比較_AiDiy_ja/audio"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "イントロ — 3つの Coding Agent と AiDiy",
      "accent": "#1a6ea0",
      "accent_soft": "rgba(26, 110, 160, 0.18)",
      "layout": "hero",
      "kicker": "CODING AI AGENTS 2026",
      "headline": "Claude Code / OpenAI Codex / Google Antigravity\nどの場面で何が得意か",
      "lead": "この動画は AiDiy の video_generation 機能で自動生成されました。3つの Coding AI Agent を利用シーン別に整理し、AiDiy の立ち位置を紹介します。",
      "image": "images/scene_000.png",
      "source_summary": "",
      "factual_bullets": [],
      "forbidden_elements": [
        "完全自動開発",
        "人間不要",
        "絶対安全",
        "どれか一つが完全上位"
      ],
      "image_prompt": "A futuristic tech illustration showing three glowing pillars representing Claude Code (Anthropic), OpenAI Codex, and Google Antigravity, connected by circuit lines on a dark background, with AiDiy logo as the hub connecting all three, Japanese labels.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AiDiy のビデオ生成機能で作られた、Coding AI 比較動画へようこそ。",
          "naration_text": "こんにちは。今回の動画では、Claude Code、OpenAI Codex、Google Antigravity という 3 つのコーディング AI エージェントを、どの製品が上かではなく、どの利用シーンで何が得意かという視点で整理してお届けします。なお、この動画は AiDiy のビデオページ生成機能によって自動生成されました。シナリオ作成・画像生成・音声合成のすべてを AiDiy 自身が担当しています。",
          "audio": "audio/dlg_000_01_female.mp3",
          "duration_sec": 27.12
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "3 つの Coding Agent はそれぞれ異なる設計思想と得意シーンを持っています。",
          "naration_text": "Claude Code は Anthropic が開発した terminal ベースの agentic coding system です。OpenAI Codex は CLI からクラウドまで複数の作業面を持つ多面展開型の coding agent です。そして Google Antigravity は IDE と browser を横断する agent-first な開発プラットフォームです。それぞれ設計思想が異なり、得意とする利用シーンも違います。",
          "audio": "audio/dlg_000_02_male.mp3",
          "duration_sec": 22.104
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "勝敗ランキングではなく、用途別の使い分けを整理するのが今回のテーマです。",
          "naration_text": "今回の動画では、どれが一番優れているかを競わせるのではなく、terminal での深い作業が必要なとき、複数の作業面を使い分けたいとき、ブラウザを含めた視覚的な検証が必要なとき、それぞれどのツールが向いているかを整理していきます。判断の指針として、ぜひ最後までご覧ください。",
          "audio": "audio/dlg_000_03_female.mp3",
          "duration_sec": 19.488
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "動画の最後では AiDiy がこれらの agent をどう位置づけているかも解説します。",
          "naration_text": "そして動画の最後では、AiDiy がこれらのコーディング AI エージェントとどのような関係にあるかも解説します。AiDiy は 3 つのツールと競合する agent ではなく、複数の agent を日本語業務システムの開発基盤へつなげて試すための土台として設計されています。どうぞ楽しみにしていてください。",
          "audio": "audio/dlg_000_04_male.mp3",
          "duration_sec": 17.28
        }
      ],
      "duration_sec": 85.992
    },
    {
      "id": "scene_001",
      "title": "Claude Code — terminal とコードベース全体を把握するエージェント",
      "accent": "#c75b1a",
      "accent_soft": "rgba(199, 91, 26, 0.18)",
      "layout": "split",
      "kicker": "ANTHROPIC",
      "headline": "Claude Code\nterminal / codebase / tests\nexisting toolchain",
      "lead": "Anthropic の agentic coding system。terminal で動作し、コードベース全体を把握して複数ファイルを変更・テスト・コミットまで担う。",
      "image": "images/scene_001.png",
      "source_summary": "",
      "factual_bullets": [],
      "forbidden_elements": [
        "完全自動開発",
        "人間不要"
      ],
      "image_prompt": "A developer terminal interface showing Claude Code agent working on a large codebase, multiple files open, tests running, commit history visible, Anthropic branding, dark terminal aesthetic with orange accents.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Claude Code は Anthropic の agentic coding system で、terminal で動作します。",
          "naration_text": "まず Claude Code について見ていきましょう。Claude Code は Anthropic が開発した agentic coding system で、terminal 上で動作します。コードベース全体を読み込み、複数ファイルにまたがる変更を行い、テストを実行し、コミット可能なコードを届けるプロジェクトレベルのエージェントです。機能構築、デバッグ、コードベース理解、CI やリリースノートの自動化にも対応しています。",
          "audio": "audio/dlg_001_01_female.mp3",
          "duration_sec": 26.04
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "既存の terminal とツールチェーンにそのまま溶け込み、コードベース全体を把握します。",
          "naration_text": "Claude Code の大きな特徴は、開発者がすでに使っている terminal やツールチェーンにそのまま溶け込む設計です。新しい IDE を導入する必要はなく、今の terminal 環境でそのまま動かせます。コードベース全体の文脈を把握しながら動作するため、大規模なプロジェクトでの一貫した変更が得意です。MCP 経由で外部データソースや開発ツールと連携する機能も持っています。",
          "audio": "audio/dlg_001_02_male.mp3",
          "duration_sec": 23.448
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "検証はテスト実行や CI コマンドを使い、人間によるレビューと組み合わせて行います。",
          "naration_text": "変更の検証には、既存のテスト実行や CI コマンドをそのまま使います。ファイル変更やコマンド実行の許可管理、人間によるレビュー、プロジェクト固有のルールを明示することが重要とされています。エージェントの自律性を活かしながら、適切な人間の関与を組み合わせることで安心して使える環境を整えられます。",
          "audio": "audio/dlg_001_03_female.mp3",
          "duration_sec": 21.888
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "terminal で深くコードベースに向き合う開発スタイルで Claude Code が力を発揮します。",
          "naration_text": "まとめると、Claude Code は terminal を使い慣れた開発者が、大きなコードベースに対して深く関与しながら作業するシーンに向いています。Unix 的なワークフローとの親和性が高く、既存のツールチェーンをそのまま活かしながらエージェントの力を加えたいケースで力を発揮します。",
          "audio": "audio/dlg_001_04_male.mp3",
          "duration_sec": 15.888
        }
      ],
      "duration_sec": 87.264
    },
    {
      "id": "scene_002",
      "title": "OpenAI Codex — CLI / IDE / app / cloud の多面展開",
      "accent": "#10a37f",
      "accent_soft": "rgba(16, 163, 127, 0.18)",
      "layout": "split",
      "kicker": "OPENAI",
      "headline": "OpenAI Codex\nCLI / IDE / app / cloud\nsandbox / MCP",
      "lead": "OpenAI の software development 向け coding agent。CLI・IDE extension・web・desktop app・cloud など複数 surface を持ち、sandbox と MCP 連携で制御できる。",
      "image": "images/scene_002.png",
      "source_summary": "",
      "factual_bullets": [],
      "forbidden_elements": [
        "完全自動開発",
        "人間不要"
      ],
      "image_prompt": "A multi-surface interface showing OpenAI Codex working across CLI terminal, IDE extension, web app, and cloud environment simultaneously, green OpenAI branding, connected workflow diagram on dark background.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "OpenAI Codex は CLI から cloud まで複数 surface を持つ多面展開型の coding agent です。",
          "naration_text": "次は OpenAI Codex です。Codex は OpenAI の software development 向け coding agent で、CLI、IDE extension、web、desktop app、cloud など複数の作業面を持つ多面展開が特徴です。コード作成、未知のコードベースの理解、コードレビュー、デバッグ、開発タスクの自動化に使えると説明されています。",
          "audio": "audio/dlg_002_01_female.mp3",
          "duration_sec": 23.952
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Codex CLI は terminal の軽量 agent で、ローカルでコードを読み書きできます。",
          "naration_text": "Codex CLI は terminal 上の lightweight coding agent で、ローカルマシン上でコードを読み、変更し、コマンドを実行できます。approval モードや config による細かい制御が可能で、sandbox 環境での実行もサポートされています。CLI と IDE extension では MCP がサポートされており、外部ドキュメントや開発ツールへのアクセスを拡張できます。",
          "audio": "audio/dlg_002_02_male.mp3",
          "duration_sec": 22.296
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Codex app は複数の agent を並列に管理する command center として機能します。",
          "naration_text": "Codex app は複数の agent を並列に管理する command center として説明されています。クラウドで複数の agent を並列実行し、複数のタスクを同時に進めることができます。ローカルの CLI から始まり、必要に応じてクラウドやアプリへと作業規模を広げられる柔軟な設計です。",
          "audio": "audio/dlg_002_03_female.mp3",
          "duration_sec": 20.784
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "複数 surface と MCP 連携を活かしたいとき、Codex が一つの有力な選択肢になります。",
          "naration_text": "まとめると、Codex は OpenAI 系モデルをベースに CLI での軽量な terminal 作業から、IDE での統合、app での並列 agent 管理まで、状況に応じて作業面を選べます。MCP 連携による拡張性も高く、作業面を柔軟に使い分けながら開発規模を広げたいケースに向いています。surface ごとの役割差を意識することが大切です。",
          "audio": "audio/dlg_002_04_male.mp3",
          "duration_sec": 22.008
        }
      ],
      "duration_sec": 89.04
    },
    {
      "id": "scene_003",
      "title": "Google Antigravity — agent-first IDE と browser 検証",
      "accent": "#1a73e8",
      "accent_soft": "rgba(26, 115, 232, 0.18)",
      "layout": "split",
      "kicker": "GOOGLE",
      "headline": "Google Antigravity\nagent-first IDE / Manager\nbrowser control / artifacts",
      "lead": "Google の agentic development platform。Agent Manager と AI-powered IDE で、editor / terminal / browser を横断した視覚的・非同期な agent 管理を提供する。",
      "image": "images/scene_003.png",
      "source_summary": "",
      "factual_bullets": [],
      "forbidden_elements": [
        "完全自動開発",
        "人間不要"
      ],
      "image_prompt": "A futuristic AI-powered IDE showing Google Antigravity agent managing multiple sub-agents across editor, terminal, and browser panels, with screenshots and artifacts displayed, Google blue branding on dark background.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Google Antigravity は agent-first IDE と Agent Manager を持つ開発プラットフォームです。",
          "naration_text": "3つ目は Google Antigravity です。Antigravity は Google が開発した agentic development platform で、Agent Manager と AI-powered IDE を持ちます。agents が editor、terminal、browser にまたがって自律的に動き、tasks と artifacts の単位で高レベルに指示できる設計です。agent-first era を見据えたプロダクト形態として説明されています。",
          "audio": "audio/dlg_003_01_female.mp3",
          "duration_sec": 25.176
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "browser control で実際のブラウザを操作し、screenshots などの成果物を残せます。",
          "naration_text": "Antigravity の大きな特徴は browser control です。agent が実際のブラウザを操作しながら動作確認を行い、screenshots や browser recordings などの artifacts として結果を残します。task list、implementation plan、screenshots など、視覚的な成果物で進捗を確認できるため、何が行われたかを後から追いやすい設計になっています。",
          "audio": "audio/dlg_003_02_male.mp3",
          "duration_sec": 21.744
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "非同期でエージェントに任せ、artifacts で確認するスタイルが Antigravity の中心です。",
          "naration_text": "Antigravity は非同期インタラクションを前提にしています。agent が自律的に動いている間、開発者は別の作業を進め、完了後に artifacts で結果を確認するスタイルです。ローカル操作からのフィードバックや、knowledge base を使った自己改善の仕組みも説明されています。",
          "audio": "audio/dlg_003_03_female.mp3",
          "duration_sec": 19.08
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "browser を含めた視覚的な agent 管理が必要なシーンで Antigravity が力を発揮します。",
          "naration_text": "まとめると、Antigravity は IDE と terminal だけでなく browser も含めた環境で、複数の agent を視覚的に監督しながら進めたいシーンに向いています。agent の自律性が高い分、権限境界の設定、成果物の確認、破壊的操作の制御が特に重要です。視覚的な検証とタスクレベルの成果物管理が求められる場面で活用できます。",
          "audio": "audio/dlg_003_04_male.mp3",
          "duration_sec": 22.008
        }
      ],
      "duration_sec": 88.008
    },
    {
      "id": "scene_004",
      "title": "比較表 — 作業面・検証・連携・向いている用途",
      "accent": "#7c3aed",
      "accent_soft": "rgba(124, 58, 237, 0.18)",
      "layout": "table",
      "kicker": "COMPARISON",
      "headline": "3つの Coding Agent を\n利用シーン別に整理する",
      "lead": "主な作業面・実行スタイル・検証方法・連携手段・選び方の5軸で比較します。勝敗ランキングではなく、利用シーンに応じた選択の指針として整理します。",
      "image": "images/scene_004.png",
      "source_summary": "",
      "factual_bullets": [],
      "forbidden_elements": [
        "どれか一つが完全上位",
        "性能順位の断定"
      ],
      "image_prompt": "A clean comparison table showing Claude Code vs OpenAI Codex vs Google Antigravity across five dimensions: work surface, execution style, verification, integration, and best use cases, on dark background with color coding for each product.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "作業面・実行スタイル・検証・連携・用途の 5 軸で 3 つの Agent を整理します。",
          "naration_text": "ここで 3 つの Coding AI Agent を 5 つの軸で比較整理してみましょう。作業面、実行スタイル、検証方法、連携手段、そして向いている用途の観点から見ていきます。これは優劣のランキングではなく、利用シーンに応じた選択の指針として整理するものです。",
          "audio": "audio/dlg_004_01_female.mp3",
          "duration_sec": 19.032
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "作業面は terminal 中心・複数 surface・agent-first IDE と 3 者で異なります。",
          "naration_text": "作業面から見ると、Claude Code は terminal 中心、Codex は CLI から cloud までの複数 surface、Antigravity は agent-first IDE と Agent Manager という構成です。実行スタイルでは、Claude Code は既存 terminal に寄り添う、Codex はローカルから並列 agent 管理へ広げる、Antigravity は editor・terminal・browser を横断する視覚的・非同期管理を目指しています。",
          "audio": "audio/dlg_004_02_male.mp3",
          "duration_sec": 22.848
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "検証はテスト/CI・diffs/sandbox・artifacts と 3 者で方法が分かれています。",
          "naration_text": "検証方法も 3 者で異なります。Claude Code はテスト実行や CI コマンドを使い、Codex は diffs のレビューや sandbox、MCP を活用、Antigravity は artifacts・screenshots・browser recordings による task レベルの検証を使います。連携面では Claude Code と Codex は MCP 連携を明示し、Antigravity は artifacts と knowledge base を中心に説明しています。",
          "audio": "audio/dlg_004_03_female.mp3",
          "duration_sec": 26.952
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "terminal 重視・多 surface 展開・browser 視覚検証の 3 シーンで用途が分かれます。",
          "naration_text": "用途の選び方をまとめます。terminal で深くコードベースと向き合うなら Claude Code、OpenAI 系モデルをベースに CLI・IDE・app・cloud を横断したいなら Codex、browser も含めた視覚的な検証と複数 agent の監督が必要なら Antigravity という整理が一つの指針になります。それぞれの強みを理解して、自分のワークフローに合う選択をすることが大切です。",
          "audio": "audio/dlg_004_04_male.mp3",
          "duration_sec": 21.432
        }
      ],
      "duration_sec": 90.264
    },
    {
      "id": "scene_005",
      "title": "AiDiy — 日本語業務テンプレート + 15 MCP + Code AI の受け皿",
      "accent": "#059669",
      "accent_soft": "rgba(5, 150, 105, 0.18)",
      "layout": "split",
      "kicker": "AIDIY",
      "headline": "AiDiy\n日本語業務テンプレート\n複数 agent を試す実験基盤",
      "lead": "AiDiy は Claude Code / Codex / Antigravity と競合する単一 agent ではなく、複数 AI / Code CLI / MCP / Avatar を束ねる日本語ファーストの業務システム開発テンプレート兼実験基盤。",
      "image": "images/scene_005.png",
      "source_summary": "",
      "factual_bullets": [],
      "forbidden_elements": [
        "完全自動開発",
        "商用製品として公式リリースの断言"
      ],
      "image_prompt": "AiDiy system architecture showing FastAPI backend, Vue 3 frontend, 15 MCP servers, Electron avatar, and multiple Code AI agents (Claude, Codex, Antigravity, Copilot) all connected to a central hub, Japanese labels, green accent on dark background.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AiDiy はこれら 3 つと競合しない日本語ファーストの業務システム開発テンプレートです。",
          "naration_text": "ここで AiDiy の立ち位置を整理しましょう。AiDiy は Claude Code・Codex・Antigravity と競合する単一の coding agent ではありません。FastAPI と SQLite と Vue 3 をベースにした日本語ファーストの業務システム開発テンプレートであり、複数の AI・Code CLI・MCP・Avatar を束ねる実験基盤として設計されています。",
          "audio": "audio/dlg_005_01_female.mp3",
          "duration_sec": 23.76
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Code AI 設定で Claude Code や Codex など複数の agent を切り替えて試せます。",
          "naration_text": "AiDiy の AI コアには Code AI 設定があり、claude_sdk、claude_cli、copilot_cli、codex_cli、antigravity_cli、opencode_cli、aidiy_hermes を Code AI1 から Code AI6 として割り当てられます。つまり AiDiy は、どの agent を使うかを選ぶ場所ではなく、複数の agent を業務システム・Web UI・音声・画像・MCP とつなげて試す土台として機能します。",
          "audio": "audio/dlg_005_02_male.mp3",
          "duration_sec": 22.584
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "15 の MCP サーバーが Chrome 操作から画像生成まで HTTP API で利用できます。",
          "naration_text": "AiDiy には 15 個の MCP サーバーが組み込まれており、Chrome ブラウザ操作、デスクトップキャプチャ、SQLite・PostgreSQL 確認、ログ確認、AI 画像生成、AI 動画生成、音声認識、テキスト音声合成、OBS Studio 制御、FFmpeg 実行、コードエージェント実行、Chat LLM 実行などを HTTP API として利用できます。",
          "audio": "audio/dlg_005_03_female.mp3",
          "duration_sec": 24.624
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "日本語識別子を全レイヤーで使う設計が業務ドメインとコードの対応を直感的にします。",
          "naration_text": "AiDiy のもう一つの特徴は日本語ファースト設計です。テーブル名、カラム名、API パス、JSON キー、Vue コンポーネント名、Router パスまで全レイヤーで日本語識別子を使います。日本語話者が業務ドメインとコードを直接対応づけられることを優先した設計で、3D アバター UI と組み合わせた実験基盤として活用できます。",
          "audio": "audio/dlg_005_04_male.mp3",
          "duration_sec": 21.312
        }
      ],
      "duration_sec": 92.28
    },
    {
      "id": "scene_999",
      "title": "まとめ — 選び方と AiDiy で試す誘導",
      "accent": "#1a6ea0",
      "accent_soft": "rgba(26, 110, 160, 0.18)",
      "layout": "hero",
      "kicker": "SUMMARY",
      "headline": "利用シーンで選ぶ\nCoding AI Agent",
      "lead": "terminal で深く回すなら Claude Code、複数 surface と MCP 連携なら Codex、browser 検証と複数 agent 管理なら Antigravity。AiDiy でそれらを日本語業務システムにつなげて試そう。",
      "image": "images/scene_999.png",
      "source_summary": "",
      "factual_bullets": [],
      "forbidden_elements": [
        "どれか一つが完全上位",
        "完全自動開発"
      ],
      "image_prompt": "A closing scene showing the three coding agents and AiDiy logo together, with a call to action for viewers to try AiDiy, warm gradient lighting, Japanese text overlay saying 'AiDiy で試してみよう', subscribe button visible.",
      "dialogue": [
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "利用シーンで選ぶ 3 つの Coding AI Agent の整理をおさらいします。",
          "naration_text": "今回の動画で整理した 3 つの Coding AI Agent の選び方をおさらいします。terminal で既存のツールチェーンに寄り添いながらコードベース全体を深く扱いたいなら Claude Code、OpenAI 系モデルをベースに CLI・IDE・app・cloud を状況に応じて使い分けたいなら Codex、IDE と browser を横断した視覚的な検証と複数 agent の非同期管理が必要なら Antigravity が指針となります。",
          "audio": "audio/dlg_999_01_male.mp3",
          "duration_sec": 21.648
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "どれが上かではなく、自分のワークフローと用途に合うツールを選ぶことが大切です。",
          "naration_text": "3 つのツールは互いに優劣をつけるより、それぞれ異なる得意シーンを持つと考えるほうが実用的です。ワークフローの種類、チームの規模、検証方法の好み、利用するモデル環境によって、向いているツールは変わります。自分の開発スタイルに合うものを実際に試してみることが一番の近道です。",
          "audio": "audio/dlg_999_02_female.mp3",
          "duration_sec": 20.52
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "AiDiy を使えば複数の agent を日本語業務システムとつなげて比較・検証できます。",
          "naration_text": "AiDiy は Code AI 設定で複数の coding agent を切り替えながら、日本語業務システムの開発や MCP との連携を試せる実験基盤です。自分でビデオを自動生成したり、3D アバターに agent を喋らせたり、業務テンプレートに agent を組み込んだりと、さまざまな実験ができます。今回のような比較動画も AiDiy で自分で作れます。",
          "audio": "audio/dlg_999_03_male.mp3",
          "duration_sec": 21.0
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "この動画は AiDiy 製。チャンネル登録して、あなたも AiDiy で動画を作ってみよう！",
          "naration_text": "最後までご覧いただき、ありがとうございました。この動画は AiDiy のビデオページ生成機能によって自動生成されています。シナリオ作成から画像生成、音声合成まで AiDiy が担当しています。ぜひチャンネル登録をして、次の AiDiy 動画もお楽しみに。AiDiy を使えば、あなたも今回のような比較・解説ビデオを自分で作れます。AI と一緒に、業務システムも動画も自分で作る楽しさをぜひ体験してみてください。",
          "audio": "audio/dlg_999_04_female.mp3",
          "duration_sec": 30.024
        }
      ],
      "duration_sec": 93.192
    }
  ],
  "total_duration_sec": 626.04
};
