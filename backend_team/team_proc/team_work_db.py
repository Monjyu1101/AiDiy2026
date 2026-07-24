# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""Aチーム作業の DB アクセス。"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

from .team_db import DB_PATH

作業テーブル = "Aチーム作業"
状態一覧 = ("準備開始", "準備中", "準備完了", "待機", "実行中", "エラー", "完了", "中止")
状態入力一覧 = 状態一覧
実行タイムアウト分 = 30

_採番テーブル = "C採番"
_採番ID = "Aチーム作業"
_採番プレフィックス = "TW"
_採番初期値 = 1000


def _現在日時() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def 接続取得() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def 初期化() -> None:
    conn = 接続取得()
    try:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS "{作業テーブル}" (
                作業ID TEXT NOT NULL,
                要員ID TEXT NOT NULL,
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
                PRIMARY KEY (作業ID)
            )
        """)
        columns = {
            row[1]
            for row in conn.execute(f'PRAGMA table_info("{作業テーブル}")').fetchall()
        }
        if "TASK_AI_NAME" not in columns:
            conn.execute(
                f'ALTER TABLE "{作業テーブル}" ADD COLUMN TASK_AI_NAME TEXT NOT NULL DEFAULT \'claude_cli\''
            )
            conn.execute(f'UPDATE "{作業テーブル}" SET TASK_AI_NAME = TEAM_AI_NAME')
        if "TASK_AI_MODEL" not in columns:
            conn.execute(
                f'ALTER TABLE "{作業テーブル}" ADD COLUMN TASK_AI_MODEL TEXT NOT NULL DEFAULT \'auto\''
            )
            conn.execute(f'UPDATE "{作業テーブル}" SET TASK_AI_MODEL = TEAM_AI_MODEL')
        if "タスクID" not in columns:
            conn.execute(
                f'ALTER TABLE "{作業テーブル}" ADD COLUMN タスクID TEXT NOT NULL DEFAULT \'\''
            )
        if "要員ID" not in columns:
            # 旧スキーマ（利用者ID・複合PK）からの移行: 列追加のうえ値を引き継ぐ
            if "利用者ID" in columns:
                conn.execute(f'ALTER TABLE "{作業テーブル}" ADD COLUMN 要員ID TEXT NOT NULL DEFAULT \'\'')
                conn.execute(f'UPDATE "{作業テーブル}" SET 要員ID = 利用者ID')
            else:
                conn.execute(f'ALTER TABLE "{作業テーブル}" ADD COLUMN 要員ID TEXT NOT NULL DEFAULT \'\'')
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS "IX_Aチーム作業_状態"
            ON "{作業テーブル}" (要員ID, 状態, 作業ID)
        """)
        conn.commit()

        # 旧スキーマ（利用者ID を含む複合PK）が残っている場合はテーブルを作り直す
        PKカラム = [row[1] for row in conn.execute(f'PRAGMA table_info("{作業テーブル}")').fetchall() if row[5] > 0]
        if PKカラム != ["作業ID"]:
            _旧スキーマ再作成(conn)
            conn.commit()
    finally:
        conn.close()


def _旧スキーマ再作成(conn: sqlite3.Connection) -> None:
    """複合PK（利用者ID, 作業ID）だった旧テーブルを 作業ID 単独PKへ作り直す。"""
    旧テーブル = f"{作業テーブル}_old"
    conn.execute(f'DROP TABLE IF EXISTS "{旧テーブル}"')
    conn.execute(f'ALTER TABLE "{作業テーブル}" RENAME TO "{旧テーブル}"')
    conn.execute(f"""
        CREATE TABLE "{作業テーブル}" (
            作業ID TEXT NOT NULL,
            要員ID TEXT NOT NULL,
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
            PRIMARY KEY (作業ID)
        )
    """)
    conn.execute(f"""
        INSERT INTO "{作業テーブル}" (
            作業ID, 要員ID, プロジェクト, タイトル, 要求内容,
            TEAM_AI_NAME, TEAM_AI_MODEL, TASK_AI_NAME, TASK_AI_MODEL, タスクID,
            実行有効, 状態, PID, 開始日時, 終了日時, 実行回数, 応答タイトル, 応答内容,
            登録日時, 登録利用者ID, 登録利用者名, 登録端末ID,
            更新日時, 更新利用者ID, 更新利用者名, 更新端末ID
        )
        SELECT
            作業ID, 要員ID, プロジェクト, タイトル, 要求内容,
            TEAM_AI_NAME, TEAM_AI_MODEL, TASK_AI_NAME, TASK_AI_MODEL, タスクID,
            実行有効, 状態, PID, 開始日時, 終了日時, 実行回数, 応答タイトル, 応答内容,
            登録日時, 登録利用者ID, 登録利用者名, 登録端末ID,
            更新日時, 更新利用者ID, 更新利用者名, 更新端末ID
        FROM "{旧テーブル}"
        GROUP BY 作業ID
    """)
    conn.execute(f'DROP TABLE IF EXISTS "{旧テーブル}"')


