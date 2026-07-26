# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""Aチーム改善（PDCAサイクル）の DB アクセス。

Aチーム目標の `改善ループ` がオンのプロジェクトについて、空き時間に PDCA を1段ずつ
自動で回す。その実行状況を1レコード1作業として記録する。

- 1つの PDCA 段（P / D / C / A）で複数名に投入する場合は、要員ごとに1レコード作る。
- 経験生成まで終わって「済」になると終了日時が入り、次の段を投入できる。
- 状況・応答内容・終了日時は backend_task 側（`tasks_db._Aチーム改善反映`）が
  Aタスク要求の進行に合わせて書き込む。状況は対応する Aチーム作業の状態を写した表示用の値で、
  次の段へ進めるかどうかの判定は終了日時で行う。
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

from .team_db import DB_PATH, 接続取得

改善テーブル = "Aチーム改善"
作業テーブル = "Aチーム作業"
経験テーブル = "Aチーム経験"
# Aチーム作業が「完了」（＝経験生成待ち）のまま、この分数を過ぎても「済」にならない改善レコードは
# 経験生成が失敗したものとみなして回収する。team_exp_db.生成タイムアウト分（30分）より
# 十分に長くとり、正常な経験生成を先回りして打ち切らないようにする。
完了滞留回収分 = 90
# 状況は対応する Aチーム作業の状態を写す（表示用。段の完了判定は終了日時で行う）
状況一覧 = ("準備中", "準備完了", "待機", "実行中", "エラー", "完了", "済", "中止")
初期状況 = "準備中"
# S（相談）は計画を立てる前の意見交換。n名で並行して意見を出し、その結果を P（計画）で1つにまとめる
PDCA区分一覧 = ("S", "P", "D", "C", "A")
PDCA区分名 = {"S": "相談", "P": "計画", "D": "実行", "C": "評価", "A": "改善"}
# 実装済みの区分だけを投入する。未実装の区分が次になったサイクルは何も投入しない。
実装済みPDCA区分 = ("S", "P", "D", "C", "A")
一覧最大件数 = 100

_採番テーブル = "C採番"
_採番ID = "Aチーム改善"
_採番プレフィックス = "TP"
_採番初期値 = 1000


def _現在日時() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _監査項目(利用者ID: str, 利用者名: str, 端末ID: str) -> dict[str, str]:
    now = _現在日時()
    return {
        "登録日時": now,
        "登録利用者ID": 利用者ID,
        "登録利用者名": 利用者名,
        "登録端末ID": 端末ID,
        "更新日時": now,
        "更新利用者ID": 利用者ID,
        "更新利用者名": 利用者名,
        "更新端末ID": 端末ID,
    }


def 初期化() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = 接続取得()
    try:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS "{改善テーブル}" (
                改善ID TEXT NOT NULL PRIMARY KEY,
                プロジェクト TEXT NOT NULL DEFAULT '',
                ループ INTEGER NOT NULL DEFAULT 0,
                作業ID TEXT NOT NULL DEFAULT '',
                チーム目標 TEXT NOT NULL DEFAULT '',
                要員ID TEXT NOT NULL DEFAULT '',
                PDCA区分 TEXT NOT NULL DEFAULT '',
                状況 TEXT NOT NULL DEFAULT '',
                開始日時 TEXT NOT NULL DEFAULT '',
                終了日時 TEXT NOT NULL DEFAULT '',
                応答内容 TEXT NOT NULL DEFAULT '',
                まとめ内容 TEXT NOT NULL DEFAULT '',
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
        # 状況を後から足したため、既存DBには無い場合だけ追加する
        既存列 = {row["name"] for row in conn.execute(f'PRAGMA table_info("{改善テーブル}")')}
        if "状況" not in 既存列:
            conn.execute(
                f'ALTER TABLE "{改善テーブル}" ADD COLUMN 状況 TEXT NOT NULL DEFAULT \'\''
            )
        if "まとめ内容" not in 既存列:
            if "経験内容" in 既存列:
                conn.execute(f'ALTER TABLE "{改善テーブル}" RENAME COLUMN 経験内容 TO まとめ内容')
            else:
                conn.execute(
                    f'ALTER TABLE "{改善テーブル}" ADD COLUMN まとめ内容 TEXT NOT NULL DEFAULT \'\''
                )
        if "ループ" not in 既存列:
            conn.execute(
                f'ALTER TABLE "{改善テーブル}" ADD COLUMN ループ INTEGER NOT NULL DEFAULT 0'
            )
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS "IX_Aチーム改善_プロジェクト"
            ON "{改善テーブル}" (プロジェクト, 改善ID)
        """)
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS "IX_Aチーム改善_作業"
            ON "{改善テーブル}" (作業ID)
        """)
        conn.commit()
    finally:
        conn.close()


