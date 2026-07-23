# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

from . import team_work_db

監視間隔秒 = 5
実行回数上限 = 3

BASE_DIR = Path(__file__).resolve().parents[1]
SUB_INIT_PATH = BASE_DIR / "sub_init.py"
INPUT_DIR = BASE_DIR / "temp" / "input"


def _safe_file_part(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.\-\u3040-\u30ff\u3400-\u9fff]", "_", value)


def _input_path(user_id: str, work_id: str) -> Path:
    return INPUT_DIR / f"{_safe_file_part(user_id)}.{_safe_file_part(work_id)}.json"


def _kill_python_process(pid: int, logger: logging.Logger) -> None:
    try:
        if os.name == "nt":
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if f'"{pid}"' not in result.stdout:
                return
            if "python" not in result.stdout.lower():
                logger.warning(f"PID {pid} はpythonプロセスではないため停止しません")
                return
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True,
                timeout=15,
            )
        else:
            import signal

            os.kill(pid, signal.SIGKILL)
        logger.info(f"残存sub_initを停止しました: PID={pid}")
    except ProcessLookupError:
        pass
    except Exception as exc:
        logger.warning(f"PID {pid} の停止に失敗しました: {exc}")


def startup_cleanup(logger: logging.Logger) -> None:
    """再起動前から残るsub_initを停止し、未投入作業を準備開始へ戻す。"""
    try:
        active = team_work_db.active_processes()
        for item in active:
            pid = str(item.get("PID", "")).strip()
            if pid.isdigit():
                _kill_python_process(int(pid), logger)
        reset_count = team_work_db.reset_active_processes()
        if reset_count:
            logger.info(f"残存作業プロセスを{reset_count}件準備開始へ戻しました")
    except Exception:
        logger.exception("チーム作業の起動時クリーンアップに失敗しました")


def _start_work(item: dict, logger: logging.Logger) -> None:
    user_id = str(item["利用者ID"])
    work_id = str(item["作業ID"])
    if int(item.get("実行回数", 0) or 0) >= 実行回数上限:
        team_work_db.record_submission_failure(
            user_id,
            work_id,
            f"実行回数が上限({実行回数上限}回)に達しました",
        )
        return
    if not team_work_db.claim_work(user_id, work_id):
        return

    try:
        INPUT_DIR.mkdir(parents=True, exist_ok=True)
        input_path = _input_path(user_id, work_id)
        with input_path.open("w", encoding="utf-8") as file:
            json.dump(
                {
                    "利用者ID": user_id,
                    "作業ID": work_id,
                    "プロジェクト": str(item.get("プロジェクト", "")),
                    "要求内容": str(item.get("要求内容", "")),
                    "TASK_AI_NAME": str(item.get("TASK_AI_NAME", "claude_cli")),
                    "TASK_AI_MODEL": str(item.get("TASK_AI_MODEL", "auto")),
                    "実行有効": int(item.get("実行有効", 1) or 0),
                },
                file,
                ensure_ascii=False,
                indent=2,
            )

        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        process = subprocess.Popen(
            [sys.executable, str(SUB_INIT_PATH), str(input_path)],
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
        team_work_db.record_process_pid(user_id, work_id, process.pid)
        logger.info(f"チーム作業のタスク投入を開始しました: {user_id}/{work_id} PID={process.pid}")
    except Exception as exc:
        team_work_db.record_submission_failure(user_id, work_id, f"sub_init起動エラー: {exc}")
        logger.exception(f"チーム作業sub_initの起動に失敗しました: {user_id}/{work_id}")


def watch_once(logger: logging.Logger) -> None:
    for item in team_work_db.preparing_works():
        _start_work(item, logger)


async def watch_loop(logger: logging.Logger) -> None:
    logger.info(f"チーム作業監視ループを開始しました (interval={監視間隔秒}s)")
    while True:
        try:
            await asyncio.to_thread(watch_once, logger)
        except Exception:
            logger.exception("チーム作業監視ループでエラーが発生しました")
        await asyncio.sleep(監視間隔秒)
