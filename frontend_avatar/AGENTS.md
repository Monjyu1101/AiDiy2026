# frontend_avatar 実装要点まとめ

## 本書の目的

このファイルは **frontend_avatar（Electron ベースのデスクトップアバタークライアント）の実装詳細** を記載したドキュメントです。  
本書は **日本語で分かりやすく記載しています**。追記時もこの方針を維持してください。

**対象読者：**
- `frontend_avatar` の構造を把握したい開発者
- AIコア用デスクトップアバターを修正・拡張したい開発者
- Electron / Vue / WebSocket / VRM 連携の実装箇所を素早く確認したい開発者

**このファイルの役割：**
- アプリ全体の構造と役割分担の理解
- Electron メインプロセス / preload / renderer の責務整理
- ウィンドウ制御、AI接続、音声処理、アバター表示の実装ポイント整理
- 修正時に見落としやすい連動箇所の明確化

**関連ドキュメント：**
- **[../AGENTS.md](../AGENTS.md)** - プロジェクト全体方針
- **[../backend_server/AGENTS.md](../backend_server/AGENTS.md)** - バックエンド実装詳細
- **[../frontend_web/AGENTS.md](../frontend_web/AGENTS.md)** - Web版フロントエンド実装詳細
- **[../CLAUDE.md](../CLAUDE.md)** - プロジェクト全体インデックス
- **[../docs/開発ガイド/11_コーディングルール/](../docs/開発ガイド/11_コーディングルール/_index.html)** - コーディングルール

---

## 概要

`frontend_avatar` は、**Vue 3 + Vite + TypeScript** で構成された **AIコア専用クライアント** です。  
**Electron デスクトップアプリ** としても **Web ブラウザ単体** でも動作する **デュアルモード** 設計です。

`frontend_web` がブラウザ向けの業務UIであるのに対し、`frontend_avatar` は次の役割に特化しています。

- ログイン用の小さなウィンドウ（Electron: 専用ウィンドウ / Web: 画面内ログインフォーム）
- 常駐型のアバターウィンドウ（VRM / VRMA 3D 表示）
- チャット / ファイル / 画像 / コード用の補助パネル（Electron: 個別ウィンドウ / Web: タブ切替）
- WebSocket による AIコアとのリアルタイム通信
- マイク入力 / スピーカー出力の双方向音声連携

### Electron モードと Web モードの違い

| 項目 | Electron モード | Web モード |
|------|---------------|-----------|
| 判定方法 | `!!window.desktopApi` が `true` | `!!window.desktopApi` が `false` |
| 認証Storage | `localStorage` | `sessionStorage` |
| ウィンドウ | 複数 BrowserWindow（role で分離） | 単一タブ（`/AiDiy?role=core`） |
| パネル表示 | 独立ウィンドウを `show()`/`hide()` | 左右分割レイアウト内タブ切替 |
| アクセス URL | Electron アプリ起動 | `http://localhost:8099/AiDiy` |

---

## まず知っておくこと

### 技術スタック

- **Node.js + npm**
- **Vue 3 Composition API + Vite + TypeScript**
- **Electron**
- **Axios**
- **WebSocket**
- **Three.js**
- **@pixiv/three-vrm**
- **@pixiv/three-vrm-animation**
- **Monaco Editor**（AIコード画面用）

### 基本方針

- 文字コードは **UTF-8 固定**
- ビジネス用語や画面名は **日本語識別子を優先**
- システム用語は英字のままで可
- Vue の日本語ファイル名は可、ただし **コンポーネントタグは ASCII 名のみ**
- `frontend_web` のような Vue Router / Pinia 中心構成ではなく、**単一 App + 複数 Electron ウィンドウ** が前提

### 重要な前提

