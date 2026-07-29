# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""Aチーム会話の DB アクセス。

雑談エリアの要員から選んだ1名の発言を、team_watcher.py の1分ごとの確認（雑談確認）から
sub_hatugen.py 経由で書き込む。登録経路はこれのみで、フロントエンドからの直接登録は無い。
"""

from __future__ import annotations

import sqlite3
from datetime import datetime

from .team_db import DB_PATH, 接続取得

会話テーブル = "Aチーム会話"
一覧最大件数 = 100

_採番テーブル = "C採番"
_採番ID = "Aチーム会話"
_採番プレフィックス = "TC"
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


def _採番確保(conn: sqlite3.Connection) -> None:
    """C採番（backend_server共有）にAチーム会話用の採番行が無ければ作成する。"""
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
        [_採番ID, _採番初期値, "AIチーム会話の採番（TC）", now, now],
    )


def _新規会話ID(conn: sqlite3.Connection) -> str:
    _採番確保(conn)
    conn.execute(
        f'UPDATE "{_採番テーブル}" SET 最終採番値 = 最終採番値 + 1 WHERE 採番ID = ?',
        [_採番ID],
    )
    行 = conn.execute(
        f'SELECT 最終採番値 FROM "{_採番テーブル}" WHERE 採番ID = ?', [_採番ID]
    ).fetchone()
    return f"{_採番プレフィックス}{行[0]:08d}"


def 起動時クリア() -> int:
    """backend_team 起動時、Aチーム会話を全件削除する（会話はその場限りの表示用のため引き継がない）。"""
    初期化()
    conn = 接続取得()
    try:
        cursor = conn.execute(f'DELETE FROM "{会話テーブル}"')
        conn.commit()
        return max(0, int(cursor.rowcount))
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


def 会話取得(会話ID: str) -> dict | None:
    初期化()
    conn = 接続取得()
    try:
        row = conn.execute(
            f'SELECT * FROM "{会話テーブル}" WHERE 会話ID = ?', [会話ID]
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def 発言状況一覧(プロジェクト: str) -> dict[str, str]:
    """要員IDごとの最終発言日時（発言内容が入っている行の登録日時）を返す。

    team_watcher.py の雑談確認が、次の発言者（未発言優先、全員発言済みなら最古の発言者）を
    選ぶために使う。空の発言（発言シーケンスに入っただけの行）は対象にしない。
    """
    初期化()
    conn = 接続取得()
    try:
        rows = conn.execute(
            f"""
            SELECT 要員ID, MAX(登録日時) AS 最終発言日時
              FROM "{会話テーブル}"
             WHERE プロジェクト = ? AND 発言内容 != ''
             GROUP BY 要員ID
            """,
            [プロジェクト],
        ).fetchall()
        return {str(row["要員ID"]): str(row["最終発言日時"]) for row in rows}
    finally:
        conn.close()


def 最新発言一覧(プロジェクト: str) -> list[dict]:
    """要員ごとの最新の発言（会話IDが最大のもの）を返す。「他者意見」として次の発言者へ渡す。"""
    初期化()
    conn = 接続取得()
    try:
        rows = conn.execute(
            f"""
            SELECT t1.会話ID, t1.要員ID, t1.要求内容, t1.発言内容, t1.登録日時
              FROM "{会話テーブル}" t1
              INNER JOIN (
                  SELECT 要員ID, MAX(会話ID) AS 最大会話ID
                    FROM "{会話テーブル}"
                   WHERE プロジェクト = ? AND 発言内容 != ''
                   GROUP BY 要員ID
              ) t2 ON t1.要員ID = t2.要員ID AND t1.会話ID = t2.最大会話ID
             WHERE t1.プロジェクト = ?
             ORDER BY t1.会話ID DESC
            """,
            [プロジェクト, プロジェクト],
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def 発言登録(プロジェクト: str, 要員ID: str, 操作者: dict) -> dict:
    """発言シーケンスに入ったことを示す空の会話行を追加する（要求内容・発言内容はあとで発言更新が書く）。"""
    初期化()
    監査 = _監査項目(操作者["利用者ID"], 操作者["利用者名"], 操作者["端末ID"])
    conn = 接続取得()
    try:
        会話ID = _新規会話ID(conn)
        conn.execute(
            f"""
            INSERT INTO "{会話テーブル}" (
                会話ID, プロジェクト, 要員ID, 要求内容, 発言内容,
                登録日時, 登録利用者ID, 登録利用者名, 登録端末ID,
                更新日時, 更新利用者ID, 更新利用者名, 更新端末ID
            ) VALUES (?, ?, ?, '', '', ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                会話ID, プロジェクト, 要員ID,
                監査["登録日時"], 監査["登録利用者ID"], 監査["登録利用者名"], 監査["登録端末ID"],
                監査["更新日時"], 監査["更新利用者ID"], 監査["更新利用者名"], 監査["更新端末ID"],
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return 会話取得(会話ID) or {}


def 発言更新(会話ID: str, 要求内容: str, 発言内容: str) -> None:
    """発言登録で作った行へ、実際に送った依頼内容と発言内容を書き戻す（sub_hatugen.py の結果）。"""
    初期化()
    now = _現在日時()
    conn = 接続取得()
    try:
        conn.execute(
            f"""
            UPDATE "{会話テーブル}"
               SET 要求内容 = ?, 発言内容 = ?,
                   更新日時 = ?, 更新利用者ID = 'system',
                   更新利用者名 = 'システム', 更新端末ID = 'backend_team'
             WHERE 会話ID = ?
            """,
            [要求内容, 発言内容, now, 会話ID],
        )
        conn.commit()
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
