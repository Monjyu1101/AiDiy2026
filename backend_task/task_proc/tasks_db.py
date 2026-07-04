# -*- coding: utf-8 -*-

"""AIタスクの DB アクセス。

AIタスク要求 / AIタスク明細 テーブルを backend_server の共有 SQLite に作成し、
一覧取得・登録を提供する。Alembic は使わず CREATE TABLE IF NOT EXISTS で管理する。
"""

from __future__ import annotations

import os
import json
import sqlite3
from datetime import datetime

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.normpath(os.path.join(_BASE_DIR, "..", "backend_server", "_data", "AiDiy"))
DB_PATH = os.path.join(DB_DIR, "database.db")

_初期化済み = False

AIタスク要求テーブル = "AIタスク要求"
AIタスク明細テーブル = "AIタスク明細"
TASK_AI_NAME既定 = "claude_cli"
TASK_AI_MODEL既定 = "auto"
要求PKカラム = ["利用者ID", "タスクID"]
明細PKカラム = ["利用者ID", "タスクID", "明細SEQ"]
要求カラム順 = [
    "利用者ID",
    "タスクID",
    "プロジェクト",
    "タイトル",
    "要求内容",
    "TASK_AI_NAME",
    "TASK_AI_MODEL",
    "有効",
    "状態",
    "マーメイド記号",
    "PID",
    "開始日時",
    "終了日時",
    "実行回数",
    "登録日時",
    "登録利用者ID",
    "登録利用者名",
    "登録端末ID",
    "更新日時",
    "更新利用者ID",
    "更新利用者名",
    "更新端末ID",
]
明細カラム順 = [
    "利用者ID",
    "タスクID",
    "明細SEQ",
    "タイトル",
    "要求内容",
    "先行SEQ",
    "TASK_AI_NAME",
    "TASK_AI_MODEL",
    "有効",
    "状態",
    "PID",
    "開始日時",
    "終了日時",
    "実行回数",
    "応答内容",
    "登録日時",
    "登録利用者ID",
    "登録利用者名",
    "登録端末ID",
    "更新日時",
    "更新利用者ID",
    "更新利用者名",
    "更新端末ID",
]


def _TASK_AI設定() -> tuple[str, str]:
    path = os.path.normpath(os.path.join(_BASE_DIR, "..", "backend_server", "_config", "AiDiy_key.json"))
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        return str(data.get("TASK_AI_NAME", TASK_AI_NAME既定)), str(data.get("TASK_AI_MODEL", TASK_AI_MODEL既定))
    except Exception:
        return TASK_AI_NAME既定, TASK_AI_MODEL既定


def _識別子(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def 接続取得() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def _現在日時() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def 新規タスクID() -> str:
    return datetime.now().strftime("%Y%m%d.%H%M%S")


def _監査項目(利用者ID: str = "system", 利用者名: str = "システム") -> dict[str, str]:
    now = _現在日時()
    return {
        "登録日時": now,
        "登録利用者ID": 利用者ID,
        "登録利用者名": 利用者名,
        "登録端末ID": "backend_task",
        "更新日時": now,
        "更新利用者ID": 利用者ID,
        "更新利用者名": 利用者名,
        "更新端末ID": "backend_task",
    }


_監査カラムDDL = """
    登録日時 TEXT NOT NULL,
    登録利用者ID TEXT NOT NULL,
    登録利用者名 TEXT NOT NULL,
    登録端末ID TEXT NOT NULL,
    更新日時 TEXT NOT NULL,
    更新利用者ID TEXT NOT NULL,
    更新利用者名 TEXT NOT NULL,
    更新端末ID TEXT NOT NULL
"""


def _カラム一覧(conn: sqlite3.Connection, テーブル名: str) -> list[sqlite3.Row]:
    return list(conn.execute(f"PRAGMA table_info({_識別子(テーブル名)})"))


def _PKカラム一覧(conn: sqlite3.Connection, テーブル名: str) -> list[str]:
    rows = _カラム一覧(conn, テーブル名)
    return [row[1] for row in sorted([row for row in rows if row[5] > 0], key=lambda row: row[5])]


def _カラム名一覧(conn: sqlite3.Connection, テーブル名: str) -> list[str]:
    return [row[1] for row in _カラム一覧(conn, テーブル名)]


def _テーブル存在(conn: sqlite3.Connection, テーブル名: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        [テーブル名],
    ).fetchone()
    return row is not None


def _AIタスク要求テーブル作成(conn: sqlite3.Connection) -> None:
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {AIタスク要求テーブル} (
            利用者ID TEXT NOT NULL,
            タスクID TEXT NOT NULL,
            プロジェクト TEXT NOT NULL DEFAULT '',
            タイトル TEXT NOT NULL,
            要求内容 TEXT NOT NULL DEFAULT '',
            TASK_AI_NAME TEXT NOT NULL DEFAULT 'claude_cli',
            TASK_AI_MODEL TEXT NOT NULL DEFAULT 'auto',
            有効 INTEGER NOT NULL DEFAULT 1,
            状態 TEXT NOT NULL DEFAULT '準備完了',
            マーメイド記号 TEXT NOT NULL DEFAULT '',
            PID TEXT NOT NULL DEFAULT '',
            開始日時 TEXT NOT NULL DEFAULT '',
            終了日時 TEXT NOT NULL DEFAULT '',
            実行回数 INTEGER NOT NULL DEFAULT 0,
            {_監査カラムDDL},
            PRIMARY KEY (利用者ID, タスクID)
        )
    """)


def _AIタスク明細テーブル作成(conn: sqlite3.Connection) -> None:
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {AIタスク明細テーブル} (
            利用者ID TEXT NOT NULL,
            タスクID TEXT NOT NULL,
            明細SEQ INTEGER NOT NULL,
            タイトル TEXT NOT NULL,
            要求内容 TEXT NOT NULL DEFAULT '',
            先行SEQ TEXT NOT NULL DEFAULT '',
            TASK_AI_NAME TEXT NOT NULL DEFAULT 'claude_cli',
            TASK_AI_MODEL TEXT NOT NULL DEFAULT 'auto',
            有効 INTEGER NOT NULL DEFAULT 1,
            状態 TEXT NOT NULL DEFAULT '待機',
            PID TEXT NOT NULL DEFAULT '',
            開始日時 TEXT NOT NULL DEFAULT '',
            終了日時 TEXT NOT NULL DEFAULT '',
            実行回数 INTEGER NOT NULL DEFAULT 0,
            応答内容 TEXT NOT NULL DEFAULT '',
            {_監査カラムDDL},
            PRIMARY KEY (利用者ID, タスクID, 明細SEQ)
        )
    """)


