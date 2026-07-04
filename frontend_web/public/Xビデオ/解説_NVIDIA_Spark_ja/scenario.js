window.SCENARIO = {
  "project_name": "解説_NVIDIA_Spark_ja",
  "version": "duo-v2",
  "title": "NVIDIA Spark — GB10 Grace Blackwell が切り拓くローカル AI マシンの新時代",
  "assets_policy": {
    "male_avatar": "../_vrm/VRM_male.vrm",
    "female_avatar": "../_vrm/VRM_female.vrm",
    "tts_male": "edge:male",
    "tts_female": "edge:female",
    "audio_output_dir": "frontend_web/public/Xビデオ/解説_NVIDIA_Spark_ja/audio"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "イントロ — NVIDIA Spark とは",
      "accent": "#76b900",
      "accent_soft": "rgba(118, 185, 0, 0.18)",
      "layout": "hero",
      "kicker": "NVIDIA SPARK",
      "headline": "GB10 Grace Blackwell が切り拓く\nローカル AI マシンの新時代",
      "lead": "RTX Spark と DGX Spark — 2 つの Spark ファミリーが AI をローカルで動かす世界を変えます。",
      "image": "images/scene_000.png",
      "source_summary": "NVIDIA Spark ファミリー。RTX Spark は薄型軽量 Windows PC 向けスーパーチップ（1PFLOP/128GB統合メモリ）。DGX Spark は GB10 Grace Blackwell 搭載デスクトップ AI スパコン（最大2,000億パラメータ対応）。この動画は AiDiy のビデオページ生成機能で自動生成。",
      "factual_bullets": [
        "RTX Spark スーパーチップ: 1PFLOP(FP4) / Blackwell GPU 最大6,144コア / Arm CPU 最大20コア / 統合メモリ最大128GB",
        "DGX Spark: GB10 Grace Blackwell スーパーチップ / Cortex-X925×10 + A725×10 / 最大2,000億パラメータ対応",
        "Microsoft と NVIDIA が共同発表。搭載 Windows PC は秋発売予定",
        "AiDiy + ローカル LLM をクラウド非依存で動かす AI 実行基盤として活用可能",
        "この動画は AiDiy のビデオページ生成機能で自動生成"
      ],
      "forbidden_elements": [
        "完全な AGI 実現・人間の完全代替を示唆する表現",
        "記事に記載のない価格・発売日の断定",
        "RTX Spark と DGX Spark の混同"
      ],
      "image_prompt": "Wordless cinematic opener: a thin AI laptop silhouette and a compact desktop AI workstation silhouette connected by green energy streams, with abstract chip patterns and local network lines. No readable text, no numbers, no dates, no brand logos, no UI labels.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "この動画は AiDiy のビデオページ生成機能で自動生成されました。NVIDIA Spark の世界へようこそ。",
          "naration_text": "こんにちは。今回の動画では、NVIDIA の新しい Spark ファミリー、RTX Spark と DGX Spark を中心に、ローカルで動く高性能 AI マシンの新時代を解説していきます。なお、このシナリオ作成・画像生成・音声合成はすべて、AiDiy のビデオページ生成機能によって自動生成されました。NVIDIA と Microsoft が共同で生み出した Spark の世界へ、一緒に踏み込んでみましょう。",
          "audio": "audio/dlg_000_01_female.mp3",
          "duration_sec": 27.624
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "RTX Spark と DGX Spark という 2 つの製品形態が Spark ファミリーを構成します。",
          "naration_text": "Spark ファミリーには大きく 2 つの製品形態があります。ひとつは薄型軽量の Windows ノート PC やコンパクトデスクトップ向けスーパーチップ「RTX Spark」、もうひとつはデスクトップ型のパーソナル AI スーパーコンピューター「DGX Spark」です。同じ Spark ファミリーですが、ターゲットユーザーと用途が異なる独立した製品として位置づけられています。",
          "audio": "audio/dlg_000_02_male.mp3",
          "duration_sec": 21.024
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "RTX Spark は AI 性能 1 ペタフロップスと業界最高クラスの電力効率を薄型 PC に凝縮したチップです。",
          "naration_text": "RTX Spark スーパーチップは、FP4 精度で 1 ペタフロップスという AI 演算性能を薄型軽量の Windows PC に搭載できるよう設計されています。Blackwell GPU コアを最大 6,144 基、高効率の Arm CPU を最大 20 コア、統合メモリを最大 128GB 搭載し、業界最高クラスの電力効率とともに、Windows PC の在り方そのものを再定義しようとしています。",
          "audio": "audio/dlg_000_03_female.mp3",
          "duration_sec": 28.368
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "DGX Spark は AI 研究者・データサイエンティスト向けのデスクトップ型パーソナル AI スパコンです。",
          "naration_text": "一方の DGX Spark は、AI 研究者やデータサイエンティスト向けに設計されたデスクトップ型パーソナル AI スーパーコンピューターです。中核に NVIDIA GB10 Grace Blackwell スーパーチップを搭載し、最大 2,000 億パラメータの言語・ビジョン・マルチモーダルモデルの学習と推論を実行できます。エンタープライズレベルの AI 開発が、個人のデスクで可能になります。",
          "audio": "audio/dlg_000_04_male.mp3",
          "duration_sec": 22.176
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "この動画ではスペック・Windows PC の変化・DGX Spark・用途・AiDiy 活用まで順に解説します。",
          "naration_text": "この動画では、RTX Spark スーパーチップの詳細スペック、Spark を搭載した新しい Windows PC の姿、DGX Spark のパワーと可能性、用途別の活用価値、そして AiDiy をローカルで動かす実践的な活用シナリオまでを順番に見ていきます。ローカル AI の新時代がどんな形になるのか、一緒に確認していきましょう。",
          "audio": "audio/dlg_000_05_female.mp3",
          "duration_sec": 22.872
        }
      ],
      "duration_sec": 122.064
    },
    {
      "id": "scene_001",
      "title": "RTX Spark スーパーチップのスペック",
      "accent": "#76b900",
      "accent_soft": "rgba(118, 185, 0, 0.18)",
      "kicker": "RTX SPARK CHIP",
      "headline": "1 ペタフロップ・128GB 統合メモリ\nRTX Spark スーパーチップの実力",
      "lead": "Blackwell GPU 最大6,144コア、Arm CPU 最大20コア、1PFLOP（FP4）の AI 性能を1チップに凝縮。",
      "image": "images/scene_001.png",
      "source_summary": "RTX Spark スーパーチップ仕様: AI 性能1PFLOP(FP4) / Blackwell RTX コア最大6,144基 / Arm CPU 最大20コア（高効率）/ 統合メモリ最大128GB。WPS(Workload Profile Scheduling)で20コアを効率配分、MPTF(Microsoft Power and Thermal Framework)で電力・温度管理。CUDA ネイティブ対応。Windows ML 経由で TensorRT 利用可。",
      "factual_bullets": [
        "AI 性能: 1 ペタフロップス（FP4）",
        "GPU: Blackwell RTX コア 最大6,144基",
        "CPU: Arm 系 高効率コア 最大20コア",
        "統合メモリ: 最大128GB",
        "WPS（Workload Profile Scheduling）で20コアに効率配分",
        "MPTF（Microsoft Power and Thermal Framework）で電力・温度管理",
        "CUDA ネイティブ対応 / Windows ML 経由で TensorRT 利用可"
      ],
      "forbidden_elements": [
        "完全な AGI 実現を示唆する表現",
        "記事に記載のない価格・消費電力数値の断定",
        "RTX Spark と DGX Spark の混同"
      ],
      "image_prompt": "Wordless technical hero image of a glowing AI system-on-chip on a dark circuit board, with abstract GPU/CPU/memory regions represented by geometric light blocks. No readable text, no numbers, no labels, no brand logos.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "RTX Spark は 1PFLOP（FP4）の AI 演算性能を薄型軽量 PC に搭載できるよう設計されたチップです。",
          "naration_text": "RTX Spark スーパーチップの中核は、FP4 精度で 1 ペタフロップスという AI 演算性能です。これを実現するのが NVIDIA Blackwell アーキテクチャの RTX コア、最大 6,144 基です。最新の AI モデルの推論から画像生成まで、あらゆる AI タスクをノート PC の中でクラウドに頼らず高速処理できます。",
          "audio": "audio/dlg_001_01_female.mp3",
          "duration_sec": 23.112
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Arm CPU は最大 20 コアで、WPS がワークロードを動的配分し MPTF が電力と温度を統合管理します。",
          "naration_text": "CPU 側には Arm 系の高効率コアを最大 20 基搭載しています。Microsoft との共同開発による WPS（Workload Profile Scheduling）がこの 20 コアへのワークロード配分を動的に最適化します。さらに MPTF（Microsoft Power and Thermal Framework）が電力と温度を統合管理し、薄型ボディで最大限の性能を引き出しながら発熱と消費電力を抑えています。",
          "audio": "audio/dlg_001_02_male.mp3",
          "duration_sec": 23.424
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "統合メモリ最大 128GB で CPU と GPU が同じメモリ空間を高速共有、大規模モデルもローカルで動かせます。",
          "naration_text": "統合メモリ最大 128GB も大きなポイントです。CPU と GPU が同一のメモリプールを共有するため、データのコピーなしに両者が高速でアクセスできます。従来の PC では GPU の VRAM が数十 GB に限られていましたが、RTX Spark では 128GB という広大なメモリ空間が AI タスクに活用でき、より大規模なモデルをローカルで動かせるようになります。",
          "audio": "audio/dlg_001_03_female.mp3",
          "duration_sec": 27.456
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "GPU と CPU が同じ CUDA 環境で動き、AI 開発コードをクラウドから薄型 PC にそのまま移行できます。",
          "naration_text": "開発者にとって重要なのが CUDA ネイティブ対応です。クラウドの NVIDIA GPU で使っていたのと同じ CUDA 環境がそのまま動くため、開発環境を切り替える手間がありません。さらに Windows ML 経由で TensorRT を利用できるため、推論の高速化もそのまま適用できます。データセンターで作ったコードを薄型 PC にそのまま持ち込んで実行できます。",
          "audio": "audio/dlg_001_04_male.mp3",
          "duration_sec": 21.984
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "1 ペタフロップの AI 性能と業界最高クラスの電力効率を両立した、まったく新しいカテゴリーのチップです。",
          "naration_text": "Microsoft と NVIDIA は RTX Spark を「史上最もパワフルで効率的な薄型軽量 Windows PC」を実現するチップと表現しています。AI 性能と電力効率というかつてトレードオフだった 2 つを同時に達成した点が革新的です。1 ペタフロップスの AI 性能を持ちながら、モバイル機器に必要な電力効率も業界最高クラスを実現しました。",
          "audio": "audio/dlg_001_05_female.mp3",
          "duration_sec": 25.512
        }
      ],
      "duration_sec": 121.488
    },
    {
      "id": "scene_002",
      "title": "Windows PC の再定義 — Arm 互換・WSL・各社秋発売",
      "accent": "#0078d4",
      "accent_soft": "rgba(0, 120, 212, 0.18)",
      "kicker": "WINDOWS REIMAGINED",
      "headline": "Surface Laptop Ultra はじめ各社秋発売\nPrism・WSL・OpenShell で Windows が変わる",
      "lead": "薄型軽量で Arm 上でクリエイティブツールがネイティブ動作、Linux AI エコシステムとも連携します。",
      "image": "images/scene_002.png",
      "source_summary": "RTX Spark 搭載 Windows PC: Surface Laptop Ultra / ASUS ProArt P16・P14 / Dell XPS 16 Creator Edition / HP OmniBook Ultra 16・OmniBook X 14 / Lenovo Yoga Pro 9n / MSI Prestige N16 Flip AI+ 秋発売予定。Blender/DaVinci Resolve/Photoshop/Premiere が Arm 上でネイティブ動作。Prism エミュレータ強化で x86 互換向上。WSL 経由で Linux AI エコシステムへ接続。NVIDIA OpenShell 統合でエージェント実行の安全性確保。",
      "factual_bullets": [
        "秋発売予定: Surface Laptop Ultra / ASUS ProArt P16・P14 / Dell XPS 16 Creator Edition / HP OmniBook Ultra 16・X14 / Lenovo Yoga Pro 9n / MSI Prestige N16 Flip AI+",
        "Blender・DaVinci Resolve・Photoshop・Premiere が Arm 上でネイティブ動作",
        "Prism エミュレータ強化で x86 アプリの互換性向上",
        "WSL 経由で Linux AI エコシステムへ接続",
        "NVIDIA OpenShell 統合でエージェント実行時の安全性確保"
      ],
      "forbidden_elements": [
        "完全な AGI 実現を示唆する表現",
        "記事に記載のない価格・具体的発売日の断定"
      ],
      "image_prompt": "Wordless collage of slim Windows-class laptops and a local Linux development terminal visualized as abstract code-like light patterns, with blue and green accents. No readable text, no dates, no product logos, no app icons, no UI labels.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "RTX Spark ?? Windows PC ? 2026 ?????????",
          "naration_text": "RTX Spark スーパーチップを搭載した Windows PC は 2026 年秋の発売が予定されています。Microsoft の Surface Laptop Ultra を筆頭に、ASUS ProArt P16 と P14、Dell XPS 16 Creator Edition、HP OmniBook Ultra 16 と OmniBook X 14、Lenovo Yoga Pro 9n、MSI Prestige N16 Flip AI+ といった主要メーカーが参入します。デスクトップ PC についても、コンパクト設計で 24 時間稼働可能な製品が提供予定です。",
          "audio": "audio/dlg_002_01_female.mp3",
          "duration_sec": 34.032
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "????????????? Arm ?????????????",
          "naration_text": "クリエイター向けに重要な点として、Blender、DaVinci Resolve、Photoshop、Premiere といった定番ツールが Arm アーキテクチャ上でネイティブ動作します。これまで Arm PC の課題だったソフトウェア互換性が大きく改善されています。ハードウェアエンコードは 4:2:2 品質と AV1 コーデックに対応しており、映像制作ワークフローもネイティブな速度で動かせます。",
          "audio": "audio/dlg_002_02_male.mp3",
          "duration_sec": 21.792
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Prism エミュレータ強化で x86 アプリの互換性が向上し、既存ツールも並行して使えます。",
          "naration_text": "Arm ネイティブ対応が進む一方で、既存の x86 アプリも Prism エミュレータの強化によって動かせます。Microsoft は Prism の互換性と性能を継続的に改善しており、移行期間中も手持ちのツールを使い続けられます。Arm ネイティブ化が完了するまでの橋渡し役として、実用上の支障を最小限に抑えています。",
          "audio": "audio/dlg_002_03_female.mp3",
          "duration_sec": 22.512
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Windows から AI エコシステムへのアクセスが、WSL と OpenShell の統合でさらに広がります。",
          "naration_text": "Linux の AI エコシステムへのアクセスも WSL（Windows Subsystem for Linux）経由で実現しています。PyTorch や Hugging Face など Linux 向けの AI ライブラリを Windows 上から直接使えます。また NVIDIA OpenShell との統合により、AI エージェントがローカルで実行される際の安全性が確保されます。Windows が本格的な AI 開発プラットフォームとして大きく進化しています。",
          "audio": "audio/dlg_002_04_male.mp3",
          "duration_sec": 23.616
        }
      ],
      "duration_sec": 101.952
    },
    {
      "id": "scene_003",
      "title": "DGX Spark — GB10 Grace Blackwell のデスクトップ AI スパコン",
      "accent": "#00a67e",
      "accent_soft": "rgba(0, 166, 126, 0.18)",
      "kicker": "DGX SPARK",
      "headline": "Cortex-X925×10 + A725×10\n最大 2,000 億パラメータのデスクトップ AI スパコン",
      "lead": "AI 研究者・データサイエンティスト向け。GB10 Grace Blackwell が個人の AI 開発を最前線へ引き上げます。",
      "image": "images/scene_003.png",
      "source_summary": "NVIDIA DGX Spark: GB10 Grace Blackwell スーパーチップ搭載。Arm Cortex-X925×10（高性能）+ Cortex-A725×10（汎用）の20コア構成。最大2,000億パラメータの言語・ビジョン・マルチモーダルモデルの学習・推論に対応。AI研究者・データサイエンティスト・学生向けのパーソナルAIスパコン。デスクトップでエンタープライズレベルの AI 開発が可能。",
      "factual_bullets": [
        "中核チップ: NVIDIA GB10 Grace Blackwell スーパーチップ",
        "CPU: Arm Cortex-X925 ×10（高性能コア）+ Cortex-A725 ×10（汎用コア）= 20コア",
        "最大2,000億パラメータのモデルの学習・推論に対応",
        "言語モデル・ビジョンモデル・マルチモーダルモデルに対応",
        "AI 研究者・データサイエンティスト・個人研究者・学生向け"
      ],
      "forbidden_elements": [
        "完全な AGI 実現・人間の完全代替を示唆する表現",
        "記事に記載のない価格・消費電力・仕様の断定"
      ],
      "image_prompt": "Wordless compact desktop AI supercomputer in a research lab, translucent side panel with a glowing chip, monitors showing abstract graphs and neural network shapes without readable text. No numbers, no labels, no logos.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "DGX Spark ? GB10 ????????? AI ???????",
          "naration_text": "DGX Spark は、AI 研究者やデータサイエンティスト向けに設計された、デスクトップ型のパーソナル AI スーパーコンピューターです。その中核を担うのが NVIDIA GB10 Grace Blackwell スーパーチップです。Grace Blackwell アーキテクチャが持つ AI 処理能力をデスクトップサイズに凝縮したマシンで、エンタープライズレベルの AI 開発が自分のデスク上で実現します。",
          "audio": "audio/dlg_003_01_female.mp3",
          "duration_sec": 25.08
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "20 コアの Arm ハイブリッド CPU が AI 計算タスクと汎用処理を効率よく分担します。",
          "naration_text": "GB10 の CPU 部分は Arm アーキテクチャで構成されています。高性能コアの Cortex-X925 を 10 基と、汎用コアの Cortex-A725 を 10 基、合計 20 コアのハイブリッド設計です。高性能コアが重い AI 計算タスクを担い、汎用コアが日常的なシステム処理を効率よく処理します。この組み合わせが、AI 学習から一般的な開発作業まで幅広いワークロードをカバーします。",
          "audio": "audio/dlg_003_02_male.mp3",
          "duration_sec": 25.56
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "最大 2,000 億パラメータの言語・ビジョン・マルチモーダルモデルの学習と推論に対応しています。",
          "naration_text": "DGX Spark の驚異的な点は、最大 2,000 億パラメータという大規模なモデルの学習と推論をデスクトップで実行できることです。テキスト生成の言語モデル、画像認識のビジョンモデル、そしてテキストと画像を組み合わせたマルチモーダルモデルまで幅広い種類の AI モデルに対応しています。これまでクラウドや大型データセンターが必要だった規模の AI が、手元で動く時代になりました。",
          "audio": "audio/dlg_003_03_female.mp3",
          "duration_sec": 26.664
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "個人研究者や学生にも最先端 AI 開発へのアクセスを広げ、AI 開発の民主化を実現します。",
          "naration_text": "DGX Spark がもたらす最大の意義は AI 開発の民主化です。これまで大学の研究室や大企業のデータセンターにしかなかったエンタープライズレベルの AI 計算資源が、個人研究者や学生でも手元に置けるようになります。自分のデスクで最先端の AI モデルを学習・ファインチューニング・推論できる環境は、AI 研究の速度と範囲を根本から変える可能性を持っています。",
          "audio": "audio/dlg_003_04_male.mp3",
          "duration_sec": 23.184
        }
      ],
      "duration_sec": 100.488
    },
    {
      "id": "scene_004",
      "title": "用途別の価値 — クリエイター・開発者・ゲーマー",
      "accent": "#ff6b35",
      "accent_soft": "rgba(255, 107, 53, 0.18)",
      "kicker": "USE CASES",
      "headline": "クリエイター・開発者・ゲーマー\nそれぞれに応える CUDA ネイティブの力",
      "lead": "リアルタイム 3D からローカル AI 推論、レイトレーシングまで、CUDA ネイティブが活きる 3 つの顔。",
      "image": "images/scene_004.png",
      "source_summary": "RTX Spark の用途別価値: クリエイター（リアルタイム3Dレンダリング、4:2:2エンコード、AV1）、開発者（最新モデルのローカルプロトタイプ作成・ファインチューニング・推論、CUDA ネイティブ）、ゲーマー（レイトレーシング、DLSS、Reflex、G-SYNC）。コンパクトデスクトップは24時間稼働可能。",
      "factual_bullets": [
        "クリエイター: リアルタイム3Dレンダリング、4:2:2 ハードウェアエンコード、AV1 コーデック対応",
        "開発者: 最新モデルのローカルプロトタイプ作成・ファインチューニング・推論、CUDA ネイティブ",
        "ゲーマー: レイトレーシング、DLSS、Reflex、G-SYNC 対応",
        "コンパクトデスクトップは24時間稼働設計"
      ],
      "forbidden_elements": [
        "完全な AGI 実現を示唆する表現",
        "記事に記載のない具体的なベンチマーク数値の断定"
      ],
      "image_prompt": "Wordless triptych visual for creator, developer, and gamer workflows: 3D rendering scene, AI model workspace, ray-traced game environment, all connected to a central glowing chip. No readable text, no numbers, no logos, no UI labels.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Spark はクリエイターに 3D レンダリング・4:2:2 エンコード・AV1 を薄型ノート PC で提供します。",
          "naration_text": "クリエイターにとって RTX Spark は、Blackwell アーキテクチャのリアルタイム 3D レンダリング性能と、4:2:2 品質のハードウェアエンコード、AV1 コーデック対応を薄型ノート PC に持ち込んでくれます。Blender や DaVinci Resolve、Photoshop、Premiere が Arm 上でネイティブに動作するため、ポストプロダクション作業を移動中のラップトップでも高速に行えます。",
          "audio": "audio/dlg_004_01_female.mp3",
          "duration_sec": 24.384
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "開発者向けには最新モデルのローカルプロトタイプ作成・ファインチューニング・推論が CUDA ネイティブで行えます。",
          "naration_text": "開発者向けの価値は、ローカル環境での AI 開発サイクルを大幅に加速できることです。最新の大規模言語モデルのプロトタイプ作成、ファインチューニング、推論をすべてローカルで実行できます。CUDA ネイティブ対応なので、クラウドの NVIDIA GPU 向けに書いたコードがそのまま動き、API コストもデータのクラウド転送も不要になります。",
          "audio": "audio/dlg_004_02_male.mp3",
          "duration_sec": 20.76
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "ゲーマー向けにはレイトレーシング・DLSS・Reflex・G-SYNC が薄型 Windows PC で楽しめます。",
          "naration_text": "ゲーマーにとっては、Blackwell アーキテクチャのレイトレーシング、超解像技術 DLSS、低遅延技術 Reflex、ティアリングを防ぐ G-SYNC という RTX GPU の定番機能がすべて薄型ノート PC で利用できます。高性能ゲーミングとビジネス・クリエイティブ用途を 1 台でこなせる、新しいジャンルのマシンが生まれています。",
          "audio": "audio/dlg_004_03_female.mp3",
          "duration_sec": 22.512
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "コンパクトデスクトップは 24 時間稼働設計で、AI 推論サーバーとしても常時活用できます。",
          "naration_text": "デスクトップ版は小型でありながら 24 時間稼働に対応した設計になっています。これにより、自宅や研究室で常時動き続ける AI 推論サーバーとして使えます。クラウドサービスの月額費用をかけずに、自分専用の AI バックエンドをデスクに置ける。開発者やリサーチャーにとって、これは大きなコスト削減とデータプライバシーの両立を意味します。",
          "audio": "audio/dlg_004_04_male.mp3",
          "duration_sec": 21.792
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AI 開発・クリエイティブ制作・ゲームを 1 チップでカバーする、まったく新しいオールインワン設計です。",
          "naration_text": "RTX Spark が革新的なのは、AI 性能・グラフィックス・クリエイティブ処理を 1 つのチップに統合した点です。これまで用途別に異なるマシンが必要だったものが、1 台の薄型軽量 PC に集約されています。クリエイターであり開発者であり、趣味でゲームも楽しむ現代のパワーユーザーにとって、理想的なオールインワン ソリューションといえます。",
          "audio": "audio/dlg_004_05_female.mp3",
          "duration_sec": 23.568
        }
      ],
      "duration_sec": 113.016
    },
    {
      "id": "scene_005",
      "title": "AiDiy 活用シナリオ — Spark でローカル AI を動かす",
      "accent": "#6c5ce7",
      "accent_soft": "rgba(108, 92, 231, 0.18)",
      "kicker": "AIDIY + SPARK",
      "headline": "Spark × AiDiy で実現する\nクラウド非依存のローカル AI 環境",
      "lead": "128GB 統合メモリと 1PFLOP の性能を持つ Spark で AiDiy + ローカル LLM を 1 台で完結させる。",
      "image": "images/scene_005.png",
      "source_summary": "AiDiy + Spark 活用シナリオ: 128GB 統合メモリと1ペタフロップ級の性能で、Ollama 等のローカル LLM と AiDiy（backend_server 2サーバー + backend_tools 15 MCP + frontend_web + frontend_avatar）を1台で稼働。CHAT_AI_NAME/LIVE_AI_NAME/CODE_AI1_NAME〜CODE_AI6_NAME にローカルモデルを設定。データをクラウドに出さずに AIコア・Code AI を低レイテンシで利用可能。",
      "factual_bullets": [
        "AiDiy: FastAPI + SQLAlchemy + SQLite (Python 3.13) + Vue 3 + Vite の 2サーバー構成（8091/9098）",
        "backend_tools: 15 MCP サーバーを集約（コードエージェント・画像生成・TTS など）",
        "CHAT_AI_NAME / LIVE_AI_NAME / CODE_AI1〜6_NAME にローカルモデルを指定可能",
        "Ollama 等でローカル LLM を稼働させ AiDiy AI コアと連携",
        "データがクラウドに出ない、低レイテンシ、API コスト不要"
      ],
      "forbidden_elements": [
        "AiDiy が商用製品として公式リリースされているかのような断言",
        "具体的な動作保証・SLA・ベンチマーク数値の断定",
        "完全な AGI 実現を示唆する表現"
      ],
      "image_prompt": "Wordless local AI architecture visual: one Spark-powered machine at center, private local network nodes and avatar interface shapes around it, all connections staying inside a room-scale local environment. No cloud icons, no readable text, no numbers, no labels, no logos.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Spark で AiDiy とローカル LLM を 1 台でクラウド非依存に動かせます。",
          "naration_text": "RTX Spark や DGX Spark の 128GB 統合メモリと 1 ペタフロップ以上の AI 性能があれば、AiDiy の全サービスとローカル LLM を 1 台で動かすことができます。AiDiy は FastAPI バックエンド 2 サーバー、15 の MCP サーバーを集めた TOOL HUB、Vue 3 の Web UI、Electron 対応の 3D アバターが連携するフルスタック環境です。Ollama などでローカル LLM を立ち上げれば、クラウドに一切依存しない AI 環境が完成します。",
          "audio": "audio/dlg_005_01_female.mp3",
          "duration_sec": 31.224
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "15 MCP と Avatar を含む AiDiy を 1 台の Spark で完全ローカルに動かすことができます。",
          "naration_text": "AiDiy の設定ファイルには CHAT_AI_NAME、LIVE_AI_NAME、そして CODE_AI1_NAME から CODE_AI6_NAME という AI の割り当てキーがあります。ここにローカルで動いている Ollama のモデル名や claude_sdk、copilot_cli などのローカル対応エンジンを指定するだけで、チャット AI、音声 AI、コード支援 AI がすべてローカルで動きます。データが外に出ない、低レイテンシ、API コスト不要の環境が整います。",
          "audio": "audio/dlg_005_02_male.mp3",
          "duration_sec": 25.632
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "ローカル LLM を指定するだけで、コードエージェントから動画生成まですべてクラウドなしで動きます。",
          "naration_text": "AiDiy の backend_tools には、コードエージェント実行、AI 画像生成、音声合成、Chrome 自動操作、OBS 録画制御、ffmpeg 動画処理など 15 の MCP サーバーが集約されています。Spark のローカル AI 実行基盤と組み合わせることで、これらの機能がすべてクラウドなしに動きます。この動画自体も AiDiy の自動化パイプラインで生成されていますが、Spark があればそのパイプライン全体をローカルで実行できます。",
          "audio": "audio/dlg_005_03_female.mp3",
          "duration_sec": 28.392
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "データ外部流出なし・低レイテンシ・API コスト不要の三拍子を Spark + AiDiy の組み合わせで実現できます。",
          "naration_text": "Spark の高性能とローカル実行の利点を整理すると、まずデータがクラウドに送られないため機密情報も安心して扱えます。ネットワーク通信が不要なため応答速度も速くなります。そして API の課金がなくなるため、開発・実験のコストが大幅に下がります。RTX Spark や DGX Spark という強力なローカル AI マシンと AiDiy の統合環境の組み合わせは、個人や小チームにとって現実的な選択肢になります。",
          "audio": "audio/dlg_005_04_male.mp3",
          "duration_sec": 26.352
        }
      ],
      "duration_sec": 111.6
    },
    {
      "id": "scene_999",
      "title": "まとめ — NVIDIA Spark が変えるローカル AI の未来",
      "accent": "#76b900",
      "accent_soft": "rgba(118, 185, 0, 0.18)",
      "kicker": "SUMMARY",
      "headline": "NVIDIA Spark が切り拓く\nローカル AI 新時代のまとめ",
      "lead": "RTX Spark × Windows PC と DGX Spark × AiDiy で、AI の主戦場が手元にやってきます。",
      "image": "images/scene_999.png",
      "source_summary": "まとめ: RTX Spark（1PFLOP/128GB統合メモリ/Blackwell GPU 6,144コア/Arm CPU 20コア）搭載薄型 Windows PC が各社から秋発売予定。DGX Spark（GB10 Grace Blackwell、2,000億パラメータ対応）がデスクトップ AI スパコンを個人へ。AiDiy + Spark でローカル LLM + 全機能をクラウド非依存で運用可能。",
      "factual_bullets": [
        "RTX Spark: 1PFLOP(FP4) / 128GB 統合メモリ / Blackwell GPU 6,144コア / Arm CPU 20コア",
        "各社搭載 PC が 2026 年秋発売予定（Surface / ASUS / Dell / HP / Lenovo / MSI）",
        "DGX Spark: GB10 Grace Blackwell / 2,000億パラメータ対応のデスクトップ AI スパコン",
        "AiDiy + Spark: クラウド非依存でローカル LLM と全機能を 1 台で運用可能",
        "この動画は AiDiy のビデオページ生成機能で自動生成"
      ],
      "forbidden_elements": [
        "完全な AGI 実現を示唆する表現",
        "記事に記載のない価格・発売日の断定",
        "AiDiy が商用製品として公式リリースされているかのような断言"
      ],
      "image_prompt": "Wordless optimistic final visual: laptop and compact AI workstation connected to a private local AI workspace, green energy flowing toward a friendly creator desk setup. No readable text, no dates, no numbers, no logos, no UI labels.",
      "dialogue": [
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "RTX Spark と DGX Spark の 2 形態が、AI の主戦場をローカルへと引き寄せます。",
          "naration_text": "今回の解説をまとめます。NVIDIA Spark ファミリーは、RTX Spark スーパーチップ搭載の薄型軽量 Windows PC と、DGX Spark デスクトップ型パーソナル AI スパコンという 2 形態でローカル AI の新時代を切り拓きます。RTX Spark は FP4 で 1 ペタフロップス、Blackwell GPU 最大 6,144 コア、Arm CPU 最大 20 コア、統合メモリ最大 128GB を実現。DGX Spark は GB10 Grace Blackwell で最大 2,000 億パラメータの AI 処理に対応します。",
          "audio": "audio/dlg_999_01_male.mp3",
          "duration_sec": 32.04
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "2026 年秋発売の PC が Windows を本格 AI 開発プラットフォームへと進化させます。",
          "naration_text": "Surface Laptop Ultra をはじめ ASUS、Dell、HP、Lenovo、MSI から RTX Spark 搭載 PC が 2026 年秋に発売予定です。Prism エミュレータ強化で x86 互換を保ちながら、WSL 経由で Linux の AI エコシステムへアクセスし、NVIDIA OpenShell でエージェント実行の安全性も確保される。Windows がいよいよ本格的な AI 開発プラットフォームとして進化しています。",
          "audio": "audio/dlg_999_02_female.mp3",
          "duration_sec": 28.584
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Spark と AiDiy でローカル LLM と AI 機能を 1 台に集約。低レイテンシで安心な環境が完成します。",
          "naration_text": "AiDiy の 2 サーバー構成と 15 MCP の TOOL HUB、そして Ollama などのローカル LLM を Spark のハードウェアと組み合わせると、完全にクラウド非依存の AI 開発環境が手元に完成します。データが外に出ない、低レイテンシ、API コスト不要という 3 つの利点を同時に実現できるのは、Spark のローカル AI 実行基盤があってこそです。AI コアと Code AI のパネルをすべてローカルモデルで動かせます。",
          "audio": "audio/dlg_999_03_male.mp3",
          "duration_sec": 24.36
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AiDiy のビデオ生成機能で作られた動画です。ぜひ AiDiy を試してチャンネル登録もお願いします！",
          "naration_text": "最後に、この動画のシナリオ作成・画像生成・音声合成まで、すべて AiDiy のビデオページ生成機能によって自動生成されました。AiDiy は GitHub からクローンしてすぐ動かせる、日本語ファーストのフルスタック業務管理テンプレートです。Spark 上でローカル LLM と組み合わせれば、クラウドに頼らない自分だけの AI 環境が作れます。この動画が参考になったら、ぜひチャンネル登録をお願いします。皆さんも AiDiy × Spark でローカル AI の新時代を、一緒に楽しみましょう！",
          "audio": "audio/dlg_999_04_female.mp3",
          "duration_sec": 32.784
        }
      ],
      "duration_sec": 117.768
    }
  ],
  "total_duration_sec": 788.376
};
