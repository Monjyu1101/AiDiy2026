# AiDiy AIコア 紹介 — ナレーション台本

## scene_000 (0〜12秒) INTRODUCTION
この動画では、AiDiy のAIコアを紹介します。チャット、ライブ、コード支援、音声処理の 4 モード、WebSocket 通信設計、複数の AI Provider、A会話履歴の永続化、Claude Agent SDK と MCP の連携まで、実装に沿って見ていきます。

## scene_001 (12〜26秒) AI CORE OVERVIEW
AIコアは core_router/AIコア.py が WebSocket エンドポイントを提供し、AIコア ディレクトリ配下の各モジュールがモードごとの処理を担当します。AIセッション管理がセッションとモデル設定を保持し、AIストリーミング処理がレスポンスをリアルタイムに転送します。AIチャット、AIライブ、AIコード、AI音声処理の各モジュールが Provider ごとに実装されています。

## scene_002 (26〜40秒) 4 MODES
AIコアは 4 つのモードで構成されます。チャットモードは CHAT_AI_NAME で指定し、名前は _chat で終わる規約です。ライブモードは LIVE_AI_NAME で、_live で終わります。コード支援は CODE_AI1_NAME から CODE_AI6_NAME の 6 スロットで、原則 _sdk か _cli で終わり、例外として aidiy_hermes も指定できます。音声処理は AI音声処理.py と AI音声認識.py が担当します。

## scene_003 (40〜54秒) WEBSOCKET
WebSocket の接続フローは、open 後に connect メッセージを送信し、サーバーから init を受けてセッションIDを確定します。テキスト入力は input_text、ファイルは input_file、音声は input_audio をそれぞれのチャンネルで送信します。AI の出力は output メッセージで返り、チャット・code1 から code6・audio のチャンネルに分配されます。音声は audio チャンネル専用で、input_audio は高頻度送信のためトークン延長対象外です。

## scene_004 (54〜68秒) CONVERSATION HISTORY
AIコアの会話は A会話履歴テーブルに SQLite へ永続化されます。セッションIDをキーに会話を管理し、リロードや再接続後もセッションを復元できます。A会話履歴は core_main の C 系・A 系担当サーバーが管理します。セッションIDは WebSocket 接続時の init で確定し、リロード時は既存セッションIDを渡して復元します。

## scene_005 (68〜82秒) CLAUDE SDK & MCP
AIコード_claude.py は Claude Agent SDK を使って AI エージェントを構築します。_config/AiDiy_mcp.json に定義した 13 個の MCP サーバーをエージェントに渡すことで、ブラウザ操作やDB確認、画像生成などを Claude が自動的に使用できます。コードパネルの code スロットに claude_sdk を設定すると、AIコード_claude.py が起動して MCP 連携が有効になります。

## scene_006 (82〜96秒) AI PROVIDERS
AIコアは用途別に対応 Provider が異なります。チャットモードは Claude、Gemini、OpenRouter、Ollama、FreeAI に対応し、AIチャット.py と AIチャット_gemini.py などで実装されています。ライブモードは Gemini Live と OpenAI Realtime に対応し、AIライブ_gemini.py と AIライブ_openai.py で実装されています。コード支援は Claude SDK、Claude CLI、Gemini CLI、aidiy_hermes、Codex など多様な CLI に対応しています。

## scene_999 (96〜112秒) CLOSING
ご視聴ありがとうございました。AiDiy の AIコアはチャット、ライブ、コード支援、音声処理の 4 モードを WebSocket で統合し、A会話履歴で永続化します。Claude Agent SDK と MCP 連携でエージェント化し、Claude、Gemini、Ollama など多様な Provider を切り替えられます。AiDiy を通じて多様な AI をあなたの業務に組み込んでみてください。
