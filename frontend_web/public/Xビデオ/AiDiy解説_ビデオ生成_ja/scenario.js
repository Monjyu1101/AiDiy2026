window.SCENARIO = {
  "project_name": "AiDiy解説_ビデオ生成_ja",
  "version": "duo-v2",
  "title": "AiDiy ビデオページ生成機能 解説 — topic からビデオ完成まで全自動化の 9 ステップ",
  "assets_policy": {
    "male_avatar": "../_vrm/VRM_male.vrm",
    "female_avatar": "../_vrm/VRM_female.vrm",
    "tts_male": "edge:male",
    "tts_female": "edge:female",
    "audio_output_dir": "frontend_web/public/Xビデオ/AiDiy解説_ビデオ生成_ja/audio"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "イントロ — AiDiy ビデオページ生成機能へようこそ",
      "accent": "#1a6ea0",
      "accent_soft": "rgba(26, 110, 160, 0.18)",
      "layout": "hero",
      "kicker": "VIDEO GENERATION",
      "headline": "topic からビデオ完成まで\n全自動化する AiDiy ビデオページ生成",
      "lead": "AiDiy のビデオページ生成機能が、topic 設定からシナリオ作成・画像生成・音声合成・HTML 組み立てまでを 9 ステップで全自動化します。",
      "image": "images/scene_000.png",
      "source_summary": "AiDiy ビデオページ生成機能の概要。ビデオページ生成_紹介.py（ひとりアバター）と ビデオページ生成_解説.py（二人掛け合い）の 2 スクリプトで topic から完成ビデオまで 9 ステップ全自動。この動画は AiDiy のビデオページ生成機能で自動生成された。",
      "factual_bullets": [
        "2 種類のスクリプト: ビデオページ生成_紹介.py（ひとりアバター）/ ビデオページ生成_解説.py（二人掛け合い）",
        "9 ステップ: Step 00〜08 + Step 99（完成案内）",
        "設定: _ビデオページ生成_*_設定.json（topic / folder_name / template_dir / language）",
        "状況管理: _ビデオページ生成_*_状況.json（途中再開・特定ステップ再実行）",
        "この動画は AiDiy のビデオページ生成機能で自動生成"
      ],
      "forbidden_elements": [
        "AiDiy が商用製品として公式リリースされているかのような断言",
        "具体的な料金や SLA の断定"
      ],
      "image_prompt": "A futuristic automation pipeline diagram showing 9 steps of video generation: topic.json at the start, arrows flowing through scenario generation, image generation, audio synthesis, HTML assembly, and complete video page at the end. Python script icons and MCP tool icons at each stage. Blue tech aesthetic on dark background with Japanese step labels.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "この動画は AiDiy のビデオページ生成機能によって自動生成されました。",
          "naration_text": "こんにちは。この動画は AiDiy のビデオページ生成機能によって自動生成されました。シナリオの作成、シーン画像の生成、ナレーション音声の合成、そして HTML プレイヤーへの組み立てまで、すべての工程を AiDiy 自身が担当しています。AiDiy のビデオページ生成機能は、topic という設定に書かれたテーマから完成したビデオページを 9 ステップで自動作成する仕組みです。今回の動画では、そのビデオページ生成機能の全体像を、男女 2 人の掛け合いでお届けします。ぜひ最後までお楽しみください。",
          "audio": "audio/dlg_000_01_female.mp3",
          "duration_sec": 35.952
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "ビデオページ生成には 2 スクリプトがあり、9 ステップで topic から完成します。",
          "naration_text": "AiDiy のビデオページ生成には 2 種類のスクリプトがあります。ビデオページ生成_紹介.py はひとりアバターで解説する紹介型、ビデオページ生成_解説.py は 2 人が掛け合いで解説する解説型です。どちらも topic にテーマを書いて実行するだけで、Step 00 の初期確認から始まり、フォルダ作成、シナリオ生成、HTML 修正、画像生成、音声合成、再生時間更新、最終確認、そして完成案内の Step 99 まで、9 ステップを順番に実行して完成ビデオページを出力します。",
          "audio": "audio/dlg_000_02_male.mp3",
          "duration_sec": 31.8
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "設定 JSON に topic・言語・フォルダ名を書けば、あとは自動実行です。",
          "naration_text": "ビデオページ生成の入口となるのは設定 JSON ファイルです。topic にテーマの説明を書き込み、folder_name で出力先フォルダ名を決め、language で出力言語を指定するだけで準備完了です。設定ファイルを用意したあとはスクリプトを起動するだけで、CodeAgents による AI 処理と各種 MCP ツールが連携して、シナリオ作成から音声生成まで自動で進行します。途中から再開したり特定ステップだけ再実行したりすることも、状況 JSON を使って簡単に行えます。",
          "audio": "audio/dlg_000_03_female.mp3",
          "duration_sec": 32.664
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "CodeAgents と 14 の MCP ツールが連携してビデオ生成の全工程を担います。",
          "naration_text": "ビデオページ生成のバックエンドでは、CodeAgents と AiDiy TOOL HUB の MCP ツール群が連携します。シナリオ作成と HTML 修正では CodeAgents が AI でテキストを生成し、画像生成では aidiy_image_generation MCP が各シーンの背景画像を作ります。音声合成では aidiy_text_to_speech MCP が Edge TTS を使って男女それぞれのナレーション音声を生成し、再生時間計測では aidiy_ffmpeg_control MCP が実際の音声ファイルを解析して duration_sec を正確な値に更新します。",
          "audio": "audio/dlg_000_04_male.mp3",
          "duration_sec": 30.0
        }
      ],
      "duration_sec": 130.416
    },
    {
      "id": "scene_001",
      "title": "2 つのメインスクリプト — 紹介型と解説型",
      "accent": "#2e86ab",
      "accent_soft": "rgba(46, 134, 171, 0.18)",
      "kicker": "SCRIPTS",
      "headline": "紹介型スクリプトと解説型スクリプト\n2 種類のビデオ生成ワークフロー",
      "lead": "ビデオページ生成_紹介.py（ひとりアバター）と ビデオページ生成_解説.py（二人掛け合い）がそれぞれ異なるスタイルのビデオを全自動生成します。",
      "image": "images/scene_001.png",
      "source_summary": "ビデオページ生成_紹介.py: ひとりアバター（female 単一話者）、short_audio/long_audio。ビデオページ生成_解説.py: 二人掛け合い（female/male 交互）、dialogue 配列。どちらも 9 ステップ共通フロー。各スクリプト 600〜800 行設計。",
      "factual_bullets": [
        "ビデオページ生成_紹介.py: ひとりアバター、female 単一話者、short/long audio",
        "ビデオページ生成_解説.py: 二人掛け合い、female/male 交互、dialogue 配列",
        "Step 00〜99 の 9 ステップは両スクリプト共通フロー",
        "utils/ 共通ロジック共有、各メインスクリプト 600〜800 行設計"
      ],
      "forbidden_elements": [
        "スクリプトの具体的なファイルサイズや行数の断言",
        "未実装の機能があるかのような誤解"
      ],
      "image_prompt": "A side-by-side comparison of two video generation scripts: left side shows a solo female avatar with single audio waveform (introduction style), right side shows two avatars (female and male) with alternating dialogue bubbles (discussion style). Python script files labeled 紹介.py and 解説.py above each. Blue tech aesthetic, dark background.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "ビデオページ生成_紹介.py はひとりのアバターが解説する紹介型スクリプトです。",
          "naration_text": "ビデオページ生成_紹介.py は、ひとりの女性アバターがテーマをひとりで解説する紹介型ビデオを自動生成するスクリプトです。female の単一話者でナレーションを進め、各シーンに 1 本の音声ファイルを割り当てます。シンプルな構成なので視聴者に内容が伝わりやすく、製品やサービスの紹介、機能の概要説明などに向いています。紹介型では short_audio と long_audio の 2 種類の長さを使い分けて、シーンごとに最適な尺で収録します。",
          "audio": "audio/dlg_001_01_female.mp3",
          "duration_sec": 31.008
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "ビデオページ生成_解説.py は female と male の 2 人が掛け合うスクリプトです。",
          "naration_text": "ビデオページ生成_解説.py は今回の動画のような二人掛け合いスタイルで解説するビデオを自動生成するスクリプトです。female と male の 2 アバターが交互に発言する dialogue 形式で進行し、1 シーンに複数の発言ターンが含まれます。このスタイルは視聴者が飽きにくく、一方がポイントを提示してもう一方が補足するという形で、複雑な内容を分かりやすく伝えるのに向いています。このビデオ自体がその解説型の出力例です。",
          "audio": "audio/dlg_001_02_male.mp3",
          "duration_sec": 26.64
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "2 つのスクリプトは utils/ モジュールで共通ロジックを共有する設計です。",
          "naration_text": "紹介型と解説型の 2 スクリプトは、コードを単純に 2 倍に書くのではなく、utils フォルダに共通ロジックを切り出して共有する設計になっています。共通ロジックには設定の読み書き、状況の管理、CodeAgents の実行、MCP ツールの呼び出し、ffmpeg による音声長計測などが含まれます。各メインスクリプトはそのビデオスタイル固有のプロンプトや描画ロジックと main 関数だけを持ち、600 から 800 行程度に収まるよう設計されています。",
          "audio": "audio/dlg_001_03_female.mp3",
          "duration_sec": 31.224
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Step 00 から Step 99 まで 9 ステップで topic から完成ビデオを出力します。",
          "naration_text": "全体フローは Step 00 から Step 99 まで番号で管理されています。Step 00 で設定とツールの疎通を確認し、Step 01 でテンプレートフォルダをコピーして出力フォルダを作成します。Step 02 で CodeAgents が scenario.js を生成し、Step 03 で HTML の表示文言を更新します。Step 04 で各シーンの画像を生成し、Step 05 で中間確認を行います。Step 06 で音声を合成し、Step 07 で実再生時間を更新、Step 08 で最終確認を行い、Step 99 で完成を案内します。",
          "audio": "audio/dlg_001_04_male.mp3",
          "duration_sec": 34.488
        }
      ],
      "duration_sec": 123.36
    },
    {
      "id": "scene_002",
      "title": "設定 JSON と状況 JSON — 2 ファイルで制御する柔軟な管理",
      "accent": "#e84855",
      "accent_soft": "rgba(232, 72, 85, 0.18)",
      "kicker": "CONFIGURATION",
      "headline": "設定 JSON と状況 JSON\n2 ファイルで柔軟なステップ管理",
      "lead": "_ビデオページ生成_*_設定.json で静的な設定を管理し、_ビデオページ生成_*_状況.json で進行状況を記録して途中再開と部分再実行を実現します。",
      "image": "images/scene_002.png",
      "source_summary": "設定.json: topic/folder_name/template_dir/language/API URL などの静的パラメータ。状況.json: 現在のステップ番号・実行日時を自動記録。途中再開: 状況.jsonの番号から継続。部分再実行: ステップ番号を引数で指定。",
      "factual_bullets": [
        "_ビデオページ生成_*_設定.json: topic / folder_name / template_dir / language / API URL",
        "_ビデオページ生成_*_状況.json: 現在ステップ番号・実行日時（スクリプトが自動更新）",
        "途中再開: 状況.json のステップ番号から自動継続",
        "部分再実行: 引数でステップ番号を指定して特定ステップだけ再実行"
      ],
      "forbidden_elements": [
        "JSON ファイルの具体的なキー名の断言（実装と乖離する恐れ）"
      ],
      "image_prompt": "Two JSON configuration files side by side: left file labeled 設定.json containing fields like topic, folder_name, language in a clean code editor view; right file labeled 状況.json showing step number and timestamp. Arrows showing the workflow: human edits 設定.json, script auto-updates 状況.json. Red accent color scheme, dark background.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "設定 JSON には topic・folder_name・language などの静的パラメータを記述します。",
          "naration_text": "ビデオページ生成の中心となる設定 JSON には、topic、folder_name、template_dir、language、API の URL など、ビデオ生成に必要なすべての静的パラメータを記述します。topic にはビデオのテーマと解説したい内容の詳細を書きます。これが CodeAgents に渡されてシナリオの内容を決定する重要な情報になります。folder_name は出力先フォルダの名前、template_dir はベースとなるテンプレートフォルダのパス、language は出力言語コードです。これらを一か所に集めることで、ビデオの設定変更が簡単になります。",
          "audio": "audio/dlg_002_01_female.mp3",
          "duration_sec": 37.008
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "状況 JSON にはステップ番号が記録され、途中再開・部分再実行ができます。",
          "naration_text": "状況 JSON には、現在どのステップまで完了しているかのステップ番号と実行日時が記録されています。スクリプトは起動時にこの状況 JSON を読み込み、前回の続きから自動的に再開します。また引数でステップ番号を指定することで、特定のステップだけを再実行することもできます。たとえば画像生成だけやり直したい場合は Step 04 を指定して実行すれば、他のステップには触れずに画像だけ再生成できます。長い処理の途中で停止しても、ゼロからやり直さずに済む設計です。",
          "audio": "audio/dlg_002_02_male.mp3",
          "duration_sec": 30.432
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "設定と状況の JSON 分離が、安全な管理と進捗追跡を両立させます。",
          "naration_text": "設定 JSON と状況 JSON の 2 ファイルに役割を分けているのには理由があります。設定 JSON は人間が編集するファイルで、テーマや言語などビデオの内容を決める情報を持ちます。一方の状況 JSON はスクリプトが自動で書き換えるファイルで、どのステップまで完了したかを追跡します。この分離によって、設定を変更しても状況の記録が上書きされることがなく、途中再開のロジックが壊れません。また設定を誤って変更した場合でも状況はそのまま保持されるため、安全なデバッグができます。",
          "audio": "audio/dlg_002_03_female.mp3",
          "duration_sec": 34.128
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "同じ構造で topic や language だけ変えると別テーマのビデオをすぐ作れます。",
          "naration_text": "この 2 JSON 設計はシンプルですが実用上の利点が大きいです。たとえばほぼ同じ内容で言語だけ変えたビデオを作りたい場合、設定 JSON の language だけ変更して状況 JSON を初期化すれば、同じフローで別言語版のビデオが作れます。テーマを変える場合は topic と folder_name を書き替えるだけです。共通のシナリオ構造と処理フローをそのまま再利用しながら、コンテンツだけを差し替える柔軟性が、この JSON 分離設計によって実現されています。",
          "audio": "audio/dlg_002_04_male.mp3",
          "duration_sec": 27.096
        }
      ],
      "duration_sec": 128.664
    },
    {
      "id": "scene_003",
      "title": "Step 00〜02 — 初期確認・フォルダ作成・シナリオ生成",
      "accent": "#34a853",
      "accent_soft": "rgba(52, 168, 83, 0.18)",
      "kicker": "STEP 00-02",
      "headline": "初期確認からシナリオ生成まで\nStep 00・01・02 の流れ",
      "lead": "Step 00 で設定と疎通を確認し、Step 01 でテンプレートをコピー、Step 02 で CodeAgents が scenario.js を全シーン分生成します。",
      "image": "images/scene_003.png",
      "source_summary": "Step 00: 設定.json 存在確認 / テンプレートフォルダ確認 / API 疎通 / CodeAgents 疎通。Step 01: template_dir を folder_name にコピー。Step 02: CodeAgents が scenario.js を生成（scenes 配列・dialogue・image_prompt・audio パス）。",
      "factual_bullets": [
        "Step 00: 設定確認 / テンプレート確認 / API 疎通 / CodeAgents 疎通",
        "Step 01: テンプレートフォルダをそのままコピーして出力フォルダ作成",
        "Step 02: CodeAgents が scenes 配列・dialogue・image_prompt・音声パスを生成",
        "image_prompt はシーンごとに生成され Step 04 の画像生成で直接使用"
      ],
      "forbidden_elements": [
        "CodeAgents が人間の確認なしに完璧なシナリオを生成すると断言すること"
      ],
      "image_prompt": "A step-by-step flow diagram for Steps 00-02: Step 00 shows checkmarks confirming config file, template folder, API connection, and CodeAgents ready; Step 01 shows folder copy operation; Step 02 shows CodeAgents generating scenario.js with JSON structure visible. Green accent color scheme, clean tech illustration, dark background.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Step 00 は設定・テンプレート・API・CodeAgents の疎通確認ステップです。",
          "naration_text": "Step 00 の初期確認は、ビデオページ生成を開始する前の事前チェックです。設定 JSON が正しく存在するか、テンプレートフォルダが見つかるか、API の URL が有効か、そして CodeAgents が応答するかを順番に確認します。いずれかのチェックが失敗した場合は、その問題を解決してから次のステップへ進むよう案内します。この初期確認を丁寧に行うことで、後のステップで環境依存の失敗が発生する確率が大幅に下がります。準備が整っていれば Step 01 へ自動で進みます。",
          "audio": "audio/dlg_003_01_female.mp3",
          "duration_sec": 34.8
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Step 01 はテンプレートフォルダを丸ごとコピーして出力フォルダを作成します。",
          "naration_text": "Step 01 では、テンプレートフォルダを output フォルダとしてコピーします。テンプレートには index.html、初期の scenario.js、images フォルダ、audio フォルダなどビデオプレイヤーの骨格が揃っています。このコピーによって、既存のテンプレートを壊さずに新しいビデオ専用のフォルダが出来上がります。出力フォルダ名は設定 JSON の folder_name で決まるため、テーマごとに分かりやすい名前のフォルダが自動で作成されます。コピーが完了したら状況 JSON のステップ番号が 01 に更新されます。",
          "audio": "audio/dlg_003_02_male.mp3",
          "duration_sec": 31.92
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Step 02 では CodeAgents が scenario.js の全シーンとダイアログを生成します。",
          "naration_text": "Step 02 はビデオの内容を決める最重要ステップです。CodeAgents が設定 JSON の topic を受け取り、scenes 配列の全シーン定義と各シーンの dialogue エントリをすべて生成します。dialogue には speaker、telop_text、naration_text、audio パス、仮の duration_sec が含まれます。各シーンには image_prompt も生成されるため、Step 04 の画像生成でそのまま使用できます。複雑な JSON 構造の生成を AI に任せることで、人間が手作業でシナリオを書く時間を大幅に短縮できます。",
          "audio": "audio/dlg_003_03_female.mp3",
          "duration_sec": 35.472
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "image_prompt はシーンごとに生成されて Step 04 の画像生成で直接使われます。",
          "naration_text": "Step 02 で生成される scenario.js には、各シーンに image_prompt フィールドが含まれます。このフィールドには、そのシーンの内容を視覚化するための画像生成プロンプトが英文で書かれています。Step 04 では、この image_prompt を aidiy_image_generation MCP にそのまま渡すことで、シーンに合った背景画像が自動生成されます。source_summary と factual_bullets フィールドも含まれるため、情報として誤った画像が生成されにくくなっています。",
          "audio": "audio/dlg_003_04_male.mp3",
          "duration_sec": 27.0
        }
      ],
      "duration_sec": 129.192
    },
    {
      "id": "scene_004",
      "title": "Step 03〜06 — HTML 更新・画像生成・中間確認・音声合成",
      "accent": "#f4a261",
      "accent_soft": "rgba(244, 162, 97, 0.18)",
      "kicker": "STEP 03-06",
      "headline": "HTML 更新・画像生成・中間確認\n音声合成まで 4 ステップ連続実行",
      "lead": "CodeAgents が HTML を更新し、MCP ツールが画像と音声を自動生成。中間確認で品質を担保します。",
      "image": "images/scene_004.png",
      "source_summary": "Step 03: CodeAgents が index.html の表示文言をテーマに更新。Step 04: aidiy_image_generation MCP で image_prompt から各シーン背景画像を生成。Step 05: 中間確認（シナリオ・HTML・画像の検証）。Step 06: aidiy_text_to_speech MCP で Edge TTS、male/female 交互に音声生成。",
      "factual_bullets": [
        "Step 03: CodeAgents が index.html のコンテンツ部分の文言を更新（プレイヤーロジックは変更なし）",
        "Step 04: aidiy_image_generation MCP + image_prompt で scene_NNN.png を images/ に保存",
        "Step 05: シナリオ・HTML・画像の内容検証、問題あれば前ステップに戻る",
        "Step 06: aidiy_text_to_speech MCP + Edge TTS で dlg_NNN_NN_speaker.mp3 を audio/ に保存",
        "500 バイト超の既存音声ファイルは再生成スキップ"
      ],
      "forbidden_elements": [
        "AI 生成画像が常に正確な情報を表現できるという断言"
      ],
      "image_prompt": "A workflow diagram showing Steps 03-06: Step 03 shows HTML file being updated with text edits; Step 04 shows image generation with a scene background being created from a text prompt; Step 05 shows a checklist verification screen; Step 06 shows audio waveforms being generated for female and male voices alternately. Orange accent color scheme, dark background.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Step 03 では CodeAgents が index.html の表示文言をテーマに合わせて更新します。",
          "naration_text": "Step 03 では、テンプレートからコピーした index.html の表示テキストをテーマに合わせて更新します。タイトルや概要テキスト、フッターなどのビデオタイトルや説明文を CodeAgents が書き直します。index.html のプレイヤーとしての動作ロジック、つまりアバター表示、字幕表示、音声再生、口パク同期などには手を加えずに、コンテンツ部分の文言だけをテーマに合わせて変更します。これにより、テンプレートの再利用性を維持しながら、各ビデオのタイトルや説明が正しく表示されます。",
          "audio": "audio/dlg_004_01_female.mp3",
          "duration_sec": 35.952
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Step 04 では aidiy_image_generation MCP が各シーンの背景画像を自動生成します。",
          "naration_text": "Step 04 では scenario.js の image_prompt を使って各シーンの背景画像を生成します。aidiy_image_generation MCP は OpenAI、Gemini、FreeAI など複数のプロバイダに対応しており、設定で指定したプロバイダでシーンごとに画像を生成して images フォルダに保存します。scene_000.png から scene_999.png まで、シーン ID に対応するファイル名で自動保存されるため、scenario.js の image フィールドと自動的に一致します。画像の内容は image_prompt の品質に依存するため、Step 02 でのプロンプト作成が重要です。",
          "audio": "audio/dlg_004_02_male.mp3",
          "duration_sec": 35.04
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Step 05 は中間確認で、問題があれば Step 02 や Step 03 に戻って修正します。",
          "naration_text": "Step 05 は自動生成後の中間確認ステップです。生成された scenario.js の内容、更新後の index.html の表示、そして各シーンの画像を確認し、問題があれば前のステップに戻って修正します。たとえばシナリオの内容がテーマからずれている場合は Step 02 を再実行し、HTML の文言が不適切な場合は Step 03 を再実行します。この中間確認を挟むことで、音声合成の前に内容の問題を発見でき、無駄な音声ファイルの生成を防げます。",
          "audio": "audio/dlg_004_03_female.mp3",
          "duration_sec": 34.896
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Step 06 では Edge TTS で female・male それぞれのナレーション音声を生成します。",
          "naration_text": "Step 06 では scenario.js の各 dialogue エントリの naration_text を使って音声ファイルを生成します。aidiy_text_to_speech MCP の Edge TTS を使い、female には日本語の女性音声、male には日本語の男性音声を割り当てます。音声ファイルは audio/dlg_シーン番号_ターン番号_speaker.mp3 という命名規則で保存されます。すでに 500 バイト超のファイルが存在する場合は再生成をスキップするため、特定のターンだけ再生成する際の誤生成を防げます。すべての dialogue に対して順番に音声が生成されます。",
          "audio": "audio/dlg_004_04_male.mp3",
          "duration_sec": 34.32
        }
      ],
      "duration_sec": 140.208
    },
    {
      "id": "scene_005",
      "title": "Step 07〜99 と utils/ — 仕上げと共通ロジック設計",
      "accent": "#7c3aed",
      "accent_soft": "rgba(124, 58, 237, 0.18)",
      "kicker": "STEP 07-99 & UTILS",
      "headline": "音声尺更新・最終確認・完成案内\nutils/ 5 モジュール設計",
      "lead": "ffmpeg で正確な音声長を計測して scenario.js を更新し、最終確認を経て完成案内へ。utils/ の 5 モジュール設計が 2 スクリプトの共通ロジックを支えます。",
      "image": "images/scene_005.png",
      "source_summary": "Step 07: ffprobe で各音声ファイルの実尺取得 → scenario.js の duration_sec 更新。Step 08: 必須ファイル・画像数・音声数の最終確認。Step 99: 完成案内・URL 表示。utils/: VideoGenCtx / runner / steps / generation / infra の 5 モジュール。",
      "factual_bullets": [
        "Step 07: aidiy_ffmpeg_control MCP ffprobe で各 MP3 の duration を取得、duration_sec を実尺に更新",
        "Step 08: scenario.js / index.html / images/ / audio/ の必須ファイル最終確認",
        "Step 99: 完成案内・ビデオページ URL 表示",
        "utils/VideoGenCtx: 全体コンテキスト管理",
        "utils/runner: ステップ順次実行・状況 JSON 更新",
        "utils/steps: 各ステップ実装",
        "utils/generation: CodeAgents / MCP 呼び出し / 音声生成",
        "utils/infra: ファイル操作 / JSON 読み書き / ログ出力"
      ],
      "forbidden_elements": [
        "Step 07 以降が常に正常完了するという断言"
      ],
      "image_prompt": "A finalization workflow diagram: Step 07 shows ffmpeg measuring audio duration with waveform and timer icons; Step 08 shows a checklist with all green checkmarks for files, images, and audio; Step 99 shows a completion banner with video page URL. Below, a module diagram shows utils/ folder with 5 labeled boxes (VideoGenCtx, runner, steps, generation, infra). Purple accent color scheme, dark background.",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Step 07 では ffmpeg が各音声の実再生時間を計測し duration_sec を更新します。",
          "naration_text": "Step 07 では、Step 06 で生成した音声ファイルの実際の再生時間を計測します。aidiy_ffmpeg_control MCP の ffprobe を使って各 MP3 の正確な duration を取得し、scenario.js の各 dialogue エントリの duration_sec と、シーンの合計 duration_sec を実尺に更新します。Step 02 で設定した仮の duration_sec は目安値なので、音声生成後に実尺で上書きすることが不可欠です。この更新によってビデオプレイヤーのタイマー精度が確保され、次のシーンへの移行タイミングが正確になります。",
          "audio": "audio/dlg_005_01_female.mp3",
          "duration_sec": 37.176
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "Step 08 は必須ファイル・画像数・音声数を確認する最終チェックです。",
          "naration_text": "Step 08 は完成前の最終確認ステップです。scenario.js と index.html が正しく存在するか、images フォルダに各シーンの画像が揃っているか、audio フォルダに全 dialogue の音声ファイルが揃っているかをチェックします。不足しているファイルがあれば対応するステップ番号を指定して再実行するよう案内します。この最終確認でエラーが出なければ、すべての素材が揃った完成品のビデオページが出力されたことを保証できます。確認が通ると状況 JSON にステップ 08 完了が記録されます。",
          "audio": "audio/dlg_005_02_male.mp3",
          "duration_sec": 31.512
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Step 99 は完成を案内するステップで、ブラウザで開いて動作確認できます。",
          "naration_text": "Step 99 は完成案内ステップです。すべてのステップが正常に完了したことを確認し、完成したビデオページの URL やフォルダパスを表示します。ブラウザで index.html を開けば、2 体のアバターが左右に配置され、シーンごとに背景画像が切り替わりながら音声が再生されるビデオページを確認できます。字幕の表示、アバターの口パク同期、話者切替の暗転エフェクト、ステレオパンニングなども動作します。完成したビデオページは frontend_web の Xビデオメニューからも一覧表示できます。",
          "audio": "audio/dlg_005_03_female.mp3",
          "duration_sec": 35.184
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "utils/ の 5 モジュールが 2 スクリプトの共通ロジックを分担して担います。",
          "naration_text": "ビデオページ生成の共通ロジックは utils フォルダの 5 モジュールに集約されています。VideoGenCtx はビデオ生成全体のコンテキストと状態を管理するクラスです。runner はステップの順次実行と状況 JSON の更新を担当します。steps には Step 00 から Step 99 の各ステップの実装が揃っています。generation は CodeAgents 呼び出し、MCP ツール呼び出し、音声生成などの生成処理を集めたモジュールです。infra はファイル操作、JSON 読み書き、ログ出力などのインフラ層です。この 5 分割により各メインスクリプトは固有のロジックだけに集中できます。",
          "audio": "audio/dlg_005_04_male.mp3",
          "duration_sec": 36.696
        }
      ],
      "duration_sec": 140.568
    },
    {
      "id": "scene_999",
      "title": "まとめ — AiDiy が自分で動画を作る世界",
      "accent": "#1a6ea0",
      "accent_soft": "rgba(26, 110, 160, 0.18)",
      "kicker": "SUMMARY",
      "headline": "topic を入力するだけで\nビデオページが完成する AiDiy",
      "lead": "シナリオ作成から画像生成・音声合成・HTML 組み立てまで全自動化する AiDiy ビデオページ生成機能のまとめです。",
      "image": "images/scene_999.png",
      "source_summary": "AiDiy ビデオページ生成機能のまとめ: 2 スクリプト（紹介型・解説型）、9 ステップ全自動化、設定.json + 状況.json 管理、CodeAgents + 14 MCP 連携、utils/ 5 モジュール設計。この動画は AiDiy のビデオページ生成機能で自動生成。",
      "factual_bullets": [
        "2 スクリプト: 紹介型（ひとりアバター）/ 解説型（二人掛け合い）",
        "9 ステップ全自動化: Step 00〜08 + Step 99",
        "設定.json + 状況.json で設定管理と進捗追跡を分離",
        "CodeAgents + 14 MCP の連携でシナリオ・画像・音声をすべて自動生成",
        "utils/ 5 モジュール設計で共通ロジックを集約",
        "この動画は AiDiy のビデオページ生成機能で自動生成"
      ],
      "forbidden_elements": [
        "AiDiy が商用製品として公式リリースされているかのような断言",
        "チャンネル登録数や視聴数への言及"
      ],
      "image_prompt": "A triumphant summary visualization of AiDiy's video generation feature: center shows a glowing pipeline from a settings JSON file through 9 numbered steps to a complete video page. The video page shows two VRM avatars (female right, male left) with scene images and subtitles. Text labels: scenario.js, images/, audio/, index.html. Blue and gold color scheme, inspiring futuristic aesthetic.",
      "dialogue": [
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "topic を書いて実行するだけで 9 ステップが自動進行してビデオが完成します。",
          "naration_text": "今回の動画では、AiDiy のビデオページ生成機能の全体像をお届けしました。設定 JSON に topic を書いてスクリプトを実行するだけで、Step 00 の初期確認から Step 99 の完成案内まで 9 ステップが自動で進行します。シナリオ作成では CodeAgents が AI の力で全シーンの dialogue と image_prompt を生成し、画像生成では MCP が image_prompt から各シーンの背景画像を作ります。音声合成では Edge TTS が male と female の音声を生成し、ffmpeg が実尺を計測して scenario.js を更新します。",
          "audio": "audio/dlg_999_01_male.mp3",
          "duration_sec": 32.688
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "設定と状況の JSON 分離が途中再開と部分再実行を可能にする重要な設計です。",
          "naration_text": "ビデオページ生成の設計で特に重要なのは、設定 JSON と状況 JSON を分離したシンプルな管理方式です。この分離によって、途中で失敗しても続きから再開できる堅牢性と、特定ステップだけ再実行できる柔軟性が同時に実現されています。また utils フォルダの 5 モジュール設計によって、紹介型と解説型の 2 スクリプトが共通ロジックを再利用しながら、それぞれのビデオスタイルに特化した処理だけを持つ、保守しやすいコード構成になっています。",
          "audio": "audio/dlg_999_02_female.mp3",
          "duration_sec": 30.624
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "CodeAgents と 14 の MCP の組み合わせが AiDiy 自動化の可能性を広げます。",
          "naration_text": "ビデオページ生成機能は、AiDiy のコアコンセプトである「AI の力で業務を自動化する」の実践例です。CodeAgents による複雑な構造化テキストの生成と、14 の MCP ツールによる画像・音声・動画処理の組み合わせは、ビデオ生成以外の自動化タスクにも応用できます。たとえば定期レポートの自動生成、技術ドキュメントのビデオ化、イベント告知コンテンツの量産など、topic を変えるだけでさまざまなビデオを効率よく作れます。",
          "audio": "audio/dlg_999_03_male.mp3",
          "duration_sec": 26.688
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "この動画は AiDiy 自身が自動生成しました。ぜひ AiDiy を試してみてください！",
          "naration_text": "この動画はまさに AiDiy のビデオページ生成機能によって自動生成されました。シナリオの作成から画像の生成、音声の合成まで、すべての工程を AiDiy 自身が担当しています。AiDiy に興味を持っていただけた方は、ぜひご自身で動かしてみてください。設定に topic を書いて実行するだけで、こんな動画が自動で生成されます。使えば使うほど「こんなことも自動化できるんだ」という発見があります。ぜひ AiDiy と一緒に、AI 自動化の楽しさを体験してみてください！",
          "audio": "audio/dlg_999_04_female.mp3",
          "duration_sec": 32.928
        }
      ],
      "duration_sec": 122.928
    }
  ],
  "total_duration_sec": 915.336
};
