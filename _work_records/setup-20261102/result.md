# 実環境 setup / Diag 起動結果

2026-11-02、`python -X utf8 -B _setup.py` を通常AUTO選択で実行し、終了コード0、正常終了を確認。

- 共通、Diag、Local、Tools、Core/Apps、Task/Team、Web、Avatar、Hermes、IDE群、Discord、Slackをsetup。
- Localモデル事前ダウンロード、グローバルAI CLI本体の導入更新は既定のno。
- Toolsの既存AiDiy MCP設定再登録、Code/Live VS Code拡張配置は完了。
- IDE共通UI／TaskTeam、Discord、Slackのビルド・配布物確認は成功。Electron v44.10.1を配置・再利用。ビルド失敗・Electronコピー失敗なし。
- 注意は続行モードの一般警告、MCP再登録前の未設定警告、VS Code CLIのDEP0169非推奨API警告。MCPはその後書込完了、拡張もインストール成功。通常setupがローカル履歴用 `.git_local` を生成した。追加pull・pushなし。

setup終了後に `node backend_diag/diag_main.mjs` を引数なしで実行し、起動コマンド終了コード0。Diagの実画面（システム起動タブ、未起動状態）を確認。システム起動ボタンは操作していない。

Diag本体node PID24624、Electron主窓PID9068（OSタイトル「AiDiy 診断」、HWND3541912）、補助Electron PID28580/20380/13448。直接TCPで8090/8091/8092/8093/8095/8096/8098はすべて接続不可。他サーバーは起動していない。

開始前から存在した `_config` 16ファイルは終了後もすべてSHA-256一致、欠落なし。値は表示・記録していない。

**開始前から** `_data/AiDiy/database.db` および以前の `_work_records/cleanup-20261102` はこの作業フォルダに存在しなかった。今回のsetupで消したものではなく、保持済みと扱わない。別フォルダ探索・復元・DB新規作成は行っていない。終了後もDBは不在。システム起動は今回の依頼範囲外。

事前ハッシュは `before.json`、事後照合とポート確認は `after.json`。全セルフテスト再実行なし。
