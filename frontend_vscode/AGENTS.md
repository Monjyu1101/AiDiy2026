# frontend_vscode 実装概要

## 本書の目的

このファイルは `frontend_vscode` の構成、設計方針、主要な実装入口を示す概要ドキュメントです。
導入、変更、検証、VSIX 配布、トラブル対応などの HowTo は `README.md` と `_AIDIY/knowledge` に置きます。
AI エージェントは、本書に個別手順や一時的な作業メモを追記しないでください。

## HowTo 参照先

| 目的 | 参照先 |
|------|--------|
| 利用方法、設定、対応範囲 | [`README.md`](./README.md) |
| 実装変更、検証、VSIX 配布 | [`../_AIDIY/knowledge/frontend_vscode,VSCodeチャット拡張変更手順.md`](../_AIDIY/knowledge/frontend_vscode,VSCodeチャット拡張変更手順.md) |
| プロジェクト全体のセットアップ | [`../_AIDIY/knowledge/共通,開発環境運用手順.md`](../_AIDIY/knowledge/共通,開発環境運用手順.md) |
| 拡張機能と生成物のクリーンアップ | [`../_AIDIY/knowledge/共通,クリーンアップ手順.md`](../_AIDIY/knowledge/共通,クリーンアップ手順.md) |
| Hermes の Provider / モデル選択 | [`../_AIDIY/knowledge/command_hermes,Provider一覧と選択ロジック.md`](../_AIDIY/knowledge/command_hermes,Provider一覧と選択ロジック.md) |
| Hermes の Windows 対応 | [`../_AIDIY/knowledge/command_hermes,Windows対応規則.md`](../_AIDIY/knowledge/command_hermes,Windows対応規則.md) |

## 概要

`frontend_vscode` は `aidiy_hermes` CLI を VS Code のセカンダリサイドバーから操作するチャット拡張です。
拡張プロセスが CLI を直接起動するため、AiDiy の常駐バックエンドや AI コア WebSocket は使用しません。

通常の VS Code 拡張モードに加え、同じ Webview と CLI 実行層を使うチャット単独試用モードを持ちます。

## 技術スタック

- TypeScript。
- VS Code Extension API / Webview API。
- Node.js `child_process` / `http`。
- esbuild。
- `@vscode/vsce`。
- markdown-it。

## 基本方針

- `extensionKind` は `workspace` とし、ローカルファイルと CLI を扱える拡張ホストで動作する。
- 拡張バージョンは、固定解除の明示的な指示があるまで `0.1.0` を維持する。
- ワークスペースを信頼済みの場合だけ CLI 実行とコード添付を許可する。
- `aidiy_hermes` は `shell: false` で起動し、要求本文は UTF-8 の標準入力で渡す。
- 拡張側から `--yolo` を付与せず、Hermes 側の承認・ツール設定を維持する。
- Webview と拡張間では、既存の `AIコード.vue` / `AIコード.py` / `AIコード_cli.py` と同じメッセージ識別子を使う。
- HTML を含む Markdown は無効化し、外部画像や任意の command URI を回答から実行しない。
- Windows デスクトップ版 VS Code を主対象とする。Web 版、仮想ワークスペース、Remote SSH / WSL は対象外。

## ファイル構成

| パス | 役割 |
|------|------|
| `package.json` | 拡張 ID、ビュー、コマンド、設定、ビルド / 配布スクリプト |
| `src/extension.ts` | 拡張のエントリ、WebviewView、会話状態、VS Code コマンド、モデル選択 |
| `src/runner.ts` | CLI 解決、引数構築、子プロセス実行、停止、タイムアウト |
| `src/protocol.ts` | AIコード互換 packet と開始・進捗・終了・回答の変換 |
| `src/webview.ts` | チャット描画、入力、モデル表示、Webview IPC |
| `src/standalone.ts` | 単独試用用の localhost HTTP / SSE サーバー |
| `media/chat.html` / `media/chat.css` | Webview の HTML と見た目 |
| `standalone/bridge.js` | 単独試用画面と HTTP / SSE の橋渡し |
| `scripts/model-catalog.py` | Hermes 既存 picker から Provider / モデル候補を取得 |
| `scripts/build.mjs` | 拡張、単独試用、Webview の bundle と第三者ライセンス生成 |
| `test/` | CLI 実行、protocol、停止、単独試用のテスト |
| `_setup.py` / `_cleanup.py` | VSIX の生成・配置と、拡張・生成物の解除 |

## 実行フロー

1. `extension.ts` が対象ワークスペース、会話、Provider / モデル、添付コードを確定する。
2. `runner.ts` が `aidiy_hermes`、AiDiy 形式の `.cmd`、または `cli_main.py` を安全に解決する。
3. `protocol.ts` が要求を CLI 実行へ渡し、進捗と正式回答を AIコード互換 packet へ変換する。
4. `webview.ts` が進捗と回答を表示し、VS Code の `workspaceState` へ保存する会話は `extension.ts` が管理する。

単独試用では `standalone.ts` と `standalone/bridge.js` が VS Code API の代わりを担当し、`runner.ts`、`protocol.ts`、`webview.ts` は共用します。

## CLI 解決と会話

- 既定の CLI 名は `aidiy_hermes`。
- PATH と `~/.local/bin` を探索し、作業フォルダ内の `command_hermes/cli_main.py` も候補にする。
- AiDiy が生成した `.cmd` は `PY` / `CLI` の絶対パスを読み取り、バッチ自体をシェル実行しない。
- Python ファイルを直接指定する場合は、隣接する `.venv` または設定された Python を使う。
- Provider / モデル候補は `scripts/model-catalog.py` から Hermes の既存 picker を再利用する。
- Hermes のセッション ID を保持し、次回要求では `--resume` で会話を継続する。
- 表示履歴は最新 60 件、合計 200 万文字を上限としてワークスペース単位で保存する。

## セキュリティ境界

- Webview は nonce 付き CSP とローカル resource root を使う。
- 回答内リンクは `http` / `https` だけを外部ブラウザで開く。
- 選択コードは 80,000 文字、要求本文は 200,000 文字、回答表示は 2,000,000 文字を上限とする。
- 単独試用サーバーは `127.0.0.1` のランダムポートとランダム path で待ち受け、Host / Origin / Content-Type を検証する。
- 停止時は Windows では `taskkill /T /F`、その他では process group へ signal を送り、子孫プロセスも終了対象にする。

## 実装時の入口

- VS Code のビュー、コマンド、設定を変える場合は `package.json` と `src/extension.ts` をセットで見る。
- CLI の探索、引数、標準入出力、停止を変える場合は `src/runner.ts` と `test/runner.test.cjs` をセットで見る。
- packet を変える場合は `src/protocol.ts` と既存 AIコード実装との互換性を確認する。
- チャット UI を変える場合は `media/chat.html`、`media/chat.css`、`src/webview.ts` をセットで見て、単独試用側も確認する。
- Provider / モデル候補を変える場合は `scripts/model-catalog.py` と `command_hermes` の picker 実装を先に確認する。
- 具体的な変更手順と検証項目は `_AIDIY/knowledge/frontend_vscode,VSCodeチャット拡張変更手順.md` を参照する。
