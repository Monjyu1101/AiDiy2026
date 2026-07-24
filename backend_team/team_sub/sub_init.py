# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""Aチーム作業の入力 JSON を aidiy_task_agents へ投入するサブプロセス。

team_watcher.py が temp/input/<作業ID>.json に入力値を書き、
このスクリプトを `python sub_init.py <入力JSONパス>` で起動する。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from log_config import get_logger, setup_logging
from team_proc import team_work_db

BASE_DIR = Path(__file__).resolve().parent
TASK_AGENTS_URL = (
    os.environ.get("AIDIY_TASK_AGENTS_URL")
    or "http://127.0.0.1:8095/aidiy_task_agents/submit"
)


def POST送信(url: str, payload: dict, timeout: int = 30) -> dict:
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


def タスク投入(項目: dict) -> dict:
    return POST送信(
        TASK_AGENTS_URL,
        {
            "prompt": str(項目["要求内容"]),
            "project_path": str(項目.get("プロジェクト", "")),
            "ai_name": str(項目.get("TASK_AI_NAME", "claude_cli")),
            "ai_model": str(項目.get("TASK_AI_MODEL", "auto")),
            "user_id": str(項目["要員ID"]),
            "task_id": str(項目["作業ID"]),
            "enabled": bool(int(項目.get("実行有効", 1) or 0)),
            "return_task_id": True,
            "request_timeout_sec": 15,
        },
    )


def main() -> int:
    setup_logging("sub_init")
    logger = get_logger("team_sub_init")
    入力パス: Path | None = None
    要員ID = ""
    作業ID = ""
    try:
        if len(sys.argv) < 2:
            raise ValueError("使い方: python sub_init.py <temp/input/作業ID.json>")
        入力パス = Path(sys.argv[1]).resolve()
        with 入力パス.open("r", encoding="utf-8-sig") as f:
            項目 = json.load(f)
        要員ID = str(項目.get("要員ID", "")).strip()
        作業ID = str(項目.get("作業ID", "")).strip()
        if not 要員ID or not 作業ID or not str(項目.get("要求内容", "")).strip():
            raise ValueError("入力JSONに要員ID、作業ID、要求内容がありません")

        logger.info(f"aidiy_task_agentsへ投入します: {作業ID} (要員ID={要員ID})")
        結果 = タスク投入(項目)
        if 結果.get("status") != "OK":
            raise RuntimeError(str(結果.get("message") or "AIタスク投入に失敗しました"))
        タスクID = str(結果.get("タスクID") or 結果.get("task_id") or "").strip()
        if not タスクID:
            raise RuntimeError("aidiy_task_agentsの応答にタスクIDがありません")
        team_work_db.投入成功記録(作業ID, タスクID)
        logger.info(f"AIタスクを投入しました: {作業ID} -> {タスクID}")
        return 0
    except Exception as exc:
        logger.exception(f"チーム作業のAIタスク投入に失敗しました: {作業ID}")
        if 作業ID:
            try:
                team_work_db.投入失敗記録(作業ID, str(exc))
            except Exception:
                logger.exception("Aチーム作業への失敗記録にも失敗しました")
        return 1
    finally:
        if 入力パス is not None:
            try:
                入力パス.unlink(missing_ok=True)
            except OSError:
                logger.warning(f"入力JSONを削除できませんでした: {入力パス}")


if __name__ == "__main__":
    raise SystemExit(main())
