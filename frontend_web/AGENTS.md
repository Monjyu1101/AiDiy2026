# frontend_web 実装要点まとめ

## 本書の目的

このファイルは **frontend_web（フロントエンドサーバー）の実装詳細** を記載したドキュメントです。
本書は **日本語で分かりやすく記載しています**（全書共通の方針として、追記時もこの方針を維持します）。

**対象読者：** このプロジェクトのフロントエンド（Vue 3 + Vite + TypeScript + Pinia）を理解・修正・拡張する開発者

**このファイルの役割：**
- フロントエンドの全体構造とファイル配置の理解
- 実装の特徴とアーキテクチャパターンの把握
- 新規機能追加やデバッグ時の参照ガイド

**関連ドキュメント：**
- **[../CLAUDE.md](../CLAUDE.md)** - Claude Code向けインデックス（プロジェクト全体概要）
- **[../AGENTS.md](../AGENTS.md)** - プロジェクト全体方針（基本方針、開発コマンド、共通問題）
- **[../docs/開発ガイド/11_コーディングルール/](../docs/開発ガイド/11_コーディングルール/_index.html)** - コーディングルール、命名規則、ベストプラクティス
- **[../docs/開発ガイド/12_フロントエンド画面追加例/](../docs/開発ガイド/12_フロントエンド画面追加例/_index.html)** - フロントエンドCRUD画面追加手順
- **[../backend_server/AGENTS.md](../backend_server/AGENTS.md)** - バックエンド実装詳細（FastAPI + SQLAlchemy + SQLite）
- **[../frontend_avatar/AGENTS.md](../frontend_avatar/AGENTS.md)** - デスクトップアバタークライアント（Electron + WebSocket + VRM）

**📚 ドキュメントリソース（docs/フォルダ）：**
プロジェクトの詳細なドキュメントは `docs/開発ガイド/` フォルダにHTML形式で整備されています。
- **[../docs/開発ガイド/11_コーディングルール/](../docs/開発ガイド/11_コーディングルール/_index.html)** - 命名規則、ベストプラクティス、レビューチェックリスト（**必読**）
- **[../docs/開発ガイド/12_フロントエンド画面追加例/](../docs/開発ガイド/12_フロントエンド画面追加例/_index.html)** - フロントエンドCRUD画面追加手順（**必読**）

**バックエンド・他フロントエンドの情報は別ドキュメント：**
このドキュメントは `frontend_web`（ブラウザ向け業務UI）に特化しています。
- バックエンド → `backend_server/AGENTS.md`
- AIコア専用デスクトップアバタークライアント → `frontend_avatar/AGENTS.md`（Vue Router / Pinia 不使用、Electron マルチウィンドウ構成）

**このファイルの内容：**
- まず知っておくこと（基本原則）
- 実装の全体像と特徴
- フロントエンド構成（ファイル構成と役割）
- Routing（ルート定義、日本語URL対応、認証ガード）
- State Management（Pinia認証ストア）
- API Client（Axios JWT インターセプター）
- Component Structure（レイアウト、共通、機能別コンポーネント）
- qTublerシステム（カスタムテーブルコンポーネント）
- AIコア frontend実装（WebSocket統合）
- Authentication Flow（frontend視点）
- Development Commands（frontend固有）
- 新規テーブル/ビュー/機能 追加手順
- Debugging方法と注意点
- 実装の注意点とベストプラクティス

---

## まず知っておくこと（基本原則）

### 技術スタック
- **Node.js v22.14.0 + npm 11.3.0**
- **Vue 3 Composition API + Vite + TypeScript**
- **Pinia** (状態管理)
- **Vue Router 4** (ルーティング、日本語URL対応)
- **Axios** (HTTP client with interceptors)
- **dayjs** (日付処理)
- **jQuery** (一部レガシー機能で使用)

### 命名規約と文字コード
- **画面/URL/コンポーネント名は日本語が基本**
  - ルート: `/C管理`, `/Mマスタ`, `/T配車/一覧`
  - コンポーネント: `C利用者一覧.vue`, `M商品編集.vue`
  - 変数名（ビジネスロジック）: `利用者名`, `配車日付`, `商品名`
- **文字コードは UTF-8 固定** - 全ファイル必須
- システム用語や一般名詞は英字: `router`, `store`, `apiClient`, `props`, `emit`

### TypeScript設定の特徴
- **Strict mode disabled** (`strict: false`)
  - `strictNullChecks: false`
  - `noImplicitAny: false`
  - 開発速度優先、型エラーに寛容な設定
- **Path alias**: `@/*` → `./src/*`
- **Target**: ES2020

### コンポーネント設計の原則
- **Vue component tags must use ASCII names**
  - ❌ 誤り: `<C利用者一覧 />`（日本語タグ名は無効）
  - ✅ 正解: `<component :is="C利用者一覧" />`（動的コンポーネントとして日本語名を使用）
- **ファイル名は日本語OK**: `C利用者一覧.vue`, `M商品編集.vue`
- **script setup構文を使用** (Composition API)

## 概要
- Vue 3 + Vite + TypeScript の日本語標準UI構成。
- 画面/ルーティング/コンポーネント名は日本語を前提。
- 認証はJWTトークンを `localStorage` に保持し、API呼び出し時に付与。

## 実装の全体像と特徴

### アーキテクチャの特徴

**1. シングルページアプリケーション（SPA）:**
- Vue Router による画面遷移（ページリロードなし）
- 日本語URLのブラウザリロード対応（`decodeURIComponent`）
- 認証ガード機能（未認証は自動的に `/ログイン` へリダイレクト）

**2. 日本語命名規約の徹底:**
- ルートパス: `/C管理/C利用者/一覧`, `/Mマスタ/M商品/編集`
- コンポーネントファイル名: `C利用者一覧.vue`, `M商品編集.vue`
- JSON keys (API通信): `{"利用者名": "admin", "権限ID": "1"}`
- Vue component tags は ASCII name のみ（日本語タグ名は無効）

