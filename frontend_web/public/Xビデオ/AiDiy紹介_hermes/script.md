# AiDiy Hermes 紹介 台本

合計尺: 123.0 秒（実測 48kbps MP3 計測値）

## scene_000: AiDiy Hermes 紹介

- 字幕: AiDiy Hermes — 位置づけ・Provider・Slash Command・連携を紹介します。
- ナレーション: この紹介では、AiDiy 専用のコードエージェント CLI、aidiy_hermes の実態を説明します。位置づけ、技術スタック、Provider、Slash Command、そして AiDiy との連携まで順に見ていきます。
- 画像: ../sozai/アイディ.png（ヒーロー）
- 音声: audio/scene_000.mp3 (15.0 秒)

## scene_001: 位置づけと起動方式

- 字幕: 常駐しない。コードパネルから subprocess で起動される on-demand CLI。
- ナレーション: aidiy_hermes は常駐 HTTP サーバーではありません。_start.py の起動対象でもない。AiDiy の AI コードパネルが必要なときだけ subprocess で呼び出す、on-demand なコードエージェント CLI です。
- 画像: images/scene_001.png
- 音声: audio/scene_001.mp3 (16.0 秒)

## scene_002: 技術スタックと構成

- 字幕: cli_main.py が起点。5 層構成で provider・TUI・tools を分担。
- ナレーション: aidiy_hermes は Python で実装されており、TUI には prompt_toolkit を使います。cli_main.py がエントリで、core、base、hermes_cli、tools、skills の5層で役割を分担します。
- 画像: images/scene_002.png
- 音声: audio/scene_002.mp3 (17.5 秒)

## scene_003: 31 Provider Overlay

- 字幕: 31 overlays、50+ aliases。auto 検出または --provider で解決。
- ナレーション: hermes_cli/providers.py の HERMES_OVERLAYS に 31 の provider が定義されており、50 以上のエイリアスでフレンドリ名から canonical ID へマッピングします。優先順位は --provider フラグ、config.yaml、環境変数、auto の順です。
- 画像: images/scene_003.png
- 音声: audio/scene_003.mp3 (18.0 秒)

## scene_004: 60 Slash Commands

- 字幕: 60 slash commands。/ 補完で一覧が出る。
- ナレーション: hermes_cli/commands.py の COMMAND_REGISTRY に 60 の slash command が登録されています。Session、Configuration、Tools and Skills、Info、Exit の5カテゴリに分かれ、/model で provider と model を interactive に切り替えられます。
- 画像: images/scene_004.png
- 音声: audio/scene_004.mp3 (17.5 秒)

## scene_005: AiDiy システム連携

- 字幕: CODE_AI*_NAME = aidiy_hermes で AI コードパネルと連携。
- ナレーション: AI コードパネルで CODE_AI アスタリスク NAME を aidiy_hermes に設定すると、backend_server の AIコード_cli.py が Hermes を subprocess で起動します。モデル一覧は conf_model.py が動的生成し、モデル設定は CODE_AIDIY_HERMES_MODEL を使います。
- 画像: images/scene_005.png
- 音声: audio/scene_005.mp3 (20.5 秒)

## scene_999: ご視聴ありがとうございました

- 字幕: aidiy_hermes — on-demand、31 providers、60 slash commands。
- ナレーション: ご視聴ありがとうございました。aidiy_hermes は on-demand のコードエージェントとして、31 の provider と 60 の slash command を持ちます。AiDiy のコードパネルからも単体 CLI としても動きます。あなたのコード作業をエージェントに任せてみてください。
- 画像: ../sozai/アイディ.png（ヒーロー）
- 音声: audio/scene_999.mp3 (18.5 秒)
