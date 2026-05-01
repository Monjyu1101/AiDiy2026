# AIコア WebSocket 仕様

> 文書: `backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md` | 実装: `frontend_avatar/src/api/websocket.ts`, `frontend_avatar/src/AiDiy.vue`, `backend_server/core_router/AIコア/`

## このメモを使う場面
- AIコアの WebSocket 接続、再接続、セッション復元を調査する
- `input_text`、`input_audio` などの送受信形式を確認する
- Electron 補助ウィンドウや Web モードでセッション状態が同期されない原因を切り分ける

## 関連ファイル
- `frontend_avatar/src/api/websocket.ts` — WebSocket クライアント
- `frontend_avatar/src/AiDiy.vue` — コア/入力ソケット、BroadcastChannel、パネル状態
- `frontend_avatar/src/components/AIコア.vue` — 音声ソケット生成
- `backend_server/core_router/AIコア.py` — WebSocket エンドポイント
- `backend_server/core_router/AIコア/AIセッション管理.py` — セッションとモデル設定
- `frontend_avatar/src/api/config.ts` — `AI_WS_ENDPOINT`

## 接続仕様

エンドポイントは `ws://<host>/core/ws/AIコア`。Vite 開発時は frontend の host から生成され、Proxy 経由で backend `8091` へ転送される。

| ソケット番号 | 主な生成箇所 | 用途 |
|-------------|-------------|------|
| `0` | `AiDiy.vue` | AI出力受信、状態制御 |
| `1` | `AiDiy.vue` | テキスト、画像、ファイルなどの入力 |
| `audio` | `AIコア.vue` | `input_audio` 送信、`output_audio` / `cancel_audio` 受信 |
| `chat` / `file` / `code1`〜`code6` | 各パネル | パネル別の出力受信 |

接続時は WebSocket open 後に `{ type: "connect", セッションID, ソケット番号 }` を送信し、サーバーから `{ メッセージ識別: "init", セッションID: "<確定ID>" }` を受けて sessionId が確定する。`connect()` を await せずに送信しない。

## 主要メッセージ形式

```typescript
// テキスト入力
{
  メッセージ識別: "input_text",
  メッセージ内容: "ユーザー入力",
  出力先チャンネル: "0",
  セッションID: "<id>",
}

// AI出力
{
  メッセージ識別: "output",
  チャンネル: "0",
  メッセージ内容: "AIの返答",
}

// 出力完了
{
  メッセージ識別: "output_end",
  チャンネル: "0",
}
```

音声は `audio` チャンネル専用に扱う。

```typescript
// マイクPCM送信
{
  チャンネル: "audio",
  メッセージ識別: "input_audio",
  メッセージ内容: "audio/pcm",
  ファイル名: "<base64 PCM>",
  サムネイル画像: null,
}

// AI音声受信
{
  メッセージ識別: "output_audio",
  チャンネル: "audio",
  メッセージ内容: "audio/pcm",
  ファイル名: "<base64 PCM>",
}

// 音声停止
{
  メッセージ識別: "cancel_audio",
  チャンネル: "audio",
}
```

## セッションと状態共有

- Electron は `localStorage`、Web は `sessionStorage` に `token` / `user` / `avatar_session_id` を保持する
- Web モードは URL の `?セッションID=` も参照し、リロード復帰しやすくする
- Electron 補助ウィンドウは BroadcastChannel `avatar-desktop-sync` の snapshot で sessionId と状態を受け取る
- 401 時は `apiClient` が認証情報を削除し、`auth-expired` イベント経由でログインへ戻す

パネル状態を追加する場合は、`SharedSnapshot` 型、`buildSnapshot()`、受信側反映処理、Electron の `WindowRole` / `PanelKey` をセットで確認する。

## トークン延長ルール

送信前に `/core/auth/トークン更新` を呼ぶ対象:
- `input_text`
- `input_file`
- `input_image`
- `input_request`
- AIファイル `files_temp`

延長しない対象:
- `input_audio`（高頻度送信のため）
- `operations`
- `cancel_run`
- `cancel_audio`

## 注意点

- sessionId は `init` 受信後に確定する
- 明示的に `disconnect()` すると自動再接続は止まる
- Electron と Web で Storage が違うため、調査時は実行モードを先に確認する
- Vite 開発時の Network では `8099/core/ws/...` に見えても、実体は Proxy 先の `8091` で処理される
- Code AI パネルは現行 `code1`〜`code6` 前提。実装確認は `frontend_avatar/src/AiDiy.vue`、`frontend_web/src/components/AiDiy/AiDiy.vue`、`backend_server/core_router/AIコア.py` を見る

## 確認方法

- ブラウザ DevTools の Network で WebSocket frames を確認する
- 接続直後に `connect` 送信と `init` 受信が見えることを確認する
- 音声調査では `audio` チャンネルに `input_audio` / `output_audio` / `cancel_audio` が流れることを確認する
