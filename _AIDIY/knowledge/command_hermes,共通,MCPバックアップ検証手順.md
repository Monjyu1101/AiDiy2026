# MCP バックアップツールを使ったファイル検証手順

> 文書: `command_hermes,共通,MCPバックアップ検証手順.md` | 実装: `backend_tools/tools_proc/backup.py`, `backend_server/AIコア/AIバックアップ.py`, `frontend_ide/launch.mjs`, `backend_server/core_router/AIコア.py`

## このメモを使う場面

- バックアップを元に、変更後のファイルが正しいか検証する
- バックアップ日時を指定して before/after の差分を確認する
- 差分の有無だけを素早く確認したい

## 関連 MCP ツール

| MCP ツール | 用途 |
|-----------|------|
| `aidiy_backup_backup_get_before_after` | 指定ファイルのバックアップ版(before)と現行版(after)を同時取得 |
| `aidiy_backup_backup_diff_stats` | before/after の追加・削除行数を軽量サマリで返す |
| `aidiy_backup_backup_list_versions` | 指定ファイルがバックアップに出現する全日時一覧 |
| `aidiy_backup_backup_find_changed` | 指定期間の変更ファイル一覧 |

## 検証手順

### 保存先とプロジェクトルートの確認

- 保存先は対象プロジェクト直下の `backup/YYYYMMDD/HHMMSS[.all]/`。`_AIDIY/` はナレッジ・会話履歴などの保存先であり、プロジェクト直下から起動したIDEのバックアップ先ではない。
- `aidiy_ide` の対象は起動時の作業フォルダ、または位置引数 / `--project` で指定したフォルダ。IDEを開くだけではバックアップしない。Codeのオンライン接続で新規inputセッションを作ると、WebSocket初回メッセージの `CODE_BASE_PATH` を確定してから保存する。配置側の共通設定よりセッションの指定を優先する。
- MCP / HTTPの保存処理は `project_root` を対象とし、省略時はAiDiy配置先のルートを使う。ネイティブ実装は常にAiDiy配置先から読み込み、保存と差分確認の両方へ対象の絶対パスを明示する。対象側の `backend_server/` は不要。
- 別環境だけ保存先が違う場合は、IDE画面のプロジェクトパス、実際に呼ばれたPATHランチャー（Windows: `where aidiy_ide`、Linux / macOS: `command -v aidiy_ide`）、バックエンドログの `バックアップ開始(対象パス)` を照合する。ランチャー・Code配布物・稼働中バックエンドが同じ更新済み配置先を使っているか確認し、配布物更新後はIDEとバックエンドを再起動する。
- `python -m unittest discover -s backend_server/tests -p 'test_backup*.py'` は外部プロジェクトの保存・差分確認・参照の一致とファイル数上限を検証する。IDE起動経路の確認には一時プロジェクトを用意し、起動だけの状態とCodeオンライン接続後の状態を分けて保存先を調べる。

### 1. バックアップと現行ファイルの内容比較

```python
# aidiy_backup_backup_get_before_after を呼び出す
# path: プロジェクトルート相対パス
# base_ts: 省略時は直前のバックアップが自動選択される
```

戻り値の構造:

```json
{
  "before": { "content": "…", "timestamp": "YYYYMMDD_HHMMSS", "backup_folder": "YYYYMMDD/HHMMSS" },
  "after":  { "content": "…", "mtime": "YYYY-MM-DD HH:MM:SS", "source": "live" }
}
```

### 2. 差分行数の確認

```python
# aidiy_backup_backup_diff_stats を呼び出す
# path: プロジェクトルート相対パス
# base_ts: 省略可
```

戻り値:

```json
{
  "added_lines": 0,
  "removed_lines": 0,
  "before_lines_total": 485,
  "after_lines_total": 485
}
```

### 3. 判断基準

- `added_lines == 0` かつ `removed_lines == 0` → バックアップと現行ファイルは同一（変更なし）
- `added_lines > 0` または `removed_lines > 0` → 内容の精査が必要
- バックアップフォルダ名が `YYYYMMDD/HHMMSS` 形式であることを確認する

## 注意点

- 保存処理は、除外後の全対象ファイル数が100,000件以上になると走査中にキャンセルする（差分コピー件数ではない）。`backend_server/AIコア/AIバックアップ.py` の `_バックアップキャンセル件数` が判定値で、対象パスと検出件数を ERROR ログへ出力する。コピーや保存先フォルダ作成は行わず、MCP / HTTP の保存結果は `ok: false` と `error` を返す。
- `backup_get_before_after` は内容全体を返す。ファイルが大きい場合は `backup_diff_stats` で軽量確認してから必要に応じて内容を取得する
- `backup_diff_stats` は行ベースの差分カウントであり、同一内容でも改行コードの違い（CRLF vs LF）は行数に影響しない
- バックアップがないファイルの場合は `before` が `null` になる
- この検証は MCP バックアップが正常稼働していることが前提。MCP が落ちている場合は `git diff` など代替手段を使う
