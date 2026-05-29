window.SCENARIO = {
  "project_name": "AiDiy紹介avatar",
  "version": "avatar",
  "title": "AiDiy - frontend_avatar 紹介",
  "source": {
    "type": "agents_and_knowledge",
    "summary": "frontend_avatar/AGENTS.md と .aidiy/knowledge の関連ファイルから実装実態を抜粋して構成。"
  },
  "target": {
    "language": "ja-JP",
    "format": "html_avatar_presenter_with_media",
    "tone": "高校生にもわかる、使う楽しさ重視、やさしい説明",
    "goal": "AI と話す時間にアバターがいる楽しさ、ブラウザとデスクトップで使える便利さ、自分好みに表示を変えられる体験を伝える。"
  },
  "assets_policy": {
    "visual_style": "left_avatar_38_right_content_62",
    "audio_dir": "audio",
    "image_dir": "images",
    "avatar": "../vrm/VRM_AiDiy.vrm",
    "tts_provider": "freeai:female"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "この動画で紹介すること",
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "INTRODUCTION",
      "headline": "この動画では、frontend_avatar の\n位置づけと仕組みを紹介します",
      "lead": "AIコア専用クライアント、Electron / Web 両対応、VRM アバター、表示選択、状態同期までを短く見ていきます。",
      "subtitle": "この動画では、frontend_avatar の位置づけ、技術、ウィンドウ設計、VRM/VRMA、表示選択を紹介します。",
      "image": "images/scene_000.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "short_narration": "AiDiy のアバターは、AI と話す時間を楽しくしてくれる相棒です。作業の横で表情や動きで反応します。",
      "long_narration": "この動画では、AiDiy のアバターを、使う人の目線で紹介します。むずかしい仕組みよりも、AI と話すときにキャラクターがそばにいる楽しさ、ブラウザでもデスクトップでも使える便利さ、自分好みに表示を変えられるところを見ていきます。アバターは VRM 形式の 3D モデルで、表情・モーション・リップシンクすべてをリアルタイムに動かします。Electron と Web の両モードを一枚の renderer で共有しているので、どちらでも同じアバターが迎えてくれます。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 8.304,
      "long_start_sec": 0.0,
      "long_duration_sec": 30.168
    },
    {
      "id": "scene_001",
      "title": "AIコア専用クライアント",
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125, 255, 179, 0.18)",
      "kicker": "ROLE",
      "headline": "Electron と Web で\n同じ renderer が動く",
      "lead": "frontend_avatar は AIコア専用の Avatar クライアントです。判定は window.desktopApi の有無で切り替わります。",
      "subtitle": "AIコア専用 Avatar クライアント。Electron / Web 両対応で、同じ renderer を使う。",
      "image": "images/scene_001.png",
      "chips": [
        "AIコア専用",
        "Electron",
        "Web ブラウザ",
        "window.desktopApi で判定"
      ],
      "metrics": [
        {
          "label": "対応モード",
          "value": "2"
        },
        {
          "label": "判定",
          "value": "desktopApi"
        },
        {
          "label": "認証 storage",
          "value": "local / session"
        }
      ],
      "cards": [
        {
          "title": "Electron モード",
          "lines": [
            "BrowserWindow を role 別に持つ",
            "認証は localStorage",
            "パネルは IPC で show / hide"
          ]
        },
        {
          "title": "Web モード",
          "lines": [
            "左アバター + 右タブの単一ページ",
            "認証は sessionStorage",
            "パネルはアクティブタブで表現"
          ]
        }
      ],
      "facts": [
        "frontend_avatar は AIコア専用の Avatar クライアントである。",
        "Electron / Web の判定は !!window.desktopApi で行う。",
        "Web 認証は sessionStorage、Electron 認証は localStorage を使う。"
      ],
      "evidence": [
        {
          "source": "frontend_avatar/AGENTS.md",
          "text": "frontend_avatar は AIコア専用の Avatar クライアントです。Electron デスクトップアプリと通常 Web ブラウザの両方で動作します。"
        }
      ],
      "short_narration": "ブラウザでもデスクトップでも、AI の相棒を呼び出せます。作業の横に置いておけるのがポイントです。",
      "long_narration": "このアバター画面は、AI と話すための入り口です。ブラウザで開いても、デスクトップアプリとして起動しても使えます。たとえば調べものをしながら質問したり、アイデア出しの横に置いたりできます。どのモードでも、AI が画面の中の相棒として近くにいる感じを目指しています。モードの切り替えは window.desktopApi の有無だけで自動判定され、認証情報の保存先も Electron なら localStorage、Web なら sessionStorage に自動で切り替わります。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_start_sec": 8.304,
      "short_duration_sec": 7.296,
      "long_start_sec": 30.168,
      "long_duration_sec": 31.248
    },
    {
      "id": "scene_002",
      "title": "技術スタック",
      "expression": "neutral",
      "accent": "#ff6bd6",
      "accent_soft": "rgba(255, 107, 214, 0.18)",
      "kicker": "TECH STACK",
      "headline": "Vue 3 + Three.js + @pixiv/three-vrm を中核に、\nElectron が周りを包む",
      "lead": "renderer は Vue 3 + Vite + TypeScript。Three.js と @pixiv/three-vrm シリーズで VRM を描画し、Electron が複数ウィンドウを束ねます。",
      "subtitle": "Vue 3 / Vite / TypeScript / Three.js / @pixiv/three-vrm / @pixiv/three-vrm-animation / Electron / WebSocket / BroadcastChannel / Monaco Editor。",
      "image": "images/scene_002.png",
      "chips": [
        "Vue 3 + Vite + TS",
        "Three.js",
        "@pixiv/three-vrm",
        "@pixiv/three-vrm-animation",
        "Electron",
        "WebSocket",
        "BroadcastChannel",
        "Monaco Editor"
      ],
      "metrics": [
        {
          "label": "Renderer",
          "value": "Vue 3"
        },
        {
          "label": "3D",
          "value": "Three.js + VRM"
        },
        {
          "label": "通信",
          "value": "REST + WS"
        }
      ],
      "cards": [
        {
          "title": "Renderer",
          "lines": [
            "Vue 3 + Vite + TypeScript",
            "src/AiDiy.vue が状態の中心",
            "Vue Router / Pinia 中心ではない"
          ]
        },
        {
          "title": "3D / VRM",
          "lines": [
            "Three.js でレンダリング",
            "@pixiv/three-vrm でモデル読込",
            "@pixiv/three-vrm-animation で VRMA"
          ]
        },
        {
          "title": "通信",
          "lines": [
            "REST: 認証・設定取得・初期化",
            "WebSocket: チャット・音声・画像・コード",
            "BroadcastChannel: ウィンドウ間同期"
          ]
        }
      ],
      "facts": [
        "renderer は Vue 3 + Vite + TypeScript で実装している。",
        "VRM 描画は Three.js + @pixiv/three-vrm + @pixiv/three-vrm-animation。",
        "Vue Router / Pinia 中心の構成ではなく、AiDiy.vue が状態を持つ。"
      ],
      "evidence": [
        {
          "source": "frontend_avatar/AGENTS.md",
          "text": "技術スタックは Vue 3 + Vite + TypeScript、Electron、Three.js、@pixiv/three-vrm、@pixiv/three-vrm-animation、WebSocket、BroadcastChannel、Monaco Editor。"
        }
      ],
      "short_narration": "使う側は難しく考えなくて大丈夫です。3D キャラクターが声や操作に合わせてリアルタイムに反応します。",
      "long_narration": "アバターの裏側では、Web アプリ、3D 表示、音声、AI 通信が組み合わさっています。でも使うときに大事なのは、技術名を覚えることではありません。キャラクターが画面に出て、話しかけたり、動いたり、コードや文章づくりを手伝ったりすることです。ゲームや配信ツールに近い感覚で、AI をもっと身近にできます。内部では Vue 3 と Three.js が連携し、@pixiv/three-vrm が VRM モデルを描画します。AI との通信は WebSocket、ウィンドウ間の状態同期は BroadcastChannel が担っています。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_start_sec": 15.6,
      "short_duration_sec": 8.208,
      "long_start_sec": 61.416,
      "long_duration_sec": 37.872
    },
    {
      "id": "scene_003",
      "title": "Electron ウィンドウ設計",
      "expression": "neutral",
      "accent": "#ffbf47",
      "accent_soft": "rgba(255, 191, 71, 0.18)",
      "kicker": "WINDOWS",
      "headline": "role 別の透過フレームレス\nBrowserWindow",
      "lead": "Electron では login / core / chat / file / image / code1〜code6 / settings の役割ごとに BrowserWindow を持ちます。Web ではこれらをタブ表現に変換します。",
      "subtitle": "WindowRole 別の透過フレームレス BrowserWindow を main process で管理する。",
      "image": "images/scene_003.png",
      "chips": [
        "login",
        "core",
        "chat",
        "file",
        "image",
        "code1〜code6",
        "settings",
        "透過フレームレス"
      ],
      "metrics": [
        {
          "label": "WindowRole",
          "value": "10"
        },
        {
          "label": "frame",
          "value": "なし"
        },
        {
          "label": "transparent",
          "value": "true"
        }
      ],
      "cards": [
        {
          "title": "ウィンドウ基本",
          "lines": [
            "transparent: true",
            "frame: false / hasShadow: false",
            "_WindowShell.vue がタイトル代替"
          ]
        },
        {
          "title": "ライフサイクル",
          "lines": [
            "login → core で全 panel を作成",
            "panel toggle は破棄せず show / hide",
            "closePanelWindow で完全破棄"
          ]
        },
        {
          "title": "管理",
          "lines": [
            "windowRoles Map で id → role",
            "panelStates でパネル表示状態",
            "settings は別ウィンドウで開閉"
          ]
        }
      ],
      "facts": [
        "全 BrowserWindow は transparent: true / frame: false / hasShadow: false である。",
        "WindowRole は login / core / chat / file / image / code1〜code6 / settings。",
        "panel toggle はウィンドウを破棄せず show / hide で切り替える。"
      ],
      "evidence": [
        {
          "source": ".aidiy/knowledge/frontend_avatar,Electronウィンドウ管理.md",
          "text": "全ウィンドウは transparent: true, frame: false, hasShadow: false の透過フレームレスウィンドウです。"
        }
      ],
      "short_narration": "デスクトップ版では、チャットや画像、コードの画面を必要なときだけ出せます。机の道具のように切り出して使えます。",
      "long_narration": "デスクトップ版では、AI チャット、画像、ファイル、コード支援などの画面を、必要なときに開いたり隠したりできます。いつも全部を出すのではなく、今使いたい道具だけを机の上に置くイメージです。透明なウィンドウで重ねられるので、作業画面の横にアバターを置いて、話しながら進める使い方ができます。ウィンドウは login、core、chat、file、image、code1 から code6、settings の役割ごとに独立しており、表示と非表示は破棄せず show / hide で切り替えるので、切り替え速度も速いです。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_start_sec": 23.808,
      "short_duration_sec": 8.64,
      "long_start_sec": 99.288,
      "long_duration_sec": 35.16
    },
    {
      "id": "scene_004",
      "title": "VRM モデルと VRMA モーション",
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123, 140, 255, 0.18)",
      "kicker": "VRM / VRMA",
      "headline": "VRMA は巡回再生方式、\n姿勢の繋がりは crossFadeFrom で保つ",
      "lead": "VRM は public/vrm/、VRMA は public/vrma/サンプル と 標準 に置きます。LoopRepeat 固定ではなく、finished で次クリップを選び直す巡回方式です。",
      "subtitle": "VRM / VRMA はフォルダ配置。再生は finished イベントで次クリップへ遷移する。",
      "image": "images/scene_004.png",
      "chips": [
        "public/vrm/",
        "public/vrma/サンプル",
        "public/vrma/標準",
        "LoopRepeat ではない",
        "finished で次へ",
        "crossFadeFrom",
        "口パク BlendShape"
      ],
      "metrics": [
        {
          "label": "既定モデル",
          "value": "VRM_AiDiy.vrm"
        },
        {
          "label": "VRMA フォルダ",
          "value": "サンプル / 標準"
        },
        {
          "label": "再生方式",
          "value": "巡回"
        }
      ],
      "cards": [
        {
          "title": "ファイル配置",
          "lines": [
            "public/vrm/ に .vrm を置く",
            "public/vrma/<フォルダ名>/ に .vrma を置く",
            "現行フォルダ: サンプル / 標準"
          ]
        },
        {
          "title": "巡回再生",
          "lines": [
            "LoopRepeat ではなく finished で次選択",
            "action.crossFadeFrom で姿勢継承",
            "1 本でも終了後に再開可能"
          ]
        },
        {
          "title": "一覧取得",
          "lines": [
            "Web: config.ts の SAMPLE/STANDARD_VRMA_FILES",
            "Electron: desktop:list-vrma-files IPC",
            "両方で確認する"
          ]
        }
      ],
      "facts": [
        "DEFAULT_VRM_MODEL_URL は /vrm/VRM_AiDiy.vrm。",
        "VRMA フォルダ名は サンプル と 標準。",
        "Web は config.ts の配列、Electron は desktop:list-vrma-files IPC が一覧を返す。"
      ],
      "evidence": [
        {
          "source": ".aidiy/knowledge/frontend_avatar,VRM_VRMA追加手順.md",
          "text": "VRM は frontend_avatar/public/vrm/ に置く。VRMA は frontend_avatar/public/vrma/<フォルダ名>/ に置く。現行フォルダは サンプル / 標準。"
        },
        {
          "source": ".aidiy/knowledge/frontend_avatar,frontend_web,アバター表示とVRMA.md",
          "text": "現行方針は単一クリップの THREE.LoopRepeat ではなく、finished イベントで次の VRMA を選択して再生する巡回方式。"
        }
      ],
      "short_narration": "アバターはただ立っているだけではありません。動きや表情、リップシンクで AI との会話が生き生きとした体験になります。",
      "long_narration": "VRM モデルとモーションを使うことで、アバターは表情を変えたり、体を動かしたりできます。音声に合わせたリップシンクもあるので、ただ文字が返ってくるよりも、相手が話している感じが出ます。勉強の相談、作品づくり、プログラミングの質問など、ひとりで作業している時間にちょっとした付き添い役を作れます。モーションは finished イベントで次のクリップを選ぶ巡回方式で、crossFadeFrom を使って姿勢のつながりを自然に保ちます。VRM や VRMA ファイルを差し替えるだけで、好みのキャラクターに入れ替えられます。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_start_sec": 32.448,
      "short_duration_sec": 8.616,
      "long_start_sec": 134.448,
      "long_duration_sec": 35.376
    },
    {
      "id": "scene_005",
      "title": "表示選択と状態同期",
      "expression": "neutral",
      "accent": "#ff8a6b",
      "accent_soft": "rgba(255, 138, 107, 0.18)",
      "kicker": "DISPLAY & SYNC",
      "headline": "アバター以外も並ぶ表示選択、\nBroadcastChannel で両モード同期",
      "lead": "表示は アバター / xneko / xeyes / アナログ時計 / デジタル時計 / カレンダー / 無し から選べます。状態同期は BroadcastChannel avatar-desktop-sync を使います。",
      "subtitle": "表示選択は 7 種類。Electron と Web は avatar-desktop-sync で状態同期する。",
      "image": "images/scene_005.png",
      "chips": [
        "アバター",
        "xneko",
        "xeyes",
        "アナログ時計",
        "デジタル時計",
        "カレンダー",
        "無し"
      ],
      "metrics": [
        {
          "label": "表示候補",
          "value": "7"
        },
        {
          "label": "同期チャンネル",
          "value": "avatar-desktop-sync"
        },
        {
          "label": "controls-visible",
          "value": "UI トグル"
        }
      ],
      "cards": [
        {
          "title": "表示選択 UI",
          "lines": [
            "AIコア.vue が左下に配置",
            "アバター固有設定は右下",
            "controls-visible=false で UI を隠す"
          ]
        },
        {
          "title": "状態同期",
          "lines": [
            "BroadcastChannel avatar-desktop-sync",
            "panel 表示・session を共有",
            "AiDiy.vue が中心"
          ]
        },
        {
          "title": "xeyes / xneko",
          "lines": [
            "xeyes は IPC でウィンドウ外カーソル追従",
            "CPU 使用率は system:get-cpu-usage",
            "xneko は 256x128 スプライト"
          ]
        }
      ],
      "facts": [
        "表示候補は アバター / xneko / xeyes / アナログ時計 / デジタル時計 / カレンダー / 無し の 7 種類。",
        "Electron / Web 間の状態同期は BroadcastChannel avatar-desktop-sync を使う。",
        "xeyes の CPU 使用率は system:get-cpu-usage IPC から取得する。"
      ],
      "evidence": [
        {
          "source": ".aidiy/knowledge/frontend_avatar,frontend_web,アバター表示とVRMA.md",
          "text": "表示選択候補は アバター / xneko(猫) / xeyes(目) / アナログ時計 / デジタル時計 / カレンダー / 無し など。"
        },
        {
          "source": "frontend_avatar/AGENTS.md",
          "text": "Electron / Web 間の状態同期は BroadcastChannel avatar-desktop-sync を使います。"
        }
      ],
      "short_narration": "アバター以外にも、時計やカレンダーなどに切り替えられます。気分と作業に合わせてじゃまにならない表示を選べます。",
      "long_narration": "表示はアバターだけではありません。目の表示、時計、カレンダー、何も出さないモードなど、作業のじゃまになりにくい形へ切り替えられます。ブラウザとデスクトップで状態がそろうので、場所を変えても使い心地がつながります。今日は楽しく話したい、今は時間だけ見たい、という気分に合わせられるのが楽しいところです。xeyes は画面外のカーソルも追いかけ、xneko はスプライトアニメーションで動き回ります。Electron と Web の状態は BroadcastChannel avatar-desktop-sync で常にそろっているので、どちらで設定を変えても即座に反映されます。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_start_sec": 41.064,
      "short_duration_sec": 8.184,
      "long_start_sec": 169.824,
      "long_duration_sec": 37.296
    },
    {
      "id": "scene_999",
      "title": "ご視聴ありがとうございました",
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196, 155, 255, 0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "THANK YOU",
      "headline": "ご視聴ありがとうございました。\nあなたなら frontend_avatar をどう使いますか？",
      "lead": "VRM アバター、表示切り替え、Electron / Web 両対応の状態同期を、AIコア専用クライアントとして束ねています。",
      "subtitle": "あなたなら frontend_avatar を、どう使いますか？",
      "image": "images/scene_999.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "short_narration": "AiDiy のアバターなら、AI と音声会話しながら開発する体験ができます。あなたもぜひ試してみませんか。",
      "long_narration": "AiDiy には、アバター、音声チャット、コード支援、画像生成まで、AI を使った開発体験をそのまま試せる部品がそろっています。マイクに向かって話しかけると、アバターがリアルタイムに応答し、コードの相談にも乗ってくれます。AiDiy で、AI と音声会話しながら開発する体験、ぜひやってみませんか。あなたが声をかければ、アバターはすぐそこにいます。",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_start_sec": 49.248,
      "short_duration_sec": 7.944,
      "long_start_sec": 207.12,
      "long_duration_sec": 25.008
    }
  ],
  "short_duration_sec": 57.192,
  "long_duration_sec": 232.128
};
