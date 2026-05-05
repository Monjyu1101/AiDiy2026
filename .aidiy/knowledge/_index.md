# .aidiy/knowledge インデックス

このフォルダは AiDiy2026 専用の再利用ナレッジ置き場です。
残す内容は、次回の修正で使える HowTo、判断基準、注意点、確認方法だけにします。

## ファイル命名規則

ナレッジファイル名は `対象モジュール,トピック名.md` とします。
`,` の左側にどのモジュール（群）に関連するかを並べ、右側にトピックを日本語で記述します。

```
モジュール1,モジュール2,トピック名.md
```

モジュール名には以下を使います:

| モジュール名 | 対象 |
|-------------|------|
| `共通` | プロジェクト全体、横断的な話題 |
| `backend_server` | FastAPI サーバー（core_main / apps_main） |
| `backend_hermes` | `aidiy_hermes` CLI 基盤 |
| `backend_mcp` | MCP サーバー群 |
| `frontend_web` | Vue 3 + Vite + TypeScript Web UI |
| `frontend_avatar` | Electron/Web デュアルモード Avatar |

例:

- `backend_server,スキーマ変更手順.md` — backend_server 単独の話題
- `frontend_avatar,frontend_web,アバター表示とVRMA.md` — 両方のフロントエンドにまたがる話題
- `backend_server,frontend_web,frontend_avatar,JWT認証フロー.md` — 3モジュールにまたがる話題
- `共通,開発環境運用手順.md` — プロジェクト全体の話題

メタファイル（`_index.md`、`_最終変更.md`）は接頭辞をつけず、`_` 始まりのままにします。

## ファイル内容先頭書式

各ナレッジファイルの先頭は以下の形式に統一します。

```markdown
# <タイトル>

> 文書: `モジュール,トピック名.md` | 実装: `backend_server/path/file.py`, `frontend_web/src/path/file.vue`

## このメモを使う場面

- <このメモが役立つ状況を箇条書き>
```

ブロック引用（`> 文書: … | 実装: …`）行の目的:
- `文書:` — このファイル自身のファイル名を記載する。全文検索で `文書名.md` → 該当ファイルがヒットしやすくなる。
- `実装:` — このナレッジが参照する主要なソースファイルパスを `,` 区切りで列挙する。grep で `ファイル名.vue` → 関連ナレッジが特定できる。

例:

```markdown
# AI モデル設定変更手順

> 文書: `backend_server,frontend_avatar,frontend_web,AIモデル設定変更手順.md` | 実装: `backend_server/config.py`, `frontend_web/src/stores/AIモデル設定.ts`

## このメモを使う場面

- AI ベンダーやモデル名を切り替えるとき
- `.env` の `CHAT_AI_NAME` などの設定値を変更するとき
```

- `# <タイトル>` はファイル名末尾のトピック部分と対応させる（`AIモデル設定変更手順` など）。
- `## このメモを使う場面` は必ず箇条書きで簡潔に書く。

## 使い方

1. 目的に近いカテゴリから該当ファイルを開く。
2. 使う前に、関連ファイルとして書かれているソースを確認して現行実装との差を埋める。
3. 迷う場合は、下の「迷ったときの入口」から最初に見るファイルを決める。
4. 知見を追記するときは、作業履歴ではなく次回使える手順へ圧縮して既存ファイルへ統合する。

## 最優先ルール

| 目的 | 参照ファイル |
|------|--------------|
| `AGENTS.md` / `_AIDIY.md` / `CLAUDE.md` を整理する | [`共通,AGENTS整理手順.md`](./共通,AGENTS整理手順.md) |

## 迷ったときの入口

