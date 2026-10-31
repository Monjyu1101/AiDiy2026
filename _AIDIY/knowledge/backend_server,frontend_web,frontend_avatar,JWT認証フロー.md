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
| 有効期限 | 600 分（同期元: `backend_server/auth.py`） |
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
- 延長対象外の操作だけを続けると、ログイン中に見えても 600 分で期限切れになる。
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
- `backend_server/auth.py` の `ACCESS_TOKEN_EXPIRE_MINUTES` を変更した場合は、docs と `_AIDIY/knowledge` の有効期限表記を横断検索して更新する。

## 確認方法

```powershell
$login = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8091/core/auth/ログイン" `
  -ContentType "application/json" `
  -Body '{"利用者ID":"admin","パスワード":"admin"}'

$token = $login.data.access_token
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8091/core/auth/トークン更新" `
  -Headers @{ Authorization = "Bearer $token" }
```

## 環境固有鍵と午前3時の更新

- 公開固定署名鍵は使わない。通常ログインと Core 内部通信には、環境ごと・世代ごとに別のランダム鍵を生成する。
- 秘密鍵一覧はプロジェクトルートの `_AIDIY/backend_core/internal_auth_keys.json`。クライアント用 `_AIDIY/backend_core/internal_auth.json` には **署名鍵を入れない**。Core と TaskTeam の鍵・内部トークンは別サービス用で、相互利用できない。
- Core 起動時、最新鍵・内部トークンが25時間の有効期間内なら同じものを再利用する。午前3時を過ぎた起動でも、有効な最新世代を直ちに交換しない。期限外・初回のみ新世代を作る。壊れた既存秘密鍵一覧は上書きせず起動失敗にする。
- 稼働中は OS ローカル午前3時の周期を日付で判定し、1周期に1回更新する（約1秒間隔）。午前3時より前でも最新世代が期限切れになれば更新する。時刻が最新世代の発行時刻より前へ戻った場合は、秘密ファイルを変更せず安全側で停止・再試行する。
- 新世代へ移した旧鍵は、発行済み内部トークンと通常JWTの最大期限まで検証に使う。通常JWTの発行時に、その実際の期限を排他制御下で記録する。期限が過ぎた旧世代を削除し、保存世代数にも上限を設ける。
- 通常ログインJWTの期限は従来どおり600分（10時間）。内部トークンは25時間。起動時再利用は「再起動だけを理由とするログイン失効」を防ぐもので、無操作でも丸一日ログインを保証するものではない。トークン更新APIは最新鍵で発行し直す。
- 通常JWTは `kid`・`iss`・`aud`・`token_kind`・`iat`・`exp` を検証する。**旧公開固定鍵で発行したJWTは移行時に引き継がず、初回だけ再ログインが必要**。
- Apps は Core の秘密鍵一覧を読んで通常JWTを検証するだけで、鍵を生成・更新しない。Core 初期化より早い要求には503を返し、次の要求で再読込する。Apps独自の内部トークンは作らない。
- 別PCへ同じ秘密鍵一覧をコピーすると環境分離が失われる。配布物やGitへ秘密ファイルを含めない。

## ローカル連携の内部認証

- クライアント用 JSON は `access_token`、`token_type: "bearer"`、UTC ISO 8601 の `issued_at` / `expires_at`。パスは起動 CWD に依存しない。
- ローカル Code / Live / Discord / Slack は接続・HTTP要求ごとにトークンファイルを再読込する。トークンを URL、ログ、ブラウザー storage、リモート宛先へ流さない。
- 内部トークンは通常利用者へのなりすましではない。対象はモデル情報取得、セッション内のモデル設定、AIコアWebSocket。通常利用者API・ログイン更新・設定ファイル保存・リセット・再起動要求には使えない。
- Web / Avatar / Diag は通常ログインJWTを使用する。初期化APIは通常JWT専用。モデル情報の対象セッションとWebSocket接続には認証主体の一致を要求する。同じ通常利用者は再発行JWTでも同じセッションを利用できるが、通常利用者と内部連携のセッションは混用しない。
- HTTP と Node WebSocket は `Authorization: Bearer ...`。ブラウザー WebSocket は `['aidiy-auth', 'bearer.<JWT>']` のサブプロトコルで渡し、サーバーは認証成功後だけ `aidiy-auth` を選択して accept する。HTTP要求とWS接続時に期限を確認し、接続済みWSのハンドシェイクJWT期限による強制切断はしない。
- 秘密鍵一覧の原子的保存を先に完了し、クライアント用トークンを後から公開する。後段の保存失敗・ファイル欠落時は、同じ最新世代の保存済みトークンを再公開する。不要な再生成はしない。
- POSIXでは保存ディレクトリ0700・ファイル0600。WindowsではOS側ACLも管理する。Core/Apps間の競合はOSファイルロックと原子的置換で防ぐ。ログへ鍵・トークン・例外引数を出さない。
- 全階層の `internal_auth.json`、`internal_auth_keys.json` と対応する非公開一時ファイルは Git・AIバックアップ対象外。汎用ファイル内容取得/更新APIとIDEの閲覧経路も拒否する。Git除外は暗号化ではなく、同じOSユーザーのファイルアクセスを禁止するものでもない。
- `/core/サーバー状態` はログイン前のシアンバー用に公開を維持する。パスワード管理・MFA・全APIの権限再設計はこの変更の対象ではない。

実サービス・実DB・実資格情報を使わない確認:

```sh
backend_server/.venv/bin/python -m unittest discover -s backend_server/checks -p test_auth_keyring.py -v
backend_server/.venv/bin/python -m unittest discover -s backend_server/checks -p test_internal_auth.py -v
```
