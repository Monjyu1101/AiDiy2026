# AI入力系認証延長

## 参照する場面
- `frontend_avatar` のAIファイル画面を開いたままにすると、JWTの60分期限で認証切れする問題を扱うとき
- `frontend_web` のAIファイルと同じ「画面表示中は操作中」とみなす認証延長をAvatar側へ反映するとき
- 音声以外のAI入力系メッセージで、送信時にJWTを延長したいとき
- S系スケジュール表示やV系表示の更新日監視で、画面表示中のJWTを延長したいとき
- C/M/T系画面の登録・更新・削除・検索など、ボタン操作に紐づくAPI送信時にJWTを延長したいとき

## 関連ファイル
- `frontend_avatar/src/components/AIファイル.vue`
- `frontend_avatar/src/api/websocket.ts`
- `frontend_avatar/src/api/client.ts`
- `frontend_web/src/api/websocket.ts`
- `frontend_web/src/components/Sスケジューラー/S配車_週表示.vue`
- `frontend_web/src/components/Sスケジューラー/S配車_日表示.vue`
- `frontend_web/src/components/Sスケジューラー/S生産_週表示.vue`
- `frontend_web/src/components/Sスケジューラー/S生産_日表示.vue`
- `frontend_web/src/components/Vビュー/V商品推移表.vue`
- `frontend_web/src/api/client.ts`
- `frontend_web/src/stores/auth.ts`
- `backend_server/core_router/auth.py`
- `backend_server/auth.py`

## 実装の結論
- JWT期限は `backend_server/auth.py` の `ACCESS_TOKEN_EXPIRE_MINUTES = 60`
- トークン延長APIは `POST /core/auth/トークン更新`
- AvatarはPinia認証ストアを持たないため、`AIファイル.vue` 内で `window.desktopApi ? localStorage : sessionStorage` を使い、返却された `access_token` を保存する
- `files_temp` 送信時に `認証トークン更新()` を非同期実行する
- 音声以外のAI入力系は `AIWebSocket.send()` で `input_text` / `input_file` / `input_image` / `input_request` のみを対象にトークン更新する
- `input_audio`、`operations`、`cancel_audio`、`cancel_run` は認証延長対象外にする
- S系スケジュール表示とV商品推移表は、30秒ごとの `checkForUpdates()` 実行時に `useAuthStore().refreshToken()` を呼ぶ
- 更新が実際にあって再描画される場合だけでなく、最終更新日時を監視するタイミング自体を「画面表示中」とみなして延長する
- C/M/T系画面のボタン操作は `frontend_web/src/api/client.ts` のリクエストインターセプターで延長する
- 対象URLは `/core/C*`、`/core/V*`、`/apps/M*`、`/apps/T*`、`/apps/V*` のPOST
- C/M/Tの検索一覧はV系JOIN APIを使うため、V系URLも対象に含める

## 注意点
- 401時のトークン削除と `auth-expired` イベント発火は `frontend_avatar/src/api/client.ts` のAxiosインターセプターに任せる
- `files_temp` は5秒間隔で自動送信されるため、同時更新を避ける `トークン更新中` ガードを置く
- Web版の `frontend_web/src/components/AiDiy/compornents/AIファイル.vue` は `authStore.refreshToken()` を使うが、Avatar側には同じストアがない
- Web版の入力系は `frontend_web/src/api/websocket.ts` から `useAuthStore().refreshToken()` を呼ぶ
- Avatar版の入力系は `frontend_avatar/src/api/websocket.ts` で認証Storageへ直接トークンを書き戻す
- S/Vの更新日監視はWeb画面だけの処理なので、Avatar側ではなく `frontend_web` の各画面コンポーネントで対応する
- リクエストインターセプター内の延長は `/core/auth/トークン更新` 自体を対象にしない。対象にすると再帰する
- 複数APIが同時に走る画面があるため、`操作系認証更新Promise` で同時更新を束ねる

## 確認方法
- `frontend_avatar` で `npm run type-check`
- `frontend_web` で `npm run type-check`
- AIファイル画面を開き、`files_temp` 要求時に `/core/auth/トークン更新` が呼ばれることをブラウザ/Electron DevToolsで確認する
- チャット送信、ファイル添付、イメージ送信、コード要求送信時に `/core/auth/トークン更新` が呼ばれることを確認する
- S配車/S生産の週・日表示、V商品推移表を開き、30秒ごとの最終更新日時監視時に `/core/auth/トークン更新` が呼ばれることを確認する
- C/M/T画面の検索、登録、更新、削除ボタンで `/core/auth/トークン更新` が先に呼ばれることを確認する
