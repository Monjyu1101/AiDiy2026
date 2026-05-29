window.SCENARIO = {
  "project_name": "AiDiy web版実装例",
  "version": "take3",
  "title": "web版 AiDiy 実装例",
  "source": {
    "type": "screen_capture",
    "summary": "AiDiy の frontend_web（Vue 3 + Vite + TypeScript）の実際の画面キャプチャを使って主要機能を紹介する。"
  },
  "target": {
    "language": "ja-JP",
    "format": "html_css_scene_player_with_media",
    "tone": "Web UIシステム紹介、実用的、使いたくなる",
    "goal": "frontend_web の主要画面を実際の画面キャプチャで紹介する。"
  },
  "assets_policy": {
    "visual_style": "left_image_30_right_explanation_70",
    "audio_dir": "audio",
    "image_dir": "images",
    "avatar": "../vrm/VRM_AiDiy.vrm",
    "tts_provider": "freeai:female"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "web版 AiDiy の紹介",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "WEB FRONTEND",
      "headline": "web版 AiDiy の\n画面を紹介します",
      "lead": "Vue 3 + Vite + TypeScript で構築した AiDiy の Web UI。実際の画面でログインから AI コアまでご覧ください。",
      "subtitle": "web版 AiDiy の主要画面と機能を順番にご紹介します。",
      "image": "images/scene_000.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "short_narration": "AiDiy の Web実装は、ブラウザで使う業務管理画面です。実画面で流れを順番に見ます。",
      "long_narration": "この動画では、AiDiy の Web実装を実際の画面で紹介します。Web実装は、ブラウザから使う業務管理システムの入り口です。画面は Vue 3、Vite、TypeScript で作られていて、ログインすると業務メニューや AI コアを操作できます。見た目は普通の管理画面ですが、中身は FastAPI のバックエンド、SQLite のデータベース、AI チャット、音声対話、コード支援までつながっています。最初に全体像を確認し、次にログイン、メニュー、AI コアのパネル、コード画面、ファイルや画像の扱い、最後に設定画面を順番に見ていきます。画面に映っている内容を追いながら、どこを触ると何ができるのかが分かるように説明します。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 6.816,
      "long_start_sec": 0.0,
      "long_duration_sec": 43.968
    },
    {
      "id": "scene_991",
      "title": "AiDiy web版の概要",
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196, 155, 255, 0.18)",
      "kicker": "OVERVIEW",
      "headline": "Vue 3 + FastAPI による\n日本語ファーストの業務システム",
      "lead": "フロントエンド・バックエンド・AI コアを統合した、日本語識別子を全レイヤーで使う業務システムテンプレートです。",
      "subtitle": "Vue 3 + Vite + TypeScript + FastAPI + SQLite + AI コアの統合システムです。",
      "image": "images/scene_001.png",
      "chips": [
        "Vue 3 / Vite",
        "TypeScript",
        "FastAPI",
        "SQLite",
        "AI コア",
        "MCP Tools"
      ],
      "metrics": [
        {
          "label": "Web UI",
          "value": "port 8090"
        },
        {
          "label": "Core API",
          "value": "port 8091"
        },
        {
          "label": "Apps API",
          "value": "port 8092"
        }
      ],
      "cards": [
        {
          "title": "フロントエンド",
          "lines": [
            "Vue 3 + Vite + TypeScript",
            "qTubler 独自テーブルコンポーネント",
            "Vue Router + Pinia で状態管理"
          ]
        },
        {
          "title": "バックエンド",
          "lines": [
            "FastAPI + SQLAlchemy + SQLite",
            "C系: 認証・利用者・AI コア",
            "M/T系: 業務マスタ・トランザクション"
          ]
        }
      ],
      "facts": [
        "テーブル名・カラム名・API パス・JSON キー・ファイル名・Python 変数まで日本語で統一。",
        "C系は core_main (port 8091)、M/T/V/S系は apps_main (port 8092) が担当。",
        "AI コアは CHAT_AI・LIVE_AI・CODE_AI を統合した多パネル UI。"
      ],
      "evidence": [],
      "short_narration": "Vue 3 と FastAPI を組み合わせた、日本語中心の業務システムです。構成も見ます。",
      "long_narration": "この概要画面では、AiDiy がどんな部品でできているかを整理しています。左側にはフロントエンドとして Vue 3、Vite、TypeScript、独自テーブル部品 qTubler、Vue Router、Pinia が並びます。右側にはバックエンドとして FastAPI、SQLAlchemy、SQLite があり、認証や AI コアを担当する C 系と、マスタやトランザクションを担当する M 系、T 系が分かれています。重要なのは、日本語で業務を考え、そのままコードにも近い名前を付けていることです。たとえばテーブル名、カラム名、API パス、JSON キー、画面ファイル名が日本語でそろいます。英語の略語を覚えなくても、業務で使う言葉と画面やデータが対応します。web UI は 8090 番ポート、Core API は 8091 番、Apps API は 8092 番で動き、Vite のプロキシが振り分けます。画面上の小さなチップは、FastAPI、SQLite、AI コア、MCP Tools まで含む構成を示しています。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_start_sec": 6.816,
      "short_duration_sec": 7.056,
      "long_start_sec": 43.968,
      "long_duration_sec": 65.616
    },
    {
      "id": "scene_002",
      "title": "ログイン画面",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125, 255, 179, 0.18)",
      "kicker": "LOGIN",
      "headline": "ID とパスワードを入力して\nログインします",
      "lead": "ログイン画面で利用者 ID とパスワードを入力します。JWT 認証でセキュアにアクセスを管理します。",
      "subtitle": "ログイン後は権限に応じたメニューが表示されます。",
      "image": "images/scene_002.png",
      "chips": [
        "JWT 認証",
        "利用者 ID",
        "パスワード",
        "権限管理"
      ],
      "metrics": [
        {
          "label": "初期ユーザー",
          "value": "admin"
        },
        {
          "label": "認証方式",
          "value": "JWT"
        }
      ],
      "cards": [
        {
          "title": "初期ログイン情報",
          "lines": [
            "admin / (管理者)",
            "leader / secret",
            "user / user",
            "guest / guest"
          ]
        },
        {
          "title": "認証の仕組み",
          "lines": [
            "JWT トークンを localStorage に保存",
            "401 エラーで自動ログアウト",
            "権限コードでメニュー表示を制御"
          ]
        }
      ],
      "facts": [
        "ログイン後 JWT トークンが発行され localStorage に保存される。",
        "401 エラーを Axios interceptor が検知し、自動でログアウト処理を行う。",
        "利用者の権限コードに応じてメニューの表示内容が変わる。"
      ],
      "evidence": [],
      "short_narration": "利用者 ID とパスワードでログインし、権限に合うメニュー画面へ進みます。",
      "long_narration": "ここは AiDiy の Web実装ログイン画面です。中央の小さなカードに、利用者 ID とパスワードを入力してログインします。裏側では FastAPI の認証 API に問い合わせ、正しければ JWT トークンが発行されます。JWT はログイン済みであることを示す通行証のようなもので、Web実装では localStorage に保存されます。画面から API を呼ぶときは Axios の共通クライアントがトークンを付けて送ります。もし期限切れなどで 401 エラーが返った場合は、自動的にログアウト処理へ進みます。利用者には権限コードがあり、管理者、リーダー、一般利用者、ゲストのように、見えるメニューや使える機能を分けられます。つまり、このシンプルなログイン画面が、業務データと AI 機能を安全に使い分ける入口になっています。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_start_sec": 13.872,
      "short_duration_sec": 5.304,
      "long_start_sec": 109.584,
      "long_duration_sec": 51.096
    },
    {
      "id": "scene_003",
      "title": "メニュー画面",
      "expression": "neutral",
      "accent": "#ffbf47",
      "accent_soft": "rgba(255, 191, 71, 0.18)",
      "kicker": "MENU",
      "headline": "実装サンプルを選んで\n業務画面を確認できます",
      "lead": "メニュー画面から業務システムの実装サンプル（配車管理・生産管理・在庫管理など）を選択できます。トップメニューの「AiDiy」から AI コア画面を起動します。",
      "subtitle": "トップメニューの AiDiy ボタンで AI コア画面が起動します。",
      "image": "images/scene_003.png",
      "chips": [
        "配車管理",
        "生産管理",
        "在庫管理",
        "AiDiy 起動"
      ],
      "metrics": [
        {
          "label": "実装例",
          "value": "3 システム"
        },
        {
          "label": "AI 起動",
          "value": "トップメニュー"
        }
      ],
      "cards": [
        {
          "title": "実装サンプル",
          "lines": [
            "配車管理: 配車指示・スケジュール",
            "生産管理: 商品構成・生産指示",
            "在庫管理: 入出庫・棚卸"
          ]
        },
        {
          "title": "AiDiy の起動",
          "lines": [
            "トップメニューの「AiDiy」をクリック",
            "AI コア画面が起動する",
            "画面はいつでも切り替え可能"
          ]
        }
      ],
      "facts": [
        "メニュー画面から業務システムの実装サンプルを選択できる。",
        "トップメニューの「AiDiy」ボタンから AI コア画面を起動できる。",
        "権限に応じて表示されるメニュー項目が変わる。"
      ],
      "evidence": [],
      "short_narration": "メニューから C 管理、マスタ、トラン、スケジュール、ビュー画面を選べます。",
      "long_narration": "ログイン後に表示されるメニュー画面です。左側には C 管理、M マスタ、T トラン、S スケジュール、V ビューという分類があり、クリックすると右側のカードが切り替わります。C 管理は利用者や権限などの共通機能、M マスタは商品や取引先などの基礎データ、T トランは日々の取引データ、S スケジュールは配車や生産の予定表、V ビューは集計や検索しやすい一覧を担当します。画面に映っているように、選択した分類に合わせて複数のカードが並び、目的の業務画面へ進めます。上部メニューには AiDiy ボタンがあり、ここから AI コア画面を別タブで開けます。通常の業務管理画面と AI 支援画面を、同じ Web UI の中で行き来できる構成です。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_start_sec": 19.176,
      "short_duration_sec": 5.352,
      "long_start_sec": 160.68,
      "long_duration_sec": 47.088
    },
    {
      "id": "scene_004",
      "title": "AiDiy 画面",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.18)",
      "kicker": "AIDIY SCREEN",
      "headline": "右端のボタンで\n表示パネルを切り替えられます",
      "lead": "AiDiy 画面の右端にあるボタンで各パネルの表示・非表示を切り替えます。チャット画面やライブ会話を使って AI と対話できます。",
      "subtitle": "右端ボタンでパネルの表示オンオフ、チャット・ライブ会話が選べます。",
      "image": "images/scene_004.png",
      "chips": [
        "パネル切り替え",
        "CHAT_AI",
        "LIVE_AI",
        "表示オンオフ"
      ],
      "metrics": [
        {
          "label": "パネル制御",
          "value": "右端ボタン"
        },
        {
          "label": "会話モード",
          "value": "2 種類"
        }
      ],
      "cards": [
        {
          "title": "パネル表示の切り替え",
          "lines": [
            "右端のボタンで各パネルをオンオフ",
            "必要なパネルだけ表示して作業できる",
            "レイアウトを自由にカスタマイズ"
          ]
        },
        {
          "title": "会話の種類",
          "lines": [
            "CHAT_AI: テキストでチャット",
            "LIVE_AI: 音声でリアルタイム対話",
            "AI モデルは設定から切り替え可能"
          ]
        }
      ],
      "facts": [
        "右端のボタンクリックで各パネルの表示・非表示を切り替えられる。",
        "CHAT_AI でテキストチャット、LIVE_AI で音声リアルタイム対話ができる。",
        "使用する AI モデルは設定から変更できる。"
      ],
      "evidence": [],
      "short_narration": "AI コアでは、右端ボタンでチャットやコードなどの主要パネルを切り替えます。",
      "long_narration": "これは Web実装の AI コア画面です。画面は黒を基調にした作業スペースで、人間から見て右端に縦並びのボタンがあります。このボタンで、チャット、ライブ会話、コード、ファイル、画像、設定などのパネルを表示したり閉じたりします。中央には AI と会話するチャット欄があり、下には入力欄と送信ボタンがあります。CHAT_AI は文字で相談するための場所です。LIVE_AI は音声でリアルタイムにやり取りするためのモードです。さらに CODE_AI を開くと、コード作成や修正を AI に依頼できます。大事なのは、画面をひとつに固定していないことです。設計だけ相談したいときはチャットを大きく使い、コードを直したいときはコードパネルを並べ、ファイルを確認したいときはファイルパネルを開きます。自分の作業内容に合わせて、机の上に道具を並べ替えるように使える画面です。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_start_sec": 24.528,
      "short_duration_sec": 5.568,
      "long_start_sec": 207.768,
      "long_duration_sec": 55.512
    },
    {
      "id": "scene_005",
      "title": "チャット画面とコード画面",
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123, 140, 255, 0.18)",
      "kicker": "CHAT & CODE",
      "headline": "コード画面は最大 6 パネルで\n個別に AI と会話できます",
      "lead": "チャット画面とコード画面を並べて使えます。コード画面（CODE_AI）は最大 6 パネルまで開け、それぞれ独立して AI と会話できます。",
      "subtitle": "コード画面は最大 6 パネル、各パネルが独立して AI と会話できます。",
      "image": "images/scene_005.png",
      "chips": [
        "CHAT_AI",
        "CODE_AI 1〜6",
        "最大 6 パネル",
        "個別会話"
      ],
      "metrics": [
        {
          "label": "コードパネル",
          "value": "最大 6"
        },
        {
          "label": "独立会話",
          "value": "パネルごと"
        }
      ],
      "cards": [
        {
          "title": "コード画面の特徴",
          "lines": [
            "CODE_AI 1〜6 の最大 6 パネル",
            "各パネルが独立して AI と会話",
            "ファイル編集・コード生成・レビューに活用"
          ]
        },
        {
          "title": "チャットとの組み合わせ",
          "lines": [
            "チャット画面で全体の方針を相談",
            "コード画面で具体的なコードを生成",
            "並列作業で開発効率を大幅に向上"
          ]
        }
      ],
      "facts": [
        "CODE_AI は 1 から 6 まで最大 6 パネルを同時に開ける。",
        "各コードパネルは独立して AI との会話を持つ。",
        "チャット画面と組み合わせることで、設計と実装を並行して進められる。"
      ],
      "evidence": [],
      "short_narration": "コード画面は最大 6 パネル。作業ごとに AI との会話を分けて進められます。",
      "long_narration": "このシーンでは、チャット画面とコード画面が並んでいます。右側の Code Agent パネルは CODE_AI のひとつで、最大 6 つまで同時に開けます。たとえば一つ目のパネルでは画面の不具合を相談し、二つ目では API の修正を依頼し、三つ目ではテストの確認を進める、という使い方ができます。各パネルは独立した会話を持つので、話題が混ざりにくくなります。普通のチャットだけだと、一つの会話に設計、実装、エラー確認、メモが全部入って長くなりがちです。AiDiy では、全体方針は CHAT_AI で相談し、具体的なコード作業は CODE_AI に分けられます。画面には黒いコード用パネルと入力欄があり、開発者が指示を出し、AI から結果を受け取る流れが見えます。複数の作業を同時に進めたいときに、頭の中の作業机をそのまま画面に分けて置ける構成です。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_start_sec": 30.096,
      "short_duration_sec": 6.288,
      "long_start_sec": 263.28,
      "long_duration_sec": 54.792
    },
    {
      "id": "scene_006",
      "title": "ファイル・チャット・イメージ・コード画面",
      "expression": "neutral",
      "accent": "#ff9a47",
      "accent_soft": "rgba(255, 154, 71, 0.18)",
      "kicker": "ALL PANELS",
      "headline": "デスクトップを共有しながら\nコードを開発できます",
      "lead": "ファイル画面・チャット画面・イメージ画面・コード画面を同時に表示した状態です。デスクトップ画面を AI と共有しながら開発を進められます。",
      "subtitle": "デスクトップ共有で AI が画面を認識しながら開発を支援します。",
      "image": "images/scene_006.png",
      "chips": [
        "ファイル画面",
        "イメージ画面",
        "デスクトップ共有",
        "マルチパネル"
      ],
      "metrics": [
        {
          "label": "共有方式",
          "value": "デスクトップキャプチャ"
        },
        {
          "label": "パネル種類",
          "value": "最大 4 種類"
        }
      ],
      "cards": [
        {
          "title": "各パネルの役割",
          "lines": [
            "ファイル画面: ファイルの閲覧・編集",
            "イメージ画面: 画像の生成・表示",
            "チャット + コードで AI と協働"
          ]
        },
        {
          "title": "デスクトップ共有開発",
          "lines": [
            "画面キャプチャを AI に送信",
            "AI が画面を認識してアドバイス",
            "実画面を見ながらコードを修正"
          ]
        }
      ],
      "facts": [
        "ファイル・チャット・イメージ・コードの 4 種類のパネルを同時表示できる。",
        "デスクトップ画面を AI と共有することで、実画面を見ながら開発できる。",
        "AI が画面を認識してコードの改善提案や問題の指摘を行う。"
      ],
      "evidence": [],
      "short_narration": "ファイル、チャット、コード、ライブキャプチャを同時に並べて使えます。",
      "long_narration": "この画面では、複数のパネルを同時に開いています。左上は File Manager で、プロジェクト内のファイルやフォルダを確認できます。右上は AiDiy のチャット、左下は Code Agent、右下は Live Capture です。Live Capture はデスクトップや画面の状態を AI に見せるためのパネルです。文字だけで説明しようとすると、どのボタンが見えているか、どのエラーが出ているか、どの画面で止まっているかを長く説明する必要があります。画面共有があれば、AI は実際の表示を見ながら、どこが問題か、次に何を確認すべきかを判断しやすくなります。ファイル一覧を見て、チャットで方針を相談し、コードパネルで修正を依頼し、ライブキャプチャで結果を確認する、という流れを一つの画面で進められます。これは単なるチャットアプリではなく、開発作業そのものを AI と共有するための作業環境です。",
      "short_audio": "audio/short_scene_006.mp3",
      "long_audio": "audio/long_scene_006.mp3",
      "short_start_sec": 36.384,
      "short_duration_sec": 4.896,
      "long_start_sec": 318.072,
      "long_duration_sec": 55.32
    },
    {
      "id": "scene_007",
      "title": "設定・再起動画面",
      "expression": "neutral",
      "accent": "#ff6b6b",
      "accent_soft": "rgba(255, 107, 107, 0.18)",
      "kicker": "SETTINGS",
      "headline": "設定を保存して\nサービスを部分再起動できます",
      "lead": "設定画面では規定値の保存や、バックエンドサービスの部分再起動・リセット再起動ができます。運用中でも設定変更を反映できます。",
      "subtitle": "規定値保存・部分再起動・リセット再起動を画面から操作できます。",
      "image": "images/scene_007.png",
      "chips": [
        "規定値保存",
        "部分再起動",
        "リセット再起動",
        "apps 再起動"
      ],
      "metrics": [
        {
          "label": "再起動種別",
          "value": "3 種類"
        },
        {
          "label": "対象",
          "value": "設定 / apps"
        }
      ],
      "cards": [
        {
          "title": "設定操作",
          "lines": [
            "規定値保存: 現在の設定をデフォルトとして保存",
            "設定再起動: 設定を反映して再起動",
            "apps 部分再起動: apps サーバーのみ再起動"
          ]
        },
        {
          "title": "リセット再起動",
          "lines": [
            "設定をリセットして再起動",
            "問題が起きたときの初期化手段",
            "データは保持されたまま設定のみリセット"
          ]
        }
      ],
      "facts": [
        "規定値保存で現在の設定をデフォルト値として保存できる。",
        "設定および apps の部分再起動で、全体を止めずに一部のサービスを再起動できる。",
        "リセット再起動で設定を初期状態に戻してサービスを再起動できる。"
      ],
      "evidence": [],
      "short_narration": "設定画面で AI の種類やモデルを選び、保存や部分再起動まで実行できます。",
      "long_narration": "設定画面では、AI コアで使うモデルや接続先をまとめて管理できます。画面には CHAT_AI、LIVE_AI、CODE_AI などの設定項目が並び、チャット用、音声対話用、コード支援用を別々に選べます。たとえばチャットは軽いモデル、コード作業は別の CLI、音声会話はリアルタイムに向いたモデル、というように役割で分けられます。設定を変更しただけでは、動作中のサービスに反映されない場合があります。そのため、規定値保存、設定再起動、apps 部分再起動、リセット再起動などの操作が画面からできるようになっています。全部を止めるのではなく、必要な部分だけ再起動できるのがポイントです。開発中に設定を変えながら試したいときも、設定ファイルを直接編集するだけでなく、この画面から状態を確認して反映できます。",
      "short_audio": "audio/short_scene_007.mp3",
      "long_audio": "audio/long_scene_007.mp3",
      "short_start_sec": 41.28,
      "short_duration_sec": 6.168,
      "long_start_sec": 373.392,
      "long_duration_sec": 52.728
    },
    {
      "id": "scene_999",
      "title": "まとめ",
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196, 155, 255, 0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "THANK YOU",
      "headline": "ご視聴ありがとうございました。\nAiDiy で何を作りますか？",
      "lead": "Vue 3 + TypeScript の業務 UI に AI コアを統合した AiDiy。あなたのシステムをここから構築してください。",
      "subtitle": "AiDiy で何を作りますか？",
      "image": "images/scene_999.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "short_narration": "業務画面と AI 支援を同じ場所で使う土台です。あなたもAiDiyとシステムづくりしてみませんか？",
      "long_narration": "ここまで AiDiy の Web実装画面を見てきました。ログインして、メニューから業務画面を選び、必要に応じて AI コアを開き、チャット、コード、ファイル、画像、画面共有、設定を組み合わせて使います。Vue 3 と TypeScript の Web UI、FastAPI の API、SQLite のデータベース、日本語中心の命名、そして AI 支援がひとつにつながっています。配車、生産、在庫のような実装例を手本にすれば、別の業務にも応用できます。大切なのは、完成品をただ使うだけではなく、現場に合わせて変えられることです。小さなマスタ画面を追加するところから始めてもよいですし、AI コアを使ってコード修正を試してもよいです。AiDiy は、業務システムを自分たちで育てていくための土台です。あなたもAiDiyとシステムづくりしてみませんか？",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_start_sec": 47.448,
      "short_duration_sec": 7.2,
      "long_start_sec": 426.12,
      "long_duration_sec": 52.416
    }
  ],
  "short_duration_sec": 54.648,
  "long_duration_sec": 478.536
};
