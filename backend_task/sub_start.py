# -*- coding: utf-8 -*-

"""AIタスクの開始明細を処理するサブプロセス。"""

from __future__ import annotations

import json
import os
import sys
import traceback

from task_proc import tasks_db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ログパス = os.path.join(BASE_DIR, "temp", "task", "sub_start.log")


def ログ(メッセージ: str) -> None:
    print(メッセージ, flush=True)
    os.makedirs(os.path.dirname(ログパス), exist_ok=True)
    with open(ログパス, "a", encoding="utf-8") as f:
        f.write(メッセージ + "\n")


def main() -> int:
    global ログパス
    try:
        if len(sys.argv) < 3:
            raise ValueError("使い方: python sub_start.py <temp/output/利用者ID.タスクID.json> <SEQ>")
        出力JSONパス = os.path.abspath(sys.argv[1])
        明細SEQ = int(sys.argv[2])
        ファイルステム = os.path.splitext(os.path.basename(出力JSONパス))[0]
        ログパス = os.path.join(BASE_DIR, "temp", "task", f"{ファイルステム}.step{明細SEQ}.log")

        with open(出力JSONパス, "r", encoding="utf-8-sig") as f:
            データ = json.load(f)
        利用者ID = str(データ.get("利用者ID", "")).strip()
        タスクID = str(データ.get("タスクID", "")).strip()
        if not 利用者ID or not タスクID:
            raise ValueError("出力 JSON に 利用者ID または タスクID がありません")

        ログ(f"=== 開始処理: {利用者ID}/{タスクID} SEQ={明細SEQ} ===")
        tasks_db.開始明細完了(利用者ID, タスクID, 明細SEQ)
        ログ("開始処理 完了")
        return 0
    except Exception as e:
        ログ(f"エラー: {e}\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
