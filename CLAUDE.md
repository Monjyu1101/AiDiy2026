# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 本書の目的

このファイルは **Claude Code 向けのインデックスドキュメント** です。

**重要:** このドキュメントは各種ドキュメントへのナビゲーション（索引）のみを提供します。**新しいドキュメントが追加されない限り、ここには詳細な実装情報を書き込まないでください。** 詳細情報は全て参照先ドキュメントに記載されています。

### CLAUDE.md更新時の必須事項（Claude Code向けの注意）

**🚫 このファイルに詳細情報を書いてはいけません！**

このファイルは **インデックス（目次）専用** です。以下を厳守してください：

**禁止事項：**
- ❌ 具体的な手順やコマンドの詳細説明
- ❌ トラブルシューティングの詳細
- ❌ コード例や設定例
- ❌ 「開発時のポイント」「ベストプラクティス」などの詳細内容
- ❌ 100文字を超える説明文

**許可事項：**
- ✅ 「〇〇については [ファイル名] の××セクションを参照」という案内のみ
- ✅ プロジェクト概要の簡潔な説明（3-5行程度）
- ✅ クイックスタートコマンド（コメントなし）

**このファイルを更新する前に：**
1. **先に各AGENTS.mdを確認すること** - 追加したい情報が既に存在しないか確認
2. **このファイルはインデックスとして使うこと** - 詳細情報は書かず、参照先を示すのみ
3. 詳細情報は適切なドキュメントに記載する：
   - プロジェクト全体・開発方法・よくある問題 → `AGENTS.md`
   - コーディングルール・手順 → `このシステムの歩き方.md`
   - バックエンド詳細 → `backend_server/AGENTS.md`
   - フロントエンド詳細 → `frontend_server/AGENTS.md`

---

## ドキュメント体系

プロジェクトのドキュメントは以下の役割で分類されています：

| ドキュメント | 役割 |
|------------|------|
| **[README.md](./README.md)** | 初回セットアップ・起動・停止・クリーンアップ手順（初心者向け） |
| **[AGENTS.md](./AGENTS.md)** | プロジェクト全体方針、基本方針、テーブル命名規則、開発コマンド、アクセスURL、よくある問題 |
| **[このシステムの歩き方.md](./このシステムの歩き方.md)** | コーディングルール、命名規則、開発フロー、新規機能追加の詳細手順、ベストプラクティス |
| **[backend_server/AGENTS.md](./backend_server/AGENTS.md)** | バックエンド実装詳細（FastAPI/SQLAlchemy/SQLite/API/DB/認証/初期データ/追加手順/Debugging） |
| **[frontend_server/AGENTS.md](./frontend_server/AGENTS.md)** | フロントエンド実装詳細（Vue 3/Vite/TypeScript/Pinia/画面/ルーティング/認証/追加手順/Debugging） |

### 参照順序の推奨

**初めての方:**
1. **[README.md](./README.md)** - セットアップと起動方法を確認
2. **[AGENTS.md](./AGENTS.md)** - プロジェクト全体像を把握
3. **[このシステムの歩き方.md](./このシステムの歩き方.md)** - コーディングルールを理解

**バックエンド開発:**
1. **[backend_server/AGENTS.md](./backend_server/AGENTS.md)** - バックエンド実装を理解
2. **[このシステムの歩き方.md](./このシステムの歩き方.md)** - 新規テーブル追加手順を参照

**フロントエンド開発:**
1. **[frontend_server/AGENTS.md](./frontend_server/AGENTS.md)** - フロントエンド実装を理解
2. **[このシステムの歩き方.md](./このシステムの歩き方.md)** - 新規画面追加手順を参照

**コーディングルール確認:**
- **[このシステムの歩き方.md](./このシステムの歩き方.md)** - 命名規則、ファイルエンコーディング、コメント規則、インデント規則

### 必須理解事項（CRITICAL）

**このプロジェクトの特徴:**
- **日本語優先実装** - これはこのシステムの設計上の特徴です（課題や問題ではありません）
- テーブル名・カラム名・API endpoint・JSON keys・Vue components は日本語
- システム/フレームワーク用語（`request`, `router`, `items`, `total`）は英語
- この命名規則は意図的な設計であり、変更の必要はありません

**ファイルエンコーディング:**
- 全ファイルは **UTF-8 エンコーディング必須**（日本語識別子使用のため）
- 新規ファイル作成時は必ずUTF-8で保存

