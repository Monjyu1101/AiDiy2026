# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""Aチーム状況の読取専用アクセス。

Aチーム状況は backend_task 側（実行開始条件の監視ループ、10秒間隔）が
有効なAチーム要員×実行有効なAタスク要求（24時間以内更新）を要員IDで集計して
作り直しているテーブル。backend_team はここでは読み取るだけで、書き込みは行わない。
"""

from __future__ import annotations

import sqlite3

from .team_db import DB_PATH

状況テーブル = "Aチーム状況"


def 接続取得() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def _テーブル確保(conn: sqlite3.Connection) -> None:
    """backend_task がまだ一度も更新していない場合に備え、空テーブルとして用意する。"""
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS "{状況テーブル}" (
            要員ID TEXT NOT NULL PRIMARY KEY,
            要員名 TEXT NOT NULL DEFAULT '',
            最終更新日時 TEXT NOT NULL DEFAULT '',
            経験最終更新日時 TEXT NOT NULL DEFAULT '',
            待機数 INTEGER NOT NULL DEFAULT 0,
            実行数 INTEGER NOT NULL DEFAULT 0,
            まとめ中数 INTEGER NOT NULL DEFAULT 0,
            完了数 INTEGER NOT NULL DEFAULT 0,
            エラー数 INTEGER NOT NULL DEFAULT 0,
            更新日時 TEXT NOT NULL DEFAULT ''
        )
    """)
    既存列 = {row["name"] for row in conn.execute(f'PRAGMA table_info("{状況テーブル}")')}
    if "まとめ中数" not in 既存列:
        conn.execute(
            f'ALTER TABLE "{状況テーブル}" ADD COLUMN まとめ中数 INTEGER NOT NULL DEFAULT 0'
        )
    if "経験最終更新日時" not in 既存列:
        conn.execute(
            f'ALTER TABLE "{状況テーブル}" ADD COLUMN 経験最終更新日時 TEXT NOT NULL DEFAULT \'\''
        )
    conn.commit()


def 実行中要員数() -> int:
    """実行数（準備中・実行中のAタスク要求）が1件以上ある要員の人数を返す。

    0 ならチーム全体が空き時間と判断できる（改善ループの投入条件）。
    """
    conn = 接続取得()
    try:
        _テーブル確保(conn)
        row = conn.execute(
            f'SELECT COUNT(*) AS 人数 FROM "{状況テーブル}" WHERE 実行数 > 0'
        ).fetchone()
        return int(row["人数"]) if row else 0
    finally:
        conn.close()


def 状況一覧() -> list[dict]:
    conn = 接続取得()
    try:
        _テーブル確保(conn)
        rows = conn.execute(
            f'SELECT 要員ID, 要員名, 最終更新日時, 経験最終更新日時, '
            f'待機数, 実行数, まとめ中数, 完了数, エラー数, 更新日時 '
            f'FROM "{状況テーブル}" ORDER BY 要員ID'
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def 状況最大更新日時() -> str:
    """一覧の再取得判定に使う最大更新日時を返す。"""
    conn = 接続取得()
    try:
        _テーブル確保(conn)
        row = conn.execute(
            f'SELECT MAX(更新日時) AS 最大更新日時 FROM "{状況テーブル}"'
        ).fetchone()
        return str(row["最大更新日時"] or "") if row else ""
    finally:
        conn.close()
