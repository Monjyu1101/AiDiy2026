# AiDiy MCP Hub 紹介 — ナレーション台本

## scene_000 INTRODUCTION
AiDiy の MCP Hub を紹介します。AI が使える 13 種類のツールが、ポート 8095 にまとまっています。

## scene_001 ARCHITECTURE
backend_mcp は 13 個のツールサーバーをまとめて提供します。AI エージェントは SSE という方式で接続し、ツールを呼び出します。

## scene_002 OVERVIEW
13 のツールは役割で 6 つのグループに分かれています。ブラウザ操作、データベース確認、観測、バックアップ、メディア生成、動画制作です。

## scene_003 CHROME / DESKTOP
Chrome ブラウザを Python から直接操作できます。画面のスクリーンショットも取れます。Node.js は不要です。

## scene_004 DB / OBSERVE / CHECK
データベースの中身を確認したり、ログのエラーを探したり、コードの問題を自動チェックする 4 つのツールです。

## scene_005 MEDIA
画像生成、音声認識、音声合成の 3 つのツールです。OpenAI や Gemini など複数の AI サービスに対応しています。

## scene_006 VIDEO PRODUCTION
OBS Studio での録画や ffmpeg での動画変換を AI から操作できます。動画制作の自動化に使えます。

## scene_999 CLOSING
13 種類のツールを AI が自動で使い分けます。ぜひ活用してみてください。
