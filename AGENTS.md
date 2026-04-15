# プロジェクト全体方針 (AGENTS.md)

## 本書の目的

このファイルは **AiDiy プロジェクト全体の基本方針、アーキテクチャ概要、開発環境のセットアップ手順** を記載した総合ドキュメントです。
本書は **日本語で分かりやすく記載しています**（全書共通の方針として、追記時もこの方針を維持します）。

**対象読者：**
- AiDiyプロジェクトの全体像を把握したい開発者
- 新規メンバーのオンボーディング
- プロジェクトの基本方針や命名規則を確認したい開発者

**このドキュメントの役割：**
- プロジェクト全体の概要と目的の理解
- 日本語命名規約とテーブル命名規則の把握
- 開発環境のセットアップとコマンドの参照
- バックエンドとフロントエンドの詳細ドキュメントへのナビゲーション

**バックエンドサーバーとフロントエンドサーバーの詳細は別ドキュメント：**
- **バックエンド（FastAPI + SQLAlchemy + SQLite）の実装詳細** → [backend_server/AGENTS.md](./backend_server/AGENTS.md)
- **バックエンド MCP（Chrome DevTools MCP サーバー）の実装詳細** → [backend_mcp/AGENTS.md](./backend_mcp/AGENTS.md)
- **フロントエンド Web（Vue 3 + Vite + TypeScript）の実装詳細** → [frontend_web/AGENTS.md](./frontend_web/AGENTS.md)
- **フロントエンド Avatar（Electron/Web デュアルモード）の実装詳細** → [frontend_avatar/AGENTS.md](./frontend_avatar/AGENTS.md)

**関連ドキュメント：**
- **[./CLAUDE.md](./CLAUDE.md)** - Claude Code向けインデックス（クイックスタート、アーキテクチャサマリー）
- **[./docs/](./docs/)** - HTML形式の詳細ドキュメント（コーディングルール、実装例など）
- **[./backend_server/AGENTS.md](./backend_server/AGENTS.md)** - バックエンド実装の完全ガイド
- **[./frontend_web/AGENTS.md](./frontend_web/AGENTS.md)** - フロントエンド実装の完全ガイド

**このファイルの内容：**
- AiDiyとは何か（プロジェクトの目的と特徴）
- プロジェクト概要と基本方針
- 日本語命名規約とテーブル命名規則
- アーキテクチャ概要（3サーバー構成、主要な設計パターン）
- 開発コマンド（起動方法、依存関係管理）
- アクセスURL・ポート設定
- よくある問題と解決方法
- テスト手順
- バックエンド/フロントエンドドキュメントの内容インデックス

**コーディングルール・開発フローは別ドキュメント：**
- **[./docs/開発ガイド/11_コーディングルール/](./docs/開発ガイド/11_コーディングルール/_index.html)** - 詳細なコーディングルール、命名規則、ベストプラクティス
- **[./docs/開発ガイド/12_フロントエンド画面追加例/](./docs/開発ガイド/12_フロントエンド画面追加例/_index.html)** - フロントエンドCRUD画面追加手順

---

## 📚 ドキュメントリソース（docs/フォルダ）

プロジェクトの詳細なドキュメントは **`docs/`フォルダ** にHTML形式で整備されています。

| フォルダ | 内容 |
|---------|------|
| **[docs/開発ガイド/00_このプロジェクトの歩き方/](./docs/開発ガイド/00_このプロジェクトの歩き方/_index.html)** | システム全体の概要、FAQ |
| **[docs/開発ガイド/01_明日のために！その１_環境構築ハンズオン/](./docs/開発ガイド/01_明日のために！その１_環境構築ハンズオン/_index.html)** | 環境構築ハンズオン |
| **[docs/開発ガイド/02_明日のために！その２_設計/](./docs/開発ガイド/02_明日のために！その２_設計/_index.html)** | 設計方針・設計手順 |
| **[docs/開発ガイド/03_明日のために！その３_バックエンド開発/](./docs/開発ガイド/03_明日のために！その３_バックエンド開発/_index.html)** | バックエンドAPI実装手順 |
| **[docs/開発ガイド/04_明日のために！その４_フロントエンド開発/](./docs/開発ガイド/04_明日のために！その４_フロントエンド開発/_index.html)** | フロントエンド実装手順 |
| **[docs/開発ガイド/11_コーディングルール/](./docs/開発ガイド/11_コーディングルール/_index.html)** | 命名規則、ベストプラクティス、レビューチェックリスト |
| **[docs/開発ガイド/12_フロントエンド画面追加例/](./docs/開発ガイド/12_フロントエンド画面追加例/_index.html)** | フロントエンドCRUD画面追加手順 |

**開発時は必ず参照してください。** 特にコーディングルール（docs/開発ガイド/11）は必読です。

### `.aidiy` フォルダの使い方（重要）

`.aidiy` フォルダは、**コードエージェントの実行ルート直下に置く、そのプロジェクト専用の知見フォルダ**です。
グローバル共通知識ではなく、**プロジェクトごとに分離された修正知見・履歴**として扱ってください。

#### 基本方針
- `.aidiy` は **コードエージェントの実行ルート配下**に作成・参照する
- 知見は **そのプロジェクト専用** とし、他プロジェクトと混在させない
- ファイル操作を伴う修正を行う場合、**まず `.aidiy/_index.md` を確認**し、類似修正の知見があれば利用する
- 修正と検証が完了したら、必要に応じて `.aidiy` 配下へ知見を追記し、次回以降の改造精度を上げる

#### 主なファイル
- `.aidiy/_index.md`
  - 自己改善のためのインデックス
  - 修正テーマ別メモへの導線をまとめる
- `.aidiy/_最終変更.md`
  - 直近の修正内容の要約
  - ユーザーから再修正依頼が来た際の最優先参照先
- `.aidiy/<修正テーマ>.md`
  - テーマ別の修正記録
  - 修正内容、関連ファイル、関連箇所、注意点、次回への知見を記録する

#### 記録ルール
- ファイル名は **内容がわかる日本語名** を優先する
- 単なる作業ログではなく、**次回の修正に再利用できる知見** を残す
- 同じテーマの修正が増えた場合は、重複ファイルを増やすより **既存知見へ統合** を優先する
- `.aidiy` 更新時は、**アプリ本体の仕様変更と混同しない**こと
  - 本体修正は通常のソースコードへ
  - 知見整理は `.aidiy` へ

