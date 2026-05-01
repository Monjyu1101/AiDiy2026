# .aidiy/knowledge インデックス

このフォルダは AiDiy2026 専用の再利用ナレッジ置き場です。
残す内容は、次回の修正で使える HowTo、判断基準、注意点、確認方法だけにします。

## 使い方

1. 目的に近いカテゴリから該当ファイルを開く。
2. 使う前に、関連ファイルとして書かれているソースを確認して現行実装との差を埋める。
3. 迷う場合は、下の「迷ったときの入口」から最初に見るファイルを決める。
4. 知見を追記するときは、作業履歴ではなく次回使える手順へ圧縮して既存ファイルへ統合する。

## 最優先ルール

| 目的 | 参照ファイル |
|------|--------------|
| `AGENTS.md` / `_AIDIY.md` / `CLAUDE.md` を整理する | [`AGENTS整理手順.md`](./AGENTS整理手順.md) |

## 迷ったときの入口

| 症状・依頼 | 最初に見るファイル |
|-----------|------------------|
| AGENTS / CLAUDE / _AIDIY の役割分担整理 | [`AGENTS整理手順.md`](./AGENTS整理手順.md) |
| DB スキーマ差分、起動時のカラム不足 | [`スキーマ変更手順.md`](./スキーマ変更手順.md) |
| M / T / V / S 系の追加、登録漏れ | [`M系マスタ追加手順.md`](./M系マスタ追加手順.md)、[`T系トランザクション追加手順.md`](./T系トランザクション追加手順.md)、[`V系エンドポイント追加手順.md`](./V系エンドポイント追加手順.md)、[`S系スケジューラ追加手順.md`](./S系スケジューラ追加手順.md) |
| 採番、監査フィールド、初期データ | [`C採番と監査フィールド.md`](./C採番と監査フィールド.md) |
| backend の層構造、実装パターン、落とし穴 | [`backend実装パターン.md`](./backend実装パターン.md) |
| ログイン、401、トークン延長、パスワード | [`JWT認証フロー.md`](./JWT認証フロー.md)、[`認証延長ルール.md`](./認証延長ルール.md)、[`C利用者パスワード運用.md`](./C利用者パスワード運用.md) |
| backend / MCP 起動、ポート残留 | [`バックエンド起動.md`](./バックエンド起動.md)、[`backendMCP構成.md`](./backendMCP構成.md) |
| AI モデル、WebSocket、code1〜code6 | [`AIモデル設定変更手順.md`](./AIモデル設定変更手順.md)、[`AIコアWebSocket仕様.md`](./AIコアWebSocket仕様.md)、[`AIコードパネル拡張手順.md`](./AIコードパネル拡張手順.md) |
| Code CLI 追加、CLI 出力、MCP 設定 | [`CodeCLI追加手順.md`](./CodeCLI追加手順.md)、[`CodeCLI表示ANSI制御コード対処.md`](./CodeCLI表示ANSI制御コード対処.md)、[`CodeCLI_MCP設定.md`](./CodeCLI_MCP設定.md) |
| frontend_web 画面、X系、proxy | [`frontendWeb画面追加手順.md`](./frontendWeb画面追加手順.md)、[`X系静的画面追加.md`](./X系静的画面追加.md)、[`Viteプロキシ設定.md`](./Viteプロキシ設定.md) |
| frontend_web の UI ルール、qTubler、明細型編集 | [`frontendWeb実装パターン.md`](./frontendWeb実装パターン.md) |
| frontend_avatar、Electron、VRM / VRMA、音声 | [`frontendAvatar変更チェック.md`](./frontendAvatar変更チェック.md)、[`ElectronIPC追加手順.md`](./ElectronIPC追加手順.md)、[`VRM_VRMA追加手順.md`](./VRM_VRMA追加手順.md)、[`アバター表示とVRMA.md`](./アバター表示とVRMA.md)、[`AI音声処理.md`](./AI音声処理.md) |
| backend_hermes の CLI 起動・確認 | [`backendHermes運用手順.md`](./backendHermes運用手順.md) |
| backend_mcp の起動・SSE・環境変数 | [`backendMCP運用手順.md`](./backendMCP運用手順.md) |
| Markdown、BOM、ナレッジ整理 | [`Markdown現状追従チェック.md`](./Markdown現状追従チェック.md)、[`UTF8BOM問題対処.md`](./UTF8BOM問題対処.md)、[`ナレッジ更新手順.md`](./ナレッジ更新手順.md) |
| 開発環境操作、DB、Swagger、よくある問題 | [`開発環境運用手順.md`](./開発環境運用手順.md) |
| GitHub issue の確認・close | [`GitHubIssue運用手順.md`](./GitHubIssue運用手順.md) |

既存の運用で `_最終変更.md` を参照する場合は、履歴ではなく [`再修正時の確認入口`](./_最終変更.md) として扱います。

## Backend データ・スキーマ

| 目的 | 参照ファイル |
|------|--------------|
| SQLite スキーマ差分を既存 DB へ反映する | [`スキーマ変更手順.md`](./スキーマ変更手順.md) |
| C採番と監査フィールドを使う | [`C採番と監査フィールド.md`](./C採番と監査フィールド.md) |
| backend の Model / Schema / CRUD / Router パターンを確認する | [`backend実装パターン.md`](./backend実装パターン.md) |

## Backend 認証

| 目的 | 参照ファイル |
|------|--------------|
| JWT ログインから 401 ハンドリングまで確認する | [`JWT認証フロー.md`](./JWT認証フロー.md) |
| どの操作でトークンを延長するか確認する | [`認証延長ルール.md`](./認証延長ルール.md) |
| C利用者のパスワード保存・照合方針を確認する | [`C利用者パスワード運用.md`](./C利用者パスワード運用.md) |

