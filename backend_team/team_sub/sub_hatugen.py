# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""雑談エリアの要員1名に「今やるべきこと」を発言させるサブプロセス。

team_watcher.py（1分ごとの雑談確認）が、雑談エリア（状態=雑談中）の要員から1名を選び、
Aチーム会話へ空の発言行（発言シーケンスに入ったことのマーク）を追加したうえで
temp/talk/<ファイル名>.json に入力値を書き、このスクリプトを
`python sub_hatugen.py <入力JSONパス>` で起動する。

チーム目標と、他の要員の最新の発言（あれば）を並べて、対象要員の人格で
aidiy_code_agents（team_chat.py の単発会話と同じ経路）へ「今やるべきこと」を尋ね、
その応答をAチーム会話の該当行へ書き戻す。ここでは意見を集めるだけで、実行はしない。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_TEAM_SUB_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_TEAM_SUB_DIR.parent))
sys.path.insert(0, str(_TEAM_SUB_DIR))

from log_config import get_logger, setup_logging
from team_proc import team_chat, team_talk_db


def 依頼内容を作る(チーム目標: str, 他者意見一覧: list[dict]) -> str:
    if 他者意見一覧:
        他者意見 = "\n\n".join(
            f"### {行.get('要員ID', '')} の直近の発言\n{str(行.get('発言内容', '')).strip()}"
            for 行 in 他者意見一覧
        )
    else:
        他者意見 = "まだ他の要員の発言はありません。"

    return f"""チーム目標: {チーム目標}

## 他の要員の直近の発言

{他者意見}

これらを踏まえ、あなた自身の考えとして「今やるべきこと」を一言、自然な口調で発言してください。
結論だけを簡潔に述べ、長い説明や前置きは不要です。他の要員の発言と重複しにくい観点があれば、それを優先してください。
"""


def main() -> int:
    setup_logging("sub_hatugen")
    logger = get_logger("team_sub_hatugen")
    会話ID = ""
    try:
        if len(sys.argv) < 2:
            raise ValueError("使い方: python sub_hatugen.py <temp/talk/入力JSON>")
        入力パス = Path(sys.argv[1]).resolve()
        with 入力パス.open("r", encoding="utf-8-sig") as f:
            項目 = json.load(f)
        会話ID = str(項目.get("会話ID", "")).strip()
        プロジェクト = str(項目.get("プロジェクト", "")).strip()
        要員ID = str(項目.get("要員ID", "")).strip()
        チーム目標 = str(項目.get("チーム目標", "")).strip()
        TASK_AI_NAME = str(項目.get("TASK_AI_NAME", "claude_cli")).strip() or "claude_cli"
        TASK_AI_MODEL = str(項目.get("TASK_AI_MODEL", "auto")).strip() or "auto"
        他者意見一覧 = 項目.get("他者意見", []) or []
        if not 会話ID or not プロジェクト or not 要員ID:
            raise ValueError("入力JSONに会話ID・プロジェクト・要員IDがありません")

        依頼内容 = 依頼内容を作る(チーム目標, 他者意見一覧)
        logger.info(f"雑談の発言を開始します: 会話ID={会話ID} 要員ID={要員ID} プロジェクト={プロジェクト}")
        結果 = team_chat.会話実行(要員ID, プロジェクト, TASK_AI_NAME, TASK_AI_MODEL, 依頼内容)
        team_talk_db.発言更新(会話ID, 依頼内容, str(結果.get("応答内容", "")))
        logger.info(f"雑談の発言を記録しました: 会話ID={会話ID} 要員ID={要員ID}")
        return 0
    except Exception as exc:
        logger.exception("雑談の発言処理に失敗しました")
        if 会話ID:
            try:
                team_talk_db.発言更新(会話ID, "", f"(発言できませんでした: {exc})")
            except Exception:
                logger.exception(f"Aチーム会話への失敗記録にも失敗しました: {会話ID}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
