# -*- coding: utf-8 -*-

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from task_proc import tasks_db, tasks_seed, tasks_watcher  # noqa: E402


class TaskSeedTest(unittest.TestCase):
    """DB 再作成時に投入される実行監視ひな形の検証。"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_db_path = tasks_db.DB_PATH
        self.old_db_dir = tasks_db.DB_DIR
        self.old_initialized = tasks_db._初期化済み
        tasks_db.DB_PATH = str(Path(self.temp_dir.name) / "database.db")
        tasks_db.DB_DIR = self.temp_dir.name
        tasks_db._初期化済み = False
        self.team_patch = patch.object(tasks_db, "_Aチーム依頼反映")
        self.team_patch.start()
        tasks_db.初期化()

    def tearDown(self):
        self.team_patch.stop()
        tasks_db.DB_PATH = self.old_db_path
        tasks_db.DB_DIR = self.old_db_dir
        tasks_db._初期化済み = self.old_initialized
        self.temp_dir.cleanup()

    def test_空DBへ1件目として投入される(self):
        タスクID = tasks_db.初期タスクを投入()
        self.assertTrue(タスクID)
        一覧 = tasks_db.タスク要求一覧(tasks_db.初期タスク利用者ID)
        self.assertEqual(len(一覧), 1)
        self.assertEqual(一覧[0]["タスクID"], タスクID)
        self.assertEqual(一覧[0]["タイトル"], tasks_seed.タイトル)

    def test_勝手に起動しない状態で入る(self):
        タスクID = tasks_db.初期タスクを投入()
        要求 = tasks_db.タスク要求取得(タスクID)
        # 実行有効=0 なので、実行開始条件があっても発火しない
        self.assertEqual(int(要求["実行有効"]), 0)
        self.assertEqual(要求["状態"], "完了")
        self.assertEqual(要求["PID"], "")
        # 実行待ちにも上がらない（要求の実行有効=0 が効いている）
        self.assertEqual(tasks_db.実行待ち一覧(), [])
        self.assertEqual(
            [行 for 行 in tasks_db.実行待ち明細一覧() if 行["タスクID"] == タスクID], []
        )
        # 発火条件を満たさない
        self.assertFalse(tasks_db.タスク発火(タスクID))

    def test_有効化すれば発火して回り始める(self):
        タスクID = tasks_db.初期タスクを投入()
        tasks_db.タスク実行有効更新(タスクID, True)
        # 状態=完了 かつ明細が全件完了なので、そのまま次の周期で発火できる
        self.assertTrue(tasks_db.タスク発火(タスクID))
        要求 = tasks_db.タスク要求取得(タスクID)
        self.assertEqual(要求["状態"], "待機")
        明細 = tasks_db.タスク明細一覧(タスクID)
        self.assertTrue(all(行["状態"] == "待機" for 行 in 明細))
        # 開始明細から実行可能になる
        実行可能 = [行["明細SEQ"] for 行 in tasks_db.実行待ち明細一覧() if 行["タスクID"] == タスクID]
        self.assertEqual(実行可能, [0])

    def test_分岐タスクは完了とパスの混在から2周目が発火する(self):
        """if 分岐を含むタスクは 1 周終えると 完了 と パス が混ざる。

        ここで発火できないと、通らなかった枝が パス で残る監視タスクは
        2 周目以降が永久に来なくなる（間隔実行を設定していても回らない）。
        """
        タスクID = tasks_db.初期タスクを投入()
        tasks_db.タスク実行有効更新(タスクID, True)
        self.assertTrue(tasks_db.タスク発火(タスクID))  # 1 周目

        # 1 周を終えた状態を作る: N 側を通り、Y 側の枝は パス で残る
        conn = tasks_db.接続取得()
        try:
            conn.execute(
                f"UPDATE {tasks_db.AIタスク明細テーブル} SET 状態 = '完了' "
                "WHERE タスクID = ? AND 明細SEQ IN (0, 1, 2, 9, 10, 9999)",
                [タスクID],
            )
            conn.execute(
                f"UPDATE {tasks_db.AIタスク明細テーブル} SET 状態 = 'パス' "
                "WHERE タスクID = ? AND 明細SEQ IN (3, 4, 5, 6, 7, 8)",
                [タスクID],
            )
            conn.execute(
                f"UPDATE {tasks_db.AIタスク要求テーブル} SET 状態 = '完了' WHERE タスクID = ?",
                [タスクID],
            )
            conn.commit()
        finally:
            conn.close()
        状態集合 = {行["状態"] for 行 in tasks_db.タスク明細一覧(タスクID)}
        self.assertEqual(状態集合, {"完了", "パス"})

        self.assertTrue(tasks_db.タスク発火(タスクID), "完了とパスの混在から2周目が発火しない")
        明細 = tasks_db.タスク明細一覧(タスクID)
        self.assertTrue(all(行["状態"] == "待機" for 行 in 明細), "パスが待機へ戻っていない")

    def test_実行途中では発火しない(self):
        タスクID = tasks_db.初期タスクを投入()
        tasks_db.タスク実行有効更新(タスクID, True)
        self.assertTrue(tasks_db.タスク発火(タスクID))
        conn = tasks_db.接続取得()
        try:
            conn.execute(
                f"UPDATE {tasks_db.AIタスク明細テーブル} SET 状態 = '実行中' "
                "WHERE タスクID = ? AND 明細SEQ = 1",
                [タスクID],
            )
            conn.execute(
                f"UPDATE {tasks_db.AIタスク要求テーブル} SET 状態 = '完了' WHERE タスクID = ?",
                [タスクID],
            )
            conn.commit()
        finally:
            conn.close()
        # 走っている明細を巻き戻して二重起動させない
        self.assertFalse(tasks_db.タスク発火(タスクID))

    def test_実行条件が間隔実行で入る(self):
        タスクID = tasks_db.初期タスクを投入()
        条件 = tasks_db.実行条件取得(タスクID)
        self.assertEqual(条件["実行区分"], "間隔実行")
        self.assertEqual(条件["間隔区分"], "分")
        self.assertEqual(int(条件["間隔値"]), 8)
        # 実行有効=0 の間は次回実行日時を持たない
        self.assertEqual(条件["次回実行日時"], "")

    def test_明細のDAGが整合している(self):
        タスクID = tasks_db.初期タスクを投入()
        明細 = tasks_db.タスク明細一覧(タスクID)
        seq一覧 = [int(行["明細SEQ"]) for 行 in 明細]
        self.assertEqual(seq一覧, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 9999])
        タイプ表 = {int(行["明細SEQ"]): 行["タイプ"] for 行 in 明細}
        self.assertEqual(タイプ表[0], "start")
        self.assertEqual(タイプ表[9999], "end")
        self.assertEqual(タイプ表[2], "if")
        self.assertEqual(タイプ表[4], "if")
        self.assertEqual(タイプ表[7], "or")
        self.assertEqual(タイプ表[10], "or")
        for 行 in 明細:
            seq = int(行["明細SEQ"])
            先行 = tasks_db.先行SEQ解析(行["先行SEQ"])
            for 親, 条件 in 先行:
                self.assertIn(親, seq一覧, f"SEQ{seq} の先行 {親} が存在しない")
                self.assertNotEqual(親, seq, f"SEQ{seq} が自分自身を先行に持つ")
                # 判定値を付けられるのは先行が if のときだけ
                if 条件:
                    self.assertEqual(タイプ表[親], "if", f"SEQ{seq} の先行 {親} は if ではない")
                else:
                    self.assertNotEqual(
                        タイプ表[親], "if", f"SEQ{seq} は if 明細 {親} の判定値を指定していない"
                    )

    def test_停止検査で停止と判定されない(self):
        タスクID = tasks_db.初期タスクを投入()
        診断 = tasks_db.タスク停止検査(タスクID)[0]
        # 実行有効=0 でも、完了済みのテンプレートは「止まっている」扱いにしない
        self.assertFalse(診断["停止"], 診断["停止理由"])

    def test_監視対象IDを書き換える箇所は1つだけ(self):
        import re

        タスクID = tasks_db.初期タスクを投入()
        要求 = tasks_db.タスク要求取得(タスクID)
        # 監視先を変えるとき直すのは「監視対象タスクID = <ID>」の代入行だけにする。
        # 残りの出現（ダミーである旨の説明など）は書き換え不要な地の文なので数えない。
        代入行 = re.findall(r"監視対象タスクID\s*=\s*\S+", 要求["要求内容"])
        self.assertEqual(代入行, [f"監視対象タスクID = {tasks_seed.監視対象未設定ID}"])
        # 明細側にはタスクIDを書かない（明細は開始明細が配る処理目標から読む）
        for 行 in tasks_db.タスク明細一覧(タスクID):
            self.assertNotRegex(
                str(行["要求内容"]), r"TK\d{8}",
                f"SEQ{行['明細SEQ']} の要求内容にタスクIDが混入している",
            )

    def test_既存タスクがあれば投入しない(self):
        最初 = tasks_db.初期タスクを投入()
        self.assertTrue(最初)
        二回目 = tasks_db.初期タスクを投入()
        self.assertEqual(二回目, "")
        self.assertEqual(len(tasks_db.タスク要求一覧(tasks_db.初期タスク利用者ID)), 1)

    def test_起動時実行条件初期化で次回が入らない(self):
        import logging

        タスクID = tasks_db.初期タスクを投入()
        tasks_watcher.起動時実行条件初期化(logging.getLogger("test"))
        条件 = tasks_db.実行条件取得(タスクID)
        # 実行有効=0 は発火対象外。再起動しても勝手に予約が入らない
        self.assertEqual(条件["次回実行日時"], "")


if __name__ == "__main__":
    unittest.main()