**実装上の制約:**
- Vue component tags は ASCII のみ（`<component :is="日本語名" />` で対応）

---

## プロジェクト概要

**AiDiy_next** は日本語を第一言語とするフルスタックビジネス管理システムです。

**特徴:**
- データベーステーブル名、カラム名、API endpoints、JSON keys、Vue componentsが全て日本語
- デュアルサーバー構成（Core: port 8091 / Apps: port 8092）
- JWT認証、カスタムID生成（C採番）、WebSocket統合（AコアAI）

**技術スタック:**
- **バックエンド**: FastAPI (Python 3.13) + SQLAlchemy + SQLite
- **フロントエンド**: Vue 3 + Vite + TypeScript + Pinia

**詳細:** [AGENTS.md](./AGENTS.md) を参照してください。

---

## クイックスタート

### 初回セットアップ

```bash
python _setup.py
```

### システム起動

```bash
# 両方起動（デフォルト）
python _start.py

# フロントのみ起動
python _start.py --frontend=yes

# バックのみ起動
python _start.py --backend=yes
```

### アクセスURL

| サービス | URL |
|---------|-----|
| **フロントエンド** | http://localhost:8090 |
| **API (Core)** | http://localhost:8091/docs |
| **API (Apps)** | http://localhost:8092/docs |

### デフォルトログイン

- **ユーザー名**: `admin`
- **パスワード**: `********`

### システム停止

```bash
# 両方停止（デフォルト）
python _stop.py

# フロントのみ停止
python _stop.py --frontend=yes

# バックのみ停止
python _stop.py --backend=yes
```

### 注意点（概要）
- `_start.py` / `_stop.py` はパラメータなし=両方、パラメータあり=yes指定のみ実行
- `_start.py` で起動したバックエンドは `--reload` なし（詳細は [README.md](./README.md) または [AGENTS.md](./AGENTS.md) を参照）
- 初期データの投入は「admin が未存在のときのみ」（詳細は [backend_server/AGENTS.md](./backend_server/AGENTS.md) を参照）
- デュアルサーバー構成: main1.py (C系, A系) + main2.py (M系, T系, V系, S系) - 両方必要

### 詳細な手順

- **セットアップ**: [README.md](./README.md) の「セットアップ」セクション
- **起動・停止**: [README.md](./README.md) の「システム起動」「システム停止」セクション
- **開発コマンド**: [AGENTS.md](./AGENTS.md) の「Development Commands」セクション
- **よくある問題**: [AGENTS.md](./AGENTS.md) の「Common Issues」セクション
- **新規機能追加**: [このシステムの歩き方.md](./このシステムの歩き方.md) の「新規機能の追加手順」セクション
- **ベストプラクティス**: [このシステムの歩き方.md](./このシステムの歩き方.md) の「ベストプラクティス」セクション

---

## 主要なインデックス

**アーキテクチャ理解:**
- Database VIEWs（V系実装）: [AGENTS.md](./AGENTS.md) - "Architecture Overview" セクション
- カスタムID生成（C採番）: [backend_server/AGENTS.md](./backend_server/AGENTS.md) - "Custom ID Generation System" セクション
- API設計パターン: [backend_server/AGENTS.md](./backend_server/AGENTS.md) - "API Design Pattern" セクション
- 認証フロー: [backend_server/AGENTS.md](./backend_server/AGENTS.md) - "Authentication & Security" セクション
- 監査フィールド: [backend_server/AGENTS.md](./backend_server/AGENTS.md) - "Audit Fields Pattern" セクション

**開発タスク:**
- 新規テーブル追加: [このシステムの歩き方.md](./このシステムの歩き方.md) - 「バックエンド：新規テーブルの追加」「フロントエンド：新規CRUD画面の追加」セクション
- 新規VIEW追加: [このシステムの歩き方.md](./このシステムの歩き方.md) - 対応するセクション
- データベースリセット: [README.md](./README.md) - トラブルシューティング、または [AGENTS.md](./AGENTS.md) - "Common Issues"

**デバッグ:**
- バックエンドデバッグ: [backend_server/AGENTS.md](./backend_server/AGENTS.md) - "Debugging" セクション
- フロントエンドデバッグ: [frontend_server/AGENTS.md](./frontend_server/AGENTS.md) - "Debugging" セクション

