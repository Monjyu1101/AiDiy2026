# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""改善ループ（S → P → D → C → A）の各段で共通する投入処理。

全 5 段が使う共通部品:

- `前段結果を取得()`: 前段の全レコードが `済` / `エラー` になったかを確認する
- `最新の成功記録()` / `まとめ内容()`: 前段から次段へ引き渡す本文を取り出す
- `段を投入()`: Aチーム作業（準備中）→ Aチーム改善の開始レコード → タスク投入
- `実行不能を記録()`: 引き継ぐ内容が無いとき、終了済みレコードだけ残して次段へ送る

D・C・A はさらに「直前の段のまとめ内容（最新1件）を受け取り、担当をAIに選ばせて
1件だけ投入する」という流れまで同じなので、`段を実行()` がメイン処理ごと引き受ける。
段ごとに違うのは「どの区分の結果を受け取るか」と「AIへ渡すプロンプト」だけで、
その 2 つを呼び出し側（`sub_SPDCA_do.py` / `sub_SPDCA_check.py` / `sub_SPDCA_action.py`）が渡す。

S と P はメイン処理の流れが違うため、それぞれの実装（`sub_SPDCA_soudan.py` /
`sub_SPDCA_plan.py`）に残し、上の共通部品だけを使っている。

| | 前段の取り方 | 担当の決め方 | 投入件数 |
|---|---|---|---|
| S | 前ループのA（同ループに前段なし）。ループ番号を新規採番する | admin以外からランダム | 動員要員数ぶん |
| P | 同ループのSの成功レコード全件 | S成功者からランダム | 1件（成功Sが1件ならAIを起動せずupsert） |
| D / C / A | 同ループの前段の最新1件 | AI選択（`sub_init.py` と同じ経験ベース） | 1件 |
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_TEAM_SUB_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_TEAM_SUB_DIR.parent))
sys.path.insert(0, str(_TEAM_SUB_DIR))

from log_config import get_logger, setup_logging
from team_proc import team_pdca_db, team_work_db

# 担当要員のAI選択は sub_init.py と同じ処理を使う（有効要員 + Aチーム経験で判断させる）
from sub_init import 担当要員を選択, 既定利用者ID

TASK_AGENTS_URL = (
    os.environ.get("AIDIY_TASK_AGENTS_URL")
    or "http://127.0.0.1:8095/aidiy_task_agents/submit"
)
操作者 = {"利用者ID": "system", "利用者名": "システム", "端末ID": "backend_team"}