def _採番確保(conn: sqlite3.Connection) -> None:
    """C採番（backend_server共有）にAチーム作業用の採番行が無ければ作成する。"""
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
        [_採番ID, _採番初期値, "AIチーム作業の採番（TW）", now, now],
    )


def _新規作業ID(conn: sqlite3.Connection, 要員ID: str) -> str:
    del 要員ID  # 作業ID は単独PKのためグローバルに一意（引数は呼び出し互換のため保持）
    _採番確保(conn)
    conn.execute(
        f'UPDATE "{_採番テーブル}" SET 最終採番値 = 最終採番値 + 1 WHERE 採番ID = ?',
        [_採番ID],
    )
    行 = conn.execute(
        f'SELECT 最終採番値 FROM "{_採番テーブル}" WHERE 採番ID = ?',
        [_採番ID],
    ).fetchone()
    return f"{_採番プレフィックス}{行[0]:08d}"


def _タイトル(要求内容: str) -> str:
    return 要求内容.splitlines()[0][:40] if 要求内容 else ""


def 作業一覧(要員ID: str) -> list[dict]:
    初期化()
    conn = 接続取得()
    try:
        rows = conn.execute(
            f"""
            SELECT 作業ID, 要員ID, プロジェクト, タイトル, 要求内容,
                   TEAM_AI_NAME, TEAM_AI_MODEL, TASK_AI_NAME, TASK_AI_MODEL, タスクID,
                   実行有効, 状態, PID,
                   開始日時, 終了日時, 実行回数, 応答タイトル, 応答内容, 更新日時
              FROM "{作業テーブル}"
             WHERE 要員ID = ?
             ORDER BY 作業ID DESC
            """,
            [要員ID],
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def 作業最大更新日時(要員ID: str) -> str:
    初期化()
    conn = 接続取得()
    try:
        row = conn.execute(
            f'SELECT MAX(更新日時) AS 最大更新日時 FROM "{作業テーブル}" WHERE 要員ID = ?',
            [要員ID],
        ).fetchone()
        return str(row["最大更新日時"] or "") if row else ""
    finally:
        conn.close()


def 作業取得(要員ID: str, 作業ID: str) -> dict | None:
    初期化()
    conn = 接続取得()
    try:
        row = conn.execute(
            f"""
            SELECT 作業ID, 要員ID, プロジェクト, タイトル, 要求内容,
                   TEAM_AI_NAME, TEAM_AI_MODEL, TASK_AI_NAME, TASK_AI_MODEL, タスクID,
                   実行有効, 状態, PID,
                   開始日時, 終了日時, 実行回数, 応答タイトル, 応答内容, 更新日時
              FROM "{作業テーブル}"
             WHERE 要員ID = ? AND 作業ID = ?
            """,
            [要員ID, 作業ID],
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def 作業登録(作業データ: dict, 操作者: dict) -> dict:
    初期化()
    now = _現在日時()
    conn = 接続取得()
    try:
        作業ID = _新規作業ID(conn, 作業データ["要員ID"])
        conn.execute(
            f"""
            INSERT INTO "{作業テーブル}" (
                作業ID, 要員ID, プロジェクト, タイトル, 要求内容,
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
                作業ID,
                作業データ["要員ID"],
                作業データ["プロジェクト"],
                _タイトル(作業データ["要求内容"]),
                作業データ["要求内容"],
                作業データ["TEAM_AI_NAME"],
                作業データ["TEAM_AI_MODEL"],
                作業データ["TASK_AI_NAME"],
                作業データ["TASK_AI_MODEL"],
                int(作業データ["実行有効"]),
                作業データ["状態"],
                now,
                操作者["利用者ID"],
                操作者["利用者名"],
                操作者["端末ID"],
                now,
                操作者["利用者ID"],
                操作者["利用者名"],
                操作者["端末ID"],
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return 作業取得(作業データ["要員ID"], 作業ID) or {}


def 作業変更(作業データ: dict, 操作者: dict) -> dict:
    初期化()
    if 作業データ["状態"] not in 状態一覧:
        raise ValueError("状態が正しくありません")
    現行 = 作業取得(作業データ["要員ID"], 作業データ["作業ID"])
    if 現行 is None:
        raise KeyError(作業データ["作業ID"])
    now = _現在日時()
    タスクID = str(現行["タスクID"] or "")
    PID = str(現行["PID"] or "")
    開始日時 = str(現行["開始日時"] or "")
    終了日時 = str(現行["終了日時"] or "")
    実行回数 = int(現行["実行回数"] or 0)
    応答タイトル = str(現行["応答タイトル"] or "")
    応答内容 = str(現行["応答内容"] or "")
    if 作業データ["状態"] == "準備開始":
        タスクID = ""
        PID = ""
        開始日時 = ""
        終了日時 = ""
        実行回数 = 0
        応答タイトル = ""
        応答内容 = ""
    if 作業データ["状態"] == "実行中" and not 開始日時:
        開始日時 = now
    if 作業データ["状態"] in ("完了", "中止"):
        終了日時 = now
    elif 作業データ["状態"] == "待機":
        終了日時 = ""
    conn = 接続取得()
    try:
        conn.execute(
            f"""
            UPDATE "{作業テーブル}"
               SET プロジェクト = ?, タイトル = ?, 要求内容 = ?,
                   TEAM_AI_NAME = ?, TEAM_AI_MODEL = ?,
                   TASK_AI_NAME = ?, TASK_AI_MODEL = ?,
                   実行有効 = ?, 状態 = ?,
                   タスクID = ?, PID = ?, 開始日時 = ?, 終了日時 = ?,
                   実行回数 = ?, 応答タイトル = ?, 応答内容 = ?,
                   更新日時 = ?, 更新利用者ID = ?, 更新利用者名 = ?, 更新端末ID = ?
             WHERE 要員ID = ? AND 作業ID = ?
            """,
            (
                作業データ["プロジェクト"],
                _タイトル(作業データ["要求内容"]),
                作業データ["要求内容"],
                作業データ["TEAM_AI_NAME"],
                作業データ["TEAM_AI_MODEL"],
                作業データ["TASK_AI_NAME"],
                作業データ["TASK_AI_MODEL"],
                int(作業データ["実行有効"]),
                作業データ["状態"],
                タスクID,
                PID,
                開始日時,
                終了日時,
                実行回数,
                応答タイトル,
                応答内容,
                now,
                操作者["利用者ID"],
                操作者["利用者名"],
                操作者["端末ID"],
                作業データ["要員ID"],
                作業データ["作業ID"],
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return 作業取得(作業データ["要員ID"], 作業データ["作業ID"]) or {}


def 投入待ち一覧() -> list[dict]:
    """準備開始かつ未投入で、sub_initによるAIタスク登録を待つ作業を返す。"""
    初期化()
    conn = 接続取得()
    try:
        rows = conn.execute(
            f"""
            SELECT 作業ID, 要員ID, プロジェクト, タイトル, 要求内容,
                   TEAM_AI_NAME, TEAM_AI_MODEL, TASK_AI_NAME, TASK_AI_MODEL,
                   実行有効, 状態, PID, 実行回数
              FROM "{作業テーブル}"
             WHERE 状態 = '準備開始'
               AND PID = ''
               AND タスクID = ''
             ORDER BY 作業ID
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def 作業確保(作業ID: str) -> bool:
    """準備開始の1件を準備中へ進めて確保し、sub_initの二重起動を防ぐ。"""
    初期化()
    now = _現在日時()
    conn = 接続取得()
    try:
        cursor = conn.execute(
            f"""
            UPDATE "{作業テーブル}"
               SET 状態 = '準備中', PID = 'CLAIM',
                   開始日時 = ?, 終了日時 = '', 実行回数 = 実行回数 + 1,
                   応答タイトル = '', 応答内容 = '',
                   更新日時 = ?, 更新利用者ID = 'system',
                   更新利用者名 = 'システム', 更新端末ID = 'backend_team'
             WHERE 作業ID = ?
               AND 状態 = '準備開始'
               AND PID = ''
               AND タスクID = ''
            """,
            [now, now, 作業ID],
        )
        conn.commit()
        return cursor.rowcount == 1
    finally:
        conn.close()


def 実行開始記録(作業ID: str, pid: int) -> None:
    """CLAIM中の作業へsub_initのPIDを記録する。先に完了した場合は上書きしない。"""
    now = _現在日時()
    conn = 接続取得()
    try:
        conn.execute(
            f"""
            UPDATE "{作業テーブル}"
               SET PID = ?, 更新日時 = ?
             WHERE 作業ID = ?
               AND 状態 = '準備中' AND PID = 'CLAIM'
            """,
            [str(pid), now, 作業ID],
        )
        conn.commit()
    finally:
        conn.close()


def 投入成功記録(作業ID: str, タスクID: str) -> None:
    """aidiy_task_agentsへの投入成功を作業行へ反映する。"""
    now = _現在日時()
    conn = 接続取得()
    try:
        cursor = conn.execute(
            f"""
            UPDATE "{作業テーブル}"
               SET タスクID = ?, 状態 = '準備完了', PID = '',
                   応答タイトル = 'AIタスク投入済み',
                   更新日時 = ?, 更新利用者ID = 'system',
                   更新利用者名 = 'システム', 更新端末ID = 'backend_team'
             WHERE 作業ID = ? AND 状態 = '準備中'
            """,
            [タスクID, now, 作業ID],
        )
        if cursor.rowcount != 1:
            raise KeyError(作業ID)
        conn.commit()
    finally:
        conn.close()


def 投入失敗記録(作業ID: str, メッセージ: str) -> None:
    """sub_initの起動またはタスク投入失敗をエラーとして記録する。"""
    now = _現在日時()
    conn = 接続取得()
    try:
        conn.execute(
            f"""
            UPDATE "{作業テーブル}"
               SET 状態 = 'エラー', PID = '', 終了日時 = ?,
                   応答タイトル = 'AIタスク投入エラー', 応答内容 = ?,
                   更新日時 = ?, 更新利用者ID = 'system',
                   更新利用者名 = 'システム', 更新端末ID = 'backend_team'
             WHERE 作業ID = ?
               AND (状態 = '準備中' OR PID != '')
            """,
            [now, メッセージ[:2000], now, 作業ID],
        )
        conn.commit()
    finally:
        conn.close()


def 残存PID一覧() -> list[dict]:
    """再起動時に整理するsub_init PIDを返す。"""
    初期化()
    conn = 接続取得()
    try:
        rows = conn.execute(
            f"""
            SELECT 作業ID, 要員ID, PID
              FROM "{作業テーブル}"
             WHERE PID != ''
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def PID全クリア() -> int:
    """残存sub_initを準備開始へ戻し、次回監視で再実行できるようにする。"""
    now = _現在日時()
    conn = 接続取得()
    try:
        cursor = conn.execute(
            f"""
            UPDATE "{作業テーブル}"
               SET 状態 = '準備開始', PID = '', 開始日時 = '', 終了日時 = '',
                   更新日時 = ?, 更新利用者ID = 'system',
                   更新利用者名 = 'システム', 更新端末ID = 'backend_team'
             WHERE PID != '' AND タスクID = ''
            """,
            [now],
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def 作業タイムアウト対象一覧(制限分: int = 実行タイムアウト分) -> list[dict]:
    """開始日時だけが入ったまま制限分以上経過した作業を返す。

    呼び出し側で PID のプロセスを停止してから 作業タイムアウト対象エラー化() でエラー化する。
    """
    初期化()
    conn = 接続取得()
    try:
        閾値 = (datetime.now() - timedelta(minutes=制限分)).strftime("%Y-%m-%d %H:%M:%S")
        rows = conn.execute(
            f"""
            SELECT 作業ID, 要員ID, 状態, PID, 開始日時
              FROM "{作業テーブル}"
             WHERE 開始日時 != '' AND 終了日時 = '' AND 状態 != 'エラー' AND 開始日時 <= ?
            """,
            [閾値],
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def 作業タイムアウト対象エラー化(対象一覧: list[dict]) -> int:
    """タイムアウト対象を 状態='エラー'・実行有効=0・PID='' にする。"""
    if not 対象一覧:
        return 0
    初期化()
    now = _現在日時()
    conn = 接続取得()
    try:
        更新件数 = 0
        for 行 in 対象一覧:
            作業ID = str(行.get("作業ID", ""))
            PID = str(行.get("PID", ""))
            開始日時 = str(行.get("開始日時", ""))
            if not 作業ID:
                continue
            cursor = conn.execute(
                f"""
                UPDATE "{作業テーブル}"
                   SET 状態 = 'エラー', 実行有効 = 0, PID = '', 終了日時 = ?,
                       応答タイトル = '実行タイムアウト', 更新日時 = ?
                 WHERE 作業ID = ?
                   AND 状態 != 'エラー' AND 終了日時 = '' AND PID = ? AND 開始日時 = ?
                """,
                [now, now, 作業ID, PID, 開始日時],
            )
            更新件数 += cursor.rowcount
        conn.commit()
        return 更新件数
    finally:
        conn.close()
