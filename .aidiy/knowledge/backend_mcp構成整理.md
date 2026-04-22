# backend_mcp構成整理

## このメモを使う場面
- `backend_mcp` のファイル配置を整理するとき
- 入口ファイルとロジックファイルを分けたいとき

## 結論
- 入口は `backend_mcp/mcp_main.py` に置く
- Codex 向けの transport 変換入口は `backend_mcp/mcp_stdio.py` に分ける
- 再利用ロジックは `backend_mcp/mcp_proc/` にまとめる
- `mcp_main.py` や `tools/__init__.py` からは `mcp_proc.<module>` で import する

## 関連ファイル
- `backend_mcp/mcp_main.py`
- `backend_mcp/mcp_stdio.py`
- `backend_mcp/mcp_proc/chrome_manager.py`
- `backend_mcp/mcp_proc/chrome_devtools.py`
- `_start.py`

## 注意点
- `mcp_main.py` は入口として残し、`mcp_proc` へ入れない
- stdio <-> SSE の transport 変換は `mcp_stdio.py` に閉じ込め、`mcp_main.py` の共有 Chrome 管理と混ぜない
- import パスを旧ファイル名のまま残すと起動時に `ModuleNotFoundError` になる
- `_start.py` の `(mcp)` ブラウザ起動ヘルパーも `from mcp_proc.chrome_manager import ChromeManager` に揃える
- 環境によっては `backend_mcp` の仮想環境に `mcp.server` などの依存が欠けていることがあるので、構成変更後は import 確認だけでなく実起動確認も必要

## 最低限の確認方法
- `backend_mcp/.venv/Scripts/python.exe -` で `mcp_main.py` を import できる
- `backend_mcp/.venv/Scripts/python.exe backend_mcp/mcp_stdio.py --help` が動く
- `rg "chrome_manager|chrome_devtools" backend_mcp` で旧 import が残っていない