## Backend API 追加

| 目的 | 参照ファイル |
|------|--------------|
| M系マスタを追加する | [`M系マスタ追加手順.md`](./M系マスタ追加手順.md) |
| T系トランザクションを追加する | [`T系トランザクション追加手順.md`](./T系トランザクション追加手順.md) |
| V系 JOIN / 集計エンドポイントを追加する | [`V系エンドポイント追加手順.md`](./V系エンドポイント追加手順.md) |
| S系スケジューラを追加する | [`S系スケジューラ追加手順.md`](./S系スケジューラ追加手順.md) |

## Backend 起動・運用

| 目的 | 参照ファイル |
|------|--------------|
| backend_server / backend_mcp を起動・再起動する | [`バックエンド起動.md`](./バックエンド起動.md) |
| 開発環境の起動、依存関係、DB、API確認、問題切り分けを行う | [`開発環境運用手順.md`](./開発環境運用手順.md) |
| Docker / Nginx 構成で起動する | [`Docker構成.md`](./Docker構成.md) |
| MCP サーバー構成を確認する | [`backendMCP構成.md`](./backendMCP構成.md) |
| backend_mcp の起動、stdio bridge、環境変数を確認する | [`backendMCP運用手順.md`](./backendMCP運用手順.md) |
| MCP ツールをコードエージェントから使う | [`MCP活用手順.md`](./MCP活用手順.md) |

## Frontend 共通

| 目的 | 参照ファイル |
|------|--------------|
| Vite proxy / CORS / ポートを調整する | [`Viteプロキシ設定.md`](./Viteプロキシ設定.md) |

## Frontend Web

| 目的 | 参照ファイル |
|------|--------------|
| Vue 3 の業務画面を追加する | [`frontendWeb画面追加手順.md`](./frontendWeb画面追加手順.md) |
| qTubler、UI ルール、明細型編集を既存パターンへ合わせる | [`frontendWeb実装パターン.md`](./frontendWeb実装パターン.md) |
| X系の静的画面・ゲーム・デモを追加する | [`X系静的画面追加.md`](./X系静的画面追加.md) |

## Frontend Avatar / Electron

| 目的 | 参照ファイル |
|------|--------------|
| Electron IPC を追加する | [`ElectronIPC追加手順.md`](./ElectronIPC追加手順.md) |
| Electron / Web 両モードの変更チェックを行う | [`frontendAvatar変更チェック.md`](./frontendAvatar変更チェック.md) |
| VRM モデル・VRMA モーションを追加する | [`VRM_VRMA追加手順.md`](./VRM_VRMA追加手順.md) |
| アバター表示・VRMA 連続再生・表示選択 UI を調整する | [`アバター表示とVRMA.md`](./アバター表示とVRMA.md) |
| xneko / xeyes 系ウィジェットを追加する | [`xneko_xeyesウィジェット追加手順.md`](./xneko_xeyesウィジェット追加手順.md) |
| マイク入力・音声再生を調整する | [`AI音声処理.md`](./AI音声処理.md) |

## AI コア

| 目的 | 参照ファイル |
|------|--------------|
| AIコア WebSocket の接続・パケット形式を確認する | [`AIコアWebSocket仕様.md`](./AIコアWebSocket仕様.md) |
| AI モデル設定を変更する | [`AIモデル設定変更手順.md`](./AIモデル設定変更手順.md) |
| code1〜code6 のコード AI パネルを調整する | [`AIコードパネル拡張手順.md`](./AIコードパネル拡張手順.md) |

## Code CLI

| 目的 | 参照ファイル |
|------|--------------|
| Code CLI を追加する | [`CodeCLI追加手順.md`](./CodeCLI追加手順.md) |
| Code CLI の MCP 設定を確認する | [`CodeCLI_MCP設定.md`](./CodeCLI_MCP設定.md) |
| Code CLI のプロンプト整形責務を確認する | [`CodeCLIプロンプト整形.md`](./CodeCLIプロンプト整形.md) |
| CLI 出力の ANSI 制御コードを除去する | [`CodeCLI表示ANSI制御コード対処.md`](./CodeCLI表示ANSI制御コード対処.md) |
| Hermes CLI の TUI を調整する | [`HermesCLI_TUI調整手順.md`](./HermesCLI_TUI調整手順.md) |
| backend_hermes を単体 CLI として起動・確認する | [`backendHermes運用手順.md`](./backendHermes運用手順.md) |

## ドキュメント・共通

| 目的 | 参照ファイル |
|------|--------------|
| Markdown を現行実装へ追従させる | [`Markdown現状追従チェック.md`](./Markdown現状追従チェック.md) |
| `AGENTS.md` 系ドキュメントを概要と HowTo に分離する | [`AGENTS整理手順.md`](./AGENTS整理手順.md) |
| `.aidiy/knowledge` を更新する | [`ナレッジ更新手順.md`](./ナレッジ更新手順.md) |
| UTF-8 BOM を検出・除去する | [`UTF8BOM問題対処.md`](./UTF8BOM問題対処.md) |
| 一時ファイル・バックアップを整理する | [`クリーンアップ手順.md`](./クリーンアップ手順.md) |
| GitHub issue を確認・close する | [`GitHubIssue運用手順.md`](./GitHubIssue運用手順.md) |

## 記録ルール

- ファイル名は内容が分かる日本語名にする。
- 同じテーマの知見は既存ファイルへ統合する。
- 残すのは HowTo、判断基準、注意点、確認方法だけにする。
- 日付つき履歴、担当者メモ、経緯説明、完了報告、編集対象の列挙だけの記録は残さない。
- 現行実装と同期が必要な値は、同期元のファイルパスを併記する。
- `.aidiy/knowledge` 更新とアプリ本体の仕様変更は混同しない。