def _AIタスク要求群再作成(conn: sqlite3.Connection) -> None:
    if _テーブル存在(conn, AIタスク要求テーブル):
        旧テーブル = f"{AIタスク要求テーブル}_old"
        conn.execute(f"DROP TABLE IF EXISTS {_識別子(旧テーブル)}")
        conn.execute(f"ALTER TABLE {_識別子(AIタスク要求テーブル)} RENAME TO {_識別子(旧テーブル)}")
        _AIタスク要求テーブル作成(conn)
        旧カラム = set(_カラム名一覧(conn, 旧テーブル))
        task_ai_name, task_ai_model = _TASK_AI設定()
        select_exprs: list[str] = []
        params: list[str] = []
        for カラム in 要求カラム順:
            if カラム in 旧カラム:
                select_exprs.append(_識別子(カラム))
            elif カラム == "TASK_AI_NAME":
                select_exprs.append("?")
                params.append(task_ai_name)
            elif カラム == "TASK_AI_MODEL":
                select_exprs.append("?")
                params.append(task_ai_model)
            elif カラム == "有効":
                select_exprs.append("1")
            elif カラム == "実行回数":
                select_exprs.append("0")
            else:
                select_exprs.append("''")
        conn.execute(
            f"INSERT INTO {_識別子(AIタスク要求テーブル)} ({', '.join(_識別子(c) for c in 要求カラム順)}) "
            f"SELECT {', '.join(select_exprs)} FROM {_識別子(旧テーブル)}",
            params,
        )
        conn.execute(f"DROP TABLE IF EXISTS {_識別子(旧テーブル)}")
        return
    _AIタスク要求テーブル作成(conn)


def _AIタスク明細テーブル再作成(conn: sqlite3.Connection) -> None:
    if _テーブル存在(conn, AIタスク明細テーブル):
        旧テーブル = f"{AIタスク明細テーブル}_old"
        conn.execute(f"DROP TABLE IF EXISTS {_識別子(旧テーブル)}")
        conn.execute(f"ALTER TABLE {_識別子(AIタスク明細テーブル)} RENAME TO {_識別子(旧テーブル)}")
        _AIタスク明細テーブル作成(conn)
        旧カラム = set(_カラム名一覧(conn, 旧テーブル))
        task_ai_name, task_ai_model = _TASK_AI設定()
        select_exprs: list[str] = []
        params: list[str] = []
        for カラム in 明細カラム順:
            if カラム in 旧カラム:
                select_exprs.append(_識別子(カラム))
            elif カラム == "TASK_AI_NAME":
                select_exprs.append("?")
                params.append(task_ai_name)
            elif カラム == "TASK_AI_MODEL":
                select_exprs.append("?")
                params.append(task_ai_model)
            else:
                select_exprs.append("''")
        conn.execute(
            f"INSERT INTO {_識別子(AIタスク明細テーブル)} ({', '.join(_識別子(c) for c in 明細カラム順)}) "
            f"SELECT {', '.join(select_exprs)} FROM {_識別子(旧テーブル)}",
            params,
        )
        conn.execute(f"DROP TABLE IF EXISTS {_識別子(旧テーブル)}")
        return
    _AIタスク明細テーブル作成(conn)


