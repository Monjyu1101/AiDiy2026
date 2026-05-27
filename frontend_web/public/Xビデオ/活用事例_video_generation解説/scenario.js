window.SCENARIO = {
  "project_name": "AiDiy video_generation機能 活用事例 (掛け合い版)",
  "version": "duo-v2",
  "title": "AiDiy活用事例 video_generation機能 で動画素材を自動生成",
  "assets_policy": {
    "male_avatar": "../vrm/VRM_male.vrm",
    "female_avatar": "../vrm/VRM_female.vrm",
    "tts_male": "edge:male",
    "tts_female": "edge:female",
    "audio_output_dir": "frontend_web/public/Xビデオ/活用事例_video_generation解説/audio"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "video_generation機能 で動画素材を自動生成",
      "accent": "#1f8a70",
      "accent_soft": "rgba(31, 138, 112, 0.18)",
      "layout": "hero",
      "kicker": "AIDIY USE CASE",
      "headline": "video_generation機能\n動画素材の作成を自動化する",
      "lead": "フォルダ作成からシナリオ、画像、音声、完成確認まで、段階的に進めるワークフローを実際に使ってみました。",
      "image": "images/scene_000.png",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "今回は AiDiy の video_generation機能 を実際に使った話をします。",
          "naration_text": "今回は、AiDiy の video_generation機能 を実際に使った話をします。動画素材の作成を自動化するツールで、フォルダ作成からシナリオ、画像生成、音声生成、完成確認まで、一連の作業を段階的に処理していきます。",
          "audio": "audio/dlg_000_01_female.mp3",
          "duration_sec": 16.248
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "MCP と CodeAgents を組み合わせて、ひとつのワークフローとして動かせます。",
          "naration_text": "MCP と CodeAgents を組み合わせて、ファイル操作からブラウザ確認まで、ひとつのワークフローとしてまとめて動かせます。実際に使ってみると、何度でも同じ流れを再現できる点が便利でした。",
          "audio": "audio/dlg_000_02_male.mp3",
          "duration_sec": 12.24
        }
      ],
      "duration_sec": 28.488
    },
    {
      "id": "scene_001",
      "title": "Step 00〜99の番号管理で途中から再開",
      "accent": "#0b6ea8",
      "accent_soft": "rgba(11, 110, 168, 0.18)",
      "kicker": "STEP FLOW",
      "headline": "Step 00〜99の番号管理で\n途中から再開できる",
      "lead": "各処理を番号で区切ることで、失敗した場所だけを再実行できます。",
      "image": "images/scene_001.png",
      "chips": [
        "Step 00-99",
        "START_STEP",
        "STOP_STEP",
        "進捗 Markdown"
      ],
      "metrics": [
        {
          "label": "管理単位",
          "value": "100 steps"
        },
        {
          "label": "再実行",
          "value": "範囲指定"
        }
      ],
      "cards": [
        {
          "title": "段階実行の利点",
          "lines": [
            "失敗した場所から再開できる",
            "中間確認を明示できる",
            "不要な再生成をスキップできる"
          ]
        }
      ],
      "facts": [
        "Step 01 では動画フォルダ、images、audio、進捗 Markdown を用意します。",
        "後続ステップでシナリオ、HTML、画像、音声、再生時間を順番に確定します。"
      ],
      "evidence": [
        {
          "source": "活用事例",
          "text": "開始ステップと終了ステップを指定して必要な範囲だけ再実行できます。"
        }
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "video_generation機能 は作業を Step 00 から 99 の番号で管理します。",
          "naration_text": "video_generation機能 では、作業を Step 00 から 99 までの番号で管理します。フォルダ作成、シナリオ作成、HTML修正、画像生成、確認、音声生成、再生時間更新、完成確認を、段階ごとに切り分けます。",
          "audio": "audio/dlg_001_01_female.mp3",
          "duration_sec": 17.664
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "開始と終了のステップを指定すれば、必要な範囲だけを再実行できます。",
          "naration_text": "開始ステップと終了ステップを指定すれば、必要な範囲だけを再実行できます。画像生成や音声生成は時間がかかるので、うまくいった部分をスキップできるのは、実際に使っていてとても助かりました。",
          "audio": "audio/dlg_001_02_male.mp3",
          "duration_sec": 12.648
        }
      ],
      "duration_sec": 30.312
    },
    {
      "id": "scene_002",
      "title": "差分バックアップで既存成果物を安全に検証",
      "accent": "#d65a31",
      "accent_soft": "rgba(214, 90, 49, 0.18)",
      "kicker": "BACKUP VERIFY",
      "headline": "差分バックアップで\n既存成果物を安全に検証",
      "lead": "ファイルが存在するだけで完了とせず、内容の整合性まで確認します。",
      "image": "images/scene_002.png",
      "chips": [
        "差分確認",
        "空ファイル検出",
        "テンプレート残留確認"
      ],
      "facts": [
        "対象フォルダが既にある場合も、テーマや scenario.js との整合性を検査します。",
        "テンプレート元の文言や生成途中の空ファイルがあれば修正対象にします。"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "既存フォルダがある場合も、存在確認だけでは通しません。",
          "naration_text": "既存フォルダがある場合も、存在確認だけでは通しません。今回のテーマと scenario.js が一致しているか、必要なファイルがそろっているか、空ファイルやテンプレート文言が残っていないかを毎回確認します。",
          "audio": "audio/dlg_002_01_female.mp3",
          "duration_sec": 14.208
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "差分検証のおかげで、直すべき場所をピンポイントで見つけられました。",
          "naration_text": "差分検証のおかげで、壊れている部分や不足している部分をピンポイントで直せました。自動化していても、人間が確認しやすい状態を保てる点が実用的でした。",
          "audio": "audio/dlg_002_02_male.mp3",
          "duration_sec": 10.44
        }
      ],
      "duration_sec": 24.648
    },
    {
      "id": "scene_003",
      "title": "根拠情報をもとにシーンごとの画像を自動生成",
      "accent": "#8a4fff",
      "accent_soft": "rgba(138, 79, 255, 0.18)",
      "kicker": "IMAGE AUTO",
      "headline": "根拠情報をもとに\nシーンごとの画像を自動生成",
      "lead": "雰囲気だけでなく、シーンの内容に沿った画像を作れるようにします。",
      "image": "images/scene_003.png",
      "chips": [
        "source_documents",
        "factual_bullets",
        "forbidden_elements"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "画像生成では、シーンごとの根拠情報を先に整理します。",
          "naration_text": "画像生成では、シーンごとに source_documents や factual_bullets などの根拠情報を整理してからプロンプトを作ります。内容に沿った素材が生成されるので、見た目と説明がかみ合いやすくなります。",
          "audio": "audio/dlg_003_01_female.mp3",
          "duration_sec": 13.512
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "生成した画像は images フォルダに scene_000.png 形式で保存されます。",
          "naration_text": "生成した画像は images フォルダに scene_000.png、scene_001.png の形式で保存されます。ブラウザで確認すると、シーンごとの表示や余白、文字の重なりがそろっているかをまとめてチェックできます。",
          "audio": "audio/dlg_003_02_male.mp3",
          "duration_sec": 14.136
        }
      ],
      "duration_sec": 27.648
    },
    {
      "id": "scene_004",
      "title": "掛け合い台本をMP3へ自動変換",
      "accent": "#b8860b",
      "accent_soft": "rgba(184, 134, 11, 0.18)",
      "kicker": "VOICE AUTO",
      "headline": "掛け合い台本を\nMP3へ自動変換",
      "lead": "female と male の発話を分けて管理し、シーン・ターン単位でファイル名をつけます。",
      "image": "images/scene_004.png",
      "chips": [
        "edge:female",
        "edge:male",
        "dlg_001_01_female.mp3"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "音声は発話ごとに MP3 として保存します。",
          "naration_text": "音声は発話ごとに MP3 として保存します。dlg_001_01_female.mp3 のように、シーン番号、ターン番号、話者がわかるファイル名にすることで、後から差し替えや確認がしやすくなります。",
          "audio": "audio/dlg_004_01_female.mp3",
          "duration_sec": 15.168
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "十分なサイズの音声ファイルが既にある場合は再生成をスキップします。",
          "naration_text": "十分なサイズの音声ファイルが既にある場合は再生成をスキップします。空ファイルや途中で止まったものだけを作り直す仕組みなので、長い動画でも安定して作業を再開できました。",
          "audio": "audio/dlg_004_02_male.mp3",
          "duration_sec": 11.352
        }
      ],
      "duration_sec": 26.52
    },
    {
      "id": "scene_005",
      "title": "生成した音声の長さを実測してタイムラインへ反映",
      "accent": "#3178c6",
      "accent_soft": "rgba(49, 120, 198, 0.18)",
      "kicker": "TIMELINE SYNC",
      "headline": "生成した音声の長さを実測して\nタイムラインへ反映",
      "lead": "予測値と実測値のずれをなくし、字幕やシーン送りのタイミングを正確にします。",
      "image": "images/scene_005.png",
      "chips": [
        "ffprobe",
        "duration_sec",
        "total_duration_sec"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "音声を生成したら、実際の再生時間を計測して duration_sec に反映します。",
          "naration_text": "音声を生成したら、実際の再生時間を計測して duration_sec に反映します。台本から予測した秒数のままだと字幕やシーン送りがずれるため、MP3 の実測値で上書きします。",
          "audio": "audio/dlg_005_01_female.mp3",
          "duration_sec": 13.872
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "シーン全体の尺と全体尺を更新すると、完成確認のステップに進めます。",
          "naration_text": "各発話の長さを合計してシーン全体の尺と全体尺を更新します。ここが固まると、ブラウザ再生や録画、トリミング、最終確認へ進める状態になります。",
          "audio": "audio/dlg_005_02_male.mp3",
          "duration_sec": 11.304
        }
      ],
      "duration_sec": 25.176
    },
    {
      "id": "scene_006",
      "title": "ブラウザで全項目を確認して完成判定",
      "accent": "#2f4858",
      "accent_soft": "rgba(47, 72, 88, 0.18)",
      "kicker": "QUALITY CHECK",
      "headline": "ブラウザで全項目を確認して\n完成判定へ進む",
      "lead": "画像・字幕・音声・アバター・シーン送りの動きをブラウザ上で実際に確かめます。",
      "image": "images/scene_006.png",
      "chips": [
        "中間確認",
        "再生検証",
        "完成判定"
      ],
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "完成確認では、ブラウザ上で実際の表示を確かめます。",
          "naration_text": "完成確認では、ブラウザ上で実際の表示を確かめます。画像が出ているか、字幕が長すぎないか、アバターの口パクと話者切り替えが自然か、シーン送りが崩れていないかを確認します。",
          "audio": "audio/dlg_006_01_female.mp3",
          "duration_sec": 13.248
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "問題があれば Step の番号を指定して該当箇所だけ直します。",
          "naration_text": "問題があれば、Step の番号を指定して該当箇所だけ直します。番号管理と差分検証の組み合わせがあるので、どこを直せばいいかがすぐわかる。これが、実際に使ってみて一番便利だと感じた点です。",
          "audio": "audio/dlg_006_02_male.mp3",
          "duration_sec": 13.44
        }
      ],
      "duration_sec": 26.688
    },
    {
      "id": "scene_999",
      "title": "まとめ",
      "accent": "#1f8a70",
      "accent_soft": "rgba(31, 138, 112, 0.18)",
      "layout": "hero",
      "kicker": "AIDIY USE CASE",
      "headline": "AiDiy で\nビデオ制作を自動化する",
      "lead": "video_generation機能 を使えば、素材作成から完成確認まで再現可能なワークフローで進められます。",
      "image": "images/scene_999.png",
      "dialogue": [
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "AiDiy は、AI と業務システムを組み合わせた開発環境です。",
          "naration_text": "AiDiy は、業務システム開発テンプレートをベースに、AI エージェント、MCP、画像・音声・動画生成ツールを組み合わせた開発環境です。video_generation機能 のような自動化ツールも、この環境から生まれています。",
          "audio": "audio/dlg_999_01_male.mp3",
          "duration_sec": 14.304
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "チャンネル登録して、AiDiy の活用事例をチェックしてください。",
          "naration_text": "動画を気に入っていただけたら、ぜひチャンネル登録をお願いします。AiDiy の活用事例はこれからも続々と紹介していく予定です。皆さんもぜひ video_generation機能 を試してみてください。自動化の可能性をきっと感じていただけると思います。",
          "audio": "audio/dlg_999_02_female.mp3",
          "duration_sec": 16.824
        }
      ],
      "duration_sec": 31.128
    }
  ],
  "total_duration_sec": 220.608
};
