# frontend_avatar

`frontend_avatar` は、**Electron デスクトップアプリ** と **通常ブラウザ** の両方で動く AI コア専用クライアントです。

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