- Electron ウィンドウは **透明 + フレームレス** が基本です
- 画面の表示切替は URL ルーティングではなく、**ウィンドウ role** と IPC で制御します（`?role=<role>` クエリパラメータで役割を伝達）
- 認証情報: **Electron** は `localStorage`、**Web** は `sessionStorage` に保持します
- バックエンドへの HTTP は `8091`、Vite 開発サーバーは `8099` が前提です
- Web モードでは Vite Proxy 経由（`/core` → `8091`, `/apps` → `8092`）でアクセス

---

## アーキテクチャ概要

`frontend_avatar` は 3 層で構成されています。

### 1. Electron メインプロセス

ファイル: `electron/main.ts`

責務:
- BrowserWindow 作成
- ウィンドウ位置・サイズ制御
- login / core / panel の role 管理
- IPC ハンドラ提供
- デスクトップキャプチャ候補一覧の取得
- パネルの表示状態の一元管理

このアプリは次の role を扱います。

- `login` - ログイン画面（初期表示）
- `core` - アバター常駐ウィンドウ（メイン）
- `chat` - チャットパネル
- `file` - ファイルパネル
- `image` - 画像・画面取得パネル
- `code1` 〜 `code4` - コード支援パネル（4つ）
- `settings` - AI設定ダイアログウィンドウ（**新規追加**）

`settings` ウィンドウは `electron/main.ts` の `settingsWindow` で管理され、core ウィンドウからの IPC で開閉します。

**重要な設計ポイント：**
- `createBaseWindow()` で login / core / panel ウィンドウ共通設定を適用
  - `transparent: true`
  - `frame: false`
  - `backgroundColor: '#00000000'`
- `settings` ウィンドウは `createBaseWindow()` を使わず個別生成
  - `transparent: false`、`backgroundColor: '#f8fafc'`（不透明の白背景）
  - サイズ: `760×700`（最小 `600×400`）、画面中央に表示
- `applyPrimaryMode()` で login/core のサイズと位置を切り替え
- `panelStates` で補助ウィンドウの表示状態を共有
- ウィンドウの最小サイズは Electron の Windows バグ回避のため `windowMinSizes` Map で独自管理し、ロード後に再適用

### 2. Preload

ファイル: `electron/preload.ts`

責務:
- `contextBridge.exposeInMainWorld('desktopApi', api)` で renderer に安全な API を公開
- IPC をラップして、renderer 側から直接 `ipcRenderer` を触らせない

主な公開 API:
- `versions` - `{ chrome, electron, node }` バージョン情報
- `getWindowRole()` - 現在ウィンドウの role を返す
- `getWindowBounds()` - ウィンドウ位置・サイズ・最小サイズを返す（`WindowMetrics` 型）
- `setWindowBounds(bounds)` - ウィンドウ位置・サイズを設定
- `setWindowInteractive(interactive)` - マウスイベントの透過/受付を切り替え
- `setWindowMode(mode)` - login / core モードを切り替え
- `openCoreWindow()` - core ウィンドウを開く
- `openLoginWindow()` - login ウィンドウを開く
- `closeCurrentWindow()` - 現在ウィンドウを閉じる（パネルなら `hide()`）
- `minimizeCurrentWindow()` - 現在ウィンドウを最小化
- `togglePanel(panel)` - 補助パネルの表示/非表示を切り替え
- `applyPanelStates(states)` - 複数パネルの表示状態を一括適用
- `getPanelStates()` - 全パネルの表示状態を取得
- `listDisplaySources()` - デスクトップキャプチャ候補一覧を取得
- `listVrmaFiles(folderName)` - 指定フォルダの VRMA ファイル一覧を取得（Electron ローカルパス対応）
- `setDisplaySource(sourceId)` - キャプチャ対象ソースを設定
- `openSettingsWindow(sessionId)` - 設定ウィンドウを開く（sessionId を渡す）
- `closeSettingsWindow()` - 設定ウィンドウを閉じる（hide）
- `onSettingsPrepare(callback)` - 設定ウィンドウ側で `settings:session-id` を受け取るリスナー登録（解除関数を返す）
- `onPanelStatesChanged(callback)` - パネル表示状態変更イベントのリスナー登録（解除関数を返す）
- `onWindowShown(callback)` - ウィンドウ表示イベントのリスナー登録（解除関数を返す）