**3. カテゴリベースのコンポーネント構成:**
- `C管理/` - Core/Common管理画面（C権限、C利用者、C採番）
- `Mマスタ/` - Master data管理画面（M配車区分、M生産区分、M生産工程、M商品分類、M車両、M商品、M商品構成）
- `Tトラン/` - Transaction管理画面（T配車、T生産、T生産払出、T商品入庫/出庫/棚卸）
- `Sスケジューラー/` - Special processing画面（S配車_週/日表示、S生産_週/日表示）
- `Vビュー/` - View画面（V商品推移表）
- `AiDiy/` - AI Core interface（WebSocket統合、マルチパネルUI）
- `Xテスト/` - Experimental features（Xテトリス、Xインベーダー、Xリバーシ）
- `_share/` - 共有ユーティリティ（ダイアログ、qTubler）
- `_Layout`, `_TopBar`, `_TopMenu` - レイアウトコンポーネント

**4. 統一されたCRUD画面パターン:**
```
<カテゴリ>/
  ├── <テーブル名>/
  │   ├── <テーブル名>一覧.vue       // 一覧画面
  │   ├── <テーブル名>編集.vue       // 編集/新規画面（モード切替）
  │   └── components/
  │       └── <テーブル名>一覧テーブル.vue  // qTublerテーブル
```

**5. qTublerシステム（カスタムテーブルコンポーネント）:**
- グリッドレイアウトベースのテーブル表示
- ソート、ページング、行選択機能
- 統一されたテーブルUI/UX
- 型定義: `types/qTubler.ts`
- コンポーネント: `_share/qTubler.vue`, `_share/qTublerFrame.vue`

**6. TypeScript型システム:**
- `types/` ディレクトリで一元管理
  - `api.ts` - API request/response型
  - `entities.ts` - エンティティ型（C利用者、M商品など）
  - `store.ts` - Pinia store型
  - `router.ts` - Vue Router型
  - `qTubler.ts` - qTublerコンポーネント型
  - `common.ts` - 共通型

**7. Vite Proxy設定（開発サーバー）:**
- フロントエンド: `http://localhost:8090`
- `/core/*` → `http://127.0.0.1:8091` (core_main - コア機能)
- `/apps/*` → `http://127.0.0.1:8092` (apps_main - アプリ機能)
- バックエンドとのシームレスな統合
- **注意**: フロントのポートを変更したら、`backend_server/core_main.py` と `apps_main.py` の CORS 許可リストも更新する。

**8. WebSocket統合 (AIコア):**
- `api/websocket.ts` で WebSocket client 提供
- `AIコアWebSocket` クラス
- 自動再接続機能（最大5回、3秒間隔）
- セッション永続化（リロード対応、URLクエリパラメータでソケットID管理）
- メッセージハンドラーシステム

**9. 共通ダイアログシステム:**
- `qAlert(message)` - アラートダイアログ
- `qConfirm(message)` - 確認ダイアログ
- `qColorPicker(initialColor, title)` - カラーピッカーダイアログ
- グローバルインスタンス（App.vueで登録）
- Promise-based API

**10. レイアウトシステム:**
- `_Layout.vue` - メインレイアウト（TopBar + TopMenu + コンテンツ）
- `_TopBar.vue` - トップバー（ユーザー情報、サーバー状態、ログアウト）
- `_TopMenu.vue` - タブ型メニュー（管理/マスタ/トラン/スケジュール/ビュー/リンク/その他/ログアウト）
- メニュー状態管理（`menu_state`: 全表示/非表示/最小化）
- ログイン画面はレイアウト非適用

**11. 認証フロー:**
- JWT token を `localStorage` に保存
- Pinia store (`stores/auth.ts`) で状態管理
- Axios interceptor で自動的に `Authorization: Bearer <token>` ヘッダー付与
- 401エラーで自動ログアウト
- Vue Router guard で未認証時は `/ログイン` へリダイレクト

**12. AIコア マルチパネルUI:**
- 6つの独立パネル（チャット、イメージ、エージェント1-4）
- 動的グリッドレイアウト（1-6パネル対応）
- ポートレート/ランドスケープ対応
- フローティングコントロール（マイク、スピーカー、カメラ、コンポーネント選択）
- WebSocketリアルタイム通信

### No UI Framework / No CSS Framework

このプロジェクトは **外部UIフレームワークを使用していません**：
- ❌ Vuetify, Quasar, Element Plus, PrimeVue などは不使用
- ✅ カスタムCSS + 独自コンポーネント (`qTubler`, `_Modal`, etc.)
- ✅ `assets/main.css` と `assets/menu-common.css` でグローバルスタイル
- ✅ 各コンポーネントの `<style scoped>` でスコープドスタイル

## フロントエンド構成 (frontend_web/src/)

### Core Files（エントリーポイントと設定）

**main.ts** - アプリケーションエントリーポイント:
```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css'

const app = createApp(App)
app.use(createPinia())  // Pinia (state management)
app.use(router)          // Vue Router
app.mount('#app')
```

**App.vue** - ルートコンポーネント:
- `<script setup>` with Composition API
- ログイン画面 (`/ログイン`) 以外は `_Layout` を適用
- グローバルダイアログの登録:
  - `qAlertDialog` (ref: `alertRef`)
  - `qConfirmDialog` (ref: `confirmRef`)
  - `qColorPickerDialog` (ref: `colorPickerRef`)
- `onMounted` でダイアログインスタンスを `utils/qAlert.ts` に登録
- `computed` で `isLogin` を判定（`route.path === '/ログイン'`）

**vite.config.ts** - Vite設定:
- Port: `8090`
- Path alias: `@` → `./src`
- Proxy設定:
  - `/core` → `http://127.0.0.1:8091` (core_main)
  - `/apps` → `http://127.0.0.1:8092` (apps_main)

**tsconfig.json** - TypeScript設定:
- Target: ES2020
- Module: ESNext
- Strict mode: **disabled** (`strict: false`)
- Path alias: `@/*` → `./src/*`
- Types: `vite/client`, `node`

