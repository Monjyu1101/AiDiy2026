# AiDiy 自己紹介 アバター版 台本

合計尺: 90.912 秒
※ 音声: audio/ に自己完結 (take4 と同一ナレーション)。画像: images/ に自己完結。

## scene_000: この紹介で話すこと

- 字幕: この紹介では、AiDiy の全体像、設計方針、業務サンプル、AI・MCP 連携を紹介します。
- ナレーション: この動画では、AiDiy の全体像と設計の考え方を紹介します。日本語ファースト設計、業務サンプル、AI コア、MCP、ナレッジの入口まで、実装に沿って見ていきます。
- 画像: images/hero.png
- 音声: audio/scene_000.mp3 (11.616 秒)

## scene_001: AiDiyとは

- 字幕: 日本語識別子と業務サンプルを土台に、AI / 音声 / MCP まで一体化した基盤。
- ナレーション: AiDiy は、日本語を第一言語にしたフルスタック業務管理テンプレートです。FastAPI と SQLite と Vue 3 を軸に、業務サンプルと AI 実験基盤をひとつにまとめます。
- 画像: images/scene_001.png
- 音声: audio/scene_001.mp3 (11.088 秒)

## scene_002: 日本語ファースト設計

- 字幕: 業務語彙と実装名を揃え、読めるまま保守できる構成。
- ナレーション: 画面、URL、JSON、コード識別子まで日本語を原則にし、業務語彙と実装名をまっすぐ対応づけます。だから設計意図を日本語のまま保守へ持ち込めます。
- 画像: images/scene_002.png
- 音声: audio/scene_002.mp3 (10.152 秒)

## scene_003: 3常駐サーバー + マルチCLI

- 字幕: Code AI はひとつではなく、複数CLI + 独自実装 Hermes を切り替える。
- ナレーション: AiDiy の Code AI は、Claude や Copilot や Codex や Gemini や OpenCode など複数の CLI を切り替えて使えます。その上で backend_hermes は、AiDiy 専用に組み込まれた on-demand の独自コードエージェントで、AI コードパネルから subprocess で起動されます。
- 画像: images/scene_003.png
- 音声: audio/scene_003.mp3 (16.776 秒)

## scene_004: 業務サンプルと命名規則

- 字幕: サンプル名と実装パターンが一致しているので、横展開しやすい。
- ナレーション: C、M、T、V、S、A、X の接頭辞と、配車、生産、在庫の実務サンプルがあるので、新機能を既存パターンに沿って横展開できます。明細型パターンも最初から実例付きです。
- 画像: images/scene_004.png
- 音声: audio/scene_004.mp3 (14.760 秒)

## scene_005: AIコアとアバター

- 字幕: AIコアの多パネル体験を、VRM アバターまで含めて運用できる。
- ナレーション: AIコアはチャット、音声、画像、ファイル、コード支援を統合し、frontend_avatar は Electron と Web の両方で VRM アバター体験を支えます。状態同期には BroadcastChannel を使います。
- 画像: images/avatar_web.png, images/avatar_desktop.png
- 音声: audio/scene_005.mp3 (13.200 秒)

## scene_999: ご視聴ありがとうございました

- 字幕: あなたなら AiDiy でなにを創りますか？
- ナレーション: ご視聴ありがとうございました。AiDiy には、ウェブ、アバター、バックエンド、MCP まで、一緒に試しながら形にできる部品がそろっています。あなたなら AiDiy で、なにを創りますか。
- 画像: images/hero.png
- 音声: audio/scene_999.mp3 (13.320 秒)
