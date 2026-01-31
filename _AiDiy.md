# AiDiy について

## 本書について

プロジェクト概要のみを説明する資料です。

---

## プロジェクト概要

**AiDiy** (AI Do-It-Yourself) は、**日本語を第一言語とするフルスタックビジネス管理システムの開発フレームワーク/テンプレート** です。

### システムの特徴

- **日本語ネイティブ設計**
  - データベーステーブル名、カラム名、API endpoints、JSON keys、Vue componentsが全て日本語
  - ビジネスドメインと完全に一致したコード

- **フルスタック構成**
  - バックエンド: FastAPI (Python 3.13) + SQLAlchemy + SQLite
  - フロントエンド: Vue 3 + Vite + TypeScript + Pinia
  - デュアルサーバー構成（Core: 8091 / Apps: 8092）

- **実用的なテンプレート実装**
  - 権限管理、マスタデータ管理、トランザクション管理
  - カスタムID生成システム（C採番）
  - JWT認証、WebSocket統合

- **AI統合の実験場**
  - マルチベンダーAI対応（Anthropic Claude, OpenAI, Google Gemini）
  - リアルタイムAI対話インターフェース（AコアAI）

---

## 実装メモ（概要）

- 起動は `python _start.py`（backend 8091/8092 + frontend 8090 を同時起動）
- SQLite DB は `backend_server/_data/AiDiy/database.db` に作成され、main1 / main2 で共有
- 初期ログインは `admin / ********`（初期データ投入は admin 未存在時のみ）

---

## 詳細な内容

詳細はプロジェクトルートの **[AGENTS.md](./AGENTS.md)** を参照してください。