#### コードエージェント利用時のルール
プロジェクト内のファイル操作を行う場合は、
- `.aidiy` フォルダ
- `.aidiy/_index.md`
を確認し、類似の操作の記載があれば知見として利用してください。

### 新規作成時の自己検証（必須）

新規作成（新規API・新規テーブル・新規画面）を行った場合は、実装完了後に以下ドキュメントを使って**自己検証を必ず実施**してください。

- **歩き方**: [docs/開発ガイド/00_このプロジェクトの歩き方/](./docs/開発ガイド/00_このプロジェクトの歩き方/_index.html)
- **明日のために**: [docs/開発ガイド/01_明日のために！その１_環境構築ハンズオン/](./docs/開発ガイド/01_明日のために！その１_環境構築ハンズオン/_index.html) ～ [docs/開発ガイド/04_明日のために！その４_フロントエンド開発/](./docs/開発ガイド/04_明日のために！その４_フロントエンド開発/_index.html)

実装内容に応じて該当章のチェック項目（手順、確認観点、動作確認）を一通り実施し、抜け漏れがないことを確認してください。

**【重要】バックエンドテーブル新規追加時の必須チェック項目:**
1. `apps_models/__init__.py` に Model import 追加済み（テーブル生成に必要）
2. **`apps_crud/__init__.py` に CRUD関数の import と __all__ 追加済み（必須、忘れやすい）**
3. `apps_main.py` に Router 登録済み
4. 初期データ作成時は `apps_crud/init.py` に初期化処理追加済み

過去実績: マスタテーブル追加時に `apps_crud/__init__.py` への登録漏れでエラー発生。CRUD関数が import されておらず、Router で CRUD関数が使えませんでした。

---

## AiDiyとは

**AiDiy** (AI Do-It-Yourself) は、**日本語を第一言語とするフルスタックビジネス管理システムの開発フレームワーク/テンプレート** です。

### プロジェクトの目的

1. **日本語ネイティブな開発環境の提供**
   - データベーステーブル名、カラム名、API endpoints、JSON keys、Vue components 全てが日本語
   - 日本語話者にとって理解しやすく、ビジネスドメインと完全に一致したコード

2. **実用的なビジネスアプリケーションのテンプレート**
   - 権限管理、マスタデータ管理、トランザクション管理の実装例
   - CRUD操作、検索、ソート、ページングなどの標準機能
   - カスタマイズ可能な基盤システム

3. **AI統合の実験場**
   - マルチベンダーAI対応（Anthropic Claude, OpenAI, Google Gemini）
   - WebSocketによるリアルタイムAI対話
   - 音声・画像・テキスト統合インターフェース (AIコア)
   - **マルチ Code CLI 対応** — `claude_sdk` / `claude_cli` / `copilot_cli` / `codex_cli` / `gemini_cli` / `hermes_cli` を並走
   - **自己改善機構** — コードエージェントが修正完了後に `.aidiy/` へ知見を自動整理し、使うほど修正精度が上がる

### 提供される機能

**開発フレームワーク/テンプレートシステムとして以下のサンプル実装を提供：**

- **C系 (Core/Common)** - User and permission management
  - C権限 - 権限マスタ
  - C利用者 - 利用者マスタ（JWT認証）
  - C採番 - カスタムID生成システム

- **M系 (Master)** - Master data management
  - M配車区分 - 配車区分マスタ
  - M生産区分 - 生産区分マスタ（例: 原料系・完成品系）
  - M生産工程 - 生産工程マスタ（例: 混合・充填・包装）
  - M商品分類 - 商品分類マスタ
  - M車両 - 車両マスタ
  - M商品 - 商品マスタ（原料・完成品）
  - M商品構成 - 商品構成マスタ（**明細型マスタ**：ヘッダー＋明細を単一テーブルで管理）

- **T系 (Transaction)** - Transaction management
  - T配車 - 配車トランザクション
  - T生産 - 生産トランザクション（**明細型**：生産ヘッダー＋材料払出明細を単一テーブルで管理）
  - T商品入庫/出庫/棚卸 - 在庫管理トランザクション

- **V系 (View)** - Complex query views（生SQLクエリ、DB VIEWオブジェクト不使用）
  - V利用者、V権限、V採番 - コア系JOIN表示（core_main）
  - V配車区分、V生産区分、V生産工程、V商品分類、V車両、V商品、V商品構成 - マスタJOIN表示
  - V配車、V生産、V生産払出 - トランザクションJOIN表示
  - V商品入庫、V商品出庫、V商品棚卸、V商品推移表 - 在庫管理JOIN・集計表示

- **S系 (Scheduler/Special)** - Special processing
  - S配車_週表示、S配車_日表示 - 配車スケジュール表示
  - S生産_週表示、S生産_日表示 - 生産スケジュール表示

- **A系 (AI/Advanced)** - AI integration
  - AIコア - Multi-panel AI interface（WebSocket + マルチベンダーAI）
  - A会話履歴 - Conversation history storage

- **X系 (Experimental)** - Test/example features (フロントエンドのみ)
  - Xテトリス、Xインベーダー、Xリバーシ - ゲーム実装例
  - X自己紹介 - 静的コンテンツの実装例

### 対象ユーザー

- 日本語でビジネスアプリケーションを開発したいチーム
- FastAPI + Vue 3 のフルスタック開発を学びたい開発者
- AI統合の実装例を探している開発者
- 管理画面・CRUD システムのテンプレートを必要とするプロジェクト

## プロジェクトの特徴

### 1. 日本語ファースト設計

**全レイヤーで日本語識別子を使用：**
- Database: テーブル名 `C権限`, カラム名 `利用者ID`
- API: Endpoints `/core/利用者/一覧`, JSON keys `{"利用者名": "admin"}`
- フロントエンド: コンポーネント `C利用者一覧.vue`, ルート `/C管理/C利用者/一覧`
- Code: Variables `利用者名`, `配車日付`, `商品名`

**メリット：**
- ビジネスドメインとコードの完全な一致
- 日本語話者にとって理解しやすい
- ドキュメントとコードのギャップがない

### 2. 3サーバーアーキテクチャ