### Routing (router/) - Vue Router 設定

**router/index.ts** - Vue Router設定:

**基本設定:**
```typescript
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [...]
})
```

**認証ガード:**
```typescript
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // 認証が必要なルート
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/ログイン')
  } else {
    next()
  }
})
```

**日本語URLのリロード対応:**
- ブラウザのリロード時、日本語URLがエンコードされる問題に対応
- Router内で `decodeURIComponent` を使用してパスを再解決
- 例: `/C%E7%AE%A1%E7%90%86` → `/C管理`

**ルート定義パターン:**
```typescript
{
  path: '/C管理/C利用者/一覧',
  name: 'C利用者一覧',
  component: () => import('../components/C管理/C利用者/C利用者一覧.vue'),
  meta: { requiresAuth: true, title: 'C利用者一覧' }
}
```

**主要ルート一覧:**

**認証不要:**
- `/ログイン` - ログイン画面

**認証必要（`meta.requiresAuth: true`）:**
- `/` - ダッシュボード（`/C管理` と同じ）
- `/ログアウト` - ログアウト画面

**カテゴリメニュー:**
- `/C管理` - C系カテゴリメニュー
- `/Mマスタ` - M系カテゴリメニュー
- `/Tトラン` - T系カテゴリメニュー
- `/Sスケジュール` - S系カテゴリメニュー
- `/Vビュー` - V系カテゴリメニュー
- `/リンク` - リンク集
- `/Xその他` - その他機能

**C系（管理）画面:**
- `/C管理/C権限/一覧`, `/C管理/C権限/編集`
- `/C管理/C利用者/一覧`, `/C管理/C利用者/編集`
- `/C管理/C採番/一覧`, `/C管理/C採番/編集`

**M系（マスタ）画面:**
- `/Mマスタ/M配車区分/一覧`, `/Mマスタ/M配車区分/編集`
- `/Mマスタ/M生産区分/一覧`, `/Mマスタ/M生産区分/編集`
- `/Mマスタ/M生産工程/一覧`, `/Mマスタ/M生産工程/編集`
- `/Mマスタ/M商品分類/一覧`, `/Mマスタ/M商品分類/編集`
- `/Mマスタ/M車両/一覧`, `/Mマスタ/M車両/編集`
- `/Mマスタ/M商品/一覧`, `/Mマスタ/M商品/編集`
- `/Mマスタ/M商品構成/一覧`, `/Mマスタ/M商品構成/編集`（明細型マスタ）

**T系（トランザクション）画面:**
- `/Tトラン/T配車/一覧`, `/Tトラン/T配車/編集`
- `/Tトラン/T生産/一覧`, `/Tトラン/T生産/編集`（明細型トランザクション）
- `/Tトラン/T生産払出/一覧`（払出一覧、編集なし）
- `/Tトラン/T商品入庫/一覧`, `/Tトラン/T商品入庫/編集`
- `/Tトラン/T商品出庫/一覧`, `/Tトラン/T商品出庫/編集`
- `/Tトラン/T商品棚卸/一覧`, `/Tトラン/T商品棚卸/編集`

**S系（スケジューラー）画面:**
- `/Sスケジュール/S配車_週表示` - 週別配車表示
- `/Sスケジュール/S配車_日表示` - 日別配車表示
- `/Sスケジュール/S生産_週表示` - 週別生産表示
- `/Sスケジュール/S生産_日表示` - 日別生産表示

**V系（ビュー）画面:**
- `/Vビュー/V商品推移表` - 商品推移表

**A系（AI）画面:**
- `/AiDiy` - AIコア インターフェース（新しいタブで開く）

**X系（テスト）画面:**
- `/Xその他/Xテトリス/ゲーム` - テトリスゲーム
- `/Xその他/Xインベーダー/ゲーム` - インベーダーゲーム
- `/Xその他/Xリバーシ/ゲーム` - リバーシゲーム
- `/Xその他/X自己紹介/表示` - 自己紹介画面

**ルーティング設計の特徴:**
- Lazy loading: `() => import(...)` で必要な時だけコンポーネント読み込み
- Meta fields: `requiresAuth`, `title` でルート情報を管理
- 日本語パス: `/C管理`, `/Mマスタ` などURLに日本語使用
- 階層構造: `/カテゴリ/テーブル/アクション` で統一

### State Management (stores/) - Pinia Store

**stores/auth.ts** - 認証状態管理 (Pinia):

**State:**
```typescript
state: (): AuthState => ({
  token: localStorage.getItem('token') || '',
  user: JSON.parse(localStorage.getItem('user') || 'null'),
})
```

**Getters:**
```typescript
getters: {
  isAuthenticated: (state): boolean => !!state.token,
  // CRITICAL: 権限IDは文字列型なので '1' と比較する（数値の 1 ではない）
  isAdmin: (state): boolean => state.user?.権限ID === '1',
}
```

**Actions:**

**`login(username, password)`** - ログイン:
1. `POST /core/auth/ログイン` with `{利用者ID, パスワード}`
2. Success時: `token` を `localStorage` に保存
3. `fetchUser()` で利用者情報取得
4. レスポンス `初期ページ` があれば `/${初期ページ}` へ、未設定なら `/Xその他` へリダイレクト
5. Return: `{success: true/false, message?: string}`

**`fetchUser()`** - 現在利用者情報取得:
1. `POST /core/auth/現在利用者`
2. Success時: `user` を `state` と `localStorage` に保存
3. Error時: `logout()` を呼び出し

**`logout()`** - ログアウト:
1. `token` と `user` をクリア
2. `localStorage` から削除
3. `/ログイン` へリダイレクト

**使用例:**
```typescript
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// ログイン
const result = await authStore.login('admin', '********')
if (!result.success) {
  console.error(result.message)
}

// ログアウト
authStore.logout()

// 認証状態確認
if (authStore.isAuthenticated) {
  console.log('User:', authStore.user.利用者名)
  console.log('Admin:', authStore.isAdmin)
}
```

