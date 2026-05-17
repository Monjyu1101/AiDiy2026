window.SCENARIO = {
  "project_name": "AiDiy avatar版紹介",
  "version": "take2",
  "title": "avatar版 AiDiy 紹介",
  "source": {
    "type": "agents_and_knowledge",
    "summary": "AiDiy の frontend_avatar（Electron/Web デュアルモード + VRM アバター）の主要機能を実装実態から紹介する。"
  },
  "target": {
    "language": "ja-JP",
    "format": "html_css_scene_player_with_media",
    "tone": "AIアバターシステム紹介、先進的、使いたくなる",
    "goal": "frontend_avatar の Electron/Web デュアルモード、VRM アバター、AI コア連携を実際に使いたくなるように紹介する。"
  },
  "assets_policy": {
    "visual_style": "left_image_30_right_explanation_70",
    "audio_dir": "audio",
    "image_dir": "images",
    "avatar": "vrm/AiDiy_Sample_M.vrm",
    "tts_provider": "edge:female"
  },
  "scenes": [
    {
      "id": "scene_000",
      "title": "avatar版 AiDiy 紹介",
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196, 155, 255, 0.2)",
      "layout": "hero",
      "hero_image_focus": true,
      "kicker": "AVATAR CLIENT",
      "headline": "avatar版 AiDiy の\n主要機能を紹介します",
      "lead": "Electron デスクトップと Web ブラウザの両方で動く AI アバタークライアント。VRM モデルと音声で AI を体感できます。",
      "subtitle": "avatar版 AiDiy の主要機能と操作感を順番にご紹介します。",
      "image": "images/scene_000.png",
      "image_prompt": "Square 1:1 hero poster for an AI avatar client application. Bold typography 'AiDiy Avatar' with a stylish VRM character and holographic UI elements, dark background, strong violet glow, futuristic AI interface aesthetic.",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "short_narration": "avatar版 AiDiy の主要機能をご紹介します。VRM アバターが声と口パクで AI と対話する、デスクトップ＆ブラウザ対応のクライアントです。",
      "long_narration": "この動画では、AiDiy の AI アバタークライアントをご紹介します。Electron デスクトップアプリと Web ブラウザの両方に対応した frontend_avatar です。Three.js でリアルタイムに描画される VRM アバター、音声でリアルタイムに AI と対話する LIVE_AI、コード支援の CODE_AI まで、主要な機能を順番にご覧ください。デスクトップに常駐するアバターが AI の返答を声と口パクで表現する、これまでにない開発体験です。",
      "short_audio": "audio/short_scene_000.mp3",
      "long_audio": "audio/long_scene_000.mp3",
      "short_start_sec": 0.0,
      "short_duration_sec": 10.536,
      "long_start_sec": 0.0,
      "long_duration_sec": 29.736
    },
    {
      "id": "scene_001",
      "title": "Electron / Web デュアルモード",
      "expression": "neutral",
      "accent": "#c49bff",
      "accent_soft": "rgba(196, 155, 255, 0.18)",
      "kicker": "DUAL MODE",
      "headline": "デスクトップアプリと\nWeb ブラウザの両方で動く",
      "lead": "window.desktopApi の有無で Electron モードと Web モードを自動判定。同じコードベースで両方の環境に対応します。",
      "subtitle": "window.desktopApi の有無でモードを自動判定します。",
      "image": "images/scene_001.png",
      "image_prompt": "Vertical 2:3 infographic showing Electron desktop mode versus web browser mode for an AI avatar application, side by side comparison with window.desktopApi detection, violet accent, clean technical diagram.",
      "chips": [
        "Electron モード",
        "Web モード",
        "window.desktopApi",
        "BroadcastChannel"
      ],
      "metrics": [
        {
          "label": "モード",
          "value": "2"
        },
        {
          "label": "ポート",
          "value": "8099"
        }
      ],
      "cards": [
        {
          "title": "Electron モード",
          "lines": [
            "window.desktopApi あり",
            "複数の BrowserWindow で構成",
            "localStorage でセッション管理"
          ]
        },
        {
          "title": "Web モード",
          "lines": [
            "window.desktopApi なし",
            "左アバター + 右タブのレイアウト",
            "sessionStorage でセッション管理"
          ]
        }
      ],
      "facts": [
        "frontend_avatar は Electron デスクトップアプリと通常 Web ブラウザの両方で動作する。",
        "window.desktopApi の有無でモードを自動判定し、認証 Storage を切り替える。",
        "BroadcastChannel 'avatar-desktop-sync' で Electron の複数ウィンドウ間の状態を同期する。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "frontend_avatar は Electron デスクトップアプリと通常 Web ブラウザの両方で動作します。"
        }
      ],
      "short_narration": "Electron デスクトップとブラウザの両方で動くデュアルモード設計。window.desktopApi の有無でモードを自動判定し、同一コードで両環境に対応します。",
      "long_narration": "frontend_avatar は Electron デスクトップアプリとしても、通常の Web ブラウザアプリとしても同一コードベースで動作します。window.desktopApi の有無でモードを自動判定し、Electron モードでは複数の BrowserWindow を開いて localStorage でセッションを永続管理します。Web モードでは左アバター・右タブのレイアウトで動作し、sessionStorage で認証トークンを管理するためタブを閉じると自動でセッションが終了します。1つのコードで2種類の動作環境に対応できるため、デプロイ先に応じた柔軟な運用が可能です。",
      "short_audio": "audio/short_scene_001.mp3",
      "long_audio": "audio/long_scene_001.mp3",
      "short_start_sec": 10.536,
      "short_duration_sec": 11.544,
      "long_start_sec": 29.736,
      "long_duration_sec": 35.016
    },
    {
      "id": "scene_002",
      "title": "VRM アバター（Three.js + @pixiv/three-vrm）",
      "expression": "neutral",
      "accent": "#ff6bd6",
      "accent_soft": "rgba(255, 107, 214, 0.18)",
      "kicker": "VRM AVATAR",
      "headline": "Three.js と VRM で\n3D アバターを動かす",
      "lead": "Three.js と @pixiv/three-vrm でレンダリングする VRM アバター。表情、アニメーション、リップシンクに対応します。",
      "subtitle": "Three.js + @pixiv/three-vrm でリアルタイム 3D アバターを実現します。",
      "image": "images/scene_002.png",
      "image_prompt": "Vertical 2:3 illustration of a 3D VRM avatar character rendered with Three.js, showing expression controls and animation clips, magenta accent, modern 3D avatar application aesthetic, professional and clean.",
      "chips": [
        "Three.js",
        "@pixiv/three-vrm",
        "VRM",
        "VRMA",
        "リップシンク"
      ],
      "metrics": [
        {
          "label": "表示種別",
          "value": "7"
        },
        {
          "label": "表情",
          "value": "VRM"
        }
      ],
      "cards": [
        {
          "title": "VRM アバター",
          "lines": [
            "public/vrm/ に VRM モデルを配置",
            "VRMA でアニメーションクリップ再生",
            "表情（happy/sad/relaxed 等）を制御"
          ]
        },
        {
          "title": "リップシンク",
          "lines": [
            "音声再生中に aa 表情をドライブ",
            "AudioContext + AnalyserNode で音量取得",
            "自然な口の動きで音声を表現"
          ]
        }
      ],
      "facts": [
        "Three.js と @pixiv/three-vrm でリアルタイムに VRM モデルをレンダリングする。",
        "表示種別はアバター、xneko、xeyes、アナログ時計、デジタル時計、カレンダー、表示無しの7種類。",
        "音声再生時は AudioContext + AnalyserNode でリップシンクを自動実行する。"
      ],
      "evidence": [
        {
          "source": "frontend_avatar/AGENTS.md",
          "text": "Three.js + @pixiv/three-vrm で VRM をレンダリング。VRMA でアニメーション再生。"
        }
      ],
      "short_narration": "Three.js と @pixiv/three-vrm でリアルタイムレンダリングされた VRM アバターは、表情・VRMA アニメーション・音声リップシンクに対応しています。",
      "long_narration": "frontend_avatar は Three.js と @pixiv/three-vrm を使って VRM モデルをリアルタイムにレンダリングします。happy、sad、relaxed などの表情を動的に制御でき、VRMA ファイルでアニメーションクリップを再生できます。音声再生中は AudioContext と AnalyserNode で音量をリアルタイムに取得してリップシンクを自動実行するため、アバターが自然に話しているように見えます。表示モードはアバター、xneko、xeyes、アナログ時計、デジタル時計、カレンダー、表示無しの7種類から切り替えられます。自分の VRM モデルをファイルとして配置するだけで、オリジナルのアバターに差し替えられます。",
      "short_audio": "audio/short_scene_002.mp3",
      "long_audio": "audio/long_scene_002.mp3",
      "short_start_sec": 22.08,
      "short_duration_sec": 12.264,
      "long_start_sec": 64.752,
      "long_duration_sec": 42.744
    },
    {
      "id": "scene_003",
      "title": "Web モードの操作感",
      "expression": "neutral",
      "accent": "#7b8cff",
      "accent_soft": "rgba(123, 140, 255, 0.18)",
      "kicker": "WEB MODE",
      "headline": "ブラウザで開く\nアバター + タブ UI",
      "lead": "Web モードは左にアバター、右にタブパネルという構成で、ブラウザから直接アクセスして AI と対話できます。",
      "subtitle": "Web モードは左アバター + 右タブの構成で動作します。",
      "image": "images/scene_003.png",
      "image_prompt": "Vertical 2:3 screenshot-style mockup of a web browser AI avatar interface, showing VRM avatar on the left and tab panel with chat interface on the right, blue-violet accent, modern AI web application design.",
      "chips": [
        "左アバター",
        "右タブパネル",
        "sessionStorage",
        "role/query URL"
      ],
      "metrics": [
        {
          "label": "レイアウト",
          "value": "左38%+右62%"
        },
        {
          "label": "アクセス",
          "value": "localhost:8099"
        }
      ],
      "cards": [
        {
          "title": "Web モード UI",
          "lines": [
            "左 38%: Three.js アバターレンダリング",
            "右 62%: チャット・音声・コードタブ",
            "sessionStorage で認証トークン管理"
          ]
        },
        {
          "title": "URL 制御",
          "lines": [
            "role パラメータで画面を指定",
            "query パラメータで初期入力",
            "Electron から Web ウィンドウへの操作連携"
          ]
        }
      ],
      "facts": [
        "Web モードは左アバターパネル 38%、右タブパネル 62% のレイアウト。",
        "sessionStorage で認証トークンを管理し、タブ閉じでセッションが終了する。",
        "role と query パラメータで画面状態を制御できる。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "Web モードは左アバター + 右タブ。sessionStorage でセッション管理。"
        }
      ],
      "short_narration": "Web モードはブラウザで localhost:8099 にアクセスするだけで使えます。左 38% がアバター描画、右 62% がチャット・音声・コード支援タブです。",
      "long_narration": "Web モードでブラウザから localhost:8099 にアクセスすると、左 38% に Three.js で描画される VRM アバター、右 62% にチャット・音声・コード支援のタブパネルが表示されます。sessionStorage で認証トークンを管理するため、タブを閉じると自動的にセッションが終了し、セキュリティ的にも安心です。role パラメータで初期表示する画面を指定でき、query パラメータで初期入力テキストを設定することもできます。Electron をインストールせずともブラウザだけで AI アバターを体験できるため、チーム全員で手軽に利用できます。",
      "short_audio": "audio/short_scene_003.mp3",
      "long_audio": "audio/long_scene_003.mp3",
      "short_start_sec": 34.344,
      "short_duration_sec": 12.96,
      "long_start_sec": 107.496,
      "long_duration_sec": 38.664
    },
    {
      "id": "scene_004",
      "title": "Desktop モード（Electron）",
      "expression": "neutral",
      "accent": "#00e0b8",
      "accent_soft": "rgba(0, 224, 184, 0.18)",
      "kicker": "DESKTOP MODE",
      "headline": "複数ウィンドウで\nデスクトップ常駐の AI 体験",
      "lead": "Electron モードでは複数の BrowserWindow が連携し、デスクトップアプリとして常駐しながら AI と対話できます。",
      "subtitle": "Electron モードは複数 BrowserWindow + BroadcastChannel で連携します。",
      "image": "images/scene_004.png",
      "image_prompt": "Vertical 2:3 screenshot-style mockup of an Electron desktop AI avatar application, showing multiple windows with avatar display and chat panel, teal accent, modern desktop AI application design.",
      "chips": [
        "複数 BrowserWindow",
        "IPC通信",
        "BroadcastChannel",
        "localStorage",
        "常駐"
      ],
      "metrics": [
        {
          "label": "ウィンドウ",
          "value": "複数"
        },
        {
          "label": "同期",
          "value": "BroadcastChannel"
        }
      ],
      "cards": [
        {
          "title": "Electron 構成",
          "lines": [
            "main.ts: BrowserWindow 管理・IPC",
            "preload.ts: window.desktopApi 注入",
            "renderer: Vue 3 で UI 描画"
          ]
        },
        {
          "title": "ウィンドウ連携",
          "lines": [
            "アバターウィンドウとチャットウィンドウ",
            "BroadcastChannel でリアルタイム同期",
            "localStorage で認証持続"
          ]
        }
      ],
      "facts": [
        "Electron モードでは window.desktopApi が注入されてモードを判定する。",
        "複数の BrowserWindow 間の状態同期は BroadcastChannel avatar-desktop-sync を使う。",
        "main.ts が IPC 通信と BrowserWindow 管理を担当する。"
      ],
      "evidence": [
        {
          "source": "frontend_avatar/AGENTS.md",
          "text": "Electron: 複数 BrowserWindow、IPC、preload で window.desktopApi を注入。"
        }
      ],
      "short_narration": "Electron モードは main.ts が複数 BrowserWindow を管理し、BroadcastChannel でリアルタイム同期。デスクトップに常駐しながら AI との対話を継続できます。",
      "long_narration": "Electron モードでは main.ts が複数の BrowserWindow を管理し、preload.ts が window.desktopApi をレンダラープロセスに注入します。アバターウィンドウとチャットウィンドウが BroadcastChannel avatar-desktop-sync を通じてリアルタイムに状態を同期するため、どちらのウィンドウで操作しても即座に連動します。localStorage で認証トークンを永続管理するため、PC を再起動してもログイン状態が維持されます。デスクトップに常駐するアバターと音声で対話しながら、コード支援を受けて開発を進めるという、これまでとは違う開発体験ができます。",
      "short_audio": "audio/short_scene_004.mp3",
      "long_audio": "audio/long_scene_004.mp3",
      "short_start_sec": 47.304,
      "short_duration_sec": 11.616,
      "long_start_sec": 146.16,
      "long_duration_sec": 37.416
    },
    {
      "id": "scene_005",
      "title": "AI コア連携（音声・チャット・コード支援）",
      "expression": "neutral",
      "accent": "#ffbf47",
      "accent_soft": "rgba(255, 191, 71, 0.18)",
      "kicker": "AI INTEGRATION",
      "headline": "音声対話からコード支援まで\nアバターが AI と直結",
      "lead": "frontend_avatar の AI コアは音声リアルタイム対話、テキストチャット、コード支援パネルをアバターと統合します。",
      "subtitle": "LIVE_AI の音声対話とアバターのリップシンクが連動します。",
      "image": "images/scene_005.png",
      "image_prompt": "Vertical 2:3 illustration of AI avatar integrating with voice dialogue, chat and code assistance panels, showing speech waveform connected to avatar lip sync, amber accent, futuristic AI interface design.",
      "chips": [
        "LIVE_AI 音声",
        "CHAT_AI",
        "CODE_AI",
        "リップシンク連動",
        "WebSocket"
      ],
      "metrics": [
        {
          "label": "AI種別",
          "value": "3系統"
        },
        {
          "label": "WebSocket",
          "value": "8091"
        }
      ],
      "cards": [
        {
          "title": "音声 AI（LIVE_AI）",
          "lines": [
            "マイクからリアルタイム音声入力",
            "AI の返答をアバターが声で読み上げ",
            "aa 表情でリップシンク自動実行"
          ]
        },
        {
          "title": "チャット・コード支援",
          "lines": [
            "CHAT_AI: テキストチャット",
            "CODE_AI1〜6: 6パネルのコード支援",
            "WebSocket で backend_server と接続"
          ]
        }
      ],
      "facts": [
        "LIVE_AI モードでは音声入力をリアルタイムに AI へ送り、返答をアバターが読み上げる。",
        "音声再生中は AudioContext AnalyserNode が aa 表情をドライブしてリップシンクを実現。",
        "backend_server のポート 8091 の WebSocket エンドポイントと接続する。"
      ],
      "evidence": [
        {
          "source": "AGENTS.md",
          "text": "AIコア: テキスト、音声、画像、ファイル、コード支援を統合する多パネルUI。"
        }
      ],
      "short_narration": "LIVE_AI 音声対話中はアバターがリップシンクで口を動かし AI の返答を声で読み上げます。CHAT_AI と CODE_AI も同じ画面で使えます。",
      "long_narration": "avatar版 AiDiy の最大の特徴は、AI コアとアバターの深い統合です。LIVE_AI モードではマイクで音声入力すると AI がリアルタイムに返答し、アバターが声で読み上げながらリップシンクで口が動きます。テキストチャットの CHAT_AI と、6パネル構成のコード支援 CODE_AI も同じ画面で利用できます。使用する AI モデルは Claude、Copilot、Gemini、Codex など設定から切り替え可能で、すべて WebSocket で backend_server とリアルタイム接続しています。会話は A会話履歴テーブルに自動保存されるため、過去の対話を後から振り返ることもできます。",
      "short_audio": "audio/short_scene_005.mp3",
      "long_audio": "audio/long_scene_005.mp3",
      "short_start_sec": 58.92,
      "short_duration_sec": 11.016,
      "long_start_sec": 183.576,
      "long_duration_sec": 38.4
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
      "headline": "ご視聴ありがとうございました。\nあなたなら AiDiy でどんな体験を創りますか？",
      "lead": "Electron とブラウザの両方で動く VRM アバター + AI コアの組み合わせで、まったく新しい体験を創ってください。",
      "subtitle": "あなたなら AiDiy アバターで、どんな体験を創りますか？",
      "chips": [],
      "metrics": [],
      "cards": [],
      "facts": [],
      "evidence": [],
      "image": "images/scene_999.png",
      "image_prompt": "Square 1:1 elegant closing card for avatar AiDiy introduction. Clean typography 'Thank you for Watching', dark blue gradient background, subtle violet glow, premium futuristic style.",
      "short_narration": "ご視聴ありがとうございました。AiDiy アバターで、デスクトップに AI が常駐する新しい開発体験をぜひ試してみてください。",
      "long_narration": "ご視聴ありがとうございました。AiDiy の avatar版は、Electron とブラウザの両方で動く VRM アバターと AI コアの組み合わせです。音声で AI と対話しながらリップシンクするアバターを眺める体験は、テキストチャットとは全く違う感覚です。デスクトップに常駐させて開発のパートナーとして使ったり、ブラウザで手軽に AI を呼び出したり、あなたならではの使い方を見つけてみてください。VRM モデルを差し替えてオリジナルキャラクターにするカスタマイズも、ファイルを置き換えるだけで実現できます。",
      "short_audio": "audio/short_scene_999.mp3",
      "long_audio": "audio/long_scene_999.mp3",
      "short_start_sec": 69.936,
      "short_duration_sec": 9.096,
      "long_start_sec": 221.976,
      "long_duration_sec": 33.024
    }
  ],
  "short_duration_sec": 79.032,
  "long_duration_sec": 255.0
};