### 3. Renderer

エントリーポイント: `src/main.ts` → `src/AiDiy.vue` を直接マウント（`App.vue` は存在しない）

`src/AiDiy.vue` の責務:
- Electron / Web の動作モード判定（`isElectron = !!window.desktopApi`）
- 現在ウィンドウの role 判定（IPC または `?role=` クエリパラメータ）
- ログイン状態の管理（`認証Storage` で Electron=localStorage / Web=sessionStorage を切替）
- セッションIDの維持（`localStorage` の `avatar_session_id`）
- AIコアへの WebSocket 接続（`コアソケット` / `入力ソケット` の 2 本）
- 補助ウィンドウ向けの状態同期（BroadcastChannel `avatar-desktop-sync`）
- 各 Vue コンポーネントの切り替え
- **Web モード固有**: 左右分割レイアウト＋タブ切替（`web-split-layout`）の制御

`frontend_avatar` では Vue Router を使わず、`AiDiy.vue` が role に応じて描画を切り替えます。

**Web モード専用レイアウト（`isElectron === false` の core ロール）:**
- 左ペイン: アバター（`AIコア.vue`）
- 右ペイン: タブバー＋パネルエリア（`chat` / `file` / `image` / `code1〜4` をタブ切替）
- タブ切替は `アクティブタブ` ref で管理（`webTabs` 配列で定義）
- ペイン幅はドラッグリサイズ可能（`リサイズ中` フラグ + `mousemove` ハンドラー）

---

## ファイル構成

### ルート直下

- `index.html` - Vite エントリーポイント
- `vite.config.ts` - Vite 設定
- `tsconfig.json` - renderer 用 TypeScript 設定
- `tsconfig.electron.json` - Electron 用 TypeScript 設定
- `package.json` - npm scripts と依存関係

### Electron

- `electron/main.ts` - メインプロセス
- `electron/preload.ts` - preload

### Renderer

- `src/main.ts` - Vue 起動（`AiDiy.vue` を直接マウント）
- `src/AiDiy.vue` - 認証・接続・role 管理の中心コンポーネント（エントリーポイント）
- `src/style.css` - 全体スタイル
- `src/types.ts` - 共通型
- `src/env.d.ts` - Electron `desktopApi` の型宣言

### コンポーネント

- `src/components/ログイン.vue` - ログイン画面
- `src/components/AIコア.vue` - 常駐アバターウィンドウ
- `src/components/AIコア_アバター.vue` - VRM / VRMA 3D表示
- `src/components/AIコア_音声処理.ts` - AudioController クラス（マイク入力・PCM変換・音声再生・レベル計測）
- `src/components/AIコア_自立身体制御.ts` - Three.js 身体制御（腕の動き・上下揺れのアニメーション）
- `src/components/AIコア_自動カメラワーク.ts` - Three.js カメラアニメーション制御
- `src/components/_WindowShell.vue` - フレームレスウィンドウ共通シェル
- `src/components/AIチャット.vue` - チャットパネル
- `src/components/AIファイル.vue` - ファイルパネル
- `src/components/AIイメージ.vue` - 画像・画面取得パネル
- `src/components/AIコード.vue` - コード支援パネル
- `src/components/ファイル内容表示.vue` - ファイル内容インラインビューア

### ダイアログ

- `src/dialog/AI設定再起動.vue` - モデル設定ダイアログ（CHAT_AI_NAME / LIVE_AI_NAME 等の変更後に再起動をトリガー）
- `src/dialog/再起動カウントダウン.vue` - 再起動カウントダウン表示
- `src/dialog/更新ファイル一覧.vue` - ファイル更新確認ダイアログ
- `src/dialog/ファイル内容表示.vue` - ダイアログ形式のファイル内容表示

