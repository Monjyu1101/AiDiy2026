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
    "duration_sec": 121.632,
    "format": "html_avatar_presenter_with_media",
    "tone": "事実ベース、簡潔、根拠付き",
    "goal": "frontend_avatar の位置づけ、技術、ウィンドウ設計、VRM/VRMA、表示選択、状態同期を正確に伝える。"
  },
  "assets_policy": {
    "visual_style": "left_avatar_38_right_content_62",
    "audio_dir": "audio",
    "image_dir": "images",
    "avatar": "vrm/AiDiy_Sample_M.vrm"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "この動画で紹介すること",
      "start_sec": 0.0,
      "duration_sec": 13.632,
      "expression": "neutral",
      "accent": "#29d8ff",
      "accent_soft": "rgba(41, 216, 255, 0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "INTRODUCTION",
      "headline": "この動画では、frontend_avatar の\n位置づけと仕組みを紹介します",
      "lead": "AIコア専用クライアント、Electron / Web 両対応、VRM アバター、表示選択、状態同期までを短く見ていきます。",
      "subtitle": "この動画では、frontend_avatar の位置づけ、技術、ウィンドウ設計、VRM/VRMA、表示選択を紹介します。",
      "narration": "この動画では、frontend_avatar の位置づけと仕組みを紹介します。AIコア専用クライアント、Electron と Web の両対応、VRM アバター、表示選択、状態同期まで、実装に沿って短く見ていきます。",
      "image": "images/scene_000.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "audio": "audio/scene_000.mp3",
      "short_narration": "frontend_avatar は AI コア専用クライアントです。Electron デスクトップとブラウザの両対応で動作します。",
      "long_narration": "この動画では、frontend_avatar の位置づけと仕組みを紹介します。AIコア専用クライアントとしての役割、Electron デスクトップアプリと Web ブラウザの両対応、VRM アバターの描画、7 種類の表示選択、Electron と Web の間の状態同期まで、実装に沿って見ていきます。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 7.824,
      "long_start_sec": 0.0,
      "long_duration_sec": 20.304
    },
    {
      "id": "scene_001",
      "title": "AIコア専用クライアント",
      "start_sec": 13.632,
      "duration_sec": 15.312,
      "expression": "neutral",
      "accent": "#7dffb3",
      "accent_soft": "rgba(125, 255, 179, 0.18)",
      "kicker": "ROLE",
      "headline": "Electron と Web で\n同じ renderer が動く",
      "lead": "frontend_avatar は AIコア専用の Avatar クライアントです。判定は window.desktopApi の有無で切り替わります。",
      "subtitle": "AIコア専用 Avatar クライアント。Electron / Web 両対応で、同じ renderer を使う。",
      "narration": "frontend_avatar は AIコア専用の Avatar クライアントです。Electron デスクトップアプリと通常 Web ブラウザの両方で動作し、判定は window の desktopApi が在るかどうかで行います。認証 storage は Electron が localStorage、Web が sessionStorage です。",
      "image": "images/scene_001.png",
      "audio": "audio/scene_001.mp3",
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
      "short_narration": "Electron デスクトップアプリと Web ブラウザの両方で動く AI 専用クライアントです。実行環境の判定は window.desktopApi の有無で行います。",
      "long_narration": "frontend_avatar は AIコア専用のアバタークライアントです。通常の Web ブラウザでも動きますし、Electron でデスクトップアプリとしても動作します。実行環境の判定は window.desktopApi が存在するかどうかで行います。認証情報のストレージは Electron が localStorage、Web が sessionStorage と、環境ごとに切り替わります。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_start_sec": 7.824,
      "short_duration_sec": 10.632,
      "long_start_sec": 20.304,
      "long_duration_sec": 22.152
    },
    {
      "id": "scene_002",
      "title": "技術スタック",
      "start_sec": 28.944,
      "duration_sec": 14.568,
      "expression": "neutral",
      "accent": "#ff6bd6",
      "accent_soft": "rgba(255, 107, 214, 0.18)",
      "kicker": "TECH STACK",
      "headline": "Vue 3 + Three.js + @pixiv/three-vrm を中核に、\nElectron が周りを包む",
      "lead": "renderer は Vue 3 + Vite + TypeScript。Three.js と @pixiv/three-vrm シリーズで VRM を描画し、Electron が複数ウィンドウを束ねます。",
      "subtitle": "Vue 3 / Vite / TypeScript / Three.js / @pixiv/three-vrm / @pixiv/three-vrm-animation / Electron / WebSocket / BroadcastChannel / Monaco Editor。",
      "narration": "renderer は Vue 3 と Vite と TypeScript で作ります。VRM 描画は Three.js と pixiv の three-vrm シリーズです。Electron が複数ウィンドウを担当し、AI との通信は WebSocket、ウィンドウ間の状態同期には BroadcastChannel を使います。",
      "image": "images/scene_002.png",
      "audio": "audio/scene_002.mp3",
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
      "short_narration": "Vue 3・TypeScript・Three.js・VRM で構築された、アバター付きアプリケーションです。",
      "long_narration": "技術スタックは Vue 3、Vite、TypeScript で renderer を構築し、Three.js と @pixiv/three-vrm シリーズで VRM モデルを描画します。AI との通信は WebSocket、Electron の複数ウィンドウ間の状態同期は BroadcastChannel を使います。Vue Router と Pinia 中心の構成ではなく、AiDiy.vue が状態を持つ設計になっています。TypeScript は strict mode が有効で、frontend_web との差異のひとつになっています。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_start_sec": 18.456,
      "short_duration_sec": 8.712,
      "long_start_sec": 42.456,
      "long_duration_sec": 32.832
    },
    {
      "id": "scene_003",
      "title": "Electron ウィンドウ設計",
      "start_sec": 43.512,
      "duration_sec": 18.984,
      "expression": "neutral",
      "accent": "#ffbf47",
      "accent_soft": "rgba(255, 191, 71, 0.18)",
      "kicker": "WINDOWS",
      "headline": "role 別の透過フレームレス\nBrowserWindow",
      "lead": "Electron では login / core / chat / file / image / code1〜code6 / settings の役割ごとに BrowserWindow を持ちます。Web ではこれらをタブ表現に変換します。",
      "subtitle": "WindowRole 別の透過フレームレス BrowserWindow を main process で管理する。",
      "narration": "Electron 版は ログイン、コア、チャット、ファイル、イメージ、コード 1 から 6、セッティング、合計 10 種類の役割別 BrowserWindow を持ちます。すべて transparent: true、frame: false、hasShadow: false の透過フレームレスで、_WindowShell がタイトル代わりの操作領域を提供します。Web 版は同じ役割を単一ページのタブで扱います。",
      "image": "images/scene_003.png",
      "audio": "audio/scene_003.mp3",
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
      "short_narration": "役割別に複数の BrowserWindow を持ち、透過・フレームレスで画面に溶け込みます。",
      "long_narration": "Electron 版は login、core、chat、file、image、code1 から code6、settings の役割別 BrowserWindow を持ちます。全ウィンドウは transparent:true、frame:false、hasShadow:false の透過フレームレスで作られており、_WindowShell がタイトルバーの代わりとなる操作領域を提供します。パネルの切り替えはウィンドウを破棄せず show と hide で行います。Web モードでは同じ役割をタブで表現します。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_start_sec": 27.168,
      "short_duration_sec": 6.072,
      "long_start_sec": 75.288,
      "long_duration_sec": 32.304
    },
    {
      "id": "scene_004",
      "title": "VRM モデルと VRMA モーション",
      "start_sec": 62.496,
      "duration_sec": 30.288,
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123, 140, 255, 0.18)",
      "kicker": "VRM / VRMA",
      "headline": "VRMA は巡回再生方式、\n姿勢の繋がりは crossFadeFrom で保つ",
      "lead": "VRM は public/vrm/、VRMA は public/vrma/サンプル と 標準 に置きます。LoopRepeat 固定ではなく、finished で次クリップを選び直す巡回方式です。",
      "subtitle": "VRM / VRMA はフォルダ配置。再生は finished イベントで次クリップへ遷移する。",
      "narration": "VRM モデルは public の vrm フォルダに、VRMA モーションは public の vrma のサンプルと標準のフォルダに置きます。モーションは LoopRepeat 固定ではなく、finished イベントで次の VRMA を選び直す巡回再生方式です。姿勢のガクつきは crossFadeFrom で吸収します。Web モードでは config.ts の一覧、Electron モードでは desktop list vrma files の IPC が実ファイルを返します。",
      "image": "images/scene_004.png",
      "audio": "audio/scene_004.mp3",
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
          "value": "AiDiy_Sample_M.vrm"
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
        "DEFAULT_VRM_MODEL_URL は /vrm/AiDiy_Sample_M.vrm。",
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
      "short_narration": "VRM モデルにモーションと表情を適用し、音声のリップシンクと連動して動かします。クリップ切り替えは crossFadeFrom で吸収します。",
      "long_narration": "VRM モデルのファイルは public/vrm/ フォルダに、VRMA モーションファイルは public/vrma/サンプル と public/vrma/標準 に置きます。モーションの再生は LoopRepeat で無限ループするのではなく、finished イベントで次の VRMA クリップを選び直す巡回再生方式です。クリップの切り替えによる姿勢のガクつきは crossFadeFrom で吸収します。Web モードでは config.ts の配列がファイル一覧を返し、Electron モードでは desktop:list-vrma-files の IPC がリアルファイルを返します。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_start_sec": 33.24,
      "short_duration_sec": 9.672,
      "long_start_sec": 107.592,
      "long_duration_sec": 45.12
    },
    {
      "id": "scene_005",
      "title": "表示選択と状態同期",
      "start_sec": 92.784,
      "duration_sec": 15.36,
      "expression": "neutral",
      "accent": "#ff8a6b",
      "accent_soft": "rgba(255, 138, 107, 0.18)",
      "kicker": "DISPLAY & SYNC",
      "headline": "アバター以外も並ぶ表示選択、\nBroadcastChannel で両モード同期",
      "lead": "表示は アバター / xneko / xeyes / アナログ時計 / デジタル時計 / カレンダー / 無し から選べます。状態同期は BroadcastChannel avatar-desktop-sync を使います。",
      "subtitle": "表示選択は 7 種類。Electron と Web は avatar-desktop-sync で状態同期する。",
      "narration": "表示はアバター以外に、 xneko、 xeyes、アナログ時計、デジタル時計、カレンダー、表示無し、合わせて 7 種類から選べます。Electron と Web の間のパネル表示やセッションは、BroadcastChannel の avatar-desktop-sync を使ってつなぎます。",
      "image": "images/scene_005.png",
      "audio": "audio/scene_005.mp3",
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
      "short_narration": "アバター・xneko・xeyes など 7 種の表示から選べます。Electron と Web は BroadcastChannel でリアルタイム同期します。",
      "long_narration": "表示モードはアバター、xneko、xeyes、アナログ時計、デジタル時計、カレンダー、表示無しの 7 種類から選べます。xeyes の CPU 使用率は system:get-cpu-usage の IPC から取得します。Electron と Web の間のパネル表示とセッション状態の同期には BroadcastChannel の avatar-desktop-sync チャンネルを使います。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_start_sec": 42.912,
      "short_duration_sec": 8.904,
      "long_start_sec": 152.712,
      "long_duration_sec": 25.392
    },
    {
      "id": "scene_999",
      "title": "ご視聴ありがとうございました",
      "start_sec": 108.144,
      "duration_sec": 13.488,
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196, 155, 255, 0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "THANK YOU",
      "headline": "ご視聴ありがとうございました。\nあなたなら frontend_avatar をどう使いますか？",
      "lead": "VRM アバター、表示切り替え、Electron / Web 両対応の状態同期を、AIコア専用クライアントとして束ねています。",
      "subtitle": "あなたなら frontend_avatar を、どう使いますか？",
      "narration": "ご視聴ありがとうございました。frontend_avatar は VRM アバター、表示選択、Electron と Web 両対応の状態同期を、AIコア専用クライアントとして束ねています。あなたなら frontend_avatar を、どう使いますか。",
      "image": "images/scene_999.png",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "audio": "audio/scene_999.mp3",
      "short_narration": "Electron と Web の両対応、VRM アバター、BroadcastChannel 同期。すべてをひとつのクライアントに束ねています。",
      "long_narration": "ご視聴ありがとうございました。frontend_avatar は VRM アバター、7 種類の表示選択、Electron と Web の両対応、BroadcastChannel による状態同期を、AIコア専用クライアントとして束ねています。デスクトップとブラウザの両方でシームレスに動くアバター体験を、あなたの環境でぜひ試してみてください。",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_start_sec": 51.816,
      "short_duration_sec": 8.952,
      "long_start_sec": 178.104,
      "long_duration_sec": 22.56
    }
  ],
  "duration_sec": 121.632,
  "short_duration_sec": 60.768,
  "long_duration_sec": 200.664
};