| 症状・依頼 | 最初に見るファイル |
|-----------|------------------|
| AGENTS / CLAUDE / _AIDIY の役割分担整理 | [`共通,AGENTS整理手順.md`](./共通,AGENTS整理手順.md) |
| DB スキーマ差分、起動時のカラム不足 | [`backend_server,スキーマ変更手順.md`](./backend_server,スキーマ変更手順.md) |
| M / T / V / S 系の追加、登録漏れ | [`backend_server,M系マスタ追加手順.md`](./backend_server,M系マスタ追加手順.md)、[`backend_server,T系トランザクション追加手順.md`](./backend_server,T系トランザクション追加手順.md)、[`backend_server,V系エンドポイント追加手順.md`](./backend_server,V系エンドポイント追加手順.md)、[`backend_server,S系スケジューラ追加手順.md`](./backend_server,S系スケジューラ追加手順.md) |
| M系マスタへのカラム追加 | [`backend_server,M系マスタカラム追加手順.md`](./backend_server,M系マスタカラム追加手順.md) |
| 採番、監査フィールド、初期データ | [`backend_server,C採番と監査フィールド.md`](./backend_server,C採番と監査フィールド.md) |
| backend の層構造、実装パターン、落とし穴 | [`backend_server,実装パターン.md`](./backend_server,実装パターン.md) |
| ログイン、401、トークン延長、パスワード | [`backend_server,frontend_web,frontend_avatar,JWT認証フロー.md`](./backend_server,frontend_web,frontend_avatar,JWT認証フロー.md)、[`backend_server,frontend_web,frontend_avatar,認証延長ルール.md`](./backend_server,frontend_web,frontend_avatar,認証延長ルール.md)、[`backend_server,C利用者パスワード運用.md`](./backend_server,C利用者パスワード運用.md) |
| backend / MCP 起動、ポート残留 | [`backend_server,backend_hermes,backend_mcp,バックエンド起動.md`](./backend_server,backend_hermes,backend_mcp,バックエンド起動.md)、[`backend_mcp,構成.md`](./backend_mcp,構成.md) |
| aidiy_hermes で MCP が `failed` / ツール未認識 | [`backend_hermes,backend_mcp,MCP_SSE接続.md`](./backend_hermes,backend_mcp,MCP_SSE接続.md) |
| hermes を MCP サーバーとして Code CLI から使う | [`backend_hermes,MCP_サーバー起動.md`](./backend_hermes,MCP_サーバー起動.md) |
| AI モデル、WebSocket、code1〜code6 | [`backend_server,frontend_avatar,frontend_web,AIモデル設定変更手順.md`](./backend_server,frontend_avatar,frontend_web,AIモデル設定変更手順.md)、[`backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md`](./backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md)、[`backend_server,frontend_avatar,frontend_web,AIコードパネル拡張手順.md`](./backend_server,frontend_avatar,frontend_web,AIコードパネル拡張手順.md) |
| Code CLI 追加、CLI 出力、MCP 設定 | [`backend_server,backend_hermes,frontend_avatar,frontend_web,CodeCLI追加手順.md`](./backend_server,backend_hermes,frontend_avatar,frontend_web,CodeCLI追加手順.md)、[`backend_server,backend_hermes,frontend_avatar,CodeCLI表示ANSI制御コード対処.md`](./backend_server,backend_hermes,frontend_avatar,CodeCLI表示ANSI制御コード対処.md)、[`backend_hermes,backend_mcp,CodeCLI_MCP設定.md`](./backend_hermes,backend_mcp,CodeCLI_MCP設定.md) |
| frontend_web 画面、X系、proxy | [`frontend_web,画面追加手順.md`](./frontend_web,画面追加手順.md)、[`frontend_web,X系静的画面追加.md`](./frontend_web,X系静的画面追加.md)、[`frontend_web,frontend_avatar,backend_server,Viteプロキシ設定.md`](./frontend_web,frontend_avatar,backend_server,Viteプロキシ設定.md) |
| frontend_web の UI ルール、qTubler、明細型編集 | [`frontend_web,実装パターン.md`](./frontend_web,実装パターン.md) |
| frontend_avatar、Electron、VRM / VRMA、音声 | [`frontend_avatar,変更チェック.md`](./frontend_avatar,変更チェック.md)、[`frontend_avatar,ElectronIPC追加手順.md`](./frontend_avatar,ElectronIPC追加手順.md)、[`frontend_avatar,VRM_VRMA追加手順.md`](./frontend_avatar,VRM_VRMA追加手順.md)、[`frontend_avatar,frontend_web,アバター表示とVRMA.md`](./frontend_avatar,frontend_web,アバター表示とVRMA.md)、[`backend_server,frontend_avatar,AI音声処理.md`](./backend_server,frontend_avatar,AI音声処理.md) |
| backend_hermes の CLI 起動・確認 | [`backend_hermes,backend_server,運用手順.md`](./backend_hermes,backend_server,運用手順.md) |
| backend_mcp の起動・SSE・環境変数 | [`backend_mcp,backend_server,運用手順.md`](./backend_mcp,backend_server,運用手順.md) |
| Markdown、BOM、ナレッジ整理 | [`共通,Markdown現状追従チェック.md`](./共通,Markdown現状追従チェック.md)、[`共通,UTF8BOM問題対処.md`](./共通,UTF8BOM問題対処.md)、[`共通,ナレッジ更新手順.md`](./共通,ナレッジ更新手順.md) |
| 開発環境操作、DB、Swagger、よくある問題 | [`共通,開発環境運用手順.md`](./共通,開発環境運用手順.md) |
| GitHub issue の確認・close | [`共通,GitHubIssue運用手順.md`](./共通,GitHubIssue運用手順.md) |

