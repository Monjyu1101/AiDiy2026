# JWT 認証フロー

## 参照する場面
- 認証が通らない / 401 エラーが頻発する
- トークンの有効期限延長の仕組みを把握したい
- 新しい画面や API でトークンを正しく扱いたい

## 関連ファイル
- `backend_server/core_router/auth.py` — ログイン・ログアウト・現在利用者・トークン更新エンドポイント
- `backend_server/auth.py` — JWT 生成・検証、有効期限
- `frontend_web/src/api/client.ts` — Axios インターセプター（トークン自動付与・401 ハンドリング）
- `frontend_web/src/stores/auth.ts` — Web 版のログイン状態、`refreshToken()`、storage 保存
- `frontend_avatar/src/api/client.ts` — avatar 版（Electron/Web で storage を切り替え）
- `frontend_avatar/src/api/websocket.ts` — AI 入力送信前のトークン延長

## 認証仕様

| 項目 | 値 |
|------|-----|
| トークン形式 | JWT（HS256） |
| 有効期限 | 60 分 |
| 延長 API | `POST /core/auth/トークン更新` |
| storage（frontend_web） | `localStorage` |
| storage（frontend_avatar Electron） | `localStorage` |
| storage（frontend_avatar Web） | `sessionStorage` |

`frontend_web` と `frontend_avatar` は認証管理の作りが違う。Web という語だけで判断せず、対象が `frontend_web` なのか `frontend_avatar` の Web モードなのかを必ず分ける。

## 実装の結論

### ログインフロー

```
POST /core/auth/ログイン
  body: { 利用者ID, パスワード }
  → 200: { status: "OK", data: { access_token: "eyJ...", token_type: "bearer", 初期ページ: "..." } }
  → 対象クライアントの storage に `token` キーで保存
```

OAuth2 互換の `POST /core/auth/token` もあるが、画面ログインの通常経路は `/core/auth/ログイン` を使う。

### API 呼び出し時のヘッダー

```
Authorization: Bearer eyJ...
```

Axios インターセプターが自動付与（`client.ts` の `request` インターセプター）。

### トークン延長

詳細な延長対象は `認証延長ルール.md` にまとめる。認証フロー側では以下だけ押さえる。

- 延長 API は `POST /core/auth/トークン更新`
- 期限切れ後のトークンでは延長できない
- 延長対象外の操作だけを続けると、ログイン中に見えても 60 分で期限切れになる

### 現在利用者の取得

ログイン直後と画面再表示時は `POST /core/auth/現在利用者` で利用者情報を取得する。`frontend_web` では `fetchUser()` が成功した利用者情報を `localStorage` の `user` に保存する。

### 401 受信時

`frontend_web` は `client.ts` の `response` インターセプターが `useAuthStore().logout()` を呼び、`localStorage` の `token` / `user` を削除して `/ログイン` へ遷移する。

`frontend_avatar` は `client.ts` の `response` インターセプターが `token` / `user` / `avatar_session_id` を storage から削除し、`auth-expired` カスタムイベントを発火する。`AiDiy.vue` 側のログアウト処理と合わせて確認する。

## 再発しやすい注意点

- **パスワードは平文保存**（現状の仕様） — ハッシュ化は将来課題
- `frontend_web` は `localStorage`。`frontend_avatar` は Electron が `localStorage`、Web モードが `sessionStorage`
- 延長対象でない操作が連続する場合（音声入力のみ30分など）はトークンが切れる — 現状の仕様
- `POST /core/auth/トークン更新` は認証済みトークンを必要とする — 期限切れ後に呼んでも更新できない
- 401時の削除キーやイベント名を変える場合は、`client.ts` とログアウト処理側を同時に確認する
- `backend_server/auth.py` の `ACCESS_TOKEN_EXPIRE_MINUTES` を変更した場合は、docs と `.aidiy/knowledge` の「60分」表記も横断検索して追従する

## 確認方法

```bash
# ログイン
curl -X POST http://localhost:8091/core/auth/ログイン \
  -H "Content-Type: application/json" \
  -d '{"利用者ID":"admin","パスワード":"admin"}'

# トークン更新
curl -X POST http://localhost:8091/core/auth/トークン更新 \
  -H "Authorization: Bearer <token>"
```
