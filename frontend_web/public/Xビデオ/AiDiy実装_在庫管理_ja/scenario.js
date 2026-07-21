window.SCENARIO = {
  "project_name": "AiDiy在庫管理紹介",
  "version": "take2",
  "title": "在庫管理システム紹介",
  "source": {
    "type": "agents_and_knowledge",
    "summary": "AiDiy の在庫管理システム（T商品入庫、T商品出庫、T商品棚卸、V商品推移表）を実装実態から紹介する。"
  },
  "target": {
    "language": "ja-JP",
    "format": "html_css_scene_player_with_media",
    "tone": "業務システム紹介、実用的、使いたくなる",
    "goal": "在庫管理の主要画面と機能を、実際に使いたくなるように紹介する。"
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
      "title": "在庫管理システム紹介",
      "expression": "neutral",
      "accent": "#ffbf47",
      "accent_soft": "rgba(255, 191, 71, 0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "INVENTORY MANAGEMENT",
      "headline": "在庫管理システム\nの主要機能を紹介します",
      "lead": "入庫・出庫・棚卸のトランザクション管理から、商品推移表による在庫状況の可視化まで、AiDiy の在庫管理をご覧ください。",
      "subtitle": "在庫管理システムの主要画面と機能を順番にご紹介します。",
      "image": "images/scene_000.png",
      "image_prompt": "Square 1:1 hero poster for an inventory management system. Bold typography 'Inventory Management' with warehouse and stock icons, dark background, strong amber glow, professional enterprise software aesthetic, clean and modern.",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "short_narration": "AiDiy の在庫管理をご紹介します。小規模事業者向けです。入庫・出庫・棚卸と推移表で在庫を把握します。",
      "long_narration": "この動画では、AiDiy の在庫管理システムをご紹介します。在庫管理というと難しく聞こえるかもしれませんが、基本はとてもシンプルです。商品が入ってきたら入庫、商品が出ていったら出庫、実際に数えたら棚卸です。AiDiy では、この3つの動きをT商品入庫、T商品出庫、T商品棚卸として記録します。そしてV商品推移表で、商品ごとの在庫が日付ごとにどう変わったかを見られます。さらに生産管理とつながると、生産で完成した商品は受入、材料として使った商品は払出として在庫に反映されます。通常の入出庫だけでなく、生産予定まで含めて在庫の動きを確認できることが、この在庫管理サンプルの大きな特徴です。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_duration_sec": 9.624,
      "long_duration_sec": 47.496
    },
    {
      "id": "scene_001",
      "title": "在庫管理の概要",
      "expression": "neutral",
      "accent": "#ffbf47",
      "accent_soft": "rgba(255, 191, 71, 0.18)",
      "kicker": "OVERVIEW",
      "headline": "入庫・出庫・棚卸を記録し\n在庫状況を可視化するシステム",
      "lead": "M商品マスタを基盤に、3つの在庫トランザクションと V商品推移表で在庫を一元管理します。",
      "subtitle": "M商品、T商品入庫、T商品出庫、T商品棚卸、V商品推移表で構成されます。",
      "image": "images/scene_001.png",
      "image_prompt": "Vertical 2:3 overview infographic of an inventory management system, showing product master, three inventory transactions for receiving, shipping and stocktaking, and view for stock movement table. Clean enterprise blueprint style, amber accent.",
      "chips": [
        "M商品",
        "T商品入庫",
        "T商品出庫",
        "T商品棚卸",
        "V商品推移表"
      ],
      "metrics": [
        {
          "label": "在庫TX",
          "value": "3種"
        },
        {
          "label": "推移表",
          "value": "V系"
        }
      ],
      "cards": [
        {
          "title": "トランザクション種別",
          "lines": [
            "T商品入庫: 仕入・受入れ",
            "T商品出庫: 出荷・払出し",
            "T商品棚卸: 在庫の現物確認・実棚数量"
          ]
        },
        {
          "title": "在庫推移表",
          "lines": [
            "V商品推移表で期間内の動きを集計",
            "入庫・出庫・棚卸を一覧で確認",
            "商品・期間での絞り込み検索"
          ]
        }
      ],
      "facts": [
        "在庫管理は M商品、T商品入庫、T商品出庫、T商品棚卸、V商品推移表で構成される。",
        "V商品推移表はDB VIEWではなく、Router内の生SQL集計エンドポイント。",
        "T系3種のトランザクションにより在庫の増減履歴をすべて記録する。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "資材在庫管理: M商品、T商品入庫、T商品出庫、T商品棚卸、V商品推移表"
        }
      ],
      "short_narration": "入庫・出庫・棚卸の3種で在庫の増減を記録し、推移表で現状を確認できます。",
      "long_narration": "在庫管理システムは、M商品マスタを基盤に、3つの在庫トランザクションとV商品推移表で構成されています。T商品入庫は在庫を増やす記録です。T商品出庫は在庫を減らす記録です。T商品棚卸は、実際に数えた在庫数を記録するものです。ここで大事なのは、在庫残を直接手で書き換えるのではなく、入庫、出庫、棚卸という理由つきの記録を積み上げることです。V商品推移表は、これらに加えて生産受入と生産払出もまとめて計算します。表では、入、受、払、出、在の5行で表示されます。入は通常の入庫、受は生産受入、払は生産払出、出は通常の出庫、在は推定在庫です。動きの理由が分かるので、あとから見ても理解しやすい在庫管理になります。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_duration_sec": 7.128,
      "long_duration_sec": 53.568
    },
    {
      "id": "scene_002",
      "title": "入庫・出庫登録（T商品入庫・T商品出庫）",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125, 255, 179, 0.18)",
      "kicker": "RECEIVING & SHIPPING",
      "headline": "仕入・受入れと出荷・払出しを\nそれぞれトランザクションで記録する",
      "lead": "T商品入庫で在庫を増やし、T商品出庫で在庫を減らします。日々の在庫増減をこの2画面で管理します。",
      "subtitle": "T商品入庫とT商品出庫が在庫増減の2大トランザクションです。",
      "image": "images/scene_002.png",
      "image_prompt": "Vertical 2:3 screenshot-style mockup of two inventory forms side by side in Japanese: left panel T商品入庫 (receiving form with date, product, quantity, supplier) and right panel T商品出庫 (shipping form with date, product, quantity, destination), green accent, clean enterprise form design.",
      "chips": [
        "T商品入庫",
        "T商品出庫",
        "入庫日",
        "出庫日",
        "商品選択"
      ],
      "metrics": [
        {
          "label": "T商品入庫",
          "value": "在庫＋増加"
        },
        {
          "label": "T商品出庫",
          "value": "在庫−減少"
        }
      ],
      "cards": [
        {
          "title": "T商品入庫",
          "lines": [
            "入庫日・商品コード・入庫数量",
            "入庫備考と複数明細に対応",
            "在庫が増加するトランザクション"
          ]
        },
        {
          "title": "T商品出庫",
          "lines": [
            "出庫日・商品コード・出庫数量",
            "出庫備考と複数明細に対応",
            "在庫が減少するトランザクション"
          ]
        }
      ],
      "facts": [
        "T商品入庫は仕入れや受入れなど在庫を増加させるトランザクション。",
        "T商品出庫は出荷や払出しなど在庫を減少させるトランザクション。",
        "どちらも商品はM商品マスタからのドロップダウン選択で入力ミスを防ぐ。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "T商品入庫・T商品出庫: 在庫管理トランザクション"
        }
      ],
      "short_narration": "T商品入庫で在庫を増やし、T商品出庫で在庫を減らします。マスタから選ぶだけで記録できます。",
      "long_narration": "T商品入庫とT商品出庫は、在庫の増減を記録する2つのメイントランザクションです。実装ではどちらも明細型です。明細SEQが0の行に伝票日付と伝票備考を持ち、明細SEQが1以上の行に商品と数量を持ちます。つまり、1枚の入庫伝票に複数の商品明細を登録できます。T商品入庫では入庫日、商品ID、入庫数量、入庫備考を扱います。T商品出庫では出庫日、商品ID、出庫数量、出庫備考を扱います。商品はM商品から選ぶので、商品名の入力ゆれを防げます。登録後は合計入庫数量や合計出庫数量として一覧でも確認しやすくなります。監査フィールドも自動で残るため、いつ、誰が、どの伝票を登録したのかを追跡できます。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_duration_sec": 7.92,
      "long_duration_sec": 53.76
    },
    {
      "id": "scene_003",
      "title": "棚卸登録（T商品棚卸）",
      "expression": "neutral",
      "accent": "#ff8a6b",
      "accent_soft": "rgba(255, 138, 107, 0.18)",
      "kicker": "STOCKTAKING",
      "headline": "実地棚卸で\n現物の在庫数に合わせる",
      "lead": "T商品棚卸で現物の在庫数を記録し、推定在庫を実棚数量に合わせます。定期的な棚卸で在庫精度を維持します。",
      "subtitle": "T商品棚卸が在庫精度を保つための棚卸トランザクションです。",
      "image": "images/scene_003.png",
      "image_prompt": "Vertical 2:3 screenshot-style mockup of an inventory stocktaking registration form in Japanese, showing stocktaking date, product selection, actual count, book count and difference calculation fields, orange-red accent, clean enterprise form design.",
      "chips": [
        "棚卸日付",
        "商品",
        "実在庫数",
        "実棚数量",
        "推定在庫"
      ],
      "metrics": [
        {
          "label": "T商品棚卸",
          "value": "棚卸TX"
        },
        {
          "label": "棚卸反映",
          "value": "推定在庫"
        }
      ],
      "cards": [
        {
          "title": "登録項目",
          "lines": [
            "棚卸日・商品コード",
            "実在庫数（現物カウント値）",
            "推定在庫を実棚数量に合わせる"
          ]
        },
        {
          "title": "棚卸の役割",
          "lines": [
            "紛失・劣化・計上漏れによるズレを補正",
            "定期棚卸でデータの信頼性を維持",
            "V商品推移表の集計に自動反映"
          ]
        }
      ],
      "facts": [
        "T商品棚卸は実地棚卸で現物の在庫数を記録し、V商品推移表で推定在庫へ反映するトランザクション。",
        "棚卸結果はV商品推移表の集計に自動反映され、棚卸後すぐに正確な在庫残高を確認できる。",
        "定期的な棚卸により、入出庫の記録漏れや現物ズレを継続的に補正できる。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "T商品棚卸: 在庫管理トランザクション"
        }
      ],
      "short_narration": "T商品棚卸で実地棚卸を記録し、帳簿との差異を計算します。定期棚卸で在庫データを維持します。",
      "long_narration": "T商品棚卸は、実際に数えた在庫数を記録するトランザクションです。こちらも明細型で、明細SEQが0の行に棚卸日と棚卸備考を持ち、明細SEQが1以上の行に商品IDと実棚数量を持ちます。実棚数量とは、現場で本当に数えた数のことです。システム上の計算では、入庫と出庫を積み上げて推定在庫を出します。しかし現場では、破損、紛失、数え間違い、入力忘れなどでズレることがあります。棚卸を登録すると、V商品推移表ではその日の在庫を実棚数量に合わせて、そこから先の推定在庫を計算し直します。これにより、帳簿だけを信じるのではなく、現物確認で在庫の正確さを取り戻せます。月末や棚卸日ごとの確認に向いた機能です。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_duration_sec": 8.616,
      "long_duration_sec": 52.08
    },
    {
      "id": "scene_004",
      "title": "商品推移表（V商品推移表）",
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123, 140, 255, 0.18)",
      "kicker": "STOCK MOVEMENT VIEW",
      "headline": "在庫推移を確認しながら\nその場で入出庫を登録できる",
      "lead": "V商品推移表で在庫の動きを一覧確認。セルをダブルクリックすれば各伝票画面に遷移して登録・修正でき、この画面だけで在庫ショートを防いだまま業務が完結します。",
      "subtitle": "V商品推移表が在庫管理の中心的な確認・操作画面です。",
      "image": "images/scene_004.png",
      "image_prompt": "Vertical 2:3 screenshot-style mockup of a stock movement table view in Japanese, showing date, product, in/out quantities and running balance in a clean grid with a highlighted cell showing double-click navigation hint, blue-violet accent, enterprise reporting style.",
      "chips": [
        "期間指定",
        "商品絞り込み",
        "ダブルクリック遷移",
        "在庫残",
        "業務完結"
      ],
      "metrics": [
        {
          "label": "V商品推移表",
          "value": "集計表示"
        },
        {
          "label": "ダブルクリック",
          "value": "伝票へ遷移"
        }
      ],
      "cards": [
        {
          "title": "在庫推移の一覧確認",
          "lines": [
            "入庫・出庫・棚卸・在庫残を日付順に集計",
            "期間と商品を指定して絞り込み検索",
            "在庫ショートの予兆をひと目で把握"
          ]
        },
        {
          "title": "ダブルクリックで伝票へ遷移",
          "lines": [
            "セルをダブルクリックで各伝票画面へ直接遷移",
            "入庫・出庫・棚卸の新規追加もこの画面から",
            "確認→登録を一画面で完結、在庫ショートを防ぐ"
          ]
        }
      ],
      "facts": [
        "V商品推移表はDB VIEWオブジェクトではなく、Router内の生SQL集計エンドポイント。",
        "推移表のセルをダブルクリックすることで、対応する入庫・出庫・棚卸の伝票画面に遷移できる。",
        "在庫残の確認から伝票登録までこの画面で完結するため、在庫ショートをリアルタイムに防げる。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "V商品推移表: V系View endpoint、在庫推移のJOIN/集計表示"
        }
      ],
      "short_narration": "推移表で在庫推移を確認。ダブルクリックで入出庫を登録でき、在庫ショートを防いで業務完結です。",
      "long_narration": "V商品推移表は、在庫管理の中心となる確認画面です。開始日から32日分を横に並べ、商品ごとに入、受、払、出、在の5行で表示します。入庫、出庫、棚卸だけでなく、生産管理から来る生産受入と生産払出も同じ表に入ります。商品分類で絞り込めるので、原材料だけ、製品だけ、といった見方もできます。土曜と日曜は背景色が変わり、棚卸が入った在庫セルは見た目も変わります。在庫がマイナスになったセルは赤く表示されるので、不足しそうな商品を見つけやすくなります。セルをダブルクリックすると、入庫、出庫、棚卸、生産受入、生産払出のそれぞれの一覧へ移動できます。見つける、原因を見る、必要なら伝票を直す、という流れが短くなります。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_duration_sec": 8.136,
      "long_duration_sec": 53.304
    },
    {
      "id": "scene_005",
      "title": "伝票フォーム（入庫・出庫・棚卸）",
      "expression": "neutral",
      "accent": "#ffbf47",
      "accent_soft": "rgba(255, 191, 71, 0.18)",
      "kicker": "SLIP FORM",
      "headline": "推移表からダブルクリックで\n各伝票画面へ直接遷移",
      "lead": "V商品推移表のセルをダブルクリックするだけで、入庫・出庫・棚卸の各伝票フォームが開きます。新規追加も同じフォームで完結します。",
      "subtitle": "入庫・出庫・棚卸の伝票フォームはV商品推移表と連動しています。",
      "image": "images/scene_005.png",
      "image_prompt": "Vertical 2:3 screenshot-style mockup of an inventory receiving form in Japanese, showing fields for 入庫日, 商品コード, 入庫数量, 入庫備考, amber accent, clean enterprise form design.",
      "chips": [
        "推移表から呼出",
        "入庫伝票",
        "出庫伝票",
        "棚卸伝票",
        "新規追加"
      ],
      "metrics": [
        {
          "label": "呼出元",
          "value": "推移表"
        },
        {
          "label": "操作",
          "value": "登録・編集"
        }
      ],
      "cards": [
        {
          "title": "推移表から直接呼び出せる",
          "lines": [
            "推移表のセルをダブルクリックで伝票フォームが開く",
            "商品・日付を引き継いだ状態でフォームが起動",
            "新規追加ボタンからも同じフォームを使用"
          ]
        },
        {
          "title": "入庫・出庫・棚卸の各フォーム",
          "lines": [
            "T商品入庫: 入庫日・商品・数量・備考",
            "T商品出庫: 出庫日・商品・数量・備考",
            "T商品棚卸: 棚卸日・商品・実棚数量・備考"
          ]
        }
      ],
      "facts": [
        "推移表のセルをダブルクリックすると、その商品・日付を引き継いだ状態で伝票フォームが開く。",
        "入庫・出庫・棚卸のすべての伝票が共通のフォームデザインで操作感が統一されている。",
        "登録後は自動的に推移表に反映され、在庫残の変化をすぐに確認できる。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "T商品入庫・T商品出庫・T商品棚卸: 在庫管理トランザクション"
        }
      ],
      "short_narration": "推移表からダブルクリックで各伝票フォームへ遷移します。商品・日付を引き継いで開くので入力が速いです。",
      "long_narration": "V商品推移表から各伝票画面への移動は、実装上かなり便利に作られています。入庫のセルをダブルクリックするとT商品入庫一覧へ、出庫のセルならT商品出庫一覧へ、在庫行ならT商品棚卸一覧へ移動します。生産受入のセルはT生産一覧へ、生産払出のセルはT生産払出一覧へ移動します。そのとき、日付、商品ID、URLメニュー、URL戻り先を持って移動するので、対象データを絞り込んだ状態で開けます。URL戻り先があるため、確認後に推移表へ戻る流れも自然です。さらに推移表は30秒ごとに最終更新日時を確認し、更新があれば再読み込みします。最近更新されたセルは点滅表示されるので、どこが変わったかにも気づきやすくなっています。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_duration_sec": 8.4,
      "long_duration_sec": 50.352
    },
    {
      "id": "scene_999",
      "title": "生産管理と連動した在庫管理",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125, 255, 179, 0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "INTEGRATED MANAGEMENT",
      "headline": "生産管理と連動すると\n資材払出・生産受入まで在庫管理",
      "lead": "AiDiy の生産管理スケジューラーと連動すると、材料の払出と製品の受入が在庫トランザクションに自動記録され、在庫管理の範囲が製造現場まで広がります。",
      "subtitle": "AiDiyの在庫管理と生産管理、つかってみませんか？",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "image": "images/scene_999.png",
      "image_prompt": "Square 1:1 elegant infographic showing integration of inventory management and production management. Left side: inventory movement table with amber accent. Right side: production scheduler calendar with green accent. Connected by arrows in the center showing material disbursement and production receipt flow. Dark background, professional enterprise style, 'Inventory x Production' concept.",
      "short_narration": "生産管理と連動すると資材払出・生産受入が在庫に記録されます。AiDiyの在庫管理と生産管理、つかってみませんか？",
      "long_narration": "在庫管理だけでも使えますが、AiDiyの生産管理と連動させると、できることがさらに増えます。V商品推移表のバックエンドでは、T生産のヘッダー行を生産受入、T生産の明細行を生産払出として集計しています。製品が完成する予定日は受入として在庫を増やし、材料を使う予定日は払出として在庫を減らします。これにより、単純な入庫と出庫だけでは見えない、製造予定を含めた在庫の変化が見えるようになります。たとえば、来週の生産で材料が足りなくなりそうなら、早めに発注できます。反対に、作りすぎで在庫が増えすぎそうなら、生産予定を見直せます。AiDiyの在庫管理と生産管理は、過去の記録を見るだけでなく、これから起きる在庫の変化を考えるためにも使えます。AiDiyの在庫管理と生産管理、使ってみませんか？",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_duration_sec": 9.792,
      "long_duration_sec": 53.952
    }
  ],
  "short_duration_sec": 59.616,
  "long_duration_sec": 364.512
};
