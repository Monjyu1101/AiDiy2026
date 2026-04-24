# X系静的画面追加

## 参照する場面

`frontend_web` の `Xその他` 配下に、ゲーム・デモ・マスコットなどの実験的な静的画面を追加するときに参照する。

## 関連ファイル

- `frontend_web/src/router/index.ts`
- `frontend_web/src/components/Xその他.vue`
- `frontend_web/src/components/Xテスト/<画面名>.vue`
- `frontend_web/public/<画面名>/index.html`
- `frontend_web/public/<画面名>/index.js`
- `frontend_web/public/<画面名>/NOTICE.md`（外部アセットを置く場合）

## 実装の結論

- ゲーム系の X画面は、Vue コンポーネントを薄い iframe ラッパーにして、実体を `frontend_web/public/<画面名>/` 配下の静的HTML/JSへ置く。
- マスコット系のように Vue 画面内で完結できるものは、iframe を使わず `frontend_web/src/components/Xテスト/<画面名>.vue` に直接実装してよい。
- ルートは `frontend_web/src/router/index.ts` の `baseRoutes` に追加する。
- メニュー導線は `frontend_web/src/components/Xその他.vue` のカードへ追加する。
- iframe ラッパーは既存の `Xテトリス.vue` / `Xインベーダー.vue` / `Xリバーシ.vue` と同じ戻URL処理を使う。
- `react-neko` という npm パッケージは 2026-04-23 時点で npm registry に存在しない。近いものとして `neko-ts` があるが `UNLICENSED` なので、このプロジェクトへ依存追加する場合はライセンス確認を優先する。
- `Xネコ` は `oneko.js` 互換の 32px スプライト方式へ変更した。`oneko.gif` は `adryd325/oneko.js` の MIT ライセンス資産なので、`public/Xネコ/NOTICE.md` に出典とライセンスを残す。
- Vue 直実装で確実に表示したい画像は `public` 直参照ではなく `src/assets` へ置いて import する。日本語 `public` パスや base URL の影響を受けにくい。
- `X立体リバーシ` は `frontend_web/public/X立体リバーシ/` に静的 HTML/CSS/JS を置き、`src/components/Xその他/X立体リバーシ.vue` を iframe ラッパーとして追加した。ルートは `/Xその他/X立体リバーシ/ゲーム`、メニュー導線は `Xその他.vue` に追加する。盤は 6面×4x4。現在は 6面ネットを表示せず、Three.js の 3D キューブを直接クリックしてプレイする。
- 6面立方体のように特殊なゲームルールを実装する場合は、ルール説明を画面内に明記し、合法手ハイライト・CPU対戦・終局/特殊モード遷移のログを同時に実装して、単なる盤面だけにしない。
- Three.js を `frontend_web` に依存追加しない静的ページでは、CDN の ES module import を使うと `node --check` は通るが、オフライン環境では 3D 表示だけ失敗する。3D 表示が必須の画面は、可能ならローカル依存化も検討する。

## 注意点

- `public` 配下の日本語ディレクトリは Vite でそのまま配信できるが、ブラウザ確認では URL エンコードされたパスでも取得できることを確認する。
- Vue 側の新規コンポーネントタグは日本語タグで直接書かず、今回のようなルート lazy import なら問題ない。
- X系の静的ページはバックエンドAPIを使わないため、基本確認は `npm run type-check`、必要に応じた `node --check public/<画面名>/index.js`、Vite 経由の HTTP 取得で足りる。
- Vue 直実装の場合は `node --check` 対象がないので、`npm run type-check` を優先する。
- 画面表示が出ない場合は、親レイアウトの高さ継承だけに頼らず、ステージ側に `min-height` を持たせる。
- DevTools MCP が使える場合は、最終的に `http://localhost:8090/<画面名>/index.html` を開いてコンソールエラーと描画を確認する。

## 最低限の確認方法

```powershell
cd frontend_web
npm run type-check
node --check .\public\<画面名>\index.js
Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8090/<URLエンコード済み画面名>/index.html'
```
