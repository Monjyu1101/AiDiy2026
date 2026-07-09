# frontend_avatar

`frontend_avatar` は、**Electron デスクトップアプリ** と **通常ブラウザ** の両方で動く AI コア専用クライアントです。

## 前提

- `backend_server`（`8091` / `9098`）が起動していること
- AIタスク画面（TASK ボタン / task ウィンドウ）を使う場合は `backend_task`（`8093`）も起動していること
- Claude 系のブラウザ自動操作まで使う場合は `backend_tools`（`8095`）も起動していること

## 開発起動

```powershell
cd frontend_avatar
npm install
npm run dev
```

`npm run dev` で次が起動します。

- Vite 開発サーバー: `http://127.0.0.1:8092`
- Electron メインプロセス
- Electron アプリ本体

## Web モード

ブラウザからは次で確認できます。

```text
http://localhost:8092
```

## 主な構成

- `src/AiDiy.vue` : renderer 側のメインエントリ
- `src/components/` : ログイン、AIコア、チャット、ファイル、イメージ、コード
- `src/dialog/` : AI設定再起動などのダイアログ
- `electron/main.ts` : Electron メインプロセス
- `electron/preload.ts` : preload
- `src/api/config.ts` : API / WebSocket / VRM 設定

## 接続先

- Core API / WebSocket: `http://localhost:8091` / `ws://localhost:8091/core/ws/AIコア`
- Apps API: `http://localhost:9098`
- Task API（AIタスク）: `http://localhost:8093`（開発時は Vite proxy `/task` 経由、Electron 本番は直結）
- Backend MCP（17 サーバー同居）: `http://localhost:8095/`（一覧）、`http://localhost:8095/{mcp_name}/sse`（SSE 接続）

## 補足コマンド

```powershell
cd frontend_avatar
npm run type-check
```

## ビルド

```powershell
cd frontend_avatar
npm run build
npm run start
```

注意:

- `npm run build` は `dist` / `dist-electron` を生成します。
- 通常の調査や開発では `npm run dev` / `npm run type-check` を優先してください。
