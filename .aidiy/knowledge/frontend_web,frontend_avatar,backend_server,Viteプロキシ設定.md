# Vite プロキシ設定

> 文書: `frontend_web,frontend_avatar,backend_server,Viteプロキシ設定.md` | 実装: `frontend_web/vite.config.ts`, `frontend_avatar/vite.config.ts`

## このメモを使う場面
- フロントから API を呼ぶと CORS エラーになる
- Vite / backend のポートを変更する
- HTTP API と WebSocket のプロキシ経路を確認する

## 関連ファイル
- `frontend_web/vite.config.ts` — Web 用 Vite Proxy（port 8090）
- `frontend_avatar/vite.config.ts` — Avatar 用 Vite Proxy（port 8099）
- `frontend_web/src/api/client.ts` — `baseURL: '/'` 前提の Axios クライアント
- `frontend_avatar/src/api/config.ts` — `VITE_CORE_BASE_URL` / `VITE_CORE_WS_URL` の解決
- `backend_server/core_main.py` — CORS 許可リスト
- `backend_server/apps_main.py` — CORS 許可リスト

## 開発時の経路

```text
ブラウザ → Vite dev server (8090/8099)
        → /core/* → backend core (8091)
        → /apps/* → backend apps (8092)
```

- 画面側では `/core/...` または `/apps/...` の相対URLだけを書く。
- backend の `http://127.0.0.1:8091` / `8092` をコンポーネントへ直書きしない。
- 本番では Vite dev server がいないため、Nginx 等で同等の `/core` / `/apps` プロキシを用意する。

## proxy 設定の基準

```typescript
proxy: {
  '/core': { target: 'http://127.0.0.1:8091', changeOrigin: true, ws: true },
  '/apps': { target: 'http://127.0.0.1:8092', changeOrigin: true, ws: true },
}
```

- `ws: true` は WebSocket 転送に必要。AIコアの `ws://localhost:8090/core/ws/AIコア` も backend core へ転送される。
- `/core` / `/apps` の prefix は backend 側エンドポイントでも使うため、rewrite で削らない。
- `frontend_avatar` は `strictPort: true`。WebSocket URL を host から動的生成するため 8099 固定が前提。

## 現行ポート

| 対象 | ポート |
|------|--------|
| `frontend_web` | 8090 |
| `frontend_avatar` | 8099 |
| `backend_server/core_main.py` | 8091 |
| `backend_server/apps_main.py` | 8092 |

## ポート変更時の手順
1. `frontend_web/vite.config.ts` または `frontend_avatar/vite.config.ts` の `server.port` を更新する。
2. `backend_server/core_main.py` / `apps_main.py` の CORS origins にフロントの新URLを追加する。
3. 固定URLを参照している表示部品（例: `_TopBar.vue` のサーバー状態表示）を確認する。
4. `frontend_avatar` で明示 URL を使う場合は `VITE_CORE_BASE_URL` / `VITE_CORE_WS_URL` も更新する。
5. ブラウザの origin が変わるため、保存済み token / localStorage / sessionStorage を確認する。

```python
origins = [
    "http://localhost:8090",
    "http://localhost:8099",
    "http://localhost:5173",
]
```

## Avatar の接続先解決

`frontend_avatar/src/api/config.ts` の優先順:

1. `VITE_CORE_BASE_URL` / `VITE_CORE_WS_URL`
2. 開発時: `'/'` または `window.location.host` から生成した WebSocket URL
3. 本番: `http://127.0.0.1:8091`

Electron と Web で同じ proxy 前提にできるよう、明示 URL を増やす場合は両モードで確認する。

## 注意点
- CORS エラーではまず `core_main.py` / `apps_main.py` の許可リストを見る。
- `localhost` と `127.0.0.1` はブラウザ上の origin が別。CORS、Storage、ログイン状態で混同しない。
- Vite dev server を介さず `http://localhost:8091/core/...` へ直アクセスすると、Origin 条件が通常の画面確認と変わる。
- 静的X系の `public/<画面名>/index.html` は Vite がそのまま配信する。404 の場合は proxy ではなく `public` パス、`BASE_URL`、日本語URLエンコードを疑う。

## 確認方法

```powershell
cd frontend_web
npm run dev
Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8090/core/サーバー状態'
```

- DevTools Network で `OPTIONS` が 200 を返すか、`Access-Control-Allow-Origin` が付くかを確認する。
- `/apps` は POST 中心なので、ログイン後に既存画面の `/apps/V商品/一覧` などを Network で確認する。
- WebSocket は AIコア画面で `101 Switching Protocols` または接続済み状態を確認する。