**3つの独立したサーバー：**
- **core_main.py** (port 8091) - Core/Common features (C系, A系)
- **apps_main.py** (port 8092) - Application features (M系, T系, V系, S系)
- **mcp_main.py** (port 8095) - MCP サーバー（Chrome DevTools MCP — AIブラウザ自動操作）
- core/apps は同じSQLiteデータベースを共有
- Vite Proxy で `/core/*` と `/apps/*` を自動振り分け

**メリット：**
- 機能のモジュラー化
- 独立したデプロイとスケーリング
- 開発時のサーバー再起動が高速

### 3. POST中心のAPI設計

**全CRUDエンドポイントはPOSTメソッド：**
- `/core/利用者/一覧` (POST) - 一覧取得
- `/core/利用者/取得` (POST) - 1件取得
- `/core/利用者/登録` (POST) - 作成
- `/core/利用者/変更` (POST) - 更新
- `/core/利用者/削除` (POST) - 削除

**統一レスポンス形式：**
```json
{
  "status": "OK" | "NG",
  "message": "メッセージ",
  "data": {...}
}
```

### 4. Database VIEWsを使わないアーキテクチャ

- V系エンドポイントは生SQLクエリ（SELECT + LEFT JOIN）で実装
- データベースVIEWオブジェクトは作成しない
- 柔軟性と保守性を優先

### 5. カスタムID生成システム (C採番)

- AUTOINCREMENTを使用しない
- C採番テーブルで各テーブルのID採番を管理
- トランザクション保護された予測可能なID生成

### 6. 監査フィールドの標準化

**全テーブルに自動付与：**
- 登録日時、登録利用者ID、登録利用者名、登録端末ID
- 更新日時、更新利用者ID、更新利用者名、更新端末ID
- 共通ヘルパー関数で統一生成

### 7. No Alembic Migrations

- マイグレーションツール不使用
- SQLAlchemyモデル更新 + データベースリセットで対応
- シンプルで迅速な開発サイクル
- **テーブル追加・項目追加時は既存DBへの `ALTER TABLE` 適用が必須**
  （既存データが残っている場合、モデルとDBのスキーマが乖離してサーバー起動エラーになる）
- **機能削除時は不要テーブルを `DROP TABLE` で削除すること**
- 詳細な手順・サンプルコード → **[backend_server/AGENTS.md](./backend_server/AGENTS.md)** の「テーブルスキーマ変更時の必須対応」参照

### 8. AI統合システム (AIコア)

**マルチベンダーAI対応：**
- Anthropic Claude (claude-agent-sdk)
- OpenAI (GPT models)
- Google Gemini (Native Audio Preview)

**WebSocketリアルタイム通信：**
- ストリーミングレスポンス
- 音声・画像・テキスト統合
- セッション永続化（リロード対応）

**コードエージェント補足（重要）:**
- コードエージェントは project ごとの `.aidiy` 知見フォルダを利用する
- 修正系処理では `.aidiy/_index.md` の類似知見を参照し、完了後は `.aidiy` へ知見整理を追記する
- 新しい code CLI を追加する場合は、backend の CLI 実装・モデル定義・設定JSON・frontend の設定UI対応を一式揃える
- 詳細な実装手順は `backend_server/AGENTS.md` を参照

### 9. qTublerシステム（カスタムテーブル）

- UIフレームワーク不使用
- カスタムグリッドレイアウトテーブル
- ソート、ページング、行選択機能
- 統一されたUI/UX

### 10. Reboot機構（内部再起動システム）

- `temp/reboot_core.txt` または `temp/reboot_apps.txt` でサーバー再起動
- `_start.py` による自動プロセス監視
- 設定変更やコード再読み込みに便利

### 11. 実用的な管理画面とサンプルシステム

**完全に動作する管理画面を実装：**
- 権限管理画面（C権限）- 権限マスタのCRUD
- 利用者管理画面（C利用者）- ユーザーマスタのCRUD
- 採番管理画面（C採番）- ID採番設定のCRUD
- マスタデータ管理（M配車区分、M車両、M商品、M商品分類、M生産区分、M生産工程）
- 商品構成マスタ（M商品構成）- 明細型マスタのCRUD（ヘッダー＋材料明細）
- トランザクション管理（T配車、T商品入庫/出庫/棚卸）
- 生産トランザクション（T生産）- 明細型トランザクションのCRUD（生産ヘッダー＋材料払出明細）
- スケジュール表示（S配車_週表示/日表示、S生産_週表示/日表示）
- ビュー表示（V商品推移表、V生産、V生産払出）

**サンプルシステムとして：**

#### 配車管理システム

車両と配車区分を管理し、日付ベースのスケジュール計画を実現する。

| 構成要素 | テーブル/エンドポイント | 内容 |
|---------|----------------------|------|
| マスタ | M配車区分、M車両 | 配車区分・車両の登録管理 |
| トランザクション | T配車 | 配車日付・車両・区分・数量の登録 |
| ビュー | V配車、V配車区分、V車両 | JOIN済みの一覧表示 |
| スケジューラー | S配車_週表示、S配車_日表示 | カレンダー形式の週・日スケジュール表示 |

主なユースケース: 日次配送計画の立案、週間スケジュールの確認。

---

#### 生産管理システム

商品構成（BOM）を定義し、生産指示と材料払出明細を管理する。明細型マスタ・明細型トランザクションの実装例でもある。

| 構成要素 | テーブル/エンドポイント | 内容 |
|---------|----------------------|------|
| 区分マスタ | M生産区分 | 生産区分の登録（例: 原料系・完成品系） |
| 工程マスタ | M生産工程 | 生産工程の登録（例: 混合・充填・包装） |
| 商品分類マスタ | M商品分類 | 商品分類の登録（原料・半製品・完成品など） |
| 商品マスタ | M商品 | 商品の登録（区分・分類・単位など） |
| 構成マスタ（明細型） | M商品構成 | 完成品の材料構成（BOM）を明細型で管理。`明細SEQ=0` がヘッダー、`明細SEQ>=1` が材料明細 |
| 生産トランザクション（明細型） | T生産 | 生産指示と材料払出明細を一体管理。`明細SEQ=0` が生産ヘッダー、`明細SEQ>=1` が払出明細 |
| ビュー | V生産、V生産払出、V商品構成 | JOIN済みの生産一覧・払出明細・構成明細表示 |
| スケジューラー | S生産_週表示、S生産_日表示 | 生産計画の週・日スケジュール表示 |

