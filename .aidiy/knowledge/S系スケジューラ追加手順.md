# S系スケジューラ追加手順

## このメモを使う場面
- 配車スケジュール・生産スケジュールのような週/日カレンダー形式の画面を追加したい
- ドラッグ&リサイズでスケジュールを編集する UI を実装したい

## 関連ファイル
- `backend_server/apps_router/S配車.py` / `S生産.py` — 参考実装
- `backend_server/apps_main.py` — Router 登録
- `frontend_web/src/components/S*/` — スケジューラ系画面

## Backend 実装手順

S系は以下のエンドポイントをセットで実装する。

| エンドポイント | 用途 |
|--------------|------|
| `POST /apps/S<名称>/車両一覧`（or 工程一覧） | スケジュール行（縦軸）の一覧 |
| `POST /apps/S<名称>/<対象>一覧` | スケジュールアイテム一覧（日付範囲指定） |
| `POST /apps/S<名称>/データ` | カレンダー表示用の整形済みデータ |
| `POST /apps/S<名称>/ドラッグ更新` | ドラッグ移動後の日時・行を更新 |
| `POST /apps/S<名称>/リサイズ更新` | リサイズ後の期間を更新 |
| `POST /apps/S<名称>/最終更新日時` | フロントの変更監視用（軽量） |

週表示・日表示を分ける場合は、既存の `S配車_週表示.py` / `S配車_日表示.py`、`S生産_週表示.py` / `S生産_日表示.py` のように Router ファイルも分ける。`apps_main.py` には両方を import し、両方 `include_router` する。

### Request クラスのパターン

```python
class データRequest(BaseModel):
    開始日付: str  # YYYY-MM-DD
    終了日付: str
    利用者ID: str | None = None

class ドラッグ更新Request(BaseModel):
    ID: str
    新開始日付: str
    新終了日付: str
    新行ID: str  # 車両IDや工程IDなど
    # 認証情報
    利用者ID: str
    利用者名: str
    端末ID: str
```

### ドラッグ更新・リサイズ更新の実装方針

```python
@router.post("/apps/S配車/ドラッグ更新")
def ドラッグ更新(request: ドラッグ更新Request, db: Session = Depends(get_db),
                current_user = Depends(get_current_user)):
    record = db.query(T配車).filter(
        T配車.配車ID == request.ID, T配車.明細SEQ == 0
    ).first()
    if not record:
        return {"status": "NG", "message": "対象データなし"}
    record.開始日付 = request.新開始日付
    record.終了日付 = request.新終了日付
    record.車両ID   = request.新行ID
    audit = update_audit_fields(request.dict())
    for k, v in audit.items():
        setattr(record, k, v)
    db.commit()
    return {"status": "OK", "message": "更新しました"}
```

## Frontend 実装の特徴

- スケジューラ画面は `qTublerFrame.vue` ではなく独自のカレンダー描画を実装
- 日付ヘッダー（横軸）は表示期間（週/月）を動的生成
- ドラッグ&リサイズのイベントは `mousedown` → `mousemove` → `mouseup` で追跡
- 最終更新日時を 30 秒ごとにポーリングして他ユーザーの変更を検知し自動リロード

### `checkForUpdates()` の実装パターン（Vue / frontend_web）

```typescript
import { useAuthStore } from '@/stores/auth'
const lastUpdated = ref<string | null>(null)
let updateInterval: ReturnType<typeof setInterval> | null = null

const checkForUpdates = async () => {
  // JWT 延長（S系は CMT操作系でないため、画面側で明示的に呼ぶ）
  await useAuthStore().refreshToken()

  const res = await apiClient.post('/apps/S<名称>/最終更新日時', {})
  if (res.data.status !== 'OK') return

  const latest = res.data.data.最終更新日時
  if (lastUpdated.value !== null && latest !== lastUpdated.value) {
    // 他ユーザーの変更を検知 → データ再取得
    await loadData()
  }
  lastUpdated.value = latest
}

onMounted(async () => {
  await loadData()
  updateInterval = setInterval(checkForUpdates, 30000)
})
onBeforeUnmount(() => {
  if (updateInterval) clearInterval(updateInterval)
})
```

- 初回マウント時に `lastUpdated` を設定し、次回以降の差分で変更を判定する
- `refreshToken()` は更新があった場合だけでなく、監視のたびに呼ぶ（「画面を表示中=操作中」とみなす）
- S系の URL は `/apps/S*` のため `CMT操作系認証延長対象()` の対象外。画面側で呼ぶ必要がある

### ドラッグ座標の計算方針

```typescript
// セル位置からドロップ後の日付・行IDを計算する例
const onMouseUp = async (event: MouseEvent) => {
  if (!isDragging.value) return
  const cellIndex = getCellIndexFromPosition(event.clientX)
  const rowId = getRowIdFromPosition(event.clientY)
  const newDate = dateFromCellIndex(cellIndex)
  
  // 「移動量」ではなく「確定後の値」をAPIに渡す
  await apiClient.post('/apps/S<名称>/ドラッグ更新', {
    ID: draggingItem.value.ID,
    新開始日付: newDate,
    新終了日付: calcNewEnd(draggingItem.value, newDate),
    新行ID: rowId,
    ...authFields,
  })
  isDragging.value = false
  await loadData()
}
```

## Backend 実装の判断基準

- 行マスタ（車両・工程など）は `有効=True` で絞るか、既存画面の「無効も表示」方針と合わせる。
- スケジュール対象が明細型 T 系の場合、表示・更新対象はヘッダー行だけにする。条件に `明細SEQ == 0` を入れる。
- 表示範囲は画面範囲ぴったりではなく、ドラッグや横スクロールのため前後に余白を持たせてもよい。`S生産_週表示` は指定範囲の前後30日を取得する。
- 日時を扱う場合は ISO 形式文字列で保存し、比較時は `datetime.fromisoformat()` または SQLite の `date()` を使う。
- ドラッグ更新では「新しい行ID」「新しい開始/終了」を保存する前に、開始 < 終了、対象行の存在、重複を確認する。
- 監査項目は `current_user` から `利用者ID` / `利用者名` を作って `update_audit_fields()` で更新する。端末IDが必要な画面では request から渡す。

## 注意点

- 重複チェック（同一行・同一期間に既存スケジュールがあるか）は更新前に必ず実施
- 日付の比較は `YYYY-MM-DD` 文字列比較で可（SQLite は文字列比較で日付順が保証される）
- ドラッグ更新とリサイズ更新は「移動量だけ」を受け取るのではなく「移動後の確定値」を受け取る設計にすること（フロント計算ミスを防ぐため）
- `最終更新日時` エンドポイントは認証チェックありで実装する（ポーリング間隔が短くても安全なように）
- 重複チェックでは自分自身を除外する。除外条件がないと、ドラッグやリサイズを保存するたびに自レコードと重複して更新不能になる。
- 日表示と週表示で同じ T 系を更新する場合、更新ロジックの条件を揃える。片方だけ重複判定や監査更新が違うと画面間で挙動がずれる。

## 確認方法

1. Swagger `http://localhost:8092/docs` でデータ取得エンドポイントが動作することを確認
2. フロントで週表示・月表示の切替が正常か確認
3. ドラッグ後にリロードして位置が保存されているか確認
4. 既存予定と重なる位置へ移動して `NG` が返ることを確認
5. 日表示で更新した内容が週表示にも反映されることを確認
