window.SCENARIO = {
  "project_name": "AiDiy紹介_AIチーム_ja",
  "version": "mcp",
  "title": "AiDiy AIチーム - AI の仲間が集まって相談し、経験を貯めながら仕事を進めます",
  "source": {
    "type": "agents_and_knowledge",
    "summary": "AiDiy の AIチーム機能を backend_taskteam/AGENTS.md（Team 機能）と frontend_web/src/components/AIチーム/ の現行実装に基づいて、初心者向けに紹介する。"
  },
  "target": {
    "language": "ja-JP",
    "format": "html_css_scene_player_with_media",
    "tone": "初心者向け、専門用語を避けたやさしい語り口、短い文、3D 空間の楽しさを伝える",
    "goal": "AI をまだ仕事に使ったことがない人が『AI の仲間が集まって働く様子』を思い浮かべられ、『これなら自分にも頼めそう』と思えること。"
  },
  "assets_policy": {
    "visual_style": "left_avatar_38_right_content_62",
    "audio_dir": "audio",
    "image_dir": "images",
    "avatar": "../_vrm/VRM_AiDiy.vrm",
    "tts_provider": "freeai:female",
    "image_source_note": "scene_001 / 002 / 004 / 007 / 008 / 010 は ../sozai/ の実画面スクリーンショットを images/scene_NNN.png へコピーして使用（AI 画像生成はスキップされる）。"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "AI の仲間が集まって働く場所",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.2)",
      "kicker": "INTRODUCTION",
      "headline": "AI の仲間たちが集まって、\n相談しながら\n仕事を進めてくれます",
      "lead": "AiDiy の AIチームは、AI のメンバーが集まった小さなチームです。得意分野のちがう仲間をそろえて、目標を決めて、お願いをする。あとはメンバーどうしで相談しながら進めてくれます。",
      "subtitle": "仲間を呼ぶ → 目標を決める → お願いする → 得意な人が動く → 経験が貯まる。",
      "image": "images/scene_000.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "image_prompt": "Warm, friendly widescreen illustration of a small team of gentle glowing AI companions gathered in a sunny park-like space, talking together around a board, soft green grass and blue sky, welcoming and hopeful mood, no text in the image.",
      "short_narration": "AI の仲間が集まったチームです。相談しながら、あなたの仕事を進めてくれます。",
      "long_narration": "この動画は、AiDiy のビデオページ生成機能で自動生成されました。台本づくりから画像、音声まで、すべて AI が作っています。さて、ひとりで仕事をしていると、こんなことはありませんか。相談する相手がいない。いくつか案を出して比べたいけれど、手が回らない。AiDiy の AIチームは、そんなときに使えます。AI のメンバーが集まった、小さなチームです。得意分野のちがう仲間をそろえて、チームの目標を決めて、お願いをする。あとは、メンバーどうしで相談しながら、仕事を進めてくれます。しかも、やった仕事は経験として貯まっていきます。使うほどに、チームが育っていくのです。この動画では、実際の画面を見ながら、その様子をやさしく紹介します。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 5.4,
      "long_start_sec": 0.0,
      "long_duration_sec": 41.064,
      "layout": "hero",
      "hero_image_focus": true,
      "background_word": ""
    },
    {
      "id": "scene_001",
      "title": "仲間を呼ぶ",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125, 255, 179, 0.18)",
      "kicker": "STEP 1 — 仲間を呼ぶ",
      "headline": "歴史に名を残した人たちを\nチームに呼べます",
      "lead": "召喚のボタンを押すと、一覧が開きます。数学、哲学、音楽、政治、医学。それぞれ得意分野を持った顔ぶれから選んで、チームに加わってもらえます。",
      "subtitle": "得意分野のちがう仲間をそろえるほど、話し合いの幅が広がります。",
      "image": "images/scene_001.png",
      "chips": [
        "一覧から選ぶだけ",
        "得意分野つき",
        "何人でも呼べる",
        "管理者役は最初からいる"
      ],
      "metrics": [
        {
          "label": "呼び方",
          "value": "選んで押すだけ"
        },
        {
          "label": "顔ぶれ",
          "value": "得意分野つき"
        },
        {
          "label": "チーム管理者",
          "value": "最初からいる"
        }
      ],
      "cards": [
        {
          "title": "こんな顔ぶれがいます",
          "lines": [
            "数学やコンピューターが得意な人",
            "哲学や倫理を考えるのが得意な人",
            "音楽、政治、医学が得意な人"
          ]
        },
        {
          "title": "呼び方はかんたん",
          "lines": [
            "召喚のボタンを押して一覧を開く",
            "名前と得意分野を見て選ぶ",
            "この要員を召喚、を押すだけ"
          ]
        },
        {
          "title": "うれしいポイント",
          "lines": [
            "考え方のちがう仲間がそろう",
            "ひとりでは出てこない案が出る",
            "あとから増やしても減らしてもよい"
          ]
        }
      ],
      "facts": [
        "Aチーム要員は要員ID・表示名・役割・人格情報・有効状態を持つ。初期要員 admin は削除できない。",
        "要員は persona ディレクトリから召喚して追加できる（POST /team/エージェント/召喚、/team/召喚要員/一覧）。",
        "要員の保守は POST /team/要員/一覧・取得・登録・変更・削除。"
      ],
      "evidence": [
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "Aチーム要員: 要員ID、表示名、役割、人格情報、有効状態。初期要員 admin は削除不可。"
        },
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "POST /team/エージェント/一覧 / 召喚 / 状態変更 / 排除 — インメモリ状態、persona 召喚、単発調査会話。"
        }
      ],
      "image_prompt": "(実画面を使用) sozai/web_AIチーム_要員召喚.png",
      "short_narration": "得意分野のちがう仲間を、一覧から選んで呼びます。",
      "long_narration": "まずは、仲間を呼ぶところから始めましょう。画面の召喚ボタンを押すと、一覧が開きます。並んでいるのは、歴史に名を残した人たちです。数学やコンピューターが得意な人。哲学を考えるのが得意な人。音楽、政治、医学。名前のとなりに、その人の得意分野が書かれています。気になる名前を選んで、この要員を召喚、を押すだけ。それでチームに加わってくれます。何人呼んでもかまいません。考え方のちがう仲間がそろうほど、話し合いの幅は広がります。ひとりでは思いつかなかった案が出てくる。それが、チームで進めるいちばんの楽しさです。なお、チームをまとめる管理者役は、最初から用意されています。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 3.6,
      "long_start_sec": 0.0,
      "long_duration_sec": 40.056,
      "image_source": "sozai/web_AIチーム_要員召喚.png"
    },
    {
      "id": "scene_002",
      "title": "チームをのぞいてみる",
      "expression": "neutral",
      "accent": "#ffc46b",
      "accent_soft": "rgba(255, 196, 107, 0.18)",
      "kicker": "STEP 2 — チームをのぞく",
      "headline": "公園のような空間で、\n仲間たちが話し合っています",
      "lead": "AIチームの画面は 3D の空間です。呼んだ仲間がその場に立ち、吹き出しで話し合っています。ドラッグで見回せて、ホイールで近づけます。左が仲間の様子、右がお願いと経験の記録です。",
      "subtitle": "いま誰が何をしているか。画面を見るだけで分かります。",
      "image": "images/scene_002.png",
      "chips": [
        "3D の空間",
        "吹き出しで会話",
        "左＝仲間の様子",
        "右＝お願いと経験"
      ],
      "metrics": [
        {
          "label": "見え方",
          "value": "3D の空間"
        },
        {
          "label": "操作",
          "value": "ドラッグで見回す"
        },
        {
          "label": "分かること",
          "value": "誰が何をしているか"
        }
      ],
      "cards": [
        {
          "title": "画面の見方",
          "lines": [
            "左 … 仲間の一覧と、いまの様子",
            "右上 … お願いした仕事の一覧",
            "右下 … 終わった仕事と、貯まった経験"
          ]
        },
        {
          "title": "空間の中では",
          "lines": [
            "呼んだ仲間がその場に立っている",
            "吹き出しで意見を交わしている",
            "奥の掲示板にチームの目標が出る"
          ]
        },
        {
          "title": "うれしいポイント",
          "lines": [
            "進み具合をひと目で確認できる",
            "誰が手が空いているか分かる",
            "見ているだけでも楽しい"
          ]
        }
      ],
      "facts": [
        "チーム空間は 3D 表示で、ドラッグで 360 度回転、ホイールでズームできる。",
        "左パネルに要員ごとの状態（雑談中・実行・まとめ）、右上に依頼状況、右下に経験状況と経験値の合計を表示する。",
        "Aチーム状況テーブルが要員ごとの待機・実行・まとめ中・完了・エラーを集計する。",
        "奥の掲示板には最終更新の Aチーム目標が表示される。"
      ],
      "evidence": [
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "Aチーム状況: 要員ごとの待機・実行・まとめ中・完了・エラー集計。"
        },
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "POST /team/状況/一覧 / 最大更新日時 — 要員別のタスク集計。"
        }
      ],
      "image_prompt": "(実画面を使用) sozai/web_AIチーム.png",
      "short_narration": "公園のような空間で、仲間たちが話し合っています。",
      "long_narration": "では、チームをのぞいてみましょう。AIチームの画面は、公園のような 3D の空間です。呼んだ仲間が、その場に立っています。近づいてみると、吹き出しで話し合っているのが分かります。この実装、もう少し軽くできそう。さっきの発見、共有しておいたよ。そんな具合です。画面はドラッグで見回せます。ホイールを回すと、近づいたり離れたりできます。左側には、仲間の一覧と、いまの様子が出ます。誰が話し合っていて、誰が作業しているか。ひと目で分かります。右上には、お願いした仕事の一覧。右下には、終わった仕事と、貯まった経験が出ます。奥の掲示板に書かれているのは、チームの目標です。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 3.672,
      "long_start_sec": 0.0,
      "long_duration_sec": 43.464,
      "image_source": "sozai/web_AIチーム.png"
    },
    {
      "id": "scene_003",
      "title": "仲間に直接きいてみる",
      "expression": "neutral",
      "accent": "#b79bff",
      "accent_soft": "rgba(183, 155, 255, 0.18)",
      "kicker": "STEP 3 — その場できく",
      "headline": "気になることは、\nその場で仲間に\nきけます",
      "lead": "仲間を選んで話しかけると、その場で調べて答えてくれます。このときは読むだけ。ファイルを勝手に書きかえることはありません。まず相談してみたい、というときに使えます。",
      "subtitle": "頼む前にちょっと相談。読むだけなので安心してきけます。",
      "image": "images/scene_003.png",
      "chips": [
        "選んで話しかける",
        "調べて答えてくれる",
        "読むだけ・変更なし",
        "頼む前の相談に"
      ],
      "metrics": [
        {
          "label": "使い方",
          "value": "選んで話しかける"
        },
        {
          "label": "できること",
          "value": "調べて答える"
        },
        {
          "label": "安全",
          "value": "読むだけ"
        }
      ],
      "cards": [
        {
          "title": "こんなときに",
          "lines": [
            "いきなり頼むのは不安なとき",
            "今どうなっているか知りたいとき",
            "案を出す前に下調べしたいとき"
          ]
        },
        {
          "title": "安心なところ",
          "lines": [
            "このときは読むだけで動く",
            "ファイルは書きかえない",
            "答えを見てから、頼むか決められる"
          ]
        },
        {
          "title": "うれしいポイント",
          "lines": [
            "相談相手がいつでもいる",
            "得意な仲間を選んできける",
            "答えを待つ時間も画面で分かる"
          ]
        }
      ],
      "facts": [
        "単発会話は team_proc/team_chat.py が aidiy_code_agents の HTTP API を毎回呼ぶ。会話履歴は Team 側に保持しない。",
        "調査モードは code_permissions を既定（auto）に戻してツールを使わせ、システム指示で『読み取り調査のみ・変更禁止』を明示する。",
        "調査モードは CodeAgent 300 秒 / HTTP 360 秒。フロントエンドの最大待機秒 360 と揃えている。",
        "取りまとめなど追加調査が不要な用途は通常モード（code_permissions=none、ツール禁止）で動く。"
      ],
      "evidence": [
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "調査モード: 利用者画面の会話（/team/エージェント/会話）、雑談の発言。code_permissions を既定（auto）に戻してツールを使わせる。システム指示で「読み取り調査のみ・変更禁止」を明示する。"
        },
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "調査モードの HTTP 360秒は、フロントエンド AIチーム_会話要求.vue の 最大待機秒 = 360 と揃えています。"
        }
      ],
      "image_prompt": "Friendly widescreen illustration: a person having a calm conversation with a gentle glowing AI companion in a sunny park, a soft speech bubble with a magnifying glass symbol suggesting looking things up, reassuring and light mood, no text in the image.",
      "short_narration": "気になることは、その場で仲間にきけます。調べて答えてくれます。",
      "long_narration": "仕事を頼む前に、ちょっと相談したいときもありますよね。そんなときは、仲間を選んで話しかけてみてください。その場で調べて、答えを返してくれます。たとえば、いまこの画面はどうなっているのか。この作りで問題はないか。そんな質問です。このとき仲間がするのは、読んで調べることだけです。ファイルを勝手に書きかえることはありません。ですから、気軽にきいて大丈夫です。答えを見てから、あらためて仕事として頼むかどうかを決められます。得意分野のちがう仲間に、同じことをきいてみるのもおもしろいですよ。返ってくる答えが、少しずつちがいます。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 4.128,
      "long_start_sec": 0.0,
      "long_duration_sec": 35.232
    },
    {
      "id": "scene_004",
      "title": "チームの目標を決める",
      "expression": "neutral",
      "accent": "#ff9ad5",
      "accent_soft": "rgba(255, 154, 213, 0.18)",
      "kicker": "STEP 4 — 目標を決める",
      "headline": "目標を 1 行書くと、\n空間の掲示板に\n貼り出されます",
      "lead": "チーム目標には、めざす方向を 1 行で書きます。書いた目標は空間の奥の掲示板に貼り出され、仲間たちはそれを見ながら意見を出します。プロジェクトごとに 1 つ持てます。",
      "subtitle": "細かい指示はいりません。向かう方向だけ決めてあげてください。",
      "image": "images/scene_004.png",
      "chips": [
        "目標は 1 行",
        "掲示板に貼り出される",
        "プロジェクトごとに 1 つ",
        "自動で話し合うスイッチ"
      ],
      "metrics": [
        {
          "label": "書くこと",
          "value": "目標を 1 行"
        },
        {
          "label": "貼り出し先",
          "value": "空間の掲示板"
        },
        {
          "label": "単位",
          "value": "プロジェクトごと"
        }
      ],
      "cards": [
        {
          "title": "目標の書き方",
          "lines": [
            "めざす方向を 1 行で書く",
            "たとえば、学んでより良いものを作る",
            "細かい手順は書かなくてよい"
          ]
        },
        {
          "title": "書いたあとは",
          "lines": [
            "空間の奥の掲示板に貼り出される",
            "仲間たちが目標を見て意見を出す",
            "自動で話し合わせるスイッチもある"
          ]
        },
        {
          "title": "うれしいポイント",
          "lines": [
            "やることを一から指示しなくてよい",
            "チームの向きがそろう",
            "いつでも書きかえられる"
          ]
        }
      ],
      "facts": [
        "Aチーム目標はプロジェクト単位で、チーム目標・自動作業設定・チーム作業・作業ループ設定を持つ。",
        "CODE_BASE_PATH ごとに 1 件で、同じパスを保存すると上書きされる。",
        "最新の目標がチーム空間の掲示板に表示される。",
        "目標の保守は POST /team/目標/一覧・最終・取得・保存・削除。"
      ],
      "evidence": [
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "Aチーム目標: プロジェクト単位のチーム目標、自動作業設定、チーム作業、作業ループ設定。"
        },
        {
          "source": "frontend_web AIチーム目標保守画面",
          "text": "CODE_BASE_PATH ごとに 1 件です。同じパスを保存すると上書きされ、更新日時が最新の目標がチーム空間の掲示板に表示されます。"
        }
      ],
      "image_prompt": "(実画面を使用) sozai/web_AIチーム_目標編集.png",
      "short_narration": "チームの目標を 1 行書くと、掲示板に貼り出されます。",
      "long_narration": "つぎは、チームの目標です。むずかしく考える必要はありません。めざす方向を、1 行書くだけです。たとえば、成功と失敗から学んで、今より良いものを作る。それくらいで十分です。書いた目標は、さきほどの空間の、奥の掲示板に貼り出されます。仲間たちは、その掲示板を見ながら意見を出します。だから、細かい手順まで書く必要はありません。向かう方向だけ決めてあげれば、あとは仲間たちが考えてくれます。目標は、プロジェクトごとに 1 つ持てます。気が変わったら、いつでも書きかえて大丈夫です。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 3.648,
      "long_start_sec": 0.0,
      "long_duration_sec": 33.096,
      "image_source": "sozai/web_AIチーム_目標編集.png"
    },
    {
      "id": "scene_005",
      "title": "仲間どうしで話し合う",
      "expression": "neutral",
      "accent": "#ffe066",
      "accent_soft": "rgba(255, 224, 102, 0.18)",
      "kicker": "STEP 5 — 話し合い",
      "headline": "順番に意見を出して、\nまとまったら\nやることが決まります",
      "lead": "自動で話し合うスイッチを入れると、仲間が順番に「いまやるべきこと」を 1 つずつ発言します。半分以上の意見が集まると、管理者役がそれをまとめて、チームの作業として決めてくれます。",
      "subtitle": "人が議題を出さなくても、仲間たちの意見からやることが決まります。",
      "image": "images/scene_005.png",
      "chips": [
        "順番に 1 人ずつ発言",
        "半分以上で取りまとめ",
        "管理者役がまとめる",
        "決まったら作業になる"
      ],
      "metrics": [
        {
          "label": "発言",
          "value": "1 人ずつ順番に"
        },
        {
          "label": "まとめる条件",
          "value": "半分以上の意見"
        },
        {
          "label": "まとめ役",
          "value": "管理者"
        }
      ],
      "cards": [
        {
          "title": "話し合いの進み方",
          "lines": [
            "仲間が 1 人ずつ、今やるべきことを言う",
            "他の人の発言も見たうえで発言する",
            "意見は空間の吹き出しに出る"
          ]
        },
        {
          "title": "まとまるとき",
          "lines": [
            "半分以上の仲間の意見が集まったら",
            "管理者役がひとつにまとめる",
            "まとめた内容がチームの作業になる"
          ]
        },
        {
          "title": "うれしいポイント",
          "lines": [
            "議題を人が出さなくてよい",
            "いろんな視点の意見が並ぶ",
            "止めたいときはスイッチひとつ"
          ]
        }
      ],
      "facts": [
        "自動作業設定がオンのとき、Team 状態監視の毎分ゲートで話し合いを回す。",
        "分の下一桁が 1〜9 のときは sub_self_talk.py が雑談エリアの要員 1 名を選び、チーム目標・他要員の最新発言・自身の 1 回前の発言を渡して『今やるべきこと』を 1 件発言させる。",
        "分の下一桁が 0 のときは sub_self_work.py が、有効要員数の 50% 以上の意見が集まっていれば admin 人格でチーム作業へ取りまとめる。",
        "雑談は前回プロセスが動いている間は次を投入しない（直列化）。"
      ],
      "evidence": [
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "1〜9: sub_self_talk.py — 雑談エリアの要員から1名を選び、チーム目標・他要員の最新発言・その要員自身の1回前の発言を渡して「今やるべきこと」を1件発言させる。意見を集めるだけで実行はしない。"
        },
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "0: sub_self_work.py — 有効要員数の50%以上の意見が集まっていれば、admin 人格でチーム作業へ取りまとめる。"
        }
      ],
      "image_prompt": "Warm widescreen illustration: several gentle glowing AI companions sitting in a circle in a sunny park exchanging soft speech bubbles, one slightly larger figure gathering the bubbles into a single note, collaborative and cheerful mood, no text in the image.",
      "short_narration": "仲間が順番に意見を出し、まとまったらやることが決まります。",
      "long_narration": "目標を決めたら、自動で話し合うスイッチを入れてみましょう。ここからが、チームらしいところです。仲間たちが、順番に発言をはじめます。ひとりずつ、いま やるべきことを 1 つだけ言います。そのとき、他の仲間が何を言ったか、自分が前に何を言ったかも見たうえで考えます。だから、話がつながっていきます。意見は、空間の吹き出しに出ます。のぞきに行くと、みんなが何を考えているかが分かります。そして、半分以上の仲間の意見が集まると、管理者役が動きます。ばらばらの意見をひとつにまとめて、チームの作業として決めてくれるのです。議題を人が出さなくても、やることが決まっていく。これが AIチームのおもしろいところです。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 4.2,
      "long_start_sec": 0.0,
      "long_duration_sec": 43.2
    },
    {
      "id": "scene_006",
      "title": "進め方を選ぶ",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125, 255, 179, 0.18)",
      "kicker": "STEP 6 — 進め方",
      "headline": "かんたんな 2 段階か、\nじっくり 5 段階か。\n選べます",
      "lead": "進め方は 2 つ。計画して実行する 2 段階と、相談・計画・実行・評価・改善と進む 5 段階です。くり返す回数や、相談に加わる人数も決められます。ファイルを書きかえるのは実行の段だけです。",
      "subtitle": "急ぎなら 2 段階。じっくり見直したいときは 5 段階。",
      "image": "images/scene_006.png",
      "chips": [
        "計画 → 実行の 2 段階",
        "相談・計画・実行・評価・改善",
        "くり返し 1〜99 回",
        "書きかえは実行の段だけ"
      ],
      "metrics": [
        {
          "label": "進め方",
          "value": "2 段階 / 5 段階"
        },
        {
          "label": "くり返し",
          "value": "1〜99 回"
        },
        {
          "label": "相談の人数",
          "value": "選べる"
        }
      ],
      "cards": [
        {
          "title": "2 段階（計画 → 実行）",
          "lines": [
            "まず計画を立てる",
            "つづけて実行する",
            "急ぎのときや、内容が固まっているとき"
          ]
        },
        {
          "title": "5 段階（じっくり）",
          "lines": [
            "相談 → 計画 → 実行 →",
            "評価 → 改善 と進む",
            "見直しながら良くしていきたいとき"
          ]
        },
        {
          "title": "安心なところ",
          "lines": [
            "ファイルを書きかえるのは実行の段だけ",
            "評価と改善は、確認と動作テストだけ",
            "止めたいときはスイッチひとつ"
          ]
        }
      ],
      "facts": [
        "作業ループは PlanDo（計画→実行）と SPDCA（相談→計画→実行→評価→改善）の 2 パターン。既定は PlanDo。",
        "ソース変更を許可するのは D（実行）だけ。C（評価）と A（改善）は読み取り・テスト・動作確認のみで変更しない。",
        "Aチーム目標.作業ループ回数は 1〜99 で 99 は無制限。動員要員数は相談段の人数上限。",
        "起動時には自動作業設定と作業ループをオフへ戻し、前回プロセスの続きを無断で再開しない。"
      ],
      "evidence": [
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "PlanDo: P（計画）→ D（実行）。既定値。SPDCA: S（相談）→ P（計画）→ D（実行）→ C（評価）→ A（改善）。ソース変更を許可するのは D だけです。"
        },
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "Aチーム目標.作業ループ回数は1〜99で、99は無制限です。動員要員数は相談段の人数上限です。"
        }
      ],
      "image_prompt": "Clean widescreen illustration comparing two gentle paths in a sunny park: a short two-step stepping-stone path and a longer five-step circular path, soft glowing markers on each stone, calm instructional mood, no text in the image.",
      "short_narration": "進め方は 2 段階か、じっくり 5 段階から選べます。",
      "long_narration": "仕事の進め方も選べます。用意されているのは 2 つです。ひとつめは、計画して、実行する。かんたんな 2 段階です。やることが決まっているときは、これで十分です。ふたつめは、じっくり進む 5 段階。まず相談して、計画を立てて、実行して、結果を評価して、そして改善する。はじめから完璧をめざさず、回しながら良くしていく進め方です。何回くり返すかも決められます。1 回だけでも、何十回でも。相談に何人加わるかも選べます。ここでひとつ、安心していただきたいことがあります。ファイルを実際に書きかえるのは、実行の段だけです。評価と改善のときは、読んで確かめて、動かしてみるだけ。勝手にどんどん書きかえられていく、ということは起きません。",
      "short_audio": "audio/short_scene_006.mp3",
      "long_audio": "audio/long_scene_006.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 4.08,
      "long_start_sec": 0.0,
      "long_duration_sec": 44.4
    },
    {
      "id": "scene_007",
      "title": "仕事をお願いする",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.2)",
      "kicker": "KEY — お願いする",
      "headline": "日本語で書くだけ。\n得意な仲間が\n自動で選ばれます",
      "lead": "お願いは日本語で書きます。在庫管理の使い勝手を改善したい、案を出し合って進めてほしい。そんな書き方で大丈夫です。誰に頼むかは、これまでの経験を見て AI が選んでくれます。",
      "subtitle": "担当を指名しなくていい。経験のある仲間に、自然と仕事が集まります。",
      "image": "images/scene_007.png",
      "chips": [
        "日本語で書くだけ",
        "担当は自動で決まる",
        "経験のある人が選ばれる",
        "そのまま実行まで"
      ],
      "metrics": [
        {
          "label": "書くこと",
          "value": "お願いの文章"
        },
        {
          "label": "担当決め",
          "value": "AI におまかせ"
        },
        {
          "label": "選ぶ基準",
          "value": "これまでの経験"
        }
      ],
      "cards": [
        {
          "title": "お願いの書き方",
          "lines": [
            "やってほしいことを日本語で書く",
            "箇条書きで手順を添えてもよい",
            "対象のフォルダを選んで登録する"
          ]
        },
        {
          "title": "担当はこう決まる",
          "lines": [
            "いま動ける仲間の一覧を見る",
            "それぞれの経験と、学んだことを見る",
            "いちばん合いそうな仲間を AI が選ぶ"
          ]
        },
        {
          "title": "うれしいポイント",
          "lines": [
            "誰に頼むか迷わなくていい",
            "得意な人に自然と集まる",
            "選ばれた人がそのまま進めてくれる"
          ]
        }
      ],
      "facts": [
        "Aチーム依頼を『準備開始』で登録すると Team 起動監視が team_sub/sub_init.py を起動する。",
        "有効要員一覧と要員ごとの Aチーム経験（経験値・分類・直近の学び）を材料に、AI が担当要員を選ぶ。経験のある要員へ寄せることで蓄積ナレッジが再利用される。",
        "AI の出力が有効要員一覧に無ければ admin へフォールバックする。",
        "無進捗タイムアウトは、担当選択・タスク投入中の『準備中』が 10 分、それ以外が 30 分。"
      ],
      "evidence": [
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "有効要員一覧と要員ごとの Aチーム経験（経験値・分類・直近の学び）を材料に、AI へ担当要員を選ばせる。経験のある要員へ寄せることで蓄積ナレッジが再利用される。"
        },
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "出力が有効要員一覧に無ければ admin へフォールバックする。"
        }
      ],
      "image_prompt": "(実画面を使用) sozai/web_AIチーム_依頼編集.png",
      "short_narration": "お願いは日本語で書くだけ。担当は AI が選んでくれます。",
      "long_narration": "さあ、仕事をお願いしてみましょう。追加のボタンを押すと、お願いを書く画面が開きます。書き方は自由です。たとえば、在庫管理の使い勝手を改善したい。チームで案を出し合って進めてほしい。見づらいところを洗い出して、案を複数出して比べて、決まったら実装してほしい。そんなふうに、思っていることをそのまま書けば大丈夫です。ここがおもしろいところなのですが、誰に頼むかは、指名しなくていいのです。登録すると、いま動ける仲間の一覧と、それぞれのこれまでの経験を見て、AI がいちばん合いそうな仲間を選びます。似た仕事をしたことがある人がいれば、その人に。経験のある仲間に、自然と仕事が集まっていきます。",
      "short_audio": "audio/short_scene_007.mp3",
      "long_audio": "audio/long_scene_007.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 3.984,
      "long_start_sec": 0.0,
      "long_duration_sec": 39.216,
      "image_source": "sozai/web_AIチーム_依頼編集.png"
    },
    {
      "id": "scene_008",
      "title": "お願いが手順に変わる",
      "expression": "neutral",
      "accent": "#ffc46b",
      "accent_soft": "rgba(255, 196, 107, 0.18)",
      "kicker": "STEP 8 — 実行される",
      "headline": "選ばれた仲間が、\nお願いを手順に分けて\n進めていきます",
      "lead": "担当が決まると、お願いはそのまま作業に変わります。AI が手順に分け、順番に実行していきます。進み具合は AIタスクの画面で確認できます。どこまで進んだか、いつでも見に行けます。",
      "subtitle": "お願い 1 つが、いくつもの手順に分かれて、順番に片づいていきます。",
      "image": "images/scene_008.png",
      "chips": [
        "手順に自動で分かれる",
        "順番に実行される",
        "進み具合が見える",
        "終わったらまとめが残る"
      ],
      "metrics": [
        {
          "label": "分け方",
          "value": "AI が自動で"
        },
        {
          "label": "進み具合",
          "value": "画面で確認"
        },
        {
          "label": "終わったら",
          "value": "まとめが残る"
        }
      ],
      "cards": [
        {
          "title": "実行までの流れ",
          "lines": [
            "担当の仲間が決まる",
            "お願いが手順に分かれる",
            "順番に実行されていく"
          ]
        },
        {
          "title": "見守り方",
          "lines": [
            "AIタスクの画面で進み具合を見る",
            "待っている・動いている・終わったが分かる",
            "気になる手順は開いて中身を読める"
          ]
        },
        {
          "title": "終わったあと",
          "lines": [
            "何をしたかのまとめが残る",
            "依頼の状態が済に変わる",
            "その内容が経験になる"
          ]
        }
      ],
      "facts": [
        "依頼IDをタスクIDとして aidiy_task_agents へ投入し、Aタスク要求と紐づける。",
        "Task の進捗は同じ SQLite DB へ反映され、AIタスク画面から確認できる。",
        "AIタスク側では明細（手順）に分解され、先行SEQ による依存にしたがって順番に実行される。",
        "完了後に依頼を『済』へ進め、まとめ内容を保存する。"
      ],
      "evidence": [
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "依頼IDを task ID として aidiy_task_agents へ投入し、Aタスク要求と紐づける。Task の進捗を同じ SQLite DB へ反映する。"
        },
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "経験本登録後、依頼を『済』へ進め、まとめ内容を保存する。"
        }
      ],
      "image_prompt": "(実画面を使用) sozai/web_AIタスク.png",
      "short_narration": "お願いは手順に分かれて、順番に実行されていきます。",
      "long_narration": "担当の仲間が決まると、お願いはそのまま作業に変わります。AI がお願いの中身を読んで、必要な手順に分けます。そして、順番に実行していきます。その様子は、AIタスクという画面で見られます。いま画面に出ているのがそれです。右側にずらりと並んでいるのが、分かれた手順です。待っているもの、動いているもの、終わったもの。それぞれ状態が出ているので、どこまで進んだかがひと目で分かります。まん中には、手順のつながりを描いた流れ図。気になる手順があれば、開いて中身を読むこともできます。そして最後まで終わると、何をしたかのまとめが残ります。任せきりにせず、あとから確かめられるのです。",
      "short_audio": "audio/short_scene_008.mp3",
      "long_audio": "audio/long_scene_008.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 4.008,
      "long_start_sec": 0.0,
      "long_duration_sec": 39.624,
      "image_source": "sozai/web_AIタスク.png"
    },
    {
      "id": "scene_009",
      "title": "経験が貯まって、チームが育つ",
      "expression": "neutral",
      "accent": "#b79bff",
      "accent_soft": "rgba(183, 155, 255, 0.18)",
      "kicker": "GROW — 経験が貯まる",
      "headline": "終わった仕事は経験になり、\n次の担当選びに\n活きます",
      "lead": "仕事が終わると、その内容が経験として記録されます。何をして、何を学んだか。次に似た仕事が来たとき、その経験を持つ仲間が選ばれます。使うほどに、チームは育っていきます。",
      "subtitle": "一度やったことは、次はもっと上手に。それがチームの成長です。",
      "image": "images/scene_009.png",
      "chips": [
        "終わると経験になる",
        "何を学んだかが残る",
        "次の担当選びに活きる",
        "経験値が貯まる"
      ],
      "metrics": [
        {
          "label": "貯まるもの",
          "value": "経験と学び"
        },
        {
          "label": "活きる場面",
          "value": "次の担当選び"
        },
        {
          "label": "見る場所",
          "value": "画面の右下"
        }
      ],
      "cards": [
        {
          "title": "経験が残る流れ",
          "lines": [
            "仕事が終わると内容がまとめられる",
            "何をして、何を学んだかが残る",
            "画面の右下に経験値として貯まる"
          ]
        },
        {
          "title": "次に活きるところ",
          "lines": [
            "似た仕事は、経験のある仲間へ",
            "同じ失敗をくり返しにくくなる",
            "得意分野がだんだんはっきりする"
          ]
        },
        {
          "title": "うれしいポイント",
          "lines": [
            "使うほどにチームが育つ",
            "任せられる範囲が広がる",
            "誰が何を得意か分かってくる"
          ]
        }
      ],
      "facts": [
        "完了後に team_sub/sub_exp.py が Aチーム経験（経験値・分類・まとめ・学び）を生成する。",
        "sub_exp.py は 2 段構えで、第1ステップが対象プロジェクトで明細を読んで経験値をまとめ、第2ステップが AiDiy ルートで経験 JSON を書き出す。",
        "生成された経験は、次の依頼で担当要員を選ぶ材料として再利用される。",
        "Aチーム経験は TE + 8 桁で採番される。"
      ],
      "evidence": [
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "Task の進捗を同じ SQLite DB へ反映し、完了後に team_sub/sub_exp.py が経験を生成する。"
        },
        {
          "source": "backend_taskteam/AGENTS.md",
          "text": "Aチーム経験: 完了タスクから生成した経験値、分類、まとめ、学び。"
        }
      ],
      "image_prompt": "Warm widescreen illustration: a gentle glowing AI companion holding a small growing plant while soft light particles of finished work flow into it, sunny park background, symbolizing accumulated experience and growth, no text in the image.",
      "short_narration": "終わった仕事は経験になり、次の担当選びに活きます。",
      "long_narration": "仕事が終わったあとが、AIチームのいちばん良いところかもしれません。終わった仕事は、そのまま経験として記録されます。何をして、何がうまくいって、何を学んだか。それが仲間ごとに残っていきます。画面の右下を見ると、経験値として貯まっているのが分かります。そして次に、似た仕事をお願いしたとき。その経験を持っている仲間が選ばれます。一度やったことは、次はもっと上手にできる。同じつまずき方を、くり返しにくくなる。使えば使うほど、誰が何を得意とするかがはっきりしてきます。はじめは小さな仕事から。そのうちに、任せられる範囲が広がっていきます。チームが育つ、というのはそういうことです。",
      "short_audio": "audio/short_scene_009.mp3",
      "long_audio": "audio/long_scene_009.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 3.72,
      "long_start_sec": 0.0,
      "long_duration_sec": 43.968
    },
    {
      "id": "scene_010",
      "title": "仲間の目線で見てみる",
      "expression": "neutral",
      "accent": "#ff9ad5",
      "accent_soft": "rgba(255, 154, 213, 0.18)",
      "kicker": "STEP 10 — のぞいてみる",
      "headline": "仲間をクリックすると、\nその人の目線で\n空間を歩けます",
      "lead": "左の一覧から仲間をクリックすると、その人の目線に入れます。空間を歩いて、掲示板を読んだり、他の仲間の様子を見に行ったり。元の眺めに戻りたくなったら、エスケープキーを押すだけです。",
      "subtitle": "ただの管理画面ではありません。のぞきに行ける、居場所のある空間です。",
      "image": "images/scene_010.png",
      "chips": [
        "クリックで目線に入る",
        "空間を歩ける",
        "掲示板も読める",
        "エスケープで戻る"
      ],
      "metrics": [
        {
          "label": "入り方",
          "value": "クリック"
        },
        {
          "label": "できること",
          "value": "歩いて見て回る"
        },
        {
          "label": "戻り方",
          "value": "エスケープキー"
        }
      ],
      "cards": [
        {
          "title": "目線に入ってできること",
          "lines": [
            "空間の中を自由に歩く",
            "掲示板のチーム目標を読む",
            "他の仲間の吹き出しを見に行く"
          ]
        },
        {
          "title": "操作はかんたん",
          "lines": [
            "矢印キーで前後に進む",
            "左右で向きを変える",
            "エスケープキーで元の眺めに戻る"
          ]
        },
        {
          "title": "うれしいポイント",
          "lines": [
            "チームの様子が肌で分かる",
            "見ているだけで気分が変わる",
            "休憩エリアものぞける"
          ]
        }
      ],
      "facts": [
        "左パネルの要員をクリックするとその要員の視点（憑依視点）に入る。ESC で解除する。",
        "視点操作は上下キーで前後、左右キーで向き。画面下部に操作ガイドが表示される。",
        "チーム空間はドラッグで 360 度回転、ホイールでズームできる。",
        "空間には雑談エリア・休憩エリアなどのエリアがあり、看板で示される。"
      ],
      "evidence": [
        {
          "source": "frontend_web AIチーム空間画面",
          "text": "DRAG 360° 回転 / WHEEL ズーム / 要員状況をクリックでその人の視点 / 視点を戻す。"
        },
        {
          "source": "frontend_web AIチーム空間画面",
          "text": "CASPER に憑依中 — ↑↓ 前後、←→ 向き、ESC で解除。"
        }
      ],
      "image_prompt": "Warm first-person style widescreen illustration: walking through a sunny park from a character's point of view, other gentle glowing companions and a notice board visible ahead, immersive and friendly mood, no text in the image.",
      "short_narration": "仲間をクリックすると、その人の目線で空間を歩けます。",
      "long_narration": "最後にもうひとつ、楽しい使い方を紹介します。左の一覧から仲間をクリックしてみてください。その人の目線に、すっと入れます。あとは矢印キーで、空間の中を歩けます。前に進んで、向きを変えて。掲示板の前まで行けば、チームの目標を読めます。他の仲間のところへ行けば、その人の吹き出しが見えます。休憩エリアをのぞいてみるのもいいですね。元の眺めに戻りたくなったら、エスケープキーを押すだけです。AIチームは、ただの管理画面ではありません。仲間たちに居場所があって、様子を見に行ける空間なのです。",
      "short_audio": "audio/short_scene_010.mp3",
      "long_audio": "audio/long_scene_010.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 3.672,
      "long_start_sec": 0.0,
      "long_duration_sec": 34.92,
      "image_source": "sozai/web_AIチーム_憑依視点.png"
    },
    {
      "id": "scene_999",
      "title": "まとめ",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.2)",
      "kicker": "SUMMARY",
      "headline": "仲間を呼んで、目標を決めて、\nお願いするだけ。\nあとはチームが育ちます",
      "lead": "得意分野のちがう仲間を呼ぶ。チームの目標を 1 行書く。やってほしいことを日本語でお願いする。あとは、経験のある仲間が動いて、その経験がまた次に活きていきます。",
      "subtitle": "ひとりで抱えていた仕事を、AI のチームに相談してみませんか。",
      "image": "images/scene_999.png",
      "chips": [
        "仲間を呼ぶ",
        "目標を決める",
        "日本語でお願いする",
        "使うほど育つ"
      ],
      "metrics": [
        {
          "label": "やること",
          "value": "呼ぶ・決める・頼む"
        },
        {
          "label": "チームの成長",
          "value": "経験が貯まる"
        },
        {
          "label": "この動画",
          "value": "AiDiy が自動生成"
        }
      ],
      "cards": [
        {
          "title": "AIチームでできること",
          "lines": [
            "得意分野のちがう仲間をそろえる",
            "目標をもとに、仲間が話し合って決める",
            "経験のある仲間が選ばれて仕事を進める"
          ]
        },
        {
          "title": "はじめの一歩",
          "lines": [
            "気になる仲間を 2 人か 3 人呼んでみる",
            "チームの目標を 1 行書いてみる",
            "ひとりでは手が回らない仕事を頼んでみる"
          ]
        }
      ],
      "facts": [
        "AIチームは要員の召喚、チーム目標と作業ループ、依頼から Aタスクへの投入、経験の蓄積までを一貫して扱う。",
        "経験は次の担当要員選びに再利用され、使うほど蓄積ナレッジが増える。",
        "この紹介動画自体も AiDiy のビデオページ生成機能で自動生成されている。"
      ],
      "evidence": [],
      "image_prompt": "Bright, uplifting widescreen closing illustration: a small circle of gentle glowing AI companions in a sunny park, one of them holding a small growing plant symbolizing accumulated experience, warm sunrise gradient, hopeful mood, no text in the image.",
      "short_narration": "この動画は AiDiy が自動で作りました。チャンネル登録をお願いします。あなたの仕事も、AI のチームに相談してみませんか。",
      "long_narration": "最後にまとめます。AiDiy の AIチームは、AI の仲間が集まった小さなチームです。得意分野のちがう仲間を呼んで、チームの目標を 1 行書いて、やってほしいことを日本語でお願いする。それだけで、経験のある仲間が選ばれて、相談しながら仕事を進めてくれます。そして終わった仕事は経験として残り、また次の仕事に活きていきます。ひとりで抱えていた仕事を、まずは 1 つだけ、チームに相談してみてください。ご紹介したこの動画も、AiDiy のビデオページ生成機能で自動生成されました。台本づくりから画像、音声、ページの組み立てまで、すべて自動です。チャンネル登録を、ぜひお願いします。AiDiy で、あなたのチームを作ってみませんか。",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 8.472,
      "long_start_sec": 0.0,
      "long_duration_sec": 40.08
    }
  ],
  "total_short_duration_sec": 52.584,
  "total_long_duration_sec": 478.32
};
