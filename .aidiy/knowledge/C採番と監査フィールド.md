# C採番と監査フィールド

## このメモを使う場面
- 新規レコードを登録するときに ID を発番したい
- 登録・更新時に監査フィールド（誰が・いつ・どの端末で）を自動付与したい

## 関連ファイル
- `backend_server/core_crud/utils.py` — `create_audit_fields()` / `update_audit_fields()`
- `backend_server/apps_crud/utils.py` — apps 側の同名関数
- `backend_server/core_router/C採番.py` — 採番 API
- エンドポイント: `POST /core/C採番/採番`

## 実装手順

### C採番の使い方

新規レコード作成前に C採番から ID を取得する。AUTOINCREMENT は使わない。

```python
# CRUD 関数内で採番する場合（同一 DB セッション内）
from core_crud import get_next_id

new_id = get_next_id(db, "テーブル名")
# API 経由で採番する場合（フロントから呼ぶ場合）
# POST /core/C採番/採番  body: {"テーブル名": "M商品"}
```

フロントから呼ぶ場合は、作成 API の前に採番 API を呼び、返ってきた `次ID` を作成リクエストの ID フィールドに渡す。

### 監査フィールドの付与

全テーブルに以下の 8 フィールドが必須：

| フィールド | 付与タイミング |
|-----------|--------------|
| `登録日時` | 登録時のみ |
| `登録利用者ID` | 登録時のみ |
| `登録利用者名` | 登録時のみ |
| `登録端末ID` | 登録時のみ |
| `更新日時` | 登録・更新両方 |
| `更新利用者ID` | 登録・更新両方 |
| `更新利用者名` | 登録・更新両方 |
| `更新端末ID` | 登録・更新両方 |

```python
from apps_crud.utils import create_audit_fields, update_audit_fields

# 登録時（8フィールド全て設定）
audit = create_audit_fields(認証情報)
record = MyModel(**data.dict(), **audit)

# 更新時（更新系4フィールドのみ上書き）
audit = update_audit_fields(認証情報)
for key, value in audit.items():
    setattr(record, key, value)
db.commit()
```

認証情報 dict の必須キー: `利用者ID`, `利用者名`, `端末ID`
未指定 / 初期データ投入時は `'system'` がデフォルトで入る。

### 初期データ投入時

```python
from apps_crud.utils import create_audit_fields
audit = create_audit_fields({"利用者ID": "system", "利用者名": "system", "端末ID": "system"})
record = MyModel(ID="M001", 名称="サンプル", **audit)
db.add(record)
db.commit()
```

## 注意点

- `C採番` テーブルに対象テーブル名のエントリがないと採番が失敗する → 初期データに採番レコードを追加すること
- 採番APIは `C採番.最終採番値 + 1` を保存して返す。新規 T 系や伝票系を追加したら、`core_crud/C採番.py` の初期データ、または既存DB向けの `apps_crud/init.py` 補正で対象 `採番ID` を追加する
- `create_audit_fields` と `update_audit_fields` を混同しないこと（更新時に登録系フィールドを上書きしてはいけない）
- 監査フィールドを Model 定義に書き忘れると `column not found` エラーになる
- `C採番` の初期化関数は「1件でも存在したら return」するため、後から採番IDを増やしても既存DBには自動追加されない。既存DB対応が必要なときは `init_db_data()` 側で個別に未存在チェックして追加する。
- 採番IDは原則テーブル名と一致させる（例: `T商品入庫`）。フロントが `/core/C採番/採番` を呼ぶ場合も同じ文字列を使う。
- `create_audit_fields()` に渡す認証情報は `利用者ID` / `利用者名` / `端末ID` を揃える。既存実装には端末ID省略時に既定値へ倒す箇所もあるが、新規実装では明示する。

## 採番を使う対象の判断

- M系の分類マスタなど、IDを利用者が意味を持って入力するマスタは採番不要にしてよい。
- T系伝票ID、システム生成ID、連番で衝突回避したいIDは `C採番` を使う。
- 明細型テーブルではヘッダーIDだけを採番し、`明細SEQ` はリクエスト明細順に 0, 1, 2... を組み立てる。

## 確認方法

```bash
# 採番テーブルの確認
sqlite3 backend_server/_data/AiDiy/database.db "SELECT * FROM C採番"
```
