# AiDiy AIコア 紹介 — ナレーション台本

## scene_000 INTRODUCTION
AiDiy の AI 機能を紹介します。チャット、ライブ、コード支援、音声の 4 つのモードがあります。

## scene_001 AI CORE OVERVIEW
AI の入口は WebSocket サーバーです。モードごとのモジュールが AI Provider と通信して結果を返します。

## scene_002 4 MODES
AI の名前にはルールがあります。チャットは _chat、ライブは _live で終わる名前にします。コード支援は 6 スロットに割り当てられます。

## scene_003 WEBSOCKET
AI と通信するとき WebSocket を使います。接続後に connect を送ると、サーバーから init が返ってセッション ID が決まります。

## scene_004 CONVERSATION HISTORY
会話の内容はデータベースに保存します。セッション ID で管理するので、ページを再読み込みしても続きから話せます。

## scene_005 CLAUDE SDK & MCP
AIコード_claude.py は Claude Agent SDK を使います。13 個の MCP ツールを AI に渡すことで、ブラウザ操作や DB 確認も AI が自動実行します。

## scene_006 AI PROVIDERS
チャットは Claude、Gemini、OpenRouter など複数の AI サービスに対応しています。設定ファイルで切り替えられます。

## scene_999 CLOSING
4 モード、WebSocket、会話保存、Claude SDK と MCP。多様な AI を業務に組み込んでみてください。
