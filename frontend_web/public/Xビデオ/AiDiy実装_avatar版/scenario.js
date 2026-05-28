window.SCENARIO = {
  "project_name": "AiDiy avatar版実装例",
  "version": "take3",
  "title": "avatar版 AiDiy 実装例",
  "source": {
    "type": "screen_capture",
    "summary": "AiDiy の frontend_avatar（Electron/Web デュアルモード + VRM アバター）の実際の画面キャプチャを使って主要機能を紹介する。"
  },
  "target": {
    "language": "ja-JP",
    "format": "html_css_scene_player_with_media",
    "tone": "AIアバターシステム紹介、先進的、使いたくなる",
    "goal": "frontend_avatar の主要画面を実際の画面キャプチャで紹介する。"
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
      "title": "avatar版 AiDiy の紹介",
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196, 155, 255, 0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "AVATAR CLIENT",
      "headline": "avatar版 AiDiy の\n画面を紹介します",
      "lead": "Electron デスクトップと Web ブラウザの両方で動く AI アバタークライアント。実際の画面でログインから AI コアまでご覧ください。",
      "subtitle": "avatar版 AiDiy の主要画面と機能を順番にご紹介します。",
      "image": "images/scene_000.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "short_narration": "avatar版 AiDiy は、AI 画面にアバター表示を組み合わせたクライアントです。",
      "long_narration": "この動画では、AiDiy の avatar版を紹介します。avatar版は、AI チャットやコード支援の画面に、VRM アバター表示を組み合わせたクライアントです。Electron のデスクトップアプリとしても動き、ブラウザから 8099 番ポートへアクセスして使うこともできます。画面にはアバター、チャット、コード、ファイル、ライブキャプチャ、設定などが登場します。アバターはただ横に置いてあるだけではなく、音声出力に合わせて口を動かしたり、表示モードを切り替えたりできます。最初に全体像を確認し、ログイン、AI コア画面、表示切替、コード作業、画面共有、設定、Web 表示の順に見ていきます。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 5.568,
      "long_start_sec": 0.0,
      "long_duration_sec": 43.032
    },
    {
      "id": "scene_991",
      "title": "avatar版 AiDiy の概要",
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196, 155, 255, 0.18)",
      "kicker": "OVERVIEW",
      "headline": "Electron / Web デュアルモードの\nAI アバタークライアント",
      "lead": "Vue 3 + Three.js + VRM で構築した AI アバタークライアント。Electron デスクトップアプリとしても Web ブラウザとしても動作します。",
      "subtitle": "Electron / Web デュアルモード + VRM アバター + AI コア統合システムです。",
      "image": "images/scene_001.png",
      "chips": [
        "Vue 3 / Vite",
        "TypeScript",
        "Electron",
        "Three.js",
        "VRM / VRMA",
        "AI コア"
      ],
      "metrics": [
        {
          "label": "Avatar Web",
          "value": "port 8099"
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
          "title": "デュアルモード",
          "lines": [
            "Electron: デスクトップ常駐アプリ",
            "Web: ブラウザで直接アクセス",
            "window.desktopApi の有無で自動判定"
          ]
        },
        {
          "title": "VRM アバター",
          "lines": [
            "Three.js + @pixiv/three-vrm でレンダリング",
            "xneko・xeyes など表示種別を切り替え可能",
            "音声リップシンク対応"
          ]
        }
      ],
      "facts": [
        "window.desktopApi の有無で Electron モードと Web モードを自動判定する。",
        "Electron は localStorage、Web は sessionStorage で認証トークンを管理する。",
        "表示種別はアバター・xneko・xeyes・時計・カレンダー・表示無しの 7 種類。"
      ],
      "evidence": [],
      "short_narration": "Electron と Web の両方で動き、VRM 表示と AI コアをまとめて扱います。",
      "long_narration": "概要画面では、avatar版 AiDiy の技術構成を整理しています。画面には Electron と Web のデュアルモード、VRM アバター、ポート 8099、Vue 3、TypeScript、Three.js などが示されています。Electron モードではデスクトップアプリとして常駐し、複数ウィンドウや透明ウィンドウなど、デスクトップ向けの動きが使えます。Web モードではブラウザからアクセスできるので、インストールせずに試せます。モードの判定には window.desktopApi の有無を使い、認証情報の保存先も切り替えます。Electron では localStorage、Web では sessionStorage を使います。アバター描画は Three.js と VRM ライブラリで行い、音声に合わせた口パク、まばたき、ゆるい体の動きも入ります。つまり avatar版は、AI と会話する画面を、より見える形、聞こえる形にするためのクライアントです。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_start_sec": 5.568,
      "short_duration_sec": 6.048,
      "long_start_sec": 43.032,
      "long_duration_sec": 57.024
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
      "subtitle": "ログイン後は権限に応じた画面が表示されます。",
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
            "Electron: localStorage にトークン保存",
            "Web: sessionStorage にトークン保存",
            "401 エラーで自動ログアウト"
          ]
        }
      ],
      "facts": [
        "ログイン後 JWT トークンが発行され、Electron は localStorage、Web は sessionStorage に保存される。",
        "401 エラーを Axios interceptor が検知し、自動でログアウト処理を行う。",
        "Web モードはタブを閉じると sessionStorage が消えてセッションが終了する。"
      ],
      "evidence": [],
      "short_narration": "利用者 ID とパスワードでログインし、実行モードに合わせて認証情報を保存します。",
      "long_narration": "ここは AiDiy Avatar のログイン画面です。背景の上に小さなログインカードがあり、利用者 ID とパスワードを入力します。ログインに成功すると JWT トークンが発行され、以後の API 呼び出しに使われます。avatar版の特徴は、Electron モードと Web モードで保存先を分けていることです。Electron モードでは localStorage に保存し、デスクトップアプリとして続けて使いやすくします。Web モードでは sessionStorage に保存し、ブラウザのタブを閉じるとセッションが終わる形にします。同じ画面に見えても、実行環境に合わせて安全性と使い勝手を変えています。ログイン後は、アバター表示と AI コアの各パネルを使える状態になります。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_start_sec": 11.616,
      "short_duration_sec": 6.192,
      "long_start_sec": 100.056,
      "long_duration_sec": 45.024
    },
    {
      "id": "scene_003",
      "title": "AiDiy 画面",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.18)",
      "kicker": "AIDIY SCREEN",
      "headline": "左端のボタンで\n表示パネルを切り替えられます",
      "lead": "AiDiy 画面の左端にあるボタンで各パネルの表示・非表示を切り替えます。チャット画面やライブ会話を使って AI と対話できます。",
      "subtitle": "左端ボタンでパネルの表示オンオフ、チャット・ライブ会話が選べます。",
      "image": "images/scene_003.png",
      "chips": [
        "パネル切り替え",
        "CHAT_AI",
        "LIVE_AI",
        "表示オンオフ"
      ],
      "metrics": [
        {
          "label": "パネル制御",
          "value": "左端ボタン"
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
            "左端のボタンで各パネルをオンオフ",
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
        "左端のボタンクリックで各パネルの表示・非表示を切り替えられる。",
        "CHAT_AI でテキストチャット、LIVE_AI で音声リアルタイム対話ができる。",
        "LIVE_AI の返答はアバターがリップシンクしながら声で読み上げる。"
      ],
      "evidence": [],
      "short_narration": "チャット画面とアバターを同時に使い、音声に合わせて口も動きます。",
      "long_narration": "このシーンでは、AI チャット画面とアバター表示が同時に出ています。左側には AI との会話パネルがあり、右側にはアバター表示のウィンドウがあります。チャットでは文字で質問できますし、LIVE_AI を使うと音声でリアルタイムに対話できます。音声が再生されると、アバターの口が音量に合わせて動きます。これは、音声プレイヤーの音を AudioContext と AnalyserNode で読み取り、VRM の表情値に反映しているためです。単に音が流れるだけではなく、画面上のキャラクターが話しているように見えるので、長い説明でも状態が分かりやすくなります。右側の操作パネルでは、表示するアバターやモードを選べます。AI コアの機能とアバター演出が、別々の飾りではなく同じ作業画面の中でつながっています。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_start_sec": 17.808,
      "short_duration_sec": 5.16,
      "long_start_sec": 145.08,
      "long_duration_sec": 50.544
    },
    {
      "id": "scene_004",
      "title": "アバター切替（xneko・xeyes など）",
      "expression": "neutral",
      "accent": "#ff6bd6",
      "accent_soft": "rgba(255, 107, 214, 0.18)",
      "kicker": "AVATAR MODE",
      "headline": "アバターの表示種別を\n自由に切り替えられます",
      "lead": "VRM アバターだけでなく、xneko（走る猫）・xeyes（目が追う）・時計・カレンダーなど 7 種類の表示に切り替えられます。",
      "subtitle": "7 種類の表示種別をワンクリックで切り替えられます。",
      "image": "images/scene_004.png",
      "chips": [
        "アバター（VRM）",
        "xneko",
        "xeyes",
        "アナログ時計",
        "デジタル時計",
        "カレンダー",
        "表示無し"
      ],
      "metrics": [
        {
          "label": "表示種別",
          "value": "7 種類"
        },
        {
          "label": "切り替え",
          "value": "ワンクリック"
        }
      ],
      "cards": [
        {
          "title": "表示種別一覧",
          "lines": [
            "アバター（VRM）: 3D キャラクター",
            "xneko: 画面を走り回る猫",
            "xeyes: カーソルを追いかける目"
          ]
        },
        {
          "title": "その他の表示",
          "lines": [
            "アナログ時計: クラシックな時計表示",
            "デジタル時計: シンプルな数字時計",
            "カレンダー: 月間カレンダー表示",
            "表示無し: アバターエリアを非表示"
          ]
        }
      ],
      "facts": [
        "表示種別はアバター・xneko・xeyes・アナログ時計・デジタル時計・カレンダー・表示無しの 7 種類。",
        "xneko はデスクトップ上を猫が走り回るクラシックなデスクトップマスコット。",
        "xeyes はカーソルの動きを目が追いかけるデスクトップウィジェット。"
      ],
      "evidence": [],
      "short_narration": "表示種別は VRM、時計、カレンダー、xneko、xeyes などから選べます。",
      "long_narration": "avatar版のアバターエリアは、VRM キャラクターだけに固定されていません。画像にあるように、カレンダーやデジタル時計のような実用表示にも切り替えられます。表示種別には、アバター、xneko、xeyes、アナログ時計、デジタル時計、カレンダー、表示無しがあります。作業に集中したいときは小さな時計やカレンダー、対話している感じを出したいときは VRM アバター、軽いデスクトップウィジェットとして使いたいときは xneko や xeyes、というように選べます。表示無しも用意されているので、必要ないときは消して画面を広く使えます。これは見た目の遊びだけではなく、デスクトップ上で AI 支援を邪魔にならない形に変えるための機能です。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_start_sec": 22.968,
      "short_duration_sec": 6.024,
      "long_start_sec": 195.624,
      "long_duration_sec": 44.04
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
        "各コードパネルは独立した AI との会話を持つ。",
        "チャット画面と組み合わせることで、設計と実装を並行して進められる。"
      ],
      "evidence": [],
      "short_narration": "コード画面は最大 6 パネル。アバターを横に置いたまま作業できます。",
      "long_narration": "この画面では、複数のコード用ウィンドウとアバターが同時に表示されています。CODE_AI は最大 6 パネルまで開け、それぞれが独立した会話を持ちます。一つのパネルではフロントエンドの修正、別のパネルではバックエンド API、さらに別のパネルではテストや調査、というように役割を分けられます。ウィンドウが重なって表示されているのは、デスクトップアプリとして複数の作業窓を持てることを示しています。アバターは右側に残り、AI の音声応答や状態を視覚的に伝えます。文字だけのチャットでは、どの作業をどの AI に頼んだのか分かりにくくなることがあります。avatar版では、作業ごとに窓を分け、アバター表示も合わせて使うことで、複数の作業を整理しながら進められます。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_start_sec": 28.992,
      "short_duration_sec": 5.496,
      "long_start_sec": 239.664,
      "long_duration_sec": 48.12
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
      "short_narration": "ファイル、コード、ライブキャプチャ、アバターを同時に表示できます。",
      "long_narration": "このシーンでは、ファイル画面、コード画面、ライブキャプチャ、アバター表示が同時に出ています。左上のファイル画面では、プロジェクト内のファイルやフォルダを確認できます。中央にはコード用の AI パネル、左下にはライブキャプチャがあります。ライブキャプチャは、今見ている画面を AI に渡して、文字だけでは説明しにくい状況を共有するためのものです。たとえば、画面のどこにエラーが出ているか、ボタンがどの位置にあるか、レイアウトが崩れているか、といった情報は、画像として見せた方が伝わりやすくなります。右側のアバターは対話の相手として表示され、音声応答がある場合は口の動きも反映されます。ファイルを見て、画面を共有し、コードを直し、アバターから反応を受け取る。この一連の作業を、ひとつのデスクトップ環境で進められるのが avatar版の強みです。",
      "short_audio": "audio/short_scene_006.mp3",
      "long_audio": "audio/long_scene_006.mp3",
      "short_start_sec": 34.488,
      "short_duration_sec": 4.8,
      "long_start_sec": 287.784,
      "long_duration_sec": 53.544
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
      "short_narration": "設定画面でチャット、ライブ会話、コード支援の AI を個別に選びます。",
      "long_narration": "設定画面では、avatar版から使う AI の種類やモデルをまとめて選べます。画面には CHAT_AI、LIVE_AI、CODE_AI などの項目があり、チャット用、音声対話用、コード支援用を別々に設定できます。たとえば、文字で相談する AI、声で話す AI、コードを書く AI を同じものにする必要はありません。用途に合うものを選べます。下部には規定値保存、設定再起動、リセット再起動などの操作があります。設定を変えたあと、必要なサービスへ反映するためのボタンです。デスクトップアプリでは、AI モデルや接続先を試しながら作業する場面が多くなります。そのため、設定ファイルを探して直接編集するだけでなく、画面から確認し、保存し、反映できることが大切です。画像に映っているように、多くの設定項目を一画面で見渡せるので、今どの AI を使う状態なのかを確認しやすくなっています。",
      "short_audio": "audio/short_scene_007.mp3",
      "long_audio": "audio/long_scene_007.mp3",
      "short_start_sec": 39.288,
      "short_duration_sec": 5.688,
      "long_start_sec": 341.328,
      "long_duration_sec": 59.376
    },
    {
      "id": "scene_008",
      "title": "Web 表示（port 8099）",
      "expression": "neutral",
      "accent": "#00e0b8",
      "accent_soft": "rgba(0, 224, 184, 0.18)",
      "kicker": "WEB MODE",
      "headline": "左右 2 画面をタブで切り替える\nシンプルな Web インターフェース",
      "lead": "ブラウザで localhost:8099 にアクセスするだけで起動します。左のアバター画面と右のチャット・コード画面をタブで切り替えるシンプルな構成です。",
      "subtitle": "左アバター画面と右タブ画面をワンクリックで切り替えられます。",
      "image": "images/scene_008.png",
      "chips": [
        "port 8099",
        "左アバター画面",
        "右タブ画面",
        "タブ切り替え",
        "シンプル UI"
      ],
      "metrics": [
        {
          "label": "アクセス",
          "value": "localhost:8099"
        },
        {
          "label": "画面構成",
          "value": "左右 2 画面"
        }
      ],
      "cards": [
        {
          "title": "左右 2 画面構成",
          "lines": [
            "左画面: アバター（VRM・xneko 等）表示",
            "右画面: チャット・コード・ファイル等のタブ",
            "タブクリックで左右をワンクリック切り替え"
          ]
        },
        {
          "title": "シンプルインターフェース",
          "lines": [
            "Electron インストール不要",
            "ブラウザだけで全機能を利用可能",
            "sessionStorage でセッション管理"
          ]
        }
      ],
      "facts": [
        "ブラウザで localhost:8099 にアクセスするだけで avatar版 AiDiy が起動する。",
        "左のアバター画面と右のタブ画面をタブで切り替えるシンプルな 2 画面構成。",
        "Electron をインストールせずとも全機能を利用できる。"
      ],
      "evidence": [],
      "short_narration": "Web モードは localhost 8099 を開き、タブで各パネルを切り替えます。",
      "long_narration": "Web モードでは、ブラウザで localhost 8099 にアクセスするだけで avatar版 AiDiy を開けます。画像では、上部にタブが並び、左側にアバター、右側にチャットやコードなどのパネルが表示されています。Electron をインストールしなくても使えるので、まず試したい人や、チーム内で画面を共有したい場合に便利です。Electron モードでは複数ウィンドウを活かしたデスクトップ体験になりますが、Web モードではブラウザの一画面に整理されます。アバターを表示しながら、チャット、コード、ファイル、設定などをタブで切り替えるため、画面構成が分かりやすくなります。認証情報は sessionStorage に保存され、タブを閉じるとセッションが切れる設計です。デスクトップアプリの機能を、ブラウザでも確認できる入口として使えます。",
      "short_audio": "audio/short_scene_008.mp3",
      "long_audio": "audio/long_scene_008.mp3",
      "short_start_sec": 44.976,
      "short_duration_sec": 5.952,
      "long_start_sec": 400.704,
      "long_duration_sec": 49.488
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
      "headline": "ご視聴ありがとうございました。\nAiDiy アバターで何を作りますか？",
      "lead": "Electron とブラウザの両方で動く VRM アバター + AI コアの組み合わせで、まったく新しい体験を創ってください。",
      "subtitle": "AiDiy アバターで何を作りますか？",
      "image": "images/scene_999.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "short_narration": "AIに声と姿を。あなたもAiDiyとシステムづくりしてみませんか？",
      "long_narration": "ここまで avatar版 AiDiy を見てきました。ログインして、AI と会話し、アバターを表示し、必要に応じて時計やカレンダーなどへ切り替え、コード作業やファイル確認、ライブキャプチャも同じ環境で扱えます。Electron モードではデスクトップアプリとして複数ウィンドウを使い、Web モードではブラウザから一画面で使えます。VRM アバターは音声に合わせて口を動かし、AI の返答をただの文字ではなく、見える反応として受け取れるようにします。AI 支援は便利ですが、長い作業では画面のどこで何が起きているかを見失いやすくなります。avatar版は、AI とのやり取りをもっと分かりやすく、作業のそばに置くための形です。自分の作業に合わせて、アバター、コード、ファイル、画面共有を組み合わせて使ってください。あなたもAiDiyとシステムづくりしてみませんか？",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_start_sec": 50.928,
      "short_duration_sec": 5.496,
      "long_start_sec": 450.192,
      "long_duration_sec": 52.8
    }
  ],
  "short_duration_sec": 56.424,
  "long_duration_sec": 502.992
};