主なユースケース: 製品ごとの材料構成登録、日次生産指示の発行、払出実績の確認、週間生産計画の閲覧。

---

#### 資材在庫管理システム

商品（資材）の入庫・出庫・棚卸を管理し、在庫推移を集計して表示する。

| 構成要素 | テーブル/エンドポイント | 内容 |
|---------|----------------------|------|
| 商品マスタ | M商品、M商品分類 | 資材・商品の登録（分類・単位など） |
| 入庫 | T商品入庫 | 入庫数量・日付・商品の登録 |
| 出庫 | T商品出庫 | 出庫数量・日付・商品の登録 |
| 棚卸 | T商品棚卸 | 棚卸数量・日付・商品の登録（在庫調整用） |
| ビュー | V商品入庫、V商品出庫、V商品棚卸 | JOIN済みの各種明細表示 |
| 在庫推移表 | V商品推移表 | 商品ごとの期間別入出庫・在庫残数を集計した一覧表 |

主なユースケース: 日次入出庫の記録、棚卸による在庫調整、期間別在庫推移の確認。

---

- 各機能が実際に動作し、カスタマイズ可能
- 統一されたUI/UX（qTublerテーブル、共通ダイアログ）

**実験的機能（X系）：**
- Xテトリス - Canvas APIの実装例
- Xインベーダー - ゲームロジックの実装例
- Xリバーシ - アルゴリズムの実装例
- X自己紹介 - 静的コンテンツの実装例

**メリット：**
- すぐに動かせる完成品
- カスタマイズのベースとして使用可能
- 実装パターンの学習教材として最適（明細型マスタ/トランザクションの実装パターン含む）
- プロトタイプ作成が迅速

### 12. 明細型マスタ/トランザクションパターン

ヘッダー行と明細行を**単一テーブルで管理**する設計パターン。

**M商品構成（明細型マスタ）:**
```
商品ID | 明細SEQ | ...
H100   | 0       |  ← ヘッダー行（M商品構成ヘッダーとして扱う）
H100   | 1       |  ← 明細行（原料A）
H100   | 2       |  ← 明細行（原料B）
```

**T生産（明細型トランザクション）:**
```
生産ID | 明細SEQ | ...
P001   | 0       |  ← ヘッダー行（生産指示情報）
P001   | 1       |  ← 明細行（材料払出1）
P001   | 2       |  ← 明細行（材料払出2）
```

**実装の特徴：**
- `明細SEQ=0` がヘッダー、`明細SEQ>=1` が明細
- `get_ヘッダ()`、`get_明細一覧()` で用途別取得
- `build_data()` でヘッダー＋明細をまとめて構築して返す
- `create/update` は全明細を一括削除→再作成（楽観ロック不要）

### 13. アバター デュアルモード実装

frontend_avatar は **Electron デスクトップアプリ**と**通常 Web ブラウザ**の両方で動作する。

**動作モードの判定：**
```typescript
const isElectron = !!window.desktopApi  // IPC bridge が存在すれば Electron
```

| 機能 | Electron モード | Web モード |
|------|----------------|-----------|
| 認証 Storage | `localStorage` | `sessionStorage` |
| ウィンドウ管理 | Electron 複数ウィンドウ（IPC） | 単一ブラウザウィンドウ（タブ切替） |
| レイアウト | 専用パネルウィンドウ | 左アバター＋右タブ切替のスプリット |
| API URL | Vite proxy `/core/...` | Vite proxy `/core/...`（同じプロキシ設定） |
| アクセス URL | Electron 内 http://127.0.0.1:8099 | http://localhost:8099 |

**ウィンドウ役割（WindowRole）：**
- `login` - ログイン画面
- `core` - メインアバター＋AI操作
- `chat` / `file` / `image` / `code1`-`code4` - 各パネル
- `settings` - AI設定ダイアログ（Electron専用ウィンドウ）

**BroadcastChannel `avatar-desktop-sync`** でウィンドウ間のスナップショット状態を同期。

### 14. 音声対話インターフェース

マイクからの音声入力と AI からの音声応答を双方向でリアルタイム処理する。テキストチャットと音声会話の両モードを切り替えながら開発作業を進められる。

**音声処理の流れ：**

```
[マイク] → PCM変換(16kHz) → WebSocket audio チャンネル
                                        ↓
                              AIコア (バックエンド)
                              Gemini Live / OpenAI Realtime
                                        ↓
                     受信PCM(24kHz) → キューバッファ再生 → [スピーカー]
```

**実装コンポーネント（`AIコア_音声処理.ts` / クラス名 `AudioController`）：**

| 機能 | 詳細 |
|------|------|
| マイク入力 | `getUserMedia` → `ScriptProcessorNode` で PCM 変換 |
| 入力サンプルレート | 16kHz（`inputSampleRate = 16000`、モデルにより切替可） |
| 送信 | WebSocket `audio` チャンネル経由で `input_audio` パケット送信 |
| 受信再生 | 受信 PCM をキューに積み順次再生（出力 24kHz） |
| 即時キャンセル | `cancelOutput()` で再生中キューをすべてクリア |
| ビジュアライザー | 入出力それぞれ 32 バンドのスペクトラム計測（`AnalyserNode`） |
| レベル計測 | 入力/出力レベルをアバターの口パク演出に連動 |

**AIモードの種類：**
- `CHAT_AI_NAME`（`_chat` サフィックス） — テキストチャット専用 AI（Claude / GPT / Gemini）
- `LIVE_AI_NAME`（`_live` サフィックス） — 音声リアルタイム対話 AI（Gemini Live / OpenAI Realtime）
- `CODE_AI*_NAME`（`_sdk` または `_cli` サフィックス） — コード支援 AI（コードパネル専用）。有効値: `claude_sdk`, `claude_cli`, `copilot_cli`, `codex_cli`, `gemini_cli`, `hermes_cli`

音声設定は frontend_avatar の `settings` ウィンドウ（AI設定ダイアログ）から切り替え可能。設定変更後はバックエンドが自動再起動（Reboot機構）。

**音声対話で開発（AI Coding with Voice）：**  
AIコアに接続したまま音声で指示を出してコーディング作業を進める使い方を想定している。コードパネル（code1〜code4）にはコード変更内容が表示され、ファイルパネルでリポジトリのファイルツリーと内容を確認しながら会話できる。バックエンドの `files API`（`/core/files/内容取得`、`/core/files/内容更新`）を通じて AI がファイルを直接読み書きする。

