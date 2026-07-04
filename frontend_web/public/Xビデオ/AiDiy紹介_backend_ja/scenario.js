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
    "format": "html_css_scene_player_with_media",
    "tone": "事実ベース、簡潔、根拠付き",
    "goal": "backend_server の 2 サーバー構成・4 層アーキテクチャ・テーブル命名規則・採番・監査フィールド・V系を正確に伝える。"
  },
  "assets_policy": {
    "visual_style": "left_avatar_38_right_content_62",
    "audio_dir": "audio",
    "image_dir": "images",
    "avatar": "../_vrm/VRM_AiDiy.vrm",
    "tts_provider": "freeai:female"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "この動画で紹介すること",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41,216,255,0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "INTRODUCTION",
      "headline": "この動画では、AiDiy backend_server の\n設計と実装パターンを紹介します",
      "lead": "2 サーバー構成・4 層アーキテクチャ・日本語ファースト命名・採番・監査フィールド・V系まで、実装に沿って見ていきます。",
      "subtitle": "backend_server の 2 サーバー構成、4 層アーキテクチャ、命名規則、採番、V系を紹介します。",
      "image": "images/scene_000.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "short_narration": "AiDiy のバックエンドは Python 製ウェブサーバー 2 本構成です。設計ルールと実装パターンを紹介します。",
      "long_narration": "この動画では、AiDiy のバックエンドサーバーを詳しく紹介します。バックエンドとは、画面の裏側でデータを保存したり計算したりするプログラムのことです。AiDiy のバックエンドは Python という言語と FastAPI という最新フレームワークで動いています。コードの書き方がパターン化されているため、「配送管理の機能を追加して」と AI に指示するだけで、データベースの設計から API まで一気に作れます。業務の言葉をそのままコードの名前に使うシンプルなルール、ID の自動管理、更新履歴の自動保存、複数テーブルを組み合わせた検索 API まで、実装に沿って順番に見ていきます。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_duration_sec": 7.776,
      "long_duration_sec": 40.104
    },
    {
      "id": "scene_001",
      "title": "2 サーバー構成",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41,216,255,0.18)",
      "kicker": "DUAL SERVER",
      "headline": "core_main (8091) と apps_main (9098) が\n同じ SQLite DB を共有",
      "lead": "Core は C系・A系・認証・AIコアを担当し、Apps は M系・T系・V系・S系を担当します。DB ファイルは `backend_server/_data/AiDiy/database.db` の1ファイルを両サーバーで共有します。",
      "subtitle": "core_main:8091 と apps_main:9098 が同一 SQLite DB を共有する 2 サーバー構成。",
      "image": "images/scene_001.png",
      "chips": [
        "core_main:8091",
        "apps_main:9098",
        "SQLite 共有",
        "FastAPI"
      ],
      "metrics": [
        {
          "label": "サーバー数",
          "value": "2"
        },
        {
          "label": "DB",
          "value": "SQLite 共有"
        },
        {
          "label": "フレームワーク",
          "value": "FastAPI"
        }
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
          "title": "apps_main (9098)",
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
        "`core_main.py` はポート 8091、`apps_main.py` はポート 9098 で起動する。",
        "両サーバーは `backend_server/_data/AiDiy/database.db` の同一 SQLite ファイルを共有する。",
        "技術スタック: Python 3.13、FastAPI、SQLAlchemy、SQLite、uv、Pydantic、JWT。"
      ],
      "evidence": [
        {
          "source": "backend_server/AGENTS.md",
          "text": "`core_main.py`：C系、A系、認証、files、AIコア（ポート 8091）。`apps_main.py`：M系、T系、V系、S系（ポート 9098）。"
        },
        {
          "source": "backend_server/AGENTS.md",
          "text": "DB ファイルは `backend_server/_data/AiDiy/database.db` です。`core_main.py` と `apps_main.py` は同じ SQLite DB を共有します。"
        }
      ],
      "short_narration": "Core（認証・AI）と Apps（業務機能）の 2 本構成で、データベースを共有します。",
      "long_narration": "バックエンドは 2 本のサーバーで動いています。1 本目は Core サーバー（ポート 8091）で、ログイン認証・利用者管理・AI 機能を担当します。2 本目は Apps サーバー（ポート 9098）で、配車・生産・在庫などの業務機能を担当します。2 本は同じデータベースを共有しているため、データは 1 か所にまとまります。言語は Python 3.13、Web API の仕組みは FastAPI という最新フレームワークを使っています。FastAPI は速く動き、API の仕様書（Swagger）を自動で作成してくれるのが特徴です。Swagger 画面をブラウザで開けば、フロントエンドなしで直接 API の動作確認ができます。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_duration_sec": 6.6,
      "long_duration_sec": 45.288
    },
    {
      "id": "scene_002",
      "title": "テーブル命名と日本語ファースト",
      "expression": "neutral",
      "accent": "#ff8a6b",
      "accent_soft": "rgba(255,138,107,0.18)",
      "kicker": "JAPANESE FIRST",
      "headline": "テーブル名・カラム名・API パスまで\nすべて日本語識別子",
      "lead": "接頭辞 C / A / M / T / V / S / X で種別と担当サーバーを区別。API パスは `/core/利用者/一覧`、JSON キーは `{\"利用者名\": \"admin\"}` など、全レイヤーで日本語を統一します。",
      "subtitle": "全レイヤー日本語識別子。接頭辞 C/A/M/T/V/S/X で種別を区別。",
      "image": "images/scene_002.png",
      "chips": [
        "C: Core",
        "M: Master",
        "T: Transaction",
        "V: View",
        "S: Scheduler",
        "A: AI"
      ],
      "metrics": [
        {
          "label": "命名レイヤー",
          "value": "全レイヤー"
        },
        {
          "label": "接頭辞種別",
          "value": "7種"
        },
        {
          "label": "例外",
          "value": "英字ライブラリ名"
        }
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
        {
          "source": "CLAUDE.md",
          "text": "全レイヤーで日本語識別子を使います。テーブル名: `C権限`、`T配車`、`M商品構成`。カラム名: `利用者ID`、`配車日付`、`商品名`。API パス: `/core/利用者/一覧`、`/apps/配車/検索`。"
        },
        {
          "source": "CLAUDE.md",
          "text": "システム用語（`request`、`query`、`items`、`total`、`limit`）や英字ライブラリ名はそのまま使用します。"
        }
      ],
      "short_narration": "テーブル名・API パス・変数名はすべて日本語です。業務用語とコードを直結させます。",
      "long_narration": "AiDiy のユニークなルールは、テーブル名・列名・API のパス・変数名をすべて日本語で書くことです。たとえばテーブル名は「T配車」、API のパスは「/apps/配車/登録」、列名は「配車日付」のように書きます。このルールのおかげで AI への指示がとてもシンプルになります。「T配車テーブルに配車先住所の列を追加して API を作って」という日本語の指示が、そのままコードの名前として使われるからです。設計書の業務用語とプログラムの名前が一致しているので、AI もコードの意図を正確に理解できます。ただし request・query・items などのシステム用語や FastAPI などのライブラリ名は英語のまま使います。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_duration_sec": 7.68,
      "long_duration_sec": 44.28
    },
    {
      "id": "scene_003",
      "title": "4層アーキテクチャ",
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196,155,255,0.18)",
      "kicker": "4-LAYER",
      "headline": "Model → Schema → CRUD → Router の\n4 層で新機能を実装",
      "lead": "新規 M/T/C 機能はすべてこの 4 層で実装します。加えて `apps_main.py` への router 登録と `__init__.py` への import 追加が必要です。",
      "subtitle": "Model / Schema / CRUD / Router + Main登録の5ステップ。落とし穴は __init__.py 追加漏れ。",
      "image": "images/scene_003.png",
      "chips": [
        "SQLAlchemy Model",
        "Pydantic Schema",
        "CRUD",
        "FastAPI Router"
      ],
      "metrics": [
        {
          "label": "層数",
          "value": "4 (+1登録)"
        },
        {
          "label": "CRUD メソッド",
          "value": "POST 統一"
        },
        {
          "label": "レスポンス形式",
          "value": "統一形式"
        }
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
        {
          "source": "backend_server,実装パターン.md",
          "text": "新規テーブルや機能は、原則として Model / Schema / CRUD / Router / Main の層を揃える。"
        },
        {
          "source": "backend_server,実装パターン.md",
          "text": "よくある落とし穴: `apps_crud/__init__.py` の import / `__all__` 追加漏れ。`apps_models/__init__.py` の import 追加漏れにより `create_all()` 対象外になる。"
        }
      ],
      "short_narration": "新機能は Model・Schema・CRUD・Router の 4 ファイルで追加します。統一パターンで迷いません。",
      "long_narration": "新しい機能を追加するとき、バックエンドでは 4 種類のファイルを作ります。データベースの構造を決める Model、入出力の形を決める Schema、データの取得・保存を書く CRUD、API の窓口となる Router です。このパターンが全機能で統一されているので、AI への指示がシンプルです。「M商品と同じ 4 層パターンで、M顧客マスタを追加して」の一言で、Model から Router まで 4 ファイルを一気に生成します。できたら起動ファイルに Router を 1 行登録するだけで API が動き出します。サンプルコードがお手本になるので、AI は細かいルールを指示しなくても AiDiy の書き方に沿ったコードを作れます。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_duration_sec": 7.608,
      "long_duration_sec": 41.952
    },
    {
      "id": "scene_004",
      "title": "採番と監査フィールド",
      "expression": "neutral",
      "accent": "#00e0b8",
      "accent_soft": "rgba(0,224,184,0.18)",
      "kicker": "NUMBERING & AUDIT",
      "headline": "AUTOINCREMENT 非依存の C採番と\n全テーブル共通 8 監査フィールド",
      "lead": "`C採番` テーブルで採番を一元管理し、AUTOINCREMENT に依存しません。全テーブルに登録/更新 × 日時/利用者ID/利用者名/端末ID の 8 フィールドが必須です。",
      "subtitle": "採番は get_next_id()、監査は create_audit_fields() / update_audit_fields() で統一。",
      "image": "images/scene_004.png",
      "chips": [
        "C採番テーブル",
        "get_next_id()",
        "create_audit_fields()",
        "update_audit_fields()"
      ],
      "metrics": [
        {
          "label": "監査フィールド数",
          "value": "8"
        },
        {
          "label": "採番方式",
          "value": "C採番 (非AUTOINCREMENT)"
        },
        {
          "label": "ヘルパー関数",
          "value": "2種"
        }
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
        {
          "source": "backend_server,C採番と監査フィールド.md",
          "text": "AUTOINCREMENT を前提にしない。採番が必要なテーブルは `C採番` に初期値を追加する。"
        },
        {
          "source": "backend_server,C採番と監査フィールド.md",
          "text": "全テーブルに 8 フィールド: 登録日時・登録利用者ID・登録利用者名・登録端末ID・更新日時・更新利用者ID・更新利用者名・更新端末ID。"
        }
      ],
      "short_narration": "ID は C採番テーブルで管理します。全テーブルに 8 項目の監査フィールドが必須です。",
      "long_narration": "AiDiy には 2 つの便利な仕組みが標準で入っています。1 つは C採番テーブルによる ID の自動発行です。テーブルごとに連番を管理するので、複数のテーブルで ID が重ならない設計が簡単にできます。2 つ目は全テーブルに必須の 8 つの更新記録項目です。登録した日時・利用者名・端末 ID と、更新した日時・利用者名・端末 ID が自動でセットされます。この仕組みが標準で入っていることで、AI が機能を生成するとき ID 発行と更新記録の処理をゼロから考えなくて済みます。誰がいつ変更したかをあとから必ず追跡できるため、業務システムとしての信頼性も高まります。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_duration_sec": 6.912,
      "long_duration_sec": 44.136
    },
    {
      "id": "scene_005",
      "title": "V系ビュー（生 SQL JOIN）",
      "expression": "neutral",
      "accent": "#ffd166",
      "accent_soft": "rgba(255,209,102,0.18)",
      "kicker": "V-SERIES VIEW",
      "headline": "DB VIEW を作らず、V系 Router に\n生 SQL で JOIN・集計",
      "lead": "V系は Model / CRUD 層を持たず、Router 内に生 SQL を直接書きます。`SELECT` と `COUNT(*)` は同じ FROM / JOIN / WHERE を使い、SQL には bind params を使います。",
      "subtitle": "DB VIEW オブジェクトなし。V系 Router に生 SQL。一覧の items と total は同一条件で取得。",
      "image": "images/scene_005.png",
      "chips": [
        "生 SQL JOIN",
        "bind params",
        "items + total",
        "dict(row._mapping)"
      ],
      "metrics": [
        {
          "label": "作成ファイル",
          "value": "Router のみ"
        },
        {
          "label": "DB VIEW",
          "value": "なし"
        },
        {
          "label": "担当",
          "value": "core/apps 双方"
        }
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
        {
          "source": "backend_server,実装パターン.md",
          "text": "DB VIEW オブジェクトは作らない。`core_router/V*.py` または `apps_router/V*.py` に生 SQL を書く。`SELECT` と `COUNT(*)` は同じ FROM / JOIN / WHERE 条件を使う。SQL へ値を直結せず、bind params を使う。"
        },
        {
          "source": "backend_server/AGENTS.md",
          "text": "DB VIEW オブジェクトは作らず、V系 Router の生 SQL で JOIN / 集計する。"
        }
      ],
      "short_narration": "複数テーブルを集約して返す V 系は、SQL を Router に直接書くシンプルなパターンです。",
      "long_narration": "V 系は、複数のテーブルを組み合わせて一覧データを返す API のグループです。データベースに VIEW という仕組みを作る代わりに、Router ファイルに SQL を直接書くシンプルな作りにしています。たとえば「取引先と取引先分類を結合して一覧を返す」という処理は、Router に SQL を書いてパラメータを渡すだけです。AI への指示は「V系パターンで商品在庫一覧の API を作って」の一言で済みます。AI はサンプルの V 系コードを見て、検索条件・ページング・件数取得まで揃ったコードを同じパターンで生成します。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_duration_sec": 6.672,
      "long_duration_sec": 37.8
    },
    {
      "id": "scene_006",
      "title": "業務サンプルと S系スケジューラ",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125,255,179,0.18)",
      "kicker": "BUSINESS SAMPLES",
      "headline": "配車・生産・商品管理など\n実装済みの業務サンプル",
      "lead": "M系 9 テーブル・T系 5 テーブル・S系 4 エンドポイントの業務サンプルが実装済み。明細型は `明細SEQ=0` をヘッダー予約、複合主キーで管理します。",
      "subtitle": "M系9・T系5・S系4の業務サンプル実装済み。明細型パターンは M商品構成・T生産が代表実装。",
      "image": "images/scene_006.png",
      "chips": [
        "M系 ×9",
        "T系 ×5",
        "S系 ×4",
        "明細型パターン"
      ],
      "metrics": [
        {
          "label": "M系テーブル",
          "value": "9"
        },
        {
          "label": "T系テーブル",
          "value": "5"
        },
        {
          "label": "S系エンドポイント",
          "value": "4"
        }
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
        {
          "source": "backend_server/AGENTS.md",
          "text": "Apps: M配車区分・M車両・M商品・M商品分類・M取引先分類・M取引先・M生産区分・M生産工程・M商品構成。T配車・T生産・T商品入庫・T商品出庫・T商品棚卸。S配車_*・S生産_*。"
        },
        {
          "source": "backend_server,実装パターン.md",
          "text": "明細型: `明細SEQ=0` をヘッダー行に予約する。`(親ID, 明細SEQ)` の複合主キーを使う。更新時は対象親IDの既存行を全削除して、ヘッダー + 明細を再作成する。"
        }
      ],
      "short_narration": "M 系 9・T 系 5 のサンプルが実装済みです。AI のお手本になり、すぐ新機能を追加できます。",
      "long_narration": "AiDiy の業務サンプルは「学習教材」というより「AI がコードを生成するときのお手本」として設計されています。マスタ系 9 テーブル・トランザクション系 5 テーブル・スケジューラ 4 種類が、4 層パターンで統一された形で実装されています。AI への指示はシンプルです。「M商品構成と同じパターンで M顧客マスタを追加して」と言えば、Model から Router まで 4 層を一気に生成します。明細行を持つ T生産のパターンを見せれば、親レコードと明細行を同時に扱う機能も作れます。スケジューラ S配車のお手本があれば、定期実行の集計機能も同じように作れます。",
      "short_audio": "audio/short_scene_006.mp3",
      "long_audio": "audio/long_scene_006.mp3",
      "short_duration_sec": 7.752,
      "long_duration_sec": 40.536
    },
    {
      "id": "scene_999",
      "title": "ご視聴ありがとうございました",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41,216,255,0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "AIDIY BACKEND",
      "headline": "ご視聴ありがとうございました。\nどのテーブルから実装しますか？",
      "lead": "2 サーバー・4 層・日本語ファースト・C採番・8 監査フィールド・V系生 SQL。業務サンプルを参考に、あなたの業務テーブルを追加してみてください。",
      "subtitle": "backend_server — 2 サーバー構成、4 層アーキテクチャ、日本語ファースト、C採番、V系生 SQL。",
      "image": "images/scene_999.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "short_narration": "AI の指示一つで API から画面まで一気に作れます。AiDiy で業務システムを作ってみませんか。",
      "long_narration": "AiDiy の AI コーディング機能を使えば、バックエンドとフロントエンドを一気通貫で生成できます。「配送管理の一覧・登録・編集機能を追加して」と AI に指示するだけで、サーバー側の API とフロントエンドの画面が同時に出来上がります。サンプルコードが AI のお手本になるので、4 層パターン・日本語ルール・テーブル設計を細かく指示しなくても、AiDiy のルールに沿ったコードを生成します。開発環境を立ち上げ、AI に機能を頼み、動作確認する。このサイクルで業務システムをどんどん育てていけます。今日から使える業務システムを、AiDiy で作ってみませんか。",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_duration_sec": 7.536,
      "long_duration_sec": 39.672
    }
  ],
  "short_duration_sec": 58.536,
  "long_duration_sec": 333.768
};
