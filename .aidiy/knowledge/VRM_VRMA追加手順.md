# VRM・VRMA 追加手順

## このメモを使う場面
- アバターに新しい VRM モデルを追加したい
- 新しいモーション（VRMA）を追加したい
- モデルやモーション一覧をフロントから切り替えたい

## 関連ファイル
- `frontend_avatar/public/vrm/` — VRM モデル格納フォルダ
- `frontend_avatar/public/vrma/` — VRMA モーション格納フォルダ（`サンプル/`・`標準/` サブフォルダ）
- `frontend_avatar/src/api/config.ts` — `DEFAULT_VRM_MODEL_URL`, `SAMPLE_VRMA_FILES`, `STANDARD_VRMA_FILES`
- `frontend_avatar/src/components/AIコア_アバター.vue` — Three.js + @pixiv/three-vrm 実装
- `frontend_avatar/electron/main.ts` — `desktop:list-vrma-files` IPC（ローカルファイル一覧）

## 実装の結論

- VRM モデルは `frontend_avatar/public/vrm/`、VRMA モーションは `frontend_avatar/public/vrma/` 配下へ置く
- Web モードでは `config.ts` の一覧がフォールバックになるため、追加したファイル名を設定へ反映する
- Electron モードでは `desktop:list-vrma-files` IPC がローカルファイル一覧を優先する
- モーションは `finished` イベントで次の VRMA を選び直す巡回再生方式のため、単一クリップの `LoopRepeat` 前提で調整しない

### config.ts の定数（現行値）

```typescript
// frontend_avatar/src/api/config.ts
export const DEFAULT_VRM_MODEL_URL = '/vrm/AiDiy_Sample_M.vrm'
export const SAMPLE_VRMA_FOLDER_NAME = 'サンプル'
export const STANDARD_VRMA_FOLDER_NAME = '標準'

export const SAMPLE_VRMA_FILES = [
  '/vrma/サンプル/VRMA_01.vrma',
  // ... VRMA_07.vrma まで 7 ファイル
]
export const STANDARD_VRMA_FILES = [
  '/vrma/標準/VRMA_01.vrma',
  // ... VRMA_05.vrma まで 5 ファイル
]
```

VRMA を追加したら、対応する配列の末尾に追記するだけで Web モードのフォールバックへ反映される。

### VRM モデルを追加する場合

1. `public/vrm/` に `.vrm` ファイルを配置
2. `config.ts` の `DEFAULT_VRM_MODEL_URL` または設定画面のモデル一覧に追加
3. `AIコア_アバター.vue` の初期化処理（`loadVrm()`）が参照する URL を更新

### VRMA モーションを追加する場合

1. `public/vrma/<フォルダ名>/` に `.vrma` ファイルを配置
2. `config.ts` の `SAMPLE_VRMA_FILES` または `STANDARD_VRMA_FILES` 配列に追加
3. Electron モードでは `listVrmaFiles(folderName)` IPC がローカルファイルを優先するため、`config.ts` への追記は Web モードのフォールバックとして機能する

### Electron IPC の戻り値型

`desktop:list-vrma-files` IPC は Electron の `main.ts` に登録されており、サブフォルダごとの `.vrma` ファイル一覧を返す。

```typescript
// ElectronIPC追加手順.md と合わせて 3 点セットで実装済み
const vrmaFiles = await window.desktopApi?.listVrmaFiles(SAMPLE_VRMA_FOLDER_NAME)
// → string[] | undefined（フォルダが存在しない場合は空配列）
```

Electron 側で `public/` 相当のパスを使って実ファイルを列挙するため、`config.ts` に未記載のファイルも取得できる。

### モーション連続再生の仕組み

`AIコア_アバター.vue` の `モーション終了時処理` が `finished` イベントで次のモーションを選択・再生する。  
詳細は `アバター表示とVRMA.md` の「アニメーションの連続再生（ループ）」を参照。

## 確認方法

- `npm run dev` で Electron を起動し、アバターウィンドウでモーションが再生されることを確認
- Electron の DevTools Console でエラーが出ていないことを確認
