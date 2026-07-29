# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""Aチーム会話の DB アクセス（参照専用。登録経路は別途追加予定）。"""

from __future__ import annotations

from .team_db import DB_PATH, 接続取得

会話テーブル = "Aチーム会話"
一覧最大件数 = 100


def 初期化() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = 接続取得()
    try:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS "{会話テーブル}" (
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
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS "IX_Aチーム会話_プロジェクト"
            ON "{会話テーブル}" (プロジェクト, 会話ID)
        """)
        conn.commit()
    finally:
        conn.close()


def 会話一覧(プロジェクト: str = "", 件数: int = 一覧最大件数) -> list[dict]:
    """会話を新しい順で返す。"""
    初期化()
    conn = 接続取得()
    try:
        条件 = " WHERE プロジェクト = ?" if プロジェクト else ""
        params: list = [プロジェクト] if プロジェクト else []
        params.append(max(1, int(件数)))
        rows = conn.execute(
            f"""
            SELECT 会話ID, プロジェクト, 要員ID, 要求内容, 発言内容, 登録日時, 更新日時
              FROM "{会話テーブル}"{条件}
             ORDER BY 会話ID DESC
             LIMIT ?
            """,
            params,
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def 会話最大更新日時(プロジェクト: str = "") -> str:
    """一覧の再取得判定に使う最大更新日時を返す。"""
    初期化()
    conn = 接続取得()
    try:
        条件 = " WHERE プロジェクト = ?" if プロジェクト else ""
        row = conn.execute(
            f'SELECT MAX(更新日時) AS 最大更新日時 FROM "{会話テーブル}"{条件}',
            [プロジェクト] if プロジェクト else [],
        ).fetchone()
        return str(row["最大更新日時"] or "") if row else ""
    finally:
        conn.close()
