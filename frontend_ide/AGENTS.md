# frontend_ide 実装概要

Term / Code / Live / IDE / Task / Team は AiDiy の正式なサブシステムであり、本フォルダが6種類のVue 3画面を所有する。VS Code拡張はCode / Liveだけ、単独起動は6種類。Task / Team は利用者の指定によるAvatar画面のコピー版で、元Avatarの機能を残し、専用bundleと独立した認証・ウィンドウを使う。

全体のコンセプトは **開発スペース（宇宙をテーマにした IDE 開発環境）**。プロジェクトを宇宙（フォルダ＝銀河、ファイル＝星・惑星）として見せ、人はソースをほぼ触らずに「眺める・辿る・読む・頼む」で開発する。本文の編集は Code / Live を通じて AI に任せ、ビューアは読み取り専用を保つ。エクスプローラーでは明示操作によるコピー・名前変更・新規作成・確認付きのゴミ箱移動を提供する。Code / Live は単独起動・VS Code 拡張を維持したまま、開発スペースの部品としても動作させる（3つの使い方を壊さない）。説明文では見た目を宇宙、画面の文字は「フォルダ」「ファイル」など一般名で書く。

- ルート直下は起動入口（`launch.mjs` / `server.mjs` / `desktop.cjs`）、セットアップ・解除、設定・説明に限定する。Electronの内部処理は `デスクトップ/`、検索・解析・履歴・エクスプローラー操作のAPIは `ファイル機能/`、PTYは `aidiy_term/`、Markdown表示は `viewer/`、VS Code用HTMLは `host/src/` に置く。
- 画面・通信・描画・補助処理は `src/` の日本語機能フォルダにまとめる。共通表示と下書き連携は各画面から共有し、同じ概念の別名部品やアプリ別コピーを増やさない。
- Code / Liveの通信・VS Code拡張ホストは `host/`、ファイルAPI・Office表示は `viewer/` に統合する。Discordは `host/` の共通処理を利用する。AIコア・Hermesは共通バックエンドを使用し、UIに秘密情報を渡さない。
- ポートは自動割り当て。ElectronとWebで同じVue画面を使う。
- IDEのElectron版は「＋ Term」「＋ Code」「＋ Live」で同じプロジェクトの別ウィンドウを開く。Web版は画面内タブ。別窓はIDEの利用モード・セッションとの連携を必須とする。「終了」は子窓を閉じて起動画面へ戻す。タイトルバーの×は確認後にIDE全体を閉じる。オンライン判定はTermと同じtoolsポートのpingを使う。toolsの接続喪失では作業セッションと子窓を維持し、tools復帰時に再接続する。起動・権限・終了連携はElectronメインプロセスで管理する。
- IDEの利用開始は手動。オフラインではTerm / Code、オンラインではTerm / Code / Live。宇宙表示と文書ビューアは読み取り専用。
- コンポーネント破棄時は購読、タイマー、描画、マイク、接続を片付ける。
- 自作ソースには既存の著作権・利用条件の定型文を維持する。第三者ライセンスは配布物へ含める。
- 実装変更は画面を撮影して確認する。手順はREADMEと `_AIDIY/knowledge/` に記載する。

- Termは `ターミナルパネル.vue`（xterm.js）と `aidiy_term/terminal.mjs`（WebSocket）を使い、`aidiy_term/terminal-process.mjs` / `aidiy_term/terminal-worker.mjs` が端末ごとのPTYとプロセス終了を管理する。端末は通常のシェル権限を持ち、ファイルビューアだけが読み取り専用。TermにはVS Code拡張を作らない。
- setup / cleanup の表示・処理順は Term → Code → Live → IDE → Task → Team。全体startの自動起動対象は従来どおりで、Task / Team は独立コマンドから手動起動する。共有依存物は各アプリの停止・解除後に片付ける。
