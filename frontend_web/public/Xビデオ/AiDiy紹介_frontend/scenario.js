window.SCENARIO = {
  "project_name": "AiDiy紹介frontend",
  "version": "frontend",
  "title": "AiDiy frontend_web - Vue 3 + qTubler + 日本語ファースト UI",
  "source": {
    "type": "agents_and_knowledge",
    "summary": "frontend_web/AGENTS.md、.aidiy/knowledge の実装パターン・画面追加手順・Vue Router・Pinia から実装実態を抜粋して構成。"
  },
  "target": {
    "language": "ja-JP",
    "format": "html_css_scene_player_with_media",
    "tone": "事実ベース、簡潔、根拠付き",
    "goal": "frontend_web の技術スタック・コンポーネント配置・qTubler・認証・Vite proxy・AIコア連携を正確に伝える。"
  },
  "assets_policy": {
    "visual_style": "left_avatar_38_right_content_62",
    "audio_dir": "audio",
    "image_dir": "images",
    "avatar": "vrm/AiDiy_Sample_M.vrm"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "この動画で紹介すること",
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123,140,255,0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "INTRODUCTION",
      "headline": "この動画では、AiDiy frontend_web の\n設計と実装パターンを紹介します",
      "lead": "Vue 3・Vite・qTubler・Vue Router・Pinia・Axios・認証・Vite proxy・AIコア連携まで、実装に沿って見ていきます。",
      "subtitle": "frontend_web の技術スタック、コンポーネント配置、qTubler、認証、AIコア連携を紹介します。",
      "image": "images/scene_000.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "short_narration": "AiDiy の Web 画面は Vue 3 で作られています。画面の仕組みと構成を紹介します。",
      "long_narration": "この動画では、AiDiy の Web 画面フロントエンドを詳しく紹介します。フロントエンドとは、ブラウザに表示される画面のことです。AiDiy の Web 画面は Vue 3 という最新の JavaScript フレームワークで作られています。Vue 3 は画面を部品（コンポーネント）の組み合わせで作る仕組みで、コードの構成がパターン化されているため、AI に「この画面と同じ形で商品管理画面を追加して」と指示するだけで、API 連携まで含めた画面を生成できます。Vite・TypeScript・Vue Router・Pinia と、今のフロントエンド開発の標準ツールを組み合わせた構成です。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 6.36,
      "long_start_sec": 0.0,
      "long_duration_sec": 38.208
    },
    {
      "id": "scene_001",
      "title": "技術スタックと基本方針",
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123,140,255,0.18)",
      "kicker": "TECH STACK",
      "headline": "Vue 3 + Vite + TypeScript で\nポート 8090 から提供",
      "lead": "Composition API・`<script setup lang=\"ts\">`・Vue Router・Pinia を使います。UI framework は使わず、既存 CSS と共有コンポーネントへ合わせます。TypeScript は strict mode 無効で運用します。",
      "subtitle": "Vue 3 Composition API、Vite:8090、strict mode 無効 TypeScript、独自 CSS。",
      "image": "images/scene_001.png",
      "chips": [
        "Vue 3 Composition API",
        "Vite:8090",
        "TypeScript (strict無効)",
        "Pinia + Vue Router"
      ],
      "metrics": [
        {
          "label": "ポート",
          "value": "8090"
        },
        {
          "label": "フレームワーク",
          "value": "Vue 3 + Vite"
        },
        {
          "label": "状態管理",
          "value": "Pinia"
        }
      ],
      "cards": [
        {
          "title": "コア技術",
          "lines": [
            "Vue 3 Composition API / `<script setup lang=\"ts\">`",
            "Vite (開発サーバー + ビルド)",
            "Vue Router + Pinia"
          ]
        },
        {
          "title": "追加ライブラリ",
          "lines": [
            "Axios (API クライアント)",
            "dayjs (日付処理)",
            "Monaco Editor (コードエディタ)"
          ]
        },
        {
          "title": "UI 方針",
          "lines": [
            "UI framework / CSS framework なし",
            "既存 CSS と共有コンポーネントへ合わせる",
            "TypeScript strict mode 無効"
          ]
        }
      ],
      "facts": [
        "Vue 3 Composition API と `<script setup lang=\"ts\">` を使う。",
        "UI framework / CSS framework は使わず、既存 CSS と共有コンポーネントへ合わせる。",
        "TypeScript は strict mode 無効の設定で運用する。"
      ],
      "evidence": [
        {
          "source": "frontend_web/AGENTS.md",
          "text": "Vue 3。Vite。TypeScript。Vue Router。Pinia。Axios。dayjs。Monaco Editor。qTubler 独自テーブル。"
        },
        {
          "source": "frontend_web,実装パターン.md",
          "text": "Vue 3 Composition API と `<script setup lang=\"ts\">` を使う。UI framework / CSS framework は使わず、既存 CSS と共有コンポーネントへ合わせる。TypeScript は strict mode 無効の設定で運用しているが、不要な `any` の拡大は避ける。"
        }
      ],
      "short_narration": "ポート 8090 で動く Vue 3 アプリです。画面切り替えは Vue Router、データ共有は Pinia で管理します。",
      "long_narration": "Web 画面はポート 8090 番で動く Vue 3 アプリです。ビルドには高速な Vite、言語は TypeScript を使っています。ページの切り替えには Vue Router を使い、URL と画面コンポーネントを対応づけます。アプリ全体で共有するデータの管理には Pinia を使い、ログイン中の利用者情報など複数の画面をまたぐデータをここで管理します。Vue 3・Vite・TypeScript・Vue Router・Pinia は、今のフロントエンド開発で世界標準となっているツールの組み合わせです。AI の学習データも豊富なので、コード生成の精度が高く、エラーの解決もしやすいのが特徴です。外部 UI フレームワークは使わず、既存スタイルに合わせた統一した見た目を保っています。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_start_sec": 6.36,
      "short_duration_sec": 8.04,
      "long_start_sec": 38.208,
      "long_duration_sec": 45.936
    },
    {
      "id": "scene_002",
      "title": "コンポーネント配置と Router",
      "expression": "neutral",
      "accent": "#ff8a6b",
      "accent_soft": "rgba(255,138,107,0.18)",
      "kicker": "COMPONENTS & ROUTER",
      "headline": "接頭辞別にフォルダ分け、\nRouter は 3 ファイル構成",
      "lead": "C系は C管理、M系は Mマスタ、T系は Tトラン、V系は Vビュー、S系は Sスケジューラー、X系は Xその他。Router は index.ts / coreRouter.ts / appsRouter.ts の 3 ファイルで分担します。",
      "subtitle": "コンポーネントは接頭辞別フォルダ。Router は index.ts / coreRouter.ts / appsRouter.ts の 3 分割。",
      "image": "images/scene_002.png",
      "chips": [
        "C管理/Mマスタ/Tトラン/Vビュー",
        "Sスケジューラー/Xその他",
        "Router 3分割",
        "<component :is>"
      ],
      "metrics": [
        {
          "label": "コンポーネントフォルダ",
          "value": "6カテゴリ"
        },
        {
          "label": "Router ファイル",
          "value": "3"
        },
        {
          "label": "日本語タグ問題",
          "value": "<component :is>"
        }
      ],
      "cards": [
        {
          "title": "コンポーネントフォルダ",
          "lines": [
            "`C管理/` — C系管理画面",
            "`Mマスタ/` — M系マスタ、`Tトラン/` — T系トランザクション",
            "`Vビュー/` / `Sスケジューラー/` / `Xその他/`"
          ]
        },
        {
          "title": "Router 3 ファイル構成",
          "lines": [
            "`index.ts` — 基底・ログイン・X系全般",
            "`coreRouter.ts` — C系・A系",
            "`appsRouter.ts` — M系・T系・V系・S系"
          ]
        },
        {
          "title": "日本語コンポーネントの扱い",
          "lines": [
            "`<C利用者一覧 />` のような日本語タグは無効",
            "`import C利用者一覧 from '...'` して",
            "`<component :is=\"C利用者一覧\" />` と書く"
          ]
        }
      ],
      "facts": [
        "コンポーネントは接頭辞別に C管理/Mマスタ/Tトラン/Vビュー/Sスケジューラー/Xその他 フォルダに配置。",
        "Router は index.ts / coreRouter.ts / appsRouter.ts の 3 ファイルで分担。",
        "日本語 component tag は template 内で直接書けないため `<component :is=\"日本語名\">` を使う。"
      ],
      "evidence": [
        {
          "source": "frontend_web/AGENTS.md",
          "text": "日本語 component は import して `<component :is=\"...\">` で扱う。"
        },
        {
          "source": "frontend_web,実装パターン.md",
          "text": "よくある落とし穴: `<C利用者一覧 />` のような日本語タグを書くとブラウザで無効扱いになる。"
        }
      ],
      "short_narration": "画面コンポーネントは C 系・M 系・T 系など、接頭辞別のフォルダに整理して配置します。",
      "long_narration": "コンポーネントは接頭辞ごとのフォルダに整理されています。C 系は C管理、M 系は Mマスタ、T 系は Tトラン、V 系は Vビュー、X 系は Xその他フォルダです。このフォルダ構成を AI に教えることで、「M系のマスタ画面として Mマスタ フォルダに追加して」という指示だけで、正しい場所に正しい形のファイルを作れます。Router は 3 ファイル（index.ts・coreRouter.ts・appsRouter.ts）に分かれており、AI が追加するファイルをどの Router に登録するかも自動で判断します。日本語のファイル名で作ったコンポーネントは component タグの is 属性で呼び出す書き方が必要ですが、サンプルコードがあれば AI がそのまま踏襲します。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_start_sec": 14.4,
      "short_duration_sec": 7.056,
      "long_start_sec": 84.144,
      "long_duration_sec": 45.696
    },
    {
      "id": "scene_003",
      "title": "qTubler — 独自グリッドコンポーネント",
      "expression": "neutral",
      "accent": "#00e0b8",
      "accent_soft": "rgba(0,224,184,0.18)",
      "kicker": "qTUBLER",
      "headline": "ソート・ページング・行選択を持つ\n独自テーブル qTubler",
      "lead": "`_share/qTublerFrame.vue` が主要グリッドです。外部 UI framework に置き換えない方針で、`columns`・`rows`・`totalCount`・`currentPage`・`sortKey` などを props で渡し、sort/page イベントで再取得します。",
      "subtitle": "qTublerFrame.vue が標準一覧テーブル。sort/page イベントで V系 API を再取得する。",
      "image": "images/scene_003.png",
      "chips": [
        "qTublerFrame.vue",
        "columns / rows / totalCount",
        "sort / page イベント",
        "V系 API 連携"
      ],
      "metrics": [
        {
          "label": "コアファイル",
          "value": "qTublerFrame.vue"
        },
        {
          "label": "標準 props",
          "value": "8種"
        },
        {
          "label": "イベント",
          "value": "sort / page"
        }
      ],
      "cards": [
        {
          "title": "主要 props",
          "lines": [
            "`columns` — 列定義 (types/qTubler.ts に合わせる)",
            "`rows` / `rowKey` / `totalCount` / `totalAll`",
            "`currentPage` / `totalPages` / `sortKey` / `sortOrder`"
          ]
        },
        {
          "title": "V系連携パターン",
          "lines": [
            "sort / page イベントで `/apps/V商品/一覧` を再取得",
            "レスポンス `data.items` → `rows`",
            "レスポンス `data.total` → `totalCount`"
          ]
        },
        {
          "title": "UI 統一ルール",
          "lines": [
            "数値欄: 内部は文字列、非フォーカス時に3桁区切り",
            "ラベル幅 160px 基準、入力幅は倍数で揃える",
            "qAlert / qConfirm — 標準 alert/confirm を増やさない"
          ]
        }
      ],
      "facts": [
        "`_share/qTublerFrame.vue` が一覧画面の標準テーブル。外部 UI framework に置き換えない方針。",
        "sort / page イベントで V系 API を再取得するパターンが標準。",
        "数値入力は内部値をカンマなし文字列で持ち、非フォーカス時だけ 3桁区切り表示にする。",
        "保存完了は `qAlert()`、削除確認は `qConfirm()` を使い、ブラウザ標準を増やさない。"
      ],
      "evidence": [
        {
          "source": "frontend_web/AGENTS.md",
          "text": "qTubler は `_share/qTublerFrame.vue` を中心にした独自テーブルです。ソート、ページング、行選択を持ち、外部 UI framework へ置き換えない方針です。"
        },
        {
          "source": "frontend_web,実装パターン.md",
          "text": "`columns` は `types/qTubler.ts` の型に合わせる。`rows`、`rowKey`、`totalCount`、`totalAll`、`currentPage`、`totalPages`、`sortKey`、`sortOrder` を渡す。sort / page イベントで再取得する。"
        }
      ],
      "short_narration": "qTubler は列定義を渡すだけで、一覧・検索・ページングが揃う AiDiy 独自のテーブル部品です。",
      "long_narration": "qTubler は AiDiy 独自の一覧テーブル部品です。列の定義・データ・件数の 3 つを渡すだけで、ページングとソートが動くテーブルが完成します。外部 UI ライブラリに依存しない独自部品なので、AiDiy のルールを学習した AI なら qTubler を使ったコードを自動で生成できます。「qTubler を使って商品在庫一覧画面を追加して」の一言で、検索フォーム・ページング・ソートが揃った画面が出来上がります。数値はカンマなしで受け取って表示時に桁区切りを付ける仕組みも自動で含まれます。AiDiy 全体で統一された見た目を保ちながら、新しい一覧画面を素早く追加できます。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_start_sec": 21.456,
      "short_duration_sec": 7.104,
      "long_start_sec": 129.84,
      "long_duration_sec": 40.32
    },
    {
      "id": "scene_004",
      "title": "認証と Vite Proxy",
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196,155,255,0.18)",
      "kicker": "AUTH & PROXY",
      "headline": "JWT を localStorage に保存し、\n401 は interceptor でログアウト",
      "lead": "token と user を `localStorage` に保存します。401 は Axios response interceptor でログアウト処理へ流れます。API は `/core/*` → 8091、`/apps/*` → 8092 に Vite proxy 経由で転送します。",
      "subtitle": "localStorage + Axios interceptor。Vite proxy で /core→8091、/apps→8092 に転送。",
      "image": "images/scene_004.png",
      "chips": [
        "JWT localStorage",
        "Axios interceptor",
        "/core→8091",
        "/apps→8092"
      ],
      "metrics": [
        {
          "label": "token 保存先",
          "value": "localStorage"
        },
        {
          "label": "401 処理",
          "value": "interceptor 自動ログアウト"
        },
        {
          "label": "proxy 先",
          "value": "8091 / 8092"
        }
      ],
      "cards": [
        {
          "title": "認証フロー",
          "lines": [
            "ログイン成功 → `localStorage` に token / user 保存",
            "backend の `初期ページ` を優先して遷移",
            "権限IDは文字列として扱う (`'1'` で比較)"
          ]
        },
        {
          "title": "Axios interceptor",
          "lines": [
            "`src/api/client.ts` で設定",
            "request: Bearer token を自動付与",
            "response: 401 → ログアウト処理へ"
          ]
        },
        {
          "title": "Vite Proxy",
          "lines": [
            "`baseURL: '/'` で Vite proxy を経由",
            "`/core/*` → `http://127.0.0.1:8091`",
            "`/apps/*` → `http://127.0.0.1:8092`"
          ]
        }
      ],
      "facts": [
        "token と user は `localStorage` の `token` / `user` キーに保存する。",
        "401 は `client.ts` の response interceptor でログアウト処理へ流れる。",
        "API の `baseURL` は `/` とし、Vite proxy で `/core` → 8091、`/apps` → 8092 に転送する。",
        "直接 `http://localhost:8091` を叩かない（CORS 条件が変わる）。"
      ],
      "evidence": [
        {
          "source": "frontend_web/AGENTS.md",
          "text": "JWT token と user は `frontend_web` では `localStorage` に保存します。401 は Axios response interceptor でログアウト処理へ流します。"
        },
        {
          "source": "frontend_web,実装パターン.md",
          "text": "よくある落とし穴: Vite proxy を使わず `http://localhost:8091` へ直叩きして CORS 条件が変わる。"
        }
      ],
      "short_narration": "ログイン情報はブラウザに保存し、API リクエストは Vite Proxy で Core と Apps に自動で振り分けます。",
      "long_narration": "ログイン後のトークンと利用者情報はブラウザの localStorage に保存します。API のエラーは Axios のインターセプターが自動でキャッチして、ログアウト画面に誘導します。サーバーとの通信はすべて Vite の Proxy 設定を経由します。/core で始まるパスは Core サーバー（ポート 8091）に、/apps で始まるパスは Apps サーバー（ポート 8092）に自動で振り分けられます。この仕組みのおかげで、フロントエンドのコードにサーバーのアドレスを直書きしなくて済みます。AI がコードを生成するときも「/apps/商品/一覧を呼ぶ」と書けば、Proxy が自動で転送先を解決します。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_start_sec": 28.56,
      "short_duration_sec": 7.848,
      "long_start_sec": 170.16,
      "long_duration_sec": 40.464
    },
    {
      "id": "scene_005",
      "title": "AIコア画面連携",
      "expression": "neutral",
      "accent": "#ffd166",
      "accent_soft": "rgba(255,209,102,0.18)",
      "kicker": "AI INTEGRATION",
      "headline": "WebSocket で backend AIコアと接続し、\ncode1〜code6・チャット・音声を統合",
      "lead": "`ws://…/core/ws/AIコア` に WebSocket 接続し、テキスト・ファイル・画像・コード支援・音声を統合するパネルを提供します。AIWebSocket は再接続ポリシーとメッセージディスパッチを持ちます。",
      "subtitle": "WebSocket でAIコアと通信。code1〜code6 パネル、チャット、ファイル、音声を統合。",
      "image": "images/scene_005.png",
      "chips": [
        "AIWebSocket 再接続",
        "code1〜code6",
        "チャット/ファイル/音声",
        "sessionId確定"
      ],
      "metrics": [
        {
          "label": "WebSocket エンドポイント",
          "value": "/core/ws/AIコア"
        },
        {
          "label": "コードパネル",
          "value": "6 (code1〜6)"
        },
        {
          "label": "入力種別",
          "value": "テキスト/ファイル/画像/音声"
        }
      ],
      "cards": [
        {
          "title": "WebSocket 接続手順",
          "lines": [
            "open 後に `{ type: \"connect\", セッションID, ソケット番号 }` を送信",
            "サーバーから `{ メッセージ識別: \"init\", セッションID }` を受信",
            "sessionId 確定後にメッセージ送受信開始"
          ]
        },
        {
          "title": "入力チャンネル",
          "lines": [
            "`input_text` — テキスト入力",
            "`input_file` / `input_image` — ファイル・画像",
            "`input_audio` — マイク PCM（トークン延長なし）"
          ]
        },
        {
          "title": "出力チャンネル",
          "lines": [
            "チャット出力: `output` → `chat` チャンネル",
            "コード出力: `output` → `code1`〜`code6`",
            "音声出力: `output_audio` → `audio` チャンネル"
          ]
        }
      ],
      "facts": [
        "AIコア WebSocket エンドポイントは `ws://.../core/ws/AIコア`。",
        "接続後に `connect` 送信 → `init` 受信で sessionId を確定する。",
        "コードパネルは code1〜code6 の 6 チャンネル。",
        "`input_audio` は高頻度送信のためトークン延長対象外。"
      ],
      "evidence": [
        {
          "source": "backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md",
          "text": "エンドポイントは `ws://<host>/core/ws/AIコア`。接続時に `{ type: \"connect\", セッションID, ソケット番号 }` を送信し、サーバーから `{ メッセージ識別: \"init\", セッションID: \"<確定ID>\" }` を受けて sessionId が確定する。"
        },
        {
          "source": "frontend_web/AGENTS.md",
          "text": "`frontend_web` 版 AI コアは backend の `/core/AIコア` と WebSocket で接続します。code1〜code6、ファイル、画像、チャット、設定ダイアログを扱います。"
        }
      ],
      "short_narration": "AI 画面は WebSocket で接続し、テキスト・画像・音声・コードをリアルタイムでやり取りします。",
      "long_narration": "AI 画面はサーバーと WebSocket でリアルタイムに繋がっています。普通の API は「送ったら返ってくる」一方通行ですが、WebSocket は繋いだまま双方向にデータを流せます。AI の返答が少しずつリアルタイムで表示されるのは、この WebSocket のおかげです。送れるのはテキスト・ファイル・画像・音声で、受け取れるのはチャットの返答・生成コード・音声データです。コード支援パネルは code1 から code6 まで 6 つ同時に使えるため、複数の AI に並行して相談できます。AIWebSocket クラスが接続管理・再接続・メッセージの振り分けを担当するので、画面側は受け取ったデータを表示するだけで済みます。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_start_sec": 36.408,
      "short_duration_sec": 7.416,
      "long_start_sec": 210.624,
      "long_duration_sec": 43.248
    },
    {
      "id": "scene_006",
      "title": "X系と Monaco Editor",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125,255,179,0.18)",
      "kicker": "X-SERIES & MONACO",
      "headline": "X系でゲーム・デモ・静的ページを追加し、\nMonaco Editor でコード編集",
      "lead": "X系はルーター登録で動く通常コンポーネントと、`public/` に直置きする静的 HTML ページの 2 パターンがあります。Monaco Editor は言語マッピング `モナコ言語推定()` と Worker 構成を共通化しています。",
      "subtitle": "X系は Vue コンポーネントと public/ 静的 HTML の 2 パターン。Monaco は Worker 共通化。",
      "image": "images/scene_006.png",
      "chips": [
        "Xテトリス",
        "X世界の絶景",
        "public/ 直置き HTML",
        "Monaco 言語マッピング"
      ],
      "metrics": [
        {
          "label": "X系パターン",
          "value": "2種"
        },
        {
          "label": "Monaco Worker",
          "value": "共通化"
        },
        {
          "label": "担当 Router",
          "value": "index.ts"
        }
      ],
      "cards": [
        {
          "title": "X系の 2 パターン",
          "lines": [
            "Vue コンポーネント: `Xその他/` + `index.ts` で router 登録",
            "静的 HTML: `public/X*/` に直置き → そのまま配信",
            "このビデオ自体も `public/Xビデオ/` の静的 HTML"
          ]
        },
        {
          "title": "Monaco Editor",
          "lines": [
            "Worker 構成を共通化（frontend_web / avatar 共通）",
            "`モナコ言語推定()` で拡張子 → 言語マッピング",
            "AI コードパネルと統合してコード編集・表示"
          ]
        },
        {
          "title": "共通ユーティリティ",
          "lines": [
            "`qAlert` / `qConfirm` / `qColorPicker` — シングルトン",
            "`AIWebSocket` — 再接続ポリシー・ディスパッチ",
            "`createWebSocketUrl()` — 環境依存 URL 生成"
          ]
        }
      ],
      "facts": [
        "X系は Vue コンポーネント (index.ts 登録) と public/ 静的 HTML の 2 パターン。",
        "このビデオ自体も `public/Xビデオ/` の静的 HTML として配信されている。",
        "Monaco Editor の Worker 構成と `モナコ言語推定()` は frontend_web と avatar で共通化。",
        "`qAlert` / `qConfirm` / `qColorPicker` はシングルトンダイアログパターン。"
      ],
      "evidence": [
        {
          "source": "frontend_web/AGENTS.md",
          "text": "X系は `components/Xその他/` と `public/` を見る。"
        },
        {
          "source": "CLAUDE.md",
          "text": "共通項目: Monaco Editor 設定 — Worker 構成、拡張子→言語マッピング（`モナコ言語推定()`）。qAlert / qConfirm / qColorPicker — シングルトンダイアログパターン。"
        }
      ],
      "short_narration": "X 系は自由に実験できる領域です。Vue コンポーネントか静的 HTML で追加できます。",
      "long_narration": "X 系は自由に追加できる実験領域です。Vue コンポーネントとして作って Router に登録する方法と、HTML ファイルを public フォルダに置く方法の 2 つがあります。この紹介ビデオ自体も public/Xビデオ フォルダの静的 HTML として配信されています。Monaco Editor（VSCode と同じエディタ部品）や qAlert・qConfirm のダイアログ部品も共通で使えます。AI に「X系にゲーム画面を追加して」と指示するだけで、ファイルの作成から Router の登録まで一緒にやってもらえます。業務機能とは独立しているため、失敗を恐れず自由に試せる場所です。",
      "short_audio": "audio/short_scene_006.mp3",
      "long_audio": "audio/long_scene_006.mp3",
      "short_start_sec": 43.824,
      "short_duration_sec": 7.536,
      "long_start_sec": 253.872,
      "long_duration_sec": 40.536
    },
    {
      "id": "scene_999",
      "title": "ご視聴ありがとうございました",
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123,140,255,0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "AIDIY FRONTEND",
      "headline": "ご視聴ありがとうございました。\nどの画面から実装しますか？",
      "lead": "Vue 3・qTubler・接頭辞別コンポーネント・Router 3分割・Vite proxy・JWT interceptor・AIコア WebSocket。業務画面は既存パターンを参考にどうぞ。",
      "subtitle": "frontend_web — Vue 3、qTubler、接頭辞別コンポーネント、Vite proxy、AIコア WebSocket。",
      "image": "images/scene_999.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "short_narration": "AI への指示一つで API から画面まで一気に作れます。AiDiy で業務システムを作ってみませんか。",
      "long_narration": "AiDiy の AI コーディング機能を使えば、フロントエンドの画面とバックエンドの API を一気通貫で生成できます。「取引先マスタの一覧・登録・編集画面を追加して」と AI に指示するだけで、サーバー側の CRUD・API・画面コンポーネント・Router 登録まで、AiDiy のルールに沿ったコードがそろいます。サンプルコードが AI のお手本になるので、qTubler の使い方・日本語ルール・Vite Proxy の設定を細かく指示しなくても正しい形で生成します。開発環境を立ち上げ、AI に機能を頼み、ブラウザで確認する。このサイクルで業務システムをどんどん育てていけます。今日から使える業務システムを、AiDiy で作ってみませんか。",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_start_sec": 51.36,
      "short_duration_sec": 7.656,
      "long_start_sec": 294.408,
      "long_duration_sec": 44.784
    }
  ],
  "short_duration_sec": 59.016,
  "long_duration_sec": 339.192
};