### 共有コンポーネント

- `src/_share/qAlertDialog.vue` - アラート/確認ダイアログ実装

### API / ユーティリティ

- `src/api/client.ts` - Axios クライアント（`CORE_BASE_URL` 使用、401で自動ログアウト）
- `src/api/config.ts` - 接続先URL・VRM/VRMA初期設定・デフォルトモデル設定（環境変数 `VITE_CORE_BASE_URL` 参照）
- `src/api/websocket.ts` - AI用 WebSocket クライアント（自動再接続、ソケット番号分離）
- `src/utils/monaco.ts` - Monaco Editor 初期化関連
- `src/utils/qAlert.ts` - アラート/確認ダイアログ呼び出しユーティリティ

### アセット

- `public/vrm/` - VRM モデル
- `public/vrma/` - モーション
- `public/icons/` - アイコン群

---

## ウィンドウ設計

### login ウィンドウ

- 初期表示用
- 小さなサイズで中央表示
- 認証成功後に `core` モードへ切り替え

### core ウィンドウ

- 右下に常駐するアバター本体
- AI接続状態、マイク、スピーカー、各パネルのトグルを持つ
- 透明表示やホバー時 UI 表示など、このウィンドウに対する要件変更が多い

### 補助パネルウィンドウ

- `chat` / `file` / `image` / `code1-4`
- 非表示時もウィンドウ自体は作成済みのままにし、`show()` / `hide()` で制御
- role ごとに初期位置が異なる

### 状態同期

`AiDiy.vue` では **BroadcastChannel (`avatar-desktop-sync`)** を使って、
core ウィンドウの状態を他パネルへ配信しています。

同期される主な情報（`SharedSnapshot` 型）:
- `認証済み` / `利用者ラベル` - 認証状態・表示名
- `セッションID` - WebSocket セッション
- `メッセージ一覧` - チャット履歴
- `チャットモード` - `'chat'` / `'live'` / `'code1'〜'code4'`
- `モデル設定` - AI モデル設定（CHAT_AI_NAME 等）
- `入力接続済み` / `チャット接続済み` - WebSocket 接続状態
- `コア処理中` / `コアエラー` - AI 処理ステータス
- `入力ウェルカム情報` / `入力ウェルカム本文` - セッション開始メッセージ
- `パネル表示状態` - 各補助パネルの表示/非表示

---

## AI 接続まわり

### HTTP API

ファイル: `src/api/client.ts`

特徴:
- `CORE_BASE_URL` を `baseURL` に使用
- `localStorage` の `token` を自動で `Authorization` ヘッダーへ付与
- `401` を受けたら `token` と `user` を削除し、`auth-expired` イベントを発火

### WebSocket

ファイル: `src/api/websocket.ts`

特徴:
- 接続時に `connect` メッセージを送信（`セッションID` / `ソケット番号` を含む）
- `init` メッセージ受信時にセッションIDを確定し `connect()` の Promise が解決
- 最大5回まで自動再接続（3秒間隔）
- ソケット番号ごとに接続を分離
- チャンネルつきイベントは `メッセージ識別_チャンネル` でもディスパッチされる
- `onStateChange(handler)` で接続状態の変化を監視できる（解除関数を返す）
- 接続タイムアウトは 30 秒

**主なメソッド:**
- `connect()` - WebSocket 接続を開始し、セッションID 解決後に resolve
- `send(message)` - JSON メッセージを送信（未接続時は無視）
- `on(type, handler)` / `off(type, handler?)` - メッセージハンドラー登録/解除
- `disconnect()` - 意図的に切断（自動再接続を抑止）
- `sendPing()` - ping メッセージを送信
- `updateState(ボタン)` - `operations` メッセージでUIボタン状態をバックエンドへ通知
- `sendChatMessage(text)` - チャットテキストを `出力先チャンネル='0'` で送信
- `sendInputText(text, 出力先チャンネル?)` - テキスト入力を `input_text` メッセージで送信
- `onStateChange(handler)` - 接続状態変化リスナー登録（即時呼び出し＋解除関数返却）
- `セッションID取得()` - 現在のセッションIDを返す（未接続なら `null`）

