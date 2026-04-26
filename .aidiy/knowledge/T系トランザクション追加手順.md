# T系トランザクション追加手順

## このメモを使う場面
- T配車・T生産のような業務トランザクションテーブルを新たに追加したい
- 明細型（ヘッダー行＋明細行を単一テーブルで管理）のパターンも含む

## 関連ファイル
- M系追加と共通: `apps_models/__init__.py`, `apps_crud/__init__.py`, `apps_main.py`, `apps_crud/init.py`
- T系固有: `apps_router/T*.py`, `apps_router/V*.py`（T系一覧表示用の V系も必要）

## 実装手順

### Backend

- [ ] `apps_models/T<名称>.py` — SQLAlchemy Model 作成
- [ ] `apps_models/__init__.py` — `from apps_models.T<名称> import *` 追加（テーブル生成に必須）
- [ ] `apps_crud/T<名称>.py` — CRUD 関数作成
- [ ] **`apps_crud/__init__.py` — CRUD 関数を import して `__all__` に追加（最も忘れやすい）**
- [ ] `apps_router/T<名称>.py` — Router 作成（POST のみ）
- [ ] `apps_router/V<名称>.py` — 一覧表示用 V系 Router 作成（JOIN + 生 SQL）
- [ ] `apps_main.py` — 両 Router を `include_router` で登録
- [ ] `apps_crud/init.py` — 初期データが必要なら `init_db_data()` に追記
- [ ] `apps_crud/init.py` — カラム追加があれば `apply_schema_migrations()` に追記
- [ ] `C採番` テーブルに新テーブルのエントリを追加（初期データとして）

### Frontend（frontend_web）

- [ ] `src/types/<名称>型.ts` — TypeScript 型定義
- [ ] `src/api/<名称>Api.ts` — API 呼び出し関数
- [ ] `src/components/T<カテゴリ>/<テーブル名>/一覧.vue` — 一覧画面
- [ ] `src/components/T<カテゴリ>/<テーブル名>/編集.vue` — 編集画面
- [ ] `src/components/T<カテゴリ>/<テーブル名>/components/一覧テーブル.vue` — qTublerFrame ラッパー
- [ ] `src/router/index.ts` — ルート追加
- [ ] メニューコンポーネントへのリンク追加

## 明細型パターン（ヘッダー+明細を単一テーブルで管理）

T生産・M商品構成が参考実装。

```python
# 明細SEQ=0: ヘッダー行、明細SEQ>=1: 明細行
class T生産(Base):
    __tablename__ = "T生産"
    生産ID    = Column(String, primary_key=True)
    明細SEQ   = Column(Integer, primary_key=True)  # 0=ヘッダ
    生産日付  = Column(String)  # ヘッダ項目
    商品ID    = Column(String)  # 明細項目（ヘッダ行はNULL）
    数量      = Column(Integer)
    ...監査フィールド...
```

CRUD の方針:
- `get_ヘッダ(db, 生産ID)`: `明細SEQ=0` の1行を取得
- `get_明細一覧(db, 生産ID)`: `明細SEQ>=1` の一覧を取得
- `create/update` は全明細を一括削除→再作成（楽観ロック不要）

## 明細型 CRUD の実装基準

- 主キーは `伝票ID + 明細SEQ` の複合PKにする。
- 登録時はヘッダー行を `明細SEQ=0` として先に作り、明細配列を 1 始まりで追加する。
- 更新時は対象伝票IDの既存行を全削除してから、ヘッダーと明細を再作成する。削除前に存在確認を行い、対象なしなら `NG` を返す。
- 削除は物理削除ではなく `有効=False` を標準にする。ただし既存実装が全行削除方式の場合は、その機能の既存パターンに合わせる。
- V系やスケジューラでヘッダーだけを扱うときは必ず `明細SEQ = 0` を条件に入れる。明細行まで混ざると件数や予定表示が二重になる。
- 明細だけを集計する V 系では `明細SEQ > 0` を条件に入れる。

## T系一覧の件数制限

- T系の一覧エンドポイントは `Optional[schemas.ListRequest] = None` を受け取り、ORM なら `apply_active_filter()`、生SQLなら `append_active_condition()` / `get_limit_clause()` を使う。
- `件数制限` と `無効も表示` を request から受け取れるようにし、レスポンスの `data` には `items` / `total` / `limit` を返す。
- 日付範囲を受ける場合は `開始日付` / `終了日付` を使い、保存値が `YYYY-MM-DD` なら文字列比較でよい。日時文字列の場合は `date(カラム)` を使う。

## 注意点

- **`apps_crud/__init__.py` への登録が最も忘れやすい** — 漏れると `ImportError` でサーバー起動失敗
- T系一覧画面のフロントは M系と同様に V系エンドポイントを使う。T系の直接 `/apps/T*/一覧` は補助用
- 明細型の `create/update` で「明細行だけ更新」は実装しない — 全明細を削除・再作成が標準
- 採番は `C採番` テーブルを経由する（AUTOINCREMENT 禁止）
- 日付は `YYYY-MM-DD` 文字列で保存（SQLite の DATE 型は使わない）

## 確認方法

1. `http://localhost:8092/docs` で POST エンドポイントが表示されることを確認
2. 作成→一覧取得→更新→削除の一通りを Swagger で実行
3. `npm run type-check` でフロント型エラーがないことを確認
