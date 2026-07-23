# -*- coding: utf-8 -*-

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "backend_server" / "_data" / "AiDiy" / "database.db"
TABLE_NAME = "Aチーム要員"
ADMIN_ID = "admin"


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def _create_audit(user_id: str, user_name: str, terminal_id: str) -> dict[str, str]:
    now = _now()
    return {
        "登録日時": now,
        "登録利用者ID": user_id,
        "登録利用者名": user_name,
        "登録端末ID": terminal_id,
        "更新日時": now,
        "更新利用者ID": user_id,
        "更新利用者名": user_name,
        "更新端末ID": terminal_id,
    }


def initialize() -> None:
    with _connect() as connection:
        connection.execute(f"""
            CREATE TABLE IF NOT EXISTS "{TABLE_NAME}" (
                要員ID TEXT NOT NULL PRIMARY KEY,
                要員名 TEXT NOT NULL,
                役割 TEXT NOT NULL DEFAULT '',
                人格情報 TEXT NOT NULL DEFAULT '',
                有効 INTEGER NOT NULL DEFAULT 1,
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
        connection.execute(f"""
            CREATE TRIGGER IF NOT EXISTS "Aチーム要員_admin削除禁止"
            BEFORE DELETE ON "{TABLE_NAME}"
            WHEN OLD.要員ID = '{ADMIN_ID}'
            BEGIN
                SELECT RAISE(ABORT, 'admin要員は削除できません');
            END
        """)
        connection.execute(f"""
            CREATE TRIGGER IF NOT EXISTS "Aチーム要員_admin無効化禁止"
            BEFORE UPDATE OF 有効 ON "{TABLE_NAME}"
            WHEN OLD.要員ID = '{ADMIN_ID}' AND NEW.有効 = 0
            BEGIN
                SELECT RAISE(ABORT, 'admin要員は無効化できません');
            END
        """)
        audit = _create_audit("system", "システム", "backend_team")
        connection.execute(
            f"""
            INSERT OR IGNORE INTO "{TABLE_NAME}" (
                要員ID, 要員名, 役割, 人格情報, 有効,
                登録日時, 登録利用者ID, 登録利用者名, 登録端末ID,
                更新日時, 更新利用者ID, 更新利用者名, 更新端末ID
            ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ADMIN_ID, "admin", "チーム管理者", "チーム全体を見守り、必要に応じて調整する。",
                audit["登録日時"], audit["登録利用者ID"], audit["登録利用者名"], audit["登録端末ID"],
                audit["更新日時"], audit["更新利用者ID"], audit["更新利用者名"], audit["更新端末ID"],
            ),
        )
        connection.commit()


def list_members(include_disabled: bool = False) -> list[dict]:
    initialize()
    sql = f'SELECT * FROM "{TABLE_NAME}"'
    params: list = []
    if not include_disabled:
        sql += " WHERE 有効 = ?"
        params.append(1)
    sql += " ORDER BY CASE WHEN 要員ID = 'admin' THEN 0 ELSE 1 END, 要員ID"
    with _connect() as connection:
        return [dict(row) for row in connection.execute(sql, params).fetchall()]


def get_member(member_id: str) -> dict | None:
    initialize()
    with _connect() as connection:
        row = connection.execute(
            f'SELECT * FROM "{TABLE_NAME}" WHERE 要員ID = ?', [member_id]
        ).fetchone()
        return dict(row) if row else None


