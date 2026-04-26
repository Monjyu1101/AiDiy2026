# frontend_web 画面追加手順

## 参照する場面
- Vue 3 で新しい業務画面（一覧＋編集）を追加したい
- メニューに新しい項目を追加したい

## 関連ファイル
- `frontend_web/src/router/index.ts` — ベースルート、認証ガード、X系ルート
- `frontend_web/src/router/coreRouter.ts` — C系/AiDiy ルート
- `frontend_web/src/router/appsRouter.ts` — M系/T系/V系/S系 ルート
- `frontend_web/src/components/<カテゴリ>/` — 画面コンポーネント
- `frontend_web/src/api/client.ts` — Axios クライアント、JWT 付与、認証延長
- `frontend_web/src/types/` — エンティティ/API/qTubler 型
- メニューコンポーネント — カテゴリ別の `.vue` ファイル

## 追加する主なファイル

- [ ] `src/components/<カテゴリ>/<テーブル名>/一覧.vue` — 一覧画面
- [ ] `src/components/<カテゴリ>/<テーブル名>/編集.vue` — 作成・編集画面
- [ ] `src/components/<カテゴリ>/<テーブル名>/components/<テーブル名>一覧テーブル.vue` — `qTublerFrame` ラッパー
- [ ] `src/types/entities.ts` など — 必要なら表示行・フォーム用の型を追加
- [ ] `src/router/coreRouter.ts` / `appsRouter.ts` / `index.ts` — 系統に応じてルート追加
- [ ] メニュー `.vue` — リンク追加

## ルート追加先の判断

| 系統 | 追加先 | パス例 |
|------|--------|--------|
| C系 / AiDiy | `src/router/coreRouter.ts` | `/C管理/C利用者/一覧`, `/AiDiy` |
| M系 / T系 / V系 / S系 | `src/router/appsRouter.ts` | `/Mマスタ/M商品/一覧`, `/Tトラン/T配車/編集` |
| X系 / ログイン / リンク / ベースメニュー | `src/router/index.ts` の `baseRoutes` | `/Xその他/Xテトリス/ゲーム` |

編集画面の主キーはパスパラメータではなく、既存画面に合わせてクエリで渡す。

```typescript
router.push({
  path: '/Mマスタ/M商品/編集',
  query: { モード: '編集', 商品ID: row.商品ID, 戻URL: '/Mマスタ/M商品/一覧' }
})
```

ルート定義には `name` と `meta.requiresAuth: true` と `meta.title` を入れる。日本語URLは `router/index.ts` の `decodeURIComponent` 処理でリロード対応済みなので、個別画面で再実装しない。

## 実装時の判断

- 一覧表示は V系 JOIN API を使い、登録・更新・削除は M/T系 API を使う。
- C/M/T/V 操作系 API の認証延長は `frontend_web/src/api/client.ts` の Axios インターセプターに合わせる。手動延長が必要なケースは既存画面を確認する。
- ファイル名は日本語でよい。テンプレート内で日本語コンポーネントタグを直接使う場合は問題が出やすいため、動的表示は `<component :is="...">` を使う。
- API 呼び出しは専用ラッパーファイルを増やすより、既存CRUD画面と同じく `apiClient.post('/apps/...', payload)` / `apiClient.post('/core/...', payload)` を画面側で使う実装が多い。新規 `Api.ts` を作る場合は既存パターンと整合させる。
- API レスポンスは `status === 'OK'` を確認し、`data.items` / `data.total` の有無に対応する。古いAPIや静的配列形式では `Array.isArray(data)` の分岐を入れる。
- 検索・フィルタ・ソート・ページングは、サーバー再取得ではなく、取得済み配列に対してフロント側で `filteredRows` → `sortedRows` → `pagedRows` の順に `computed` を組む既存実装が標準。
- 明細型画面では、フォーム上の表示専用計算値やバックエンドスキーマに存在しない項目を payload に含めない。

## 画面の UI ルール（厳守）

| 項目 | ルール |
|------|--------|
| 数値入力 | 非フォーカス時は3桁区切り表示、フォーカス時はカンマ除去＋全選択 |
| 日付・日時 | センタリング表示 |
| ラベル幅 | `160px`（またはその倍数）で統一 |
| ID 選択肢 | `ID : 名称` 形式 |
| ダイアログ | `qAlert(message)` / `qConfirm(message)` — Promise-based グローバル関数 |
| テーブル | `qTublerFrame.vue` を使う（`qTubler.vue` は存在しない） |
| 外部UI | Vuetify / Element Plus / Quasar などは使わず、既存CSSと共有コンポーネントで作る |
| コンポーネントタグ | 日本語タグを直接書かず、lazy import または `<component :is="...">` を使う |