**WebSocketMessage 型（主なフィールド）:**

```ts
{
  type?: string            // 接続制御用（'connect' / 'ping' 等）
  セッションID?: string
  ソケット番号?: string
  チャンネル?: string | null  // 入力チャンネル（'input' / 'audio' 等）
  出力先チャンネル?: string   // 出力先（'0' = メインチャンネル）
  メッセージ識別?: string    // メッセージ種別（'input_text' / 'input_audio' / 'init' 等）
  メッセージ内容?: unknown   // ペイロード本体
  ファイル名?: string | null
  サムネイル画像?: string | null  // Base64
  error?: string           // エラーメッセージ（サーバー側エラー通知時）
  [key: string]: unknown   // その他の任意フィールド
}
```

**主なソケット用途:**
- `input` チャンネル: テキスト入力（`input_text`）
- `audio` チャンネル: 音声データ（`input_audio`）
- `operations` メッセージ: UI ボタン状態送信（`updateState(ボタン)` 経由）
- `chat` 系は各パネルコンポーネント側で WebSocket インスタンスを持つ

**メッセージハンドラーの登録（`on` / `off`）:**
- `on('init', handler)` のようにメッセージ識別を指定して登録
- チャンネルつきメッセージは `メッセージ識別_チャンネル`（例: `output_audio`）でも個別に受け取れる
- `on('*', handler)` で全メッセージを横断的に受け取るワイルドカードリスナーも登録可能
- `off(type)` でハンドラー全削除、`off(type, handler)` で個別削除

**WebSocket エンドポイント:** `/core/ws/AIコア`（`src/api/config.ts` の `AI_WS_ENDPOINT`）

### セッション管理

`AiDiy.vue` が `avatar_session_id` を `localStorage` に保持します。
補助ウィンドウは core ウィンドウから snapshot を受け取り、同一セッションを参照します。

---

## 音声処理

ファイル: `src/components/AIコア_音声処理.ts`（クラス名: `AudioController`）

責務:
- マイク入力開始 / 停止
- PCM 変換（ScriptProcessorNode 使用）
- WebSocket `audio` チャンネル経由で `input_audio` 送信
- 受信音声のキューバッファ再生
- 入出力レベル・スペクトラムの計測（32バンド）

**実装上の注意:**
- 入力サンプルレートはデフォルト 16kHz（`inputSampleRate = 16000`）、モデルにより切替
- 出力サンプルレートはデフォルト 24kHz（`outputSampleRate = 24000`）
- スピーカー無効時は再生キューを積まない（既存キューもクリア）
- マイク開始にはブラウザ/Electron のメディア権限が必要
- `AudioController` には専用の `audioSocket` を渡す（メインソケットと分離）
- `cancelOutput()` で再生中のすべての音声を即停止しキュークリア可能

**ビジュアライザー:**
- バンド数: 32（`VISUALIZER_BAR_COUNT = 32`）
- 入力・出力それぞれ独立した `AnalyserNode` で計測

---

## アバター表示

ファイル: `src/components/AIコア_アバター.vue`

構成:
- Three.js の renderer / scene / camera を自前構築
- VRM モデル読込
- VRMA モーションをランダム再生
- マイク / スピーカーレベルに応じて口パクや演出を更新
- ドラッグで向きを変更可能

**重要な前提:**
- `alpha: true` と `setClearColor(..., 0)` により背景透過対応
- 見た目だけを透明にしたい変更は CSS と props で吸収しやすい
- モデルやモーションの追加時は `src/api/config.ts` の定数と `public/vrm`, `public/vrma` を合わせて更新する
- `AIコア_自立身体制御.ts` が腕・上下揺れを制御、`AIコア_自動カメラワーク.ts` がカメラアニメーションを担当

