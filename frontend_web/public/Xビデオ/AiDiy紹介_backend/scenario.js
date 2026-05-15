window.SCENARIO = {
  "project_name": "AiDiy紹介backend",
  "version": "backend",
  "title": "AiDiy backend_server - 4層構造と日本語ファースト設計",
  "source": {
    "type": "agents_and_knowledge",
    "summary": "backend_server/AGENTS.md、.aidiy/knowledge の実装パターン・採番・監査フィールド・M系T系追加手順から実装実態を抜粋して構成。"
  },
  "target": {
    "language": "ja-JP",
    "duration_sec": 112.0,
    "format": "html_css_scene_player_with_media",
    "tone": "事実ベース、簡潔、根拠付き",
    "goal": "backend_server の 2 サーバー構成・4 層アーキテクチャ・テーブル命名規則・採番・監査フィールド・V系を正確に伝える。"
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
      "accent": "#29d8ff",
      "accent_soft": "rgba(41,216,255,0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "INTRODUCTION",
      "headline": "この動画では、AiDiy backend_server の\n設計と実装パターンを紹介します",
      "lead": "2 サーバー構成・4 層アーキテクチャ・日本語ファースト命名・採番・監査フィールド・V系まで、実装に沿って見ていきます。",
      "subtitle": "backend_server の 2 サーバー構成、4 層アーキテクチャ、命名規則、採番、V系を紹介します。",
      "narration": "この動画では、AiDiy の backend_server を紹介します。2 サーバー構成と 4 層アーキテクチャ、日本語ファースト命名、採番と監査フィールド、V系ビューまで、実装に沿って見ていきます。",
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
      "title": "2 サーバー構成",
      "start_sec": 12.0,
      "duration_sec": 14.0,
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41,216,255,0.18)",
      "kicker": "DUAL SERVER",
      "headline": "core_main (8091) と apps_main (8092) が\n同じ SQLite DB を共有",
      "lead": "Core は C系・A系・認証・AIコアを担当し、Apps は M系・T系・V系・S系を担当します。DB ファイルは `backend_server/_data/AiDiy/database.db` の1ファイルを両サーバーで共有します。",
      "subtitle": "core_main:8091 と apps_main:8092 が同一 SQLite DB を共有する 2 サーバー構成。",
      "narration": "backend_server は core_main と apps_main の 2 サーバー構成です。core_main はポート 8091 で C系、A系、認証、AIコアを担当。apps_main はポート 8092 で M系、T系、V系、S系を担当します。両サーバーは同じ SQLite DB ファイルを共有します。",
      "image": "images/scene_001.png",
      "audio": "audio/scene_001.mp3",
      "chips": ["core_main:8091", "apps_main:8092", "SQLite 共有", "FastAPI"],
      "metrics": [
        { "label": "サーバー数", "value": "2" },
        { "label": "DB", "value": "SQLite 共有" },
        { "label": "フレームワーク", "value": "FastAPI" }
      ],
      "cards": [
        {
          "title": "core_main (8091)",
          "lines": [
            "C権限 / C利用者 / C採番",
            "A会話履歴",
            "認証 (JWT) / files / AIコア"
          ]
        },
        {
          "title": "apps_main (8092)",
          "lines": [
            "M系: M配車区分、M車両、M商品、M商品構成 など",
            "T系: T配車、T生産、T商品入出庫・棚卸",
            "V系一覧 / S系スケジューラ"
          ]
        },
        {
          "title": "共通基盤",
          "lines": [
            "DB: `_data/AiDiy/database.db`",
            "Python 3.13 + FastAPI + SQLAlchemy",
            "認証: JWT (`python-jose`), uv で依存管理"
          ]
        }
      ],
      "facts": [
        "`core_main.py` はポート 8091、`apps_main.py` はポート 8092 で起動する。",
        "両サーバーは `backend_server/_data/AiDiy/database.db` の同一 SQLite ファイルを共有する。",
        "技術スタック: Python 3.13、FastAPI、SQLAlchemy、SQLite、uv、Pydantic、JWT。"
      ],
      "evidence": [
        { "source": "backend_server/AGENTS.md", "text": "`core_main.py`：C系、A系、認証、files、AIコア（ポート 8091）。`apps_main.py`：M系、T系、V系、S系（ポート 8092）。" },
        { "source": "backend_server/AGENTS.md", "text": "DB ファイルは `backend_server/_data/AiDiy/database.db` です。`core_main.py` と `apps_main.py` は同じ SQLite DB を共有します。" }
      ]
    },
    {
      "id": "scene_002",
      "title": "テーブル命名と日本語ファースト",
      "start_sec": 26.0,
      "duration_sec": 14.0,
      "expression": "neutral",
      "accent": "#ff8a6b",
      "accent_soft": "rgba(255,138,107,0.18)",
      "kicker": "JAPANESE FIRST",
      "headline": "テーブル名・カラム名・API パスまで\nすべて日本語識別子",
      "lead": "接頭辞 C / A / M / T / V / S / X で種別と担当サーバーを区別。API パスは `/core/利用者/一覧`、JSON キーは `{\"利用者名\": \"admin\"}` など、全レイヤーで日本語を統一します。",
      "subtitle": "全レイヤー日本語識別子。接頭辞 C/A/M/T/V/S/X で種別を区別。",
      "narration": "AiDiy は全レイヤーで日本語識別子を使う「日本語ファースト設計」です。テーブル名・カラム名・API パス・JSON キー・ファイル名・Vue コンポーネント名まで日本語で統一します。接頭辞 C が Core 共通、A が AI、M がマスタ、T がトランザクション、V がビュー、S がスケジューラ、X が実験的機能を表します。",
      "image": "images/scene_002.png",
      "audio": "audio/scene_002.mp3",
      "chips": ["C: Core", "M: Master", "T: Transaction", "V: View", "S: Scheduler", "A: AI"],
      "metrics": [
        { "label": "命名レイヤー", "value": "全レイヤー" },
        { "label": "接頭辞種別", "value": "7種" },
        { "label": "例外", "value": "英字ライブラリ名" }
      ],
      "cards": [
        {
          "title": "接頭辞と担当",
          "lines": [
            "C — Core 共通 (core_main)",
            "A — AI / A会話履歴 (core_main)",
            "M — マスタ、T — トランザクション、V — ビュー、S — スケジューラ (apps_main)"
          ]
        },
        {
          "title": "日本語識別子の範囲",
          "lines": [
            "テーブル名: `C権限`、`T配車`、`M商品構成`",
            "カラム名: `利用者ID`、`配車日付`",
            "API パス: `/core/利用者/一覧`",
            "JSON キー: `{\"利用者名\": \"admin\"}`"
          ]
        },
        {
          "title": "例外",
          "lines": [
            "`request`、`query`、`items`、`total`、`limit` はシステム用語として英字",
            "英字ライブラリ名はそのまま使用",
            "X系: `Xテトリス`、`X世界の絶景`（frontend_web 担当）"
          ]
        }
      ],
      "facts": [
        "全レイヤー（テーブル名・カラム名・API パス・JSON キー・ファイル名）で日本語識別子を使う。",
        "接頭辞 C/A は core_main、M/T/V/S は apps_main、X は frontend_web が担当。",
        "`request`・`query`・`items`・`total`・`limit` などシステム用語と英字ライブラリ名は英字のまま。"
      ],
      "evidence": [
        { "source": "CLAUDE.md", "text": "全レイヤーで日本語識別子を使います。テーブル名: `C権限`、`T配車`、`M商品構成`。カラム名: `利用者ID`、`配車日付`、`商品名`。API パス: `/core/利用者/一覧`、`/apps/配車/検索`。" },
        { "source": "CLAUDE.md", "text": "システム用語（`request`、`query`、`items`、`total`、`limit`）や英字ライブラリ名はそのまま使用します。" }
      ]
    },
    {
      "id": "scene_003",
      "title": "4層アーキテクチャ",
      "start_sec": 40.0,
      "duration_sec": 14.0,
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196,155,255,0.18)",
      "kicker": "4-LAYER",
      "headline": "Model → Schema → CRUD → Router の\n4 層で新機能を実装",
      "lead": "新規 M/T/C 機能はすべてこの 4 層で実装します。加えて `apps_main.py` への router 登録と `__init__.py` への import 追加が必要です。",
      "subtitle": "Model / Schema / CRUD / Router + Main登録の5ステップ。落とし穴は __init__.py 追加漏れ。",
      "narration": "新規機能の実装は Model、Schema、CRUD、Router の 4 層構造に従います。Model は SQLAlchemy テーブル定義、Schema は Pydantic のリクエスト・レスポンス定義、CRUD は DB アクセスロジック、Router は FastAPI のエンドポイントです。最後に apps_main.py への include_router 登録と __init__.py への import 追加が必要です。これを漏らすと create_all で対象外になります。",
      "image": "images/scene_003.png",
      "audio": "audio/scene_003.mp3",
      "chips": ["SQLAlchemy Model", "Pydantic Schema", "CRUD", "FastAPI Router"],
      "metrics": [
        { "label": "層数", "value": "4 (+1登録)" },
        { "label": "CRUD メソッド", "value": "POST 統一" },
        { "label": "レスポンス形式", "value": "統一形式" }
      ],
      "cards": [
        {
          "title": "4 層の役割",
          "lines": [
            "Model: SQLAlchemy テーブル定義 (`apps_models/`)",
            "Schema: Pydantic request/response (`apps_schema/`)",
            "CRUD: DB アクセスロジック (`apps_crud/`)",
            "Router: FastAPI エンドポイント (`apps_router/`)"
          ]
        },
        {
          "title": "登録漏れの落とし穴",
          "lines": [
            "`apps_models/__init__.py` 追加漏れ → `create_all()` 対象外",
            "`apps_crud/__init__.py` 追加漏れ → import エラー",
            "`apps_main.py` の `include_router` 登録漏れ → Swagger に出ない"
          ]
        },
        {
          "title": "統一レスポンス形式",
          "lines": [
            "`{\"status\": \"OK\", \"message\": \"...\", \"data\": {}}`",
            "例外時は `db.rollback()` してエラーを返す",
            "CRUD エンドポイントは POST 中心"
          ]
        }
      ],
      "facts": [
        "新規テーブルは Model / Schema / CRUD / Router の 4 層を揃える。",
        "`apps_models/__init__.py` の import 追加漏れで `create_all()` 対象外になる。",
        "CRUD エンドポイントは POST 中心、レスポンスは `{status, message, data}` 統一形式。",
        "認証は `deps.get_現在利用者` を Router dependency として使う。"
      ],
      "evidence": [
        { "source": "backend_server,実装パターン.md", "text": "新規テーブルや機能は、原則として Model / Schema / CRUD / Router / Main の層を揃える。" },
        { "source": "backend_server,実装パターン.md", "text": "よくある落とし穴: `apps_crud/__init__.py` の import / `__all__` 追加漏れ。`apps_models/__init__.py` の import 追加漏れにより `create_all()` 対象外になる。" }
      ]
    },
    {
      "id": "scene_004",
      "title": "採番と監査フィールド",
      "start_sec": 54.0,
      "duration_sec": 14.0,
      "expression": "neutral",
      "accent": "#00e0b8",
      "accent_soft": "rgba(0,224,184,0.18)",
      "kicker": "NUMBERING & AUDIT",
      "headline": "AUTOINCREMENT 非依存の C採番と\n全テーブル共通 8 監査フィールド",
      "lead": "`C採番` テーブルで採番を一元管理し、AUTOINCREMENT に依存しません。全テーブルに登録/更新 × 日時/利用者ID/利用者名/端末ID の 8 フィールドが必須です。",
      "subtitle": "採番は get_next_id()、監査は create_audit_fields() / update_audit_fields() で統一。",
      "narration": "AiDiy は AUTOINCREMENT を使わず、C採番テーブルで採番を一元管理します。新規レコード作成前に get_next_id() で ID を取得します。全テーブルに 8 フィールドの監査情報が必須です。登録時は create_audit_fields()、更新時は update_audit_fields() を使い、個別実装で監査日時を直接作らないのがルールです。",
      "image": "images/scene_004.png",
      "audio": "audio/scene_004.mp3",
      "chips": ["C採番テーブル", "get_next_id()", "create_audit_fields()", "update_audit_fields()"],
      "metrics": [
        { "label": "監査フィールド数", "value": "8" },
        { "label": "採番方式", "value": "C採番 (非AUTOINCREMENT)" },
        { "label": "ヘルパー関数", "value": "2種" }
      ],
      "cards": [
        {
          "title": "採番の使い方",
          "lines": [
            "`from core_crud import get_next_id`",
            "`new_id = get_next_id(db, \"テーブル名\")`",
            "新規テーブル追加時は `C採番` に初期値を追加する"
          ]
        },
        {
          "title": "監査フィールド 8 つ",
          "lines": [
            "登録日時 / 登録利用者ID / 登録利用者名 / 登録端末ID",
            "更新日時 / 更新利用者ID / 更新利用者名 / 更新端末ID",
            "登録時 create_audit_fields()、更新時 update_audit_fields()"
          ]
        },
        {
          "title": "注意点",
          "lines": [
            "`C採番` にエントリがないと採番が失敗する",
            "更新時に `create_audit_fields()` を使わない（登録フィールドを上書きしない）",
            "明細型は親IDだけ採番し、明細SEQ はリクエスト順で 0,1,2…"
          ]
        }
      ],
      "facts": [
        "AUTOINCREMENT を使わず `C採番` テーブルで採番を一元管理する。",
        "全テーブルに 8 フィールドの監査情報（登録/更新 × 日時/利用者ID/利用者名/端末ID）が必須。",
        "登録時は `create_audit_fields()`、更新時は `update_audit_fields()` を使う。",
        "新規テーブル追加時は `C採番` に対象テーブル名のエントリを追加する。"
      ],
      "evidence": [
        { "source": "backend_server,C採番と監査フィールド.md", "text": "AUTOINCREMENT を前提にしない。採番が必要なテーブルは `C採番` に初期値を追加する。" },
        { "source": "backend_server,C採番と監査フィールド.md", "text": "全テーブルに 8 フィールド: 登録日時・登録利用者ID・登録利用者名・登録端末ID・更新日時・更新利用者ID・更新利用者名・更新端末ID。" }
      ]
    },
    {
      "id": "scene_005",
      "title": "V系ビュー（生 SQL JOIN）",
      "start_sec": 68.0,
      "duration_sec": 14.0,
      "expression": "neutral",
      "accent": "#ffd166",
      "accent_soft": "rgba(255,209,102,0.18)",
      "kicker": "V-SERIES VIEW",
      "headline": "DB VIEW を作らず、V系 Router に\n生 SQL で JOIN・集計",
      "lead": "V系は Model / CRUD 層を持たず、Router 内に生 SQL を直接書きます。`SELECT` と `COUNT(*)` は同じ FROM / JOIN / WHERE を使い、SQL には bind params を使います。",
      "subtitle": "DB VIEW オブジェクトなし。V系 Router に生 SQL。一覧の items と total は同一条件で取得。",
      "narration": "V系ビューは DB の VIEW オブジェクトを作らず、V系 Router ファイルに生 SQL を直接書きます。Model 層と CRUD 層は作りません。一覧取得では items と total で同じ FROM・JOIN・WHERE を使い、SQL への値埋め込みには bind params を使います。SQLAlchemy の Row は dict(row._mapping) で辞書化します。",
      "image": "images/scene_005.png",
      "audio": "audio/scene_005.mp3",
      "chips": ["生 SQL JOIN", "bind params", "items + total", "dict(row._mapping)"],
      "metrics": [
        { "label": "作成ファイル", "value": "Router のみ" },
        { "label": "DB VIEW", "value": "なし" },
        { "label": "担当", "value": "core/apps 双方" }
      ],
      "cards": [
        {
          "title": "V系の実装ルール",
          "lines": [
            "DB VIEW オブジェクトは作らない",
            "`V*.py` に生 SQL を直接記述",
            "Model 層・CRUD 層は作らない"
          ]
        },
        {
          "title": "一覧 API のパターン",
          "lines": [
            "`items`: 実データ取得 SELECT",
            "`total`: 件数 COUNT(*) — 同じ FROM/JOIN/WHERE",
            "bind params で SQL インジェクション防止"
          ]
        },
        {
          "title": "実装例",
          "lines": [
            "`apps_router/V取引先.py`",
            "`apps_router/V商品構成.py`",
            "`core_router/V*.py`"
          ]
        }
      ],
      "facts": [
        "DB VIEW オブジェクトは作らず、V系 Router に生 SQL を書く。",
        "V系は Model 層・CRUD 層を持たない。",
        "`SELECT` と `COUNT(*)` は同じ FROM / JOIN / WHERE 条件を使う。",
        "SQL への値は bind params で渡し、直結しない。",
        "SQLAlchemy Row は `dict(row._mapping)` で辞書化する。"
      ],
      "evidence": [
        { "source": "backend_server,実装パターン.md", "text": "DB VIEW オブジェクトは作らない。`core_router/V*.py` または `apps_router/V*.py` に生 SQL を書く。`SELECT` と `COUNT(*)` は同じ FROM / JOIN / WHERE 条件を使う。SQL へ値を直結せず、bind params を使う。" },
        { "source": "backend_server/AGENTS.md", "text": "DB VIEW オブジェクトは作らず、V系 Router の生 SQL で JOIN / 集計する。" }
      ]
    },
    {
      "id": "scene_006",
      "title": "業務サンプルと S系スケジューラ",
      "start_sec": 82.0,
      "duration_sec": 14.0,
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125,255,179,0.18)",
      "kicker": "BUSINESS SAMPLES",
      "headline": "配車・生産・商品管理など\n実装済みの業務サンプル",
      "lead": "M系 9 テーブル・T系 5 テーブル・S系 4 エンドポイントの業務サンプルが実装済み。明細型は `明細SEQ=0` をヘッダー予約、複合主キーで管理します。",
      "subtitle": "M系9・T系5・S系4の業務サンプル実装済み。明細型パターンは M商品構成・T生産が代表実装。",
      "narration": "apps_main には業務サンプルとして M系が 9 テーブル、T系が 5 テーブル実装されています。M配車区分・M車両・M商品・M商品分類・M取引先分類・M取引先・M生産区分・M生産工程・M商品構成。T配車・T生産・T商品入庫・T商品出庫・T商品棚卸。S系スケジューラは配車と生産の日表示・週表示が 4 エンドポイント。明細型テーブルは明細SEQ=0 をヘッダー行に予約し、親ID と明細SEQ の複合主キーで管理します。",
      "image": "images/scene_006.png",
      "audio": "audio/scene_006.mp3",
      "chips": ["M系 ×9", "T系 ×5", "S系 ×4", "明細型パターン"],
      "metrics": [
        { "label": "M系テーブル", "value": "9" },
        { "label": "T系テーブル", "value": "5" },
        { "label": "S系エンドポイント", "value": "4" }
      ],
      "cards": [
        {
          "title": "M系マスタ (9テーブル)",
          "lines": [
            "M配車区分 / M車両",
            "M商品 / M商品分類 / M商品構成",
            "M取引先 / M取引先分類 / M生産区分 / M生産工程"
          ]
        },
        {
          "title": "T系トランザクション (5テーブル)",
          "lines": [
            "T配車 / T生産",
            "T商品入庫 / T商品出庫 / T商品棚卸"
          ]
        },
        {
          "title": "明細型パターン",
          "lines": [
            "`明細SEQ=0` をヘッダー行に予約",
            "親ID + 明細SEQ の複合主キー",
            "代表実装: M商品構成・T生産"
          ]
        }
      ],
      "facts": [
        "M系 9 テーブル・T系 5 テーブル・S系 4 エンドポイントの業務サンプルが実装済み。",
        "S系スケジューラは S配車_日表示・S配車_週表示・S生産_日表示・S生産_週表示 の 4 エンドポイント。",
        "明細型は `明細SEQ=0` をヘッダー予約、(親ID, 明細SEQ) の複合主キーで管理する。",
        "更新時は対象親IDの既存行を全削除してヘッダー＋明細を再作成する。"
      ],
      "evidence": [
        { "source": "backend_server/AGENTS.md", "text": "Apps: M配車区分・M車両・M商品・M商品分類・M取引先分類・M取引先・M生産区分・M生産工程・M商品構成。T配車・T生産・T商品入庫・T商品出庫・T商品棚卸。S配車_*・S生産_*。" },
        { "source": "backend_server,実装パターン.md", "text": "明細型: `明細SEQ=0` をヘッダー行に予約する。`(親ID, 明細SEQ)` の複合主キーを使う。更新時は対象親IDの既存行を全削除して、ヘッダー + 明細を再作成する。" }
      ]
    },
    {
      "id": "scene_999",
      "title": "ご視聴ありがとうございました",
      "start_sec": 96.0,
      "duration_sec": 16.0,
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41,216,255,0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "AIDIY BACKEND",
      "headline": "ご視聴ありがとうございました。\nどのテーブルから実装しますか？",
      "lead": "2 サーバー・4 層・日本語ファースト・C採番・8 監査フィールド・V系生 SQL。業務サンプルを参考に、あなたの業務テーブルを追加してみてください。",
      "subtitle": "backend_server — 2 サーバー構成、4 層アーキテクチャ、日本語ファースト、C採番、V系生 SQL。",
      "narration": "ご視聴ありがとうございました。backend_server は core_main と apps_main の 2 サーバーが同じ SQLite DB を共有し、Model・Schema・CRUD・Router の 4 層で業務機能を実装します。日本語ファースト設計、C採番、8 監査フィールド、V系生 SQL。業務サンプルを参考に、あなたの業務テーブルを追加してみてください。",
      "image": "images/scene_999.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "audio": "audio/scene_999.mp3"
    }
  ],
  "duration_sec": 112.0
}
