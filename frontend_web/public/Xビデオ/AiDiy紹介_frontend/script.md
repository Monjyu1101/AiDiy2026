# AiDiy frontend_web 紹介 — ナレーション台本

## scene_000 INTRODUCTION
AiDiy の Web 画面、frontend_web を紹介します。Vue 3 と Vite で作られた Web アプリです。

## scene_001 TECH STACK
ポート 8090 で動く Vue 3 アプリです。画面遷移は Vue Router、状態管理は Pinia を使います。

## scene_002 COMPONENTS & ROUTER
画面ファイルは接頭辞ごとにフォルダを分けます。Router は 3 つのファイルに分割されています。日本語名コンポーネントは component コロン is で呼び出します。

## scene_003 qTUBLER
qTubler は AiDiy 独自の一覧テーブルです。列定義と行データを渡すとページングとソートが使えます。

## scene_004 AUTH & PROXY
ログイン後のトークンは localStorage に保存します。API の /core と /apps は自動的に backend に振り分けられます。

## scene_005 AI INTEGRATION
AI 画面は WebSocket で backend と繋がります。接続後にセッション ID が決まり、テキストや音声を送受信できます。

## scene_006 X-SERIES & MONACO
X 系はゲームやデモなど実験的な機能の置き場所です。Vue コンポーネントか HTML 直置きの 2 通りで追加できます。

## scene_999 CLOSING
Vue 3、qTubler、Vite proxy、JWT 認証、AI 連携。既存画面を参考に作ってみてください。