---

## AI名命名規則と config.ts エクスポート定数

### AI名命名規則（重要）

`src/api/config.ts` の `defaultModelSettings()` で定義。CLAUDE.md の命名規則と同一。

| キー | サフィックス規則 | 例 |
|------|-----------|-----|
| `CHAT_AI_NAME` | 必ず `_chat` で終わる | `gemini_chat` / `freeai_chat` / `openai_chat` |
| `LIVE_AI_NAME` | 必ず `_live` で終わる | `gemini_live` / `freeai_live` / `openai_live` |
| `CODE_AI1_NAME` 〜 `CODE_AI4_NAME` | 必ず `_code` で終わる | `claude_code` / `openai_code` |

**比較は完全一致**（`startswith` 等の前方一致は使用禁止）

### config.ts 主なエクスポート定数

```ts
CORE_BASE_URL          // バックエンド HTTP ベースURL
                       // 優先順: VITE_CORE_BASE_URL 環境変数 > DEV時は '/' > 本番 'http://127.0.0.1:8091'
AI_WS_ENDPOINT         // WebSocket エンドポイント
                       // 優先順: VITE_CORE_WS_URL 環境変数 > ブラウザのホストから動的生成（ws://host/core/ws/AIコア）> 'ws://127.0.0.1:8091/core/ws/AIコア'
DEFAULT_VRM_MODEL_URL  // デフォルト VRM モデルパス（'/vrm/AiDiy_Sample_M.vrm'）
SAMPLE_VRMA_FOLDER_NAME    // サンプルモーションフォルダ名（'サンプル'）
STANDARD_VRMA_FOLDER_NAME  // 標準モーションフォルダ名（'標準'）
SAMPLE_VRMA_FILES      // サンプルフォルダの VRMA ファイルパス配列（'/vrma/サンプル/VRMA_01.vrma' 〜 VRMA_07.vrma の 7 ファイル）
STANDARD_VRMA_FILES    // 標準フォルダの VRMA ファイルパス配列（'/vrma/標準/VRMA_01.vrma' 〜 VRMA_05.vrma の 5 ファイル）
                       // ※ Electron モードでは listVrmaFiles() IPC でローカルファイルを優先使用するため、これらは Web モードのフォールバックとして使用
defaultModelSettings() // モデル設定デフォルト値を返す関数
```

**Web モードでの URL 解決:** 開発時（`import.meta.env.DEV`）は `baseURL='/'` となり、Vite Proxy を経由して `/core/*` → `8091` へルーティングされます。WebSocket も `window.location.host` から動的に生成されるため、ホスト名変更に自動追随します。

---

## 開発コマンド

### 開発起動

```bash
cd frontend_avatar
npm install
npm run dev
```

起動内容:
- Vite 開発サーバー: `http://127.0.0.1:8099`
- Electron main の TypeScript watch
- Electron アプリ起動

### ビルド

```bash
cd frontend_avatar
npm run build
```

**重要:**
- **ユーザーの明示的な指示がない限り、`npm run build` や `build:renderer` / `build:electron` を実行して `dist` / `dist-electron` を生成しないこと。**
- 調査や実装中の確認は、原則として `npm run dev` または `npm run type-check` を優先すること。

内訳:
- `npm run build:renderer`
- `npm run build:electron`

### 型チェックのみ

```bash
cd frontend_avatar
npm run type-check
```

### 実行

```bash
cd frontend_avatar
npm run start
```

---

## ポートと接続先

### Vite

- Renderer 開発サーバー: `127.0.0.1:8099`

### Proxy

- `/core/*` → `http://127.0.0.1:8091`
- `/apps/*` → `http://127.0.0.1:8092`

### 環境変数

