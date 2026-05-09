# JWT 認証フロー

> 文書: `backend_server,frontend_web,frontend_avatar,JWT認証フロー.md` | 実装: `backend_server/core_router/auth.py`, `backend_server/auth.py`, `frontend_web/src/api/`, `frontend_avatar/src/api/`

## このメモを使う場面
- ログイン、現在利用者取得、401 ハンドリングを確認する
- 新しい画面や API で JWT を正しく扱う
- `frontend_web` と `frontend_avatar` の storage 差を判断する

## 関連ファイル
- `backend_server/core_router/auth.py` — ログイン、ログアウト、現在利用者、トークン更新
- `backend_server/auth.py` — JWT 生成・検証、有効期限
- `frontend_web/src/api/client.ts` — Axios インターセプター
- `frontend_web/src/stores/auth.ts` — Web 版の認証ストア
- `frontend_avatar/src/api/client.ts` — Avatar 版の Axios インターセプター
- `frontend_avatar/src/api/websocket.ts` — AI 入力送信前のトークン延長

## 基本仕様

| 項目 | 現行仕様 |
|------|----------|
| JWT 方式 | HS256 |
| 有効期限 | 60 分（同期元: `backend_server/auth.py`） |
| 延長 API | `POST /core/auth/トークン更新` |
| 画面ログイン API | `POST /core/auth/ログイン` |
| 現在利用者 API | `POST /core/auth/現在利用者` |
| `frontend_web` storage | `localStorage` |
| `frontend_avatar` Electron storage | `localStorage` |
| `frontend_avatar` Web storage | `sessionStorage` |

`frontend_web` と `frontend_avatar` は認証管理が異なる。Web という表現だけで判断せず、対象が `frontend_web` か `frontend_avatar` の Web モードかを分けて確認する。

## ログインフロー

```text
POST /core/auth/ログイン
body: { 利用者ID, パスワード }
-> { status: "OK", data: { access_token, token_type, 初期ページ } }
-> 対象クライアントの storage に `token` キーで保存
```

- 画面ログインの通常経路は `/core/auth/ログイン`。
- OAuth2 互換の `/core/auth/token` は画面ログインの主経路ではない。
- API 呼び出し時は `Authorization: Bearer <token>` を Axios インターセプターで付与する。

## トークン延長

- 延長 API は `POST /core/auth/トークン更新`。
- 期限切れ後の JWT では延長できない。
- 延長対象外の操作だけを続けると、ログイン中に見えても 60 分で期限切れになる。
- 詳細な延長対象と除外条件は `認証延長ルール.md` を確認する。

## 現在利用者取得

- ログイン直後と画面再表示時は `POST /core/auth/現在利用者` で利用者情報を取得する。
- `frontend_web` は `fetchUser()` 成功時に `localStorage` の `user` を更新する。

## 401 ハンドリング

- `frontend_web`: `client.ts` の response インターセプターが `useAuthStore().logout()` を呼び、`token` / `user` を削除して `/ログイン` へ遷移する。
- `frontend_avatar`: `client.ts` の response インターセプターが `token` / `user` / `avatar_session_id` を削除し、`auth-expired` カスタムイベントを発火する。

401 時の削除キーやイベント名を変更する場合は、Axios インターセプターと画面側ログアウト処理を同時に確認する。

## 注意点

- パスワード保存・照合方式は [`backend_server,C利用者パスワード運用.md`](./backend_server,C利用者パスワード運用.md) を確認する。通常登録はハッシュ保存を前提にし、既存DB互換のため認証側はプレーン保存利用者も照合できるようにする。
- `POST /core/auth/トークン更新` は認証済みトークンを要求するため、失効後の復旧用途には使えない。
- `backend_server/auth.py` の `ACCESS_TOKEN_EXPIRE_MINUTES` を変更した場合は、docs と `.aidiy/knowledge` の「60分」表記を横断検索して更新する。

## 確認方法

```powershell
$login = Invoke-RestMethod -Method Post -Uri "http://localhost:8091/core/auth/ログイン" `
  -ContentType "application/json" `
  -Body '{"利用者ID":"admin","パスワード":"admin"}'

$token = $login.data.access_token
Invoke-RestMethod -Method Post -Uri "http://localhost:8091/core/auth/トークン更新" `
  -Headers @{ Authorization = "Bearer $token" }
```