### 15. 3D アバター表示インターフェース

VRM フォーマットの 3D キャラクターモデルをリアルタイムレンダリングし、AI の発話・待機・リアクションに応じてモーションと口パクを自動制御する。

**技術スタック：**
- **Three.js** — WebGL レンダラー、シーン・カメラ管理
- **@pixiv/three-vrm** — VRM モデルのロードと BlendShape 制御
- **@pixiv/three-vrm-animation** — VRMA モーションクリップの再生

**アバター表示の構成（`AIコア_アバター.vue`）：**

| コンポーネント | ファイル | 役割 |
|-------------|---------|------|
| アバター本体 | `AIコア_アバター.vue` | Three.js シーン構築・VRM ロード・VRMA モーション再生・口パク |
| 自立身体制御 | `AIコア_自立身体制御.ts` | 腕の揺れ・上下ボビング等の自律アニメーション |
| 自動カメラワーク | `AIコア_自動カメラワーク.ts` | カメラポジションの自動アニメーション |

**主な動作仕様：**
- `alpha: true` + `setClearColor(..., 0)` による **背景透過** → Electron のフレームレス透明ウィンドウに重ねて表示
- VRMA モーションは `public/vrma/` フォルダからランダム再生（`サンプル` / `標準` フォルダ分け）
- マイク入力レベル → 口パク（`A` BlendShape）連動
- スピーカー出力レベル → 発話演出連動
- ドラッグ操作でアバターの向きを変更可能

**モデル・モーションのカスタマイズ：**
```
public/vrm/      ← VRM モデルを配置（デフォルト: AiDiy_Sample_M.vrm）
public/vrma/
  サンプル/       ← カスタムモーション
  標準/           ← 基本モーション
```
モデルやモーションを追加する場合は `src/api/config.ts` の定数（`DEFAULT_VRM_MODEL_URL`、`SAMPLE_VRMA_FOLDER_NAME`、`STANDARD_VRMA_FOLDER_NAME`）も合わせて更新する。

**Electron と Web の表示の違い：**
- **Electron** — 透明フレームレスウィンドウとして画面右下に常駐、他アプリと重ねて表示可能
- **Web** — ブラウザの左ペイン（`web-split-layout` の左側）に埋め込み表示

## 概要

Full-stack business management system with JWT authentication, using FastAPI (Python 3.13.3) + SQLite backend and Vue.js 3 frontend.

日本語標準のVue 3フロントエンド + 日本語APIのFastAPIバックエンド。DBはSQLiteを採用し、管理画面中心の構成。生産管理・在庫管理・配車管理の実装例を含む実用的なサンプルシステムとして機能する。フロントエンドは通常のWebブラウザUI（frontend_web）に加え、ElectronとWebブラウザの両方で動作するAIアバタークライアント（frontend_avatar）を備える。

## 基本方針

- 画面/URL/JSONキー/識別子は日本語を原則とする
- 文字コードはUTF-8固定
- 全ファイルはUTF-8エンコーディング必須
- DBテーブルから取得/保存する項目は、できるだけDB項目名と同じ変数名を使う
- DB項目名 / API上の項目名 / ソケット上の項目名は、できるだけ同じ変数名を使う
- request / query / item / items / total / limit などの一般名は英字のまま使用する
- ファイル内容確認はUTF-8指定で読む（例: `Get-Content -Encoding UTF8`）

## テーブル命名規則

- `C` = Core/Common tables (C権限, C利用者, C採番)
- `M` = Master tables (M車両, M商品, M配車区分, M生産区分, M生産工程, M商品分類, M商品構成)
  - **明細型マスタ**: M商品構成は `明細SEQ=0` がヘッダー行、`明細SEQ≥1` が明細行として単一テーブルで管理
- `T` = Transaction tables (T配車, T商品入庫, T商品出庫, T商品棚卸, T生産)
  - **明細型トランザクション**: T生産は `明細SEQ=0` が生産ヘッダー、`明細SEQ≥1` が材料払出明細として単一テーブルで管理
- `V` = View/Joined data endpoints（DBのVIEWオブジェクトではなく、生SQLクエリ実装）
  - コア系（core_main）: V利用者, V権限, V採番
  - マスタJOIN表示（apps_main）: V車両, V商品, V配車区分, V生産区分, V生産工程, V商品分類, V商品構成
  - トランザクションJOIN表示（apps_main）: V配車, V生産, V生産払出, V商品入庫, V商品出庫, V商品棚卸, V商品推移表
- `S` = Scheduler/Special processing (S配車_週表示, S配車_日表示, S生産_週表示, S生産_日表示)
- `A` = AI/Advanced features (AIコア, A会話履歴)
- `X` = Experimental/Test features (Xテトリス, Xインベーダー, Xリバーシ, X自己紹介)

## Japanese Naming Convention

This project uses Japanese identifiers extensively:

- **Database**: Table names (C権限, C利用者), column names (利用者ID, パスワード)
- **API**: JSON keys in requests/responses (ユーザー名, 権限ID)
- **API endpoints**: `/core/利用者/一覧`, `/core/権限/作成`
- **Code**: Variables, class attributes, function parameters use Japanese where it clarifies business domain concepts
- **Vue files**: File names, route paths, component names use Japanese
- **File Encoding**: All files must be UTF-8

When adding new code, follow this convention for business logic. System/framework code can use English.

**Rationale**: Improves clarity for Japanese-speaking stakeholders and aligns code with business domain.

## Architecture Overview

This project consists of three main parts:

### バックエンド (backend_server/)

FastAPI + SQLAlchemy + SQLite backend with Japanese API endpoints and JWT authentication.

**技術スタック：**
- Python 3.13.3 + uv (package manager)
- FastAPI + Uvicorn (ASGI server)
- SQLAlchemy (ORM, no Alembic)
- SQLite (single file database)
- python-jose (JWT authentication, HS256)
- AI SDKs: anthropic, openai, google-genai, claude-agent-sdk

**主要な設計パターン：**
- core/apps デュアルサーバー + backend_mcp 連携
- POST中心のAPI設計（統一レスポンス形式）
- Database VIEWsを使わない（生SQLクエリ）
- カスタムID生成システム (C採番)
- 監査フィールドの標準化
- Reboot機構（内部再起動システム）
- 構成管理システム (conf/)
- WebSocket統合 (AIコア/AIセッション管理.py)
- AI統合機能 (AIコア/)