# プロンプト生成関数の形: (要員ID, プロジェクト, チーム目標, 前段まとめ内容) -> 要求内容
プロンプト生成関数 = Callable[[str, str, str, str], str]


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
        raise RuntimeError(f"HTTP {exc.code}: {body[:500]}") from exc
    except URLError as exc:
        raise RuntimeError(f"接続できません ({url}): {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"JSON以外の応答が返りました ({url})") from exc


def 前段結果を取得(プロジェクト: str, 前段区分: str) -> tuple[int, list[dict], list[dict]]:
    """最大ループ番号の前段レコードと、そのうち「済」になったレコードを返す。"""
    ループ = team_pdca_db.ループ最大値(プロジェクト)
    if not ループ:
        raise RuntimeError(f"{前段区分}のループ番号がありません")
    一覧 = team_pdca_db.ループ区分一覧(プロジェクト, ループ, 前段区分)
    if not 一覧:
        raise RuntimeError(f"ループ{ループ}の{前段区分}レコードがありません")
    if any(str(row.get("状況", "")) not in ("済", "エラー") for row in 一覧):
        raise RuntimeError(f"{前段区分}の全レコードが済またはエラーになっていません")
    成功一覧 = [row for row in 一覧 if str(row.get("状況", "")) == "済"]
    return ループ, 一覧, 成功一覧


def 最新の成功記録(成功一覧: list[dict]) -> dict:
    """「済」レコードのうち最新の1件（改善IDが最大のもの）を返す。"""
    return sorted(成功一覧, key=lambda row: str(row.get("改善ID", "")))[-1]


def まとめ内容(記録: dict) -> str:
    """まとめ内容（無ければ応答内容）を、次段へ引き渡す本文として返す。"""
    for キー in ("まとめ内容", "応答内容"):
        内容 = str(記録.get(キー, "")).strip()
        if 内容:
            return 内容
    return ""


def 要員をAIに選ばせる(区分: str, 本文: str, プロジェクト: str, ループ: int, logger) -> str:
    """本文の作業を担当させるのに最適な要員をAIに選ばせる（sub_init.py と同じ選択処理）。

    選択結果のJSONを書き出す一時ファイル名には区分とループ番号を使う
    （作業IDはこの時点では未採番）。失敗・不正時は sub_init 側で既定利用者IDへフォールバックする。
    """
    要員ID = 担当要員を選択(本文, f"pdca_{区分}_{ループ}", logger, プロジェクト)
    if 要員ID == 既定利用者ID:
        logger.info(f"担当要員は既定利用者ID({既定利用者ID})になりました: 区分={区分} ループ={ループ}")
    return 要員ID


def タスク投入(作業: dict, 要員ID: str) -> str:
    結果 = POST送信(
        TASK_AGENTS_URL,
        {
            "prompt": str(作業["要求内容"]),
            "project_path": str(作業.get("プロジェクト", "")),
            "ai_name": str(作業.get("TASK_AI_NAME", "claude_cli")),
            "ai_model": str(作業.get("TASK_AI_MODEL", "auto")),
            "user_id": 要員ID,
            "task_id": str(作業["作業ID"]),
            "enabled": True,
            "return_task_id": True,
            "request_timeout_sec": 15,
        },
    )
    if 結果.get("status") != "OK":
        raise RuntimeError(str(結果.get("message") or "AIタスク投入に失敗しました"))
    タスクID = str(結果.get("タスクID") or 結果.get("task_id") or "").strip()
    if not タスクID:
        raise RuntimeError("aidiy_task_agentsの応答にタスクIDがありません")
    return タスクID


def 実行不能を記録(
    区分: str, プロジェクト: str, チーム目標: str, ループ: int, 理由: str, logger
) -> None:
    """引き継ぐ内容が無いとき、終了済みレコードだけ残して次の段へ進めるようにする。"""
    改善 = team_pdca_db.改善登録(
        {
            "プロジェクト": プロジェクト,
            "ループ": ループ,
            "作業ID": "",
            "チーム目標": チーム目標,
            "要員ID": "",
            "PDCA区分": 区分,
        }
    )
    改善ID = str(改善.get("改善ID", ""))
    if 改善ID:
        team_pdca_db.改善終了記録(改善ID, 理由)
    logger.warning(f"改善ループ({区分})は投入しませんでした: 改善ID={改善ID} 理由={理由}")


def 投入失敗を記録(区分: str, プロジェクト: str, チーム目標: str, 理由: str, logger) -> None:
    """投入処理そのものが例外で落ちたとき、終了済みレコードだけ残して次の段へ進めるようにする。

    レコードを1件も残さないと、次の分の確認でまた同じ区分が投入され、同じ失敗を延々と
    繰り返して改善ループが進まなくなる（team_watcher._改善ループ確認 は未終了レコードの
    有無で次の段を決めるため）。
    """
    if not プロジェクト:
        # プロジェクトが取れない＝入力JSONすら読めていない場合は記録先を決められない
        logger.warning(f"改善ループ({区分})はプロジェクト不明のため失敗レコードを残せません")
        return
    try:
        実行不能を記録(
            区分, プロジェクト, チーム目標,
            team_pdca_db.ループ最大値(プロジェクト), 理由, logger,
        )
    except Exception:
        logger.exception(f"改善ループ({区分})の失敗レコード作成にも失敗しました")


def 段を投入(
    区分: str,
    要員ID: str,
    プロジェクト: str,
    チーム目標: str,
    ループ: int,
    要求内容: str,
    logger,
) -> bool:
    """要員1名分の Aチーム作業・Aチーム改善・Aタスク要求を作る。"""
    既定 = team_work_db.作業新規既定値(要員ID)
    作業 = team_work_db.直接投入登録(
        {
            "要員ID": 要員ID,
            "プロジェクト": プロジェクト,
            "要求内容": 要求内容,
            "TEAM_AI_NAME": 既定["TEAM_AI_NAME"],
            "TEAM_AI_MODEL": 既定["TEAM_AI_MODEL"],
            "TASK_AI_NAME": 既定["TASK_AI_NAME"],
            "TASK_AI_MODEL": 既定["TASK_AI_MODEL"],
            "実行有効": 1,
        },
        操作者,
    )
    作業ID = str(作業.get("作業ID", ""))
    if not 作業ID:
        raise RuntimeError("Aチーム作業の登録に失敗しました")

    改善 = team_pdca_db.改善登録(
        {
            "プロジェクト": プロジェクト,
            "ループ": ループ,
            "作業ID": 作業ID,
            "チーム目標": チーム目標,
            "要員ID": 要員ID,
            "PDCA区分": 区分,
        }
    )
    改善ID = str(改善.get("改善ID", ""))

    try:
        タスクID = タスク投入(作業, 要員ID)
        team_work_db.投入成功記録(作業ID, タスクID)
        if 改善ID:
            team_pdca_db.改善状況記録(改善ID, "準備完了")
        logger.info(
            f"改善ループ({区分})を投入しました: 改善ID={改善ID} 作業ID={作業ID} "
            f"要員ID={要員ID} タスクID={タスクID}"
        )
        return True
    except Exception as exc:
        logger.exception(f"改善ループ({区分})の投入に失敗しました: 作業ID={作業ID} 要員ID={要員ID}")
        try:
            team_work_db.投入失敗記録(作業ID, str(exc))
        except Exception:
            logger.exception(f"Aチーム作業への失敗記録にも失敗しました: {作業ID}")
        if 改善ID:
            try:
                team_pdca_db.改善終了記録(改善ID, f"投入エラー: {exc}")
            except Exception:
                logger.exception(f"Aチーム改善への失敗記録にも失敗しました: {改善ID}")
        return False


def 段を実行(
    区分: str, 前段区分: str, プロンプト生成: プロンプト生成関数, ログ名: str, 要員継続: bool = False
) -> int:
    """D・C・A の共通メイン処理。前段の結果を受け取り、担当を選んで1件投入する。

    前段が全件エラー、または引き継ぐ内容が空で投入できない場合は、終了済みレコードだけ
    残して 0 を返す（未投入のままだと毎分この段の投入が再試行され、改善ループが止まるため）。

    要員継続=True の場合、AIによる新規の担当選択は行わず、前段（前段区分）を担当した
    要員IDをそのまま引き継ぐ（例: PlanDoのPで計画した本人にDも実施させる）。
    前段の要員IDが取得できない場合のみ、通常どおりAIに選ばせる。
    """
    setup_logging(ログ名)
    logger = get_logger(f"team_{ログ名}")
    プロジェクト = ""
    チーム目標 = ""
    try:
        if len(sys.argv) < 2:
            raise ValueError(f"使い方: python {ログ名}.py <temp/pdca/入力JSON>")
        入力パス = Path(sys.argv[1]).resolve()
        with 入力パス.open("r", encoding="utf-8-sig") as f:
            項目 = json.load(f)
        プロジェクト = str(項目.get("プロジェクト", "")).strip()
        チーム目標 = str(項目.get("チーム目標", "")).strip()
        入力区分 = str(項目.get("PDCA区分", "")).strip() or 区分
        if not プロジェクト or not チーム目標 or 入力区分 != 区分:
            raise ValueError(f"入力JSONに{区分}のプロジェクトとチーム目標がありません")

        ループ, _一覧, 成功一覧 = 前段結果を取得(プロジェクト, 前段区分)
        if not 成功一覧:
            実行不能を記録(
                区分, プロジェクト, チーム目標, ループ,
                f"{前段区分}が全件エラーのため、引き継ぐ内容がありません", logger,
            )
            return 0

        前段記録 = 最新の成功記録(成功一覧)
        本文 = まとめ内容(前段記録)
        if not 本文:
            実行不能を記録(
                区分, プロジェクト, チーム目標, ループ,
                f"{前段区分} {前段記録.get('改善ID', '')} に引き継ぐ内容がありません", logger,
            )
            return 0

        前段要員ID = str(前段記録.get("要員ID", "")).strip()
        if 要員継続 and 前段要員ID:
            要員ID = 前段要員ID
            logger.info(f"改善ループ({区分})は前段({前段区分})の担当要員を引き継ぎます: 要員ID={要員ID}")
        else:
            要員ID = 要員をAIに選ばせる(区分, 本文, プロジェクト, ループ, logger)
        logger.info(
            f"改善ループ({区分})を開始します: プロジェクト={プロジェクト} "
            f"ループ={ループ} 要員ID={要員ID} 前段={前段記録.get('改善ID', '')}"
        )
        要求内容 = プロンプト生成(要員ID, プロジェクト, チーム目標, 本文)
        return 0 if 段を投入(
            区分, 要員ID, プロジェクト, チーム目標, ループ, 要求内容, logger
        ) else 1
    except Exception as exc:
        logger.exception(f"改善ループ({区分})の投入処理に失敗しました")
        投入失敗を記録(区分, プロジェクト, チーム目標, f"投入処理エラー: {exc}", logger)
        return 1
