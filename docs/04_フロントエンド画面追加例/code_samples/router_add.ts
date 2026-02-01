// router/index.ts に追加するルート定義

// C新テーブル（C系の場合）
{
  path: '/C管理/C新テーブル/一覧',
  name: 'C新テーブル一覧',
  component: () => import('../components/C管理/C新テーブル/C新テーブル一覧.vue'),
  meta: { requiresAuth: true, title: 'C新テーブル一覧' }
},
{
  path: '/C管理/C新テーブル/編集',
  name: 'C新テーブル編集',
  component: () => import('../components/C管理/C新テーブル/C新テーブル編集.vue'),
  meta: { requiresAuth: true, title: 'C新テーブル編集' }
},

// M系の場合は /Mマスタ/M新テーブル/一覧
// T系の場合は /Tトラン/T新テーブル/一覧
// V系の場合は /Vビュー/V新ビュー/一覧（一覧のみ）

// ルート定義のポイント:
// - Lazy loading: () => import(...) で必要な時だけ読み込み
// - meta.requiresAuth: true で認証必須
// - meta.title: ページタイトル
