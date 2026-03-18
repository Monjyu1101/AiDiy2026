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
  - バックエンド: FastAPI (Python 3.13.3) + SQLAlchemy + SQLite
  - フロントエンド Web: Vue 3 + Vite + TypeScript + Pinia (Node.js v22.14.0 / npm 11.3.0)
  - フロントエンド Avatar: Vue 3 + Vite + TypeScript + **Electron** + Three.js (VRM/VRMA 3D アバター)
  - デュアルサーバー構成（Core: 8091 / Apps: 8092）

- **実用的なテンプレート実装**
  - 権限管理、マスタデータ管理、トランザクション管理
  - カスタムID生成システム（C採番）
  - JWT認証、WebSocket統合

- **AI統合の実験場**
  - マルチベンダーAI対応（Anthropic Claude, OpenAI, Google Gemini）
  - リアルタイムAI対話インターフェース（AIコア）
  - デスクトップアバタークライアント（frontend_avatar）: WebSocket + 音声処理 + 3D VRM アバター

- **自己検証**
  - エージェント自身が生成したコードや変更内容を自動的にレビューし、品質と整合性を保つための機能。

---

## 実装メモ（概要）

- 起動は `python _start.py`（backend 8091/8092 + frontend web 8090 を同時起動、avatar は別途 `cd frontend_avatar && npm run dev`）
- SQLite DB は `backend_server/_data/AiDiy/database.db` に作成され、core_main / apps_main で共有
- 初期ログインは `admin / ********`（初期データ投入は admin 未存在時のみ）
- 開発環境: Python 3.13.3 + uv (backend) / Node.js v22.14.0 + npm 11.3.0 (frontend)
- CRUD操作は全てPOSTメソッド（統一API設計）
- frontend_avatar は Electron アプリ（port 8099）、フレームレス透明ウィンドウ + role 制御（login / core / chat / file / image / code1-4）
- ウィンドウ間状態同期: BroadcastChannel `avatar-desktop-sync`
- AI名命名規則: `CHAT_AI_NAME` = `*_chat`、`LIVE_AI_NAME` = `*_live`、`CODE_AI*_NAME` = `*_code`（厳格な完全一致）

---

## 詳細な内容

詳細はプロジェクトルートの **[AGENTS.md](./AGENTS.md)** を参照してください。