def _採番確保(conn: sqlite3.Connection) -> None:
    """C採番（backend_server共有）にAチーム改善用の採番行が無ければ作成する。"""
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS "{_採番テーブル}" (
            採番ID TEXT NOT NULL PRIMARY KEY,
            最終採番値 INTEGER NOT NULL,
            採番備考 TEXT,
            有効 INTEGER NOT NULL DEFAULT 1,
            登録日時 TEXT NOT NULL,
            登録利用者ID TEXT NOT NULL,
            登録利用者名 TEXT,
            登録端末ID TEXT NOT NULL,
            更新日時 TEXT NOT NULL,
            更新利用者ID TEXT NOT NULL,
            更新利用者名 TEXT,
            更新端末ID TEXT NOT NULL
        )
    """)
    now = _現在日時()
    conn.execute(
        f"""
        INSERT OR IGNORE INTO "{_採番テーブル}" (
            採番ID, 最終採番値, 採番備考, 有効,
            登録日時, 登録利用者ID, 登録利用者名, 登録端末ID,
            更新日時, 更新利用者ID, 更新利用者名, 更新端末ID
        ) VALUES (?, ?, ?, 1, ?, 'system', 'システム', 'backend_team', ?, 'system', 'システム', 'backend_team')
        """,
        [_採番ID, _採番初期値, "AIチーム改善の採番（TP）", now, now],
    )


def _新規改善ID(conn: sqlite3.Connection) -> str:
    _採番確保(conn)
    conn.execute(
        f'UPDATE "{_採番テーブル}" SET 最終採番値 = 最終採番値 + 1 WHERE 採番ID = ?',
        [_採番ID],
    )
    行 = conn.execute(
        f'SELECT 最終採番値 FROM "{_採番テーブル}" WHERE 採番ID = ?', [_採番ID]
    ).fetchone()
    return f"{_採番プレフィックス}{行[0]:08d}"


def 改善一覧(プロジェクト: str = "", 件数: int = 一覧最大件数) -> list[dict]:
    """改善の実行状況を新しい順で返す。"""
    初期化()
    conn = 接続取得()
    try:
        条件 = " WHERE プロジェクト = ?" if プロジェクト else ""
        params: list = [プロジェクト] if プロジェクト else []
        params.append(max(1, int(件数)))
        rows = conn.execute(
            f"""
            SELECT 改善ID, プロジェクト, ループ, 作業ID, チーム目標, 要員ID, PDCA区分, 状況,
                   開始日時, 終了日時, 応答内容, まとめ内容, 更新日時
              FROM "{改善テーブル}"{条件}
             ORDER BY 改善ID DESC
             LIMIT ?
            """,
            params,
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def 改善最大更新日時(プロジェクト: str = "") -> str:
    """一覧の再取得判定に使う最大更新日時を返す。"""
    初期化()
    conn = 接続取得()
    try:
        条件 = " WHERE プロジェクト = ?" if プロジェクト else ""
        row = conn.execute(
            f'SELECT MAX(更新日時) AS 最大更新日時 FROM "{改善テーブル}"{条件}',
            [プロジェクト] if プロジェクト else [],
        ).fetchone()
        return str(row["最大更新日時"] or "") if row else ""
    finally:
        conn.close()


def 未終了一覧(プロジェクト: str = "") -> list[dict]:
    """終了日時が入っていない（まだ実行中の）改善レコードを返す。"""
    初期化()
    conn = 接続取得()
    try:
        条件 = " AND プロジェクト = ?" if プロジェクト else ""
        rows = conn.execute(
            f"""
            SELECT 改善ID, プロジェクト, ループ, 作業ID, 要員ID, PDCA区分, 状況, 開始日時
              FROM "{改善テーブル}"
             WHERE 終了日時 = ''{条件}
             ORDER BY 改善ID
            """,
            [プロジェクト] if プロジェクト else [],
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def 最終区分(プロジェクト: str) -> str:
    """そのプロジェクトで最後に投入された PDCA区分を返す（レコードが無ければ空文字）。"""
    初期化()
    conn = 接続取得()
    try:
        row = conn.execute(
            f"""
            SELECT PDCA区分 FROM "{改善テーブル}"
             WHERE プロジェクト = ?
             ORDER BY 改善ID DESC
             LIMIT 1
            """,
            [プロジェクト],
        ).fetchone()
        return str(row["PDCA区分"] or "") if row else ""
    finally:
        conn.close()


def 最終段一覧(プロジェクト: str) -> list[dict]:
    """最後に投入された同一区分の連続レコードを、新しい順で返す。"""
    初期化()
    conn = 接続取得()
    try:
        rows = conn.execute(
            f"""
            SELECT 改善ID, プロジェクト, ループ, 作業ID, チーム目標, 要員ID, PDCA区分,
                   状況, 開始日時, 終了日時, 応答内容, まとめ内容, 更新日時
              FROM "{改善テーブル}"
             WHERE プロジェクト = ?
             ORDER BY 改善ID DESC
            """,
            [プロジェクト],
        ).fetchall()
        if not rows:
            return []
        最終区分値 = str(rows[0]["PDCA区分"] or "")
        結果: list[dict] = []
        for row in rows:
            if str(row["PDCA区分"] or "") != 最終区分値:
                break
            結果.append(dict(row))
        return 結果
    finally:
        conn.close()


def 次のPDCA区分(プロジェクト: str) -> str:
    """次に投入すべき PDCA区分を返す。投入できない場合は空文字を返す。

    - 未終了（終了日時が空）のレコードが1件でもあれば空文字（前の段がまだ終わっていない）
    - レコードが無ければ 'S'（相談から始める）
    - 直前の段が終わっていれば、その次の区分（'A' の次は 'S' に戻る）

    段が終わったかどうかは終了日時だけで判断する。状況は対応する Aチーム作業の状態を
    写した表示用の値で、「中止」「完了」など「済 / エラー」以外も入り得るため、
    ここで状況を条件にすると改善ループが永久に進めなくなる。
    """
    最終段 = 最終段一覧(プロジェクト)
    if not 最終段:
        return PDCA区分一覧[0]
    if 未終了一覧(プロジェクト):
        return ""
    直前 = str(最終段[0].get("PDCA区分", ""))
    if 直前 not in PDCA区分一覧:
        return PDCA区分一覧[0]
    次位置 = (PDCA区分一覧.index(直前) + 1) % len(PDCA区分一覧)
    return PDCA区分一覧[次位置]


def ループ最大値(プロジェクト: str) -> int:
    """プロジェクトに登録済みの最大ループ番号を返す。未登録なら0。"""
    初期化()
    conn = 接続取得()
    try:
        row = conn.execute(
            f'SELECT IFNULL(MAX(ループ), 0) AS 最大値 FROM "{改善テーブル}" WHERE プロジェクト = ?',
            [プロジェクト],
        ).fetchone()
        return int(row["最大値"] or 0) if row else 0
    finally:
        conn.close()


def ループ区分一覧(プロジェクト: str, ループ: int, PDCA区分: str) -> list[dict]:
    """指定したプロジェクト・ループ・PDCA区分の改善レコードを返す。"""
    初期化()
    conn = 接続取得()
    try:
        rows = conn.execute(
            f"""
            SELECT 改善ID, プロジェクト, ループ, 作業ID, チーム目標, 要員ID, PDCA区分,
                   状況, 開始日時, 終了日時, 応答内容, まとめ内容, 更新日時
              FROM "{改善テーブル}"
             WHERE プロジェクト = ? AND ループ = ? AND PDCA区分 = ?
             ORDER BY 改善ID
            """,
            [プロジェクト, int(ループ), PDCA区分],
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def 改善登録(データ: dict) -> dict:
    """PDCA 1段・1要員分の開始レコードを追加する（終了日時は空のまま）。"""
    初期化()
    now = _現在日時()
    監査 = _監査項目("system", "システム", "backend_team")
    conn = 接続取得()
    try:
        改善ID = _新規改善ID(conn)
        conn.execute(
            f"""
            INSERT INTO "{改善テーブル}" (
                改善ID, プロジェクト, ループ, 作業ID, チーム目標, 要員ID, PDCA区分, 状況,
                開始日時, 終了日時, 応答内容,
                登録日時, 登録利用者ID, 登録利用者名, 登録端末ID,
                更新日時, 更新利用者ID, 更新利用者名, 更新端末ID
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '', '', ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                改善ID,
                str(データ.get("プロジェクト", "")),
                max(0, int(データ.get("ループ", 0) or 0)),
                str(データ.get("作業ID", "")),
                str(データ.get("チーム目標", "")),
                str(データ.get("要員ID", "")),
                str(データ.get("PDCA区分", "")),
                str(データ.get("状況", "") or 初期状況),
                str(データ.get("開始日時", "") or now),
                監査["登録日時"], 監査["登録利用者ID"], 監査["登録利用者名"], 監査["登録端末ID"],
                監査["更新日時"], 監査["更新利用者ID"], 監査["更新利用者名"], 監査["更新端末ID"],
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return 改善取得(改善ID) or {}


def 単一計画upsert(Sレコード: dict) -> dict:
    """成功したSが1件だけのとき、AIを起動せず同じループの完了済みPを作成・更新する。"""
    初期化()
    now = _現在日時()
    監査 = _監査項目("system", "システム", "backend_team")
    プロジェクト = str(Sレコード.get("プロジェクト", ""))
    ループ = max(1, int(Sレコード.get("ループ", 0) or 0))
    conn = 接続取得()
    try:
        既存 = conn.execute(
            f"""
            SELECT 改善ID FROM "{改善テーブル}"
             WHERE プロジェクト = ? AND ループ = ? AND PDCA区分 = 'P'
             ORDER BY 改善ID DESC LIMIT 1
            """,
            [プロジェクト, ループ],
        ).fetchone()
        if 既存:
            改善ID = str(既存["改善ID"])
            conn.execute(
                f"""
                UPDATE "{改善テーブル}"
                   SET 作業ID = '', チーム目標 = ?, 要員ID = ?, 状況 = '済',
                       開始日時 = ?, 終了日時 = ?, 応答内容 = ?, まとめ内容 = ?,
                       更新日時 = ?, 更新利用者ID = 'system',
                       更新利用者名 = 'システム', 更新端末ID = 'backend_team'
                 WHERE 改善ID = ?
                """,
                [
                    str(Sレコード.get("チーム目標", "")),
                    str(Sレコード.get("要員ID", "")),
                    now,
                    now,
                    str(Sレコード.get("応答内容", "")),
                    str(Sレコード.get("まとめ内容", "")),
                    now,
                    改善ID,
                ],
            )
        else:
            改善ID = _新規改善ID(conn)
            conn.execute(
                f"""
                INSERT INTO "{改善テーブル}" (
                    改善ID, プロジェクト, ループ, 作業ID, チーム目標, 要員ID,
                    PDCA区分, 状況, 開始日時, 終了日時, 応答内容, まとめ内容,
                    登録日時, 登録利用者ID, 登録利用者名, 登録端末ID,
                    更新日時, 更新利用者ID, 更新利用者名, 更新端末ID
                ) VALUES (?, ?, ?, '', ?, ?, 'P', '済', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    改善ID,
                    プロジェクト,
                    ループ,
                    str(Sレコード.get("チーム目標", "")),
                    str(Sレコード.get("要員ID", "")),
                    now,
                    now,
                    str(Sレコード.get("応答内容", "")),
                    str(Sレコード.get("まとめ内容", "")),
                    監査["登録日時"],
                    監査["登録利用者ID"],
                    監査["登録利用者名"],
                    監査["登録端末ID"],
                    監査["更新日時"],
                    監査["更新利用者ID"],
                    監査["更新利用者名"],
                    監査["更新端末ID"],
                ],
            )
        conn.commit()
    finally:
        conn.close()
    return 改善取得(改善ID) or {}


def 改善取得(改善ID: str) -> dict | None:
    初期化()
    conn = 接続取得()
    try:
        row = conn.execute(
            f'SELECT * FROM "{改善テーブル}" WHERE 改善ID = ?', [改善ID]
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def 改善状況記録(改善ID: str, 状況: str) -> None:
    """未終了の改善レコードの状況だけを更新する（投入成功時など）。"""
    初期化()
    now = _現在日時()
    conn = 接続取得()
    try:
        conn.execute(
            f"""
            UPDATE "{改善テーブル}"
               SET 状況 = ?,
                   更新日時 = ?, 更新利用者ID = 'system',
                   更新利用者名 = 'システム', 更新端末ID = 'backend_team'
             WHERE 改善ID = ? AND 終了日時 = ''
            """,
            [状況, now, 改善ID],
        )
        conn.commit()
    finally:
        conn.close()


def 改善終了記録(改善ID: str, 応答内容: str, 状況: str = "エラー") -> None:
    """未終了の改善レコードを終了させる（backend_team 側の後始末用）。"""
    初期化()
    now = _現在日時()
    conn = 接続取得()
    try:
        conn.execute(
            f"""
            UPDATE "{改善テーブル}"
               SET 状況 = ?, 終了日時 = ?, 応答内容 = ?,
                   更新日時 = ?, 更新利用者ID = 'system',
                   更新利用者名 = 'システム', 更新端末ID = 'backend_team'
             WHERE 改善ID = ? AND 終了日時 = ''
            """,
            [状況, now, 応答内容[:4000], now, 改善ID],
        )
        conn.commit()
    finally:
        conn.close()


def 取り残し終了(プロジェクト: str = "") -> int:
    """Aチーム作業が既に終わっているのに未終了のままの改善レコードを閉じる。

    投入エラーやタイムアウトで Aチーム作業だけがエラー化された場合、改善レコードが
    未終了のまま残って次の段へ進めなくなる。それを毎分の確認で回収する。

    回収する対象は 2 種類ある。

    1. Aチーム作業が 済 / エラー / 中止 になっているもの
    2. Aチーム作業が「完了」のまま滞留しているもの
       完了は経験生成の待ち状態で、経験生成が終われば「済」へ進む（team_exp_db.経験本登録）。
       だが経験生成が失敗すると Aチーム経験だけがエラーになり、作業は完了、改善は
       終了日時が空のまま誰も閉じない。経験の再生成も走らない（経験対象一覧は
       経験レコードが無いものだけを拾うため）ので、ここで回収しないと改善ループが
       完全に止まる。経験がエラーで確定したもの、または完了滞留回収分を過ぎても
       済にならないものを対象にする。
    """
    初期化()
    now = _現在日時()
    滞留閾値 = (datetime.now() - timedelta(minutes=完了滞留回収分)).strftime("%Y-%m-%d %H:%M:%S")
    conn = 接続取得()
    try:
        条件 = " AND p.プロジェクト = ?" if プロジェクト else ""
        cursor = conn.execute(
            f"""
            UPDATE "{改善テーブル}"
               SET 状況 = IFNULL((
                       SELECT w.状態 FROM "{作業テーブル}" w
                        WHERE w.作業ID = "{改善テーブル}".作業ID
                   ), 状況),
                   終了日時 = ?,
                   応答内容 = CASE WHEN 応答内容 = '' THEN 'Aチーム作業が終了したため回収しました' ELSE 応答内容 END,
                   更新日時 = ?, 更新利用者ID = 'system',
                   更新利用者名 = 'システム', 更新端末ID = 'backend_team'
             WHERE 改善ID IN (
                   SELECT p.改善ID
                     FROM "{改善テーブル}" p
                     JOIN "{作業テーブル}" w ON w.作業ID = p.作業ID
                    WHERE p.終了日時 = ''
                      AND (
                          w.状態 IN ('済', 'エラー', '中止')
                          OR (
                              w.状態 = '完了'
                              AND (
                                  EXISTS (
                                      SELECT 1 FROM "{経験テーブル}" e
                                       WHERE e.作業ID = w.作業ID AND e.状態 = 'エラー'
                                  )
                                  OR w.更新日時 <= ?
                              )
                          )
                      ){条件}
             )
            """,
            [now, now, 滞留閾値, *([プロジェクト] if プロジェクト else [])],
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def 改善クリア(プロジェクト: str) -> int:
    """そのプロジェクトの改善記録をすべて削除する（改善ループのオン更新時）。"""
    初期化()
    conn = 接続取得()
    try:
        cursor = conn.execute(
            f'DELETE FROM "{改善テーブル}" WHERE プロジェクト = ?', [プロジェクト]
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()