# 手動登録 API 用の標準明細テンプレート（明細SEQ, タイトル, 先行SEQ）
_標準明細テンプレート: list[tuple[int, str, str]] = [
    (0, "開始", ""),
    (1, "要求分析", "0"),
    (2, "設計", "1"),
    (3, "実装A", "2"),
    (4, "実装B", "2"),
    (5, "テスト", "3,4"),
    (6, "リリース", "5"),
    (9999, "終了", "6"),
]

def 初期化() -> None:
    """テーブル作成と既存 DB 向けカラム追加を行う。多重呼び出し可。"""
    global _初期化済み
    if _初期化済み:
        return
    conn = 接続取得()
    try:
        _AIタスク要求テーブル作成(conn)
        _AIタスク明細テーブル作成(conn)
        conn.commit()

        if (
            _PKカラム一覧(conn, AIタスク要求テーブル) != 要求PKカラム
            or _カラム名一覧(conn, AIタスク要求テーブル) != 要求カラム順
        ):
            _AIタスク要求群再作成(conn)
            conn.commit()
        if (
            _PKカラム一覧(conn, AIタスク明細テーブル) != 明細PKカラム
            or _カラム名一覧(conn, AIタスク明細テーブル) != 明細カラム順
        ):
            _AIタスク明細テーブル再作成(conn)
            conn.commit()

        _初期化済み = True
    finally:
        conn.close()


def _タスク登録(
    conn: sqlite3.Connection,
    利用者ID: str,
    タイトル: str,
    要求内容: str,
    状態: str,
    明細: list[tuple[int, str, str]],
) -> str:
    タスクID = 新規タスクID()
    監査 = _監査項目(利用者ID, 利用者ID)
    監査カラム = ", ".join(監査.keys())
    監査値 = list(監査.values())
    conn.execute(
        f"INSERT INTO {AIタスク要求テーブル} (利用者ID, タスクID, タイトル, 要求内容, 状態, {監査カラム}) "
        f"VALUES (?, ?, ?, ?, ?, {', '.join('?' * len(監査値))})",
        [利用者ID, タスクID, タイトル, 要求内容, 状態, *監査値],
    )
    for 明細SEQ, タイトル, 先行SEQ in 明細:
        task_ai_name, task_ai_model = _TASK_AI設定()
        conn.execute(
            f"INSERT INTO {AIタスク明細テーブル} (利用者ID, タスクID, 明細SEQ, タイトル, 先行SEQ, TASK_AI_NAME, TASK_AI_MODEL, 状態, {監査カラム}) "
            f"VALUES (?, ?, ?, ?, ?, ?, ?, ?, {', '.join('?' * len(監査値))})",
            [利用者ID, タスクID, 明細SEQ, タイトル, 先行SEQ, task_ai_name, task_ai_model, "待機", *監査値],
        )
    return タスクID


