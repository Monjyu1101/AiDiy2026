window.SCENARIO = {
  "project_name": "AiDiy紹介_AIタスク_ja",
  "version": "mcp",
  "title": "AiDiy AIタスク - 日本語で書くだけ、あとは AI が手順を作って決めた時刻に動きます",
  "source": {
    "type": "agents_and_knowledge",
    "summary": "AiDiy の AIタスク機能を backend_taskteam/AGENTS.md と AGENTS.md・frontend_web/src/components/AIタスク/ の現行実装に基づいて、初心者向けに紹介する。"
  },
  "target": {
    "language": "ja-JP",
    "format": "html_css_scene_player_with_media",
    "tone": "初心者向け、専門用語を避けたやさしい語り口、短い文、実画面で安心感",
    "goal": "パソコンの自動化をやったことがない人が『これなら自分にもできそう』と思えること。"
  },
  "assets_policy": {
    "visual_style": "left_avatar_38_right_content_62",
    "audio_dir": "audio",
    "image_dir": "images",
    "avatar": "../_vrm/VRM_AiDiy.vrm",
    "tts_provider": "freeai:female",
    "image_source_note": "scene_003 / scene_004 / scene_006 は ../sozai/ の実画面スクリーンショットを images/scene_NNN.png へコピーして使用（AI 画像生成はスキップされる）。"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "毎日の繰り返しを AI にお願いする",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.2)",
      "kicker": "INTRODUCTION",
      "headline": "「やっておいて」と書くだけ。\nあとは AI が手順を考えて\n動いてくれます",
      "lead": "AiDiy の AIタスクは、やってほしいことを日本語で書くだけで使えます。AI が手順を考え、順番どおりに進め、決めた時刻には自分から動き出します。パソコンにくわしくなくても大丈夫です。",
      "subtitle": "お願いを書く → AI が手順に分ける → 順番どおりに進む → 決めた時刻に自分から始まる。",
      "image": "images/scene_000.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "image_prompt": "Warm, friendly widescreen illustration for a beginner-friendly automation introduction. A tidy desk with a laptop, a handwritten note, and a soft glowing AI companion light beside it, gentle sunrise colors, calm and welcoming mood, no text in the image.",
      "short_narration": "やってほしいことを日本語で書くだけ。あとは AI が手順を考えて進めてくれます。",
      "long_narration": "この動画は、AiDiy のビデオページ生成機能で自動生成されました。台本づくりから画像、音声まで、すべて AI が作っています。さて、みなさんには、毎日おなじ手順でくり返している仕事はありませんか。情報を集めて、まとめて、決まった形に整えて、そして保存する。手間はかかるのに、頭はあまり使わない。そんな作業です。AiDiy の AIタスクは、その作業を肩代わりしてくれます。使い方は、やってほしいことを日本語で書くだけ。むずかしい設定も、プログラムも要りません。AI が中身を読んで、手順に分けて、順番どおりに進めてくれます。そして、いちばんうれしいのはここからです。決めた時刻になると、AI が自分から動き出します。この動画では、実際の画面を見ながら、その流れをやさしく紹介します。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 5.28,
      "long_start_sec": 0.0,
      "long_duration_sec": 48.312,
      "layout": "hero",
      "hero_image_focus": true,
      "background_word": ""
    },
    {
      "id": "scene_001",
      "title": "やってほしいことを書く",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125, 255, 179, 0.18)",
      "kicker": "STEP 1 — お願いを書く",
      "headline": "日本語で書いて、\n作業するフォルダを選ぶ。\nそれだけです",
      "lead": "新規ボタンを押して、やってほしいことを日本語で書きます。作業してほしいフォルダを選んだら登録するだけ。専門的な書き方は必要ありません。話しかけるように書けば大丈夫です。",
      "subtitle": "お願いの文章と、作業するフォルダ。まずはこの 2 つだけ決めます。",
      "image": "images/scene_001.png",
      "chips": [
        "日本語で書くだけ",
        "作業するフォルダを選ぶ",
        "箇条書きでもよい",
        "あとから直せる"
      ],
      "metrics": [
        {
          "label": "書き方",
          "value": "ふつうの日本語"
        },
        {
          "label": "決めること",
          "value": "文章とフォルダ"
        },
        {
          "label": "書き直し",
          "value": "いつでも可"
        }
      ],
      "cards": [
        {
          "title": "書くのはこれだけ",
          "lines": [
            "やってほしいことを、話しかけるように",
            "手順が分かっていれば箇条書きでもよい",
            "作業してほしいフォルダを選ぶ"
          ]
        },
        {
          "title": "書き方の例",
          "lines": [
            "最新のニュースを集めてまとめてほしい",
            "この資料を決まった形に整えてほしい",
            "画面の見づらいところを直してほしい"
          ]
        },
        {
          "title": "うれしいポイント",
          "lines": [
            "手順を自分で考えなくてよい",
            "うまくいかなければ書き直せる",
            "登録した内容はあとから読み返せる"
          ]
        }
      ],
      "facts": [
        "タスク要求には要求内容・プロジェクト・フォルダ指定を登録する。",
        "要求内容には人間が入力した文章をそのまま保持し、AI が整理した文章は応答内容へ書き込む。",
        "AIタスクは backend_taskteam（ポート 8093）が担当し、API は /task/*。"
      ],
      "evidence": [
        {
          "source": "backend_taskteam/task_proc/tasks_db.py",
          "text": "要求内容には仮登録時の人間の入力をそのまま引き継ぎ、AI がタスク分解のために整理した文章は応答内容へ書き込む。"
        },
        {
          "source": "AGENTS.md",
          "text": "AIタスクは backend_taskteam（ポート 8093）が担当し、API は /task/*。"
        }
      ],
      "image_prompt": "Friendly widescreen illustration: a person typing a short request in plain language on a laptop, a folder icon glowing softly beside it, clean, bright, approachable, no text in the image.",
      "short_narration": "やってほしいことを日本語で書いて、作業するフォルダを選びます。",
      "long_narration": "まずは、お願いを書くところから見てみましょう。新規ボタンを押すと、入力の画面が開きます。そこに、やってほしいことを日本語で書きます。話しかけるような書き方でかまいません。たとえば、最新のニュースを集めてまとめてほしい。この資料を決まった形に整えてほしい。そんな具合です。手順が頭の中にあるなら、箇条書きで添えてもかまいません。細かく書けば、そのとおりに進めてくれます。つぎに、作業してほしいフォルダを選びます。決めるのは、この 2 つだけです。うまくいかなかったら、書き直してもう一度お願いすればいい。気軽に試してみてください。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 4.056,
      "long_start_sec": 0.0,
      "long_duration_sec": 36.984
    },
    {
      "id": "scene_002",
      "title": "AI を役割で選ぶ",
      "expression": "neutral",
      "accent": "#b79bff",
      "accent_soft": "rgba(183, 155, 255, 0.18)",
      "kicker": "STEP 2 — 役割で選ぶ",
      "headline": "考える AI、作業する AI、\n確認する AI。\n別々に選べます",
      "lead": "使う AI は、役割ごとに分けて選べます。手順を組み立てる、考える AI。実際に手を動かす、作業する AI。最後に見直す、確認する AI。得意なところに、得意な AI を割り当てられます。",
      "subtitle": "じっくり考えるところは賢い AI に。速さがほしいところは軽い AI に。",
      "image": "images/scene_002.png",
      "chips": [
        "考える AI",
        "作業する AI",
        "確認する AI",
        "それぞれ別に選べる"
      ],
      "metrics": [
        {
          "label": "役割",
          "value": "3 つに分かれる"
        },
        {
          "label": "選び方",
          "value": "一覧から選ぶだけ"
        },
        {
          "label": "迷ったら",
          "value": "そのままでよい"
        }
      ],
      "cards": [
        {
          "title": "3 つの役割",
          "lines": [
            "考える AI … 手順を組み立てる",
            "作業する AI … 実際に手を動かす",
            "確認する AI … 最後に見直す"
          ]
        },
        {
          "title": "使い分けの考え方",
          "lines": [
            "手順を考えるところは、じっくり賢い AI に",
            "たくさん動かすところは、軽くて速い AI に",
            "最後の確認は、しっかりした AI に"
          ]
        },
        {
          "title": "うれしいポイント",
          "lines": [
            "得意なところに得意な AI を置ける",
            "全部を高い AI にしなくてよい",
            "迷ったら初期のままで大丈夫"
          ]
        }
      ],
      "facts": [
        "TASK_AI_NAME に Code CLI（claude_cli / codex_cli / copilot_cli など）を選ぶ。",
        "TASK_AI_MODEL_plan（準備＝AI による明細分解）、TASK_AI_MODEL_do（各ステップの実行）、TASK_AI_MODEL_check（終了時の最終確認）の 3 種を個別に指定できる。",
        "モデル指定は明細にも引き継がれ、各ステップは TASK_AI_MODEL_do で動く。"
      ],
      "evidence": [
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "TASK_AI_NAME に Code CLI を選び、TASK_AI_MODEL_plan / _do / _check の 3 種を個別に指定できる。"
        },
        {
          "source": "backend_taskteam/task_proc/tasks_db.py",
          "text": "分解は plan、生成する明細へ引き継ぐのは do（check は終了明細が使う）。"
        }
      ],
      "image_prompt": "Clean widescreen illustration: three distinct soft glowing helper icons in a row — one thinking with a plan sketch, one working with tools, one checking with a magnifier — connected by a gentle flowing line, bright and instructional, no text in the image.",
      "short_narration": "使う AI は、考える・作業する・確認するの役割ごとに選べます。",
      "long_narration": "つぎは、使う AI を選びます。ここがちょっとおもしろいところです。AI は、役割ごとに分けて選べます。役割は 3 つ。ひとつめは、考える AI。お願いを読んで、必要な手順を組み立てる担当です。ふたつめは、作業する AI。分かれた手順を、ひとつずつ実際に片づけていく担当です。みっつめは、確認する AI。最後に、ちゃんとできているかを見直す担当です。この 3 つに、それぞれ別の AI を割り当てられます。手順を考えるところは、じっくり賢い AI に。たくさん動かすところは、軽くて速い AI に。そんな使い分けができます。もちろん、迷ったら初期のままでも大丈夫です。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 5.064,
      "long_start_sec": 0.0,
      "long_duration_sec": 38.376
    },
    {
      "id": "scene_003",
      "title": "AI が手順に分けてくれる",
      "expression": "neutral",
      "accent": "#ffc46b",
      "accent_soft": "rgba(255, 196, 107, 0.18)",
      "kicker": "STEP 3 — 手順に分かれる",
      "headline": "1 つのお願いが\n14 の手順に分かれました",
      "lead": "登録すると、AI がお願いの中身を読んで、必要な手順を自動で書き出します。画面は 3 つに分かれていて、左が受け付けたお願い、まん中が流れ図、右が分かれた手順の一覧です。",
      "subtitle": "左＝お願いの一覧、まん中＝流れ図、右＝分かれた手順。進み具合がひと目で分かります。",
      "image": "images/scene_003.png",
      "chips": [
        "お願いは 1 つ",
        "手順は 14 に",
        "3 つに分かれた画面",
        "進み具合が見える"
      ],
      "metrics": [
        {
          "label": "書いたお願い",
          "value": "1 つ"
        },
        {
          "label": "分かれた手順",
          "value": "14"
        },
        {
          "label": "人がやること",
          "value": "見ているだけ"
        }
      ],
      "cards": [
        {
          "title": "画面の見方",
          "lines": [
            "左 … 受け付けたお願いの一覧",
            "まん中 … 手順のつながりを描いた流れ図",
            "右 … 分かれた手順と、いまの状態"
          ]
        },
        {
          "title": "AI がやってくれること",
          "lines": [
            "お願いを読んで、必要な手順を書き出す",
            "最初に、もとのファイルの控えを取る手順を置く",
            "最後に、仕上がりを見直す手順を足す"
          ]
        },
        {
          "title": "状態の見方",
          "lines": [
            "待機 … 順番を待っているところ",
            "実行中 … いま動いているところ",
            "完了 … 終わったところ"
          ]
        }
      ],
      "facts": [
        "要求を『準備開始』で登録すると Task 起動監視（5 秒間隔）が『準備中』へ進め、task_sub/sub_init.py を起動する。",
        "AI が要求を開始行・処理行・終了行へ分解して本登録する。",
        "本登録後の状態は常に『準備完了』で、即時なら状態監視ループ（10 秒間隔）が『待機』へ戻して実行を始める。",
        "明細の状態は 待機 / 実行中 / 完了 / エラー / 中止 で、PID・開始日時・実行回数とともに画面に出る。"
      ],
      "evidence": [
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "Task 起動監視が要求を準備中へ進め task_sub/sub_init.py を起動する。AI が要求を明細へ分解し、開始行・処理行・終了行を本登録する。"
        },
        {
          "source": "backend_taskteam/task_proc/tasks_db.py",
          "text": "要求の状態は常に 準備完了（実行開始条件の充足待ち）で書き込む。即時実行の場合は状態監視ループが 10 秒ごとに 準備完了 を 待機 へ戻して即座に実行を開始する。"
        }
      ],
      "image_prompt": "(実画面を使用) sozai/web_AIタスク.png",
      "short_narration": "登録すると AI がお願いを読んで、手順に分けてくれます。",
      "long_narration": "登録が終わると、AI がすぐに動きはじめます。お願いの中身を読んで、必要な手順を自動で書き出してくれます。いま画面に出ているのが、その結果です。1 つのお願いが、14 の手順に分かれました。画面は 3 つに分かれています。左が、受け付けたお願いの一覧。まん中が、手順のつながりを描いた流れ図。右が、分かれた手順の一覧です。手順には、それぞれ今の状態が出ます。順番を待っているのか、いま動いているのか、もう終わったのか。ひと目で分かります。手順の中には、AI が気をきかせて足してくれるものもあります。たとえば、いちばん最初に、もとのファイルの控えを取っておく手順。そして、いちばん最後に、仕上がりを見直す手順です。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 3.504,
      "long_start_sec": 0.0,
      "long_duration_sec": 43.536,
      "image_source": "sozai/web_AIタスク.png"
    },
    {
      "id": "scene_004",
      "title": "手順の中身を見てみる",
      "expression": "neutral",
      "accent": "#ff9ad5",
      "accent_soft": "rgba(255, 154, 213, 0.18)",
      "kicker": "STEP 4 — 手順の中身",
      "headline": "1 つの手順に書いてあるのは、\nたった 3 つです",
      "lead": "手順を開くと、何をする手順かというタイトル、AI へのお願いの文章、そして、どの手順が終わったら始めるかの指定が入っています。気になるところは、あとから書き直せます。",
      "subtitle": "AI が書いた手順を、人が読んで直せる。任せきりにならないところが安心です。",
      "image": "images/scene_004.png",
      "chips": [
        "タイトル",
        "やることの文章",
        "どれが終わったら始めるか",
        "あとから直せる"
      ],
      "metrics": [
        {
          "label": "中身",
          "value": "3 つだけ"
        },
        {
          "label": "書いたのは",
          "value": "AI"
        },
        {
          "label": "直せるのは",
          "value": "いつでも"
        }
      ],
      "cards": [
        {
          "title": "手順 1 つの中身",
          "lines": [
            "タイトル … 何をする手順か",
            "やること … AI へのお願いの文章",
            "どれが終わったら始めるか … 順番の指定"
          ]
        },
        {
          "title": "人が手を入れられる",
          "lines": [
            "文章が物足りなければ書き足す",
            "使う AI をこの手順だけ変えられる",
            "一時的に外しておくこともできる"
          ]
        },
        {
          "title": "うれしいポイント",
          "lines": [
            "AI 任せにせず中身を確かめられる",
            "気になる手順だけ直せる",
            "直した内容は次から反映される"
          ]
        }
      ],
      "facts": [
        "AIタスク明細はタイトル・要求内容・先行SEQ・TASK_AI_NAME・TASK_AI_MODEL_do・操作検証・実行有効・状態を持つ。",
        "明細は編集ダイアログから個別に修正でき、実行中なら該当プロセスを停止してから更新する。",
        "実行有効を外した明細は実行対象にならない（明細作成は実行有効フラグに関係なく行う）。"
      ],
      "evidence": [
        {
          "source": "backend_taskteam/task_proc/tasks_api.py",
          "text": "明細編集ダイアログからの更新。実行中なら該当明細のプロセスを停止してから更新する。"
        },
        {
          "source": "backend_taskteam/task_proc/tasks_db.py",
          "text": "明細の 実行有効 = 0 は実行対象にしない（明細作成は実行有効フラグに関係なく行う）。"
        }
      ],
      "image_prompt": "(実画面を使用) sozai/web_AIタスク_明細編集.png",
      "short_narration": "手順に書いてあるのは、タイトルとやること、そして順番の指定だけです。",
      "long_narration": "手順を 1 つ開いてみましょう。中身はとてもかんたんです。書いてあるのは、3 つだけ。何をする手順かというタイトル。AI へのお願いを書いた、やることの文章。そして、どの手順が終わったら始めるか、という順番の指定です。これを書いたのは AI ですが、人が読んで直すこともできます。説明が物足りないと思ったら、書き足せばいい。この手順だけ別の AI に任せたい、ということもできます。今回はここを飛ばしたい、というときは、一時的に外しておくこともできます。AI に任せきりにせず、中身を確かめて、気になるところだけ直せる。そこが安心なところです。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 4.512,
      "long_start_sec": 0.0,
      "long_duration_sec": 37.896,
      "image_source": "sozai/web_AIタスク_明細編集.png"
    },
    {
      "id": "scene_005",
      "title": "順番と、同時に進むところ",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125, 255, 179, 0.18)",
      "kicker": "STEP 5 — 順番と並行",
      "headline": "待つものは待ち、\n待たなくていいものは\n同時に進みます",
      "lead": "手順のつながりは、まん中の流れ図で見られます。前の手順が終わるまで、次は静かに待ちます。待たなくてよいものは同時に走ります。いちばん時間のかかる道すじも、画面の下に出ます。",
      "subtitle": "順番を人が見張らなくていい。全体像は流れ図で確かめられます。",
      "image": "images/scene_005.png",
      "chips": [
        "流れ図で見える",
        "待つものは待つ",
        "同時に進むものもある",
        "長い道すじが分かる"
      ],
      "metrics": [
        {
          "label": "見る場所",
          "value": "まん中の流れ図"
        },
        {
          "label": "同時実行",
          "value": "できるものは同時"
        },
        {
          "label": "分かること",
          "value": "全体の道すじ"
        }
      ],
      "cards": [
        {
          "title": "順番はこう決まる",
          "lines": [
            "指定した手順が終わるまで静かに待つ",
            "待たなくてよい手順は同時に動き出す",
            "終わるたびに次が自動で始まる"
          ]
        },
        {
          "title": "流れ図の見方",
          "lines": [
            "上から下へ、矢印でつながる",
            "同時に進むものは横に並ぶ",
            "いちばん長い道すじが下に出る"
          ]
        },
        {
          "title": "うれしいポイント",
          "lines": [
            "順番を人が見張らなくてよい",
            "同時に進むぶん、早く終わる",
            "全体にどれくらいかかるか読める"
          ]
        }
      ],
      "facts": [
        "明細の依存は先行SEQ（カンマ区切りで複数指定可）による DAG で定義する。",
        "先行SEQ がすべて完了した明細を実行可能とし、依存を満たした明細は並行起動する。",
        "フロー図は最長経路をクリティカルパスとして配置し、画面下部に表示する。",
        "同一タスク内の code agent 系明細は 1 本ずつ、タスク間は並行実行する。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "明細の依存関係は先行SEQ（カンマ区切りで複数指定可）による DAG。直列だけでなく水平の並行分岐を含む自由なタスクフローを定義でき、画面のフロー図は最長経路をクリティカルパスとして配置する。"
        },
        {
          "source": "backend_taskteam/task_proc/tasks_watcher.py",
          "text": "code agent 系明細は同一タスク内で1本まで、タスク間は並行実行する。"
        }
      ],
      "image_prompt": "Clean widescreen illustration of a flowing branching path diagram made of soft glowing nodes: one path splits into two parallel branches and merges again, the longest route gently highlighted, bright and easy to read, no text in the image.",
      "short_narration": "待つものは待ち、待たなくていいものは同時に進みます。",
      "long_narration": "手順は、ただ上から順に流れるだけではありません。それぞれの手順には、どれが終わったら始めるか、という指定が入っています。指定された手順が終わるまで、次の手順は静かに待ちます。そして、待たなくてよい手順は、同時に動き出します。だから、ぜんぶを一列に並べるよりも早く終わります。全体のつながりは、画面まん中の流れ図で確かめられます。上から下へ、矢印でつながっていきます。同時に進むものは、横に並んで表示されます。そして画面の下には、いちばん時間のかかる道すじが出ます。ここを見れば、全体でどれくらいかかりそうかが読めます。順番を人が見張る必要は、もうありません。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 3.72,
      "long_start_sec": 0.0,
      "long_duration_sec": 38.304
    },
    {
      "id": "scene_006",
      "title": "決めた時刻に、AI が自分から動く",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.2)",
      "kicker": "KEY — 決めた時刻に動く",
      "headline": "一度登録すれば\n毎日・毎週・毎月、\nAI が自分から始めます",
      "lead": "ここが AIタスクのいちばんの特徴です。すぐ動かす、日時を決めて 1 回だけ、何分おき・何時間おき、毎日や毎週の決まった時刻。この 4 つから選べます。",
      "subtitle": "朝 6 時に情報集め、夜 22 時に日報づくり。人が居なくても回り続けます。",
      "image": "images/scene_006.png",
      "chips": [
        "すぐ動かす",
        "日時を決めて 1 回",
        "何分・何時間おき",
        "毎日・毎週・毎月"
      ],
      "metrics": [
        {
          "label": "動かし方",
          "value": "4 つから選ぶ"
        },
        {
          "label": "人がやること",
          "value": "最初の 1 回だけ"
        },
        {
          "label": "止めたいとき",
          "value": "スイッチひとつ"
        }
      ],
      "cards": [
        {
          "title": "4 つの動かし方",
          "lines": [
            "すぐ動かす … 登録したらそのまま開始",
            "日時を決めて 1 回だけ … 予約のように",
            "何分・何時間・何日おき … くり返し",
            "毎日・毎週・毎月の決まった時刻 … いちばん人気"
          ]
        },
        {
          "title": "こんな使い方ができます",
          "lines": [
            "朝 6 時に、その日の情報を集めておく",
            "夜 22 時に、一日の記録をまとめる",
            "毎週月曜に、週次のまとめを作る"
          ]
        },
        {
          "title": "安心なところ",
          "lines": [
            "くり返しの 1 回目はすぐ動く",
            "止めていた間の分はまとめて動かない",
            "止めたいときはスイッチを切るだけ"
          ]
        }
      ],
      "facts": [
        "実行区分は即時 / 時間指定 / 間隔実行 / 定時実行の 4 種。",
        "間隔実行は間隔区分（分・時・日）＋間隔値、定時実行は定時区分（毎日・毎週・毎月）＋実行曜日 / 実行日 / 開始時刻で指定する。",
        "間隔実行の 1 回目は間隔を待たずに即時発火し、2 回目以降が発火時刻＋間隔で回る。",
        "サーバー停止中に期限を過ぎた条件は、起動時に過去分を一括発火させず次の周期へ更新する。"
      ],
      "evidence": [
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "実行区分は即時 / 時間指定 / 間隔実行 / 定時実行。間隔実行は間隔区分（分・時・日）＋間隔値、定時実行は定時区分（毎日・毎週・毎月）＋実行曜日 / 実行日 / 開始時刻で指定する。"
        },
        {
          "source": "backend_taskteam/task_proc/tasks_watcher.py",
          "text": "間隔実行でまだ一度も実行していない（準備完了かつ前回実行日時なし）ときは、間隔を待たず基準時刻で発火する。2 回目以降は発火時刻 + 間隔。"
        }
      ],
      "image_prompt": "(実画面を使用) sozai/web_AIタスク_定時実行.png",
      "short_narration": "一度登録すれば、毎日・毎週・毎月、決めた時刻に AI が自分から動き出します。",
      "long_narration": "さあ、ここがいちばんの特徴です。画面の右側を見てください。ここで、いつ動かすかを決めます。選べるのは 4 つ。登録したらすぐ動かす。日時を決めて 1 回だけ動かす。10 分おき、1 時間おきのように、くり返し動かす。そして、毎日・毎週・毎月の決まった時刻に動かす、です。いちばんよく使われるのが、最後の決まった時刻です。たとえば、朝 6 時にその日の情報を集めておく。夜の 22 時に、一日の記録をまとめる。一度登録しておけば、あとは何もしなくても、AI が毎日その時刻に動き出します。くり返しを選んだときは、1 回目は待たずにすぐ動きます。様子を見てから任せられるので安心です。パソコンを止めていた間に時刻を過ぎてしまっても、あわてて何回もまとめて動いたりはしません。",
      "short_audio": "audio/short_scene_006.mp3",
      "long_audio": "audio/long_scene_006.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 5.928,
      "long_start_sec": 0.0,
      "long_duration_sec": 46.344,
      "image_source": "sozai/web_AIタスク_定時実行.png"
    },
    {
      "id": "scene_007",
      "title": "フォルダに届いたら動かす",
      "expression": "neutral",
      "accent": "#ffe066",
      "accent_soft": "rgba(255, 224, 102, 0.18)",
      "kicker": "STEP 7 — きっかけを変える",
      "headline": "時刻ではなく、\nフォルダの中身が変わったら\n動かせます",
      "lead": "動き出すきっかけは、時刻だけではありません。見張るフォルダを 1 つ選んでおくと、そこにファイルが増えたり、更新されたときだけ動きます。資料が届いたら処理する、という使い方です。",
      "subtitle": "届いたときだけ動く。何も来ない日は、静かに待っています。",
      "image": "images/scene_007.png",
      "chips": [
        "見張るフォルダを選ぶ",
        "中身が変わったら動く",
        "何もなければ動かない",
        "時刻の指定と組み合わせも"
      ],
      "metrics": [
        {
          "label": "きっかけ",
          "value": "フォルダの変化"
        },
        {
          "label": "見るもの",
          "value": "数と更新の日時"
        },
        {
          "label": "最初の 1 回",
          "value": "覚えるだけ"
        }
      ],
      "cards": [
        {
          "title": "こんなときに便利",
          "lines": [
            "取引先から資料が届いたら整える",
            "写真を置いたら決まった形に変換する",
            "報告書が集まったらまとめる"
          ]
        },
        {
          "title": "どう見張るのか",
          "lines": [
            "フォルダの中のファイルの数を覚える",
            "いちばん新しい更新の日時も覚える",
            "前と変わっていたら動き出す"
          ]
        },
        {
          "title": "安心なところ",
          "lines": [
            "登録した直後は覚えるだけで動かない",
            "変化がない日は静かに待っている",
            "見張るのは選んだフォルダだけ"
          ]
        }
      ],
      "facts": [
        "実行条件は『無し / フォルダ変化』。フォルダ変化は監視フォルダ直下のファイル数と最新更新日時のスナップショット比較で判定する。",
        "初回はスナップショットの取得だけを行い発火しない（登録直後の誤発火防止）。",
        "実行区分が即時 + フォルダ変化のときは毎分確認する。",
        "監視フォルダを参照できないときは発火せず次の周期へ送る。"
      ],
      "evidence": [
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "実行条件は『無し / フォルダ変化』で、フォルダ変化は監視フォルダのファイル数と最終更新日時のスナップショット比較で判定する。"
        },
        {
          "source": "backend_taskteam/task_proc/tasks_watcher.py",
          "text": "初回はスナップショット取得のみ（登録直後の誤発火防止）。変化なしのときは発火せず次周期へ。"
        }
      ],
      "image_prompt": "Warm widescreen illustration: an open folder on a desk with a single new document gently dropping into it, a soft glowing sensor ring around the folder noticing the change, calm and clear mood, no text in the image.",
      "short_narration": "見張るフォルダに資料が届いたときだけ動かす、という使い方もできます。",
      "long_narration": "動き出すきっかけは、時刻だけではありません。もうひとつ、便利な選び方があります。フォルダを見張らせる、という方法です。見張ってほしいフォルダを 1 つ選んでおきます。すると、そこにファイルが増えたときや、中身が新しくなったときだけ動きます。たとえば、取引先から資料が届いたら、決まった形に整える。写真を置いたら、まとめて変換する。そんな使い方ができます。何も届かない日は、静かに待っているだけです。見張り方はかんたんです。フォルダの中のファイルの数と、いちばん新しい更新の日時を覚えておいて、前と変わっていたら動き出します。登録した直後の 1 回目は、覚えるだけで動きません。いきなり走り出さないように、という配慮です。",
      "short_audio": "audio/short_scene_007.mp3",
      "long_audio": "audio/long_scene_007.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 3.816,
      "long_start_sec": 0.0,
      "long_duration_sec": 45.36
    },
    {
      "id": "scene_008",
      "title": "できたか確かめて、やり直す",
      "expression": "neutral",
      "accent": "#ffc46b",
      "accent_soft": "rgba(255, 196, 107, 0.18)",
      "kicker": "STEP 8 — 確かめる",
      "headline": "作業のあとに確認して、\nだめならもう一度だけ\nやり直します",
      "lead": "手順には、確認するかどうかの印を付けられます。印を付けた手順は、作業のあとに結果を確かめます。何も変わっていない、エラーが出た。そんなときは、もう一度だけやり直します。",
      "subtitle": "言われたとおりに動いたか。そこまで見てくれるので、任せられます。",
      "image": "images/scene_008.png",
      "chips": [
        "確認の印を付ける",
        "作業のあとに確かめる",
        "だめなら 1 回やり直す",
        "それでもだめなら止まる"
      ],
      "metrics": [
        {
          "label": "確認",
          "value": "手順ごとに指定"
        },
        {
          "label": "やり直し",
          "value": "1 回だけ"
        },
        {
          "label": "その後",
          "value": "止まって知らせる"
        }
      ],
      "cards": [
        {
          "title": "何を確かめるのか",
          "lines": [
            "ファイルがちゃんと変わったか",
            "エラーが出ていないか",
            "頼んだことができているか"
          ]
        },
        {
          "title": "だめだったときは",
          "lines": [
            "確認の結果をふまえて、もう一度やり直す",
            "やり直しは 1 回だけ",
            "それでもだめなら、その場で止まる"
          ]
        },
        {
          "title": "うれしいポイント",
          "lines": [
            "動いたつもりで終わることがない",
            "小さなつまずきは自分で立て直す",
            "止まったことはすぐ分かる"
          ]
        }
      ],
      "facts": [
        "『操作検証』を付けた明細は、AI が /task_check_okng へ報告した状態を確認する。",
        "書き込みなし・エラーのいずれかなら、検証結果を踏まえて 1 回だけ自動リトライする。",
        "終了明細は操作検証が false（どの明細もファイル操作なし）なら AI を介さず終了完了、true なら最終検証を依頼する。",
        "実行回数の上限は 3 回で、実行サイクルごとにリセットされる。"
      ],
      "evidence": [
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "『操作検証』を付けた明細は、AI が /task_check_okng へ報告した状態を確認し、書き込みなし・エラーのいずれかなら検証結果を踏まえて 1 回だけ自動リトライする。"
        },
        {
          "source": "backend_taskteam/task_proc/tasks_watcher.py",
          "text": "実行回数上限は 3 回（サイクル毎）。"
        }
      ],
      "image_prompt": "Clean widescreen illustration: a gentle glowing helper checking a finished document with a magnifier, a small circular arrow beside it suggesting one retry, calm and trustworthy mood, no text in the image.",
      "short_narration": "作業のあとに結果を確かめて、だめならもう一度だけやり直します。",
      "long_narration": "AI に任せるとき、いちばん気になるのは、ちゃんとできたのかどうかですよね。AIタスクには、そのための仕組みがあります。手順には、確認するかどうかの印を付けられます。印を付けた手順は、作業が終わったあとに、結果を確かめます。ファイルがちゃんと変わったか。エラーが出ていないか。頼んだことができているか。もし、何も変わっていなかったり、エラーが出ていたら、そのときは、もう一度だけやり直します。何度もくり返して、おかしなことになっていくのを防ぐため、やり直しは 1 回だけです。それでもだめなときは、その場で止まって知らせてくれます。動いたつもりで終わっていた、ということがない。だから、安心して任せられます。",
      "short_audio": "audio/short_scene_008.mp3",
      "long_audio": "audio/long_scene_008.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 3.768,
      "long_start_sec": 0.0,
      "long_duration_sec": 38.832
    },
    {
      "id": "scene_009",
      "title": "控えを取る、続きから直す",
      "expression": "neutral",
      "accent": "#b79bff",
      "accent_soft": "rgba(183, 155, 255, 0.18)",
      "kicker": "STEP 9 — 安心の備え",
      "headline": "始める前に控えを取り、\n止まっても\n続きから再開できます",
      "lead": "いちばん最初の手順で、もとのファイルの控えを取ります。もし途中でうまくいかなくても、赤い表示で止まって知らせるだけ。直したあとは、終わったところの続きから再開できます。",
      "subtitle": "気づかないうちに壊れていた、ということが起きない作りです。",
      "image": "images/scene_009.png",
      "chips": [
        "始める前に控えを取る",
        "止まって知らせる",
        "続きから再開できる",
        "終わった手順はそのまま"
      ],
      "metrics": [
        {
          "label": "控え",
          "value": "最初の手順で自動"
        },
        {
          "label": "失敗時",
          "value": "止まって知らせる"
        },
        {
          "label": "再開",
          "value": "続きから"
        }
      ],
      "cards": [
        {
          "title": "始める前に",
          "lines": [
            "もとのファイルの控えを自動で取る",
            "変わったところだけを記録する",
            "あとから見比べられる"
          ]
        },
        {
          "title": "止まったときは",
          "lines": [
            "その手順が赤い表示になる",
            "何が起きたかが画面に残る",
            "後ろの手順は動かず待っている"
          ]
        },
        {
          "title": "直したあとは",
          "lines": [
            "実行のスイッチを入れ直す",
            "終わった手順はそのまま",
            "止まったところの続きから走る"
          ]
        }
      ],
      "facts": [
        "開始明細は AI を使わず aidiy_backup MCP でプロジェクトの差分バックアップを取る。",
        "エラー時は明細と要求を 状態＝エラー・実行有効オフで止める（明細失敗・タイムアウト・PID全クリアとも同じ扱い）。",
        "明細の実行有効を戻すと、その明細と親要求がエラーなら待機へ戻り、実行回数もリセットされる。",
        "要求の実行有効も戻すと、完了済みの明細を飛ばして該当箇所から再実行される。"
      ],
      "evidence": [
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "開始明細は AI を使わず aidiy_backup MCP でプロジェクトの差分バックアップを取る。"
        },
        {
          "source": "backend_taskteam/task_proc/tasks_db.py",
          "text": "無効 → 有効 への切替時は、エラーで止まっている要求・明細を 待機 に戻して再実行できるようにする。明細は PID・開始日時・終了日時・実行回数もリセットする。"
        }
      ],
      "image_prompt": "Reassuring widescreen illustration: a soft glowing shield beside a stack of documents with one copy safely tucked away, and a gentle path resuming from a marked point, warm and calm mood, no text in the image.",
      "short_narration": "始める前に控えを取り、止まっても続きから再開できます。",
      "long_narration": "任せるとなると、心配なのは失敗したときですよね。そこはきちんと守られています。まず、いちばん最初の手順で、もとのファイルの控えを取ります。変わったところだけを記録しておくので、あとから見比べられます。そして、もし途中でうまくいかなかったら。その手順は赤い表示になって、そこで止まります。後ろに続く手順は、動かずに待っています。おかしなまま先へ進んでしまうことはありません。何が起きたかは画面に残るので、落ち着いて確かめられます。直したあとは、実行のスイッチを入れ直すだけ。すでに終わった手順はそのままで、止まったところの続きから走ります。はじめからやり直しにはなりません。気づかないうちに壊れていた、ということが起きない作りです。",
      "short_audio": "audio/short_scene_009.mp3",
      "long_audio": "audio/long_scene_009.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 3.84,
      "long_start_sec": 0.0,
      "long_duration_sec": 40.176
    },
    {
      "id": "scene_010",
      "title": "こんな使い方もできます",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125, 255, 179, 0.18)",
      "kicker": "EXAMPLE — こんな使い方も",
      "headline": "ニュースを集めて動画のページまで。\n10 数ステップで実現できます",
      "lead": "たとえば、決まった時刻に最新の AI ニュースを集めて、解説動画のページを作る。そんな流れも、10 数ステップに分ければ AI に任せられます。この紹介動画も、AiDiy の同じ仕組みで作られました。",
      "subtitle": "まずは、毎日くり返している小さな作業を 1 つ選んでみてください。",
      "image": "images/scene_010.png",
      "chips": [
        "決まった時刻に自動で",
        "10 数ステップに分ける",
        "人が触らずに完走",
        "この動画も同じ仕組み"
      ],
      "metrics": [
        {
          "label": "手順の数",
          "value": "10 数ステップ"
        },
        {
          "label": "動かし方",
          "value": "決まった時刻に"
        },
        {
          "label": "人が触る回数",
          "value": "0 回"
        }
      ],
      "cards": [
        {
          "title": "こんな流れが作れます",
          "lines": [
            "最新の AI ニュースを集める",
            "台本を作り、ページと画像と音声を作る",
            "仕上がりを確認して、完成を知らせる"
          ]
        },
        {
          "title": "他にもこんな使い方",
          "lines": [
            "毎朝、決まった資料を集めて整える",
            "週に一度、記録をまとめて保存する",
            "資料が届いたら、決まった形に変換する"
          ]
        },
        {
          "title": "はじめの一歩",
          "lines": [
            "毎日くり返している作業を 1 つ選ぶ",
            "それを日本語で書いて登録してみる",
            "うまくいったら、時刻を決めて任せる"
          ]
        }
      ],
      "facts": [
        "定時実行と 10 数ステップの明細を組み合わせれば、ニュース収集から解説動画 HTML の生成までを自動化できる。",
        "ビデオページ生成は Step00 初期確認から Step99 完成案内までのステップ構成で組み立てる。",
        "この紹介動画自体も AiDiy のビデオページ生成機能で自動生成されている。"
      ],
      "evidence": [
        {
          "source": "backend_tools/aidiy_automations/ビデオページ生成/",
          "text": "ビデオページ生成は Step00 初期確認 → Step01 フォルダ作成 → Step02 シナリオ作成 → Step03 HTML 修正 → Step04 画像生成 → Step05 中間確認 → Step06 音声生成 → Step07 再生時間更新 → Step08 最終確認 → Step99 完成案内 の流れで構成する。"
        }
      ],
      "image_prompt": "Warm widescreen illustration: a laptop on a calm desk quietly assembling a finished article page by itself, small floating icons for news, script, image and sound flowing into it, gentle daylight, reassuring mood, no text in the image.",
      "short_narration": "決まった時刻にニュースを集めて動画のページを作る。そんな流れも実現できます。",
      "long_narration": "では、こんな使い方はどうでしょう。決まった時刻になったら、最新の AI ニュースを集める。台本を作り、ページと画像と音声をそろえて、動画のページとして仕上げる。この流れも、10 数ステップに分けておけば、人がひとつも触らずに走らせられます。じつは、いまご覧いただいているこの動画も、AiDiy の同じ仕組みで作られました。もちろん、もっと小さなことからで大丈夫です。毎朝、決まった資料を集めて整える。週に一度、記録をまとめて保存する。まずは、毎日くり返している作業を 1 つだけ選んで、日本語で書いてみてください。",
      "short_audio": "audio/short_scene_010.mp3",
      "long_audio": "audio/long_scene_010.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 4.872,
      "long_start_sec": 0.0,
      "long_duration_sec": 34.368
    },
    {
      "id": "scene_999",
      "title": "まとめ",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.2)",
      "kicker": "SUMMARY",
      "headline": "書くだけで、あとはお任せ。\n決めた時刻に、AI が動きます",
      "lead": "やってほしいことを日本語で書く。AI が手順に分ける。順番どおりに進む。決めた時刻に自分から始まる。毎日くり返していたあの作業を、AIタスクに任せてみませんか。",
      "subtitle": "日本語で書くだけ。あとは AI があなたの代わりに動きます。",
      "image": "images/scene_999.png",
      "chips": [
        "日本語で書くだけ",
        "手順は AI が考える",
        "順番どおりに進む",
        "決めた時刻に自分から"
      ],
      "metrics": [
        {
          "label": "覚えること",
          "value": "書くだけ"
        },
        {
          "label": "任せられること",
          "value": "毎日のくり返し"
        },
        {
          "label": "この動画",
          "value": "AiDiy が自動生成"
        }
      ],
      "cards": [
        {
          "title": "AIタスクでできること",
          "lines": [
            "日本語のお願いから、AI が手順を作る",
            "順番を守り、同時にできるものは同時に進む",
            "毎日・毎週・毎月の決まった時刻に自分から動く"
          ]
        },
        {
          "title": "はじめの一歩",
          "lines": [
            "毎日くり返している作業を 1 つ選ぶ",
            "それを日本語で書いて登録してみる",
            "うまくいったら、時刻を決めて任せる"
          ]
        }
      ],
      "facts": [
        "AIタスクは日本語の要求から AI が明細を自動生成し、依存を判断して実行する。",
        "定時実行・間隔実行・フォルダ変化で、人が居なくても繰り返し自動実行できる。",
        "この紹介動画自体も AiDiy のビデオページ生成機能で自動生成されている。"
      ],
      "evidence": [],
      "image_prompt": "Bright, uplifting widescreen closing illustration: a person leaving a tidy desk while a soft glowing AI light keeps working gently in the background, sunrise gradient, hopeful and warm, no text in the image.",
      "short_narration": "この動画は AiDiy が自動で作りました。チャンネル登録をお願いします。あなたの毎日の作業も、AI に任せてみませんか。",
      "long_narration": "最後にまとめます。AiDiy の AIタスクは、やってほしいことを日本語で書くだけで使えます。AI が手順に分けて、順番どおりに進めてくれます。待たなくてよいものは、同時に片づけてくれます。作業のあとには、ちゃんとできたかを確かめて、だめならやり直してくれます。そして、決めた時刻になれば、AI が自分から動き出します。朝の情報集め、夜の記録づくり、届いた資料の整理。毎日くり返しているあの作業を、1 つだけ選んで、任せてみてください。ご紹介したこの動画も、AiDiy のビデオページ生成機能で自動生成されました。台本づくりから画像、音声、ページの組み立てまで、すべて自動です。チャンネル登録を、ぜひお願いします。AiDiy で、あなたの毎日を、もう少し軽くしてみませんか。",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 7.656,
      "long_start_sec": 0.0,
      "long_duration_sec": 48.552
    }
  ],
  "total_short_duration_sec": 56.016,
  "total_long_duration_sec": 497.04
};
