# MCP バックアップツールを使ったファイル検証手順

> 文書: `command_hermes,共通,MCPバックアップ検証手順.md` | 実装: `backend_tools/` (aidiy_backup)

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

- `backup_get_before_after` は内容全体を返す。ファイルが大きい場合は `backup_diff_stats` で軽量確認してから必要に応じて内容を取得する
- `backup_diff_stats` は行ベースの差分カウントであり、同一内容でも改行コードの違い（CRLF vs LF）は行数に影響しない
- バックアップがないファイルの場合は `before` が `null` になる
- この検証は MCP バックアップが正常稼働していることが前提。MCP が落ちている場合は `git diff` など代替手段を使う
