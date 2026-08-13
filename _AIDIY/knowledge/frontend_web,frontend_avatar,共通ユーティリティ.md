# 共通ユーティリティ

> 文書: `frontend_web,frontend_avatar,共通ユーティリティ.md` | 実装: `frontend_web/src/utils/monaco.ts`, `frontend_avatar/src/utils/monaco.ts`, `frontend_web/src/utils/qAlert.ts`, `frontend_avatar/src/utils/qAlert.ts`

## このメモを使う場面

- Monaco Editor の Worker 設定や言語推定を変更するとき
- qAlert / qConfirm / qColorPicker ダイアログの動作を変更するとき
- 両プロジェクトで同じ実装がコピーされているユーティリティを修正するとき
- モナコの拡張子マッピングに言語を追加するとき

## Monaco Editor ユーティリティ

両プロジェクトとも `src/utils/monaco.ts` に Monaco Editor の Worker 設定と言語推定関数を持ちます。

### Worker 設定

全く同一の `self.MonacoEnvironment.getWorker()` 設定:

```typescript
self.MonacoEnvironment = {
    getWorker(_, label) {
        if (label === 'json') return new jsonWorker()
        if (label === 'css' || label === 'scss' || label === 'less') return new cssWorker()
        if (label === 'html' || label === 'handlebars' || label === 'razor') return new htmlWorker()
        if (label === 'typescript' || label === 'javascript') return new tsWorker()
        return new editorWorker()
    },
}
```

### 言語推定マップ

両者とも `モナコ言語推定(ファイル名)` 関数で拡張子 → Monaco 言語 ID をマッピングします。

| 拡張子 | Monaco 言語 | 備考 |
|--------|-------------|------|
| py | python | |
| vue | html | 構文ハイライトが十分なため |
| html/htm | html | |
| css/scss/less | css/scss/less | avatar は sass のみなし |
| js/jsx/mjs/cjs | javascript | web は js/jsx のみ |
| ts/tsx/mts | typescript | web は ts/tsx のみ |
| json | json | |
| md | markdown | |
| yml/yaml | yaml | |
| sh/bash | shell | avatar は sh のみ |
| bat/cmd | bat | web は bat のみ |
| ps1 | powershell | |
| sql | sql | |
| xml/svg | xml | |
| ini/env/toml | ini | avatar は ini/env/toml |
| txt/log/csv | plaintext | |
| dockerfile | dockerfile | web のみ（avatar はコード上未登録だが推定関数で特別処理） |

### 差分

| 項目 | frontend_web | frontend_avatar |
|------|-------------|-----------------|
| 変数名 | `拡張子と言語`（日本語） | `EXTENSION_TO_LANGUAGE`（英語） |
| エントリ数 | 多い（sass, mjs, cjs, mts, bash, cfg, conf, dockerfile, makefile, gitignore） | 少ない |
| 関数名 | `モナコ言語推定(ファイル名)` | `モナコ言語推定(fileName)` |
| 引数名 | `ファイル名` | `fileName` |

frontend_web のマップの方が充実しています。avatar にエントリを追加するときは web のマップを参照してください。

### 修正時の注意

**Monaco Worker 設定と拡張子マップは両方の `monaco.ts` を同時に修正してください。** 片方だけ変えると非互換が生じます。理想的には共通パッケージへ抽出すべき領域ですが、現状はコピー状態です。

## ダイアログユーティリティ (qAlert / qConfirm / qColorPicker)

両プロジェクトとも `src/utils/qAlert.ts` にシングルトン形式のダイアログユーティリティを持ちます。

### シングルトンパターン

```typescript
// インスタンス登録（App.vue / AiDiy.vue の onMounted で呼ぶ）
setAlertInstance(alertDialogRef)
setConfirmInstance(confirmDialogRef)
setColorPickerInstance(colorPickerRef)

// 呼び出し
await qAlert('保存しました')
const ok = await qConfirm('削除してよろしいですか？')
const color = await qColorPicker('#ff0000', '色を選択')
```

### 差分

| 項目 | frontend_web | frontend_avatar |
|------|-------------|-----------------|
| qMessage | あり（`setMessageInstance` + `qMessage()`） | なし |
| 型定義インターフェース名 | `AlertDialogInstance`, `ConfirmDialogInstance`, `MessageDialogInstance`, `ColorPickerDialogInstance` | 同左（`MessageDialogInstance` 除く） |
| フォールバック | alert/confirm のブラウザ標準関数 | 同左 |

### 修正時の注意

- **両方の `qAlert.ts` を同時に修正してください。**
- frontend_web の `qMessage()` を frontend_avatar に追加してもよいが、対応する `MessageDialogInstance` コンポーネントも必要です。
- 新しいダイアログ種別を追加する場合は、両プロジェクトでセットで実装します（型定義 + `setXxxInstance` + `qXxx` 関数 + 呼び出し側コンポーネント）。

## コピー状態の同期ルール

`utils/` 以下のファイルは両プロジェクトで実質コピー状態です。以下のルールで運用します:

| 操作 | 手順 |
|------|------|
| バグ修正 | 両方のファイルを同内容に修正する |
| 機能追加 | 両方に追加する（frontend_web 優先で実装し avatar へ移植） |
| リファクタリング | 内容を一致させた上で、共通パッケージ化を検討する |

現状コピー状態のファイル:

| ファイル | 状態 |
|----------|------|
| `utils/monaco.ts` | ほぼ同一（avatar のマップがやや少ない） |
| `utils/qAlert.ts` | ほぼ同一（web に qMessage 追加） |
| `api/websocket.ts` | 同一インターフェース、実装に若干の差異あり |
