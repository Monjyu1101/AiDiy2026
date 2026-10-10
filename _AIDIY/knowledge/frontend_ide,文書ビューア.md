# 文書ビューア

> 文書: `frontend_ide,文書ビューア.md` | 実装: `frontend_ide/viewer/server.mjs`, `frontend_ide/viewer/web/app.js`, `frontend_ide/viewer/web/office.js`, `frontend_ide/viewer/checks/office.test.mjs`

## このメモを使う場面

- AiDiy IDE の Word・Excel・PowerPoint・PDF 表示を変更・確認する。
- Office文書がバイナリ扱いになる、ライブラリ不足、表示崩れを調べる。

## 構成と依存

VS Code の Office Viewer（cweijan/vscode-office）で採用・紹介されているライブラリを、読み取り専用の独立した画面に組み込む。拡張そのものや VS Code の API は使用しない。

| 対象 | ライブラリ | 対応形式 |
|---|---|---|
| Word | docx-preview / JSZip | docx、dotx |
| Excel | SheetJS CE | xlsx、xls、xlsm、ods、csv、tsv |
| PowerPoint | PptxViewJS / JSZip / Chart.js | pptx、pptm |
| PDF | PDF.js | pdf |

- 依存は `frontend_ide/viewer/package.json` / `package-lock.json` で管理し、他サブシステムから借りない。ライセンスは各パッケージの同梱ファイルに従う。docx-preview / SheetJS / PDF.js は Apache-2.0、PptxViewJS / Chart.js は MIT、JSZip は MIT または GPL-3.0 の選択で MIT を利用する。
- SheetJS は公式配布元 `https://cdn.sheetjs.com/xlsx-0.20.3/xlsx-0.20.3.tgz` を固定する。npm registry の `xlsx` は旧版のため置き換えない。
- `/api/file` が `kind: office` と `format` を返し、`app.js` が `/office.html` の iframe を右側に作る。
- `/api/document` は対象拡張子のみをバイナリ配信する。既存の `/api/raw` は画像専用のままにする。
- `/office-vendor/` は必要なファイルだけを配信する。Monaco の AMD ローダーとの干渉を避けるため、表示ライブラリを親画面へロードしない。
- iframe 内の CSP で外部接続を制限し、変換サーバーを使わずブラウザ内で処理する。書き込み・マクロ実行は提供しない。Word の埋め込み HTML（altChunk）は描画しない。
- 閉じる・別ファイル選択で iframe を破棄する。`fileToken` はフォルダ選択・閉じる場合も進め、以前の読み込み結果が新しい画面を上書きしないようにする。

## 導入と検証

### 著作権表記の更新

- 独自実装のソース冒頭には、既存ソースと同じ `COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.` から始まる定型文を付ける（AiDiy 公開利用ライセンス v1.1、商用利用の事前書面承諾、LICENSE 参照、GitHub URL を含む）。第三者ライブラリの原文には適用しない。
- `scripts/licenses.mjs` はルート `LICENSE` を正本として `frontend_ide/viewer/LICENSE` と `web/LICENSE.txt` に全文を同梱し、著作権ページの「AiDiy IDE の独自実装」に定型文と全文を表示する。単独配布時は同梱 `LICENSE` を利用する。

- `scripts/licenses.mjs` は導入済みのブラウザ用依存と `package-lock.json` のバージョンを照合し、同梱の LICENSE / NOTICE / ThirdPartyNotices などを原文のまま収集する。PDF用フォント・WASMの表記も対象。Node.js専用の任意依存 `@napi-rs/canvas` はブラウザへ配信しないため、この一覧の対象外。
- `npm ci` / `npm install` の `postinstall`、または `npm run licenses` で `web/THIRD_PARTY_NOTICES.txt` と `web/licenses.html` を生成する。両方をソース・配布物に含め、ライブラリ内の既存の著作権表記も残す。
- `npm run check` は表記の更新漏れも検出する。ライセンス原文が見つからない新規依存では生成を停止するので、配布元の原文を確認して収集方法を追加する。
- 画面左上の「著作権・ライセンス」から別タブで開く。項目の展開と原文テキスト保存を確認する。
- JSZip は MIT、DOMPurify は Apache-2.0 を選択する。選択元の複数ライセンス原文も保存する。Office Viewer は参考元として作者・リンクを掲載し、拡張本体のコードを組み込んだとは表記しない。

### 動作確認

1. `python frontend_ide/viewer/_setup.py` で依存を導入する（Node.js 22.13 以降）。
2. サーバー側も変更した場合は AiDiy IDE のサーバーを再起動する。画面の再読み込みだけでは `server.mjs` の変更は反映されない。
3. `frontend_ide/viewer` で `npm run check` と `npm test` を実行する。
4. ブラウザで Word の日本語・ページ区切り、Excel のシート切り替え・数式結果・結合セル・行送り、PowerPoint / PDF のページ送りと倍率変更を確認する。
5. 文書 → ソースコード → 文書、ビューアを閉じる、壊れた文書のエラー表示を確認する。

`checks/fixtures.mjs` の `createFixtures(root)` で、指定した一時ディレクトリに Word / Excel / PDF / CSV / 壊れた文書 / コードの検証用ファイルを生成できる。PowerPoint は既存の `AiDiy概要.pptx` などを読み取り用の一時フォルダへコピーして使用する。原本は更新しない。

## 制限と切り分け

- 文書は50MBまで。Excel は最大100,000行、先頭100列、1画面200行を表示する。大きいシートでは省略を画面に表示する。
- Excel の数式を再計算しない。ファイルに保存された計算結果を表示する。グラフ・画像・高度な書式の再現は対象外。
- Word / PowerPoint はブラウザ用描画エンジンによる近似表示。フォント・複雑なレイアウト・図形などでOfficeアプリとの差が出る場合がある。
- `.doc` / `.ppt` の旧形式とパスワード付き文書は対象外。PDF はページ単位のCanvas描画で、文字検索・文字選択は提供しない。
- 依存不足ならセットアップを再実行する。文書が従来どおりバイナリ扱いなら、旧サーバーが動いていないか確認する。
- 表示サイズ変更は描画を直列化して処理する。拡大時は canvas の左端にもスクロールできる配置を維持する。
