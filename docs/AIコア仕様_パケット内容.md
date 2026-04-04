# AIコア仕様_パケット内容

本書は **`WebSocket /core/ws/AIコア` の現行実装** に基づくパケット仕様メモです。

---

## 1. ソケット番号 / チャンネル

- `audio` : 音声入出力
- `input` : 共通入力
- `file` : バックアップ一覧 / temp 一覧 / files_save
- `core` : Avatar コア画面
- `0` : チャット出力
- `1` - `4` : コードエージェント出力

補足:

- 接続時は `ソケット番号` を使います。
- 通常メッセージでは `チャンネル` も併用されます。

---

## 2. 接続シーケンス

1. クライアントが `ws://.../core/ws/AIコア` に接続
2. 最初の送信で `type: "connect"` を送る
3. 必要に応じて以下を同時送信
   - `セッションID`
   - `ソケット番号`
4. サーバーが `メッセージ識別: "init"` を返す

### 初回送信例

```json
{
  "type": "connect",
  "セッションID": "abc123def0",
  "ソケット番号": "input"
}
```

### init 応答例

```json
{
  "セッションID": "abc123def0",
  "ソケット番号": "input",
  "チャンネル": "input",
  "メッセージ識別": "init",
  "メッセージ内容": {}
}
```

補足:

- `core` ソケットの `init` では `メッセージ内容` に `ボタン` と `モデル設定` が入ります。
- `input` / `audio` / `file` / `0` - `4` の `init` は基本的に空です。

---

## 3. 共通パケット形式

主に使うキー:

- `type`
- `セッションID`
- `ソケット番号`
- `チャンネル`
- `出力先チャンネル`
- `メッセージ識別`
- `メッセージ内容`
- `ファイル名`
- `サムネイル画像`

---

## 4. チャンネル別メッセージ

### 4.1 `audio`

クライアント -> サーバー:

- `input_audio`
  - `メッセージ内容`: MIME (`audio/pcm`)
  - `ファイル名`: Base64 PCM
- `cancel_audio`

サーバー -> クライアント:

- `output_audio`
  - `メッセージ内容`: MIME (`audio/pcm`)
  - `ファイル名`: Base64 PCM

### 4.2 `input`

クライアント -> サーバー:

- `operations`
- `input_text`
- `input_request`
- `input_file`
- `input_image`
- `cancel_run`

補足:

- `input_text` は `出力先チャンネル` を使って `0` または `1` - `4` に振り分けます。
- `cancel_run` は `チャンネル` に停止対象のコードチャンネル (`"1"` - `"4"`) を指定します。

サーバー -> クライアント:

- `init`
- `streaming_started`
- `heartbeat`
- `error`

### 4.3 `file`

`file` ソケットは**独立ソケット**です。要求も応答も `file` ソケットで行います。

クライアント -> サーバー:

- `files_backup`
- `files_temp`
- `files_save`

サーバー -> クライアント:

- `files_backup`
- `files_temp`

#### `files_backup` 応答

```json
{
  "セッションID": "abc123def0",
  "チャンネル": "file",
  "メッセージ識別": "files_backup",
  "メッセージ内容": {
    "要求日時": 0,
    "プロジェクトパス": "D:/OneDrive/_sandbox/AiDiy2026",
    "バックアップベースパス": "D:/OneDrive/_sandbox/AiDiy2026/backend_server/temp/backup",
    "最終ファイル日時": "2026/04/04 21:00:00",
    "ファイルリスト": [
      { "パス": "frontend_web/src/main.ts", "更新日時": "2026/04/04 20:55:00" }
    ]
  }
}
```

#### `files_temp` 応答

```json
{
  "セッションID": "abc123def0",
  "チャンネル": "file",
  "メッセージ識別": "files_temp",
  "メッセージ内容": {
    "要求日時": 60,
    "作業ファイル日時": "2026/04/04 21:05:00",
    "ファイルリスト": [
      { "パス": "temp/input/sample.png", "更新日時": "2026/04/04 21:05:00" }
    ]
  }
}
```

### 4.4 `core`

サーバー -> クライアント:

- `init`
- `welcome_info`
- `welcome_text`
- `recognition_output`
- `output_text`

補足:

- `core` は Avatar のアバター常駐画面向けです。
- チャンネル `0` の一部メッセージは `core` にも並行転送されます。

### 4.5 `0`

サーバー -> クライアント:

- `welcome_info`
- `welcome_text`
- `input_text`
- `input_file`
- `output_text`
- `output_file`
- `recognition_input`
- `recognition_output`

### 4.6 `1` - `4`

サーバー -> クライアント:

- `welcome_info`
- `welcome_text`
- `input_text`
- `input_request`
- `input_file`
- `output_text`
- `output_file`
- `output_stream`
- `cancel_run`

`cancel_run` 応答例:

```json
{
  "セッションID": "abc123def0",
  "チャンネル": "1",
  "メッセージ識別": "cancel_run",
  "メッセージ内容": "処理中断！"
}
```

---

## 5. 代表サンプル

### 5.1 テキスト入力

```json
{
  "セッションID": "abc123def0",
  "チャンネル": "input",
  "出力先チャンネル": "0",
  "メッセージ識別": "input_text",
  "メッセージ内容": "こんにちは",
  "ファイル名": "chat"
}
```

### 5.2 画像入力

```json
{
  "セッションID": "abc123def0",
  "チャンネル": "input",
  "出力先チャンネル": "0",
  "メッセージ識別": "input_image",
  "メッセージ内容": "image/jpeg",
  "ファイル名": "<base64_image>"
}
```

### 5.3 音声入力

```json
{
  "セッションID": "abc123def0",
  "チャンネル": "audio",
  "メッセージ識別": "input_audio",
  "メッセージ内容": "audio/pcm",
  "ファイル名": "<base64_pcm>"
}
```

### 5.4 コード停止要求

```json
{
  "セッションID": "abc123def0",
  "チャンネル": "1",
  "メッセージ識別": "cancel_run",
  "メッセージ内容": ""
}
```

### 5.5 バックアップ一覧要求

```json
{
  "セッションID": "abc123def0",
  "チャンネル": "file",
  "メッセージ識別": "files_backup",
  "メッセージ内容": 0
}
```

---

## 6. 実装参照

- バックエンド: `backend_server/core_router/AIコア.py`
- セッション管理: `backend_server/AIコア/AIセッション管理.py`
- Web フロント実装: `frontend_web/src/components/AiDiy/compornents/`
- Avatar 実装: `frontend_avatar/src/`