def タスク要求一覧(利用者ID: str) -> list[dict]:
    初期化()
    conn = 接続取得()
    try:
        rows = conn.execute(
            "SELECT 利用者ID, タスクID, プロジェクト, タイトル, 要求内容, TASK_AI_NAME, TASK_AI_MODEL, 有効, 状態, マーメイド記号, "
            f"PID, 開始日時, 終了日時, 実行回数, 更新日時 FROM {AIタスク要求テーブル} "
            "WHERE 利用者ID = ? "
            "ORDER BY CASE WHEN タスクID GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].*' THEN 1 ELSE 0 END DESC, "
            "タスクID DESC",
            [利用者ID],
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def タスク要求最大更新日時(利用者ID: str) -> str:
    初期化()
    conn = 接続取得()
    try:
        row = conn.execute(
            f"SELECT MAX(更新日時) AS 最大更新日時 FROM {AIタスク要求テーブル} WHERE 利用者ID = ?",
            [利用者ID],
        ).fetchone()
        return str(row["最大更新日時"] or "") if row else ""
    finally:
        conn.close()


def タスク明細一覧(利用者ID: str, タスクID: str) -> list[dict]:
    初期化()
    conn = 接続取得()
    try:
        rows = conn.execute(
            "SELECT 利用者ID, タスクID, 明細SEQ, タイトル, 要求内容, 先行SEQ, TASK_AI_NAME, TASK_AI_MODEL, 有効, 状態, "
            f"PID, 開始日時, 終了日時, 実行回数, 応答内容 FROM {AIタスク明細テーブル} "
            "WHERE 利用者ID = ? AND タスクID = ? ORDER BY 明細SEQ",
            [利用者ID, タスクID],
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def タスク明細取得(利用者ID: str, タスクID: str, 明細SEQ: int) -> dict:
    初期化()
    conn = 接続取得()
    try:
        row = conn.execute(
            "SELECT 利用者ID, タスクID, 明細SEQ, タイトル, 要求内容, 先行SEQ, TASK_AI_NAME, TASK_AI_MODEL, 有効, 状態, "
            f"PID, 開始日時, 終了日時, 実行回数, 応答内容 FROM {AIタスク明細テーブル} "
            "WHERE 利用者ID = ? AND タスクID = ? AND 明細SEQ = ?",
            [利用者ID, タスクID, 明細SEQ],
        ).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


def タスク明細最大更新日時(利用者ID: str, タスクID: str) -> str:
    初期化()
    conn = 接続取得()
    try:
        row = conn.execute(
            f"SELECT MAX(更新日時) AS 最大更新日時 FROM {AIタスク明細テーブル} "
            "WHERE 利用者ID = ? AND タスクID = ?",
            [利用者ID, タスクID],
        ).fetchone()
        return str(row["最大更新日時"] or "") if row else ""
    finally:
        conn.close()


def タスク要求登録(利用者ID: str, タイトル: str, 要求内容: str) -> dict:
    """タスク要求を登録し、標準工程明細を自動生成する。"""
    初期化()
    conn = 接続取得()
    try:
        タスクID = _タスク登録(conn, 利用者ID, タイトル, 要求内容, "準備完了", _標準明細テンプレート)
        conn.commit()
        return _タスク要求取得(conn, 利用者ID, タスクID)
    finally:
        conn.close()


def _タスク要求取得(conn: sqlite3.Connection, 利用者ID: str, タスクID: str) -> dict:
    row = conn.execute(
        "SELECT 利用者ID, タスクID, プロジェクト, タイトル, 要求内容, TASK_AI_NAME, TASK_AI_MODEL, 有効, 状態, マーメイド記号, "
        f"PID, 開始日時, 終了日時, 実行回数, 更新日時 FROM {AIタスク要求テーブル} "
        "WHERE 利用者ID = ? AND タスクID = ?",
        [利用者ID, タスクID],
    ).fetchone()
    return dict(row) if row else {}


def 仮タスク登録(
    タスクID: str,
    タイトル: str,
    要求内容: str,
    利用者ID: str,
    プロジェクト: str = "",
    TASK_AI_NAME: str = TASK_AI_NAME既定,
    TASK_AI_MODEL: str = TASK_AI_MODEL既定,
    有効: bool = True,
) -> dict:
    """AI 生成待ちの仮タスクを『準備中』状態で登録する（実行は監視ループに任せる）。"""
    初期化()
    conn = 接続取得()
    try:
        監査 = _監査項目(利用者ID, 利用者ID)
        監査カラム = ", ".join(監査.keys())
        監査値 = list(監査.values())
        conn.execute(
            f"INSERT INTO {AIタスク要求テーブル} (利用者ID, タスクID, プロジェクト, タイトル, 要求内容, TASK_AI_NAME, TASK_AI_MODEL, 有効, 状態, {監査カラム}) "
            f"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, {', '.join('?' * len(監査値))})",
            [利用者ID, タスクID, プロジェクト, タイトル, 要求内容, TASK_AI_NAME, TASK_AI_MODEL, 1 if 有効 else 0, "準備中", *監査値],
        )
        conn.commit()
        return _タスク要求取得(conn, 利用者ID, タスクID)
    finally:
        conn.close()


def 実行待ち一覧() -> list[dict]:
    """PID 未設定の仮登録（準備中）を返す。監視ループが 5 秒間隔で確認する。"""
    初期化()
    conn = 接続取得()
    try:
        rows = conn.execute(
            "SELECT 利用者ID, タスクID, プロジェクト, タイトル, 要求内容, TASK_AI_NAME, TASK_AI_MODEL, 実行回数, 登録利用者ID "
            f"FROM {AIタスク要求テーブル} WHERE 状態 = '準備中' AND PID = '' ORDER BY タスクID"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def 実行開始記録(利用者ID: str, タスクID: str, pid: int) -> None:
    """subprocess 起動時に PID・開始日時・実行回数+1 を記録する。"""
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        conn.execute(
            f"UPDATE {AIタスク要求テーブル} SET PID = ?, 開始日時 = ?, 実行回数 = 実行回数 + 1, 更新日時 = ? "
            "WHERE 利用者ID = ? AND タスクID = ?",
            [str(pid), now, now, 利用者ID, タスクID],
        )
        conn.commit()
    finally:
        conn.close()


def 実行待ち明細一覧() -> list[dict]:
    """実行可能な AIタスク明細（有効・待機・PID なし・先行 SEQ が全て完了）を返す。

    親の AIタスク要求が 準備完了 / 処理中 のものだけを対象とする
    （準備中・失敗・完了のタスクは実行しない）。
    明細の 有効 = 0 は実行対象にしない（明細作成は有効フラグに関係なく行う）。
    """
    初期化()
    conn = 接続取得()
    try:
        rows = conn.execute(
            "SELECT m.利用者ID, m.タスクID, m.明細SEQ, m.タイトル, m.先行SEQ, m.TASK_AI_NAME, m.TASK_AI_MODEL, m.実行回数 "
            f"FROM {AIタスク明細テーブル} m JOIN {AIタスク要求テーブル} r "
            "ON r.利用者ID = m.利用者ID AND r.タスクID = m.タスクID "
            "WHERE m.有効 = 1 AND m.状態 = '待機' AND m.PID = '' AND r.状態 IN ('準備完了', '処理中') "
            "ORDER BY m.タスクID, m.明細SEQ"
        ).fetchall()
        候補 = [dict(row) for row in rows]
        if not 候補:
            return []

        # タスクごとの明細状態マップで先行 SEQ の完了を確認する
        状態マップ: dict[tuple[str, str], dict[int, str]] = {}
        for 利用者ID, タスクID in {(行["利用者ID"], 行["タスクID"]) for 行 in 候補}:
            状態マップ[(利用者ID, タスクID)] = {
                int(r[0]): str(r[1])
                for r in conn.execute(
                    f"SELECT 明細SEQ, 状態 FROM {AIタスク明細テーブル} "
                    "WHERE 利用者ID = ? AND タスクID = ?",
                    [利用者ID, タスクID],
                )
            }

        実行可能: list[dict] = []
        for 行 in 候補:
            状態表 = 状態マップ[(行["利用者ID"], 行["タスクID"])]
            先行OK = True
            for p in str(行.get("先行SEQ", "")).split(","):
                p = p.strip()
                if not p:
                    continue
                if not p.isdigit() or 状態表.get(int(p)) != "完了":
                    先行OK = False
                    break
            if 先行OK:
                実行可能.append(行)
        return 実行可能
    finally:
        conn.close()


def 実行中明細数() -> int:
    """PID が設定されている（実行中の）AIタスク明細の件数を返す。"""
    初期化()
    conn = 接続取得()
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {AIタスク明細テーブル} WHERE PID != ''").fetchone()[0]
    finally:
        conn.close()


def 実行中明細一覧() -> list[dict]:
    """PID が設定されている（実行中の）AIタスク明細を返す。"""
    初期化()
    conn = 接続取得()
    try:
        rows = conn.execute(
            "SELECT 利用者ID, タスクID, 明細SEQ, タイトル, PID "
            f"FROM {AIタスク明細テーブル} WHERE PID != '' ORDER BY タスクID, 明細SEQ"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def 明細実行開始記録(利用者ID: str, タスクID: str, 明細SEQ: int, pid: int) -> None:
    """明細実行の開始: 状態=実行中・PID・開始日時・実行回数+1。"""
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        conn.execute(
            f"UPDATE {AIタスク明細テーブル} SET 状態 = '実行中', PID = ?, 開始日時 = ?, "
            "実行回数 = 実行回数 + 1, 更新日時 = ? "
            "WHERE 利用者ID = ? AND タスクID = ? AND 明細SEQ = ?",
            [str(pid), now, now, 利用者ID, タスクID, 明細SEQ],
        )
        conn.execute(
            f"UPDATE {AIタスク要求テーブル} SET 状態 = CASE WHEN 状態 = '準備完了' THEN '処理中' ELSE 状態 END, "
            "更新日時 = ? WHERE 利用者ID = ? AND タスクID = ?",
            [now, 利用者ID, タスクID],
        )
        conn.commit()
    finally:
        conn.close()


def 明細完了(利用者ID: str, タスクID: str, 明細SEQ: int, 応答内容: str = "") -> dict:
    """明細を完了にする。全明細が完了したら AIタスク要求も完了にする。"""
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        conn.execute(
            f"UPDATE {AIタスク明細テーブル} SET 状態 = '完了', 終了日時 = ?, PID = '', 応答内容 = ?, 更新日時 = ? "
            "WHERE 利用者ID = ? AND タスクID = ? AND 明細SEQ = ?",
            [now, 応答内容, now, 利用者ID, タスクID, 明細SEQ],
        )
        残 = conn.execute(
            f"SELECT COUNT(*) FROM {AIタスク明細テーブル} "
            "WHERE 利用者ID = ? AND タスクID = ? AND 状態 != '完了'",
            [利用者ID, タスクID],
        ).fetchone()[0]
        if 残 == 0:
            conn.execute(
                f"UPDATE {AIタスク要求テーブル} SET 状態 = '完了', 終了日時 = ?, 更新日時 = ? "
                "WHERE 利用者ID = ? AND タスクID = ?",
                [now, now, 利用者ID, タスクID],
            )
        else:
            conn.execute(
                f"UPDATE {AIタスク要求テーブル} SET 更新日時 = ? WHERE 利用者ID = ? AND タスクID = ?",
                [now, 利用者ID, タスクID],
            )
        conn.commit()
        return _タスク要求取得(conn, 利用者ID, タスクID)
    finally:
        conn.close()


def 開始明細完了(利用者ID: str, タスクID: str, 明細SEQ: int) -> dict:
    """開始明細を完了し、AIタスク要求を処理中にする。"""
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        conn.execute(
            f"UPDATE {AIタスク明細テーブル} SET 状態 = '完了', 終了日時 = ?, PID = '', 応答内容 = ?, 更新日時 = ? "
            "WHERE 利用者ID = ? AND タスクID = ? AND 明細SEQ = ?",
            [now, "開始処理を完了しました。", now, 利用者ID, タスクID, 明細SEQ],
        )
        conn.execute(
            f"UPDATE {AIタスク要求テーブル} SET 状態 = '処理中', 開始日時 = ?, 終了日時 = '', 実行回数 = 1, PID = '', 更新日時 = ? "
            "WHERE 利用者ID = ? AND タスクID = ?",
            [now, now, 利用者ID, タスクID],
        )
        conn.commit()
        return _タスク要求取得(conn, 利用者ID, タスクID)
    finally:
        conn.close()


def 終了明細完了(利用者ID: str, タスクID: str, 明細SEQ: int) -> dict:
    """終了明細を完了し、AIタスク要求を完了にする。"""
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        conn.execute(
            f"UPDATE {AIタスク明細テーブル} SET 状態 = '完了', 終了日時 = ?, PID = '', 応答内容 = ?, 更新日時 = ? "
            "WHERE 利用者ID = ? AND タスクID = ? AND 明細SEQ = ?",
            [now, "終了処理を完了しました。", now, 利用者ID, タスクID, 明細SEQ],
        )
        conn.execute(
            f"UPDATE {AIタスク要求テーブル} SET 状態 = '完了', 終了日時 = ?, PID = '', 更新日時 = ? "
            "WHERE 利用者ID = ? AND タスクID = ?",
            [now, now, 利用者ID, タスクID],
        )
        conn.commit()
        return _タスク要求取得(conn, 利用者ID, タスクID)
    finally:
        conn.close()


def 明細失敗(利用者ID: str, タスクID: str, 明細SEQ: int, メッセージ: str) -> dict:
    """明細を失敗にし、AIタスク要求も失敗にする（後続の実行を止める）。"""
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        conn.execute(
            f"UPDATE {AIタスク明細テーブル} SET 状態 = '失敗', 終了日時 = ?, PID = '', 応答内容 = ?, 更新日時 = ? "
            "WHERE 利用者ID = ? AND タスクID = ? AND 明細SEQ = ?",
            [now, メッセージ, now, 利用者ID, タスクID, 明細SEQ],
        )
        conn.execute(
            f"UPDATE {AIタスク要求テーブル} SET 状態 = '失敗', 要求内容 = 要求内容 || ?, 更新日時 = ? "
            "WHERE 利用者ID = ? AND タスクID = ?",
            [f"\n[エラー] SEQ{明細SEQ}: {メッセージ}", now, 利用者ID, タスクID],
        )
        conn.commit()
        return _タスク要求取得(conn, 利用者ID, タスクID)
    finally:
        conn.close()


def タスクPID一覧(利用者ID: str, タスクID: str) -> list[int]:
    """指定タスクの AIタスク要求・AIタスク明細に残っている PID を返す。"""
    初期化()
    conn = 接続取得()
    try:
        結果: list[int] = []
        for テーブル in (AIタスク要求テーブル, AIタスク明細テーブル):
            rows = conn.execute(
                f"SELECT PID FROM {_識別子(テーブル)} WHERE 利用者ID = ? AND タスクID = ? AND PID != ''",
                [利用者ID, タスクID],
            ).fetchall()
            結果.extend(int(row[0]) for row in rows if str(row[0]).strip().isdigit())
        return 結果
    finally:
        conn.close()


def タスクPIDクリア(利用者ID: str, タスクID: str) -> None:
    """指定タスクの PID をすべてクリアする。実行中のまま残った明細は待機に戻す。"""
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        conn.execute(
            f"UPDATE {AIタスク明細テーブル} SET 状態 = '待機' "
            "WHERE 利用者ID = ? AND タスクID = ? AND PID != '' AND 状態 = '実行中'",
            [利用者ID, タスクID],
        )
        for テーブル in (AIタスク要求テーブル, AIタスク明細テーブル):
            conn.execute(
                f"UPDATE {_識別子(テーブル)} SET PID = '', 更新日時 = ? "
                "WHERE 利用者ID = ? AND タスクID = ? AND PID != ''",
                [now, 利用者ID, タスクID],
            )
        conn.commit()
    finally:
        conn.close()


def タスク要求更新登録(
    利用者ID: str,
    タスクID: str,
    プロジェクト: str,
    要求内容: str,
    TASK_AI_NAME: str,
    TASK_AI_MODEL: str,
    有効: bool,
    状態: str,
) -> dict:
    """修正ダイアログの内容で AIタスク要求を更新する（PID クリア済み前提）。

    準備中（再準備）は開始日時・終了日時・実行回数をリセットし、監視ループに再分解させる。
    """
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        タイトル = 要求内容.splitlines()[0][:40] if 要求内容 else ""
        if 状態 == "準備中":
            conn.execute(
                f"UPDATE {AIタスク要求テーブル} SET プロジェクト = ?, タイトル = ?, 要求内容 = ?, TASK_AI_NAME = ?, TASK_AI_MODEL = ?, 有効 = ?, 状態 = ?, "
                "PID = '', 開始日時 = '', 終了日時 = '', 実行回数 = 0, 更新日時 = ? "
                "WHERE 利用者ID = ? AND タスクID = ?",
                [プロジェクト, タイトル, 要求内容, TASK_AI_NAME, TASK_AI_MODEL, 1 if 有効 else 0, 状態, now, 利用者ID, タスクID],
            )
        else:
            conn.execute(
                f"UPDATE {AIタスク要求テーブル} SET プロジェクト = ?, タイトル = ?, 要求内容 = ?, TASK_AI_NAME = ?, TASK_AI_MODEL = ?, 有効 = ?, 状態 = ?, "
                "PID = '', 終了日時 = ?, 更新日時 = ? "
                "WHERE 利用者ID = ? AND タスクID = ?",
                [プロジェクト, タイトル, 要求内容, TASK_AI_NAME, TASK_AI_MODEL, 1 if 有効 else 0, 状態, now, now, 利用者ID, タスクID],
            )
        conn.commit()
        return _タスク要求取得(conn, 利用者ID, タスクID)
    finally:
        conn.close()


def タスク有効更新(利用者ID: str, タスクID: str, 有効: bool) -> dict:
    """タスク要求と全タスク明細の有効フラグをまとめて更新する。"""
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        有効値 = 1 if 有効 else 0
        for テーブル in (AIタスク要求テーブル, AIタスク明細テーブル):
            conn.execute(
                f"UPDATE {_識別子(テーブル)} SET 有効 = ?, 更新日時 = ? WHERE 利用者ID = ? AND タスクID = ?",
                [有効値, now, 利用者ID, タスクID],
            )
        conn.commit()
        return _タスク要求取得(conn, 利用者ID, タスクID)
    finally:
        conn.close()


def 明細有効更新(利用者ID: str, タスクID: str, 明細SEQ: int, 有効: bool) -> bool:
    """タスク明細 1 行の有効フラグを更新する。更新できたら True。"""
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        cur = conn.execute(
            f"UPDATE {AIタスク明細テーブル} SET 有効 = ?, 更新日時 = ? "
            "WHERE 利用者ID = ? AND タスクID = ? AND 明細SEQ = ?",
            [1 if 有効 else 0, now, 利用者ID, タスクID, 明細SEQ],
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def 明細更新登録(
    利用者ID: str,
    タスクID: str,
    明細SEQ: int,
    タイトル: str,
    要求内容: str,
    先行SEQ: str,
    TASK_AI_NAME: str,
    TASK_AI_MODEL: str,
    有効: bool,
    状態: str,
) -> dict:
    """明細編集ダイアログの内容で AIタスク明細 1 行を更新する。"""
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        if 状態 == "待機":
            cur = conn.execute(
                f"UPDATE {AIタスク明細テーブル} SET タイトル = ?, 要求内容 = ?, 先行SEQ = ?, TASK_AI_NAME = ?, TASK_AI_MODEL = ?, 有効 = ?, 状態 = ?, "
                "PID = '', 開始日時 = '', 終了日時 = '', 実行回数 = 0, 応答内容 = '', 更新日時 = ? "
                "WHERE 利用者ID = ? AND タスクID = ? AND 明細SEQ = ?",
                [タイトル, 要求内容, 先行SEQ, TASK_AI_NAME, TASK_AI_MODEL, 1 if 有効 else 0, 状態, now, 利用者ID, タスクID, 明細SEQ],
            )
        else:
            cur = conn.execute(
                f"UPDATE {AIタスク明細テーブル} SET タイトル = ?, 要求内容 = ?, 先行SEQ = ?, TASK_AI_NAME = ?, TASK_AI_MODEL = ?, 有効 = ?, 状態 = ?, "
                "PID = '', 更新日時 = ? WHERE 利用者ID = ? AND タスクID = ? AND 明細SEQ = ?",
                [タイトル, 要求内容, 先行SEQ, TASK_AI_NAME, TASK_AI_MODEL, 1 if 有効 else 0, 状態, now, 利用者ID, タスクID, 明細SEQ],
            )
        conn.execute(
            f"UPDATE {AIタスク要求テーブル} SET 更新日時 = ? WHERE 利用者ID = ? AND タスクID = ?",
            [now, 利用者ID, タスクID],
        )
        conn.commit()
        if cur.rowcount <= 0:
            return {}
        return タスク明細取得(利用者ID, タスクID, 明細SEQ)
    finally:
        conn.close()


def タスク明細全削除(利用者ID: str, タスクID: str) -> int:
    """指定タスクの AIタスク明細を全削除する（sub_init の再生成前クリア用）。"""
    初期化()
    conn = 接続取得()
    try:
        cur = conn.execute(
            f"DELETE FROM {AIタスク明細テーブル} WHERE 利用者ID = ? AND タスクID = ?",
            [利用者ID, タスクID],
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def 残存PID一覧() -> list[dict]:
    """AIタスク要求・AIタスク明細に残っている PID を返す（システム開始時のクリーンアップ用）。"""
    初期化()
    conn = 接続取得()
    try:
        結果: list[dict] = []
        for テーブル in (AIタスク要求テーブル, AIタスク明細テーブル):
            rows = conn.execute(
                f"SELECT 利用者ID, タスクID, PID FROM {_識別子(テーブル)} WHERE PID != ''"
            ).fetchall()
            結果.extend({"テーブル": テーブル, **dict(row)} for row in rows)
        return 結果
    finally:
        conn.close()


def PID全クリア() -> None:
    """AIタスク要求・AIタスク明細の PID をすべてクリアする（クリア後は監視ループが再実行する）。

    実行中のまま残った AIタスク明細は 待機 に戻して再実行対象にする。
    """
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        conn.execute(
            f"UPDATE {AIタスク明細テーブル} SET 状態 = '待機' WHERE PID != '' AND 状態 = '実行中'"
        )
        for テーブル in (AIタスク要求テーブル, AIタスク明細テーブル):
            conn.execute(f"UPDATE {_識別子(テーブル)} SET PID = '', 更新日時 = ? WHERE PID != ''", [now])
        conn.commit()
    finally:
        conn.close()


def タスク本登録(
    利用者ID: str,
    タスクID: str,
    タイトル: str,
    要求内容: str,
    マーメイド記号: str,
    明細: list[dict],
) -> dict:
    """AI 生成結果で AIタスク要求・AIタスク明細を書き込む。仮登録は削除（同タスクIDで置き換え）。

    仮登録の プロジェクト・有効・開始日時・実行回数 は引き継ぎ、終了日時を記録して PID をクリアする。
    有効フラグは各 AIタスク明細にもコピーする（明細実行の可否判定に使う）。
    """
    初期化()
    conn = 接続取得()
    try:
        仮 = _タスク要求取得(conn, 利用者ID, タスクID)
        有効値 = int(仮.get("有効", 1)) if 仮 else 1
        要求TASK_AI_NAME = str(仮.get("TASK_AI_NAME", TASK_AI_NAME既定) or TASK_AI_NAME既定)
        要求TASK_AI_MODEL = str(仮.get("TASK_AI_MODEL", TASK_AI_MODEL既定) or TASK_AI_MODEL既定)
        conn.execute(f"DELETE FROM {AIタスク要求テーブル} WHERE 利用者ID = ? AND タスクID = ?", [利用者ID, タスクID])
        conn.execute(f"DELETE FROM {AIタスク明細テーブル} WHERE 利用者ID = ? AND タスクID = ?", [利用者ID, タスクID])
        監査 = _監査項目(利用者ID, 利用者ID)
        監査カラム = ", ".join(監査.keys())
        監査値 = list(監査.values())
        conn.execute(
            f"INSERT INTO {AIタスク要求テーブル} (利用者ID, タスクID, プロジェクト, タイトル, 要求内容, TASK_AI_NAME, TASK_AI_MODEL, 有効, 状態, マーメイド記号, "
            f"PID, 開始日時, 終了日時, 実行回数, {監査カラム}) "
            f"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, {', '.join('?' * len(監査値))})",
            [
                利用者ID, タスクID, str(仮.get("プロジェクト", "")), タイトル, 要求内容,
                要求TASK_AI_NAME, 要求TASK_AI_MODEL, 有効値, "準備完了", マーメイド記号,
                "",
                str(仮.get("開始日時", "")),
                _現在日時(),
                int(仮.get("実行回数", 0) or 0),
                *監査値,
            ],
        )
        for 行 in 明細:
            明細SEQ = int(行["明細SEQ"])
            conn.execute(
                f"INSERT INTO {AIタスク明細テーブル} (利用者ID, タスクID, 明細SEQ, タイトル, 要求内容, 先行SEQ, TASK_AI_NAME, TASK_AI_MODEL, 有効, 状態, {監査カラム}) "
                f"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, {', '.join('?' * len(監査値))})",
                [
                    利用者ID,
                    タスクID,
                    明細SEQ,
                    str(行.get("タイトル", "")),
                    str(行.get("要求内容", "")),
                    str(行.get("先行SEQ", "")),
                    要求TASK_AI_NAME,
                    要求TASK_AI_MODEL,
                    有効値,
                    "待機",
                    *監査値,
                ],
            )
        conn.commit()
        return _タスク要求取得(conn, 利用者ID, タスクID)
    finally:
        conn.close()


def タスク失敗(利用者ID: str, タスクID: str, メッセージ: str) -> dict:
    """AI 生成に失敗した仮タスクを『失敗』の完了タスクにする（終了日時を記録し PID をクリア）。"""
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        conn.execute(
            f"UPDATE {AIタスク要求テーブル} SET 状態 = '失敗', 要求内容 = 要求内容 || ?, "
            "PID = '', 終了日時 = ?, 更新日時 = ? WHERE 利用者ID = ? AND タスクID = ?",
            [f"\n[エラー] {メッセージ}", now, now, 利用者ID, タスクID],
        )
        conn.commit()
        return _タスク要求取得(conn, 利用者ID, タスクID)
    finally:
        conn.close()
