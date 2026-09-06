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
    "image_source_note": "scene_003 / scene_004 / scene_006 / scene_011 は ../sozai/ の実画面スクリーンショットを images/scene_NNN.png へコピーして使用（AI 画像生成はスキップされる）。"
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
      "title": "AI が手順と進み方を考える",
      "expression": "neutral",
      "accent": "#ffc46b",
      "accent_soft": "rgba(255, 196, 107, 0.18)",
      "kicker": "STEP 3 — 手順と進み方を設計",
      "headline": "1 つのお願いから\n作業・判断・合流まで\nAI が組み立てます",
      "lead": "登録すると、AI がお願いの中身を読んで、必要な手順を書き出します。ただ並べるだけではありません。どれを順番に、どれを同時に、どこで条件によって道を分けるか。進み方そのものを設計します。",
      "subtitle": "一本道に並べるだけではなく、条件に合わせて進み方そのものを設計します。",
      "image": "images/scene_003.png",
      "chips": [
        "お願いは 1 つ",
        "手順は自動で書き出し",
        "順番・同時・分岐まで設計",
        "進み具合が見える"
      ],
      "metrics": [
        {
          "label": "入力",
          "value": "日本語のお願い"
        },
        {
          "label": "AI が設計",
          "value": "作業＋進み方"
        },
        {
          "label": "条件があれば",
          "value": "分岐も作成"
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
          "title": "AI が設計すること",
          "lines": [
            "必要な手順を書き出す",
            "順番と、同時に進めるところを決める",
            "条件で道が分かれるところを置く"
          ]
        },
        {
          "title": "状態の見方",
          "lines": [
            "待機 … 順番を待っているところ",
            "実行中 … いま動いているところ",
            "完了 … 終わったところ",
            "パス … 分かれ道で選ばれなかったところ"
          ]
        }
      ],
      "facts": [
        "要求を『準備開始』で登録すると Task 起動監視（5 秒間隔）が『準備中』へ進め、task_sub/sub_init.py を起動する。",
        "AI が要求を明細へ分解し、各明細に start / do / if / or / end のタイプを付けて本登録する。0=start と 9999=end は SEQ で確定し、その間を AI が do / if / or から選ぶ。",
        "進み方は先行SEQ（カンマ区切りで複数指定可）による DAG で表し、if の後続には =Y / =N を付けて条件分岐を表現する。",
        "明細の状態は 待機 / 実行中 / 完了 / エラー / 中止 / パス で、PID・開始日時・実行回数とともに画面に出る。"
      ],
      "evidence": [
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "Task 起動監視が要求を準備中へ進め task_sub/sub_init.py を起動する。AI が要求を明細へ分解し、開始行・処理行・終了行を本登録する。"
        },
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "Aタスク明細 の タイプ は start / do / if / or / end の5値。0=start、9999=end は SEQ で確定し、その間は AI（または明細編集ダイアログ）が do（通常実行）/ if（Y・N 判定の分岐）/ or（合流点）から選ぶ。"
        },
        {
          "source": "backend_taskteam/task_proc/tasks_db.py",
          "text": "明細状態値 = (待機, 実行中, 完了, エラー, 中止, パス)。パス は if 分岐で選ばれなかった枝（失敗ではない）。"
        }
      ],
      "image_prompt": "(実画面を使用) sozai/web_AIタスク_動画作成.png",
      "short_narration": "AI は作業だけでなく、条件分岐と合流も組み立てます。",
      "long_narration": "登録が終わると、AI がすぐに動きはじめます。お願いの中身を読んで、必要な手順を自動で書き出してくれます。いま画面に出ているのが、その結果です。画面は 3 つに分かれています。左が、受け付けたお願いの一覧。まん中が、手順のつながりを描いた流れ図。右が、分かれた手順の一覧です。ここで見てほしいのは、AI がやっているのは、手順を書き出すことだけではない、というところです。書き出した手順を、どういう順番で進めるか。どれとどれなら同時に進めてよいか。そして、そのときの状況によって道を分けるべきところはどこか。進み方そのものを、AI が設計します。だから、いつも同じ一本道をたどるだけの流れにはなりません。それぞれの手順には、いまの状態も出ます。順番を待っているのか、動いているのか、終わったのか。ひと目で分かります。このあと、手順ひとつひとつの役割と、条件で道が分かれるしくみを、順に見ていきましょう。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 3.744,
      "long_start_sec": 0.0,
      "long_duration_sec": 66.288,
      "image_source": "sozai/web_AIタスク_動画作成.png"
    },
    {
      "id": "scene_004",
      "title": "手順には役割がある",
      "expression": "neutral",
      "accent": "#ff9ad5",
      "accent_soft": "rgba(255, 154, 213, 0.18)",
      "kicker": "STEP 4 — 明細の役割",
      "headline": "作業・判断・合流。\n役割と開始条件が\n1 行ずつ見えます",
      "lead": "明細には、通常作業の do、Y / N を決める if、分かれた道を戻す or という役割があります。どの明細が終わったら始めるかも指定され、内容はあとから人が直せます。",
      "subtitle": "AI が作った流れを、人が読んで確認・調整できるので、ブラックボックスになりません。",
      "image": "images/scene_004.png",
      "chips": [
        "do＝通常作業",
        "if＝Y / N 判断",
        "or＝合流",
        "あとから直せる"
      ],
      "metrics": [
        {
          "label": "明細タイプ",
          "value": "do / if / or"
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
          "title": "3 つの役割",
          "lines": [
            "do … 実際に作業する",
            "if … 条件を Y / N で判断する",
            "or … 選ばれた道を 1 本に戻す"
          ]
        },
        {
          "title": "人が手を入れられる",
          "lines": [
            "タイトルやお願いの文章を書き足す",
            "役割や前後のつながりを調整する",
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
        "AIタスク明細はタイプ（start / do / if / or / end）・タイトル・要求内容・先行SEQ・TASK_AI_NAME・TASK_AI_MODEL_do・操作検証・実行有効・状態を持つ。",
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
      "short_narration": "明細は、作業・判断・合流の 3 種類です。",
      "long_narration": "手順を 1 つ開いてみましょう。それぞれの明細には役割があります。do は実際に手を動かす通常の作業。if は条件を Y か N で判断する分岐。or は分かれた道を 1 本に戻す合流です。さらに、タイトル、AI へのお願いの文章、どの明細が終わったら始めるか、という指定が入っています。これらを書いたのは AI ですが、人が読んで直すこともできます。説明を書き足す、役割や前後のつながりを調整する、この明細だけ別の AI に任せる、一時的に外す、といった変更ができます。AI が作った流れを見える形で確認し、気になるところだけ直せるので、任せきりのブラックボックスにはなりません。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 3.456,
      "long_start_sec": 0.0,
      "long_duration_sec": 40.92,
      "image_source": "sozai/web_AIタスク_明細編集.png"
    },
    {
      "id": "scene_011",
      "title": "条件で進む道を選ぶ",
      "expression": "neutral",
      "accent": "#61e7a7",
      "accent_soft": "rgba(97, 231, 167, 0.18)",
      "kicker": "STEP 5 — 分岐判断",
      "headline": "条件を AI が Y / N で判断。\n選んだ道だけ進みます",
      "lead": "たとえば「資料があれば取り込み、なければ知らせる」。判断役の AI は条件を Y / N で答え、当てはまる側だけを実行します。選ばれなかった側は失敗ではなく、通らない道として扱います。",
      "subtitle": "条件確認を人に返さず、その場の結果に合わせてタスク自身が進み方を変えます。",
      "image": "images/scene_011.png",
      "chips": [
        "AI が条件を判定",
        "Y / N で枝分かれ",
        "選んだ側だけ実行",
        "最後は自動で合流"
      ],
      "metrics": [
        {
          "label": "判断結果",
          "value": "Y または N"
        },
        {
          "label": "実行する枝",
          "value": "選ばれた側だけ"
        },
        {
          "label": "合流処理",
          "value": "AI 不要で自動"
        }
      ],
      "cards": [
        {
          "title": "判断する — if",
          "lines": [
            "条件だけを AI に問いかける",
            "Y / N と理由を記録する",
            "判定中はファイルを変更しない"
          ]
        },
        {
          "title": "選んだ道を進む",
          "lines": [
            "Y なら Y 側、N なら N 側を実行",
            "選ばれない側は「パス」になる",
            "パスはエラーではない"
          ]
        },
        {
          "title": "1 本に戻す — or",
          "lines": [
            "通った側が終われば合流",
            "合流には AI を使わない",
            "その後の共通作業へ進む"
          ]
        }
      ],
      "facts": [
        "if 明細は条件を AI に Y / N で判定させ、応答内容へ判定と理由を記録する。判定だけを行い、ファイル操作はしない。",
        "if の後続は先行SEQへ =Y または =N を付け、選ばれなかった枝は状態『パス』として下流へ伝播する。",
        "パスは失敗ではなく要求の完了を妨げない。停止復旧時には待機へ戻して分岐をやり直せる。",
        "or 明細は AI を使わず、先行する枝のいずれか 1 本が完了すれば合流して次へ進む。"
      ],
      "evidence": [
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "if は要求内容を条件文として AI に Y / N で答えさせ、or は先行のいずれか 1 本が完了すれば機械的に合流する。"
        },
        {
          "source": "backend_taskteam/task_proc/tasks_db.py",
          "text": "if で選ばれなかった枝は状態『パス』として伝播し、失敗ではないため要求の完了を妨げない。"
        }
      ],
      "image_prompt": "(実画面を使用) sozai/web_AIタスク_画面報告.png",
      "short_narration": "AI が Y か N を選び、片方を実行します。",
      "long_narration": "ここが新しく加わった、分岐判断です。たとえば、資料があれば取り込み、なければ担当者へ知らせる、というお願いを考えてみましょう。判断を担当する if 明細は、いま資料があるかを AI に問い、Y か N と、その理由を記録します。この判断ではファイルを変更しません。Y なら取り込みの道、N ならお知らせの道というように、選ばれた側だけが実行されます。選ばれなかった側はエラーではなく、今回は通らない「パス」として淡く表示されます。そして、どちらかの道が終わると、or という合流明細が AI を使わずに 1 本の流れへ戻し、その後の共通作業へ進めます。途中で人に確認を返さなくても、その場の結果に合わせてタスク自身が進み方を選べるようになりました。",
      "short_audio": "audio/short_scene_011.mp3",
      "long_audio": "audio/long_scene_011.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 3.936,
      "long_start_sec": 0.0,
      "long_duration_sec": 45.6,
      "image_source": "sozai/web_AIタスク_画面報告.png"
    },
    {
      "id": "scene_005",
      "title": "順番と、同時に進むところ",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125, 255, 179, 0.18)",
      "kicker": "STEP 6 — 順番と並行",
      "headline": "待つものは待ち、\n待たなくていいものは\n同時に進みます",
      "lead": "手順のつながりは、まん中の流れ図で見られます。前の手順が終わるまで、次は静かに待ちます。待たなくてよいものは同時に走ります。条件で片方だけを選ぶ分岐とは別の、もうひとつの速さのしくみです。",
      "subtitle": "分かれ道は「どちらか片方」、並行は「どちらも同時」。全体像は流れ図で確かめられます。",
      "image": "images/scene_005.png",
      "chips": [
        "流れ図で見える",
        "待つものは待つ",
        "同時に進むものもある",
        "分岐とは別のしくみ"
      ],
      "metrics": [
        {
          "label": "見る場所",
          "value": "まん中の流れ図"
        },
        {
          "label": "同時に動く数",
          "value": "1 タスク最大 3"
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
          "title": "分岐と並行のちがい",
          "lines": [
            "分岐 … 条件でどちらか片方だけ通る",
            "並行 … 依存がなければどちらも同時に進む",
            "流れ図では似て見えるが別のしくみ"
          ]
        },
        {
          "title": "流れ図の見方",
          "lines": [
            "上から下へ、矢印でつながる",
            "同時に進むものは横に並ぶ",
            "いちばん長い道すじが下に出る"
          ]
        }
      ],
      "facts": [
        "明細の依存は先行SEQ（カンマ区切りで複数指定可）による DAG で定義する。",
        "先行SEQ がすべて完了した明細を実行可能とし、依存を満たした明細を並行起動する（or だけは先行のいずれか 1 本の完了で進む）。",
        "同時実行数は tasks_watcher.明細並行上限（既定 3）で制御する。上限を 1 にするとタスク単位の直列実行になり、タスクをまたぐ並行に制限はない。",
        "通知音などの軽量明細は code agent を使わないため上限の対象外で、依存が許せば常に同時起動する。",
        "フロー図は最長経路をクリティカルパスとして配置し、画面下部に表示する。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "明細の依存関係は先行SEQ（カンマ区切りで複数指定可）による DAG。直列だけでなく水平の並行分岐を含む自由なタスクフローを定義でき、画面のフロー図は最長経路をクリティカルパスとして配置する。"
        },
        {
          "source": "backend_taskteam/task_proc/tasks_watcher.py",
          "text": "明細並行上限 = 3。先行SEQ を満たした明細は、同一タスク内でもこの上限まで同時に起動する。"
        }
      ],
      "image_prompt": "Clean widescreen illustration of a flowing task diagram made of soft glowing nodes: one path splits into two parallel branches that both run at the same time and merge again, the longest route gently highlighted, bright and easy to read, no text in the image.",
      "short_narration": "待たない作業は、最大 3 件まで同時に進みます。",
      "long_narration": "手順は、ただ上から順に流れるだけではありません。それぞれの手順には、どれが終わったら始めるか、という指定が入っています。指定された手順が終わるまで、次の手順は静かに待ちます。そして、待たなくてよい手順は、同時に動き出します。だから、ぜんぶを一列に並べるよりも早く終わります。ここで、さっきの分かれ道との違いを、はっきりさせておきましょう。分かれ道は、条件によって、どちらか片方の道だけを通るしくみでした。いっぽう、いまお話ししている並行は、おたがいに関係のない手順を、どちらも同時に進めるしくみです。流れ図の上では似て見えますが、役割はまったくちがいます。同時に動かせる数は、ひとつのお願いにつき、みっつまでです。全体のつながりは、画面まん中の流れ図で確かめられます。上から下へ、矢印でつながっていきます。同時に進むものは、横に並んで表示されます。そして画面の下には、いちばん時間のかかる道すじが出ます。ここを見れば、全体でどれくらいかかりそうかが読めます。順番を人が見張る必要は、もうありません。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 3.264,
      "long_start_sec": 0.0,
      "long_duration_sec": 65.016
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
      "lead": "やってほしいことを日本語で書く。AI が作業と判断へ分け、条件に合わせて道を選ぶ。できるものは同時に進め、決めた時刻に自分から始まる。毎日の作業を AIタスクに任せてみませんか。",
      "subtitle": "日本語で書くだけ。あとは AI があなたの代わりに動きます。",
      "image": "images/scene_999.png",
      "chips": [
        "日本語で書くだけ",
        "手順は AI が考える",
        "条件で進み方を選ぶ",
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
            "日本語のお願いから、AI が作業と判断を作る",
            "条件で道を選び、同時にできるものは同時に進む",
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
        "AIタスクは日本語の要求から AI が明細を自動生成し、if の Y / N 判断、or の合流、依存関係を含む流れを実行する。",
        "定時実行・間隔実行・フォルダ変化で、人が居なくても繰り返し自動実行できる。",
        "この紹介動画自体も AiDiy のビデオページ生成機能で自動生成されている。"
      ],
      "evidence": [],
      "image_prompt": "Bright, uplifting widescreen closing illustration: a person leaving a tidy desk while a soft glowing AI light keeps working gently in the background, sunrise gradient, hopeful and warm, no text in the image.",
      "short_narration": "この動画は AiDiy が自動で作りました。チャンネル登録をお願いします。あなたの毎日の作業も、AI に任せてみませんか。",
      "long_narration": "最後にまとめます。AiDiy の AIタスクは、やってほしいことを日本語で書くだけで使えます。AI が通常の作業だけでなく、途中の判断と合流まで組み立てます。条件を Y か N で判断して選んだ道だけを進み、待たなくてよい作業は同時に片づけます。作業のあとには、ちゃんとできたかを確かめ、だめならやり直します。そして、決めた時刻になれば、AI が自分から動き出します。朝の情報集め、夜の記録づくり、届いた資料の整理。毎日くり返しているあの作業を、1 つだけ選んで、任せてみてください。ご紹介したこの動画も、AiDiy のビデオページ生成機能で自動生成されました。台本づくりから画像、音声、ページの組み立てまで、すべて自動です。チャンネル登録を、ぜひお願いします。AiDiy で、あなたの毎日を、もう少し軽くしてみませんか。",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 8.88,
      "long_start_sec": 0.0,
      "long_duration_sec": 44.88
    }
  ],
  "total_short_duration_sec": 59.904,
  "total_long_duration_sec": 591.456
};
