# -*- coding: utf-8 -*-

from __future__ import annotations

import sqlite3
from datetime import datetime

from .team_db import DB_PATH

TABLE_NAME = "Aチーム作業"
状態一覧 = ("準備開始", "準備中", "準備完了", "待機", "実行中", "エラー", "完了", "中止")
状態入力一覧 = 状態一覧


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def initialize() -> None:
    with _connect() as connection:
        connection.execute(f"""
            CREATE TABLE IF NOT EXISTS "{TABLE_NAME}" (
                利用者ID TEXT NOT NULL,
                作業ID TEXT NOT NULL,
                プロジェクト TEXT NOT NULL DEFAULT '',
                タイトル TEXT NOT NULL DEFAULT '',
                要求内容 TEXT NOT NULL DEFAULT '',
                TEAM_AI_NAME TEXT NOT NULL DEFAULT 'claude_cli',
                TEAM_AI_MODEL TEXT NOT NULL DEFAULT 'auto',
                TASK_AI_NAME TEXT NOT NULL DEFAULT 'claude_cli',
                TASK_AI_MODEL TEXT NOT NULL DEFAULT 'auto',
                タスクID TEXT NOT NULL DEFAULT '',
                実行有効 INTEGER NOT NULL DEFAULT 1,
                状態 TEXT NOT NULL DEFAULT '準備開始',
                PID TEXT NOT NULL DEFAULT '',
                開始日時 TEXT NOT NULL DEFAULT '',
                終了日時 TEXT NOT NULL DEFAULT '',
                実行回数 INTEGER NOT NULL DEFAULT 0,
                応答タイトル TEXT NOT NULL DEFAULT '',
                応答内容 TEXT NOT NULL DEFAULT '',
                登録日時 TEXT NOT NULL,
                登録利用者ID TEXT NOT NULL,
                登録利用者名 TEXT NOT NULL,
                登録端末ID TEXT NOT NULL,
                更新日時 TEXT NOT NULL,
                更新利用者ID TEXT NOT NULL,
                更新利用者名 TEXT NOT NULL,
                更新端末ID TEXT NOT NULL,
                PRIMARY KEY (利用者ID, 作業ID)
            )
        """)
        columns = {
            row[1]
            for row in connection.execute(f'PRAGMA table_info("{TABLE_NAME}")').fetchall()
        }
        if "TASK_AI_NAME" not in columns:
            connection.execute(
                f'ALTER TABLE "{TABLE_NAME}" ADD COLUMN TASK_AI_NAME TEXT NOT NULL DEFAULT \'claude_cli\''
            )
            connection.execute(f'UPDATE "{TABLE_NAME}" SET TASK_AI_NAME = TEAM_AI_NAME')
        if "TASK_AI_MODEL" not in columns:
            connection.execute(
                f'ALTER TABLE "{TABLE_NAME}" ADD COLUMN TASK_AI_MODEL TEXT NOT NULL DEFAULT \'auto\''
            )
            connection.execute(f'UPDATE "{TABLE_NAME}" SET TASK_AI_MODEL = TEAM_AI_MODEL')
        if "タスクID" not in columns:
            connection.execute(
                f'ALTER TABLE "{TABLE_NAME}" ADD COLUMN タスクID TEXT NOT NULL DEFAULT \'\''
            )
        connection.execute(f"""
            CREATE INDEX IF NOT EXISTS "IX_Aチーム作業_状態"
            ON "{TABLE_NAME}" (利用者ID, 状態, 作業ID)
        """)
        connection.commit()


def _new_work_id(connection: sqlite3.Connection, user_id: str) -> str:
    base_id = datetime.now().strftime("TEAM.%m%d.%H%M%S")
    work_id = base_id
    suffix = 0
    while connection.execute(
        f'SELECT 1 FROM "{TABLE_NAME}" WHERE 利用者ID = ? AND 作業ID = ?',
        [user_id, work_id],
    ).fetchone():
        suffix += 1
        work_id = f"{base_id}.{suffix:02d}"
    return work_id


def _title(request_content: str) -> str:
    return request_content.splitlines()[0][:40] if request_content else ""


def list_works(user_id: str) -> list[dict]:
    initialize()
    with _connect() as connection:
        rows = connection.execute(
            f"""
            SELECT 利用者ID, 作業ID, プロジェクト, タイトル, 要求内容,
                   TEAM_AI_NAME, TEAM_AI_MODEL, TASK_AI_NAME, TASK_AI_MODEL, タスクID,
                   実行有効, 状態, PID,
                   開始日時, 終了日時, 実行回数, 応答タイトル, 応答内容, 更新日時
              FROM "{TABLE_NAME}"
             WHERE 利用者ID = ?
             ORDER BY 作業ID DESC
            """,
            [user_id],
        ).fetchall()
        return [dict(row) for row in rows]


