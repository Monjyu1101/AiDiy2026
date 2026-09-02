# -*- coding: utf-8 -*-

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from task_proc import tasks_api, tasks_db, tasks_watcher  # noqa: E402


class TaskRecoveryTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_db_path = tasks_db.DB_PATH
        self.old_db_dir = tasks_db.DB_DIR
        self.old_initialized = tasks_db._初期化済み
        tasks_db.DB_PATH = str(Path(self.temp_dir.name) / "database.db")
        tasks_db.DB_DIR = self.temp_dir.name
        tasks_db._初期化済み = False
        # Team側のテーブル更新はこの単体テストの対象外。
        self.team_patch = patch.object(tasks_db, "_Aチーム依頼反映")
        self.team_patch.start()
        tasks_db.初期化()

    def tearDown(self):
        self.team_patch.stop()
        tasks_db.DB_PATH = self.old_db_path
        tasks_db.DB_DIR = self.old_db_dir
        tasks_db._初期化済み = self.old_initialized
        self.temp_dir.cleanup()

    def _create_task(self, task_id: str = "TKTEST0001") -> str:
        tasks_db.仮タスク登録(task_id, "テスト", "テスト要求", "admin")
        tasks_db.タスク本登録(
            "admin",
            task_id,
            "テストタスク",
            "テスト要求",
            "",
            [
                {"明細SEQ": 0, "タイトル": "開始", "要求内容": "開始する", "先行SEQ": ""},
                {
                    "明細SEQ": 1,
                    "タイトル": "処理",
                    "要求内容": "処理する",
                    "先行SEQ": "0",
                    "操作検証": True,
                    "予測分数": 1,
                },
                {"明細SEQ": 2, "タイトル": "終了", "要求内容": "確認する", "先行SEQ": "1"},
            ],
        )
        self.assertTrue(tasks_db.タスク発火(task_id))
        return task_id

    def _execute(self, sql: str, params=()):
        conn = tasks_db.接続取得()
        try:
            conn.execute(sql, params)
            conn.commit()
        finally:
            conn.close()

    def test_request_disabled_is_diagnosed_and_normally_recovered(self):
        task_id = self._create_task()
        self._execute("UPDATE Aタスク要求 SET 実行有効 = 0 WHERE タスクID = ?", [task_id])

        before = tasks_db.タスク停止検査(task_id)[0]
        self.assertIn("REQUEST_DISABLED", before["状態コード"])
        self.assertEqual("再開", before["推奨操作"])
        self.assertTrue(before["通常復旧可能"])

        result = tasks_db.タスク停止復旧(task_id)
        self.assertTrue(result["復旧実施"])
        self.assertEqual("再開", result["適用モード"])
        self.assertFalse(result["復旧後"]["停止"])
        self.assertEqual(1, tasks_db.タスク要求取得(task_id)["実行有効"])

    def test_internal_retry_restores_enabled_flags_and_pid(self):
        task_id = self._create_task()
        self._execute(
            "UPDATE Aタスク要求 SET 状態 = '実行中', 実行有効 = 1 WHERE タスクID = ?",
            [task_id],
        )
        self._execute(
            "UPDATE Aタスク明細 SET 状態 = '実行中', 実行有効 = 1, PID = '111', 開始日時 = ? "
            "WHERE タスクID = ? AND 明細SEQ = 1",
            [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), task_id],
        )
        tasks_db.明細失敗(task_id, 1, "検証NG")

        result = tasks_db.明細再試行(task_id, 1, 4321)
        detail = tasks_db.明細1件取得(task_id, 1)
        request = result["item"]
        self.assertEqual("実行中", detail["状態"])
        self.assertEqual(1, detail["実行有効"])
        self.assertEqual("4321", detail["PID"])
        self.assertEqual("実行中", request["状態"])
        self.assertEqual(1, request["実行有効"])
        self.assertEqual("", request["終了日時"])

    def test_timeout_requires_force_and_api_stops_pid_before_recovery(self):
        task_id = self._create_task()
        old = (datetime.now() - timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S")
        self._execute(
            "UPDATE Aタスク要求 SET 状態 = '実行中', 実行有効 = 1 WHERE タスクID = ?",
            [task_id],
        )
        self._execute(
            "UPDATE Aタスク明細 SET 状態 = '完了' WHERE タスクID = ? AND 明細SEQ = 0",
            [task_id],
        )
        self._execute(
            "UPDATE Aタスク明細 SET 状態 = '実行中', 実行有効 = 1, PID = '12345', "
            "開始日時 = ?, 予測分数 = 1 WHERE タスクID = ? AND 明細SEQ = 1",
            [old, task_id],
        )

        before = tasks_db.タスク停止検査(task_id)[0]
        self.assertIn("DETAIL_TIMEOUT", before["状態コード"])
        self.assertEqual("強制再開", before["推奨操作"])
        refused = tasks_db.タスク停止復旧(task_id)
        self.assertFalse(refused["復旧実施"])

        with patch.object(tasks_watcher, "_プロセス強制停止") as stop:
            response = asyncio.run(
                tasks_api.タスク要求停止復旧(
                    tasks_api.タスク停止復旧リクエスト(タスクID=task_id, 強制=True)
                )
            )
        self.assertEqual("OK", response["status"])
        stop.assert_called_once_with(12345, tasks_api.logger)
        self.assertTrue(response["data"]["復旧実施"])
        detail = tasks_db.明細1件取得(task_id, 1)
        self.assertEqual("待機", detail["状態"])
        self.assertEqual("", detail["PID"])

    def test_force_does_not_kill_a_healthy_running_task(self):
        task_id = self._create_task()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._execute(
            "UPDATE Aタスク要求 SET 状態 = '実行中', 実行有効 = 1 WHERE タスクID = ?",
            [task_id],
        )
        self._execute(
            "UPDATE Aタスク明細 SET 状態 = '実行中', 実行有効 = 1, PID = '23456', "
            "開始日時 = ?, 予測分数 = 30 WHERE タスクID = ? AND 明細SEQ = 0",
            [now, task_id],
        )

        with patch.object(tasks_watcher, "_プロセス強制停止") as stop:
            response = asyncio.run(
                tasks_api.タスク要求停止復旧(
                    tasks_api.タスク停止復旧リクエスト(タスクID=task_id, 強制=True)
                )
            )
        self.assertEqual("OK", response["status"])
        self.assertFalse(response["data"]["復旧実施"])
        stop.assert_not_called()
        detail = tasks_db.明細1件取得(task_id, 0)
        self.assertEqual("実行中", detail["状態"])
        self.assertEqual("23456", detail["PID"])

    def test_stalled_ai_decomposition_requires_force_and_restarts_decomposition(self):
        task_id = "TKTEST0002"
        tasks_db.仮タスク登録(task_id, "テスト", "テスト要求", "admin")
        old = (datetime.now() - timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S")
        self._execute(
            "UPDATE Aタスク要求 SET 状態 = '準備中', 実行有効 = 1, PID = '34567', "
            "開始日時 = ?, 更新日時 = ? WHERE タスクID = ?",
            [old, old, task_id],
        )

        before = tasks_db.タスク停止検査(task_id)[0]
        self.assertIn("REQUEST_TIMEOUT", before["状態コード"])
        self.assertIn("NO_DETAILS", before["状態コード"])
        self.assertEqual("強制再開", before["推奨操作"])

        with patch.object(tasks_watcher, "_プロセス強制停止") as stop:
            response = asyncio.run(
                tasks_api.タスク要求停止復旧(
                    tasks_api.タスク停止復旧リクエスト(タスクID=task_id, 強制=True)
                )
            )
        self.assertEqual("OK", response["status"])
        stop.assert_called_once_with(34567, tasks_api.logger)
        self.assertEqual("再分解", response["data"]["適用モード"])
        request = tasks_db.タスク要求取得(task_id)
        self.assertEqual("準備開始", request["状態"])
        self.assertEqual("", request["PID"])

    def test_incompatible_resume_mode_does_not_kill_stalled_decomposition(self):
        task_id = "TKTEST0003"
        tasks_db.仮タスク登録(task_id, "テスト", "テスト要求", "admin")
        old = (datetime.now() - timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S")
        self._execute(
            "UPDATE Aタスク要求 SET 状態 = '準備中', PID = '45678', 開始日時 = ?, 更新日時 = ? "
            "WHERE タスクID = ?",
            [old, old, task_id],
        )

        with patch.object(tasks_watcher, "_プロセス強制停止") as stop:
            response = asyncio.run(
                tasks_api.タスク要求停止復旧(
                    tasks_api.タスク停止復旧リクエスト(
                        タスクID=task_id,
                        強制=True,
                        復旧モード="再開",
                    )
                )
            )
        self.assertEqual("OK", response["status"])
        self.assertFalse(response["data"]["復旧実施"])
        self.assertIn("再分解", response["data"]["理由"])
        stop.assert_not_called()
        self.assertEqual("45678", tasks_db.タスク要求取得(task_id)["PID"])

    def test_undefined_details_are_sent_back_to_ai_decomposition(self):
        task_id = self._create_task()
        self._execute("UPDATE Aタスク明細 SET 要求内容 = '' WHERE タスクID = ?", [task_id])

        before = tasks_db.タスク停止検査(task_id)[0]
        self.assertIn("UNDEFINED_DETAILS", before["状態コード"])
        self.assertEqual("再分解", before["推奨操作"])
        result = tasks_db.タスク停止復旧(task_id)
        self.assertTrue(result["復旧実施"])
        self.assertEqual("再分解", result["適用モード"])
        request = tasks_db.タスク要求取得(task_id)
        self.assertEqual("準備開始", request["状態"])
        self.assertEqual(1, request["実行有効"])

    def test_dag_cycle_is_reported_but_not_rewritten_automatically(self):
        task_id = self._create_task()
        self._execute(
            "UPDATE Aタスク明細 SET 先行SEQ = CASE 明細SEQ WHEN 0 THEN '2' WHEN 1 THEN '0' ELSE '1' END "
            "WHERE タスクID = ?",
            [task_id],
        )

        before = tasks_db.タスク停止検査(task_id)[0]
        self.assertIn("DAG_BLOCKED", before["状態コード"])
        self.assertEqual("手動修正", before["推奨操作"])
        result = tasks_db.タスク停止復旧(task_id)
        self.assertFalse(result["復旧実施"])
        self.assertIn("自動修復できません", result["理由"])

    def test_request_error_after_all_details_completed_converges_to_completed(self):
        task_id = self._create_task()
        self._execute(
            "UPDATE Aタスク明細 SET 状態 = '完了', 実行有効 = 1 WHERE タスクID = ?",
            [task_id],
        )
        self._execute(
            "UPDATE Aタスク要求 SET 状態 = 'エラー', 実行有効 = 0 WHERE タスクID = ?",
            [task_id],
        )

        result = tasks_db.タスク停止復旧(task_id)
        self.assertTrue(result["復旧実施"])
        self.assertEqual("完了", tasks_db.タスク要求取得(task_id)["状態"])
        self.assertFalse(result["復旧後"]["停止"])

    def test_missing_task_is_ng_even_with_stopped_only_filter(self):
        response = asyncio.run(
            tasks_api.タスク要求停止検査(
                tasks_api.タスク停止検査リクエスト(タスクID="NOT_FOUND", 停止のみ=True)
            )
        )
        self.assertEqual("NG", response["status"])
        self.assertIn("見つかりません", response["message"])


if __name__ == "__main__":
    unittest.main()
