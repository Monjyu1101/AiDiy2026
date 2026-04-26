# MCP 活用手順

## このメモを使う場面
- Claude Agent SDK から MCP ツールを使ってブラウザ操作・DB 参照・スクリーンショット等を行いたい
- `AiDiy_mcp.json` に新しい MCP サーバーを追加したい
- MCP ツールの動作を調査・デバッグしたい

## 関連ファイル
- `backend_server/_config/AiDiy_mcp.json` — MCP サーバー接続定義（Claude Agent SDK に渡す）
- `backend_server/core_router/AIコア/AIコード_claude.py` — Claude Agent SDK で MCP を使う実装
- `backend_mcp/mcp_main.py` — 8 つの MCP サーバー（SSE）のエントリーポイント
- `backend_mcp/mcp_proc/` — 各 MCP サーバーのロジック実装

## MCP サーバー一覧（port 8095）

| サーバー名 | SSE URL | 主なツール |
|-----------|---------|-----------|
| `aidiy_chrome_devtools` | `/aidiy_chrome_devtools/sse` | ブラウザ操作、DOM 取得、ナビゲーション |
| `aidiy_desktop_capture` | `/aidiy_desktop_capture/sse` | スクリーンショット、クリック、キー入力 |
| `aidiy_sqlite` | `/aidiy_sqlite/sse` | SQLite DB 参照・検証 |
| `aidiy_postgres` | `/aidiy_postgres/sse` | PostgreSQL 参照・検証 |
| `aidiy_logs` | `/aidiy_logs/sse` | ログファイル参照 |
| `aidiy_code_check` | `/aidiy_code_check/sse` | コードファイル参照・型チェック実行 |
| `aidiy_backup_check` | `/aidiy_backup_check/sse` | バックアップ確認（`backup_find_changed(from_ts, to_ts?)` など） |
| `aidiy_backup_save` | `/aidiy_backup_save/sse` | バックアップ保存 |

## AiDiy_mcp.json の設定形式

```json
{
  "mcpServers": {
    "aidiy_chrome_devtools": {
      "type": "sse",
      "url": "http://localhost:8095/aidiy_chrome_devtools/sse"
    },
    "aidiy_sqlite": {
      "type": "sse",
      "url": "http://localhost:8095/aidiy_sqlite/sse"
    }
  }
}
```

`type: "sse"` を明示する。設定ファイルは `backend_server/_config/` 配下で、実際のキーや環境依存値を docs/code_samples へコピーしない。

## Claude Agent SDK での使い方

```python
from anthropic import Anthropic
from conf import conf

client = Anthropic(api_key=conf.json.claude_key_id)
# mcp_servers は conf.models.mcp_servers から取得（AiDiy_mcp.json の内容）
# permission_mode="bypassPermissions" でツール自動許可
```

## Chrome 自動起動

`aidiy_chrome_devtools` を使う場合、Chrome がデバッグポート 9222 で起動していなければ  
`backend_mcp` が自動起動する。環境変数 `CHROME_EXECUTABLE` で Chrome のパスを指定できる。

## ツール選択の基準

| やりたいこと | 優先する MCP |
|-------------|-------------|
| 画面上のDOM、URL遷移、クリック、スクリーンショット確認 | `aidiy_chrome_devtools` |
| Electron やブラウザ外を含むデスクトップ全体の確認 | `aidiy_desktop_capture` |
| AiDiy SQLite のテーブル・件数・監査フィールド確認 | `aidiy_sqlite` |
| 外部 PostgreSQL のスキーマ・件数確認 | `aidiy_postgres` |
| サーバーログ、Traceback、ERROR の確認 | `aidiy_logs` |
| Python 構文、ruff、TypeScript 型チェック | `aidiy_code_check` |
| 差分バックアップから変更前後を確認 | `aidiy_backup_check` |
| AiDiy ネイティブの差分バックアップ実行 | `aidiy_backup_save` |

SQLite/PostgreSQL は既定が read-only。書き込みが必要なケースでも、通常の実装検証では `allow_write=True` を使う前に、アプリのAPIや既存の初期化処理で再現できないかを確認する。

## 実装の結論

- Claude Agent SDK から使う MCP 接続定義は `backend_server/_config/AiDiy_mcp.json` に集約する
- `backend_mcp` は port 8095 の SSE サーバーとして起動し、用途ごとに `/aidiy_xxx/sse` のエンドポイントへ分かれる
- ブラウザ操作・DB 参照・ログ確認・コードチェック・バックアップ確認/保存は、まず既存の 8 サーバーへ割り当てられるか確認する
- 新しい MCP サーバーを追加する場合は、`backend_mcp/mcp_main.py` のエントリーポイントと `backend_mcp/mcp_proc/` の実処理を揃え、`AiDiy_mcp.json` に URL を追加する
- Codex など stdio クライアントから使う場合は `backend_mcp/mcp_stdio.py --sse-url http://localhost:8095/<server>/sse` で中継する
- Docker 構成には `backend_mcp` が含まれない。MCP 連携が必要な検証はローカルで `backend_mcp` を別途起動する

## 自己検証・バックアップ系ツール利用時の注意

- `backup_run` が長時間化またはタイムアウトする場合、編集前なら通常のファイル確認で続行する。編集後はバックアップ実行の再試行だけに固執せず、リンク確認、BOM/依存確認、検索チェック、差分確認など別手段で検証する。
- `Transport closed` などで MCP 接続が不安定な場合は、同一ターンで無理に繰り返さない。どの MCP ツールが使えなかったか、代替確認をどこまで実施したか、未確認の影響範囲を明示して作業を閉じる。
- バックアップ保存・確認系 MCP は自己検証の補助として扱う。ツール不調時も、対象ファイル、参照リンク、実行コマンド、検索結果などで変更範囲を説明できる状態にしておく。

## 起動・再起動の判断

- `_start.py` 経由で起動した場合、`backend_mcp/temp/reboot_mcp.txt` を作成すると `_start.py` が再起動する
- 手動でホットリロードしたい場合は `cd backend_mcp && .venv/Scripts/python.exe -m uvicorn mcp_main:app --reload --host 0.0.0.0 --port 8095`
- 8095 が反応しない場合は、まず `curl http://localhost:8095/` で本体起動を確認し、次に各 `/sse` を確認する
- Chrome DevTools だけ不安定な場合は `curl http://localhost:9222/json` でChromeデバッグポートを確認する
- PostgreSQL MCP だけ失敗する場合は、`psycopg` 未導入、DSN未設定、外部DB接続不可を切り分ける。他の MCP まで停止しているとは限らない

## 確認方法

```bash
# MCP 本体の起動確認
curl http://localhost:8095/

# MCP サーバーの起動確認
curl http://localhost:8095/aidiy_sqlite/sse
# → text/event-stream レスポンスが返れば起動中

# Chrome DevTools の接続確認
curl http://localhost:9222/json
```
