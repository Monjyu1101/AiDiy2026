window.SCENARIO = {
  "project_name": "AiDiy生産管理紹介",
  "version": "take2",
  "title": "生産管理システム紹介",
  "source": {
    "type": "agents_and_knowledge",
    "summary": "AiDiy の生産管理システム（M生産区分、M商品構成、T生産、V生産、S生産_*）を実装実態から紹介する。"
  },
  "target": {
    "language": "ja-JP",
    "format": "html_css_scene_player_with_media",
    "tone": "業務システム紹介、実用的、使いたくなる",
    "goal": "生産管理の主要画面と機能を、実際に使いたくなるように紹介する。"
  },
  "assets_policy": {
    "visual_style": "left_image_30_right_explanation_70",
    "audio_dir": "audio",
    "image_dir": "images",
    "avatar": "../_vrm/VRM_AiDiy.vrm",
    "tts_provider": "freeai:female"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "生産管理システム紹介",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125, 255, 179, 0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "PRODUCTION MANAGEMENT",
      "headline": "生産管理システム\nの主要機能を紹介します",
      "lead": "商品構成マスタ、生産指示、スケジュール表示まで、AiDiy の生産管理システムの全体像をご覧ください。",
      "subtitle": "生産管理システムの主要画面と機能を順番にご紹介します。",
      "image": "images/scene_000.png",
      "image_prompt": "Square 1:1 hero poster for a production management system. Bold typography 'Production Management' with manufacturing and process flow icons, dark background, strong green glow, professional enterprise software aesthetic, clean and modern.",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "short_narration": "AiDiy の生産管理をご紹介します。製造業向けです。材料から生産指示まで紹介します。",
      "long_narration": "この動画では、AiDiy の生産管理システムをご紹介します。生産管理とは、何を、いつ、どれだけ作るか、そしてそのためにどの材料を使うかを管理する仕組みです。AiDiy では、商品マスタ、生産区分、生産工程、商品構成マスタ、生産指示、一覧、週表示、日表示がつながっています。商品構成マスタに材料と必要数量を登録しておけば、生産指示で作る数量を決めたときに、必要な材料を展開できます。生産予定と材料払出を同じ流れで扱えるため、製造現場の予定管理と在庫管理をつなげやすくなります。明細型パターンにより、ヘッダーと材料明細を単一テーブルで扱える点も大きな特徴です。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_duration_sec": 8.016,
      "long_duration_sec": 46.128
    },
    {
      "id": "scene_001",
      "title": "生産管理の概要",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125, 255, 179, 0.18)",
      "kicker": "OVERVIEW",
      "headline": "商品構成から生産指示まで\n一貫して管理するシステム",
      "lead": "M商品構成（材料構成）の明細型マスタと、T生産（生産指示）の明細型トランザクションが特徴です。",
      "subtitle": "M生産区分、M商品構成、T生産、V生産、S生産_週/日表示で構成されます。",
      "image": "images/scene_001.png",
      "image_prompt": "Vertical 2:3 overview infographic of a production management system, showing master data for production categories and product structure, transaction for production orders with BOM, view and scheduler. Clean enterprise blueprint style, green accent, professional manufacturing software.",
      "chips": [
        "M生産区分",
        "M商品構成",
        "T生産",
        "V生産",
        "S生産_週/日"
      ],
      "metrics": [
        {
          "label": "マスタ",
          "value": "3+"
        },
        {
          "label": "明細型",
          "value": "2"
        },
        {
          "label": "スケジュール",
          "value": "2"
        }
      ],
      "cards": [
        {
          "title": "マスタ管理",
          "lines": [
            "M生産区分: 生産の種類を定義",
            "M生産工程: 工程管理",
            "M商品構成: 材料構成（明細型）"
          ]
        },
        {
          "title": "生産指示",
          "lines": [
            "T生産: ヘッダー + 材料払出明細",
            "明細SEQ=0 がヘッダー行",
            "明細SEQ>=1 が材料明細行"
          ]
        }
      ],
      "facts": [
        "生産管理は M生産区分、M生産工程、M商品、M商品構成、T生産、V生産、S生産_*で構成される。",
        "M商品構成とT生産は明細型パターンを採用し、単一テーブルでヘッダーと明細を管理する。",
        "明細SEQ=0がヘッダー行、明細SEQ>=1が明細行という設計。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "生産管理: M生産区分、M生産工程、M商品、M商品構成、T生産、V生産、S生産_*"
        }
      ],
      "short_narration": "生産管理は明細型マスタ・T生産・スケジューラーで構成。明細型が特徴です。",
      "long_narration": "生産管理システムは、M生産区分、M生産工程、M商品、M商品構成、T生産、V生産、S生産_週表示、S生産_日表示を中心に構成されています。M系は基本情報です。M生産区分は通常生産や試作などの種類、M生産工程はラインや工程、M商品は製品や材料を表します。M商品構成は、製品を作るための材料リストです。T生産は、実際の生産指示です。V生産は一覧確認、S生産は予定表として使います。特にM商品構成とT生産は明細型です。明細SEQが0の行にヘッダー情報、1以上の行に材料や払出の明細を持ちます。ひとつの伝票を、親と子の2テーブルに分けず、単一テーブルで表すため、構造を理解しやすく、AIにも追加実装させやすいパターンです。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_duration_sec": 7.392,
      "long_duration_sec": 58.392
    },
    {
      "id": "scene_002",
      "title": "商品構成マスタ（明細型パターン）",
      "expression": "neutral",
      "accent": "#ffbf47",
      "accent_soft": "rgba(255, 191, 71, 0.18)",
      "kicker": "BOM MASTER",
      "headline": "ヘッダーと材料明細を\n単一テーブルで管理する",
      "lead": "M商品構成は明細SEQ=0がヘッダー、明細SEQ>=1が材料明細という独自パターンで構成されます。",
      "subtitle": "明細SEQ=0がヘッダー、明細SEQ>=1が材料明細というパターンを使います。",
      "image": "images/scene_002.png",
      "image_prompt": "Vertical 2:3 screenshot-style mockup of a bill of materials master screen in Japanese, showing header row and material detail rows in a single table with seq numbers, amber accent, clean enterprise form design.",
      "chips": [
        "明細SEQ=0 ヘッダー",
        "明細SEQ>=1 材料明細",
        "商品コード",
        "数量",
        "単位"
      ],
      "metrics": [
        {
          "label": "パターン",
          "value": "明細型"
        },
        {
          "label": "テーブル",
          "value": "単一"
        }
      ],
      "cards": [
        {
          "title": "ヘッダー行（明細SEQ=0）",
          "lines": [
            "商品コード・商品名",
            "構成バージョン・有効期間",
            "備考・監査フィールド"
          ]
        },
        {
          "title": "材料明細行（明細SEQ>=1）",
          "lines": [
            "材料商品コード・名称",
            "使用数量・単位",
            "材料の順序・並び替え"
          ]
        }
      ],
      "facts": [
        "M商品構成は 明細SEQ=0 をヘッダー、明細SEQ>=1 を材料明細とする明細型マスタ。",
        "ヘッダーと明細を単一テーブルで管理することで JOIN を削減できる。",
        "T生産（生産指示）でも同じ明細型パターンを採用している。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "M商品構成: 明細SEQ=0 をヘッダー、明細SEQ>=1 を材料明細とする明細型マスタ。"
        }
      ],
      "short_narration": "M商品構成は単一テーブルで材料明細を管理する明細型マスタ。JOINが不要でシンプルです。",
      "long_narration": "M商品構成は、AiDiy が採用する明細型パターンの代表例です。明細SEQが0の行には、完成品の商品ID、最小ロット数量、生産区分ID、生産工程ID、段取分数、時間生産数量、備考を持ちます。明細SEQが1以上の行には、構成商品ID、計算分子数量、計算分母数量、最小ロット構成数量、構成商品備考を持ちます。簡単に言えば、ヘッダー行が「何を作るか」、明細行が「何をどれだけ使うか」です。画面では材料行を追加・削除でき、数量を変えると最小ロット構成数量を計算できます。段取分数や時間生産数量も持てるので、材料だけでなく作業時間の計画にも使えます。T生産で製造商品を選ぶと、この商品構成を読み込んで材料明細を自動展開できます。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_duration_sec": 7.992,
      "long_duration_sec": 56.736
    },
    {
      "id": "scene_003",
      "title": "生産指示登録（T生産）",
      "expression": "neutral",
      "accent": "#ff6bd6",
      "accent_soft": "rgba(255, 107, 214, 0.18)",
      "kicker": "PRODUCTION ORDER",
      "headline": "生産指示と材料払出明細を\nセットで登録する",
      "lead": "T生産はヘッダーに生産指示情報を、明細に材料払出情報を記録する明細型トランザクションです。",
      "subtitle": "T生産が生産指示のメイントランザクションです。",
      "image": "images/scene_003.png",
      "image_prompt": "Vertical 2:3 screenshot-style mockup of a production order registration form in Japanese, showing header section with production date and product, and material detail section with quantities, magenta accent, clean enterprise form design.",
      "chips": [
        "生産日付",
        "製造商品",
        "生産数量",
        "材料払出明細",
        "工程"
      ],
      "metrics": [
        {
          "label": "T生産",
          "value": "指示登録"
        },
        {
          "label": "明細型",
          "value": "ヘッダー+明細"
        }
      ],
      "cards": [
        {
          "title": "ヘッダー（明細SEQ=0）",
          "lines": [
            "生産日付・生産区分・工程",
            "製造商品コード・生産数量",
            "生産内容・生産備考"
          ]
        },
        {
          "title": "材料払出明細（明細SEQ>=1）",
          "lines": [
            "材料商品コード・払出数量",
            "M商品構成から材料を自動展開",
            "監査フィールド自動記録"
          ]
        }
      ],
      "facts": [
        "T生産は生産指示ヘッダーと材料払出明細を単一テーブルで管理する明細型トランザクション。",
        "M商品構成の材料リストを参照して、材料明細を自動展開できる。",
        "全テーブルに監査フィールド（登録/更新の日時・利用者ID・利用者名・端末ID）が必須。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "T生産: 明細SEQ=0 をヘッダー、明細SEQ>=1 を払出明細とする明細型トランザクション。"
        }
      ],
      "short_narration": "T生産は明細型で生産情報と材料払出を記録。材料の自動展開ができます。",
      "long_narration": "T生産は、生産指示の登録に使うメイントランザクションです。明細SEQが0のヘッダー行には、生産開始日時、生産終了日時、生産内容、生産備考、受入商品ID、最小ロット数量、受入数量、生産区分ID、生産工程IDなどを記録します。明細SEQが1以上の明細行には、払出商品ID、計算分子数量、計算分母数量、払出数量などを記録します。製造商品を選ぶとM商品構成を取得し、段取分数、時間生産数量、材料明細、払出数量の初期値を展開します。受入数量を変えると、材料の必要数量や生産時間も計算し直せます。つまり、製品を何個作るかを入力すれば、必要な材料と時間の見込みを同じ画面で確認できます。監査フィールドも自動記録されるため、変更履歴の追跡にも対応しています。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_duration_sec": 7.392,
      "long_duration_sec": 59.28
    },
    {
      "id": "scene_004",
      "title": "週間スケジューラー（S生産_週表示）",
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123, 140, 255, 0.18)",
      "kicker": "SCHEDULER",
      "headline": "週間スケジュールで\n生産計画をひと目で把握",
      "lead": "S生産_週表示は1週間の生産計画をカレンダー形式で表示します。行をダブルクリックすれば編集画面が開き、新規登録もできるのでこの画面だけで業務が完結します。",
      "subtitle": "S生産_週表示がスケジューラーの中心画面です。",
      "image": "images/scene_004.png",
      "image_prompt": "Vertical 2:3 screenshot-style mockup of a production weekly schedule calendar in Japanese, showing 7-day grid with product rows, blue-violet accent, double-click-to-edit UX hint, clean enterprise calendar design.",
      "chips": [
        "S生産_週表示",
        "ダブルクリック編集",
        "新規登録",
        "業務完結"
      ],
      "metrics": [
        {
          "label": "S生産_週表示",
          "value": "週間確認"
        },
        {
          "label": "ダブルクリック",
          "value": "即座に編集"
        }
      ],
      "cards": [
        {
          "title": "週間スケジュール確認",
          "lines": [
            "1週間の生産計画をカレンダー形式で俯瞰",
            "商品ごとの生産数量・工程がひと目でわかる",
            "計画の集中・空きを確認して調整も容易"
          ]
        },
        {
          "title": "ダブルクリックで編集・新規登録",
          "lines": [
            "スケジュール行をダブルクリックで編集画面が開く",
            "新規登録ボタンで新しい生産指示も入力可能",
            "確認・修正・登録の業務がこの画面だけで完結"
          ]
        }
      ],
      "facts": [
        "S生産_週表示はスケジューラとして1週間の生産計画をカレンダー形式で可視化する。",
        "テーブル行のダブルクリックでT生産の編集フォームを呼び出して即座に修正できる。",
        "新規登録ボタンも用意されており、スケジューラー画面だけで業務が完結する設計。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "S生産_週表示: スケジューラとして週単位で生産計画を可視化。"
        }
      ],
      "short_narration": "S生産_週表示で週の生産をカレンダー確認。ダブルクリックで業務完結です。",
      "long_narration": "S生産_週表示は、生産スケジューラーの中心となる画面です。1週間の生産計画を生産工程ごとに並べ、どの工程でいつ何を作る予定かを確認できます。表示データはT生産のヘッダー行をもとにしており、商品名、単位、生産区分名、配色情報も一緒に取得しています。配色を使うことで、通常生産や特別な生産などを見分けやすくできます。実装では、予定ブロックをドラッグして別の日や別の工程へ移動できます。左右のハンドルで期間を伸ばしたり縮めたりするリサイズもできます。バックエンドでは、同じ工程に同じ時間帯の予定が重ならないように重複チェックをします。30秒ごとに最終更新日時も確認するので、他の人が変更した予定も反映できます。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_duration_sec": 6.912,
      "long_duration_sec": 49.8
    },
    {
      "id": "scene_005",
      "title": "生産指示の編集・登録（T生産フォーム）",
      "expression": "neutral",
      "accent": "#ff6bd6",
      "accent_soft": "rgba(255, 107, 214, 0.18)",
      "kicker": "EDIT FORM",
      "headline": "一覧・スケジューラーから\n直接編集・新規登録",
      "lead": "T生産の編集フォームは、V生産一覧からもS生産スケジューラーからもダブルクリックで呼び出せます。新規登録も同じ画面で完結します。",
      "subtitle": "T生産フォームが生産指示のすべての入力・編集を担います。",
      "image": "images/scene_005.png",
      "image_prompt": "Vertical 2:3 screenshot-style mockup of a production order edit form in Japanese, showing header section with date and product, and material detail section, magenta-pink accent, clean enterprise modal form design.",
      "chips": [
        "T生産編集",
        "一覧から呼出",
        "スケジューラーから呼出",
        "新規登録"
      ],
      "metrics": [
        {
          "label": "呼出元",
          "value": "一覧/週表示"
        },
        {
          "label": "操作",
          "value": "編集・登録"
        }
      ],
      "cards": [
        {
          "title": "どこからでも呼び出せる",
          "lines": [
            "V生産一覧の行をダブルクリックで呼出",
            "S生産_週表示の行をダブルクリックで呼出",
            "新規登録ボタンからも同じフォームを使用"
          ]
        },
        {
          "title": "入力フォームの項目",
          "lines": [
            "生産日付・生産区分・工程",
            "製造商品・生産数量（マスタから選択）",
            "材料払出明細（M商品構成から自動展開）"
          ]
        }
      ],
      "facts": [
        "T生産フォームはV生産一覧・S生産_週表示のどちらのダブルクリックでも開く共通フォーム。",
        "新規登録と編集更新を同一フォームで処理し、画面遷移のコストを最小化している。",
        "M商品構成の材料リストを参照して材料払出明細を自動展開できる。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "T生産: 明細型トランザクション。qTublerのダブルクリックでフォームを呼び出す設計。"
        }
      ],
      "short_narration": "T生産フォームはスケジューラーからダブルクリックで開きます。商品選択で材料が展開されます。",
      "long_narration": "T生産の編集フォームは、V生産一覧からも、S生産の週表示や日表示からも呼び出せます。既存の予定ブロックをダブルクリックすれば編集、空いているセルをダブルクリックすれば新規登録の流れです。スケジューラーから開いた場合は、生産工程や日付、時間帯を引き継いでフォームを開けます。製造商品を選ぶと、M商品構成から材料明細が自動展開されます。画面には受入数量、段取分数、時間生産数量、生産時間、払出商品、払出数量などが並びます。数量を変えると計算式も見ながら確認できます。製造数量を変更したときに材料の払出数量も連動して見直せるため、手入力を減らしながら、現場で必要な調整もできるフォームになっています。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_duration_sec": 7.32,
      "long_duration_sec": 49.872
    },
    {
      "id": "scene_006",
      "title": "日次スケジューラー（S生産_日表示）",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.18)",
      "kicker": "DAILY SCHEDULER",
      "headline": "日単位の生産状況を\n時間帯別に可視化する",
      "lead": "S生産_日表示は当日の生産計画を縦軸に生産工程、横軸に時間帯として表示します。週表示で俯瞰しながら、日表示で詳細な進捗を確認する使い方が現場に最適です。",
      "subtitle": "製造現場の朝礼・進捗確認に活用できます。",
      "image": "images/scene_006.png",
      "image_prompt": "Vertical 2:3 screenshot-style mockup of a daily production scheduler in Japanese, showing vertical axis with product names and horizontal axis with time slots, cyan accent, highlighting real-time progress visualization, clean enterprise calendar design.",
      "chips": [
        "S生産_日表示",
        "時間帯別確認",
        "週表示との連携",
        "朝礼・進捗確認"
      ],
      "metrics": [
        {
          "label": "S生産_日表示",
          "value": "日次確認"
        },
        {
          "label": "ダブルクリック",
          "value": "即座に編集"
        }
      ],
      "cards": [
        {
          "title": "当日の生産を時間帯別に確認",
          "lines": [
            "縦軸に生産工程、横軸に時間帯を配置",
            "どの工程がいつ使われるかを一目で把握",
            "生産の遅れや空き時間をリアルタイムに確認"
          ]
        },
        {
          "title": "週表示と日表示の使い分け",
          "lines": [
            "S生産_週表示で週全体の計画を俯瞰",
            "S生産_日表示で当日の詳細な進捗を確認",
            "ダブルクリックで編集フォームを呼び出せる"
          ]
        }
      ],
      "facts": [
        "S生産_日表示は当日の生産計画を縦軸×横軸で視覚化する日次スケジューラー。",
        "縦軸に生産工程、横軸に時間帯を置き、どの工程がいつ使われるかをひと目で把握できる。",
        "週表示との組み合わせで、週の俯瞰と日の詳細確認という使い分けが可能。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "S生産_日表示: 日次スケジューラー。縦軸に商品、横軸に時間帯を配置して可視化。"
        }
      ],
      "short_narration": "S生産_日表示で当日の生産を時間帯別に可視化。製品の製造時刻を把握できます。",
      "long_narration": "S生産_日表示は、1日の生産計画を時間帯で細かく見る画面です。実装では、縦軸に生産工程、横軸に時間帯を置きます。どの工程が何時から何時まで使われるかを見られるので、工程の空きや重なりを確認しやすくなります。週表示では全体の予定を大きく見て、日表示では当日の動きを細かく見る、という使い分けができます。日表示でも、予定ブロックのドラッグ移動、リサイズ、ダブルクリック編集、新規登録に対応しています。工程が重なる場合はバックエンド側でチェックされます。朝礼で今日の予定を確認したり、作業が遅れたときに予定を後ろへずらしたりする場面で便利です。時間軸で見ることで、一覧表だけでは見えない混雑や空き時間が分かります。",
      "short_audio": "audio/short_scene_006.mp3",
      "long_audio": "audio/long_scene_006.mp3",
      "short_duration_sec": 7.512,
      "long_duration_sec": 49.44
    },
    {
      "id": "scene_999",
      "title": "商品在庫推移と未来在庫予測",
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196, 155, 255, 0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "INVENTORY FORECAST",
      "headline": "生産スケジュールが\n未来の在庫推移を映し出す",
      "lead": "V商品推移表は、登録済みの生産スケジュールをもとに商品ごとの在庫推移を計算し、未来の在庫を予測して表示します。",
      "subtitle": "AiDiyで何かスケジュール管理してみませんか？",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "image": "images/scene_999.png",
      "image_prompt": "Square 1:1 elegant infographic for inventory forecast from production schedule. Shows a line chart with product inventory trend over time, future forecast area highlighted in purple glow, dark background, professional enterprise analytics style, 'Inventory Forecast' typography.",
      "short_narration": "生産スケジュールが商品の未来在庫を予測します。AiDiyで何かスケジュール管理してみませんか？",
      "long_narration": "最後に、生産管理は在庫管理ともつながります。V商品推移表では、T生産のヘッダー行を生産受入、明細行を生産払出として集計しています。製品を作る予定は将来の在庫増加になり、材料を使う予定は将来の在庫減少になります。これにより、今日の在庫だけでなく、これからの予定を含めた推定在庫を見られます。在庫が不足しそうな材料があれば、先に発注を考えられます。逆に、作りすぎで在庫が増えすぎそうなら、生産予定を調整できます。生産スケジューラーは、予定表として見るだけでなく、材料と製品の未来在庫を考えるための入口にもなります。AiDiyで何かスケジュール管理してみませんか？",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_duration_sec": 7.128,
      "long_duration_sec": 46.2
    }
  ],
  "short_duration_sec": 59.664,
  "long_duration_sec": 415.848
};