**型定義 (types/store.ts):**
```typescript
export interface AuthState {
  token: string
  user: C利用者 | null
}

export interface LoginResult {
  success: boolean
  message?: string
}
```

**重要な注意点:**
- 権限IDは文字列型 (`'1'`, `'2'`, `'3'`, etc.) - 数値型ではない
- `isAdmin` getter は `権限ID === '1'` で比較（`=== 1` ではない）
- JWTトークンは60分で期限切れ（バックエンド設定）
- 期限切れ時は401エラーで自動ログアウト（Axios interceptor）

### API Client (api/) - HTTP クライアント

**api/client.ts** - Axios instance with JWT interceptors:

**基本設定:**
```typescript
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const apiClient = axios.create({
  baseURL: '/',  // Vite proxyを使用
  headers: {
    'Content-Type': 'application/json',
  },
})
```

**Request Interceptor（JWTトークン自動付与）:**
```typescript
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const authStore = useAuthStore()
  if (authStore.token) {
    config.headers.Authorization = `Bearer ${authStore.token}`
  }
  return config
})
```

**Response Interceptor（401エラーで自動ログアウト）:**
```typescript
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()  // 自動的に /ログイン へリダイレクト
    }
    return Promise.reject(error)
  }
)
```

**使用例:**
```typescript
import apiClient from '@/api/client'

// GET request (例外的)
const response = await apiClient.get('/core/サーバー状態')

// POST request (標準)
const response = await apiClient.post('/core/C利用者/一覧', {
  // request body
})

// Response structure (統一形式)
{
  status: 'OK' | 'NG',
  message: 'メッセージ',
  data: {
    items: [...],  // 一覧取得の場合
    total: 100,
    limit: 10000
  }
}
```

**Vite Proxy経由のリクエスト:**
- `/core/*` → `http://127.0.0.1:8091` (core_main)
- `/apps/*` → `http://127.0.0.1:8092` (apps_main)
- 例: `apiClient.post('/core/C利用者/一覧')` → `http://127.0.0.1:8091/core/C利用者/一覧`

**api/websocket.ts** - WebSocket client (AIコア用):

**AIコアWebSocket クラス:**
```typescript
export class AIコアWebSocket implements IWebSocketClient {
  constructor(private url: string, socketId?: string)

  // 接続管理
  async connect(): Promise<string>
  disconnect(): void
  isConnected(): boolean

  // メッセージ送受信
  send(message: WebSocketMessage): void
  on(messageType: string, handler: MessageHandler): void
  off(messageType: string, handler?: MessageHandler): void

  // AIコア専用メソッド
  sendPing(): void
  updateState(画面: any, ボタン: any): void
  sendChatMessage(message: string): void
  sendInputText(text: string, チャンネル?: number): void
  requestStream(data: any): void
}
```

**自動再接続機能:**
- 最大再接続試行回数: 5回
- 再接続間隔: 3秒
- `isIntentionallyClosed` フラグで意図的な切断と区別
- リロード時は既存の `socketId` を使用してセッション復元

**使用例:**
```typescript
import { AIコアWebSocket } from '@/api/websocket'

// WebSocket接続
const ws = new AIコアWebSocket('ws://localhost:8091/core/ws/AIコア', socketId)
const newSocketId = await ws.connect()

// メッセージハンドラー登録
ws.on('init', (message) => {
  console.log('初期化メッセージ:', message)
})

// メッセージ送信
ws.send({ type: 'chat', content: 'こんにちは' })

// 切断
ws.disconnect()
```

### Component Structure (components/) - コンポーネント構成

**Layout Components（レイアウトコンポーネント）:**

**_Layout.vue** - メインレイアウトラッパー:
- 構成: `_TopBar` + `_TopMenu` + `<slot />` (コンテンツエリア)
- メニュー状態管理: `menu_state` を `localStorage` に保存
  - `'show'` - 全表示（デフォルト）
  - `'hide'` - 非表示
  - `'minimize'` - 最小化
- メニュートグルボタン（トップバー左端）

**_TopBar.vue** - トップバー:
- ユーザー情報表示: `利用者名 (権限名)`
- サーバー状態インジケーター:
  - `GET /core/サーバー状態` を定期的にポーリング
  - `ready_count` に応じて下線アニメーション
  - 色: グリーン（処理可能）/ レッド（処理中）
- ログアウトボタン
- メニュートグルボタン

**_TopMenu.vue** - タブ型メインナビゲーション:
- タブ一覧:
  1. **AIコア** - `/AiDiy` (新しいタブで開く)
  2. **管理** - `/C管理`
  3. **マスタ** - `/Mマスタ`
  4. **トラン** - `/Tトラン`
  5. **スケジュール** - `/Sスケジュール`
  6. **ビュー** - `/Vビュー`
  7. **リンク** - `/リンク`
  8. **その他** - `/Xその他`
  9. **ログアウト** - `/ログアウト`
- アクティブタブハイライト
- クリックでルート遷移（AIコアのみ新しいタブ）

**Shared Components（共有コンポーネント）:**

**_share/qBooleanCheckbox.vue** - Boolean値専用チェックボックス:
- 0/1 または true/false をトグル
- フォーム内の有効/無効フラグ等で使用

**_share/qMessageDialog.vue** - メッセージダイアログ:
- シンプルなメッセージ表示ダイアログ

**_Modal.vue** - 再利用可能なモーダルダイアログベース:
- Props: `show` (Boolean)
- Slots: デフォルトスロットでコンテンツ
- ESCキーで閉じる
- 背景クリックで閉じる

**_share/qAlertDialog.vue** - アラートダイアログ:
- Promise-based API
- `show(message: string): Promise<void>`
- OKボタンのみ

**_share/qConfirmDialog.vue** - 確認ダイアログ:
- Promise-based API
- `show(message: string): Promise<boolean>`
- OK/キャンセルボタン

**_share/qColorPickerDialog.vue** - カラーピッカーダイアログ:
- Promise-based API
- `show(initialColor: string, title: string): Promise<string | null>`
- カラー選択UI

