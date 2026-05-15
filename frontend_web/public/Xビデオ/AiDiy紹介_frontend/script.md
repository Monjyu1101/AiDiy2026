# AiDiy frontend_web 紹介 — ナレーション台本

## scene_000 (0〜12秒) INTRODUCTION
この動画では、AiDiy の Web フロントエンド、frontend_web を紹介します。Vue 3、Vite、qTubler、Vue Router、Pinia、認証、そして AIコア連携まで、実装パターンに沿って見ていきます。

## scene_001 (12〜25秒) TECH STACK
frontend_web は Vue 3、Vite、TypeScript で構成され、ポート 8090 から提供されます。Composition API と script setup を使い、Vue Router と Pinia で画面と状態を管理します。UI framework は使わず既存 CSS と共有コンポーネントに合わせます。TypeScript は strict mode 無効で運用し、不要な any の拡大は避けます。

## scene_002 (25〜39秒) COMPONENTS & ROUTER
コンポーネントは接頭辞別にフォルダを分けます。C系管理は C管理、M系マスタは Mマスタ、T系トランザクションは Tトラン、V系は Vビュー、S系は Sスケジューラー、X系は Xその他。Router は 3 ファイル構成で、index.ts が基底とX系全般、coreRouter.ts が C系と A系、appsRouter.ts が M・T・V・S 系を担当します。日本語コンポーネントは template 内で直接タグとして書けないため、import して component コロン is で扱います。

## scene_003 (39〜53秒) qTUBLER
qTubler は AiDiy 独自のグリッドコンポーネントで、_share/qTublerFrame.vue を中心にしています。外部 UI framework には置き換えない方針です。columns、rows、rowKey、totalCount、currentPage、totalPages、sortKey、sortOrder を props で渡し、sort と page イベントで V系 API を再取得します。V系一覧では backend レスポンスの items と total を受け取って渡します。

## scene_004 (53〜66秒) AUTH & PROXY
認証は JWT で、token と user を localStorage に保存します。401 エラーは Axios response interceptor でログアウト処理へ自動誘導します。API 呼び出しは baseURL をスラッシュとし、/core で始まるパスを Vite proxy が 8091 へ、/apps で始まるパスを 8092 へ転送します。直接 localhost:8091 を叩かないことで CORS の条件を変えないようにします。

## scene_005 (66〜80秒) AI INTEGRATION
frontend_web の AIコア画面は、backend の ws://.../core/ws/AIコア に WebSocket で接続します。接続時は connect メッセージを送り、サーバーから init を受けて sessionId を確定します。テキスト、ファイル、画像、コード支援 code1 から code6、音声処理を統合したパネルを提供します。AIWebSocket は再接続ポリシーとメッセージディスパッチを内包し、チャンネルごとに出力を分配します。

## scene_006 (80〜94秒) X-SERIES & MONACO
X系はテトリスや世界の絶景など実験的・デモ機能を置く領域です。通常の Vue コンポーネントとして router 登録するパターンと、public ディレクトリに HTML を直置きする静的ページパターンの 2 種類があります。Monaco Editor はコードエディタとして AI コアと統合され、ファイル拡張子から言語を推定する モナコ言語推定 関数と Worker 構成を共通化しています。

## scene_999 (94〜110秒) CLOSING
ご視聴ありがとうございました。frontend_web は Vue 3 と Vite で構成され、qTubler 独自グリッド、接頭辞別コンポーネント配置、Router 3 ファイル分割、Vite proxy による backend 振り分け、JWT 認証、AIコア WebSocket 連携を組み合わせています。業務画面は既存の M マスタや T トランを参考にどうぞ。