def max_updated_at(user_id: str) -> str:
    initialize()
    with _connect() as connection:
        row = connection.execute(
            f'SELECT MAX(更新日時) AS 最大更新日時 FROM "{TABLE_NAME}" WHERE 利用者ID = ?',
            [user_id],
        ).fetchone()
        return str(row["最大更新日時"] or "") if row else ""


def get_work(user_id: str, work_id: str) -> dict | None:
    initialize()
    with _connect() as connection:
        row = connection.execute(
            f"""
            SELECT 利用者ID, 作業ID, プロジェクト, タイトル, 要求内容,
                   TEAM_AI_NAME, TEAM_AI_MODEL, TASK_AI_NAME, TASK_AI_MODEL, タスクID,
                   実行有効, 状態, PID,
                   開始日時, 終了日時, 実行回数, 応答タイトル, 応答内容, 更新日時
              FROM "{TABLE_NAME}"
             WHERE 利用者ID = ? AND 作業ID = ?
            """,
            [user_id, work_id],
        ).fetchone()
        return dict(row) if row else None


def create_work(data: dict, operator: dict) -> dict:
    initialize()
    now = _now()
    with _connect() as connection:
        work_id = _new_work_id(connection, data["利用者ID"])
        connection.execute(
            f"""
            INSERT INTO "{TABLE_NAME}" (
                利用者ID, 作業ID, プロジェクト, タイトル, 要求内容,
                TEAM_AI_NAME, TEAM_AI_MODEL, TASK_AI_NAME, TASK_AI_MODEL, タスクID,
                実行有効, 状態,
                PID, 開始日時, 終了日時, 実行回数, 応答タイトル, 応答内容,
                登録日時, 登録利用者ID, 登録利用者名, 登録端末ID,
                更新日時, 更新利用者ID, 更新利用者名, 更新端末ID
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, '', ?, ?,
                '', '', '', 0, '', '',
                ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                data["利用者ID"],
                work_id,
                data["プロジェクト"],
                _title(data["要求内容"]),
                data["要求内容"],
                data["TEAM_AI_NAME"],
                data["TEAM_AI_MODEL"],
                data["TASK_AI_NAME"],
                data["TASK_AI_MODEL"],
                int(data["実行有効"]),
                data["状態"],
                now,
                operator["利用者ID"],
                operator["利用者名"],
                operator["端末ID"],
                now,
                operator["利用者ID"],
                operator["利用者名"],
                operator["端末ID"],
            ),
        )
        connection.commit()
    return get_work(data["利用者ID"], work_id) or {}


def update_work(data: dict, operator: dict) -> dict:
    initialize()
    if data["状態"] not in 状態一覧:
        raise ValueError("状態が正しくありません")
    current = get_work(data["利用者ID"], data["作業ID"])
    if current is None:
        raise KeyError(data["作業ID"])
    now = _now()
    task_id = str(current["タスクID"] or "")
    pid = str(current["PID"] or "")
    start_at = str(current["開始日時"] or "")
    end_at = str(current["終了日時"] or "")
    run_count = int(current["実行回数"] or 0)
    response_title = str(current["応答タイトル"] or "")
    response_content = str(current["応答内容"] or "")
    if data["状態"] == "準備開始":
        task_id = ""
        pid = ""
        start_at = ""
        end_at = ""
        run_count = 0
        response_title = ""
        response_content = ""
    if data["状態"] == "実行中" and not start_at:
        start_at = now
    if data["状態"] in ("完了", "中止"):
        end_at = now
    elif data["状態"] == "待機":
        end_at = ""
    with _connect() as connection:
        connection.execute(
            f"""
            UPDATE "{TABLE_NAME}"
               SET プロジェクト = ?, タイトル = ?, 要求内容 = ?,
                   TEAM_AI_NAME = ?, TEAM_AI_MODEL = ?,
                   TASK_AI_NAME = ?, TASK_AI_MODEL = ?,
                   実行有効 = ?, 状態 = ?,
                   タスクID = ?, PID = ?, 開始日時 = ?, 終了日時 = ?,
                   実行回数 = ?, 応答タイトル = ?, 応答内容 = ?,
                   更新日時 = ?, 更新利用者ID = ?, 更新利用者名 = ?, 更新端末ID = ?
             WHERE 利用者ID = ? AND 作業ID = ?
            """,
            (
                data["プロジェクト"],
                _title(data["要求内容"]),
                data["要求内容"],
                data["TEAM_AI_NAME"],
                data["TEAM_AI_MODEL"],
                data["TASK_AI_NAME"],
                data["TASK_AI_MODEL"],
                int(data["実行有効"]),
                data["状態"],
                task_id,
                pid,
                start_at,
                end_at,
                run_count,
                response_title,
                response_content,
                now,
                operator["利用者ID"],
                operator["利用者名"],
                operator["端末ID"],
                data["利用者ID"],
                data["作業ID"],
            ),
        )
        connection.commit()
    return get_work(data["利用者ID"], data["作業ID"]) or {}


def preparing_works() -> list[dict]:
    """準備開始かつ未投入で、sub_initによるAIタスク登録を待つ作業を返す。"""
    initialize()
    with _connect() as connection:
        rows = connection.execute(
            f"""
            SELECT 利用者ID, 作業ID, プロジェクト, タイトル, 要求内容,
                   TEAM_AI_NAME, TEAM_AI_MODEL, TASK_AI_NAME, TASK_AI_MODEL,
                   実行有効, 状態, PID, 実行回数
              FROM "{TABLE_NAME}"
             WHERE 状態 = '準備開始'
               AND PID = ''
               AND タスクID = ''
             ORDER BY 作業ID
            """
        ).fetchall()
        return [dict(row) for row in rows]


def claim_work(user_id: str, work_id: str) -> bool:
    """準備開始の1件を準備中へ進めて確保し、sub_initの二重起動を防ぐ。"""
    initialize()
    now = _now()
    with _connect() as connection:
        cursor = connection.execute(
            f"""
            UPDATE "{TABLE_NAME}"
               SET 状態 = '準備中', PID = 'CLAIM',
                   開始日時 = ?, 終了日時 = '', 実行回数 = 実行回数 + 1,
                   応答タイトル = '', 応答内容 = '',
                   更新日時 = ?, 更新利用者ID = 'system',
                   更新利用者名 = 'システム', 更新端末ID = 'backend_team'
             WHERE 利用者ID = ? AND 作業ID = ?
               AND 状態 = '準備開始'
               AND PID = ''
               AND タスクID = ''
            """,
            [now, now, user_id, work_id],
        )
        connection.commit()
        return cursor.rowcount == 1


def record_process_pid(user_id: str, work_id: str, pid: int) -> None:
    """CLAIM中の作業へsub_initのPIDを記録する。先に完了した場合は上書きしない。"""
    now = _now()
    with _connect() as connection:
        connection.execute(
            f"""
            UPDATE "{TABLE_NAME}"
               SET PID = ?, 更新日時 = ?
             WHERE 利用者ID = ? AND 作業ID = ?
               AND 状態 = '準備中' AND PID = 'CLAIM'
            """,
            [str(pid), now, user_id, work_id],
        )
        connection.commit()


def record_submission_success(user_id: str, work_id: str, task_id: str) -> None:
    """aidiy_task_agentsへの投入成功を作業行へ反映する。"""
    now = _now()
    with _connect() as connection:
        cursor = connection.execute(
            f"""
            UPDATE "{TABLE_NAME}"
               SET タスクID = ?, 状態 = '準備完了', PID = '',
                   応答タイトル = 'AIタスク投入済み',
                   更新日時 = ?, 更新利用者ID = 'system',
                   更新利用者名 = 'システム', 更新端末ID = 'backend_team'
             WHERE 利用者ID = ? AND 作業ID = ? AND 状態 = '準備中'
            """,
            [task_id, now, user_id, work_id],
        )
        if cursor.rowcount != 1:
            raise KeyError(work_id)
        connection.commit()


def record_submission_failure(user_id: str, work_id: str, message: str) -> None:
    """sub_initの起動またはタスク投入失敗をエラーとして記録する。"""
    now = _now()
    with _connect() as connection:
        connection.execute(
            f"""
            UPDATE "{TABLE_NAME}"
               SET 状態 = 'エラー', PID = '', 終了日時 = ?,
                   応答タイトル = 'AIタスク投入エラー', 応答内容 = ?,
                   更新日時 = ?, 更新利用者ID = 'system',
                   更新利用者名 = 'システム', 更新端末ID = 'backend_team'
             WHERE 利用者ID = ? AND 作業ID = ?
               AND (状態 = '準備中' OR PID != '')
            """,
            [now, message[:2000], now, user_id, work_id],
        )
        connection.commit()


def active_processes() -> list[dict]:
    """再起動時に整理するsub_init PIDを返す。"""
    initialize()
    with _connect() as connection:
        rows = connection.execute(
            f"""
            SELECT 利用者ID, 作業ID, PID
              FROM "{TABLE_NAME}"
             WHERE PID != ''
            """
        ).fetchall()
        return [dict(row) for row in rows]


def reset_active_processes() -> int:
    """残存sub_initを準備開始へ戻し、次回監視で再実行できるようにする。"""
    now = _now()
    with _connect() as connection:
        cursor = connection.execute(
            f"""
            UPDATE "{TABLE_NAME}"
               SET 状態 = '準備開始', PID = '', 開始日時 = '', 終了日時 = '',
                   更新日時 = ?, 更新利用者ID = 'system',
                   更新利用者名 = 'システム', 更新端末ID = 'backend_team'
             WHERE PID != '' AND タスクID = ''
            """,
            [now],
        )
        connection.commit()
        return cursor.rowcount
