window.SCENARIO = {
  "project_name": "ニュース_20260902_claudefablemythos_ja",
  "language": "ja",
  "version": "duo-v2",
  "title": "Claude Fable 5.1 / Mythos 5.1 発表",
  "assets_policy": {
    "male_avatar": "../_vrm/VRM_male.vrm",
    "female_avatar": "../_vrm/VRM_female.vrm",
    "tts_male": "edge:male",
    "tts_female": "edge:female",
    "audio_output_dir": "frontend_web/public/Xビデオ/ニュース_20260902_claudefablemythos_ja/audio"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "イントロ",
      "accent": "#1a6ea0",
      "accent_soft": "rgba(26, 110, 160, 0.18)",
      "layout": "hero",
      "kicker": "AIニュース解説",
      "headline": "Claude Fable 5.1 / Mythos 5.1\n発表をやさしく解説",
      "image": "images/scene_000.png",
      "source_documents": [
        "https://www.anthropic.com/claude-fable-and-mythos-5-1"
      ],
      "source_summary": "Anthropicが2026年9月1日に発表したClaude Fable 5.1 / Mythos 5.1を、確認済みの範囲で紹介します。",
      "factual_bullets": [
        "2026年9月1日の発表",
        "同一の基盤モデルに異なる安全策と提供経路",
        "長時間の問題解決・コーディング・知識労働への対応"
      ],
      "forbidden_elements": [
        "誰でも無条件に利用できるという断定",
        "人の確認なしに全作業を完了するという断定"
      ],
      "image_prompt": "二人の案内役と、長時間のAI支援作業を表す抽象的なタスクの流れ。文字、ロゴ、数値なし。青と橙を基調にした、日本語AIニュース向けの信頼感ある画面。",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "このニュース解説動画は AiDiy のニュース版ビデオ生成機能で作られています。",
          "naration_text": "こんにちは。このニュース解説動画は、AiDiy のニュース版ビデオ生成機能で自動生成されています。今回は、Anthropic が2026年9月1日に発表した Claude Fable 5.1 / Mythos 5.1 を、初めてAIのニュースに触れる方にも分かる言葉で見ていきます。公式発表で確認できる内容と、使う前に確かめたい条件を分けてお伝えします。",
          "audio": "audio/dlg_000_01_female.mp3",
          "duration_sec": 25.392
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "今回の見出しは、Claude Fable 5.1 / Mythos 5.1 発表です。",
          "naration_text": "ニュースの見出しは「Claude Fable 5.1 / Mythos 5.1 発表」です。ここで大切なのは、一般的なClaudeの紹介ではなく、この二つの名前を持つ今回の発表そのものを扱うことです。発表では、長く続く作業への対応、開発支援の性能向上、そして性能改善によるコスト削減につながる方向性が示されています。",
          "audio": "audio/dlg_000_02_male.mp3",
          "duration_sec": 21.12
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "長い作業、開発、費用の考え方を、順番にやさしく整理していきます。",
          "naration_text": "この動画では、最初に発表の位置づけを確認し、次に長時間の自律作業とは何かを身近な例で説明します。そのあと、コーディングや試作品づくりへの期待、性能改善と費用の関係を取り上げます。最後に、料金や利用条件、生成された結果を人が確認する大切さも、忘れずに整理します。",
          "audio": "audio/dlg_000_03_female.mp3",
          "duration_sec": 22.176
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "便利さを期待しつつ、できることと利用条件は公式情報で確認しましょう。",
          "naration_text": "AIの新発表では、名前や見出しだけから使える範囲を決めつけない姿勢が重要です。利用できる機能、プラン、地域、料金、利用上限、提供時期は、公式発表と実際の展開状況により変わることがあります。今回も、期待できる方向性と、利用前に確認すべき事実を分けて見ていきましょう。",
          "audio": "audio/dlg_000_04_male.mp3",
          "duration_sec": 20.856
        }
      ],
      "duration_sec": 89.544
    },
    {
      "id": "scene_001",
      "title": "発表の概要",
      "accent": "#377f88",
      "accent_soft": "rgba(55, 127, 136, 0.18)",
      "kicker": "今回の個別ニュース",
      "headline": "Claude Fable 5.1 / Mythos 5.1\n何が発表されたのか",
      "image": "images/scene_001.png",
      "source_documents": [
        "https://www.anthropic.com/claude-fable-and-mythos-5-1"
      ],
      "source_summary": "今回の題材は、AnthropicによるClaude Fable 5.1 / Mythos 5.1の2026年9月1日の発表です。両者は同一の基盤モデルで、Fableは一般提供、Mythosは審査済み組織向けの信頼アクセス経由という安全策と提供経路に違いがあります。",
      "factual_bullets": [
        "発表元はAnthropic",
        "2026年9月1日の発表",
        "両者は同一の基盤モデル",
        "Fableは一般提供、Mythosは審査済み組織向けの信頼アクセス"
      ],
      "forbidden_elements": [
        "提供条件を断定する表現",
        "今回の発表にない機能の追加",
        "実在の人物・企業ロゴ・文字の描画"
      ],
      "image_prompt": "発表を示す抽象的なカード二枚と二人の案内役。文字、国旗、ロゴなし。青緑と深紺で端正に描く、日本語AIニュースの概要画面。",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "発表元はAnthropicで、今回の個別題材は二つの5.1の発表です。",
          "naration_text": "まず基本から確認します。発表元はAnthropicで、今回取り上げる個別の題材は Claude Fable 5.1 / Mythos 5.1 です。既存のAnthropicやClaudeに関する動画と混同しないよう、今回の見出しと字幕では、この二つの5.1の発表であることを明確にします。",
          "audio": "audio/dlg_001_01_female.mp3",
          "duration_sec": 20.04
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "公式発表では、長く続く問題解決や開発を支える方向性が示されました。",
          "naration_text": "公式発表で読み取れる大きな方向性は、短い質問に答えるだけでなく、長く続く問題解決や開発の仕事をAIが支えやすくすることです。具体的には、長時間の自律作業への対応、コーディング、プロトタイプ作成の性能向上、性能改善に伴うコスト削減につながる点が示されました。次の場面から、一つずつ言い換えて説明します。",
          "audio": "audio/dlg_001_02_male.mp3",
          "duration_sec": 22.704
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "両者は同一の基盤モデルで、安全策と提供経路が異なります。",
          "naration_text": "ここは二つの名称を混同しないことが大切です。公式発表によると、Claude Fable 5.1 と Mythos 5.1 は同一の基盤モデルで、安全策と提供経路が異なります。Fable 5.1 は一般提供され、Mythos 5.1 はサイバー防御や生命科学のための信頼アクセスを通じ、審査済みの組織などに限って提供されます。自分が使える条件は、試す前に公式の最新案内で確認してください。",
          "audio": "audio/dlg_001_03_female.mp3",
          "duration_sec": 29.544
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "今日は発表の要点を理解し、試すときの安全な考え方まで一緒に見ていきます。",
          "naration_text": "今回の解説は、特定の機能を無条件に勧めるものではありません。発表の要点を知り、自分の目的に使えそうかを考えるための入口です。作りたいもの、守りたい条件、途中で確認したいポイントを先に決めてから、小さな作業で試す。この流れを意識すると、新しいAIを落ち着いて活用しやすくなります。",
          "audio": "audio/dlg_001_04_male.mp3",
          "duration_sec": 21.144
        }
      ],
      "duration_sec": 93.432
    },
    {
      "id": "scene_002",
      "title": "長時間の自律作業",
      "accent": "#b7643c",
      "accent_soft": "rgba(183, 100, 60, 0.18)",
      "kicker": "長く続く作業",
      "headline": "大きな仕事を\n段取りよく進める",
      "image": "images/scene_002.png",
      "source_documents": [
        "https://www.anthropic.com/claude-fable-and-mythos-5-1"
      ],
      "source_summary": "発表では、長時間の自律作業への対応が示されています。",
      "factual_bullets": [
        "長時間の自律作業への対応",
        "調査・整理・下書きのような複数工程",
        "途中で人が確認する"
      ],
      "forbidden_elements": [
        "人の確認なしですべて終えるという断定",
        "処理時間や品質の保証"
      ],
      "image_prompt": "調査メモ、作業チェックリスト、資料の下書き、人による確認地点が連なる長時間のAI支援作業。文字や数値なし。暖かな橙と深い紺の落ち着いた構図。",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "長時間の自律作業は、大きな仕事を小さな工程に分けて進めるイメージです。",
          "naration_text": "長時間の自律作業という言葉は、少し難しく聞こえるかもしれません。初心者向けに言い換えると、調査する、資料を読む、要点を整理する、下書きを作る、といった複数の工程を、AIと順番に進めてもらうイメージです。一回の短い質問で終わらず、目的に向けて作業を続ける方向性が、今回の発表で示されています。",
          "audio": "audio/dlg_002_01_female.mp3",
          "duration_sec": 23.544
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "任せる前に、目的、守る条件、途中で確認する時点を具体的に伝えましょう。",
          "naration_text": "こうした作業を頼むときは、最初の指示が大切です。何を作りたいか、いつまでに必要か、使ってよい情報は何か、外部へ送ってはいけないものはあるかを具体的に伝えます。さらに、調査の後、下書きの後、実行前など、どこで人が確認するかを決めておくと、途中で方向がずれても修正しやすくなります。",
          "audio": "audio/dlg_002_02_male.mp3",
          "duration_sec": 21.024
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "調査結果や資料の下書きは、区切りごとに確かめれば安心して進められます。",
          "naration_text": "たとえば調査や資料作成では、AIに集めた情報を要約させたら、次の工程へ進む前に出典や内容を人が確認します。重要な数字、社外秘の情報、外部サービスへの送信、権限が関わる操作は特に慎重に扱いましょう。長い作業ほど、途中の小さな確認を重ねることが、最終結果の信頼性と安心感を支えます。",
          "audio": "audio/dlg_002_03_female.mp3",
          "duration_sec": 24.816
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "自律作業は放置ではなく、人とAIが役割を分けて前へ進むための仕組みです。",
          "naration_text": "自律作業は、AIが人間の確認なしにすべてを完了する、という意味ではありません。人が目的と判断基準を持ち、AIには調べる、整理する、案を作るといった役割を分けて任せる考え方です。AIの処理時間や成果の質は、指示、入力、利用環境、接続先に左右されるため、結果を確かめながら活用することが前提になります。",
          "audio": "audio/dlg_002_04_male.mp3",
          "duration_sec": 23.496
        }
      ],
      "duration_sec": 92.88
    },
    {
      "id": "scene_003",
      "title": "コーディングと試作品",
      "accent": "#9b5a53",
      "accent_soft": "rgba(155, 90, 83, 0.18)",
      "kicker": "開発を支える力",
      "headline": "アイデアから\n動く試作品へ",
      "image": "images/scene_003.png",
      "source_documents": [
        "https://www.anthropic.com/claude-fable-and-mythos-5-1"
      ],
      "source_summary": "発表では、コーディングとプロトタイプ作成の性能向上が示されています。",
      "factual_bullets": [
        "コーディング性能の向上",
        "プロトタイプ作成の性能向上",
        "コードと生成結果を確認する"
      ],
      "forbidden_elements": [
        "必ず正しいコードが生成されるという断定",
        "完成品が自動で完成するという断定"
      ],
      "image_prompt": "ワイヤーフレーム、コード編集画面、動作確認のプレビュー、人がレビューする場面。文字、ロゴ、数値なし。紺と赤茶の洗練された日本語AIニュース向けイラスト。",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "コーディングと試作品づくりの性能向上も、今回の発表の大切なポイントです。",
          "naration_text": "発表では、コーディングやプロトタイプ作成の性能向上も大切なポイントとして示されました。プロトタイプは、完成品の前に作る、動きや使い方を試すための小さな試作品です。アイデアを言葉で伝え、まず動く形にして、確認しながら直していく流れを、AIが支えやすくなる方向性として捉えられます。",
          "audio": "audio/dlg_003_01_female.mp3",
          "duration_sec": 22.032
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "最初から大作を頼まず、画面や機能を小さく分けて試すのが初心者にもおすすめです。",
          "naration_text": "初めて開発を頼むなら、最初から大きなアプリ全体を任せるより、機能を小さく分ける方法がおすすめです。たとえば、画面を一つ表示する、入力した内容を保存する、一覧に表示する、といった単位から始めます。作りたい見た目、利用者の操作、守るべきデータの扱いを順に伝えると、確認と改善を繰り返しやすくなります。",
          "audio": "audio/dlg_003_02_male.mp3",
          "duration_sec": 22.296
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "生成されたコードは、動作だけでなく安全性、権限、既存機能への影響も人が確認します。",
          "naration_text": "AIが生成したコードは、動いたとしても、そのまま本番へ反映してよいとは限りません。入力内容の扱いに問題はないか、権限が広すぎないか、秘密の情報を含めていないか、既存の機能を壊していないかを確認してください。テストを行い、変更内容を理解したうえで使うことが、開発を安全に進めるための基本です。",
          "audio": "audio/dlg_003_03_female.mp3",
          "duration_sec": 23.136
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "小さく作り、試して、直す回転を速くすることがAI活用の現実的なねらいです。",
          "naration_text": "性能向上の価値は、AIにすべてを任せきることではなく、試作と確認の回転を速くできる可能性にあります。案を作り、実際に動かし、気づいた点を言葉で返して改善する。この短い循環を重ねれば、アイデアから使える形へ近づく速度を上げやすくなります。最終的な設計と責任ある判断は、利用者が担うことを忘れないでください。",
          "audio": "audio/dlg_003_04_male.mp3",
          "duration_sec": 23.04
        }
      ],
      "duration_sec": 90.504
    },
    {
      "id": "scene_004",
      "title": "性能改善とコスト",
      "accent": "#7c5d6d",
      "accent_soft": "rgba(124, 93, 109, 0.18)",
      "kicker": "性能と費用",
      "headline": "性能改善が\nコスト削減につながる可能性",
      "image": "images/scene_004.png",
      "source_documents": [
        "https://www.anthropic.com/claude-fable-and-mythos-5-1"
      ],
      "source_summary": "性能改善によるコスト削減につながる点が、発表の要点として示されています。",
      "factual_bullets": [
        "性能改善によるコスト削減につながる方向性",
        "実測効果は利用者ごとに異なる",
        "料金や利用条件は確認が必要"
      ],
      "forbidden_elements": [
        "必ず安くなるという断定",
        "利用者全員で同じ効果が出るという断定"
      ],
      "image_prompt": "効率よく進むAI作業の流れ、控えめなグラフ形状、人による比較メモ。文字、金額、数値、ロゴなし。紫がかった紺と橙で上品な日本語AIニュース用画面。",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "性能改善がコスト削減につながるという点も、公式発表で示された要点です。",
          "naration_text": "もう一つの注目点は、性能改善がコスト削減につながるという方向性です。作業のやり直しが減ったり、同じ目的により少ない手間で近づけたりすれば、時間や費用の負担を下げられる可能性があります。ここでいうのは発表で示された方向性であり、すべての利用者に同じ結果を約束するものではありません。",
          "audio": "audio/dlg_004_01_female.mp3",
          "duration_sec": 21.648
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "実際に得られる効果は、作業内容、料金、指示、利用環境によって変わります。",
          "naration_text": "実際の効果は、何を作るか、どのくらい試行するか、どの料金体系を使うか、どんな指示を出すかによって変わります。入力の質、利用上限、外部サービスとの接続、確認にかかる時間も影響します。性能が上がったという発表内容と、自分の仕事でいくら節約できたかという実測結果は、同じものとして扱わずに考えることが大切です。",
          "audio": "audio/dlg_004_02_male.mp3",
          "duration_sec": 23.136
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "導入を考えるなら、小さな仕事で時間、品質、確認の手間、料金を比べてみましょう。",
          "naration_text": "導入を考えるなら、まずは小さく比べるのが確実です。たとえば一つの調査、短い資料の下書き、小さな画面の試作などを選びます。従来の方法と比べて、かかった時間、できあがった内容の質、確認や修正の手間、実際の料金を記録してみましょう。自分の環境で得た結果なら、次に広げるかどうかを落ち着いて判断できます。",
          "audio": "audio/dlg_004_03_female.mp3",
          "duration_sec": 24.936
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "発表の期待と実際の利用結果を分けて見れば、AIの価値を正しく判断できます。",
          "naration_text": "新しいモデルの発表は、これから試せることのヒントになります。しかし、費用だけを急いで比べるのではなく、成果物の正確さ、修正の必要性、確認に要する時間も含めて見ましょう。期待を持ちながらも、自分の目的に合うかを測る。この姿勢なら、性能改善とコスト削減という話題を、実務に役立つ判断材料へ変えられます。",
          "audio": "audio/dlg_004_04_male.mp3",
          "duration_sec": 22.728
        }
      ],
      "duration_sec": 92.448
    },
    {
      "id": "scene_005",
      "title": "利用前の留保事項",
      "accent": "#5d6178",
      "accent_soft": "rgba(93, 97, 120, 0.18)",
      "kicker": "使う前の確認",
      "headline": "期待と確認事項を\nきちんと分ける",
      "image": "images/scene_005.png",
      "source_documents": [
        "https://www.anthropic.com/claude-fable-and-mythos-5-1"
      ],
      "source_summary": "Fable 5.1 と Mythos 5.1 は同一の基盤モデルで、安全策と提供経路が異なります。料金・利用上限・地域・生成結果は、利用前と利用中に確認する必要があります。",
      "factual_bullets": [
        "Fableは一般提供、Mythosは信頼アクセスを通じた審査済み組織向け",
        "料金・利用上限・地域を確認する",
        "重要な操作と生成結果は人が確認する"
      ],
      "forbidden_elements": [
        "誰でも無条件に使えるという表現",
        "常に高品質または正確という断定"
      ],
      "image_prompt": "チェックリスト、盾、人の承認、AI作業の流れを抽象的に表す利用前確認の画面。文字、ロゴ、数値なし。静かな紺と灰紫、控えめな橙の信頼感ある構図。",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "Fableは一般提供、Mythosは審査済み組織向けの信頼アクセスです。",
          "naration_text": "利用する前には、Claude Fable 5.1 と Mythos 5.1 の提供経路を確認しましょう。公式発表では、両者は同一の基盤モデルですが、Fable 5.1 は一般提供、Mythos 5.1 はサイバー防御や生命科学のための信頼アクセスを通じた、審査済み組織向けの提供と説明されています。地域、プラン、利用上限などは変わり得るため、公式発表、公式サイト、管理画面などの最新情報で自分の条件に合うかを確かめてください。",
          "audio": "audio/dlg_005_01_female.mp3",
          "duration_sec": 31.632
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "料金、利用上限、性能値、対応条件は変わるため、使う直前の最新情報が必要です。",
          "naration_text": "料金、利用上限、具体的な性能値、対応条件は、今後変更される可能性があります。また、性能評価の結果があっても、それは特定の条件で測られた情報です。自分の仕事で同じ時間、費用、品質になるとは限りません。使う直前に最新の公式情報を確認し、必要なら小さな検証を行ってから、重要な用途へ広げるようにしましょう。",
          "audio": "audio/dlg_005_02_male.mp3",
          "duration_sec": 24.96
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "権限の変更、コードの反映、外部送信、最終成果物は、必ず利用者が確認します。",
          "naration_text": "AIが長い作業を支援できるようになっても、重要な操作を無確認で進めてはいけません。権限を変える操作、コードの本番反映、個人情報や機密情報を含む外部送信、契約や公開に関わる最終成果物は、利用者が内容を確認して判断してください。AIは便利な支援役ですが、責任を持って決める役割まで代わるわけではありません。",
          "audio": "audio/dlg_005_03_female.mp3",
          "duration_sec": 24.72
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "条件を確かめ、途中と最後の結果を見直す習慣が、安心できるAI活用につながります。",
          "naration_text": "確認は、AIを使わないためのブレーキではありません。目的に合わない結果や予想外の影響に早く気づき、よりよい使い方へ直すための習慣です。使える条件を知り、途中の成果を確認し、最後の出力も自分の目で確かめる。その積み重ねがあれば、新しい機能を取り入れながら、安心して仕事や開発に役立てられます。",
          "audio": "audio/dlg_005_04_male.mp3",
          "duration_sec": 21.552
        }
      ],
      "duration_sec": 102.864
    },
    {
      "id": "scene_999",
      "title": "まとめ",
      "accent": "#c96e35",
      "accent_soft": "rgba(201, 110, 53, 0.18)",
      "layout": "hero",
      "kicker": "まとめ",
      "headline": "新しいAIを\n確かめながら使おう",
      "image": "images/scene_999.png",
      "source_documents": [
        "https://www.anthropic.com/claude-fable-and-mythos-5-1"
      ],
      "source_summary": "Claude Fable 5.1とClaude Mythos 5.1は同一の基盤モデルで、安全策と提供経路が異なります。発表内容と利用時の確認事項をまとめます。",
      "factual_bullets": [
        "2026年9月1日の発表",
        "同一の基盤モデルに異なる安全策と提供経路",
        "性能改善と条件・結果の確認"
      ],
      "forbidden_elements": [
        "無条件の利用保証",
        "品質・費用・完全自律の保証"
      ],
      "image_prompt": "二人の案内役、AI支援の作業の光、人による確認マーク、前向きな地平線。文字、ロゴ、数値なし。橙と深紺を基調にした希望のある日本語AIニュースの締めくくり。",
      "dialogue": [
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "今回の発表は、長い作業や開発をAIと進めやすくする方向性を示しました。",
          "naration_text": "今日は、Anthropic が2026年9月1日に発表した Claude Fable 5.1 / Mythos 5.1 を見てきました。確認できる要点は、長時間の自律作業への対応、コーディングとプロトタイプ作成の性能向上、性能改善によるコスト削減につながる方向性です。短い質問だけでなく、長く続く作業や開発をAIと進める未来を考える発表でした。",
          "audio": "audio/dlg_999_01_female.mp3",
          "duration_sec": 26.016
        },
        {
          "speaker": "male",
          "expression": "neutral",
          "telop_text": "安全策と提供経路、料金、利用条件、実際の結果は分けて確認しましょう。",
          "naration_text": "一方で、両者は同一の基盤モデルでありながら、安全策と提供経路が異なります。Fable 5.1 は一般提供、Mythos 5.1 は審査済み組織向けの信頼アクセスです。地域、料金、利用上限、性能値は、公式情報と利用時点の状況を確認する必要があります。作業の品質、処理時間、費用の効果も、指示や利用環境によって変わるため、重要な操作、コード、生成結果は人が確認するという原則を大切にしましょう。",
          "audio": "audio/dlg_999_02_male.mp3",
          "duration_sec": 30.288
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "目的と条件を伝え、小さく試して結果を確かめることから、新しいAIを始めましょう。",
          "naration_text": "新しいAIを使い始めるときは、作りたいものと守る条件を具体的に伝え、小さな作業から試すのがおすすめです。途中で確認する場所を決め、最後の結果も自分で見直せば、便利さを生かしながら安心して改善を重ねられます。ニュースで可能性を知り、自分の環境で確かめていくことが、無理のない活用への近道です。",
          "audio": "audio/dlg_999_03_female.mp3",
          "duration_sec": 22.872
        },
        {
          "speaker": "female",
          "expression": "neutral",
          "telop_text": "AiDiyで最新AIニュースを作ろう。チャンネル登録もよろしくお願いします！",
          "naration_text": "この動画は AiDiy のニュース版ビデオ生成機能で自動生成されました。内容が役に立ったら、ぜひチャンネル登録をお願いします。自分でも AiDiy で最新AIニュースの解説ビデオを作ってみて。確認を大切にしながら、新しい発表を楽しく前向きに追いかけ、あなたらしい学びやものづくりにつなげていきましょう！",
          "audio": "audio/dlg_999_04_female.mp3",
          "duration_sec": 21.912
        }
      ],
      "duration_sec": 101.088
    }
  ],
  "total_duration_sec": 662.76
};
