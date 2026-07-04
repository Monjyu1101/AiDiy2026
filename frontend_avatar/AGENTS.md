# frontend_avatar 実装概要

## 本書の目的

このファイルは `frontend_avatar` の構成、実装方針、主要な入口を示す概要ドキュメントです。
起動、変更チェック、IPC 追加、VRM / VRMA、音声処理などの HowTo は `.aidiy/knowledge` に移動しています。
AI エージェントは、本書に個別手順や一時的な作業メモを追記しないでください。
業務システム機能追加は `../docs/` の開発ガイドを優先し、コアシステム機能調整は `../.aidiy/knowledge/_index.md` を入口にします。

## HowTo 参照先

| 目的 | 参照先 |
|------|--------|
| Electron / Web 両対応の変更チェック | [`../.aidiy/knowledge/frontend_avatar,変更チェック.md`](../.aidiy/knowledge/frontend_avatar,変更チェック.md) |
| Electron IPC 追加 | [`../.aidiy/knowledge/frontend_avatar,ElectronIPC追加手順.md`](../.aidiy/knowledge/frontend_avatar,ElectronIPC追加手順.md) |
| VRM / VRMA 追加 | [`../.aidiy/knowledge/frontend_avatar,VRM_VRMA追加手順.md`](../.aidiy/knowledge/frontend_avatar,VRM_VRMA追加手順.md) |
| アバター表示、VRMA 再生、表示選択 UI | [`../.aidiy/knowledge/frontend_avatar,frontend_web,アバター表示とVRMA.md`](../.aidiy/knowledge/frontend_avatar,frontend_web,アバター表示とVRMA.md) |
| xneko / xeyes ウィジェット | [`../.aidiy/knowledge/frontend_avatar,xneko_xeyesウィジェット追加手順.md`](../.aidiy/knowledge/frontend_avatar,xneko_xeyesウィジェット追加手順.md) |
| 音声入力・音声再生 | [`../.aidiy/knowledge/backend_server,frontend_avatar,AI音声処理.md`](../.aidiy/knowledge/backend_server,frontend_avatar,AI音声処理.md) |
| AI WebSocket packet | [`../.aidiy/knowledge/backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md`](../.aidiy/knowledge/backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md) |
| AI モデル設定 | [`../.aidiy/knowledge/backend_server,frontend_avatar,frontend_web,AIモデル設定変更手順.md`](../.aidiy/knowledge/backend_server,frontend_avatar,frontend_web,AIモデル設定変更手順.md) |

## 概要

`frontend_avatar` は AIコア専用の Avatar クライアントです。
Electron デスクトップアプリと通常 Web ブラウザの両方で動作します。

| 項目 | Electron モード | Web モード |
|------|----------------|-----------|
| 判定 | `!!window.desktopApi` | `!window.desktopApi` |
| 認証 storage | `localStorage` | `sessionStorage` |
| UI | 複数 BrowserWindow | 左アバター + 右タブ |
| パネル | IPC で show / hide | `アクティブタブ` |
| API | `/core` `/task` proxy / config（本番は 8091 / 8093 直結） | `/core` `/task` proxy / 動的 URL |

Web 版 AI 画面は `/AiDiy` 系の route / query で role を表現します。
Electron 版は BrowserWindow の role を main process で管理します。

## 技術スタック

- Vue 3 + Vite + TypeScript。
- Electron。
- Three.js。
- `@pixiv/three-vrm`。
- `@pixiv/three-vrm-animation`。
- WebSocket。
- BroadcastChannel。
- Monaco Editor。

## ファイル構成

| パス | 役割 |
|------|------|
| `electron/main.ts` | BrowserWindow、IPC、パネル制御 |
| `electron/preload.ts` | renderer へ `desktopApi` を公開 |
| `src/AiDiy.vue` | 認証、接続、role / panel 状態、Web layout の中心 |
| `src/main.ts` | renderer 初期化 |
| `src/api/client.ts` | REST API client（`apiClient` = core、`taskClient` = backend_task） |
| `src/api/websocket.ts` | AI コア WebSocket |
| `src/api/config.ts` | API URL（`CORE_BASE_URL` / `TASK_BASE_URL`）、モデル設定、VRM / VRMA 定数 |
| `src/components/` | AIコア、Avatar、音声、チャット、コードなどの各パネル |
| `src/components/AIタスク/` | AIタスク画面（components / dialog / windows。windows は Electron 分割ウィンドウ用） |
| `src/dialog/` | AI 設定などの dialog |
| `public/vrm/` | VRM モデル |
| `public/vrma/` | VRMA モーション |

## ウィンドウ設計

主な WindowRole:

- `login`
- `core`
- `chat`
- `file`
- `image`
- `code1`〜`code6`
- `settings`
- `task1`〜`task3`（AIタスクの要求 / フロー図 / 明細ウィンドウ）
- `taskDialog`（タスク要求 / 明細の編集ダイアログウィンドウ）

Electron では role ごとに BrowserWindow を持ちます。
Web では単一ページ内のタブとして扱います（AIタスクは `AIタスク.vue` の 3 パネル一体表示）。

## 状態同期

Electron / Web 間の状態同期は BroadcastChannel `avatar-desktop-sync` を使います。
パネル表示状態、セッション、必要な snapshot は `src/AiDiy.vue` を中心に構築します。

AIタスク関連は追加で 2 つの BroadcastChannel を使います。

- `avatar-task-sync`: 要求ウィンドウ（task1）の選択タスクをフロー図（task2）/ 明細（task3）へ配信
- `avatar-task-dialog`: taskDialog ウィンドウの登録完了を一覧側へ通知

taskDialog へ渡す行データは IPC（structured clone）を通るため、リアクティブ Proxy をそのまま渡さず `{ ...row }` で複製します。

`frontend_web` と異なり、Vue Router / Pinia 中心の構成ではありません。

## AI 接続

- REST API は認証、設定取得、初期化に使う。
- WebSocket はチャット、音声、画像、ファイル、コードパネルのリアルタイム通信に使う。
- WebSocket の packet 形式は `AIコアWebSocket仕様.md` を参照する。
- AIタスクは `taskClient`（backend_task 8093）で REST + 5 秒ポーリング。WebSocket は使わない。

## 実装時の入口

- IPC を触る場合は `electron/main.ts`、`electron/preload.ts`、`src/env.d.ts`、renderer 利用箇所をセットで見る。
- 接続まわりは `src/api/config.ts`、`src/api/client.ts`、`src/api/websocket.ts` をセットで見る。
- アバター表示は `AIコア_アバター.vue`、`AIコア_自立身体制御.ts`、`AIコア_自動カメラワーク.ts` を起点に見る。
- 音声は `AIコア_音声処理.ts` の `AudioController` を起点に見る。
- Web と Electron の差分は `frontendAvatar変更チェック.md` を先に確認する。