## qTublerFrame の使い方

```vue
<qTublerFrame
  :columns="columns"
  :rows="pagedRows"
  :rowKey="rowKey"
  :sortKey="sortKey"
  :sortOrder="sortOrder"
  :message="message"
  :messageType="messageType"
  :hasFilter="hasFilter"
  :totalCount="totalCount"
  :totalAll="totalAll"
  :currentPage="currentPage"
  :totalPages="totalPages"
  @sort="handleSort"
  @page="goToPage"
>
  <template #filter="{ column }">
    <input v-if="filters[column.key] !== undefined" v-model="filters[column.key]" class="filter-input" type="text" />
  </template>
  <template #cell="{ row, column, value }">
    <a v-if="column.key === rowKey" href="#" class="id-link" @click.prevent="openDetail(row)">{{ value ?? '' }}</a>
    <template v-else>{{ value ?? '' }}</template>
  </template>
</qTublerFrame>
```

`qTublerFrame` は表の枠・ヘッダー・スロット・ページャを提供するだけで、並び替え、フィルタ、ページ切替後の配列作成は呼び出し側で行う。`headers/items/selectedId/row-click` ではなく、現行実装は `columns/rows/rowKey/sort/page` を使う。

`Column` は `src/types/qTubler.ts` の `key`, `label`, `width`, `align`, `sortable`。幅は固定値を入れ、数値や日付は `align: 'right'` / `'center'` を明示する。リンク・チェックボックス・ボタン表示は `#cell` スロットで分岐する。

## 一覧画面の標準構成

- 親の `一覧.vue` は検索条件、件数制限、無効も表示、新規ボタン、一覧テーブルの配置を担当する。
- 子の `一覧テーブル.vue` は API 取得、ローカルフィルタ、ソート、ページング、行リンク遷移を担当する既存画面が多い。
- 子コンポーネントを親から再検索したい場合は、子で `defineExpose({ loadData })` し、親が `ref` 経由で呼ぶ。
- `戻URL` を編集画面へ渡す場合は、クエリ値に全角の `？＆＝` が混ざる可能性を考慮し、戻る前に半角へ正規化する既存X系/一覧系の処理を流用する。

## 編集画面の標準構成

- `route.query.モード` が `新規` か `編集` かで初期処理を切り替える。
- 編集時は主キーを `route.query.<ID名>` から取得し、`/取得` API でフォームに反映する。
- 保存時は `登録` / `変更` を明示的に分ける。削除は `qConfirm` 後に `/削除` を呼ぶ。
- 数値入力は内部値をカンマなし文字列で保持し、表示時だけカンマ整形する。空欄を `0` にしない。
- プルダウンのラベルは `商品ID` ではなく `商品` など業務名にし、選択肢表示は `ID : 名称` にする。

## 再発しやすい注意点

- 系統に合う router ファイルへルートを追加しないと `<router-link>` が 404 になる
- メニューカード追加だけでは画面に遷移できない。router、カテゴリメニュー、必要ならトップ/メインメニューの3点を確認する
- 外部 UI フレームワーク（Vuetify / Element Plus 等）は**使わない** — カスタム CSS + 独自コンポーネントで実装
- TypeScript の strict mode は無効（`strictNullChecks: false`）なので型エラーが出にくいが、`npm run type-check` は必ず実行すること
- `npm run build` は `dist` を生成するため、ユーザーの明示指示がない限り実行しない。通常確認は `npm run type-check` と Vite dev server で足りる
- API URL は `baseURL: '/'` と Vite Proxy 前提。`http://127.0.0.1:8091` を画面に直書きしない

## 確認方法

1. `npm run dev` でブラウザを開き、追加したルートへ直接アクセス
2. 一覧表示 → 編集 → 保存 → 一覧に戻る の動線を確認
3. `npm run type-check` で型エラーがないことを確認
4. DevTools Network で `/core` / `/apps` の呼び先、payload、`status/message/data` を確認
5. 日本語URLをブラウザでリロードし、ログイン済みなら同じ画面に復帰することを確認
