# AIコア WebSocket 仕様

> 文書: `backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md` | 実装: `frontend_avatar/src/api/websocket.ts`, `frontend_avatar/src/AiDiy.vue`, `backend_server/AIコア/`

## このメモを使う場面
- AIコアの WebSocket 接続、再接続、セッション復元を調査する
- `input_text`、`input_audio` などの送受信形式を確認する
- Electron 補助ウィンドウや Web モードでセッション状態が同期されない原因を切り分ける

## 関連ファイル
- `frontend_avatar/src/api/websocket.ts` — WebSocket クライアント
- `frontend_avatar/src/AiDiy.vue` — コア/入力ソケット、BroadcastChannel、パネル状態
- `frontend_avatar/src/components/AIコア.vue` — 音声ソケット生成
- `backend_server/core_router/AIコア.py` — WebSocket エンドポイント
- `backend_server/AIコア/AIセッション管理.py` — セッションとモデル設定
- `frontend_avatar/src/api/config.ts` — `AI_WS_ENDPOINT`

## 接続仕様

エンドポイントは `ws://<host>/core/ws/AIコア`。Vite 開発時は frontend の host から生成され、Proxy 経由で backend `8091` へ転送される。

| ソケット番号 | 主な生成箇所 | 用途 |
|-------------|-------------|------|
| `0` | `AiDiy.vue` | AI出力受信、状態制御 |
| `1` | `AiDiy.vue` | テキスト、画像、ファイルなどの入力 |
| `audio` | `AIコア.vue` | `input_audio` 送信、`output_audio` / `cancel_audio` 受信 |
| `chat` / `file` / `code1`〜`code6` | 各パネル | パネル別の出力受信 |

接続時は WebSocket open 後に `{ type: "connect", セッションID, ソケット番号, CODE_BASE_PATH?, モデル設定? }` を送信し、サーバーから `{ メッセージ識別: "init", セッションID: "<確定ID>" }` を受けて sessionId が確定する。`connect()` を await せずに送信しない。

Avatar / Web の音声接続は、core ソケットの `init` に含まれるモデル設定と `CODE_BASE_PATH` が反映されてから開始する。WebSocket の `open` だけで入力接続済みにすると、既存セッションの復元時に空のフォルダ指定で音声接続し、設定受信後に再接続するため、Live の準備通知が二重になる。

接続待ちの音声ソケットも保持し、フォルダ変更・切断・画面破棄時に閉じる。旧ソケットの遅延イベントで新しい接続状態を上書きしない。接続順序と競合の検証は、Avatar の依存関係を導入した環境で `node --test frontend_avatar/checks/audio-connection.test.cjs` を実行する（リポジトリルートから）。

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

Code AI の `output_stream` は、本文と同じパケットの `メッセージ内容` に次の ASCII 制御値を入れて境界を通知する。制御値は1バイトだけで送り、LF (`0x0A`) を含めない。

| 状態 | `メッセージ内容` | バイト |
|------|----------------------|--------|
| 開始 | `STX` | `0x02` |
| 終了 | `ETX` | `0x03` |
| 中断・異常 | `CAN` | `0x18` |

制御値は表示文字列ではない。Web / Avatar は状態遷移にだけ使い、メッセージ本文、演出キュー、デバッグ表示へは追加しない。通常のストリーム本文は末尾の CR / LF を取り除いてから表示側で LF を1つ付け、二重改行を防ぐ。将来制御値を廃止するときは、backend の `AIストリーム制御.py` と frontend の `AIストリーム制御.ts` を入口にする。

音声は `audio` チャンネル専用に扱う。

接続維持用の `{ type: "ping" }` は、通常の `メッセージ識別` を持つパケットより先に処理する。バックエンドは受信したソケットへ `{ type: "pong", セッションID: "<確定ID>" }` を返し、AI処理や会話履歴へ渡さない。VS Code Live / Web / Avatar はJSON形式、現行DiscordはWebSocket制御フレームのpingを使うため、両者を区別する。`不明なメッセージ識別: None data={"type":"ping", ...}` はバックエンドのJSON heartbeat受け口を確認する。`backend_server/tests/test_live_project_connection.py` でpong応答後も音声処理を続けることを検証する。

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
- Vite 開発時の Network では `8092/core/ws/...` に見えても、実体は Proxy 先の `8091` で処理される
- Code AI パネルは現行 `code1`〜`code6` 前提。実装確認は `frontend_avatar/src/AiDiy.vue`、`frontend_web/src/components/AiDiy/AiDiy.vue`、`backend_server/core_router/AIコア.py` を見る

## 確認方法

- ブラウザ DevTools の Network で WebSocket frames を確認する
- 接続直後に `connect` 送信と `init` 受信が見えることを確認する
- 音声調査では `audio` チャンネルに `input_audio` / `output_audio` / `cancel_audio` が流れることを確認する

## 接続時のプロジェクト指定

`connect` の `CODE_BASE_PATH` は任意指定です。新規セッションでは `init` 通知・バックアップ・LiveAI／CodeAI 初期化より先にセッションのフォルダへ反映し、共通設定ファイルは変更しません。既存セッションでは同じフォルダを指定してください。相対パスは `backend_server/` 基準で解決します。参照できないフォルダや既存セッションと異なるフォルダは `error` と切断コード `1008` で拒否します。

`aidiy_live` と `frontend_discord`（Live）は input／0／audio の接続時に作業フォルダを送信します。Web／Avatar は core 初期化情報の `モデル設定.CODE_BASE_PATH` を音声接続時に送信します。指定しない旧クライアントは従来のセッション設定を使用します。

Discordのaudio接続は `connect.Live準備確認: true` を指定し、ソケット登録の `init` に加えて `{ メッセージ識別: "live_ready", セッションID: "<確定ID>" }` を待つ。backendの `Live.待受準備確認()` がProviderの準備完了を確認してから同じaudioソケットへ返す。開始拒否・未設定キー・準備タイムアウトは `error` を返す。`Live準備確認` を指定しない接続は従来のinit方式を維持する。共有クライアントでは `waitForLiveReady: true` を指定した場合のみこの確認を使う。

確認: `backend_server/tests/test_live_project_connection.py` で、初期化通知前の反映、音声への引継ぎ、フォルダ不一致・存在しないフォルダの拒否、旧クライアント互換を検証できます。

## 接続時の Live モデル指定

`connect.モデル設定` は任意のオブジェクトで、`LIVE_AI_NAME` と Gemini／FreeAI／OpenAI のモデル・音声キーのみを受け付けます。指定した値は `init` 通知・AI 初期化より先に新規セッションへ反映し、未指定・空文字の値は既定設定を使用します。共通設定ファイルには保存しません。既存セッションと異なるモデルを指定した場合は `error` と切断コード `1008` で拒否します。モデル変更は新規セッションで再接続してください。

Live のモデル選択では、接続前に `/core/AIコア/モデル情報/取得` へ空の `セッションID` を指定し、既定設定と候補を取得できます。セッションは作成せず、実際の接続時にフォルダと選択したモデルを渡します。接続中の変更時もこの同じ接続方式を使います。

`backend_server/tests/test_live_project_connection.py` で初期モデル・音声の反映、未指定時の既定値、既存セッションのモデル不一致、接続前の候補取得を検証できます。