**_share/qTubler.vue** - カスタムテーブルコンポーネント:
- グリッドレイアウトベース
- ソート機能（カラムヘッダークリック）
- ページング機能（前へ/次へ）
- 行選択機能（クリック/ダブルクリック）
- Props:
  - `columns: Column[]` - カラム定義
  - `data: any[]` - テーブルデータ
  - `pageSize: number` - 1ページあたりの行数
  - `selectable: boolean` - 行選択可能か
- Emits:
  - `row-click` - 行クリック
  - `row-dblclick` - 行ダブルクリック

**_share/qTublerFrame.vue** - qTublerのフレームコンポーネント:
- qTublerをラップして統一UIを提供
- ヘッダー、ツールバー、フッターを含む

**utils/qAlert.ts** - グローバルダイアログAPI:
```typescript
export async function qAlert(message: string): Promise<void>
export async function qConfirm(message: string): Promise<boolean>
export async function qColorPicker(initialColor?: string, title?: string): Promise<string | null>
```
- App.vueで登録されたダイアログインスタンスへ委譲
- 未登録時は `alert()` / `confirm()` にフォールバック

**Feature Components (Category-based)（機能別コンポーネント）:**

**C管理/** - C系 (Core/Common) 管理画面:
- **C管理.vue** - カテゴリメニュー（カード型UI）
- **C権限/**
  - `C権限一覧.vue` - 一覧画面（qTublerテーブル）
  - `C権限編集.vue` - 編集/新規画面（モード切替）
  - `components/C権限一覧テーブル.vue` - qTublerラッパー
- **C利用者/** - 同様の構成
- **C採番/** - 同様の構成

**Mマスタ/** - M系 (Master) データ管理画面:
- **Mマスタ.vue** - カテゴリメニュー
- **M配車区分/**, **M生産区分/**, **M生産工程/**, **M商品分類/**, **M車両/**, **M商品/** - 標準 CRUD pages（一覧/編集/components）
- **M商品構成/** - 明細型マスタ CRUD（`M商品構成一覧.vue`, `M商品構成編集.vue`, `components/`）
- ※ `M生産分類/`, `M工程/` フォルダが残存しているが旧名称の空フォルダ（未使用）

**Tトラン/** - T系 (Transaction) 管理画面:
- **Tトラン.vue** - カテゴリメニュー
- **T配車/**, **T商品入庫/**, **T商品出庫/**, **T商品棚卸/** - 標準 CRUD pages
- **T生産/** - 明細型トランザクション CRUD（`T生産一覧.vue`, `T生産編集.vue`, `T生産払出一覧.vue`, `components/`）

**Sスケジューラー/** - S系 (Scheduler) 特殊処理画面:
- **Sスケジュール.vue** - カテゴリメニュー
- **S配車_週表示.vue**, **S配車_日表示.vue** - 配車スケジュール表示
- **S生産_週表示.vue**, **S生産_日表示.vue** - 生産スケジュール表示
  - 各 `components/<テーブル>テーブル.vue` でカスタムテーブル実装

**Vビュー/** - V系 (View) 表示画面:
- **Vビュー.vue** - カテゴリメニュー
- **V商品推移表.vue** - 商品推移表
  - `components/V商品推移表テーブル.vue` - カスタムテーブル

**AiDiy/** - AI Core インターフェース（詳細は後述）
- **AiDiy.vue** - AIコアメインコンポーネント
- **compornents/** - AIコアパネルコンポーネント（AIチャット/AIイメージ/AIコード/AIファイル/AIコア音声処理）
- **dialog/** - AIコア専用ダイアログコンポーネント
  - `AI設定再起動.vue` - AI設定変更後のサーバー再起動UI
  - `ファイル内容表示.vue` - ファイル内容表示・編集ダイアログ（`POST /core/files/内容取得|内容更新` を使用）
  - `再起動カウントダウン.vue` - 再起動カウントダウン表示
  - `更新ファイル一覧.vue` - 変更ファイル一覧表示

**Xテスト/** - X系 (Experimental) テスト機能:
- **Xその他.vue** - カテゴリメニュー
- **Xテトリス.vue** - テトリスゲーム
- **Xインベーダー.vue** - インベーダーゲーム
- **Xリバーシ.vue** - リバーシゲーム
- **X自己紹介.vue** - 自己紹介画面

**その他:**
- **ログイン.vue** - ログイン画面（認証不要）
- **ログアウト.vue** - ログアウト画面
- **リンク.vue** - リンク集

**Component organization（コンポーネントの組織化）:**
- `_` prefix = shared/layout components
- Category folders (C管理/, Mマスタ/, etc.) = feature-specific pages
- 各カテゴリに `.vue` ファイル = カテゴリメニュー
- 各カテゴリ内に `<テーブル名>/` フォルダ = テーブル別CRUD
- `components/` サブフォルダ = テーブルコンポーネント

### Styles（スタイル）

**assets/main.css** - グローバルベースCSS:
- リセットCSS
- 基本的なフォント設定
- 共通のユーティリティクラス
- ボタン、インプット、カードの基本スタイル

**assets/menu-common.css** - メニュー共通スタイル:
- タブメニューのスタイル
- カテゴリカードのスタイル
- ナビゲーション関連のスタイル

**Scoped Styles:**
- 各コンポーネントの `<style scoped>` でコンポーネント固有のスタイル
- `scoped` 属性でスタイルの衝突を防止

**スタイリング方針:**
- UIフレームワーク不使用（Vuetify, Quasar等なし）
- カスタムCSSのみ
- グリッドレイアウト (CSS Grid) を多用
- Flexboxも併用

## qTublerシステム（カスタムテーブルコンポーネント）

qTublerは、このプロジェクト専用のカスタムテーブルコンポーネントシステムです。

### コンポーネント構成

**_share/qTubler.vue** - コアテーブルコンポーネント:
- グリッドレイアウトベースのテーブル表示
- ソート機能（カラムヘッダークリック）
- ページング機能（前へ/次へボタン）
- 行選択機能（クリック/ダブルクリックイベント）

**Props:**
```typescript
interface Props {
  columns: Column[]      // カラム定義
  data: any[]           // テーブルデータ
  pageSize?: number     // 1ページあたりの行数（デフォルト: 10）
  selectable?: boolean  // 行選択可能か（デフォルト: true）
}
```

**Emits:**
```typescript
{
  'row-click': (row: any, index: number) => void    // 行クリック
  'row-dblclick': (row: any, index: number) => void // 行ダブルクリック
}
```

**Column型定義 (types/qTubler.ts):**
```typescript
export interface Column {
  key: string           // データのキー
  label: string         // 表示ラベル
  width?: string        // カラム幅（例: '100px', '20%'）
  align?: 'left' | 'right' | 'center'  // テキスト配置
  sortable?: boolean    // ソート可能か
}
```

**_share/qTublerFrame.vue** - フレームコンポーネント:
- qTublerをラップして統一UIを提供
- ヘッダー、ツールバー、フッターを含む
- 検索ボックス、追加ボタンなど

### 使用例

**一覧テーブルコンポーネント** (`<テーブル名>一覧テーブル.vue`):
```vue
<template>
  <qTubler
    :columns="columns"
    :data="items"
    :pageSize="20"
    @row-dblclick="handleRowDblClick"
  />
</template>

<script setup lang="ts">
import qTubler from '@/components/_share/qTubler.vue'
import type { Column } from '@/types/qTubler'

const columns: Column[] = [
  { key: '利用者ID', label: '利用者ID', width: '150px', sortable: true },
  { key: '利用者名', label: '利用者名', width: '200px', sortable: true },
  { key: '権限名', label: '権限', width: '150px', sortable: true },
]

const items = ref<any[]>([])

const handleRowDblClick = (row: any) => {
  router.push({ path: '/C管理/C利用者/編集', query: { 利用者ID: row.利用者ID } })
}
</script>
```

### qTublerの特徴

**1. グリッドレイアウトベース:**
- CSS Grid で柔軟なカラム幅設定
- レスポンシブ対応

**2. ソート機能:**
- カラムヘッダークリックでソート
- 昇順/降順の切り替え
- `sortable: true` のカラムのみソート可能

**3. ページング:**
- 前へ/次へボタンでページ移動
- 現在ページ/総ページ数の表示
- `pageSize` で1ページあたりの行数を指定

**4. 行選択:**
- クリックで行選択（ハイライト）
- ダブルクリックで編集画面へ遷移（一般的なパターン）
- `selectable: false` で選択無効化可能

**5. 統一されたUI/UX:**
- 全てのCRUD画面で同じテーブルUI
- 一貫した操作感

## AIコア Component System (A系)

The **AIコア** (Core AI) is a multi-panel AI interface system with flexible grid layouts.

**Key features:**
- **Session persistence**: Uses URL-based session IDs to persist component visibility and control states across page reloads
- **Dynamic grid layouts**: Automatically adjusts layout based on the number of visible panels (1-6 components)
- **Component types**: Chat (terminal-style), Image capture (with source selection), Agent panels (4 independent agents)
- **Floating controls**: Microphone, speaker, camera, and component selection toggle
- **Responsive design**: Adapts layouts for portrait/landscape orientations

**Main container** (`AiDiy.vue`):
- Manages session ID in URL query parameter `?セッションID=<uuid>`
- Tracks visibility state for 6 components (チャット, イメージ, エージェント1-4)
- Controls audio/video buttons (マイク, スピーカー, カメラ)
- Provides dynamic CSS Grid layouts based on panel count

**Component communication pattern:**
- Parent-to-child: Props for state (e.g., `autoShowSelection` to trigger image popup)
- Child-to-parent: Emits for events (e.g., `selectionCancel`, `selectionComplete`)
- Watchers for reactive state synchronization

**Image capture flow:**
- Camera button or image checkbox (OFF→ON) triggers selection popup
- User chooses: File upload, Camera capture, or Desktop capture
- Selection cancellation closes image component
- Image component always resets to `false` on page reload

**Layout behavior:**
- 1 panel: Full screen with 20% horizontal padding (portrait: 10% vertical padding)
- 2 panels: Side-by-side with 10% outer padding + 10% center gap (portrait: stacked vertically)
- 3 panels: Horizontal split (portrait: vertical stack)
- 4 panels: 2×2 grid
- 5-6 panels: 3×2 grid

**Access:**
- URL: http://localhost:8090/AiDiy (opens in new tab from top menu)
- Linked from `_TopMenu.vue` as leftmost menu item

**ダイアログコンポーネント (`AiDiy/dialog/`):**
- `AI設定再起動.vue` - AI設定（モデル・APIキー等）変更後にサーバー再起動を促すUI。`temp/reboot_core.txt` 経由で backend を再起動
- `ファイル内容表示.vue` - コードベース内のファイルを表示・編集するダイアログ。`POST /core/files/内容取得` と `POST /core/files/内容更新` を呼び出し
- `再起動カウントダウン.vue` - 再起動完了までのカウントダウン表示
- `更新ファイル一覧.vue` - AIエージェントが変更したファイルの一覧表示

**Implementation notes:**
- Image component uses `v-show` (not `v-if`) to preserve state when toggling visibility
- Session state saves automatically on any checkbox/button change via watchers
- All Japanese characters work correctly in URLs and API endpoints with UTF-8 encoding

## Authentication Flow

1. Client sends credentials to `/core/auth/ログイン`
2. Server validates and returns JWT token (60-minute expiration)
3. Client stores token in localStorage via Pinia store (`stores/auth.ts`)
4. Axios interceptor (`api/client.ts`) adds `Authorization: Bearer <token>` to all requests
5. バックエンドがトークンを検証し、現在利用者を注入
6. 401 responses trigger automatic logout and redirect to `/ログイン` via Axios response interceptor
7. Logout clears token from localStorage

## Development Commands

**フロントエンド依存関係 (Node.js + npm + TypeScript):**
```bash
cd frontend_web
npm install        # Install dependencies
npm run dev        # Start dev server
npm run build      # Type-check and build for production
npm run preview    # Preview production build
npm run type-check # Run TypeScript type checking without building
```

**重要:**
- **ユーザーの明示的な指示がない限り、`npm run build` などで `dist` を生成しないこと。**
- 動作確認や調査では、原則として `npm run dev` または `npm run type-check` を優先すること。

**Running frontend only:**
```bash
cd frontend_web
npm run dev
```

**VS Code Debugging:**
- `frontend_web/.vscode/launch.json`: フロントエンドのみ（Chromeデバッグ）

## 新規テーブル/ビュー/機能 追加手順

### 新規テーブル（管理系のCRUD画面）
1. `src/components/C管理/<テーブル名>/` に `一覧.vue` / `編集.vue` を追加。
2. 一覧のテーブル表示が必要なら `components` 配下に `一覧テーブル.vue` を追加。
3. `src/router/index.ts` に `/C管理/<テーブル名>/一覧` と `/C管理/<テーブル名>/編集` を追加。
4. `src/components/C管理.vue` にメニューカードを追加。
5. API呼び出しは `src/api/client.ts` を使用し、JSONキーは日本語名で統一。

### 新規V系（参照系の一覧）
1. `src/components/Vビュー/<V名>/` に一覧画面を追加（参照のみ）。
2. `src/router/index.ts` に `/Vビュー/<V名>/一覧` を追加。
3. `src/components/Vビュー.vue` にメニューカードを追加。
4. 一覧取得は `/core/V<対象>/一覧` または `/apps/V<対象>/一覧` を使用（パラメータなし。T配車/V配車のみ開始日付/終了日付）。

### 新規機能（カテゴリ追加）
1. 機能カテゴリに応じて `/Tトラン` / `/Sスケジュール` / `/Xその他` 配下に画面を作成。
2. `src/router/index.ts` にルートを追加（`meta.requiresAuth` 付与）。
3. 必要に応じて `_TopMenu.vue` のタブや各カテゴリ画面のカードを追加。

## 明細型マスタ 編集コンポーネントのパターン（M商品構成編集.vue が実装例）

ヘッダー項目＋複数の明細行を1画面で編集する「明細型マスタ」共通の実装パターンです。
通常の単一レコード編集と異なり、明細一覧を配列で保持して動的に行追加・削除します。

### 型定義の基本構造

```typescript
// 明細行 Form 型（数値項目も string で保持して空欄を表現する）
type 明細行Form = {
  明細SEQ: number      // 表示用連番（送信時は index+1 で再採番）
  // ... 各明細固有のフィールド（string or boolean）
}
```

> **注意**: 数値項目（金額・数量など）は `string` で保持する。`number` にすると空欄が `0` になり UX が悪化する。

### 明細行の操作パターン

```typescript
const createEmptyDetail = (明細SEQ = 1): 明細行Form => ({
  明細SEQ, /* 各フィールドの初期値 */
});

