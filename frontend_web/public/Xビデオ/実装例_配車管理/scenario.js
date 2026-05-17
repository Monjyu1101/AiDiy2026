window.SCENARIO = {
  "project_name": "AiDiy配車管理紹介",
  "version": "take2",
  "title": "配車管理システム紹介",
  "source": {
    "type": "agents_and_knowledge",
    "summary": "AiDiy の配車管理システム（M配車区分、M車両、T配車、V配車、S配車_*）を実装実態から紹介する。"
  },
  "target": {
    "language": "ja-JP",
    "format": "html_css_scene_player_with_media",
    "tone": "業務システム紹介、実用的、使いたくなる",
    "goal": "配車管理の主要画面と機能を、実際に使いたくなるように紹介する。"
  },
  "assets_policy": {
    "visual_style": "left_image_30_right_explanation_70",
    "audio_dir": "audio",
    "image_dir": "images",
    "avatar": "vrm/AiDiy_Sample_M.vrm",
    "tts_provider": "edge:female"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "配車管理システム紹介",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "DISPATCH MANAGEMENT",
      "headline": "配車管理システム\nの主要機能を紹介します",
      "lead": "車両マスタ、配車登録、スケジュール表示まで、AiDiy の配車管理システムの全体像をご覧ください。",
      "subtitle": "配車管理システムの主要画面と機能を順番にご紹介します。",
      "image": "images/scene_000.png",
      "image_prompt": "Square 1:1 hero poster for a dispatch management system. Bold typography 'Dispatch Management' with logistics and vehicle icons, dark background, strong cyan glow, professional enterprise software aesthetic, clean and modern.",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "short_narration": "AiDiy の配車管理をご紹介します。配送業向けです。配車指示からスケジュールまで紹介します。",
      "long_narration": "この動画では、AiDiy の配車管理システムをご紹介します。AiDiy はシステム開発テンプレートですが、この配車管理は実際に動く業務サンプルとして作られています。車両を登録するマスタ、配車の種類を決めるマスタ、日々の配車指示、一覧検索、週表示、日表示までがつながっています。つまり、紙の予定表、個人のメモ、口頭連絡に分かれていた配車情報を、ひとつの画面の流れで扱えます。車両と配車情報を一元管理することで、担当者が変わっても、どの車がいつ何をする予定なのかをすぐに確認できます。予定の確認、登録、変更までを同じ仕組みで扱えることが、このサンプルの大きなポイントです。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 7.8,
      "long_start_sec": 0.0,
      "long_duration_sec": 44.352
    },
    {
      "id": "scene_001",
      "title": "配車管理の概要",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.18)",
      "kicker": "OVERVIEW",
      "headline": "車両と配車指示を\n一元管理するシステム",
      "lead": "配車区分・車両のマスタ管理から、配車指示の登録・照会・スケジュール表示まで、物流の要をカバーします。",
      "subtitle": "M配車区分、M車両、T配車、V配車、S配車_週/日表示で構成されています。",
      "image": "images/scene_001.png",
      "image_prompt": "Vertical 2:3 overview infographic of a dispatch management system, showing master data for vehicles and categories, transaction for dispatch orders, view for list display, and scheduler for weekly/daily schedules. Clean enterprise blueprint style, cyan accent, professional logistics software.",
      "chips": [
        "M配車区分",
        "M車両",
        "T配車",
        "V配車",
        "S配車_週/日"
      ],
      "metrics": [
        {
          "label": "マスタ",
          "value": "2"
        },
        {
          "label": "トランザクション",
          "value": "1"
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
            "配車区分の定義（チャーター、定期便など）",
            "車両情報の登録・管理",
            "マスタは M 系テーブルで管理"
          ]
        },
        {
          "title": "配車指示",
          "lines": [
            "日付・車両・配車区分を指定して登録",
            "T配車テーブルにトランザクション記録",
            "登録・更新・削除に対応"
          ]
        }
      ],
      "facts": [
        "配車管理は M配車区分、M車両、T配車、V配車、S配車_週表示、S配車_日表示で構成される。",
        "T配車は配車日付、車両、配車区分などを記録する配車指示トランザクション。",
        "V配車は Router 内の生 SQL による JOIN エンドポイントで、一覧表示に使用する。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "配車管理: M配車区分、M車両、T配車、V配車、S配車_*"
        }
      ],
      "short_narration": "配車管理はマスタ、T配車、スケジューラーで構成されます。マスタ整備で配車入力がスムーズです。",
      "long_narration": "配車管理システムは、M配車区分、M車両、T配車、V配車、S配車_週表示、S配車_日表示で構成されています。M系は、あとから何度も使う基本情報です。T配車は、毎日の配車指示を登録する本体です。V配車は、車両名や配車区分名を結合して見やすくした一覧です。そしてS配車は、予定をカレンダーのように見る画面です。チャーター便、定期便、回収便などを配車区分として登録しておくと、入力時は選ぶだけで済みます。一覧画面は qTubler という共通テーブルで、並び替え、絞り込み、件数制限などの操作感がそろっています。画面ごとに操作を覚え直さなくてよいので、新しいスタッフにも説明しやすい構成です。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_start_sec": 7.8,
      "short_duration_sec": 7.968,
      "long_start_sec": 44.352,
      "long_duration_sec": 48.888
    },
    {
      "id": "scene_002",
      "title": "マスタ管理（M配車区分・M車両）",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125, 255, 179, 0.18)",
      "kicker": "MASTER DATA",
      "headline": "配車区分と車両情報を\n事前に登録しておく",
      "lead": "M配車区分にチャーターや定期便などの区分を登録し、M車両に実際の車両情報を管理します。",
      "subtitle": "M配車区分とM車両がマスタの基盤です。",
      "image": "images/scene_002.png",
      "image_prompt": "Vertical 2:3 screenshot-style mockup of a master data management screen for dispatch categories and vehicles, Japanese UI, clean table layout with green accent, enterprise form design, professional and minimal.",
      "chips": [
        "配車区分コード",
        "車両ID",
        "車両名",
        "車両備考"
      ],
      "metrics": [
        {
          "label": "M配車区分",
          "value": "分類管理"
        },
        {
          "label": "M車両",
          "value": "車両台帳"
        }
      ],
      "cards": [
        {
          "title": "M配車区分",
          "lines": [
            "配車区分コード・名称を管理",
            "チャーター、定期便、回収便など",
            "新規・編集・削除に対応"
          ]
        },
        {
          "title": "M車両",
          "lines": [
            "車両ID・車両名・車両備考",
            "有効フラグで運用管理",
            "qTubler テーブルで一覧表示"
          ]
        }
      ],
      "facts": [
        "M配車区分は配車の種類を事前に定義するマスタテーブル。",
        "M車両は物流で使用する車両情報を管理するマスタテーブル。",
        "マスタ画面は qTubler（独自テーブルコンポーネント）でグリッド表示する。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "M配車区分、M車両 が配車管理マスタ構成要素"
        }
      ],
      "short_narration": "配車区分と車両をマスタで管理します。使用可否フラグで稼働状況を把握できます。",
      "long_narration": "M配車区分には、チャーター、定期便、回収便など、業務で使う配車の種類を登録できます。実装では配車区分ID、配車区分名、備考だけでなく、配色枠、配色背景、配色前景も持っています。この色設定はスケジューラーの予定ブロックに使えるので、予定表を見た瞬間に種類を区別しやすくなります。M車両には車両ID、車両名、車両備考を登録します。車両ごとの注意点、たとえば冷蔵車、軽トラック、予備車などのメモも備考に残せます。マスタを先に整えておくと、T配車の入力では車両や配車区分を選ぶだけになります。手入力を減らすことは、入力ミスを減らす一番わかりやすい方法です。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_start_sec": 15.768,
      "short_duration_sec": 6.696,
      "long_start_sec": 93.24,
      "long_duration_sec": 46.8
    },
    {
      "id": "scene_003",
      "title": "配車指示登録（T配車）",
      "expression": "neutral",
      "accent": "#ffbf47",
      "accent_soft": "rgba(255, 191, 71, 0.18)",
      "kicker": "TRANSACTION",
      "headline": "日付・車両・区分を指定して\n配車指示を登録する",
      "lead": "T配車テーブルに、開始日時・終了日時・車両・配車区分・配車内容などを入力して配車指示を作成します。",
      "subtitle": "T配車が配車指示のメイントランザクションです。",
      "image": "images/scene_003.png",
      "image_prompt": "Vertical 2:3 screenshot-style mockup of a dispatch order registration form in Japanese, showing start datetime, end datetime, vehicle selection dropdown, dispatch category, dispatch content and remarks fields, amber accent, clean enterprise form design.",
      "chips": [
        "配車開始日時",
        "配車終了日時",
        "車両選択",
        "配車区分",
        "配車内容"
      ],
      "metrics": [
        {
          "label": "T配車",
          "value": "指示登録"
        },
        {
          "label": "検索",
          "value": "日付/車両"
        }
      ],
      "cards": [
        {
          "title": "登録項目",
          "lines": [
            "配車開始日時・配車終了日時",
            "車両・配車区分の選択",
            "配車内容・配車備考"
          ]
        },
        {
          "title": "操作",
          "lines": [
            "新規登録・編集・削除",
            "日付範囲・車両での絞り込み検索",
            "監査フィールド（登録日時・利用者）自動記録"
          ]
        }
      ],
      "facts": [
        "T配車は配車指示を記録するメイントランザクションテーブル。",
        "配車区分と車両はマスタから選択するドロップダウン形式。",
        "全テーブルに監査フィールド（登録/更新の日時・利用者ID・利用者名・端末ID）が必須。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "T配車: 配車トランザクション。全テーブルに監査フィールド必須。"
        }
      ],
      "short_narration": "T配車は日付・車両・区分を選ぶだけで登録完了。履歴は自動記録されます。",
      "long_narration": "配車指示の登録はT配車で行います。実装上の主な項目は、配車伝票ID、配車開始日時、配車終了日時、配車区分ID、車両ID、配車内容、配車備考です。たとえば、いつからいつまで、どの車両で、どんな配車をするのかを記録します。V配車一覧では、T配車にM車両とM配車区分を結合して、車両名や配車区分名も一緒に表示します。日付範囲での絞り込みにも対応しています。登録、編集、削除の基本操作に加えて、登録日時、更新日時、利用者ID、利用者名、端末IDといった監査フィールドも自動で残ります。あとから「誰がいつ変更したのか」を確認できるので、実務で安心して使えます。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_start_sec": 22.464,
      "short_duration_sec": 7.368,
      "long_start_sec": 140.04,
      "long_duration_sec": 49.128
    },
    {
      "id": "scene_004",
      "title": "週間スケジューラー（S配車_週表示）",
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123, 140, 255, 0.18)",
      "kicker": "SCHEDULER",
      "headline": "週間スケジュールで\n配車計画をひと目で把握",
      "lead": "S配車_週表示は1週間の配車をカレンダー形式で表示します。行をダブルクリックすれば編集画面が開き、新規登録もできるのでこの画面だけで業務が完結します。",
      "subtitle": "S配車_週表示がスケジューラーの中心画面です。",
      "image": "images/scene_004.png",
      "image_prompt": "Vertical 2:3 screenshot-style mockup of a dispatch weekly schedule calendar in Japanese, showing 7-day grid with vehicle rows, blue-violet accent, double-click-to-edit UX hint, clean enterprise calendar design.",
      "chips": [
        "S配車_週表示",
        "ダブルクリック編集",
        "新規登録",
        "業務完結"
      ],
      "metrics": [
        {
          "label": "S配車_週表示",
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
            "1週間の配車計画をカレンダー形式で俯瞰",
            "車両ごとの稼働状況・重複がひと目でわかる",
            "週をまたいだ配車計画の調整も容易"
          ]
        },
        {
          "title": "ダブルクリックで編集・新規登録",
          "lines": [
            "スケジュール行をダブルクリックで編集画面が開く",
            "新規登録ボタンで新しい配車指示も入力可能",
            "確認・修正・登録の業務がこの画面だけで完結"
          ]
        }
      ],
      "facts": [
        "S配車_週表示はスケジューラとして1週間の配車計画をカレンダー形式で可視化する。",
        "テーブル行のダブルクリックでT配車の編集フォームを呼び出して即座に修正できる。",
        "新規登録ボタンも用意されており、スケジューラー画面だけで業務が完結する設計。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "S配車_週表示: スケジューラとして週単位で配車計画を可視化。"
        }
      ],
      "short_narration": "S配車_週表示で週の配車をカレンダー確認。ダブルクリックで編集・登録でき業務完結です。",
      "long_narration": "S配車_週表示は、配車スケジューラーの中心となる画面です。1週間の配車計画を車両ごとに並べて表示するので、どの車両がどの日に動いているかをひと目で確認できます。予定ブロックは配車区分の色を使って表示できるため、通常便、回収便、特別便のような違いも見分けやすくなります。さらに実装では、予定をドラッグして別の日や別の車両へ移動できます。左右のハンドルを動かすリサイズ操作で期間も変更できます。バックエンド側では、同じ車両の予定が重ならないように重複チェックを行います。30秒ごとに最終更新日時を確認して、他の人が変更した内容も画面へ反映します。予定表を見るだけでなく、その場で調整できるのが便利な点です。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_start_sec": 29.832,
      "short_duration_sec": 7.896,
      "long_start_sec": 189.168,
      "long_duration_sec": 48.12
    },
    {
      "id": "scene_005",
      "title": "配車指示の編集・登録（T配車フォーム）",
      "expression": "neutral",
      "accent": "#ff8c47",
      "accent_soft": "rgba(255, 140, 71, 0.18)",
      "kicker": "EDIT FORM",
      "headline": "一覧・スケジューラーから\n直接編集・新規登録",
      "lead": "T配車の編集フォームは、V配車一覧からもS配車スケジューラーからもダブルクリックで呼び出せます。新規登録も同じ画面で完結します。",
      "subtitle": "T配車フォームが配車指示のすべての入力・編集を担います。",
      "image": "images/scene_005.png",
      "image_prompt": "Vertical 2:3 screenshot-style mockup of a dispatch order edit form in Japanese, showing date picker, vehicle dropdown, category dropdown, destination and staff fields, orange accent, clean enterprise modal form design.",
      "chips": [
        "T配車編集",
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
            "V配車一覧の行をダブルクリックで呼出",
            "S配車_週表示の行をダブルクリックで呼出",
            "新規登録ボタンからも同じフォームを使用"
          ]
        },
        {
          "title": "入力フォームの項目",
          "lines": [
            "配車開始日時・配車終了日時",
            "車両・配車区分（マスタから選択）",
            "配車内容・配車備考"
          ]
        }
      ],
      "facts": [
        "T配車フォームはV配車一覧・S配車_週表示のどちらのダブルクリックでも開く共通フォーム。",
        "新規登録と編集更新を同一フォームで処理し、画面遷移のコストを最小化している。",
        "配車区分と車両はマスタから選択するドロップダウン形式で入力ミスを防ぐ。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "T配車: 配車トランザクション。qTublerのダブルクリックでフォームを呼び出す設計。"
        }
      ],
      "short_narration": "T配車フォームは一覧・スケジューラーからダブルクリックで開きます。新規登録も同じフォームです。",
      "long_narration": "T配車の編集フォームは、V配車一覧からも、S配車の週表示や日表示からも呼び出せます。既存の予定ブロックをダブルクリックすると編集、空いているセルをダブルクリックすると新規登録、という流れです。スケジューラーから開いた場合は、戻URLを持っているので、保存後に元の予定表へ戻れます。新規登録では、選んだ車両や日付、時間帯を引き継いでフォームを開けるため、ゼロから入力するより速く登録できます。車両と配車区分はマスタから選ぶ形式です。入力欄が日本語名でそろっているので、画面を見ながら「開始日時、終了日時、車両、内容、備考を入れる」と自然に理解できます。業務担当者と開発者が同じ言葉で話せる点も、AiDiyらしい使いやすさです。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_start_sec": 37.728,
      "short_duration_sec": 7.2,
      "long_start_sec": 237.288,
      "long_duration_sec": 49.608
    },
    {
      "id": "scene_006",
      "title": "日別スケジューラー（S配車_日表示）",
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196, 155, 255, 0.18)",
      "kicker": "DAILY SCHEDULER",
      "headline": "縦軸を変えるだけで\n飲食店の予約管理にも即流用",
      "lead": "S配車_日表示は1日の配車を時間帯×縦軸で可視化するスケジューラーです。縦軸を「座席位置」に切り替えれば、小さな飲食店のテーブル予約管理としてそのまま活用できます。",
      "subtitle": "S配車_日表示が日単位の細かいスケジュール管理を支えます。",
      "image": "images/scene_006.png",
      "image_prompt": "Vertical 2:3 screenshot-style mockup of a daily dispatch scheduler in Japanese, showing time slots on horizontal axis and vehicle rows on vertical axis, with colored blocks for dispatch entries. Below shows a conceptual transformation where vehicle rows become restaurant table seats (テーブルA, テーブルB) for reservation management. Purple accent, clean enterprise calendar design.",
      "chips": [
        "S配車_日表示",
        "時間帯×縦軸",
        "ダブルクリック編集",
        "飲食店予約に流用",
        "汎用設計"
      ],
      "metrics": [
        {
          "label": "S配車_日表示",
          "value": "日単位管理"
        },
        {
          "label": "縦軸変更",
          "value": "即流用可能"
        }
      ],
      "cards": [
        {
          "title": "日別スケジュール確認",
          "lines": [
            "1日の配車を時間帯×車両で一覧表示",
            "ダブルクリックで配車指示の編集フォームへ",
            "新規登録もこの画面から直接入力可能"
          ]
        },
        {
          "title": "縦軸を変えれば別業種にも",
          "lines": [
            "縦軸を「座席位置」にすれば飲食店の予約管理に",
            "テーブルA・Bを縦軸、時間帯を横軸で予約を可視化",
            "スケジュール管理が必要な業種ならそのまま流用できる"
          ]
        }
      ],
      "facts": [
        "S配車_日表示は1日の配車を時間帯×縦軸（車両）で視覚化するスケジューラー。",
        "縦軸の定義を変えるだけで飲食店の座席予約など他業種のスケジュール管理に即流用できる汎用設計。",
        "ダブルクリックで編集フォームが開き、新規登録もこの画面から行える。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "S配車_日表示: 日単位の配車スケジューラー"
        }
      ],
      "short_narration": "S配車_日表示で配車を時間帯別に可視化。縦軸を変えれば予約管理にも流用できます。",
      "long_narration": "S配車_日表示は、1日のスケジュールを時間帯で細かく見る画面です。このサンプルでは、縦軸が車両、横軸が時間です。午前中にどの車が使われ、午後にどの車が空いているのかを、表の形で確認できます。週表示と同じく、予定ブロックのドラッグ移動、リサイズ、ダブルクリック編集に対応しています。1日単位で見ると、少しの時間の重なりや空き時間が見えやすくなります。この仕組みは配車専用ではありません。縦軸を車両ではなく座席にすれば、飲食店のテーブル予約表として考えられます。縦軸を会議室にすれば、会議室予約にも使えます。大事なのは、縦軸に管理したいものを置き、横軸に時間を置くという考え方です。配車管理の実装は、他の予約管理へ応用しやすいお手本にもなっています。",
      "short_audio": "audio/short_scene_006.mp3",
      "long_audio": "audio/long_scene_006.mp3",
      "short_start_sec": 44.928,
      "short_duration_sec": 7.296,
      "long_start_sec": 286.896,
      "long_duration_sec": 53.376
    },
    {
      "id": "scene_999",
      "title": "配車管理システム まとめ",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "SUMMARY",
      "headline": "マスタ整備からスケジュール管理まで\nこれひとつで配車業務が完結",
      "lead": "M系マスタで基盤を整え、T配車で日々の指示を登録し、週・日のスケジューラーで確認・編集まで完結。小規模な物流・配送業にそのまま使えるシステムです。",
      "subtitle": "AiDiyで何かスケジュール管理してみませんか？",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "image": "images/scene_999.png",
      "image_prompt": "Square 1:1 elegant summary card for dispatch management system. Shows a compact flow diagram: M配車区分+M車両 → T配車 → V配車/S配車_週/S配車_日, all connected with arrows. Bottom note: small restaurant reservation reuse concept. Cyan #29d8ff accent glow, dark background, professional enterprise style, clean and modern.",
      "short_narration": "マスタから配車指示、スケジューラー確認まで完結。AiDiyで何かスケジュール管理してみませんか？",
      "long_narration": "配車管理システムの主要機能をご紹介しました。M配車区分とM車両で基礎データを整え、T配車で日々の配車指示を登録します。V配車一覧では検索しやすい形で確認し、S配車_週表示とS配車_日表示では予定表として確認できます。さらに、ドラッグ移動、リサイズ、重複チェック、自動更新、ダブルクリック編集まで実装されています。これは単なる画面サンプルではなく、業務の流れを考えた実装例です。配車というテーマで作られていますが、縦軸と時間軸を使う考え方は、予約、貸出、作業予定、設備利用にも応用できます。まずはこの配車管理を触って、AiDiyで何かスケジュール管理してみませんか？",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_start_sec": 52.224,
      "short_duration_sec": 7.272,
      "long_start_sec": 340.272,
      "long_duration_sec": 46.344
    }
  ],
  "short_duration_sec": 59.496,
  "long_duration_sec": 386.616
};