既存の運用で `_最終変更.md` を参照する場合は、履歴ではなく [`再修正時の確認入口`](./_最終変更.md) として扱います。

## Backend データ・スキーマ

| 目的 | 参照ファイル |
|------|--------------|
| SQLite スキーマ差分を既存 DB へ反映する | [`backend_server,スキーマ変更手順.md`](./backend_server,スキーマ変更手順.md) |
| C採番と監査フィールドを使う | [`backend_server,C採番と監査フィールド.md`](./backend_server,C採番と監査フィールド.md) |
| backend の Model / Schema / CRUD / Router パターンを確認する | [`backend_server,実装パターン.md`](./backend_server,実装パターン.md) |

## Backend 認証

| 目的 | 参照ファイル |
|------|--------------|
| JWT ログインから 401 ハンドリングまで確認する | [`backend_server,frontend_web,frontend_avatar,JWT認証フロー.md`](./backend_server,frontend_web,frontend_avatar,JWT認証フロー.md) |
| どの操作でトークンを延長するか確認する | [`backend_server,frontend_web,frontend_avatar,認証延長ルール.md`](./backend_server,frontend_web,frontend_avatar,認証延長ルール.md) |
| C利用者のパスワード保存・照合方針を確認する | [`backend_server,C利用者パスワード運用.md`](./backend_server,C利用者パスワード運用.md) |

## Backend API 追加

| 目的 | 参照ファイル |
|------|--------------|
| M系マスタを追加する | [`backend_server,M系マスタ追加手順.md`](./backend_server,M系マスタ追加手順.md) |
| M系マスタにカラムを追加する | [`backend_server,M系マスタカラム追加手順.md`](./backend_server,M系マスタカラム追加手順.md) |
| T系トランザクションを追加する | [`backend_server,T系トランザクション追加手順.md`](./backend_server,T系トランザクション追加手順.md) |
| V系 JOIN / 集計エンドポイントを追加する | [`backend_server,V系エンドポイント追加手順.md`](./backend_server,V系エンドポイント追加手順.md) |
| S系スケジューラを追加する | [`backend_server,S系スケジューラ追加手順.md`](./backend_server,S系スケジューラ追加手順.md) |

## Backend 起動・運用

| 目的 | 参照ファイル |
|------|--------------|
| backend_server / backend_mcp を起動・再起動する | [`backend_server,backend_hermes,backend_mcp,バックエンド起動.md`](./backend_server,backend_hermes,backend_mcp,バックエンド起動.md) |
| 開発環境の起動、依存関係、DB、API確認、問題切り分けを行う | [`共通,開発環境運用手順.md`](./共通,開発環境運用手順.md) |
| Docker / Nginx 構成で起動する | [`backend_server,frontend_web,Docker構成.md`](./backend_server,frontend_web,Docker構成.md) |
| MCP サーバー構成を確認する | [`backend_mcp,構成.md`](./backend_mcp,構成.md) |
| backend_mcp の起動、stdio bridge、環境変数を確認する | [`backend_mcp,backend_server,運用手順.md`](./backend_mcp,backend_server,運用手順.md) |
| MCP ツールをコードエージェントから使う | [`backend_server,backend_mcp,MCP活用手順.md`](./backend_server,backend_mcp,MCP活用手順.md) |

## Frontend 共通

| 目的 | 参照ファイル |
|------|--------------|
| Vite proxy / CORS / ポートを調整する | [`frontend_web,frontend_avatar,backend_server,Viteプロキシ設定.md`](./frontend_web,frontend_avatar,backend_server,Viteプロキシ設定.md) |

## Frontend Web

| 目的 | 参照ファイル |
|------|--------------|
| Vue 3 の業務画面を追加する | [`frontend_web,画面追加手順.md`](./frontend_web,画面追加手順.md) |
| qTubler、UI ルール、明細型編集を既存パターンへ合わせる | [`frontend_web,実装パターン.md`](./frontend_web,実装パターン.md) |
| X系の静的画面・ゲーム・デモを追加する | [`frontend_web,X系静的画面追加.md`](./frontend_web,X系静的画面追加.md) |

## Frontend Avatar / Electron