`src/api/config.ts` で次を参照します。

- `VITE_CORE_BASE_URL`
- `VITE_CORE_WS_URL`

未指定時の既定値:
- HTTP: `http://127.0.0.1:8091`
- WS: `ws://127.0.0.1:8091`

---

## 実装変更時の重要チェック

### 0. Electron / Web 両モード共通の注意

`AiDiy.vue` は `isElectron` フラグで動作を分岐しています。  
**UI や接続まわりを修正する際は、Electron と Web の両方で動作を確認してください。**

| 修正箇所 | Electron への影響 | Web への影響 |
|---------|-----------------|------------|
| `AiDiy.vue` の状態管理 | core ウィンドウ + BroadcastChannel | 単一タブ内で完結 |
| パネル表示制御 | IPC `panel:toggle` → `show()`/`hide()` | `アクティブタブ` ref の切替 |
| 認証情報保存先 | `localStorage` | `sessionStorage` |
| WebSocket URL | 環境変数 or `127.0.0.1:8091` | Vite Proxy or ホスト動的解決 |

### 1. ウィンドウ role を増やす場合

次の連動修正が必要です。

- `electron/main.ts` の `PanelKey` / `WindowRole`
- `electron/preload.ts` の型
- `src/AiDiy.vue` の `PanelKey` / タイトル / 表示制御
- 必要なら `AIコア.vue` のボタン群

### 2. パネルの表示状態を変える場合

次を合わせて確認してください。

- `panelStates` 初期値（`electron/main.ts`）
- `setPanelVisibility()` / `createPanelWindow()` / `closePanelWindow()`（`electron/main.ts`）
- `PANEL_KEYS`（`src/AiDiy.vue`）
- snapshot 同期 (`buildSnapshot()`, BroadcastChannel)（`src/AiDiy.vue`）

### 3. Electron IPC を追加する場合

必ず以下をセットで更新します。

- `electron/main.ts` の `ipcMain.handle(...)`
- `electron/preload.ts` の `desktopApi`
- `src/env.d.ts` または型宣言側
- renderer 利用箇所

**現在実装済みの IPC ハンドラー一覧（`electron/main.ts`）:**

| IPC チャンネル | 説明 |
|--------------|------|
| `window:get-role` | 現在ウィンドウの role を返す |
| `window:set-mode` | login/core モード切替（ウィンドウ再構築） |
| `window:open-core` | core ウィンドウを開く |
| `window:open-login` | login ウィンドウを開く |
| `window:close-self` | 自身を閉じる（パネルは hide） |
| `window:minimize-self` | 最小化 |
| `window:get-bounds` | 現在の位置・サイズ・最小サイズを返す |
| `window:set-bounds` | 位置・サイズを設定（最小サイズにクランプ） |
| `window:set-interactive` | `setIgnoreMouseEvents` でマウス透過を切替 |
| `panel:toggle` | パネルの表示/非表示トグル |
| `panel:apply-states` | 複数パネルの表示状態を一括適用 |
| `panel:get-states` | 全パネルの表示状態を返す |
| `settings:open` | 設定ウィンドウを開く（sessionId 付き） |
| `settings:close` | 設定ウィンドウを hide |
| `desktop:list-sources` | デスクトップキャプチャ候補一覧 |
| `desktop:list-vrma-files` | 指定フォルダの VRMA ファイル一覧 |
| `desktop:set-source` | キャプチャソースを設定 |

### 4. 接続まわりを変更する場合

次の連動を確認してください。

- `src/api/config.ts`
- `src/api/client.ts`
- `src/api/websocket.ts`
- バックエンド側の API / WebSocket エンドポイント

### 5. アバター演出を変更する場合

次を確認してください。