// 行追加
const addDetailRow = () => {
  明細一覧.value.push(createEmptyDetail(明細一覧.value.length + 1));
};

// 行削除 → SEQ を再採番
const removeDetailRow = (index: number) => {
  明細一覧.value.splice(index, 1);
  明細一覧.value.forEach((row, i) => { row.明細SEQ = i + 1; });
};
```

### 送信前のサニタイズと検証

```typescript
// 1. sanitize: 明細SEQ を index+1 で振り直し、空行を除去して送信用に変換
const sanitizeDetails = () =>
  明細一覧.value
    .map((row, i) => ({ 明細SEQ: i + 1, /* 各フィールドを trim/変換 */ }))
    .filter((row) => /* 空行判定 */);

// 2. validate: 必須チェック等を行い、問題があれば null を返す
const validateDetails = () => {
  const rows = sanitizeDetails();
  if (!rows.length) { detailError.value = '明細を1件以上入力してください。'; return null; }
  for (const [i, row] of rows.entries()) {
    if (!row.必須項目) { detailError.value = `${i+1}行目の...を入力してください。`; return null; }
  }
  return rows; // 送信可能なオブジェクト配列
};
```

> **重要**: フォーム上で表示専用の計算値（M商品構成の `構成数量` など）は payload に含めない。バックエンドのスキーマに存在しないフィールドはバリデーションエラーになる。

### API 送信の基本構造

```typescript
const detailPayload = validateDetails();
if (!detailPayload) return;  // バリデーション失敗

