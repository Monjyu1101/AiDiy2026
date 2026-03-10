# frontend_avatar

Vue 3 + TypeScript + Vite + Electron のデスクトップアプリ用ベースです。

## 使い方

```powershell
cd frontend_avatar
npm install
npm run dev
```

## 主な構成

- `src/` : Vue レンダラー
- `electron/main.ts` : Electron メインプロセス
- `electron/preload.ts` : preload
- `vite.config.ts` : Vite 設定
- `tsconfig.electron.json` : Electron 側 TypeScript 設定

## ビルド

```powershell
cd frontend_avatar
npm run build
npm run start
```
