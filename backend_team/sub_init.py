# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from log_config import get_logger, setup_logging
from team_proc import team_work_db

BASE_DIR = Path(__file__).resolve().parent
TASK_AGENTS_URL = (
    os.environ.get("AIDIY_TASK_AGENTS_URL")
    or "http://127.0.0.1:8095/aidiy_task_agents/submit"
)


def _post_json(url: str, payload: dict, timeout: int = 30) -> dict:
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"aidiy_task_agents HTTP {exc.code}: {body[:500]}") from exc
    except URLError as exc:
        raise RuntimeError(f"aidiy_task_agentsへ接続できません: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("aidiy_task_agentsからJSON以外の応答が返りました") from exc


def submit_task(item: dict) -> dict:
    return _post_json(
        TASK_AGENTS_URL,
        {
            "prompt": str(item["要求内容"]),
            "project_path": str(item.get("プロジェクト", "")),
            "ai_name": str(item.get("TASK_AI_NAME", "claude_cli")),
            "ai_model": str(item.get("TASK_AI_MODEL", "auto")),
            "user_id": str(item["利用者ID"]),
            "task_id": str(item["作業ID"]),
            "enabled": bool(int(item.get("実行有効", 1) or 0)),
            "return_task_id": True,
            "request_timeout_sec": 15,
        },
    )


def main() -> int:
    setup_logging("sub_init")
    logger = get_logger("team_sub_init")
    input_path: Path | None = None
    user_id = ""
    work_id = ""
    try:
        if len(sys.argv) < 2:
            raise ValueError("使い方: python sub_init.py <temp/input/利用者ID.作業ID.json>")
        input_path = Path(sys.argv[1]).resolve()
        with input_path.open("r", encoding="utf-8-sig") as file:
            item = json.load(file)
        user_id = str(item.get("利用者ID", "")).strip()
        work_id = str(item.get("作業ID", "")).strip()
        if not user_id or not work_id or not str(item.get("要求内容", "")).strip():
            raise ValueError("入力JSONに利用者ID、作業ID、要求内容がありません")

        logger.info(f"aidiy_task_agentsへ投入します: {user_id}/{work_id}")
        result = submit_task(item)
        if result.get("status") != "OK":
            raise RuntimeError(str(result.get("message") or "AIタスク投入に失敗しました"))
        task_id = str(result.get("タスクID") or result.get("task_id") or "").strip()
        if not task_id:
            raise RuntimeError("aidiy_task_agentsの応答にタスクIDがありません")
        team_work_db.record_submission_success(user_id, work_id, task_id)
        logger.info(f"AIタスクを投入しました: {user_id}/{work_id} -> {task_id}")
        return 0
    except Exception as exc:
        logger.exception(f"チーム作業のAIタスク投入に失敗しました: {user_id}/{work_id}")
        if user_id and work_id:
            try:
                team_work_db.record_submission_failure(user_id, work_id, str(exc))
            except Exception:
                logger.exception("Aチーム作業への失敗記録にも失敗しました")
        return 1
    finally:
        if input_path is not None:
            try:
                input_path.unlink(missing_ok=True)
            except OSError:
                logger.warning(f"入力JSONを削除できませんでした: {input_path}")


if __name__ == "__main__":
    raise SystemExit(main())
