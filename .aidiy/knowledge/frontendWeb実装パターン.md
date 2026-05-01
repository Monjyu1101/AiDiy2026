# frontend_web 実装パターン

## このメモを使う場面

- `frontend_web` の画面、router、store、API client、qTubler の責務を確認する。
- 業務 CRUD 画面や V系一覧を既存 UI に合わせて実装する。
- 明細型編集画面、入力欄、検索欄、認証、エラー処理の既存パターンへ合わせる。

## 関連ファイル

- `frontend_web/src/main.ts`
- `frontend_web/src/App.vue`
- `frontend_web/src/router/`
- `frontend_web/src/stores/auth.ts`
- `frontend_web/src/api/client.ts`
- `frontend_web/src/components/`
- `frontend_web/src/components/_share/qTublerFrame.vue`
- `frontend_web/src/utils/qAlert.ts`
- `frontend_web/src/types/qTubler.ts`

## 基本方針

- Vue 3 Composition API と `<script setup lang="ts">` を使う。
- Vue Router と Pinia を使う。
- API client の `baseURL` は `/` とし、Vite proxy で `/core` と `/apps` を振り分ける。
- 日本語ファイル名、日本語 import 名は使ってよい。
- template の component tag は ASCII にし、日本語コンポーネントは `<component :is="...">` を使う。

## Router の使い分け

| 対象 | 登録先 |
|------|--------|
| C系 / A系 | `src/router/coreRouter.ts` |
| M系 / T系 / V系 / S系 | `src/router/appsRouter.ts` |
| ベース画面やカテゴリ | `src/router/index.ts` |

新規画面追加の具体手順は `frontendWeb画面追加手順.md` を使う。

## API 呼び出し

```typescript
const response = await apiClient.post('/apps/V商品/一覧', payload)
if (response.data.status === 'OK') {
  const items = response.data.data.items
  const total = response.data.data.total
}
```

- API キー名は backend と同じ日本語名へ寄せる。
- C/M/T 操作系 API はトークン延長対象。詳細は `認証延長ルール.md` を確認する。
- 401 は `client.ts` の interceptor でログアウト処理へ流れる。

## qTubler

qTubler は一覧画面の標準テーブル。

- `columns` は `types/qTubler.ts` の型に合わせる。
- `rows`、`rowKey`、`totalCount`、`totalAll`、`currentPage`、`totalPages`、`sortKey`、`sortOrder` を渡す。
- sort / page イベントで再取得する。
- V系一覧では `items` と `total` を backend のレスポンスから受け取る。

詳細は `frontendWeb画面追加手順.md` の qTubler 節を使う。

## 共通ダイアログ

```typescript
import { qAlert, qConfirm } from '@/utils/qAlert'
```

- 保存完了やエラーは `qAlert()`。
- 削除確認は `qConfirm()`。
- browser 標準 `alert()` / `confirm()` を増やさない。

## UI 統一ルール

- 数値入力欄は内部値をカンマなし文字列で持ち、非フォーカス時だけ 3桁区切り表示へ戻す。
- 数値欄はフォーカス時にカンマを外し、全選択して上書き入力しやすくする。
- 日付欄・日時欄は原則センタリング表示。
- ラベル幅は `160px` を基準にし、入力欄は `160px` / `320px` など倍数で揃える。
- 単位付き入力は「入力欄 + 単位」の合計幅で基準幅へ揃える。
- ID 選択欄のラベルは `商品`、`車両` など業務名にし、選択肢は `ID : 名称` 形式にする。
- 検索欄も編集画面と同じラベル幅・入力幅へ揃える。

## 明細型編集画面

明細型マスタや明細型トランザクションの編集画面では、ヘッダー form と `明細一覧` 配列を分ける。

実装パターン:

1. 明細行の Form 型を定義する。
2. 数値欄は空欄を扱えるよう string で保持する。
3. 行追加時は空行を push する。
4. 行削除時は `明細SEQ` を 1 から再採番する。
5. 送信前に空行除去、trim、数値変換を行う。
6. 表示専用の計算値は payload に含めない。
7. backend schema にない項目を送らない。

代表実装:

- `frontend_web/src/components/Mマスタ/M商品構成/M商品構成編集.vue`
- `frontend_web/src/components/Tトラン/T生産/T生産編集.vue`

## 認証

- token は `localStorage` の `token` キー。
- user は `localStorage` の `user` キー。
- ログイン成功時は backend の `初期ページ` を優先し、未設定なら既定ページへ遷移する。
- 権限IDは文字列として扱う。`'1'` のように比較する。

詳細は `JWT認証フロー.md` を使う。

## よくある落とし穴

- `<C利用者一覧 />` のような日本語タグを書くとブラウザで無効扱いになる。
- 権限IDを数値で比較して条件が通らない。
- `npm run build` を明示指示なしに実行して `dist/` を生成する。
- Vite proxy を使わず `http://localhost:8091` へ直叩きして CORS 条件が変わる。
- backend schema に存在しない表示専用項目を payload に入れる。
- 検索欄や編集欄の幅が画面ごとにばらつく。

## 最小確認

- `npm run type-check` が通る。
- 画面遷移できる。
- 一覧取得、ページング、ソートが通る。
- 登録 / 変更 / 削除後に一覧へ戻り、再取得で反映される。
- DevTools Console に Vue warning / JS error がない。
- Network で 401 / 403 / 500 が出ていない。