- `AIコア_アバター.vue` の Three.js 初期化
- `AIコア_自立身体制御.ts`: 腕・上下揺れのアニメーション制御
- `AIコア_自動カメラワーク.ts`: カメラ位置・視点のアニメーション制御
- UI 表示だけの変更か、3D シーンそのものの変更か
- 透明ウィンドウ時に残す要素 / 消す要素の切り分け

### 6. AI名（モデル設定）を変更する場合

- `src/api/config.ts` の `defaultModelSettings()` のデフォルト値を更新
- `CHAT_AI_NAME` は `_chat` 末尾、`LIVE_AI_NAME` は `_live` 末尾、`CODE_AI*_NAME` は `_code` 末尾 **必須**
- バックエンド側の `_config/AiDiy_*.json` と `AIコア/AIセッション管理.py` の初期設定と整合させる
- 比較箇所は完全一致（`===`）で記述し、`startswith` は使わない

---

## デバッグポイント

### Electron 側

- メインプロセスログを確認
- BrowserWindow の role と表示状態を確認
- `desktopCapturer` の一覧取得失敗を確認

### Renderer 側

- DevTools の Console
- Network で `/core/*` の HTTP エラー確認
- WebSocket 接続可否
- `localStorage` の `token`, `user`, `avatar_session_id`

### よくある問題

- **401 エラー**: トークン期限切れ。再ログインが必要
- **音声が出ない**: speaker 無効、AudioContext 未 resume、または audio ソケット未接続
- **マイクが使えない**: Electron 側権限、または audio ソケット未接続
- **補助パネルが同期しない**: BroadcastChannel snapshot が届いていない
- **透明ウィンドウが期待通りでない**: CSS だけでなく `WindowShell.vue` と `アバター.vue` の両方を確認
- **デスクトップキャプチャできない**: `desktop:set-source` の設定漏れ、または source 未選択
- **Web モードでセッションが消える**: `sessionStorage` を使用しているためタブを閉じると失われる（Electron の `localStorage` とは異なる）
- **Web モードでパネルが開かない**: Web では IPC は使えないため `アクティブタブ` ref の切替ロジックを確認
- **Web モード WebSocket が繋がらない**: Vite Proxy の設定（`/core` → `8091`）および `AI_WS_ENDPOINT` の動的 URL 解決を確認

---

## 実装の注意点とベストプラクティス

### Vue コンポーネント名

- 日本語ファイル名は可
- ただし **テンプレート上のタグ名は ASCII で扱う**
- 必要なら `<component :is="コンポーネント変数" />` を使う

### AiDiy.vue は肥大化しやすい

`src/AiDiy.vue` は現在、認証・接続・同期・role切替の中心です。  
修正時は「一見 unrelated に見える副作用」が多いため、次を意識してください。

- login/core/panel どの role に効く変更か
- snapshot に載せるべき状態か
- core 専用状態を panel 側へ誤って持ち込んでいないか
- **`isElectron` 分岐を見落としていないか**（Electron と Web で挙動が変わる箇所が多い）

### Electron と Renderer の責務を混ぜない

- ウィンドウ生成、配置、表示制御は **main.ts**
- 画面表示とユーザー操作は **renderer**
- bridge は **preload.ts**

### 透明ウィンドウ対応

見た目の変更は複数箇所に跨ります。

- Electron の `transparent`
- `WindowShell.vue` の枠・タイトルバー
- `アバター.vue` の背景演出
- `style.css` の全体背景

どれか1箇所だけ直しても、期待どおりの「完全透明」にはなりません。

---

## 注意点

- `frontend_web` の実装パターンをそのまま持ち込まないでください。`frontend_avatar` は Router / Pinia 中心ではありません。
- ポートを `8099` から変更する場合は、必要に応じて起動スクリプトや接続手順も見直してください。
- API 接続先を変える場合は `src/api/config.ts` を起点に確認してください。
- 全ファイルは UTF-8 必須です。
- **ユーザーの指示なしに `dist` / `dist-electron` を生成しないでください。** ビルド系コマンドは明示依頼時のみ実行します。