**詳細は [backend_server/AGENTS.md](backend_server/AGENTS.md) を参照**

### フロントエンド Web (frontend_web/)

Vue 3 + Vite + TypeScript frontend with Japanese component names and routes.

**技術スタック：**
- Node.js v22.14.0 + npm 11.3.0
- Vue 3 Composition API + script setup
- Vite (build tool)
- TypeScript (strict mode disabled)
- Pinia (state management)
- Vue Router 4 (日本語URL対応)
- Axios (HTTP client with interceptors)
- dayjs (日付処理)
- jQuery（一部レガシー機能）

**主要な設計パターン：**
- シングルページアプリケーション (SPA)
- カテゴリベースのコンポーネント構成
- 統一されたCRUD画面パターン
- qTublerシステム（カスタムテーブルコンポーネント）
- 共通ダイアログシステム (qAlert, qConfirm, qColorPicker)
- レイアウトシステム (_Layout, _TopBar, _TopMenu)

**詳細は [frontend_web/AGENTS.md](frontend_web/AGENTS.md) を参照**

### フロントエンド Avatar (frontend_avatar/)

Electron デスクトップアプリと通常 Web ブラウザの**両方で動作する**AIコア専用アバタークライアント。

**動作モード：**
- **Electron モード**: デスクトップアプリとして起動（`npm run dev` → Electron + Vite）
- **Web モード**: 通常ブラウザで http://localhost:8099 にアクセス

**技術スタック：**
- Node.js + npm
- Vue 3 Composition API + Vite + TypeScript
- Electron（デスクトップアプリ）
- Three.js + @pixiv/three-vrm / @pixiv/three-vrm-animation（3D VRMアバター）
- Monaco Editor（コード表示）
- Axios（REST API通信）
- WebSocket（AIコアとのリアルタイム通信）

**主要な設計パターン：**
- Vue Router / Pinia を**使用しない**（単一 App + 複数 Electron ウィンドウ）
- `const isElectron = !!window.desktopApi` でモード判定
- ウィンドウ role 制御（`login` / `core` / `chat` / `file` / `image` / `code1-4` / `settings`）
- BroadcastChannel (`avatar-desktop-sync`) でウィンドウ間状態同期（Electron/Web両対応）
- フレームレス＋透明ウィンドウ（Electron のみ: `transparent: true`, `frame: false`）
- Webモードレイアウト: 左アバター（VRM表示）＋右タブ切替パネル（スプリット画面）
- 認証Storage分岐: Electron → `localStorage`、Web → `sessionStorage`
- REST API（認証・初期化）+ WebSocket（ストリーミング）の2段構成
- VRM/VRMAアバター表示（Three.js）

**詳細は [frontend_avatar/AGENTS.md](frontend_avatar/AGENTS.md) を参照**

## Development Commands

### Starting the Application

**Recommended: Use the unified launcher**
```bash
python _start.py
```
This launcher:
- Kills any processes on ports 8090/8091/8092（Avatar有効時は 8099 も含む）
- Starts FastAPI backend core_main (port 8091 - コア機能)
- Starts FastAPI backend apps_main (port 8092 - アプリ機能)
- Starts Vite dev server (port 8090)
- Optionally starts frontend_avatar (Electron, port 8099) — **デフォルト無効**、起動時に確認あり
- Opens browser to http://localhost:8090
- Monitors servers and auto-restarts crashed processes after 15 seconds
- Stops gracefully on Ctrl+C
- Sets console encoding for Windows

**注意:** `_start.py` は**引数指定ではなく対話形式**で動作します（起動するサービスを対話的に選択）。また uvicorn の `--reload` フラグは付かないため、バックエンドのコード変更は自動で反映されません（Reboot機構 or 手動再起動が必要）。

**Individual servers:**
```bash
# バックエンド Core のみ（プロジェクトルートから）
cd backend_server
.venv/Scripts/python.exe -m uvicorn core_main:app --reload --host 0.0.0.0 --port 8091

# バックエンド Apps のみ（プロジェクトルートから）
cd backend_server
.venv/Scripts/python.exe -m uvicorn apps_main:app --reload --host 0.0.0.0 --port 8092

# フロントエンド Web のみ
cd frontend_web
npm run dev

# フロントエンド Avatar のみ（Electron + Vite on 8099）
cd frontend_avatar
npm run dev
```

**VS Code Debugging:**
Press F5 in VS Code:
- Root `.vscode/launch.json`: Runs `_start.py` with full stack
- `backend_server/.vscode/launch.json`: バックエンドのみ（debugpy）
- `frontend_web/.vscode/launch.json`: フロントエンドのみ（Chromeデバッグ）

### バックエンドのコード変更を反映する方法

`_start.py` で起動した場合、uvicorn の `--reload` フラグが付かないため、コード変更が自動で反映されません。

**方法1: Reboot機構を使う（推奨）**
```bash
# core_main.py を再起動
echo. > backend_server/temp/reboot_core.txt

# apps_main.py を再起動
echo. > backend_server/temp/reboot_apps.txt
```

**方法2: 個別起動で --reload を有効化**
```bash
cd backend_server
.venv/Scripts/python.exe -m uvicorn core_main:app --reload --host 0.0.0.0 --port 8091
```

**方法3: _start.py を再起動**
```bash
# Ctrl+C で停止してから
python _start.py
```

### Dependency Management

**バックエンド（Python 3.13.3 + uv）:**
```bash
cd backend_server
uv sync          # Install/sync dependencies from pyproject.toml
uv add <package> # Add new dependency
```

**フロントエンド Web（Node.js + npm + TypeScript）:**
```bash
cd frontend_web
npm install        # Install dependencies
npm run dev        # Start dev server
npm run build      # Type-check and build for production（※指示がない限り実行禁止）
npm run preview    # Preview production build
npm run type-check # Run TypeScript type checking without building
```

**フロントエンド Avatar（Node.js + Electron）:**
```bash
cd frontend_avatar
npm install        # Install dependencies
npm run dev        # Start Electron + Vite dev server (port 8099)
npm run type-check # Run TypeScript type checking
# ※ npm run build は明示的な指示があるときのみ実行（dist/ を生成する、指示がない限り実行禁止）
```

### Setup & Cleanup