| 目的 | 参照ファイル |
|------|--------------|
| Electron IPC を追加する | [`frontend_avatar,ElectronIPC追加手順.md`](./frontend_avatar,ElectronIPC追加手順.md) |
| Electron / Web 両モードの変更チェックを行う | [`frontend_avatar,変更チェック.md`](./frontend_avatar,変更チェック.md) |
| VRM モデル・VRMA モーションを追加する | [`frontend_avatar,VRM_VRMA追加手順.md`](./frontend_avatar,VRM_VRMA追加手順.md) |
| アバター表示・VRMA 連続再生・表示選択 UI を調整する | [`frontend_avatar,frontend_web,アバター表示とVRMA.md`](./frontend_avatar,frontend_web,アバター表示とVRMA.md) |
| xneko / xeyes 系ウィジェットを追加する | [`frontend_avatar,xneko_xeyesウィジェット追加手順.md`](./frontend_avatar,xneko_xeyesウィジェット追加手順.md) |
| マイク入力・音声再生を調整する | [`backend_server,frontend_avatar,AI音声処理.md`](./backend_server,frontend_avatar,AI音声処理.md) |

## AI コア

| 目的 | 参照ファイル |
|------|--------------|
| AIコア WebSocket の接続・パケット形式を確認する | [`backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md`](./backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md) |
| AI モデル設定を変更する | [`backend_server,frontend_avatar,frontend_web,AIモデル設定変更手順.md`](./backend_server,frontend_avatar,frontend_web,AIモデル設定変更手順.md) |
| code1〜code6 のコード AI パネルを調整する | [`backend_server,frontend_avatar,frontend_web,AIコードパネル拡張手順.md`](./backend_server,frontend_avatar,frontend_web,AIコードパネル拡張手順.md) |

## Code CLI

| 目的 | 参照ファイル |
|------|--------------|
| Code CLI を追加する | [`backend_server,backend_hermes,frontend_avatar,frontend_web,CodeCLI追加手順.md`](./backend_server,backend_hermes,frontend_avatar,frontend_web,CodeCLI追加手順.md) |
| Code CLI の MCP 設定を確認する | [`backend_hermes,backend_mcp,CodeCLI_MCP設定.md`](./backend_hermes,backend_mcp,CodeCLI_MCP設定.md) |
| aidiy_hermes の MCP SSE 接続を修復・確認する | [`backend_hermes,backend_mcp,MCP_SSE接続.md`](./backend_hermes,backend_mcp,MCP_SSE接続.md) |
| Code CLI のプロンプト整形責務を確認する | [`backend_server,CodeCLIプロンプト整形.md`](./backend_server,CodeCLIプロンプト整形.md) |
| CLI 出力の ANSI 制御コードを除去する | [`backend_server,backend_hermes,frontend_avatar,CodeCLI表示ANSI制御コード対処.md`](./backend_server,backend_hermes,frontend_avatar,CodeCLI表示ANSI制御コード対処.md) |
| Hermes CLI の TUI を調整する | [`backend_hermes,TUI調整手順.md`](./backend_hermes,TUI調整手順.md) |
| backend_hermes を単体 CLI として起動・確認する | [`backend_hermes,backend_server,運用手順.md`](./backend_hermes,backend_server,運用手順.md) |
| hermes を MCP サーバーとして起動・Code CLI から接続する | [`backend_hermes,MCP_サーバー起動.md`](./backend_hermes,MCP_サーバー起動.md) |
| hermes-agent 新バージョンへ追従・移行する | [`backend_hermes,Upstream移行手順.md`](./backend_hermes,Upstream移行手順.md) |

## ドキュメント・共通

| 目的 | 参照ファイル |
|------|--------------|
| Markdown を現行実装へ追従させる | [`共通,Markdown現状追従チェック.md`](./共通,Markdown現状追従チェック.md) |
| `AGENTS.md` 系ドキュメントを概要と HowTo に分離する | [`共通,AGENTS整理手順.md`](./共通,AGENTS整理手順.md) |
| `.aidiy/knowledge` を更新する | [`共通,ナレッジ更新手順.md`](./共通,ナレッジ更新手順.md) |
| UTF-8 BOM を検出・除去する | [`共通,UTF8BOM問題対処.md`](./共通,UTF8BOM問題対処.md) |
| 一時ファイル・バックアップを整理する | [`共通,クリーンアップ手順.md`](./共通,クリーンアップ手順.md) |
| GitHub issue を確認・close する | [`共通,GitHubIssue運用手順.md`](./共通,GitHubIssue運用手順.md) |

## 記録ルール

- ファイル名は `モジュール,トピック名.md` 形式にする（上記「ファイル命名規則」参照）。
- 同じテーマの知見は既存ファイルへ統合する。
- 残すのは HowTo、判断基準、注意点、確認方法だけにする。
- 日付つき履歴、担当者メモ、経緯説明、完了報告、編集対象の列挙だけの記録は残さない。
- 現行実装と同期が必要な値は、同期元のファイルパスを併記する。
- `.aidiy/knowledge` 更新とアプリ本体の仕様変更は混同しない。
