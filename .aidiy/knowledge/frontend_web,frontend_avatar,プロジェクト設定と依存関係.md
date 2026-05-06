# プロジェクト設定と依存関係

> 文書: `frontend_web,frontend_avatar,プロジェクト設定と依存関係.md` | 実装: `frontend_web/package.json`, `frontend_avatar/package.json`, `frontend_web/tsconfig.json`, `frontend_avatar/tsconfig.json`, `frontend_web/vite.config.ts`, `frontend_avatar/vite.config.ts`

## このメモを使う場面

- npm パッケージを追加・アップデートするとき
- TypeScript のコンパイラオプションを変更するとき
- Vite の設定を変更するとき
- 両プロジェクトの設定差異を確認するとき

## 共通依存パッケージ（バージョン同期必須）

以下のパッケージは両プロジェクトに共通です。バージョンを揃えないと型チェックやビルド結果に差が出ます。

### 本番依存

| パッケージ | frontend_web | frontend_avatar | 備考 |
|-----------|-------------|-----------------|------|
| `vue` | ^3.5.24 | ^3.5.24 | 同期済み |
| `axios` | ^1.13.2 | ^1.13.1 | ずれている。合わせること |
| `monaco-editor` | ^0.55.1 | ^0.55.1 | 同期済み |

### 開発依存

| パッケージ | frontend_web | frontend_avatar | 備考 |
|-----------|-------------|-----------------|------|
| `vite` | ^7.2.4 | ^7.2.4 | 同期済み |
| `vue-tsc` | ^3.2.2 | ^3.2.2 | 同期済み |
| `typescript` | ^5.9.3 | ^5.9.3 | 同期済み |
| `@vitejs/plugin-vue` | ^6.0.1 | ^6.0.1 | 同期済み |
| `@vue/tsconfig` | ^0.8.1 | ^0.8.1 | 同期済み |
| `@types/node` | ^25.0.9 | ^25.0.9 | 同期済み |

### バージョン同期ルール

1. 共通パッケージのバージョンを片方だけで上げない。
2. アップデート時は両方の `package.json` を同時に修正する。
3. `npm install` 後に両方で `npm run type-check` が通ることを確認する。

### 各プロジェクト固有の依存

| パッケージ | 在籍プロジェクト | 用途 |
|-----------|----------------|------|
| `pinia` | web | 状態管理 |
| `vue-router` | web | ルーティング |
| `dayjs` | web | 日付処理 |
| `jquery` | web | DOM操作（CDN等でも可） |
| `qrcode` | web | QRコード表示 |
| `@guolao/vue-monaco-editor` | web | Monaco Editor Vue ラッパー |
| `three` | avatar | 3Dレンダリング |
| `@pixiv/three-vrm` | avatar | VRMモデル読み込み |
| `@pixiv/three-vrm-animation` | avatar | VRMAモーション再生 |
| `electron` (dev) | avatar | Electron |
| `concurrently` (dev) | avatar | 並列起動 |
| `cross-env` (dev) | avatar | 環境変数 |

## TypeScript 設定の差異

| 項目 | frontend_web | frontend_avatar | 影響 |
|------|-------------|-----------------|------|
| strict | false | true | avatar の型定義を web に持ち込むと型エラーになる可能性 |
| strictNullChecks | false | true (strict に内包) | null 安全の有無 |
| noImplicitAny | false | true (strict に内包) | any 暗黙利用の可否 |
| allowJs | true | false | avatar は .js ファイルを受け付けない |
| jsx | preserve | preserve | 差異なし |

### strict 差異による注意点

frontend_avatar の型を frontend_web で使うとき:

- `null` 許容型が web 側でエラーにならないよう `useNullable` などを検討する
- 逆に web から avatar へ型を持ち込む場合は `strictNullChecks` の有無を意識する
- 両プロジェクトで共有する型（`ModelSettings`, `AuthUser` など）は avatar の strict 設定で通るよう定義する

## Vite 設定の差異

| 項目 | frontend_web | frontend_avatar |
|------|-------------|-----------------|
| port | 8090 | 8099 |
| host | 未指定（localhost） | 127.0.0.1 |
| strictPort | 未指定（false） | true |
| proxy (/core) | 8091 ws:true | 8091 ws:true（同一） |
| proxy (/apps) | 8092 ws:true | 8092 ws:true（同一） |
| optimizeDeps.include | monaco-editor | monaco-editor, three, @pixiv/three-vrm, @pixiv/three-vrm-animation |
| resolve.alias | @ → ./src | @ → ./src（同一） |

### Vite proxy 変更時の手順

詳細は `frontend_web,frontend_avatar,backend_server,Viteプロキシ設定.md` を参照してください。

### 各プロジェクトの tsconfig 継承

両方とも `@vue/tsconfig/tsconfig.dom.json` を extends しています。このベース設定のアップデートも両方へ同時適用します。

## npm scripts 命名規則

| スクリプト | frontend_web | frontend_avatar |
|-----------|-------------|-----------------|
| dev | vite | concurrently で renderer + electron 並列起動 |
| build | type-check + vite build | renderer build + electron build |
| type-check | vue-tsc --noEmit | vue-tsc + tsc (electron) |
| preview | vite preview | vite preview |

新規スクリプトを追加するときは、同じ意味のものは同じ名前で揃えてください。avatar 独自の electron 関連スクリプトは役割が分かる名前（`dev:electron`, `dev:renderer` など）を付けます。