**初期セットアップ（初回またはリセット時）:**
```bash
python _setup.py
```
- Python 仮想環境作成・依存パッケージのインストール（`uv sync`）
- フロントエンド（Web / Avatar）の `npm install`
- 対話形式で実行（引数指定なし）

**クリーンアップ（他のメンバーへの引き渡し前など）:**
```bash
python _cleanup.py
```
- `__pycache__` / `.venv` / `node_modules` / `dist` など不要なキャッシュ・ビルド成果物を削除
- SQLite DB ファイルの削除も選択可能（対話形式で確認）
- 対話形式で実行（引数指定なし）

### Database Management

**Database Location:**
```
backend_server/_data/AiDiy/database.db
```

**Database Reset (recreate all tables and initial data):**
1. Stop all servers (`Ctrl+C` on `_start.py` or close individually started processes)
2. Delete `backend_server/_data/AiDiy/database.db`
3. Restart servers (`python _start.py`)
4. Tables and initial data auto-created on startup

**注意:** 初期データ（admin など）は「該当レコードが未存在」の場合のみ投入されます。既存DBでは自動更新されません。

**Inspect Database:**
- Use SQLite Browser or DBeaver
- Close DB tools before starting servers (avoid "database locked" errors)

### API Testing

**FastAPI Swagger UI:**
- Core API: http://localhost:8091/docs
- Apps API: http://localhost:8092/docs

