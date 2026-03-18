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

`frontend_avatar` は、**Vue 3 + Vite + TypeScript + Electron** で構成された  
**AIコア専用のデスクトップアバタークライアント** です。

`frontend_web` がブラウザ向けの業務UIであるのに対し、`frontend_avatar` は次の役割に特化しています。

- ログイン用の小さなデスクトップウィンドウ
- 常駐型のアバターウィンドウ
- チャット / ファイル / 画像 / コード用の補助パネルウィンドウ
- WebSocket による AIコアとのリアルタイム通信
- VRM / VRMA を使った 3D アバター表示
- マイク入力 / スピーカー出力の双方向音声連携

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
- 画面の表示切替は URL ルーティングではなく、**ウィンドウ role** と IPC で制御します
- 認証情報は `localStorage` に保持します
- バックエンドへの HTTP は `8091`、Vite 開発サーバーは `8099` が前提です

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

- `login`
- `core`
- `chat`
- `file`
- `image`
- `code1`
- `code2`
- `code3`
- `code4`

**重要な設計ポイント：**
- `createBaseWindow()` で全ウィンドウ共通設定を適用
- `transparent: true`
- `frame: false`
- `backgroundColor: '#00000000'`
- `applyPrimaryMode()` で login/core のサイズと位置を切り替え
- `panelStates` で補助ウィンドウの表示状態を共有

### 2. Preload

ファイル: `electron/preload.ts`

責務:
- `contextBridge.exposeInMainWorld('desktopApi', api)` で renderer に安全な API を公開
- IPC をラップして、renderer 側から直接 `ipcRenderer` を触らせない

主な公開 API:
- `getWindowRole()`
- `getWindowBounds()`
- `setWindowBounds()`
- `setWindowMode()`
- `closeCurrentWindow()`
- `togglePanel()`
- `getPanelStates()`
- `listDisplaySources()`
- `setDisplaySource()`
- `onPanelStatesChanged()`
- `onWindowShown()`

### 3. Renderer

エントリーポイント: `src/main.ts` → `src/AiDiy.vue` を直接マウント（`App.vue` は存在しない）

`src/AiDiy.vue` の責務:
- 現在ウィンドウの role 判定
- ログイン状態の管理
- セッションIDの維持
- AIコアへの WebSocket 接続
- 補助ウィンドウ向けの状態同期（BroadcastChannel）
- 各 Vue コンポーネントの切り替え

`frontend_avatar` では Vue Router を使わず、`AiDiy.vue` が role に応じて描画を切り替えます。

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

同期される主な情報:
- 認証状態
- 利用者表示名
- セッションID
- メッセージ一覧
- モデル設定
- マイク / スピーカー状態
- 接続状態
- パネル表示状態

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
- 接続時に `connect` メッセージを送信
- `init` メッセージ受信時にセッションIDを確定
- 最大5回まで自動再接続（3秒間隔）
- ソケット番号ごとに接続を分離
- チャンネルつきイベントは `メッセージ識別_チャンネル` でもディスパッチされる

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
}
```

**主なソケット用途:**
- `input` チャンネル: テキスト入力（`input_text`）
- `audio` チャンネル: 音声データ（`input_audio`）
- `operations` メッセージ: UI ボタン状態送信
- `chat` 系は各パネルコンポーネント側で WebSocket インスタンスを持つ

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
CORE_BASE_URL          // バックエンド HTTP ベースURL（既定: http://127.0.0.1:8091）
AI_WS_ENDPOINT         // WebSocket エンドポイント（既定: ws://127.0.0.1:8091/core/ws/AIコア）
DEFAULT_VRM_MODEL_URL  // デフォルト VRM モデルパス（'/vrm/AiDiy_Sample_M.vrm'）
SAMPLE_VRMA_FOLDER_NAME    // サンプルモーションフォルダ名（'サンプル'）
STANDARD_VRMA_FOLDER_NAME  // 標準モーションフォルダ名（'標準'）
defaultModelSettings() // モデル設定デフォルト値を返す関数
```

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

### 1. ウィンドウ role を増やす場合

次の連動修正が必要です。

- `electron/main.ts` の `PanelKey` / `WindowRole`
- `electron/preload.ts` の型
- `src/AiDiy.vue` の `PanelKey` / タイトル / 表示制御
- 必要なら `AIコア.vue` のボタン群

### 2. パネルの表示状態を変える場合

次を合わせて確認してください。

- `panelStates` 初期値
- `createPanelVisibility()`
- `PANEL_KEYS`
- snapshot 同期 (`buildSnapshot()`, BroadcastChannel)

### 3. Electron IPC を追加する場合

必ず以下をセットで更新します。

- `electron/main.ts` の `ipcMain.handle(...)`
- `electron/preload.ts` の `desktopApi`
- `src/env.d.ts` または型宣言側
- renderer 利用箇所

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
- バックエンド側の `AIコア/AIコア_設定.py` の定数と一致させる
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
- API 接続先を変える場合は `src/lib/config.ts` を起点に確認してください。
- 全ファイルは UTF-8 必須です。
- **ユーザーの指示なしに `dist` / `dist-electron` を生成しないでください。** ビルド系コマンドは明示依頼時のみ実行します。
