# frontend_avatar

`frontend_avatar` は、**Electron デスクトップアプリ** と **通常ブラウザ** の両方で動く AI コア専用クライアントです。

## 前提

- `backend_server`（`8091` / `8092`）が起動していること
- Claude 系のブラウザ自動操作まで使う場合は `backend_mcp`（`8095`）も起動していること

## 開発起動

```powershell
cd frontend_avatar
npm install
npm run dev
```

`npm run dev` で次が起動します。

- Vite 開発サーバー: `http://127.0.0.1:8099`
- Electron メインプロセス
- Electron アプリ本体

## Web モード

ブラウザからは次で確認できます。

```text
http://localhost:8099
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
- Apps API: `http://localhost:8092`
- Backend MCP Chrome DevTools (SSE): `http://localhost:8095/aidiy_chrome_devtools/sse`
- Backend MCP Desktop Capture (SSE): `http://localhost:8095/aidiy_desktop_capture/sse`
- Backend MCP SQLite (SSE):          `http://localhost:8095/aidiy_sqlite/sse`
- Backend MCP PostgreSQL (SSE):      `http://localhost:8095/aidiy_postgres/sse`
- Backend MCP Logs (SSE):            `http://localhost:8095/aidiy_logs/sse`
- Backend MCP Code Check (SSE):      `http://localhost:8095/aidiy_code_check/sse`
- Backend MCP Backup Check (SSE):    `http://localhost:8095/aidiy_backup_check/sse`
- Backend MCP Backup Save (SSE):     `http://localhost:8095/aidiy_backup_save/sse`

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