const payload = {
  /* ヘッダー項目 */,
  明細一覧: detailPayload,
};
await apiClient.post('/apps/<テーブル名>/登録', payload);  // 登録・変更とも同一構造
```

### M商品構成固有の実装（参考）

以下は M商品構成 特有の実装であり、明細型マスタの汎用パターンではありません。

**構成数量の自動計算**（`分子 / 分母 × 生産ロット`）:

```typescript
// ヘッダーの生産ロット変更時 → 全明細を再計算
watch(() => form.生産ロット, () => { 明細一覧.value.forEach(recalcRow); });

// 分子/分母変更時 → その行のみ再計算（@input="recalcRow(row)"）
const recalcRow = (row) => {
  const val = toNumber(row.構成数量分子) / toNumber(row.構成数量分母) * toNumber(form.生産ロット);
  row.構成数量 = val === 0 ? '' : String(val);
};
// ユーザーが構成数量を直接入力した場合もその値が有効。
// ただし、生産ロット/分子/分母を再変更すると再計算で上書きされる（フラグ管理なし）。
```

**テーブル列**: No / 構成商品ID / 構成商品名 / 構成数量(分子) / 構成数量(分母) / **(参考)計算式** / **構成数量** / 構成単位 / 備考 / 操作

## Debugging

**Browser DevTools:**
- Network tab: Inspect API requests/responses, check for 401/403/500 errors
- Console tab: View Vue warnings and JavaScript errors
- Application tab → Local Storage: Check JWT token storage (`token` key)

**VS Code debugging:**
- Set breakpoints in Vue/TypeScript code
- Press F5 to launch with debugger attached
- Use configurations in `.vscode/launch.json`

## 実装の注意点とベストプラクティス

### 必須の注意事項

**1. Vue Component Tagsの制約:**
- **Vue component tags must use ASCII names**
- ❌ 誤り: `<C利用者一覧 />` （ブラウザが無効扱い、テキスト表示される）
- ✅ 正解: `<component :is="C利用者一覧" />` （動的コンポーネント）
- ファイル名は日本語OK: `C利用者一覧.vue`
- import名も日本語OK: `import C利用者一覧 from './C利用者一覧.vue'`

**2. 権限IDは文字列型:**
```typescript
// ❌ 誤り
if (authStore.user.権限ID === 1) { ... }

