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
    "duration_sec": 110.0,
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
      "start_sec": 0.0,
      "duration_sec": 12.0,
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123,140,255,0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "INTRODUCTION",
      "headline": "この動画では、AiDiy frontend_web の\n設計と実装パターンを紹介します",
      "lead": "Vue 3・Vite・qTubler・Vue Router・Pinia・Axios・認証・Vite proxy・AIコア連携まで、実装に沿って見ていきます。",
      "subtitle": "frontend_web の技術スタック、コンポーネント配置、qTubler、認証、AIコア連携を紹介します。",
      "narration": "AiDiy の Web 画面、frontend_web を紹介します。Vue 3 と Vite で作られた Web アプリです。",
      "image": "images/scene_000.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "audio": "audio/scene_000.mp3"
    },
    {
      "id": "scene_001",
      "title": "技術スタックと基本方針",
      "start_sec": 12.0,
      "duration_sec": 13.0,
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123,140,255,0.18)",
      "kicker": "TECH STACK",
      "headline": "Vue 3 + Vite + TypeScript で\nポート 8090 から提供",
      "lead": "Composition API・`<script setup lang=\"ts\">`・Vue Router・Pinia を使います。UI framework は使わず、既存 CSS と共有コンポーネントへ合わせます。TypeScript は strict mode 無効で運用します。",
      "subtitle": "Vue 3 Composition API、Vite:8090、strict mode 無効 TypeScript、独自 CSS。",
      "narration": "ポート 8090 で動く Vue 3 アプリです。画面遷移は Vue Router、状態管理は Pinia を使います。",
      "image": "images/scene_001.png",
      "audio": "audio/scene_001.mp3",
      "chips": ["Vue 3 Composition API", "Vite:8090", "TypeScript (strict無効)", "Pinia + Vue Router"],
      "metrics": [
        { "label": "ポート", "value": "8090" },
        { "label": "フレームワーク", "value": "Vue 3 + Vite" },
        { "label": "状態管理", "value": "Pinia" }
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
        { "source": "frontend_web/AGENTS.md", "text": "Vue 3。Vite。TypeScript。Vue Router。Pinia。Axios。dayjs。Monaco Editor。qTubler 独自テーブル。" },
        { "source": "frontend_web,実装パターン.md", "text": "Vue 3 Composition API と `<script setup lang=\"ts\">` を使う。UI framework / CSS framework は使わず、既存 CSS と共有コンポーネントへ合わせる。TypeScript は strict mode 無効の設定で運用しているが、不要な `any` の拡大は避ける。" }
      ]
    },
    {
      "id": "scene_002",
      "title": "コンポーネント配置と Router",
      "start_sec": 25.0,
      "duration_sec": 14.0,
      "expression": "neutral",
      "accent": "#ff8a6b",
      "accent_soft": "rgba(255,138,107,0.18)",
      "kicker": "COMPONENTS & ROUTER",
      "headline": "接頭辞別にフォルダ分け、\nRouter は 3 ファイル構成",
      "lead": "C系は C管理、M系は Mマスタ、T系は Tトラン、V系は Vビュー、S系は Sスケジューラー、X系は Xその他。Router は index.ts / coreRouter.ts / appsRouter.ts の 3 ファイルで分担します。",
      "subtitle": "コンポーネントは接頭辞別フォルダ。Router は index.ts / coreRouter.ts / appsRouter.ts の 3 分割。",
      "narration": "画面ファイルは接頭辞ごとにフォルダを分けます。Router は 3 つのファイルに分割されています。日本語名コンポーネントは component コロン is で呼び出します。",
      "image": "images/scene_002.png",
      "audio": "audio/scene_002.mp3",
      "chips": ["C管理/Mマスタ/Tトラン/Vビュー", "Sスケジューラー/Xその他", "Router 3分割", "<component :is>"],
      "metrics": [
        { "label": "コンポーネントフォルダ", "value": "6カテゴリ" },
        { "label": "Router ファイル", "value": "3" },
        { "label": "日本語タグ問題", "value": "<component :is>" }
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
        { "source": "frontend_web/AGENTS.md", "text": "日本語 component は import して `<component :is=\"...\">` で扱う。" },
        { "source": "frontend_web,実装パターン.md", "text": "よくある落とし穴: `<C利用者一覧 />` のような日本語タグを書くとブラウザで無効扱いになる。" }
      ]
    },
    {
      "id": "scene_003",
      "title": "qTubler — 独自グリッドコンポーネント",
      "start_sec": 39.0,
      "duration_sec": 14.0,
      "expression": "neutral",
      "accent": "#00e0b8",
      "accent_soft": "rgba(0,224,184,0.18)",
      "kicker": "qTUBLER",
      "headline": "ソート・ページング・行選択を持つ\n独自テーブル qTubler",
      "lead": "`_share/qTublerFrame.vue` が主要グリッドです。外部 UI framework に置き換えない方針で、`columns`・`rows`・`totalCount`・`currentPage`・`sortKey` などを props で渡し、sort/page イベントで再取得します。",
      "subtitle": "qTublerFrame.vue が標準一覧テーブル。sort/page イベントで V系 API を再取得する。",
      "narration": "qTubler は AiDiy 独自の一覧テーブルです。列定義と行データを渡すとページングとソートが使えます。",
      "image": "images/scene_003.png",
      "audio": "audio/scene_003.mp3",
      "chips": ["qTublerFrame.vue", "columns / rows / totalCount", "sort / page イベント", "V系 API 連携"],
      "metrics": [
        { "label": "コアファイル", "value": "qTublerFrame.vue" },
        { "label": "標準 props", "value": "8種" },
        { "label": "イベント", "value": "sort / page" }
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
        { "source": "frontend_web/AGENTS.md", "text": "qTubler は `_share/qTublerFrame.vue` を中心にした独自テーブルです。ソート、ページング、行選択を持ち、外部 UI framework へ置き換えない方針です。" },
        { "source": "frontend_web,実装パターン.md", "text": "`columns` は `types/qTubler.ts` の型に合わせる。`rows`、`rowKey`、`totalCount`、`totalAll`、`currentPage`、`totalPages`、`sortKey`、`sortOrder` を渡す。sort / page イベントで再取得する。" }
      ]
    },
    {
      "id": "scene_004",
      "title": "認証と Vite Proxy",
      "start_sec": 53.0,
      "duration_sec": 13.0,
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196,155,255,0.18)",
      "kicker": "AUTH & PROXY",
      "headline": "JWT を localStorage に保存し、\n401 は interceptor でログアウト",
      "lead": "token と user を `localStorage` に保存します。401 は Axios response interceptor でログアウト処理へ流れます。API は `/core/*` → 8091、`/apps/*` → 8092 に Vite proxy 経由で転送します。",
      "subtitle": "localStorage + Axios interceptor。Vite proxy で /core→8091、/apps→8092 に転送。",
      "narration": "ログイン後のトークンは localStorage に保存します。API の /core と /apps は自動的に backend に振り分けられます。",
      "image": "images/scene_004.png",
      "audio": "audio/scene_004.mp3",
      "chips": ["JWT localStorage", "Axios interceptor", "/core→8091", "/apps→8092"],
      "metrics": [
        { "label": "token 保存先", "value": "localStorage" },
        { "label": "401 処理", "value": "interceptor 自動ログアウト" },
        { "label": "proxy 先", "value": "8091 / 8092" }
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
        { "source": "frontend_web/AGENTS.md", "text": "JWT token と user は `frontend_web` では `localStorage` に保存します。401 は Axios response interceptor でログアウト処理へ流します。" },
        { "source": "frontend_web,実装パターン.md", "text": "よくある落とし穴: Vite proxy を使わず `http://localhost:8091` へ直叩きして CORS 条件が変わる。" }
      ]
    },
    {
      "id": "scene_005",
      "title": "AIコア画面連携",
      "start_sec": 66.0,
      "duration_sec": 14.0,
      "expression": "neutral",
      "accent": "#ffd166",
      "accent_soft": "rgba(255,209,102,0.18)",
      "kicker": "AI INTEGRATION",
      "headline": "WebSocket で backend AIコアと接続し、\ncode1〜code6・チャット・音声を統合",
      "lead": "`ws://…/core/ws/AIコア` に WebSocket 接続し、テキスト・ファイル・画像・コード支援・音声を統合するパネルを提供します。AIWebSocket は再接続ポリシーとメッセージディスパッチを持ちます。",
      "subtitle": "WebSocket でAIコアと通信。code1〜code6 パネル、チャット、ファイル、音声を統合。",
      "narration": "AI 画面は WebSocket で backend と繋がります。接続後にセッション ID が決まり、テキストや音声を送受信できます。",
      "image": "images/scene_005.png",
      "audio": "audio/scene_005.mp3",
      "chips": ["AIWebSocket 再接続", "code1〜code6", "チャット/ファイル/音声", "sessionId確定"],
      "metrics": [
        { "label": "WebSocket エンドポイント", "value": "/core/ws/AIコア" },
        { "label": "コードパネル", "value": "6 (code1〜6)" },
        { "label": "入力種別", "value": "テキスト/ファイル/画像/音声" }
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
        { "source": "backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md", "text": "エンドポイントは `ws://<host>/core/ws/AIコア`。接続時に `{ type: \"connect\", セッションID, ソケット番号 }` を送信し、サーバーから `{ メッセージ識別: \"init\", セッションID: \"<確定ID>\" }` を受けて sessionId が確定する。" },
        { "source": "frontend_web/AGENTS.md", "text": "`frontend_web` 版 AI コアは backend の `/core/AIコア` と WebSocket で接続します。code1〜code6、ファイル、画像、チャット、設定ダイアログを扱います。" }
      ]
    },
    {
      "id": "scene_006",
      "title": "X系と Monaco Editor",
      "start_sec": 80.0,
      "duration_sec": 14.0,
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125,255,179,0.18)",
      "kicker": "X-SERIES & MONACO",
      "headline": "X系でゲーム・デモ・静的ページを追加し、\nMonaco Editor でコード編集",
      "lead": "X系はルーター登録で動く通常コンポーネントと、`public/` に直置きする静的 HTML ページの 2 パターンがあります。Monaco Editor は言語マッピング `モナコ言語推定()` と Worker 構成を共通化しています。",
      "subtitle": "X系は Vue コンポーネントと public/ 静的 HTML の 2 パターン。Monaco は Worker 共通化。",
      "narration": "X 系はゲームやデモなど実験的な機能の置き場所です。Vue コンポーネントか HTML 直置きの 2 通りで追加できます。",
      "image": "images/scene_006.png",
      "audio": "audio/scene_006.mp3",
      "chips": ["Xテトリス", "X世界の絶景", "public/ 直置き HTML", "Monaco 言語マッピング"],
      "metrics": [
        { "label": "X系パターン", "value": "2種" },
        { "label": "Monaco Worker", "value": "共通化" },
        { "label": "担当 Router", "value": "index.ts" }
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
        { "source": "frontend_web/AGENTS.md", "text": "X系は `components/Xその他/` と `public/` を見る。" },
        { "source": "CLAUDE.md", "text": "共通項目: Monaco Editor 設定 — Worker 構成、拡張子→言語マッピング（`モナコ言語推定()`）。qAlert / qConfirm / qColorPicker — シングルトンダイアログパターン。" }
      ]
    },
    {
      "id": "scene_999",
      "title": "ご視聴ありがとうございました",
      "start_sec": 94.0,
      "duration_sec": 16.0,
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123,140,255,0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "AIDIY FRONTEND",
      "headline": "ご視聴ありがとうございました。\nどの画面から実装しますか？",
      "lead": "Vue 3・qTubler・接頭辞別コンポーネント・Router 3分割・Vite proxy・JWT interceptor・AIコア WebSocket。業務画面は既存パターンを参考にどうぞ。",
      "subtitle": "frontend_web — Vue 3、qTubler、接頭辞別コンポーネント、Vite proxy、AIコア WebSocket。",
      "narration": "Vue 3、qTubler、Vite proxy、JWT 認証、AI 連携。既存画面を参考に作ってみてください。",
      "image": "images/scene_999.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "audio": "audio/scene_999.mp3"
    }
  ],
  "duration_sec": 110.0
}
