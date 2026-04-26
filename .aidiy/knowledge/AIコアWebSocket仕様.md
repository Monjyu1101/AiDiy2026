# AIコア WebSocket 接続仕様

## このメモを使う場面
- AIコアへの WebSocket 接続が繋がらない / 切れる
- 新しいメッセージタイプを送受信したい
- WebSocket 周りを修正するときに挙動を把握したい

## 関連ファイル
- `frontend_avatar/src/api/websocket.ts` — WebSocket クライアント実装
- `frontend_avatar/src/AiDiy.vue` — コアソケット / 入力ソケットの接続管理
- `backend_server/core_router/AIコア.py` — サーバー側 WebSocket エンドポイント
- `backend_server/core_router/AIコア/AIセッション管理.py` — セッション管理

## 接続仕様

### エンドポイント

```
ws://<host>/core/ws/AIコア
```

`src/api/config.ts` の `AI_WS_ENDPOINT` で定義。Vite 開発時は `window.location.host` から動的生成。

### ソケット構成

`AiDiy.vue` は 2 本の WebSocket を管理する。

| ソケット | 用途 |
|---------|------|
| コアソケット（ソケット番号=`'0'`） | AI 出力受信・各種制御メッセージ |
| 入力ソケット（ソケット番号=`'1'`） | テキスト入力・画像・ファイルなどの送信 |

音声処理用の `audioSocket` は `AIコア.vue` で `new AIWebSocket(AI_WS_ENDPOINT, props.sessionId, 'audio')` として生成し、`AudioController` へ渡す。メインの入力ソケットとは別接続にする。

| ソケット番号 | 主な生成箇所 | 用途 |
|-------------|-------------|------|
| `'0'` | `AiDiy.vue` | core 出力受信、状態制御 |
| `'1'` | `AiDiy.vue` | テキスト・画像・ファイルなどの入力 |
| `'audio'` | `AIコア.vue` | `input_audio` 送信、`output_audio` / `cancel_audio` 受信 |
| `chat` / `file` / `code1`〜`code4` | 各パネルコンポーネント | パネル別の出力受信 |

### 接続シーケンス

1. `connect()` 呼び出し
2. WebSocket open 後、`{ type: 'connect', セッションID, ソケット番号 }` を送信
3. サーバーから `{ メッセージ識別: 'init', セッションID: <確定ID> }` を受信
4. `connect()` の Promise が resolve（セッション ID が確定）

再接続は最大 5 回、3 秒間隔で自動実施。タイムアウトは 30 秒。

### セッション ID と Storage

- Electron は `localStorage`、Web は `sessionStorage` に `token` / `user` / `avatar_session_id` を保持する
- Web モードは URL の `?セッションID=` も読む。`/AiDiy?セッションID=<id>` に同期してリロード復帰しやすくしている
- Electron の補助ウィンドウは URL ではなく BroadcastChannel `avatar-desktop-sync` の snapshot で sessionId と状態を受け取る
- 401 時は `apiClient` 側で認証情報を削除し、`auth-expired` イベント経由でログインへ戻す

`avatar_session_id` の保存先は `AiDiy.vue` の `認証Storage` に依存する。調査時は Electron なら DevTools の `localStorage`、Web なら `sessionStorage` を見る。

### 主要メッセージ形式

```typescript
// 送信（テキスト入力）
{
  メッセージ識別: 'input_text',
  メッセージ内容: 'ユーザーの入力テキスト',
  出力先チャンネル: '0',
  セッションID: '<id>',
}

// 受信（AI 出力）
{
  メッセージ識別: 'output',
  チャンネル: '0',
  メッセージ内容: 'AI の返答テキスト',
}

// 受信（処理完了）
{
  メッセージ識別: 'output_end',
  チャンネル: '0',
}
```

### 音声メッセージ形式

```typescript
// 送信（マイク PCM）
{
  チャンネル: 'audio',
  メッセージ識別: 'input_audio',
  メッセージ内容: 'audio/pcm',
  ファイル名: '<base64 PCM>',
  サムネイル画像: null,
}

// 受信（AI 音声）
{
  メッセージ識別: 'output_audio',
  チャンネル: 'audio',
  メッセージ内容: 'audio/pcm',
  ファイル名: '<base64 PCM>',
}

// 受信または送信（音声停止）
{
  メッセージ識別: 'cancel_audio',
  チャンネル: 'audio',
}
```

`input_audio` は高頻度送信のためトークン延長対象外。音声停止は `AudioController.cancelOutput()` でローカルキューを止め、必要な場合だけ `cancel_audio` をサーバーへ通知する。

## BroadcastChannel snapshot の使い分け

Electron の補助パネルは別 BrowserWindow なので、Vue の親子 props だけでは状態共有できない。`AiDiy.vue` が `SharedSnapshot` を作り、BroadcastChannel `avatar-desktop-sync` で次を配信する。

- 認証状態、利用者ラベル
- セッション ID
- メッセージ一覧、チャットモード
- モデル設定
- 入力 / チャット接続状態
- パネル表示状態
- 処理中 / エラー状態

Web モードでは単一タブ内の状態で完結するが、同じ `AiDiy.vue` を使うため snapshot 更新の副作用を完全には無視しない。パネル用状態を追加するときは `SharedSnapshot` 型、`buildSnapshot()`、受信側反映処理をセットで見る。

### メッセージハンドラーの登録

```typescript
const ws = new AiWebSocket(endpoint, sessionId)
await ws.connect()

// 特定種別のみ受信
ws.on('output', (msg) => { /* ... */ })
ws.on('output_end', (msg) => { /* ... */ })

// チャンネルつき受信（'output_0' のように種別_チャンネルでも登録可）
ws.on('output_0', (msg) => { /* channel 0 のみ */ })

// 全メッセージ受信
ws.on('*', (msg) => { console.log(msg) })
```

## トークン延長ルール

AI 入力送信前に `/core/auth/トークン更新` を呼ぶ対象：
- `input_text`, `input_file`, `input_image`, `input_request`
- AIファイル `files_temp`

延長しない対象:
- `input_audio`（音声は高頻度送信のため除外）
- `operations`, `cancel_run`, `cancel_audio`

## 再発しやすい注意点

- `connect()` を await せずに `send()` を呼ぶとメッセージが無視される
- セッション ID は `init` メッセージ受信後に確定する — それ以前の値は暫定
- BroadcastChannel の snapshot 経由で補助ウィンドウにセッション ID を渡す — 直接 API 呼び出しは不要
- Web モードは `sessionStorage` のため、タブを閉じると認証情報が消える。Electron の `localStorage` 前提で調査しない
- `AI_WS_ENDPOINT` は開発時に `window.location.host` から作るため、Network では `8099/core/ws/AIコア` に見えることがある。Vite Proxy で backend `8091` へ流れる
- `disconnect()` を呼ぶと自動再接続が止まる — 明示的に切断したい場合のみ使う
- Vite 開発時は Proxy を経由するため `ws://localhost:8099/core/ws/...` → `ws://localhost:8091/core/ws/...` に内部変換される

## 確認方法

ブラウザ DevTools の Network タブで WebSocket フレームを確認。  
接続済みなら `{ type: 'connect', ... }` と `{ メッセージ識別: 'init', ... }` の往復が見える。
