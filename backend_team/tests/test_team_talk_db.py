# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

from __future__ import annotations

import asyncio
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from team_proc import team_api, team_chat, team_goal_db, team_pdca_db, team_talk_db, team_watcher, team_work_db
from team_sub import sub_PlanDo_terminate, sub_self_talk, sub_self_work


class TeamTalkDbTest(unittest.TestCase):
    def test_新規依頼は1件目がconfで2件目以降が同じ要員の最終値(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "work-default.db"

            def 接続取得() -> sqlite3.Connection:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                return conn

            設定 = Mock(
                CODE_BASE_PATH="conf-project",
                TEAM_AI_NAME="codex_cli",
                TEAM_AI_MODEL="conf-team-model",
                TASK_AI_NAME="copilot_cli",
                TASK_AI_MODEL="conf-task-model",
            )
            操作者 = {"利用者ID": "admin", "利用者名": "admin", "端末ID": "test"}
            with (
                patch.object(team_work_db, "DB_PATH", db_path),
                patch.object(team_work_db, "接続取得", 接続取得),
                patch.object(team_work_db, "設定読込", return_value=設定),
                patch.object(team_work_db, "_初期化済み", False),
            ):
                first_defaults = team_work_db.依頼新規既定値("admin")
                self.assertEqual(first_defaults["プロジェクト"], "conf-project")
                self.assertEqual(first_defaults["TEAM_AI_NAME"], "codex_cli")
                self.assertEqual(first_defaults["TASK_AI_NAME"], "copilot_cli")

                first = team_work_db.依頼登録(
                    {
                        "要員ID": "admin", "依頼ID": "", "プロジェクト": "latest-project",
                        "要求内容": "first", "TEAM_AI_NAME": "copilot_cli", "TEAM_AI_MODEL": "latest-team",
                        "TASK_AI_NAME": "codex_cli", "TASK_AI_MODEL": "latest-task",
                        "実行有効": True, "状態": "準備開始",
                    },
                    操作者,
                )
                second = team_work_db.依頼登録(
                    {
                        "要員ID": "admin", "依頼ID": "", "プロジェクト": "older-project",
                        "要求内容": "second", "TEAM_AI_NAME": "claude_cli", "TEAM_AI_MODEL": "older-team",
                        "TASK_AI_NAME": "claude_cli", "TASK_AI_MODEL": "older-task",
                        "実行有効": True, "状態": "実行中",
                    },
                    操作者,
                )
                conn = 接続取得()
                conn.execute(
                    'UPDATE "Aチーム依頼" SET 状態 = ?, 更新日時 = ? WHERE 依頼ID = ?',
                    ["完了", "2026-01-02 00:00:00", first["依頼ID"]],
                )
                conn.execute(
                    'UPDATE "Aチーム依頼" SET 更新日時 = ? WHERE 依頼ID = ?',
                    ["2026-01-01 00:00:00", second["依頼ID"]],
                )
                conn.commit()
                conn.close()

                next_defaults = team_work_db.依頼新規既定値("admin")

            self.assertEqual(next_defaults["参照依頼ID"], first["依頼ID"])
            self.assertEqual(next_defaults["プロジェクト"], "latest-project")
            self.assertEqual(next_defaults["TEAM_AI_NAME"], "copilot_cli")
            self.assertEqual(next_defaults["TEAM_AI_MODEL"], "latest-team")
            self.assertEqual(next_defaults["TASK_AI_NAME"], "codex_cli")
            self.assertEqual(next_defaults["TASK_AI_MODEL"], "latest-task")

    def test_初期目標のAI設定はconf値を使う(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "goal-initial.db"

            def 接続取得() -> sqlite3.Connection:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                return conn

            設定 = Mock(
                TEAM_AI_NAME="copilot_cli",
                TEAM_AI_MODEL="team-model",
                TASK_AI_NAME="codex_cli",
                TASK_AI_MODEL="task-model",
            )
            with (
                patch.object(team_goal_db, "DB_PATH", db_path),
                patch.object(team_goal_db, "接続取得", 接続取得),
                patch.object(team_goal_db, "設定読込", return_value=設定),
            ):
                team_goal_db.初期目標を投入()
                item = team_goal_db.目標取得(team_goal_db.既定CODE_BASE_PATH)

            self.assertIsNotNone(item)
            self.assertEqual(item["TEAM_AI_NAME"], "copilot_cli")
            self.assertEqual(item["TEAM_AI_MODEL"], "team-model")
            self.assertEqual(item["TASK_AI_NAME"], "codex_cli")
            self.assertEqual(item["TASK_AI_MODEL"], "task-model")

    def test_発言依頼は具体的な対象と行動と確認を求める(self) -> None:
        prompt = sub_self_talk.依頼内容を作る(
            "会話状況を分かりやすくする",
            [{"要員ID": "member-2", "発言内容": "表示内容を整理したいです。"}],
            "APIの一覧順を確認したいです。",
            "D:/work/project-a",
        )

        self.assertIn("何を対象に", prompt)
        self.assertIn("どのような行動を取り", prompt)
        self.assertIn("何を確認するか", prompt)
        self.assertIn("具体的な対象を少なくとも1つ", prompt)
        self.assertIn("自分で確認していない固有名詞や数値は書かない", prompt)
        self.assertIn("APIの一覧順を確認したいです。（自身の1回前の発言）", prompt)

    def test_発言依頼は発言前にソースを調べさせる(self) -> None:
        """推測ではなく実物を読ませるための手順が入っていること。"""
        prompt = sub_self_talk.依頼内容を作る(
            "会話状況を分かりやすくする",
            [],
            "",
            "D:/work/project-a",
        )

        self.assertIn("対象プロジェクト（作業ディレクトリ）: D:/work/project-a", prompt)
        self.assertIn("`_AIDIY.md`", prompt)
        self.assertIn("`AGENTS.md`", prompt)
        self.assertIn("`.aidiy/knowledge/_index.md`", prompt)
        self.assertIn("実物を読み、現状を把握する", prompt)
        self.assertIn("実際に確認したファイルパス", prompt)
        self.assertIn("http://localhost:8095/", prompt)
        self.assertIn("ファイルの作成・変更・削除、git操作、サーバー操作は行わないでください", prompt)

    def test_旧履歴を複合主キーの最終発言へ移行して上書きする(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "talk.db"

            def 接続取得() -> sqlite3.Connection:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                return conn

            conn = 接続取得()
            conn.execute("""
                CREATE TABLE "Aチーム会話" (
                    会話ID TEXT NOT NULL PRIMARY KEY,
                    プロジェクト TEXT NOT NULL DEFAULT '',
                    要員ID TEXT NOT NULL DEFAULT '',
                    要求内容 TEXT NOT NULL DEFAULT '',
                    発言内容 TEXT NOT NULL DEFAULT '',
                    登録日時 TEXT NOT NULL,
                    登録利用者ID TEXT NOT NULL,
                    登録利用者名 TEXT NOT NULL,
                    登録端末ID TEXT NOT NULL,
                    更新日時 TEXT NOT NULL,
                    更新利用者ID TEXT NOT NULL,
                    更新利用者名 TEXT NOT NULL,
                    更新端末ID TEXT NOT NULL
                )
            """)
            rows = [
                (
                    "TC00001001", "project-a", "member-1", "q1", "old",
                    "2026-01-01 00:00:00", "system", "システム", "test",
                    "2026-01-01 00:00:01", "system", "システム", "test",
                ),
                (
                    "TC00001002", "project-a", "member-1", "q2", "latest",
                    "2026-01-01 00:01:00", "system", "システム", "test",
                    "2026-01-01 00:01:01", "system", "システム", "test",
                ),
                (
                    "TC00001003", "project-b", "member-1", "q3", "other-project",
                    "2026-01-01 00:02:00", "system", "システム", "test",
                    "2026-01-01 00:02:01", "system", "システム", "test",
                ),
            ]
            conn.executemany(
                'INSERT INTO "Aチーム会話" VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                rows,
            )
            conn.commit()
            conn.close()

            with (
                patch.object(team_talk_db, "DB_PATH", db_path),
                patch.object(team_talk_db, "接続取得", 接続取得),
            ):
                team_talk_db.初期化()

                conn = 接続取得()
                info = conn.execute('PRAGMA table_info("Aチーム会話")').fetchall()
                self.assertEqual(
                    [(row["name"], row["pk"]) for row in info if row["pk"]],
                    [("プロジェクト", 1), ("要員ID", 2)],
                )
                self.assertNotIn("会話ID", {row["name"] for row in info})
                self.assertEqual(
                    conn.execute('SELECT COUNT(*) FROM "Aチーム会話"').fetchone()[0],
                    2,
                )
                conn.close()

                self.assertEqual(
                    team_talk_db.会話取得("project-a", "member-1")["発言内容"],
                    "latest",
                )
                操作者 = {"利用者ID": "system", "利用者名": "システム", "端末ID": "test"}
                team_talk_db.発言登録("project-a", "member-1", 操作者)
                self.assertTrue(team_talk_db.発言中あり("project-a"))
                登録更新日時 = team_talk_db.会話取得("project-a", "member-1")["更新日時"]
                team_talk_db.要求内容更新("project-a", "member-1", "processing-q")
                処理中会話 = team_talk_db.会話取得("project-a", "member-1")
                self.assertEqual(処理中会話["要求内容"], "processing-q")
                self.assertEqual(処理中会話["発言内容"], "")
                self.assertGreater(処理中会話["更新日時"], 登録更新日時)
                self.assertEqual(
                    team_talk_db.会話取得("project-a", "member-1")["発言内容"],
                    "",
                )
                team_talk_db.発言更新("project-a", "member-1", "new-q", "new-final")
                self.assertFalse(team_talk_db.発言中あり("project-a"))
                self.assertEqual(
                    team_talk_db.会話取得("project-a", "member-1")["発言内容"],
                    "new-final",
                )
                self.assertEqual(len(team_talk_db.会話一覧("project-a")), 1)
                self.assertEqual(
                    team_talk_db.会話取得("project-b", "member-1")["発言内容"],
                    "other-project",
                )
                self.assertEqual(team_talk_db.会話クリア("project-a"), 1)
                self.assertEqual(team_talk_db.会話一覧("project-a"), [])
                self.assertIsNotNone(team_talk_db.会話取得("project-b", "member-1"))

    def test_会話実行はプロジェクトと指定AIをcode_agentsへ渡す(self) -> None:
        response = {
            "status": "OK",
            "result": "発言",
            "project_path": "D:/work/project-a",
            "ai_name": "codex_cli",
            "ai_model": "gpt-test",
        }
        with (
            patch.object(team_chat, "_ペルソナ指示", return_value="persona"),
            patch.object(team_chat, "_POST送信", return_value=response) as post,
        ):
            result = team_chat.会話実行(
                "member-1",
                "D:/work/project-a",
                "codex_cli",
                "gpt-test",
                "今やるべきことは？",
            )

        payload = post.call_args.args[0]
        self.assertEqual(payload["project_path"], "D:/work/project-a")
        self.assertEqual(payload["ai_name"], "codex_cli")
        self.assertEqual(payload["ai_model"], "gpt-test")
        self.assertEqual(payload["code_permissions"], "none")
        self.assertEqual(payload["timeout_sec"], team_chat.CODE_AGENT_TIMEOUT秒)
        self.assertEqual(result["応答内容"], "発言")

    def test_会話実行の調査モードはツール利用を許可して延長する(self) -> None:
        """ソースを読ませるため、権限指定を外しタイムアウトを延ばすこと。

        code_permissions="none" のままだと CLI に bypassPermissions が渡らず、
        非対話実行ではツールが拒否されてソースを一切読めない。
        """
        response = {"status": "OK", "result": "発言"}
        with (
            patch.object(team_chat, "_ペルソナ指示", return_value="persona") as persona,
            patch.object(team_chat, "_POST送信", return_value=response) as post,
        ):
            team_chat.会話実行(
                "member-1",
                "D:/work/project-a",
                "codex_cli",
                "gpt-test",
                "今やるべきことは？",
                調査モード=True,
            )

        payload = post.call_args.args[0]
        self.assertEqual(payload["code_permissions"], "auto")
        self.assertEqual(payload["timeout_sec"], team_chat.調査CODE_AGENT_TIMEOUT秒)
        self.assertEqual(post.call_args.args[1], team_chat.調査HTTP_TIMEOUT秒)
        self.assertEqual(persona.call_args.args, ("member-1", True))

    def test_ペルソナ指示は調査モードで読み取り調査を許可する(self) -> None:
        要員 = {"要員名": "テスト要員", "役割": "調査担当", "人格情報": "慎重", "有効": True}
        with (
            patch.object(team_chat.team_db, "要員取得", return_value=要員),
            patch.object(team_chat.persona_catalog, "召喚要員取得", return_value={}),
        ):
            通常 = team_chat._ペルソナ指示("member-1")
            調査 = team_chat._ペルソナ指示("member-1", True)

        self.assertIn("会話応答専用", 通常)
        self.assertNotIn("会話応答専用", 調査)
        self.assertIn("読み取りツールで必ず確認", 調査)
        self.assertIn("変更・削除", 調査)
        # 何から読み始めるかを示さないと、AIが的外れな場所を探して精度が落ちる
        self.assertIn("`_AIDIY.md`", 調査)
        self.assertIn("`AGENTS.md`", 調査)
        self.assertIn("`.aidiy/knowledge/_index.md`", 調査)
        self.assertIn("http://localhost:8095/", 調査)

    def test_エージェント会話APIは調査モードで依頼する(self) -> None:
        """利用者画面の会話も、ソースを読んだうえで答えさせること。"""
        with patch.object(team_chat, "会話実行", return_value={"応答内容": "回答"}) as chat:
            response = asyncio.run(
                team_api.エージェント会話(
                    team_api.エージェント会話要求(
                        要員ID="member-1",
                        プロジェクト="D:/work/project-a",
                        TASK_AI_NAME="codex_cli",
                        TASK_AI_MODEL="gpt-test",
                        要求内容="今の実装はどうなっていますか",
                    )
                )
            )

        self.assertEqual(response["status"], "OK")
        self.assertTrue(chat.call_args.kwargs.get("調査モード"))

    def test_sub_self_talkはAI起動前に要求内容を更新する(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            入力パス = Path(tmp) / "talk.json"
            入力パス.write_text(
                json.dumps(
                    {
                        "プロジェクト": "project-a",
                        "要員ID": "member-1",
                        "チーム目標": "会話状況を改善する",
                        "TASK_AI_NAME": "codex_cli",
                        "TASK_AI_MODEL": "gpt-test",
                        "他者意見": [],
                        "自身の1回前の発言": "前回の発言",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            呼出順: list[str] = []

            def 要求内容更新(プロジェクト: str, 要員ID: str, 要求内容: str) -> None:
                self.assertEqual((プロジェクト, 要員ID), ("project-a", "member-1"))
                self.assertIn("チーム目標: 会話状況を改善する", 要求内容)
                呼出順.append("要求内容更新")

            def 会話実行(*args, **kwargs) -> dict:
                呼出順.append("AI起動")
                self.assertTrue(kwargs.get("調査モード"))
                return {"応答内容": "具体的な発言"}

            def 発言更新(*args) -> None:
                呼出順.append("発言更新")

            with (
                patch.object(sub_self_talk, "setup_logging"),
                patch.object(sub_self_talk, "get_logger", return_value=Mock()),
                patch.object(sub_self_talk.sys, "argv", ["sub_self_talk.py", str(入力パス)]),
                patch.object(sub_self_talk.team_talk_db, "要求内容更新", side_effect=要求内容更新),
                patch.object(sub_self_talk.team_chat, "会話実行", side_effect=会話実行),
                patch.object(sub_self_talk.team_talk_db, "発言更新", side_effect=発言更新),
            ):
                self.assertEqual(sub_self_talk.main(), 0)

        self.assertEqual(呼出順, ["要求内容更新", "AI起動", "発言更新"])

    def test_sub_self_workはadmin人格で意見を取りまとめて反映する(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            入力パス = Path(tmp) / "self_work.json"
            入力パス.write_text(
                json.dumps(
                    {
                        "プロジェクト": "project-a",
                        "チーム目標": "会話状況を改善する",
                        "TASK_AI_NAME": "codex_cli",
                        "TASK_AI_MODEL": "gpt-test",
                        "意見一覧": [
                            {"要員ID": "member-1", "発言内容": "APIを確認する"},
                            {"要員ID": "member-2", "発言内容": "画面を確認する"},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with (
                patch.object(sub_self_work, "setup_logging"),
                patch.object(sub_self_work, "get_logger", return_value=Mock()),
                patch.object(sub_self_work.sys, "argv", ["sub_self_work.py", str(入力パス)]),
                patch.object(
                    sub_self_work.team_chat,
                    "会話実行",
                    return_value={"応答内容": "APIと画面を確認し、結果を記録する。"},
                ) as chat,
                patch.object(sub_self_work.team_goal_db, "取りまとめ反映") as reflect,
            ):
                self.assertEqual(sub_self_work.main(), 0)

        self.assertEqual(chat.call_args.args[0], "admin")
        self.assertIn("member-1 の意見", chat.call_args.args[4])
        self.assertIn("member-2 の意見", chat.call_args.args[4])
        self.assertEqual(reflect.call_args.args[2], "APIと画面を確認し、結果を記録する。")
        self.assertEqual(reflect.call_args.args[3], "admin")

    def test_sub_self_workはAI失敗時にDBを変更しない(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            入力パス = Path(tmp) / "self_work.json"
            入力パス.write_text(
                json.dumps(
                    {
                        "プロジェクト": "project-a",
                        "チーム目標": "会話状況を改善する",
                        "意見一覧": [{"要員ID": "member-1", "発言内容": "APIを確認する"}],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with (
                patch.object(sub_self_work, "setup_logging"),
                patch.object(sub_self_work, "get_logger", return_value=Mock()),
                patch.object(sub_self_work.sys, "argv", ["sub_self_work.py", str(入力パス)]),
                patch.object(sub_self_work.team_chat, "会話実行", side_effect=RuntimeError("AI失敗")),
                patch.object(sub_self_work.team_goal_db, "取りまとめ反映") as reflect,
            ):
                self.assertEqual(sub_self_work.main(), 1)

        reflect.assert_not_called()

    def test_取りまとめ反映はチーム作業更新とadmin会話1件化を一括実行する(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "summary.db"

            def 接続取得() -> sqlite3.Connection:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                return conn

            with (
                patch.object(team_goal_db, "DB_PATH", db_path),
                patch.object(team_goal_db, "接続取得", 接続取得),
                patch.object(team_talk_db, "DB_PATH", db_path),
                patch.object(team_talk_db, "接続取得", 接続取得),
                patch.object(team_pdca_db, "DB_PATH", db_path),
                patch.object(team_pdca_db, "接続取得", 接続取得),
            ):
                操作者 = {"利用者ID": "system", "利用者名": "システム", "端末ID": "test"}
                team_goal_db.目標保存(
                    "project-a",
                    "",
                    "会話状況を改善する",
                    操作者,
                    自動作業設定=True,
                )
                for 要員ID, 発言内容 in (("member-1", "API案"), ("member-2", "画面案")):
                    team_talk_db.発言登録("project-a", 要員ID, 操作者)
                    team_talk_db.発言更新("project-a", 要員ID, "意見依頼", 発言内容)
                team_pdca_db.作業登録(
                    {
                        "プロジェクト": "project-a",
                        "ループ": 1,
                        "チーム作業": "古い作業",
                        "要員ID": "member-1",
                        "PDCA区分": "P",
                    }
                )

                item = team_goal_db.取りまとめ反映(
                    "project-a",
                    "取りまとめ依頼",
                    "APIと画面を確認し、結果を記録する。",
                )

                self.assertEqual(item["チーム作業"], "APIと画面を確認し、結果を記録する。")
                会話一覧 = team_talk_db.会話一覧("project-a")
                self.assertEqual(len(会話一覧), 1)
                self.assertEqual(会話一覧[0]["要員ID"], "admin")
                self.assertEqual(会話一覧[0]["要求内容"], "取りまとめ依頼")
                self.assertEqual(会話一覧[0]["発言内容"], "APIと画面を確認し、結果を記録する。")
                self.assertEqual(team_pdca_db.作業一覧("project-a"), [])


class TeamTalkWatcherTest(unittest.TestCase):
    def setUp(self) -> None:
        self.元の雑談プロセス = team_watcher._雑談プロセス
        self.元の自己作業プロセス = team_watcher._自己作業プロセス
        team_watcher._雑談プロセス = None
        team_watcher._自己作業プロセス = None
        self.確認日時 = datetime(2026, 1, 1, 12, 1)
        self.目標 = {
            "自動作業設定": True,
            "CODE_BASE_PATH": "project-a",
            "チーム目標": "会話状況を改善する",
            "チーム作業": "",
            "TASK_AI_NAME": "codex_cli",
            "TASK_AI_MODEL": "gpt-test",
        }

    def tearDown(self) -> None:
        team_watcher._雑談プロセス = self.元の雑談プロセス
        team_watcher._自己作業プロセス = self.元の自己作業プロセス

    def test_空の発言行があれば新しい発言を起動しない(self) -> None:
        with (
            patch.object(team_watcher.team_goal_db, "最終目標取得", return_value=self.目標),
            patch.object(team_watcher.team_talk_db, "発言中あり", return_value=True),
            patch.object(team_watcher, "_雑談実行開始") as start,
        ):
            team_watcher._雑談確認(Mock(), self.確認日時)

        start.assert_not_called()

    def test_チーム目標が空なら発言を起動しない(self) -> None:
        目標 = {**self.目標, "チーム目標": ""}
        with (
            patch.object(team_watcher.team_goal_db, "最終目標取得", return_value=目標),
            patch.object(team_watcher, "_雑談実行開始") as start,
        ):
            team_watcher._雑談確認(Mock(), self.確認日時)

        start.assert_not_called()

    def test_チーム作業が入力済みなら発言を起動しない(self) -> None:
        目標 = {**self.目標, "チーム作業": "実装を開始する"}
        with (
            patch.object(team_watcher.team_goal_db, "最終目標取得", return_value=目標),
            patch.object(team_watcher, "_雑談実行開始") as start,
        ):
            team_watcher._雑談確認(Mock(), self.確認日時)

        start.assert_not_called()

    def test_分の下一桁が0なら発言起動確認をしない(self) -> None:
        with patch.object(team_watcher.team_goal_db, "最終目標取得") as goal_get:
            team_watcher._雑談確認(Mock(), datetime(2026, 1, 1, 12, 10))

        goal_get.assert_not_called()

    def test_分の下一桁0で有効要員4人中2人の意見があれば取りまとめを起動する(self) -> None:
        意見一覧 = [
            {"要員ID": "member-1", "発言内容": "APIを確認する"},
            {"要員ID": "member-2", "発言内容": "画面を確認する"},
        ]
        有効要員一覧 = [
            {"要員ID": "admin"},
            {"要員ID": "member-1"},
            {"要員ID": "member-2"},
            {"要員ID": "member-3"},
        ]
        with (
            patch.object(team_watcher.team_goal_db, "最終目標取得", return_value=self.目標),
            patch.object(team_watcher.team_talk_db, "発言中あり", return_value=False),
            patch.object(team_watcher.team_db, "要員一覧", return_value=有効要員一覧),
            patch.object(team_watcher.team_talk_db, "最新発言一覧", return_value=意見一覧),
            patch.object(team_watcher, "_自己作業実行開始", return_value=Mock()) as start,
        ):
            team_watcher._自己作業確認(Mock(), datetime(2026, 1, 1, 12, 10))

        start.assert_called_once_with(self.目標, 意見一覧, unittest.mock.ANY)

    def test_有効要員4人中1人の意見では取りまとめを起動しない(self) -> None:
        with (
            patch.object(team_watcher.team_goal_db, "最終目標取得", return_value=self.目標),
            patch.object(team_watcher.team_talk_db, "発言中あり", return_value=False),
            patch.object(
                team_watcher.team_db,
                "要員一覧",
                return_value=[
                    {"要員ID": "admin"},
                    {"要員ID": "member-1"},
                    {"要員ID": "member-2"},
                    {"要員ID": "member-3"},
                ],
            ),
            patch.object(
                team_watcher.team_talk_db,
                "最新発言一覧",
                return_value=[{"要員ID": "member-1", "発言内容": "APIを確認する"}],
            ),
            patch.object(team_watcher, "_自己作業実行開始") as start,
        ):
            team_watcher._自己作業確認(Mock(), datetime(2026, 1, 1, 12, 20))

        start.assert_not_called()

    def test_取りまとめは目標あり自動作業オン作業空欄の全条件を必要とする(self) -> None:
        条件外目標一覧 = [
            {**self.目標, "チーム目標": ""},
            {**self.目標, "自動作業設定": False},
            {**self.目標, "チーム作業": "入力済み作業"},
        ]
        for 目標 in 条件外目標一覧:
            with self.subTest(目標=目標):
                team_watcher._自己作業プロセス = None
                with (
                    patch.object(team_watcher.team_goal_db, "最終目標取得", return_value=目標),
                    patch.object(team_watcher, "_自己作業実行開始") as start,
                ):
                    team_watcher._自己作業確認(Mock(), datetime(2026, 1, 1, 12, 30))

                start.assert_not_called()

    def test_取りまとめは分の下一桁0以外では確認しない(self) -> None:
        with patch.object(team_watcher.team_goal_db, "最終目標取得") as goal_get:
            team_watcher._自己作業確認(Mock(), datetime(2026, 1, 1, 12, 29))

        goal_get.assert_not_called()

    def test_予定要員が10分以内に発言済みなら起動しない(self) -> None:
        最新日時 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with (
            patch.object(team_watcher.team_goal_db, "最終目標取得", return_value=self.目標),
            patch.object(team_watcher.team_talk_db, "発言中あり", return_value=False),
            patch.object(
                team_watcher.ストア,
                "エージェント一覧",
                return_value=[{"エージェントID": "member-1", "状態": "雑談中"}],
            ),
            patch.object(team_watcher, "_雑談発言者を選ぶ", return_value="member-1"),
            patch.object(
                team_watcher.team_talk_db,
                "会話取得",
                return_value={"発言内容": "直前の発言", "更新日時": 最新日時},
            ),
            patch.object(team_watcher.team_talk_db, "発言登録") as register,
            patch.object(team_watcher, "_雑談実行開始") as start,
        ):
            team_watcher._雑談確認(Mock(), self.確認日時)

        register.assert_not_called()
        start.assert_not_called()

    def test_自身の前回発言を退避して他者意見と一緒に渡す(self) -> None:
        過去日時 = (datetime.now() - timedelta(minutes=11)).strftime("%Y-%m-%d %H:%M:%S")
        他者会話 = {"要員ID": "member-2", "発言内容": "他者の発言"}
        with (
            patch.object(team_watcher.team_goal_db, "最終目標取得", return_value=self.目標),
            patch.object(team_watcher.team_talk_db, "発言中あり", return_value=False),
            patch.object(
                team_watcher.ストア,
                "エージェント一覧",
                return_value=[{"エージェントID": "member-1", "状態": "雑談中"}],
            ),
            patch.object(team_watcher, "_雑談発言者を選ぶ", return_value="member-1"),
            patch.object(
                team_watcher.team_talk_db,
                "会話取得",
                return_value={"発言内容": "自身の前回発言", "更新日時": 過去日時},
            ),
            patch.object(
                team_watcher.team_talk_db,
                "最新発言一覧",
                return_value=[
                    {"要員ID": "member-1", "発言内容": "自身の前回発言"},
                    他者会話,
                ],
            ),
            patch.object(
                team_watcher.team_talk_db,
                "発言登録",
                return_value={"プロジェクト": "project-a", "要員ID": "member-1"},
            ),
            patch.object(team_watcher, "_雑談実行開始", return_value=Mock()) as start,
        ):
            team_watcher._雑談確認(Mock(), self.確認日時)

        _, _, 他者意見一覧, 自身の前回発言, _ = start.call_args.args
        self.assertEqual(他者意見一覧, [他者会話])
        self.assertEqual(自身の前回発言, "自身の前回発言")


class TeamTerminateWatcherTest(unittest.TestCase):
    def setUp(self) -> None:
        self.元の終了プロセス = team_watcher._終了プロセス
        self.元の終了処理中キー = team_watcher._終了処理中キー
        self.元の終了処理済みキー = set(team_watcher._終了処理済みキー)
        team_watcher._終了プロセス = None
        team_watcher._終了処理中キー = None
        team_watcher._終了処理済みキー.clear()
        self.目標 = {
            "CODE_BASE_PATH": "project-a",
            "チーム目標": "品質を改善する",
            "チーム作業": "型検査とテストを実行する",
            "作業ループ": 1,
            "作業ループ回数": 1,
            "更新日時": "2026-01-01 12:00:00",
        }

    def tearDown(self) -> None:
        team_watcher._終了プロセス = self.元の終了プロセス
        team_watcher._終了処理中キー = self.元の終了処理中キー
        team_watcher._終了処理済みキー.clear()
        team_watcher._終了処理済みキー.update(self.元の終了処理済みキー)

    def test_PlanDoとSPDCAは赤ネオン消灯時に同じ終了フックを起動する(self) -> None:
        for パターン in ("PlanDo", "SPDCA"):
            with self.subTest(パターン=パターン):
                team_watcher._終了プロセス = None
                team_watcher._終了処理中キー = None
                team_watcher._終了処理済みキー.clear()
                目標 = {**self.目標, "パターン": パターン}
                with (
                    patch.object(team_watcher.team_goal_db, "作業ループ対象一覧", return_value=[目標]),
                    patch.object(team_watcher.team_pdca_db, "作業ループ終了済み", return_value=True) as finished,
                    patch.object(team_watcher.team_pdca_db, "ループ最大値", return_value=1),
                    patch.object(team_watcher, "_終了実行開始", return_value=Mock()) as start,
                ):
                    team_watcher._作業ループ終了確認(Mock())

                finished.assert_called_once_with("project-a", パターン, 1)
                start.assert_called_once_with(目標, unittest.mock.ANY)

    def test_毎分終了判定は最大ループ最終段の決着を確認する(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "terminate.db"

            def 接続取得() -> sqlite3.Connection:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                return conn

            with (
                patch.object(team_pdca_db, "DB_PATH", db_path),
                patch.object(team_pdca_db, "接続取得", 接続取得),
            ):
                for パターン, 最終区分 in (("PlanDo", "D"), ("SPDCA", "A")):
                    プロジェクト = f"project-{パターン}"
                    作業 = team_pdca_db.作業登録(
                        {
                            "プロジェクト": プロジェクト,
                            "ループ": 1,
                            "チーム作業": "確認する",
                            "要員ID": "member-1",
                            "PDCA区分": 最終区分,
                        }
                    )
                    self.assertFalse(team_pdca_db.作業ループ終了済み(プロジェクト, パターン, 1))
                    team_pdca_db.作業終了記録(作業["作業ID"], "完了", "済")
                    self.assertTrue(team_pdca_db.作業ループ終了済み(プロジェクト, パターン, 1))
                    self.assertFalse(team_pdca_db.作業ループ終了済み(プロジェクト, パターン, 2))
                    self.assertFalse(team_pdca_db.作業ループ終了済み(プロジェクト, パターン, 99))

    def test_赤ネオン点灯中は終了フックを起動しない(self) -> None:
        目標 = {**self.目標, "パターン": "PlanDo"}
        with (
            patch.object(team_watcher.team_goal_db, "作業ループ対象一覧", return_value=[目標]),
            patch.object(team_watcher.team_pdca_db, "作業ループ終了済み", return_value=False),
            patch.object(team_watcher, "_終了実行開始") as start,
        ):
            team_watcher._作業ループ終了確認(Mock())

        start.assert_not_called()

    def test_同じ完了状態では終了フックを繰り返さない(self) -> None:
        目標 = {**self.目標, "パターン": "PlanDo"}
        完了プロセス = Mock()
        完了プロセス.poll.return_value = 0
        with (
            patch.object(team_watcher.team_goal_db, "作業ループ対象一覧", return_value=[目標]),
            patch.object(team_watcher.team_pdca_db, "作業ループ終了済み", return_value=True),
            patch.object(team_watcher.team_pdca_db, "ループ最大値", return_value=1),
            patch.object(team_watcher, "_終了実行開始", return_value=完了プロセス) as start,
        ):
            team_watcher._作業ループ終了確認(Mock())
            team_watcher._作業ループ終了確認(Mock())

        start.assert_called_once()

    def test_SPDCAもsub_PlanDo_terminateを起動する(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            目標 = {**self.目標, "パターン": "SPDCA"}
            proc = Mock(pid=1234)
            with (
                patch.object(team_watcher, "_作業入力DIR", Path(tmp)),
                patch.object(team_watcher.team_pdca_db, "ループ最大値", return_value=1),
                patch.object(team_watcher.subprocess, "Popen", return_value=proc) as popen,
            ):
                result = team_watcher._終了実行開始(目標, Mock())

            self.assertIs(result, proc)
            command = popen.call_args.args[0]
            self.assertEqual(Path(command[1]).name, "sub_PlanDo_terminate.py")
            入力内容 = json.loads(Path(command[2]).read_text(encoding="utf-8"))
            self.assertEqual(入力内容["パターン"], "SPDCA")

    def test_終了フック本体はPlanDoとSPDCAの入力を受け付ける(self) -> None:
        for パターン in ("PlanDo", "SPDCA"):
            with self.subTest(パターン=パターン), tempfile.TemporaryDirectory() as tmp:
                入力パス = Path(tmp) / "terminate.json"
                入力パス.write_text(
                    json.dumps(
                        {
                            "プロジェクト": "project-a",
                            "チーム作業": "型検査とテストを実行する",
                            "パターン": パターン,
                            "作業ループ回数": 1,
                        },
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
                with (
                    patch.object(sub_PlanDo_terminate, "setup_logging"),
                    patch.object(sub_PlanDo_terminate, "get_logger", return_value=Mock()),
                    patch.object(
                        sub_PlanDo_terminate.team_goal_db,
                        "作業ループ終了後更新",
                        return_value={"処理": "再協議"},
                    ) as update,
                    patch.object(
                        sub_PlanDo_terminate.sys,
                        "argv",
                        ["sub_PlanDo_terminate.py", str(入力パス)],
                    ),
                ):
                    self.assertEqual(sub_PlanDo_terminate.main(), 0)
                update.assert_called_once_with("project-a")


class TeamGoalTalkClearTest(unittest.TestCase):
    def test_終了後更新は自動作業オンなら作業と会話をクリアして再協議する(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "terminate-auto-on.db"

            def 接続取得() -> sqlite3.Connection:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                return conn

            操作者 = {"利用者ID": "system", "利用者名": "システム", "端末ID": "test"}
            with (
                patch.object(team_goal_db, "DB_PATH", db_path),
                patch.object(team_goal_db, "接続取得", 接続取得),
                patch.object(team_talk_db, "DB_PATH", db_path),
                patch.object(team_talk_db, "接続取得", 接続取得),
            ):
                team_goal_db.目標保存(
                    "project-a",
                    "完了した作業",
                    "継続的に改善する",
                    操作者,
                    自動作業設定=True,
                    作業ループ=True,
                )
                team_talk_db.発言登録("project-a", "member-1", 操作者)
                team_talk_db.発言更新("project-a", "member-1", "意見依頼", "次の意見")

                result = team_goal_db.作業ループ終了後更新("project-a")

                self.assertEqual(result["処理"], "再協議")
                self.assertEqual(result["item"]["チーム作業"], "")
                self.assertTrue(bool(result["item"]["作業ループ"]))
                self.assertEqual(team_talk_db.会話一覧("project-a"), [])

    def test_終了後更新は自動作業オフなら作業ループだけを停止する(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "terminate-auto-off.db"

            def 接続取得() -> sqlite3.Connection:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                return conn

            操作者 = {"利用者ID": "system", "利用者名": "システム", "端末ID": "test"}
            with (
                patch.object(team_goal_db, "DB_PATH", db_path),
                patch.object(team_goal_db, "接続取得", 接続取得),
                patch.object(team_talk_db, "DB_PATH", db_path),
                patch.object(team_talk_db, "接続取得", 接続取得),
            ):
                team_goal_db.目標保存(
                    "project-a",
                    "完了した作業",
                    "継続的に改善する",
                    操作者,
                    自動作業設定=False,
                    作業ループ=True,
                )
                team_talk_db.発言登録("project-a", "member-1", 操作者)
                team_talk_db.発言更新("project-a", "member-1", "意見依頼", "保存する意見")

                result = team_goal_db.作業ループ終了後更新("project-a")

                self.assertEqual(result["処理"], "停止")
                self.assertEqual(result["item"]["チーム作業"], "完了した作業")
                self.assertFalse(bool(result["item"]["作業ループ"]))
                self.assertEqual(team_talk_db.会話一覧("project-a")[0]["発言内容"], "保存する意見")

    def test_赤ネオンは作業ループオンかつチーム作業入力済みで点灯する(self) -> None:
        for 作業ループ, チーム作業, 期待値 in (
            (True, "実装する", True),
            (True, "", False),
            (True, "   ", False),
            (False, "実装する", False),
        ):
            with self.subTest(作業ループ=作業ループ, チーム作業=チーム作業):
                item = {
                    "CODE_BASE_PATH": "project-a",
                    "チーム作業": チーム作業,
                    "作業ループ": 作業ループ,
                    "更新日時": "2026-01-01 12:00:00",
                }
                with patch.object(team_api.team_goal_db, "最終目標取得", return_value=item):
                    result = asyncio.run(team_api.チーム目標最終())

                self.assertEqual(result["status"], "OK")
                self.assertEqual(result["data"]["作業実行中"], 期待値)

    def test_作業ループ対象はループオンかつチーム作業入力済みだけ(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "goal.db"

            def 接続取得() -> sqlite3.Connection:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                return conn

            操作者 = {"利用者ID": "system", "利用者名": "システム", "端末ID": "test"}
            with (
                patch.object(team_goal_db, "DB_PATH", db_path),
                patch.object(team_goal_db, "接続取得", 接続取得),
            ):
                for パス, 作業, ループ in (
                    ("valid", "実装する", True),
                    ("empty", "", True),
                    ("spaces", "   ", True),
                    ("loop-off", "実装する", False),
                ):
                    team_goal_db.目標保存(パス, 作業, "目標", 操作者, 作業ループ=ループ)

                対象一覧 = team_goal_db.作業ループ対象一覧()

        self.assertEqual([行["CODE_BASE_PATH"] for 行 in 対象一覧], ["valid"])

    def test_作業ループ確認は対象一覧の不正な空作業を起動しない(self) -> None:
        元の作業プロセス = team_watcher._作業プロセス
        team_watcher._作業プロセス = None
        try:
            with (
                patch.object(
                    team_watcher.team_goal_db,
                    "作業ループ対象一覧",
                    return_value=[{"CODE_BASE_PATH": "project-a", "作業ループ": 1, "チーム作業": "   "}],
                ),
                patch.object(team_watcher.team_status_db, "実行中要員数") as active_count,
                patch.object(team_watcher, "_作業実行開始") as start,
            ):
                team_watcher._作業ループ確認(Mock())
        finally:
            team_watcher._作業プロセス = 元の作業プロセス

        active_count.assert_not_called()
        start.assert_not_called()

    def test_チーム目標か自動作業設定が変わった場合だけ会話クリアが必要(self) -> None:
        変更前 = {
            "チーム目標": "old-goal",
            "自動作業設定": 0,
        }
        self.assertFalse(team_goal_db.会話クリア必要(None, "new-goal", True))
        self.assertFalse(team_goal_db.会話クリア必要(変更前, "old-goal", False))
        self.assertTrue(team_goal_db.会話クリア必要(変更前, "new-goal", False))
        self.assertTrue(team_goal_db.会話クリア必要(変更前, "old-goal", True))

    def test_目標保存APIはチーム目標変更時に対象プロジェクトの会話をクリアする(self) -> None:
        request = team_api.チーム目標保存要求(
            CODE_BASE_PATH="project-a",
            チーム目標="new-goal",
            自動作業設定=False,
            チーム作業="same-work",
            作業ループ=False,
            パターン="PlanDo",
        )
        変更前 = {
            "CODE_BASE_PATH": "project-a",
            "チーム目標": "old-goal",
            "自動作業設定": 0,
            "チーム作業": "same-work",
            "作業ループ": 0,
            "パターン": "PlanDo",
        }
        with (
            patch.object(team_api.team_goal_db, "目標取得", return_value=変更前),
            patch.object(team_api.team_goal_db, "目標保存", return_value={"CODE_BASE_PATH": "project-a"}),
            patch.object(team_api.team_pdca_db, "作業クリア") as work_clear,
            patch.object(team_api.team_talk_db, "会話クリア", return_value=2) as talk_clear,
        ):
            result = asyncio.run(team_api.チーム目標保存(request))

        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["data"]["会話クリア件数"], 2)
        self.assertNotIn("作業クリア件数", result["data"])
        talk_clear.assert_called_once_with("project-a")
        work_clear.assert_not_called()

    def test_目標保存APIは自動作業オンなら作業ループオンでもチーム作業空欄を許可する(self) -> None:
        request = team_api.チーム目標保存要求(
            CODE_BASE_PATH="project-a",
            チーム目標="実施内容を協議する",
            自動作業設定=True,
            チーム作業="",
            作業ループ=True,
            パターン="PlanDo",
        )
        with (
            patch.object(team_api.team_goal_db, "目標取得", return_value=None),
            patch.object(
                team_api.team_goal_db,
                "目標保存",
                return_value={"CODE_BASE_PATH": "project-a", "チーム作業": ""},
            ) as save,
            patch.object(team_api.team_pdca_db, "作業クリア"),
            patch.object(team_api.team_talk_db, "会話クリア"),
        ):
            result = asyncio.run(team_api.チーム目標保存(request))

        self.assertEqual(result["status"], "OK")
        self.assertEqual(save.call_args.args[1], "")


if __name__ == "__main__":
    unittest.main()
