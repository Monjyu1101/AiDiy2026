# Vite プロキシ設定

## 参照する場面
- フロントから API を呼ぶと CORS エラーになる
- ポートを変更したい
- 開発時と本番で接続先が変わる仕組みを把握したい

## 関連ファイル
- `frontend_web/vite.config.ts` — Vite Proxy 設定（port 8090）
- `frontend_avatar/vite.config.ts` — Avatar 用 Proxy 設定（port 8099）
- `backend_server/core_main.py` — CORS 許可リスト
- `backend_server/apps_main.py` — CORS 許可リスト

## Vite Proxy の仕組み

開発時（`npm run dev`）は Vite がリバースプロキシとして機能する。

```
ブラウザ  →  Vite dev server (8090)  →  /core/* → backend core (8091)
                                      →  /apps/* → backend apps (8092)
```

本番（`npm run build` 後）は Vite がいないため、Nginx 等で同等のプロキシが必要。

`frontend_web/src/api/client.ts` の `baseURL` は `'/'` 前提なので、画面側では `/core/...` または `/apps/...` の相対URLだけを書く。バックエンドの `http://127.0.0.1:8091` / `8092` をコンポーネントに直書きすると、開発プロキシ、CORS、本番配置の前提が崩れる。

### `ws: true` の意味

`vite.config.ts` の proxy エントリに `ws: true` を設定すると、HTTP とWebSocket の両方が同じプレフィックスでプロキシされる。

```typescript
// frontend_web/vite.config.ts
proxy: {
  '/core': { target: 'http://127.0.0.1:8091', changeOrigin: true, ws: true },
  '/apps': { target: 'http://127.0.0.1:8092', changeOrigin: true, ws: true },
}
```

AIコアの WebSocket `ws://localhost:8090/core/ws/AIコア` も Vite が `ws://127.0.0.1:8091/core/ws/AIコア` へ転送する。`ws: true` がないと WS 接続だけ CORS エラーになる。

### `frontend_avatar` の vite.config.ts

Avatar 側も同じ構造だが `strictPort: true` が追加されている。

```typescript
// frontend_avatar/vite.config.ts
server: {
  host: '127.0.0.1',
  port: 8099,
  strictPort: true,   // 8099 使用中の場合フォールバックせずエラー終了
  proxy: {
    '/core': { target: 'http://127.0.0.1:8091', changeOrigin: true, ws: true },
    '/apps': { target: 'http://127.0.0.1:8092', changeOrigin: true, ws: true },
  },
}
```

`frontend_web` は `strictPort` なし（空きポートへフォールバックあり）。Avatar は WebSocket エンドポイントを URL から動的生成するため、8099 固定が前提。

## 現行ポート

| 対象 | ポート |
|------|--------|
| `frontend_web` | 8090 |
| `frontend_avatar` | 8099 |
| `backend_server/core_main.py` | 8091 |
| `backend_server/apps_main.py` | 8092 |

## ポート変更時の更新箇所

フロントのポートを変更する場合は **必ず** CORS 許可リストも更新する。

```python
# core_main.py / apps_main.py
origins = [
    "http://localhost:8090",  # frontend_web
    "http://localhost:8099",  # frontend_avatar
    "http://localhost:5173",  # Vite デフォルト（開発時フォールバック）
    "http://localhost:3000",  # 追加が必要な場合
]
```

合わせて確認する箇所:

- `frontend_web/vite.config.ts` の `server.port`
- `backend_server/core_main.py` / `apps_main.py` の CORS origins
- `_TopBar.vue` など、サーバー状態表示で固定URLを参照している箇所
- ブラウザに保存済みの古いURLやブックマーク
- `frontend_avatar` も同じ backend を見る場合は `frontend_avatar/vite.config.ts` と `VITE_CORE_BASE_URL` / `VITE_CORE_WS_URL`

## 環境変数による接続先切り替え

`frontend_avatar/src/api/config.ts` の URL 解決優先順：

1. 環境変数 `VITE_CORE_BASE_URL`（明示指定）
2. 開発時（`import.meta.env.DEV`）: `'/'`（Vite Proxy 経由）
3. 本番: `'http://127.0.0.1:8091'`

WebSocket も同様（`VITE_CORE_WS_URL`）。

## 再発しやすい注意点

- CORS エラーが出たらまず `core_main.py` / `apps_main.py` の許可リストを確認
- 開発時の Vite Proxy はクロスオリジン問題を隠蔽する — 本番では Nginx 設定が必要
- `frontend_avatar` の WebSocket は `window.location.host` から動的生成されるため、ホスト名変更には追随しやすい。ただし `VITE_CORE_WS_URL` を明示した場合はその値が優先される
- Vite dev server を介さず `http://localhost:8091/core/...` のように直アクセスすると、ブラウザ側では CORS とCookie/Storage/Origin条件が開発時と変わる。フロント動作確認は原則 `http://localhost:8090` から行う。
- `localhost` と `127.0.0.1` はブラウザ上の origin が別扱い。CORS許可、localStorage の token、ログイン状態確認では混同しない。
- `/core` `/apps` の proxy は prefix を残したまま backend へ転送する前提。backend 側エンドポイントも `/core/...` `/apps/...` で定義されているため、rewrite を追加しない。
- 静的X系の `public/<画面名>/index.html` は Vite がそのまま配信する。API proxy とは別経路なので、静的ファイルが404の場合は proxy ではなく `public` パス、`import.meta.env.BASE_URL`、日本語URLエンコードを疑う。

## 確認方法

ブラウザ DevTools の Network タブで `OPTIONS` リクエストが 200 を返しているか確認。  
CORS エラーの場合は `Access-Control-Allow-Origin` ヘッダーが欠けているか確認。

API proxy の疎通確認例:

```powershell
cd frontend_web
npm run dev
Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8090/core/サーバー状態'
```

`/apps` 側は POST 中心なので、ブラウザ DevTools Network で既存画面の `/apps/V商品/一覧` などを確認する。ログイン前に確認する場合は、まず `/ログイン` から認証して token が `localStorage` に入っている状態で業務画面を開く。
