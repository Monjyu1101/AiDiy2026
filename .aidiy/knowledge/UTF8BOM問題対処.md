# UTF-8 BOM 問題対処

## このメモを使う場面
- ファイルの先頭に BOM が混入してサーバーや Python が誤動作する
- エディタや OS が自動的に UTF-8 BOM を付与してしまった
- BOM が混入しているファイルを一括検出・除去したい

## 関連ファイル
- `scripts/bom_anomaly_list.py` — BOM 混入ファイルの検出
- `scripts/remove_bom.py` — BOM の一括除去

## 対処手順

### 検出

```powershell
python scripts/bom_anomaly_list.py
# BOM が混入しているファイルの一覧が表示される
```

対象を限定して確認したい場合は、PowerShell で先頭3バイトを見る。

```powershell
$files = @(".aidiy/knowledge/JWT認証フロー.md", ".aidiy/knowledge/MCP活用手順.md")
foreach ($file in $files) {
  $bytes = [System.IO.File]::ReadAllBytes((Resolve-Path $file))
  if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { $file }
}
```

### 除去

```powershell
python scripts/remove_bom.py          # プロジェクトルートから再帰的に除去
python scripts/remove_bom.py src/     # 指定フォルダ以下のみ除去
```

並列作業中に担当ファイルだけを直す場合は、一括除去の前に差分対象を確認する。担当外ファイルにBOMが見つかっても、許可されていない場合は最終報告で伝えるだけにする。

### BOM が問題になる主なケース

| 現象 | 原因 |
|------|------|
| Python `import` エラー（`SyntaxError: invalid character`） | `.py` ファイルの先頭に BOM |
| FastAPI 起動失敗 | `__init__.py` や `main.py` に BOM |
| Vue コンポーネントが壊れる | `.vue` / `.ts` ファイルに BOM |
| JSON パースエラー | `.json` ファイルに BOM |

### BOM を付与しないエディタ設定

- **VS Code**: `files.encoding: "utf8"` を設定（`utf8bom` は使わない）
- **Windows メモ帳**: 「UTF-8 BOM あり」ではなく「UTF-8」で保存
- **PyCharm**: File Encoding を `UTF-8` に統一

## 再発しやすい注意点

- Windows 環境では OS やツールが自動で BOM を付けることがある
- `git diff` で BOM 差分が見えにくいため、コミット前に `bom_anomaly_list.py` で確認する習慣をつける
- CI/CD に `bom_anomaly_list.py` を組み込むとより確実
- PowerShell でファイル内容を確認するときは `Get-Content -Encoding UTF8` を使う
- docs のコーディングルールでは Python ファイル先頭に `# -*- coding: utf-8 -*-` を置く方針だが、これはBOM付与を意味しない
- JSON 設定ファイルは UTF-8 without BOM に加えて構文エラーも起動失敗原因になるため、編集後はJSONとして読めるか確認する

## 確認方法

```powershell
python scripts/bom_anomaly_list.py
# → 出力が空なら BOM なし
```