def create_member(data: dict, operator: dict) -> dict:
    initialize()
    audit = _create_audit(operator["利用者ID"], operator["利用者名"], operator["端末ID"])
    with _connect() as connection:
        try:
            connection.execute(
                f"""
                INSERT INTO "{TABLE_NAME}" (
                    要員ID, 要員名, 役割, 人格情報, 有効,
                    登録日時, 登録利用者ID, 登録利用者名, 登録端末ID,
                    更新日時, 更新利用者ID, 更新利用者名, 更新端末ID
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["要員ID"], data["要員名"], data["役割"], data["人格情報"], int(data["有効"]),
                    audit["登録日時"], audit["登録利用者ID"], audit["登録利用者名"], audit["登録端末ID"],
                    audit["更新日時"], audit["更新利用者ID"], audit["更新利用者名"], audit["更新端末ID"],
                ),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("同じ要員IDが既に登録されています") from exc
    return get_member(data["要員ID"]) or {}


def update_member(data: dict, operator: dict) -> dict:
    initialize()
    if data["要員ID"] == ADMIN_ID and not data["有効"]:
        raise ValueError("admin要員は無効化できません")
    if get_member(data["要員ID"]) is None:
        raise KeyError(data["要員ID"])
    now = _now()
    with _connect() as connection:
        connection.execute(
            f"""
            UPDATE "{TABLE_NAME}"
               SET 要員名 = ?, 役割 = ?, 人格情報 = ?, 有効 = ?,
                   更新日時 = ?, 更新利用者ID = ?, 更新利用者名 = ?, 更新端末ID = ?
             WHERE 要員ID = ?
            """,
            (
                data["要員名"], data["役割"], data["人格情報"], int(data["有効"]),
                now, operator["利用者ID"], operator["利用者名"], operator["端末ID"], data["要員ID"],
            ),
        )
        connection.commit()
    return get_member(data["要員ID"]) or {}


def upsert_persona_member(data: dict, operator: dict) -> dict:
    """召喚時にpersonaの現在値で要員を登録または更新し、有効化する。"""
    initialize()
    audit = _create_audit(operator["利用者ID"], operator["利用者名"], operator["端末ID"])
    with _connect() as connection:
        connection.execute(
            f"""
            INSERT INTO "{TABLE_NAME}" (
                要員ID, 要員名, 役割, 人格情報, 有効,
                登録日時, 登録利用者ID, 登録利用者名, 登録端末ID,
                更新日時, 更新利用者ID, 更新利用者名, 更新端末ID
            ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(要員ID) DO UPDATE SET
                要員名 = excluded.要員名,
                役割 = excluded.役割,
                人格情報 = excluded.人格情報,
                有効 = 1,
                更新日時 = excluded.更新日時,
                更新利用者ID = excluded.更新利用者ID,
                更新利用者名 = excluded.更新利用者名,
                更新端末ID = excluded.更新端末ID
            """,
            (
                data["要員ID"], data["要員名"], data["役割"], data["人格情報"],
                audit["登録日時"], audit["登録利用者ID"], audit["登録利用者名"], audit["登録端末ID"],
                audit["更新日時"], audit["更新利用者ID"], audit["更新利用者名"], audit["更新端末ID"],
            ),
        )
        connection.commit()
    return get_member(data["要員ID"]) or {}


def disable_member(member_id: str, operator: dict) -> dict:
    """排除時に要員行を残したまま無効化する。"""
    initialize()
    if member_id == ADMIN_ID:
        raise ValueError("admin要員は排除できません")
    now = _now()
    with _connect() as connection:
        cursor = connection.execute(
            f"""
            UPDATE "{TABLE_NAME}"
               SET 有効 = 0,
                   更新日時 = ?, 更新利用者ID = ?, 更新利用者名 = ?, 更新端末ID = ?
             WHERE 要員ID = ?
            """,
            (
                now,
                operator["利用者ID"],
                operator["利用者名"],
                operator["端末ID"],
                member_id,
            ),
        )
        if cursor.rowcount == 0:
            raise KeyError(member_id)
        connection.commit()
    return get_member(member_id) or {}


def delete_member(member_id: str) -> None:
    initialize()
    if member_id == ADMIN_ID:
        raise ValueError("admin要員は削除できません")
    with _connect() as connection:
        cursor = connection.execute(f'DELETE FROM "{TABLE_NAME}" WHERE 要員ID = ?', [member_id])
        if cursor.rowcount == 0:
            raise KeyError(member_id)
        connection.commit()
