# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""Aチーム目標の DB アクセス。

CODE_BASE_PATH（プロジェクトのパス）ごとにチーム目標を 1 件保持する。
画面（AIチーム空間の掲示板）は更新日時が最新の 1 件を表示する。
"""

from __future__ import annotations

import sqlite3
from datetime import datetime

from .team_db import DB_PATH, 接続取得

目標テーブル = "Aチーム目標"
既定CODE_BASE_PATH = "../"
既定チーム目標 = "よく考えて、行うべきことを実行する。"


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


def _次の更新連番(conn: sqlite3.Connection) -> int:
    """更新日時は秒単位のため、同じ秒に複数保存されても順序が決まるよう連番を採る。"""
    row = conn.execute(f'SELECT IFNULL(MAX(更新連番), 0) + 1 AS 次 FROM "{目標テーブル}"').fetchone()
    return int(row["次"]) if row else 1


def 初期化() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = 接続取得()
    try:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS "{目標テーブル}" (
                CODE_BASE_PATH TEXT NOT NULL PRIMARY KEY,
                チーム目標 TEXT NOT NULL DEFAULT '',
                更新連番 INTEGER NOT NULL DEFAULT 0,
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
        conn.commit()
    finally:
        conn.close()


def 初期目標を投入() -> None:
    """起動時、1 件も無ければ既定のパスと目標を投入する（既存値は上書きしない）。"""
    初期化()
    conn = 接続取得()
    try:
        監査 = _監査項目("system", "システム", "backend_team")
        conn.execute(
            f"""
            INSERT OR IGNORE INTO "{目標テーブル}" (
                CODE_BASE_PATH, チーム目標, 更新連番,
                登録日時, 登録利用者ID, 登録利用者名, 登録端末ID,
                更新日時, 更新利用者ID, 更新利用者名, 更新端末ID
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                既定CODE_BASE_PATH, 既定チーム目標, _次の更新連番(conn),
                監査["登録日時"], 監査["登録利用者ID"], 監査["登録利用者名"], 監査["登録端末ID"],
                監査["更新日時"], 監査["更新利用者ID"], 監査["更新利用者名"], 監査["更新端末ID"],
            ),
        )
        conn.commit()
    finally:
        conn.close()


def 目標一覧() -> list[dict]:
    """登録済みのパスと目標を、更新日時の新しい順で返す。"""
    初期化()
    conn = 接続取得()
    try:
        rows = conn.execute(
            f"""
            SELECT CODE_BASE_PATH, チーム目標, 更新日時, 更新利用者ID, 更新利用者名
              FROM "{目標テーブル}"
             ORDER BY 更新日時 DESC, 更新連番 DESC, CODE_BASE_PATH
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def 目標取得(code_base_path: str) -> dict | None:
    初期化()
    conn = 接続取得()
    try:
        row = conn.execute(
            f"""
            SELECT CODE_BASE_PATH, チーム目標, 更新日時, 更新利用者ID, 更新利用者名
              FROM "{目標テーブル}" WHERE CODE_BASE_PATH = ?
            """,
            [code_base_path],
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def 最終目標取得() -> dict | None:
    """更新日時が最新の 1 件を返す（掲示板に出す値）。"""
    初期化()
    conn = 接続取得()
    try:
        row = conn.execute(
            f"""
            SELECT CODE_BASE_PATH, チーム目標, 更新日時, 更新利用者ID, 更新利用者名
              FROM "{目標テーブル}"
             ORDER BY 更新日時 DESC, 更新連番 DESC, CODE_BASE_PATH
             LIMIT 1
            """
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def 目標保存(code_base_path: str, チーム目標: str, 操作者: dict) -> dict:
    """パス単位の upsert。既存があれば目標と更新監査のみ書き換える。"""
    初期化()
    監査 = _監査項目(操作者["利用者ID"], 操作者["利用者名"], 操作者["端末ID"])
    conn = 接続取得()
    try:
        conn.execute(
            f"""
            INSERT INTO "{目標テーブル}" (
                CODE_BASE_PATH, チーム目標, 更新連番,
                登録日時, 登録利用者ID, 登録利用者名, 登録端末ID,
                更新日時, 更新利用者ID, 更新利用者名, 更新端末ID
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(CODE_BASE_PATH) DO UPDATE SET
                チーム目標 = excluded.チーム目標,
                更新連番 = excluded.更新連番,
                更新日時 = excluded.更新日時,
                更新利用者ID = excluded.更新利用者ID,
                更新利用者名 = excluded.更新利用者名,
                更新端末ID = excluded.更新端末ID
            """,
            (
                code_base_path, チーム目標, _次の更新連番(conn),
                監査["登録日時"], 監査["登録利用者ID"], 監査["登録利用者名"], 監査["登録端末ID"],
                監査["更新日時"], 監査["更新利用者ID"], 監査["更新利用者名"], 監査["更新端末ID"],
            ),
        )
        conn.commit()
    except sqlite3.Error as exc:
        raise ValueError(f"チーム目標の保存に失敗しました: {exc}") from exc
    finally:
        conn.close()
    return 目標取得(code_base_path) or {}


def 目標削除(code_base_path: str) -> None:
    """既定パス（../）は残す。削除対象が無ければ KeyError。"""
    初期化()
    if code_base_path == 既定CODE_BASE_PATH:
        raise ValueError(f"{既定CODE_BASE_PATH} のチーム目標は削除できません")
    conn = 接続取得()
    try:
        cursor = conn.execute(
            f'DELETE FROM "{目標テーブル}" WHERE CODE_BASE_PATH = ?', [code_base_path]
        )
        if cursor.rowcount == 0:
            raise KeyError(code_base_path)
        conn.commit()
    finally:
        conn.close()