// ✅ 正解
if (authStore.user.権限ID === '1') { ... }
```

**3. TypeScript Strict Mode無効:**
- このプロジェクトは `strict: false` 設定
- 型エラーに寛容（開発速度優先）
- 型定義は `types/` ディレクトリで提供されているので使用推奨

**4. API Response Handling:**
```typescript
// 統一レスポンス形式
interface ApiResponse<T = any> {
  status: 'OK' | 'NG'
  message: string
  data?: T
  error?: any
}

// 使用例
const response = await apiClient.post('/core/C利用者/一覧')
if (response.data.status === 'OK') {
  const items = response.data.data.items
  const total = response.data.data.total
}
```

**5. 日本語URLのリロード:**
- ブラウザでリロードすると日本語URLがエンコードされる
- Router内で `decodeURIComponent` で自動解決
- 開発者は特別な対応不要

**6. JWTトークン期限:**
- トークンは60分で期限切れ
- 期限切れ時は401エラーで自動ログアウト
- 再ログインが必要

### ベストプラクティス

**1. Composition API (script setup) の使用:**
```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const items = ref<any[]>([])
const loading = ref(false)

const fetchItems = async () => {
  loading.value = true
  try {
    const response = await apiClient.post('/core/C利用者/一覧')
    items.value = response.data.data.items
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchItems()
})
</script>
```

**2. qAlert/qConfirm の使用:**
```typescript
import { qAlert, qConfirm } from '@/utils/qAlert'

// アラート
await qAlert('保存しました')

// 確認
const confirmed = await qConfirm('削除してもよろしいですか？')
if (confirmed) {
  // 削除処理
}
```

**3. ルーターナビゲーション:**
```typescript
import { useRouter } from 'vue-router'

const router = useRouter()

// パスで遷移
router.push('/C管理/C利用者/編集')

// 名前付きルートで遷移
router.push({ name: 'C利用者編集', query: { 利用者ID: 'admin' } })

// 戻る
router.back()

// 置き換え（履歴に残さない）
router.replace('/ログイン')
```

**4. エラーハンドリング:**
```typescript
try {
  const response = await apiClient.post('/core/C利用者/登録', data)
  if (response.data.status === 'OK') {
    await qAlert('作成しました')
    router.back()
  } else {
    await qAlert(`エラー: ${response.data.message}`)
  }
} catch (error) {
  console.error(error)
  await qAlert('通信エラーが発生しました')
}
```

**5. qTublerの使用:**
```vue
<template>
  <qTubler
    :columns="columns"
    :data="items"
    :pageSize="20"
    @row-dblclick="handleEdit"
  />
</template>

<script setup lang="ts">
import qTubler from '@/components/_share/qTubler.vue'
import type { Column } from '@/types/qTubler'

const columns: Column[] = [
  { key: 'id', label: 'ID', width: '100px', sortable: true },
  { key: 'name', label: '名前', width: '200px', sortable: true },
]

const handleEdit = (row: any) => {
  router.push({ path: '/編集', query: { id: row.id } })
}
</script>
```

**6. dayjs の使用:**
```typescript
import dayjs from 'dayjs'

// 現在日時
const now = dayjs().format('YYYY-MM-DD HH:mm:ss')

// 日付のフォーマット
const date = dayjs('2025-01-29').format('YYYY年MM月DD日')

// 日付の計算
const tomorrow = dayjs().add(1, 'day').format('YYYY-MM-DD')
```

### よくある落とし穴

**1. 日本語コンポーネントタグ:**
- 日本語タグ名は無効（ブラウザがテキストとして表示）
- 必ず `<component :is="..." />` を使用

**2. 権限IDの型:**
- 数値ではなく文字列型
- `'1'`, `'2'`, `'3'` で比較

**3. TypeScript型エラーを無視しない:**
- Strict mode無効だが、型エラーは適切に対処
- `any` の多用は避ける

**4. ログイン後のリダイレクト:**
- ログイン成功時はレスポンスの `初期ページ` を優先し、未設定なら `/Xその他` へリダイレクト（`stores/auth.ts`）
- 変更する場合は `stores/auth.ts` を修正

**5. WebSocketのリロード対応:**
- AIコアのWebSocket接続はリロード時にソケットIDを保持
- URLクエリパラメータ `?セッションID=<uuid>` で管理

## 注意点
- ログイン画面は開発用にID/パスワードがプリフィル（`admin / ********`）。
- ログイン成功後は `初期ページ` を優先し、未設定なら `/Xその他` に遷移する実装（`stores/auth.ts`）。
- APIクライアントの `baseURL` は `'/'` で、Vite Proxy を前提（`/core` と `/apps` を Vite が転送）。直叩きする場合は baseURL と CORS を合わせる。
- `_TopBar.vue` のサーバー状態取得URLは固定（ポート変更時は要調整）。
- 一覧などで子コンポーネントを呼び出すタグはASCII名で統一（日本語タグはブラウザが無効扱いでテキスト表示される）。
- **Vue component tags must use ASCII names**
- 日本語名を使う場合は `<component :is="日本語コンポーネント名" />` を使用する。
- **ユーザーの指示なしに `dist` を生成しない。** `npm run build` の実行は、明示的に依頼された場合だけ行う。
