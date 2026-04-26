# Electron IPC 追加手順

## このメモを使う場面
- Renderer（Vue）から OS 機能（ファイル操作・ウィンドウ制御・システム情報など）を呼び出したい
- Electron main process の新しい機能を renderer に公開したい

## 関連ファイル
- `frontend_avatar/electron/main.ts` — `ipcMain.handle()` でハンドラー登録
- `frontend_avatar/electron/preload.ts` — `contextBridge.exposeInMainWorld()` で API 公開
- `frontend_avatar/src/env.d.ts` — `window.desktopApi` の型宣言

## 実装の結論（3 点セット）

### 1. main.ts でハンドラー登録

```typescript
// electron/main.ts
import { ipcMain } from 'electron'

ipcMain.handle('my-feature:do-something', async (event, arg1: string, arg2?: number) => {
  // OS 機能や BrowserWindow 操作
  return { result: 'OK', value: 42 }
})
```

### 2. preload.ts で renderer に公開

```typescript
// electron/preload.ts
import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('desktopApi', {
  // ...既存 API...
  doSomething: (arg1: string, arg2?: number) =>
    ipcRenderer.invoke('my-feature:do-something', arg1, arg2),
})
```

### 3. env.d.ts で型宣言

```typescript
// src/env.d.ts
declare global {
  interface Window {
    desktopApi?: {
      // ...既存型...
      doSomething?: (arg1: string, arg2?: number) => Promise<{ result: string; value: number }>
    }
  }
}
```

### Renderer（Vue）からの呼び出し

```typescript
// 必ず optional chaining で呼ぶ（Web モードでは undefined）
const result = await window.desktopApi?.doSomething('hello', 3)
if (result) {
  console.log(result.value)
}
```

## Electron / Web デュアルモードでの判断基準

IPC は Electron 専用機能なので、Web モードでも同じ画面が壊れないように代替経路を必ず決める。

| 目的 | Electron | Web |
|------|----------|-----|
| ウィンドウ role 取得 | `window.desktopApi.getWindowRole()` | `?role=` クエリまたは既定値 |
| パネル表示切替 | `panel:toggle` / `panel:apply-states` | `AiDiy.vue` の `アクティブタブ` 切替 |
| 認証 Storage | `localStorage` | `sessionStorage` |
| VRMA ファイル一覧 | `desktop:list-vrma-files` | `config.ts` の `SAMPLE_VRMA_FILES` / `STANDARD_VRMA_FILES` |
| OS カーソル位置 | `window:get-pointer-snapshot` | DOM の `pointermove` |
| CPU 使用率 | `system:get-cpu-usage` | 取得不可。0 扱いまたは UI 非表示 |

Renderer から IPC を呼ぶ場合は、必ず `window.desktopApi?.xxx` で呼び、戻り値がない場合の Web フォールバックを同じ関数内で処理する。

## 既存 role / panel へ影響する IPC を追加する場合

ウィンドウやパネルに関わる IPC は、単独で main/preload/env.d.ts を追加するだけでは不十分。次の連動を確認する。

- `electron/main.ts`: `WindowRole` / `PanelKey` / `panelStates` / `panelWindows` / `windowRoles`
- `electron/preload.ts`: renderer に公開する関数名と戻り値型
- `frontend_avatar/src/env.d.ts`: `Window.desktopApi` の型
- `frontend_avatar/src/AiDiy.vue`: `PANEL_KEYS`、`フォールバックロール解決()`、BroadcastChannel snapshot、Web モードのタブ切替
- `frontend_avatar/src/components/AIコア.vue`: core ウィンドウ上のトグルボタンや表示選択

`settings` のような panel ではない専用ウィンドウを追加する場合は、`PanelKey` に混ぜず `WindowRole` だけへ追加する。パネル表示状態と混ぜると `panelStates` 同期や Web タブ表示の意味が崩れる。

## イベント（一方向通知）が必要な場合

Main → Renderer への通知は `webContents.send()` + `ipcRenderer.on()` を使う。

```typescript
// main.ts（送信側）
mainWindow.webContents.send('my-event:notify', { message: 'hello' })

// preload.ts（ブリッジ）
onMyEvent: (callback: (data: { message: string }) => void) => {
  const handler = (_event: IpcRendererEvent, data: { message: string }) => callback(data)
  ipcRenderer.on('my-event:notify', handler)
  return () => ipcRenderer.removeListener('my-event:notify', handler)  // 解除関数を返す
}

// Vue コンポーネント（受信側）
onMounted(() => {
  const off = window.desktopApi?.onMyEvent?.((data) => { /* ... */ })
  onBeforeUnmount(() => off?.())
})
```

イベント購読 API は、preload 側で解除関数を返す形に統一する。Vue 側では `onBeforeUnmount` で必ず解除し、Electron の複数ウィンドウを開閉したときに同じハンドラーが増殖しないようにする。

## 再発しやすい注意点

- **3 ファイルをセットで更新しないと必ずエラーになる**: main.ts / preload.ts / env.d.ts
- `window.desktopApi?.xxx` の optional chaining は必須（Web モードでは `desktopApi` が undefined）
- IPC を追加しただけで Web モードに同等機能があるとは限らない。Web 側は「非表示」「0 扱い」「DOM イベントで代替」などを明示する
- `settings` のような一時ウィンドウは `show()` / `hide()` と sessionId 引き渡しのタイミングを確認する
- `BrowserWindow` 操作は renderer から直接行わず、main process の handler に閉じ込める
- IPC チャンネル名は `namespace:action` 形式で統一（`window:`, `panel:`, `system:`, `desktop:` など）
- `ipcMain.handle` は非同期（`async`）で書く — 同期版の `ipcMain.handleOnce` は使わない
- 既存チャンネル名と被らないよう `electron/main.ts` で一覧を確認してから追加する
- セキュリティ: preload で `ipcRenderer` をそのまま expose しない — 必ずラップ関数を使う

## 現在実装済みのチャンネル一覧

`frontend_avatar/AGENTS.md` の「現在実装済みの IPC ハンドラー一覧」を参照。

## 確認方法

`npm run type-check` でエラーがなければ 3 点セットが揃っている。  
Electron を起動して DevTools で `window.desktopApi` を確認すると公開 API が表示される。