**Using Swagger UI:**
1. Click "Authorize" button (top right)
2. Enter JWT token from localStorage (login first at http://localhost:8090)
3. Test endpoints interactively
4. All CRUD endpoints use POST method

## Access URLs & Port Configuration

- フロントエンド Web: http://localhost:8090
- バックエンドAPI（Core - core_main）: http://localhost:8091
- バックエンドAPI（Apps - apps_main）: http://localhost:8092
- API Documentation (Core): http://localhost:8091/docs (FastAPI Swagger UI)
- API Documentation (Apps): http://localhost:8092/docs (FastAPI Swagger UI)
- バックエンド MCP（mcp_main）SSEエンドポイント: http://localhost:8095/aidiy_chrome_devtools/sse
- フロントエンド Avatar (Electron): http://127.0.0.1:8099 ※Electronアプリとして起動
- フロントエンド Avatar (Web ブラウザ): http://localhost:8099 ※通常ブラウザからもアクセス可能

**Default Login Credentials** (seeded on first startup):
- Admin: `admin` / `********`
- Manager: `leader` / `secret`
- User: `user` / `user`
- Guest: `guest` / `guest`
- Other: `other` / `other`

**実装確認済みの補足（間違いやすい点）:**
- **初期データ投入の条件**: `core_crud.init_db_data()` は **admin が未存在のときだけ** C利用者を投入します。既存DBでは自動更新されません。
- **DBファイル位置**: `backend_server/_data/AiDiy/database.db`（core_main / apps_main で共有）。
- **_start.py の起動挙動**: `uvicorn --reload` は付かないため、バックエンドは自動リロードされません（手動再起動 or reboot_core/reboot_apps.txt を利用）。
- **ポート変更の連動修正**: `frontend_web/vite.config.ts` の `server.port` を変える場合、`backend_server/core_main.py` と `apps_main.py` の CORS 許可リスト、`_start.py` のポート設定も更新が必要。
- **_setup.py の案内文**: `_setup.py` のセットアップ完了メッセージは `python _start.py` を正確に表示するよう修正されましたが、以前のバージョンでは `python start.py` と表示されることがあったため、注意点として記載しています。実ファイルは **`_start.py`** です。

**Vite Proxy Configuration** (`frontend_web/vite.config.ts` / `frontend_avatar/vite.config.ts`):
- `/core/*` → `http://127.0.0.1:8091` (core_main - コア機能)
- `/apps/*` → `http://127.0.0.1:8092` (apps_main - アプリ機能)
- ※ frontend_avatar も同じプロキシ設定を持つ

**CORS allowed origins** (`backend_server/core_main.py` and `apps_main.py`):
- `http://localhost:8090` (production Vite server)
- `http://localhost:5173` (default Vite dev server)
- `http://localhost:3000` (alternative port)

**Port conflicts**: `_start.py` auto-kills processes on 8090/8091/8092（Avatar有効時は 8099 も含む）. To manually kill:
```bash
# Windows
netstat -ano | findstr :8091
taskkill /PID <pid> /F

# Linux/Mac
lsof -ti:8091 | xargs kill -9
```

## Common Issues

| Issue | Symptoms | Solution |
|-------|----------|----------|
| **Port conflicts** | `_start.py` fails with "address already in use" | `_start.py` auto-kills processes on 8090/8091/8092（Avatar有効時は 8099 も含む）, but may fail if unresponsive. Manually kill with `taskkill /F /PID <pid>` on Windows |
| **Japanese characters garbled** | 文字化け in console or UI | Ensure all files are UTF-8 encoded. `_start.py` は出力を cp932/UTF-8 でデコードしますが、**コンソール設定は変更しません** |
| **401 Unauthorized** | API calls fail with 401, redirected to login | JWT token expired or invalid. Check `localStorage` for token, re-login if needed |
| **CORS errors** | "blocked by CORS policy" in browser console | Verify origin in `core_main.py` and `apps_main.py` allowed list: `localhost:8090`, `localhost:5173`, `localhost:3000` |
| **Module not found (Python)** | `ModuleNotFoundError` when starting backend | Run `cd backend_server && uv sync` to install dependencies |
| **Module not found (npm)** | Vite build errors or missing packages | Run `cd frontend_web && npm install` |
| **Database locked** | `sqlite3.OperationalError: database is locked` | Close any SQLite browser/tools accessing `database.db` |
| **Tables not created** | API errors about missing tables | Restart backend servers (core_main and apps_main) - tables auto-create on startup |
| **Auto-restart loop** | `_start.py` restarts servers repeatedly | Check for Python/Node errors in console. Servers restart 15 seconds after crash. Fix the underlying error to stop the loop |
| **Initial data not updating** | admin password or initial records not changing | Initial data only inserts when DB is empty or specific records don't exist. To force re-initialization: stop servers → delete `backend_server/_data/AiDiy/database.db` → restart servers |
| **Vue component shows as text** | Japanese component name appears as text in browser | Japanese tags are invalid in HTML. Use `<component :is="日本語コンポーネント名" />` instead of `<日本語コンポーネント名 />` |
| **Database reset needed** | Need to recreate tables from scratch | Stop all servers → Delete `backend_server/_data/AiDiy/database.db` → Restart servers (tables and initial data auto-created) |
| **WebSocket接続エラー (AIコア)** | `LiveAI未初期化のため音声送信不可: ws-xxxx` | WebSocket接続と LiveAI 初期化のタイミング問題。フロントエンドで接続→設定送信の順序を確認。バックエンドログで初期化ステップを確認。詳細は [backend_server/AGENTS.md](./backend_server/AGENTS.md) の「AIコア Component System」セクション参照 |
| **コード変更が反映されない** | バックエンドのコードを変更しても動作が変わらない | `_start.py` で起動した場合は `--reload` なし。`temp/reboot_core.txt` または `temp/reboot_apps.txt` を作成して再起動、または上記「バックエンドのコード変更を反映する方法」参照 |
| **M系マスタ一覧でエラー** | M車両・M商品などの一覧画面でエラーが発生 | フロントエンドはV系エンドポイント（`/apps/V車両/一覧` など）を使用します。**M系テーブル追加時はV系エンドポイントも必ず作成**してください。詳細は [backend_server/AGENTS.md](./backend_server/AGENTS.md) の「新しいテーブルを追加する（M系, T系, S系の場合）」参照 |

## Testing

No automated test suites are configured. Testing is done manually:
- **API testing**: FastAPI Swagger UI at http://localhost:8091/docs
- **UI testing**: Browser at http://localhost:8090
- **Sample data**: Auto-seeded on first startup via `crud/init.py`

## Detailed Implementation

実装の詳細は各サブAGENTS.mdを参照：

- **[./backend_server/AGENTS.md](./backend_server/AGENTS.md)** - バックエンド実装詳細（API/DB/認証/初期データ/追加手順）
- **[./frontend_web/AGENTS.md](./frontend_web/AGENTS.md)** - フロントエンド Web 実装詳細（画面/routing/認証/追加手順）
- **[./frontend_avatar/AGENTS.md](./frontend_avatar/AGENTS.md)** - フロントエンド Avatar 実装詳細（Electron/WebSocket/VRM/音声処理）

## Additional Notes

**File Encoding Requirement:**
- **ALL files MUST be UTF-8 encoded** to support Japanese identifiers throughout the codebase
- Windows コンソールのエンコーディングは `_start.py` が変更しないため、必要に応じてターミナル側で調整

**Critical Development Pattern:**
- Vue component tags must use ASCII names
- Use `<component :is="日本語コンポーネント名" />` syntax for dynamic Japanese component names
- File content checks should specify UTF-8 (e.g., `Get-Content -Encoding UTF8`)
- frontend_web の数値入力欄は、非フォーカス時は3桁区切り表示、フォーカス時はカンマを外して全選択、フォーカスアウト時に再度カンマ表示へ戻す。
- frontend_web の日付欄・日時欄は、原則としてセンタリング表示に統一する。
- frontend_web の固定幅入力欄は、ラベル幅 `160px` と同一、またはその倍数幅で揃える。
- frontend_web の単位付き入力欄は、入力欄単体ではなく「入力欄＋単位」の合計幅で、ラベル幅 `160px` と同一、またはその倍数幅で揃える。
- frontend_web の ID 選択欄は、ラベルを業務名で表示し、選択肢は `ID : 名称` 形式で統一する。
- frontend_web の検索欄も同じ UI ルールで揃え、ラベル幅 `160px`、入力欄は `160px` または `320px` を基準にする。

**No Alembic Migrations:**
- This project does NOT use Alembic migrations
- Schema changes: SQLAlchemy model update + **ALTER TABLE** for existing DB (or full DB reset)
- **カラム追加・テーブル追加時**: `PRAGMA table_info` で確認 → `ALTER TABLE ADD COLUMN` を `init.py` に組み込む
- **機能削除時**: 不要テーブルを `DROP TABLE IF EXISTS` で削除する
- **詳細手順** → [backend_server/AGENTS.md](./backend_server/AGENTS.md) 「テーブルスキーマ変更時の必須対応」

**Database VIEWs:**
- VIEWs are not created as database objects in this implementation
- VIEW endpoints (`core_router/V*.py`, `apps_router/V*.py`) use raw SQL queries with JOINs
- Each VIEW router directly executes SELECT statements to fetch joined data

## GitHub Issues の確認方法と Close 手順

### issue の確認方法

- issue 内容は GitHub の issue ページで確認する  
  例: `https://github.com/monjyu1101/AiDiy2026/issues/1`
- issue 本文・期待動作・最新コメントを確認したうえで、ローカル実装と突き合わせる
- 実装確認時は、まず関連キーワードを `rg` で検索し、該当ファイルを UTF-8 指定で読む  
  例: `Get-Content -Encoding UTF8 <file>`
- 最終判断は、**現在の実装を正とするのか**、**issue 文面を厳密に満たすのか**を明確にしてから行う

### 作者として close する方法

`gh` コマンドが入っていない環境があるため、このリポジトリでは **PowerShell + GitHub REST API** でも close できるようにしておく。

#### 前提

- Windows Credential Manager に GitHub 認証情報が保存されていること
- 対象 credential の例:
  - `GitHub - https://api.github.com/<GitHubユーザー名>`
- **credential blob は Unicode ではなく UTF-8 で読むこと**
  - Unicode 解釈だと `401 Unauthorized`
  - UTF-8 解釈で GitHub API 認証が通る場合がある

#### 手順

1. Windows Credential Manager から `CredReadW` で GitHub credential を取得する
2. `CredentialBlob` を **UTF-8** でデコードして token を得る
3. GitHub API に対して以下を実行する
   - コメント追加  
     `POST https://api.github.com/repos/monjyu1101/AiDiy2026/issues/<番号>/comments`
   - issue close  
     `PATCH https://api.github.com/repos/monjyu1101/AiDiy2026/issues/<番号>`
4. `Authorization: Bearer <token>` を付与する
5. `PATCH` の body は `{"state":"closed"}` とする

#### 備考

- token や credential の実値はドキュメントやソースに残さない
- close 前に、issue コメントで「なぜ close するのか」を簡潔に残す
- 今回の `issue #1`, `issue #2` はこの方法で作者コメント付き close を実施した
