# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""AIタスクの DB アクセス。

AIタスク要求 / AIタスク明細 テーブルを backend_server の共有 SQLite に作成し、
一覧取得・登録を提供する。Alembic は使わず CREATE TABLE IF NOT EXISTS で管理する。
"""

from __future__ import annotations

import os
import json
import sqlite3
from datetime import datetime, timedelta

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.normpath(os.path.join(_BASE_DIR, "..", "backend_server", "_data", "AiDiy"))
DB_PATH = os.path.join(DB_DIR, "database.db")

_初期化済み = False

AIタスク要求テーブル = "Aタスク要求"
AIタスク明細テーブル = "Aタスク明細"
AIタスク実行条件テーブル = "Aタスク実行条件"
AIチーム作業テーブル = "Aチーム作業"
AIチーム要員テーブル = "Aチーム要員"
AIチーム状況テーブル = "Aチーム状況"
_採番テーブル = "C採番"
_採番ID = "Aタスク要求"
_採番プレフィックス = "TK"
_採番初期値 = 1000
TASK_AI_NAME既定 = "claude_cli"
TASK_AI_MODEL既定 = "auto"
要求PKカラム = ["タスクID"]
明細PKカラム = ["タスクID", "明細SEQ"]
要求カラム順 = [
    "タスクID",
    "利用者ID",
    "プロジェクト",
    "タイトル",
    "要求内容",
    "TASK_AI_NAME",
    "TASK_AI_MODEL",
    "実行有効",
    "状態",
    "マーメイド記号",
    "PID",
    "開始日時",
    "終了日時",
    "実行回数",
    "応答タイトル",
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
明細カラム順 = [
    "タスクID",
    "明細SEQ",
    "タイトル",
    "要求内容",
    "先行SEQ",
    "TASK_AI_NAME",
    "TASK_AI_MODEL",
    "操作検証",
    "実行有効",
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
実行条件PKカラム = ["利用者ID", "タスクID"]
実行条件カラム順 = [
    "利用者ID",
    "タスクID",
    "実行区分",
    "間隔区分",
    "間隔値",
    "定時区分",
    "実行曜日",
    "実行日",
    "開始時刻",
    "実行条件",
    "監視フォルダ",
    "フォルダ内ファイル数",
    "フォルダ内最終日時",
    "前回実行日時",
    "次回実行日時",
    "登録日時",
    "登録利用者ID",
    "登録利用者名",
    "登録端末ID",
    "更新日時",
    "更新利用者ID",
    "更新利用者名",
    "更新端末ID",
]

# 実行条件の区分は文字値で保持する（状態と同じ日本語ファースト方針）
実行区分値 = ("即時", "時間指定", "間隔実行", "定時実行")
間隔区分値 = ("分", "時", "日")
定時区分値 = ("毎日", "毎週", "毎月")
実行曜日値 = ("日", "月", "火", "水", "木", "金", "土")
実行条件値 = ("無し", "フォルダ変化")

# ダイアログから登録する入力カラム（残りはウォッチャーが管理するサーバー項目）
実行条件入力カラム = [
    "実行区分",
    "間隔区分",
    "間隔値",
    "定時区分",
    "実行曜日",
    "実行日",
    "開始時刻",
    "実行条件",
    "監視フォルダ",
]
実行条件既定値: dict[str, object] = {
    "実行区分": "即時",
    "間隔区分": "",
    "間隔値": 0,
    "定時区分": "",
    "実行曜日": "",
    "実行日": 0,
    "開始時刻": "",
    "実行条件": "無し",
    "監視フォルダ": "",
    "フォルダ内ファイル数": -1,
    "フォルダ内最終日時": "",
    "前回実行日時": "",
    "次回実行日時": "",
}


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


def _採番確保(conn: sqlite3.Connection) -> None:
    """C採番（backend_server共有）にAタスク要求用の採番行が無ければ作成する。"""
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {_識別子(_採番テーブル)} (
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
        INSERT OR IGNORE INTO {_識別子(_採番テーブル)} (
            採番ID, 最終採番値, 採番備考, 有効,
            登録日時, 登録利用者ID, 登録利用者名, 登録端末ID,
            更新日時, 更新利用者ID, 更新利用者名, 更新端末ID
        ) VALUES (?, ?, ?, 1, ?, 'system', 'システム', 'backend_task', ?, 'system', 'システム', 'backend_task')
        """,
        [_採番ID, _採番初期値, "AIタスク要求の採番（TK）", now, now],
    )


def 新規タスクID() -> str:
    conn = 接続取得()
    try:
        _採番確保(conn)
        conn.execute(
            f"UPDATE {_識別子(_採番テーブル)} SET 最終採番値 = 最終採番値 + 1 WHERE 採番ID = ?",
            [_採番ID],
        )
        行 = conn.execute(
            f"SELECT 最終採番値 FROM {_識別子(_採番テーブル)} WHERE 採番ID = ?",
            [_採番ID],
        ).fetchone()
        conn.commit()
        return f"{_採番プレフィックス}{行[0]:08d}"
    finally:
        conn.close()


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
            タスクID TEXT NOT NULL,
            利用者ID TEXT NOT NULL,
            プロジェクト TEXT NOT NULL DEFAULT '',
            タイトル TEXT NOT NULL,
            要求内容 TEXT NOT NULL DEFAULT '',
            TASK_AI_NAME TEXT NOT NULL DEFAULT 'claude_cli',
            TASK_AI_MODEL TEXT NOT NULL DEFAULT 'auto',
            実行有効 INTEGER NOT NULL DEFAULT 1,
            状態 TEXT NOT NULL DEFAULT '準備完了',
            マーメイド記号 TEXT NOT NULL DEFAULT '',
            PID TEXT NOT NULL DEFAULT '',
            開始日時 TEXT NOT NULL DEFAULT '',
            終了日時 TEXT NOT NULL DEFAULT '',
            実行回数 INTEGER NOT NULL DEFAULT 0,
            応答タイトル TEXT NOT NULL DEFAULT '',
            応答内容 TEXT NOT NULL DEFAULT '',
            {_監査カラムDDL},
            PRIMARY KEY (タスクID)
        )
    """)


def _AIタスク明細テーブル作成(conn: sqlite3.Connection) -> None:
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {AIタスク明細テーブル} (
            タスクID TEXT NOT NULL,
            明細SEQ INTEGER NOT NULL,
            タイトル TEXT NOT NULL,
            要求内容 TEXT NOT NULL DEFAULT '',
            先行SEQ TEXT NOT NULL DEFAULT '',
            TASK_AI_NAME TEXT NOT NULL DEFAULT 'claude_cli',
            TASK_AI_MODEL TEXT NOT NULL DEFAULT 'auto',
            操作検証 INTEGER NOT NULL DEFAULT 0,
            実行有効 INTEGER NOT NULL DEFAULT 1,
            状態 TEXT NOT NULL DEFAULT '待機',
            PID TEXT NOT NULL DEFAULT '',
            開始日時 TEXT NOT NULL DEFAULT '',
            終了日時 TEXT NOT NULL DEFAULT '',
            実行回数 INTEGER NOT NULL DEFAULT 0,
            応答内容 TEXT NOT NULL DEFAULT '',
            {_監査カラムDDL},
            PRIMARY KEY (タスクID, 明細SEQ)
        )
    """)


def _AIタスク実行条件テーブル作成(conn: sqlite3.Connection) -> None:
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {AIタスク実行条件テーブル} (
            利用者ID TEXT NOT NULL,
            タスクID TEXT NOT NULL,
            実行区分 TEXT NOT NULL DEFAULT '即時',
            間隔区分 TEXT NOT NULL DEFAULT '',
            間隔値 INTEGER NOT NULL DEFAULT 0,
            定時区分 TEXT NOT NULL DEFAULT '',
            実行曜日 TEXT NOT NULL DEFAULT '',
            実行日 INTEGER NOT NULL DEFAULT 0,
            開始時刻 TEXT NOT NULL DEFAULT '',
            実行条件 TEXT NOT NULL DEFAULT '無し',
            監視フォルダ TEXT NOT NULL DEFAULT '',
            フォルダ内ファイル数 INTEGER NOT NULL DEFAULT -1,
            フォルダ内最終日時 TEXT NOT NULL DEFAULT '',
            前回実行日時 TEXT NOT NULL DEFAULT '',
            次回実行日時 TEXT NOT NULL DEFAULT '',
            {_監査カラムDDL},
            PRIMARY KEY (利用者ID, タスクID)
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
            elif カラム == "実行有効":
                # 旧カラム名「有効」からの移行時は値を引き継ぐ
                select_exprs.append(_識別子("有効") if "有効" in 旧カラム else "1")
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
            elif カラム == "実行有効":
                # 旧カラム名「有効」からの移行時は値を引き継ぐ
                select_exprs.append(_識別子("有効") if "有効" in 旧カラム else "1")
            elif カラム == "操作検証":
                select_exprs.append("0")
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


def _AIタスク実行条件テーブル再作成(conn: sqlite3.Connection) -> None:
    if _テーブル存在(conn, AIタスク実行条件テーブル):
        旧テーブル = f"{AIタスク実行条件テーブル}_old"
        conn.execute(f"DROP TABLE IF EXISTS {_識別子(旧テーブル)}")
        conn.execute(f"ALTER TABLE {_識別子(AIタスク実行条件テーブル)} RENAME TO {_識別子(旧テーブル)}")
        _AIタスク実行条件テーブル作成(conn)
        旧カラム = set(_カラム名一覧(conn, 旧テーブル))
        select_exprs: list[str] = []
        params: list[object] = []
        for カラム in 実行条件カラム順:
            if カラム in 旧カラム:
                select_exprs.append(_識別子(カラム))
            elif カラム in 実行条件既定値:
                select_exprs.append("?")
                params.append(実行条件既定値[カラム])
            else:
                select_exprs.append("''")
        conn.execute(
            f"INSERT INTO {_識別子(AIタスク実行条件テーブル)} ({', '.join(_識別子(c) for c in 実行条件カラム順)}) "
            f"SELECT {', '.join(select_exprs)} FROM {_識別子(旧テーブル)}",
            params,
        )
        conn.execute(f"DROP TABLE IF EXISTS {_識別子(旧テーブル)}")
        return
    _AIタスク実行条件テーブル作成(conn)


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
        _AIタスク実行条件テーブル作成(conn)
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
        if (
            _PKカラム一覧(conn, AIタスク実行条件テーブル) != 実行条件PKカラム
            or _カラム名一覧(conn, AIタスク実行条件テーブル) != 実行条件カラム順
        ):
            _AIタスク実行条件テーブル再作成(conn)
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
            f"INSERT INTO {AIタスク明細テーブル} (タスクID, 明細SEQ, タイトル, 先行SEQ, TASK_AI_NAME, TASK_AI_MODEL, 状態, {監査カラム}) "
            f"VALUES (?, ?, ?, ?, ?, ?, ?, {', '.join('?' * len(監査値))})",
            [タスクID, 明細SEQ, タイトル, 先行SEQ, task_ai_name, task_ai_model, "待機", *監査値],
        )
    return タスクID


def _要求応答補完(conn: sqlite3.Connection, 利用者ID: str, タスクID: str = "") -> int:
    """要求側の応答欄が空の場合、最新の完了明細から補完する。

    実行中サーバーの世代差などで明細だけに応答が残ったデータを、一覧/API取得時に
    自己修復するための補助処理。既に要求側へ応答が入っている行は上書きしない。
    """
    条件 = "r.利用者ID = ? AND (r.応答タイトル = '' OR r.応答内容 = '')"
    params: list[object] = [利用者ID]
    if タスクID:
        条件 += " AND r.タスクID = ?"
        params.append(タスクID)

    rows = conn.execute(
        f"""
        SELECT r.利用者ID, r.タスクID,
               m.タイトル AS 応答タイトル,
               m.応答内容 AS 応答内容
          FROM {AIタスク要求テーブル} r
          JOIN {AIタスク明細テーブル} m
            ON m.タスクID = r.タスクID
         WHERE {条件}
           AND m.状態 = '完了'
           AND m.応答内容 != ''
           AND m.更新日時 = (
                SELECT MAX(m2.更新日時)
                  FROM {AIタスク明細テーブル} m2
                 WHERE m2.タスクID = r.タスクID
                   AND m2.状態 = '完了'
                   AND m2.応答内容 != ''
           )
         ORDER BY r.タスクID, m.明細SEQ DESC
        """,
        params,
    ).fetchall()

    更新件数 = 0
    更新済み: set[tuple[str, str]] = set()
    now = _現在日時()
    for row in rows:
        key = (str(row["利用者ID"]), str(row["タスクID"]))
        if key in 更新済み:
            continue
        conn.execute(
            f"UPDATE {AIタスク要求テーブル} SET 応答タイトル = ?, 応答内容 = ?, 更新日時 = ? "
            "WHERE 利用者ID = ? AND タスクID = ?",
            [str(row["応答タイトル"] or ""), str(row["応答内容"] or ""), now, key[0], key[1]],
        )
        更新済み.add(key)
        更新件数 += 1
    return 更新件数


def タスク要求一覧(利用者ID: str) -> list[dict]:
    初期化()
    conn = 接続取得()
    try:
        if _要求応答補完(conn, 利用者ID):
            conn.commit()
        rows = conn.execute(
            "SELECT r.利用者ID, r.タスクID, r.プロジェクト, r.タイトル, r.要求内容, r.TASK_AI_NAME, r.TASK_AI_MODEL, r.実行有効, r.状態, r.マーメイド記号, "
            "r.PID, r.開始日時, r.終了日時, r.実行回数, r.応答タイトル, r.応答内容, r.更新日時, "
            "COALESCE(j.次回実行日時, '') AS 次回実行日時 "
            f"FROM {AIタスク要求テーブル} r "
            f"LEFT JOIN {AIタスク実行条件テーブル} j ON j.利用者ID = r.利用者ID AND j.タスクID = r.タスクID "
            "WHERE r.利用者ID = ? "
            "ORDER BY CASE WHEN r.タスクID GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].*' THEN 1 ELSE 0 END DESC, "
            "r.タスクID DESC",
            [利用者ID],
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def タスク要求最大更新日時(利用者ID: str) -> str:
    初期化()
    conn = 接続取得()
    try:
        if _要求応答補完(conn, 利用者ID):
            conn.commit()
        # 実行条件（次回実行日時など）の更新も一覧の再取得対象にする
        row = conn.execute(
            "SELECT MAX(m) AS 最大更新日時 FROM ("
            f"SELECT MAX(更新日時) AS m FROM {AIタスク要求テーブル} WHERE 利用者ID = ? "
            f"UNION ALL SELECT MAX(更新日時) FROM {AIタスク実行条件テーブル} WHERE 利用者ID = ?)",
            [利用者ID, 利用者ID],
        ).fetchone()
        return str(row["最大更新日時"] or "") if row else ""
    finally:
        conn.close()


def タスク明細一覧(タスクID: str) -> list[dict]:
    初期化()
    conn = 接続取得()
    try:
        rows = conn.execute(
            "SELECT タスクID, 明細SEQ, タイトル, 要求内容, 先行SEQ, TASK_AI_NAME, TASK_AI_MODEL, 操作検証, 実行有効, 状態, "
            f"PID, 開始日時, 終了日時, 実行回数, 応答内容, 更新日時 FROM {AIタスク明細テーブル} "
            "WHERE タスクID = ? ORDER BY 明細SEQ",
            [タスクID],
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def タスク明細取得(タスクID: str, 明細SEQ: int) -> dict:
    初期化()
    conn = 接続取得()
    try:
        row = conn.execute(
            "SELECT タスクID, 明細SEQ, タイトル, 要求内容, 先行SEQ, TASK_AI_NAME, TASK_AI_MODEL, 操作検証, 実行有効, 状態, "
            f"PID, 開始日時, 終了日時, 実行回数, 応答内容 FROM {AIタスク明細テーブル} "
            "WHERE タスクID = ? AND 明細SEQ = ?",
            [タスクID, 明細SEQ],
        ).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


def タスク明細最大更新日時(タスクID: str) -> str:
    初期化()
    conn = 接続取得()
    try:
        row = conn.execute(
            f"SELECT MAX(更新日時) AS 最大更新日時 FROM {AIタスク明細テーブル} "
            "WHERE タスクID = ?",
            [タスクID],
        ).fetchone()
        return str(row["最大更新日時"] or "") if row else ""
    finally:
        conn.close()


def タスク要求登録(利用者ID: str, タイトル: str, 要求内容: str) -> dict:
    """タスク要求を登録し、標準工程明細を自動生成する。"""
    初期化()
    conn = 接続取得()
    try:
        タスクID = _タスク登録(conn, 利用者ID, タイトル, 要求内容, "待機", _標準明細テンプレート)
        conn.commit()
        return _タスク要求取得(conn, 利用者ID, タスクID)
    finally:
        conn.close()


def _タスク要求取得(conn: sqlite3.Connection, 利用者ID: str, タスクID: str) -> dict:
    row = conn.execute(
        "SELECT 利用者ID, タスクID, プロジェクト, タイトル, 要求内容, TASK_AI_NAME, TASK_AI_MODEL, 実行有効, 状態, マーメイド記号, "
        f"PID, 開始日時, 終了日時, 実行回数, 応答タイトル, 応答内容, 更新日時 FROM {AIタスク要求テーブル} "
        "WHERE 利用者ID = ? AND タスクID = ?",
        [利用者ID, タスクID],
    ).fetchone()
    return dict(row) if row else {}


def _タスク要求取得byタスクID(conn: sqlite3.Connection, タスクID: str) -> dict:
    """明細側の操作（利用者IDを持たない）から親要求を返すためのタスクID単独版。"""
    row = conn.execute(
        "SELECT 利用者ID, タスクID, プロジェクト, タイトル, 要求内容, TASK_AI_NAME, TASK_AI_MODEL, 実行有効, 状態, マーメイド記号, "
        f"PID, 開始日時, 終了日時, 実行回数, 応答タイトル, 応答内容, 更新日時 FROM {AIタスク要求テーブル} "
        "WHERE タスクID = ?",
        [タスクID],
    ).fetchone()
    return dict(row) if row else {}


def _Aチーム作業反映(
    conn: sqlite3.Connection,
    タスクID: str,
    状態: str | None = None,
    応答タイトル: str | None = None,
    応答内容: str | None = None,
    guard: str = "状態 != 'エラー'",
) -> None:
    """タスクIDがAチーム作業から投入されたものであれば、状態・応答内容をチーム側にも反映する。

    Aチーム作業とAタスク要求は同一SQLiteを共有しているため、同一トランザクションで直接UPDATEする
    （タスクIDが一致しなければ何も更新されない）。guardはAチーム作業側の現在状態に対する条件で、
    通常は既にエラーの項目を上書きしない。エラー化や再試行（エラーからの復帰）は呼び出し側で指定する。
    """
    項目: dict[str, str] = {}
    if 状態 is not None:
        項目["状態"] = 状態
    if 応答タイトル is not None:
        項目["応答タイトル"] = 応答タイトル
    if 応答内容 is not None:
        項目["応答内容"] = 応答内容
    if not 項目:
        return
    now = _現在日時()
    設定 = ", ".join(f"{列} = ?" for 列 in 項目)
    条件 = f"WHERE タスクID = ? AND {guard}" if guard else "WHERE タスクID = ?"
    conn.execute(
        f"UPDATE {AIチーム作業テーブル} SET {設定}, 更新日時 = ? {条件}",
        [*項目.values(), now, タスクID],
    )


def タスク要求取得(利用者ID: str, タスクID: str) -> dict:
    """AIタスク要求 1 件を取得する。"""
    初期化()
    conn = 接続取得()
    try:
        if _要求応答補完(conn, 利用者ID, タスクID):
            conn.commit()
        return _タスク要求取得(conn, 利用者ID, タスクID)
    finally:
        conn.close()


def _実行条件取得(conn: sqlite3.Connection, 利用者ID: str, タスクID: str) -> dict:
    row = conn.execute(
        "SELECT 利用者ID, タスクID, 実行区分, 間隔区分, 間隔値, 定時区分, 実行曜日, 実行日, 開始時刻, "
        "実行条件, 監視フォルダ, フォルダ内ファイル数, フォルダ内最終日時, 前回実行日時, 次回実行日時, 更新日時 "
        f"FROM {AIタスク実行条件テーブル} WHERE 利用者ID = ? AND タスクID = ?",
        [利用者ID, タスクID],
    ).fetchone()
    return dict(row) if row else {}


def 実行条件取得(利用者ID: str, タスクID: str) -> dict:
    """AIタスク実行条件 1 件を取得する。行が無ければ空 dict（即時扱い）。"""
    初期化()
    conn = 接続取得()
    try:
        return _実行条件取得(conn, 利用者ID, タスクID)
    finally:
        conn.close()


def 実行条件監視一覧() -> list[dict]:
    """毎分の発火確認対象（時間駆動またはフォルダ変化条件）を親要求の状態つきで返す。"""
    初期化()
    conn = 接続取得()
    try:
        rows = conn.execute(
            "SELECT j.利用者ID, j.タスクID, j.実行区分, j.間隔区分, j.間隔値, j.定時区分, j.実行曜日, j.実行日, j.開始時刻, "
            "j.実行条件, j.監視フォルダ, j.フォルダ内ファイル数, j.フォルダ内最終日時, j.前回実行日時, j.次回実行日時, "
            "r.状態 AS 要求状態, r.実行有効 AS 要求実行有効 "
            f"FROM {AIタスク実行条件テーブル} j JOIN {AIタスク要求テーブル} r "
            "ON r.利用者ID = j.利用者ID AND r.タスクID = j.タスクID "
            "WHERE j.実行区分 IN ('時間指定', '間隔実行', '定時実行') OR j.実行条件 = 'フォルダ変化' "
            "ORDER BY j.タスクID"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def 即時発火対象一覧() -> list[dict]:
    """即時実行かつ実行有効・準備完了の要求を返す（実行条件行が無い場合も即時扱い）。

    即時実行（実行区分='即時'）は時間駆動条件を持たないため 実行条件監視一覧() の対象外であり、
    放置すると準備完了のまま次回実行が発火しない。10 秒ループの先頭でこの一覧を確認し、
    タスク発火() で待機に戻すことで、条件監視より前に毎回（1 分ゲート無しで）再実行させる。
    """
    初期化()
    conn = 接続取得()
    try:
        rows = conn.execute(
            f"SELECT r.利用者ID, r.タスクID FROM {AIタスク要求テーブル} r "
            f"LEFT JOIN {AIタスク実行条件テーブル} j ON j.利用者ID = r.利用者ID AND j.タスクID = r.タスクID "
            "WHERE r.実行有効 = 1 AND r.状態 = '準備完了' "
            "AND (j.実行区分 IS NULL OR j.実行区分 = '即時') "
            "ORDER BY r.タスクID"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def 実行条件監視取得(利用者ID: str, タスクID: str) -> dict | None:
    """発火確認と同じ形（親要求の状態つき）で実行条件 1 件を返す（無ければ None）。"""
    初期化()
    conn = 接続取得()
    try:
        row = conn.execute(
            "SELECT j.利用者ID, j.タスクID, j.実行区分, j.間隔区分, j.間隔値, j.定時区分, j.実行曜日, j.実行日, j.開始時刻, "
            "j.実行条件, j.監視フォルダ, j.フォルダ内ファイル数, j.フォルダ内最終日時, j.前回実行日時, j.次回実行日時, "
            "r.状態 AS 要求状態, r.実行有効 AS 要求実行有効 "
            f"FROM {AIタスク実行条件テーブル} j JOIN {AIタスク要求テーブル} r "
            "ON r.利用者ID = j.利用者ID AND r.タスクID = j.タスクID "
            "WHERE j.利用者ID = ? AND j.タスクID = ?",
            [利用者ID, タスクID],
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def 次回実行日時更新(利用者ID: str, タスクID: str, 次回実行日時: str, 前回実行日時: str | None = None) -> None:
    """実行条件の次回実行日時（発火時は前回実行日時も）を更新する。"""
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        if 前回実行日時 is None:
            conn.execute(
                f"UPDATE {AIタスク実行条件テーブル} SET 次回実行日時 = ?, 更新日時 = ? "
                "WHERE 利用者ID = ? AND タスクID = ?",
                [次回実行日時, now, 利用者ID, タスクID],
            )
        else:
            conn.execute(
                f"UPDATE {AIタスク実行条件テーブル} SET 次回実行日時 = ?, 前回実行日時 = ?, 更新日時 = ? "
                "WHERE 利用者ID = ? AND タスクID = ?",
                [次回実行日時, 前回実行日時, now, 利用者ID, タスクID],
            )
        conn.commit()
    finally:
        conn.close()


def 発火対象外次回実行日時クリア() -> int:
    """発火対象外の実行条件の次回実行日時を一括で空にして件数を返す。

    対象外 = 時間駆動（時間指定/間隔実行/定時実行）でない、または保持可能状態
    （実行有効 かつ 要求が 待機/実行中/準備完了/完了）でないもの。監視ループの
    対象にならない行（即時など）も含めて漏れなくクリアする。
    """
    初期化()
    conn = 接続取得()
    try:
        cur = conn.execute(
            f"UPDATE {AIタスク実行条件テーブル} SET 次回実行日時 = '', 更新日時 = ? "
            "WHERE 次回実行日時 != '' AND ("
            "実行区分 NOT IN ('時間指定', '間隔実行', '定時実行') "
            f"OR NOT EXISTS (SELECT 1 FROM {AIタスク要求テーブル} r "
            f"WHERE r.利用者ID = {AIタスク実行条件テーブル}.利用者ID "
            f"AND r.タスクID = {AIタスク実行条件テーブル}.タスクID "
            "AND r.実行有効 = 1 AND r.状態 IN ('待機', '実行中', '準備完了', '完了')))",
            [_現在日時()],
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def フォルダ状態記録(利用者ID: str, タスクID: str, ファイル数: int, 最終日時: str) -> None:
    """フォルダ変化判定用のスナップショット（ファイル数・最終更新日時）を保存する。"""
    初期化()
    conn = 接続取得()
    try:
        conn.execute(
            f"UPDATE {AIタスク実行条件テーブル} SET フォルダ内ファイル数 = ?, フォルダ内最終日時 = ?, 更新日時 = ? "
            "WHERE 利用者ID = ? AND タスクID = ?",
            [ファイル数, 最終日時, _現在日時(), 利用者ID, タスクID],
        )
        conn.commit()
    finally:
        conn.close()


def 明細全件有効待機化(タスクID: str) -> int:
    """準備完了への戻し時: 全明細を 実行有効=1・状態=待機 に戻して再実行可能にする。

    PID・開始日時・終了日時・実行回数もリセットする（タスク発火と同じ初期化）。
    """
    初期化()
    conn = 接続取得()
    try:
        cur = conn.execute(
            f"UPDATE {AIタスク明細テーブル} SET 実行有効 = 1, 状態 = '待機', PID = '', "
            "開始日時 = '', 終了日時 = '', 実行回数 = 0, 更新日時 = ? "
            "WHERE タスクID = ?",
            [_現在日時(), タスクID],
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def タスク発火(利用者ID: str, タスクID: str) -> bool:
    """実行開始条件の成立時: 明細 → 要求の順で 待機 に戻し、再実行対象にする。

    要求が 準備完了 / 完了 かつ実行有効、明細が全件待機または全件完了のときだけ発火する
    （実行途中・エラー・中止のタスクは開始させない）。
    明細は PID・開始日時・終了日時・実行回数もリセットする（応答内容は次回実行で上書き）。
    """
    初期化()
    conn = 接続取得()
    try:
        req = conn.execute(
            f"SELECT 状態, 実行有効 FROM {AIタスク要求テーブル} WHERE 利用者ID = ? AND タスクID = ?",
            [利用者ID, タスクID],
        ).fetchone()
        if req is None or str(req["状態"]) not in ("準備完了", "完了") or int(req["実行有効"] or 0) != 1:
            return False
        明細状態 = {
            str(row[0])
            for row in conn.execute(
                f"SELECT DISTINCT 状態 FROM {AIタスク明細テーブル} WHERE タスクID = ?",
                [タスクID],
            )
        }
        if 明細状態 not in ({"待機"}, {"完了"}):
            return False
        now = _現在日時()
        conn.execute(
            f"UPDATE {AIタスク明細テーブル} SET 状態 = '待機', PID = '', 開始日時 = '', 終了日時 = '', "
            "実行回数 = 0, 更新日時 = ? WHERE タスクID = ?",
            [now, タスクID],
        )
        conn.execute(
            f"UPDATE {AIタスク要求テーブル} SET 状態 = '待機', PID = '', 更新日時 = ? "
            "WHERE 利用者ID = ? AND タスクID = ?",
            [now, 利用者ID, タスクID],
        )
        conn.commit()
        return True
    finally:
        conn.close()


def 実行条件登録(利用者ID: str, タスクID: str, 条件: dict) -> dict:
    """ダイアログ入力の実行条件を UPSERT する。

    入力カラムだけを書き込み、ウォッチャー管理のサーバー項目
    （フォルダスナップショット・前回/次回実行日時）は既存値を保持する。
    """
    初期化()
    conn = 接続取得()
    try:
        値: dict[str, object] = {k: 実行条件既定値[k] for k in 実行条件入力カラム}
        for k in 実行条件入力カラム:
            if k in 条件 and 条件[k] is not None:
                値[k] = 条件[k]
        now = _現在日時()
        既存 = conn.execute(
            f"SELECT 1 FROM {AIタスク実行条件テーブル} WHERE 利用者ID = ? AND タスクID = ?",
            [利用者ID, タスクID],
        ).fetchone()
        if 既存:
            conn.execute(
                f"UPDATE {AIタスク実行条件テーブル} SET "
                + ", ".join(f"{_識別子(k)} = ?" for k in 実行条件入力カラム)
                + ", 更新日時 = ?, 更新利用者ID = ?, 更新利用者名 = ?, 更新端末ID = ? "
                "WHERE 利用者ID = ? AND タスクID = ?",
                [*[値[k] for k in 実行条件入力カラム], now, 利用者ID, 利用者ID, "backend_task", 利用者ID, タスクID],
            )
        else:
            監査 = _監査項目(利用者ID, 利用者ID)
            conn.execute(
                f"INSERT INTO {AIタスク実行条件テーブル} (利用者ID, タスクID, "
                + ", ".join(_識別子(k) for k in 実行条件入力カラム)
                + f", {', '.join(監査.keys())}) "
                f"VALUES (?, ?, {', '.join('?' * len(実行条件入力カラム))}, {', '.join('?' * len(監査))})",
                [利用者ID, タスクID, *[値[k] for k in 実行条件入力カラム], *監査.values()],
            )
        conn.commit()
        return _実行条件取得(conn, 利用者ID, タスクID)
    finally:
        conn.close()


def 仮タスク登録(
    タスクID: str,
    タイトル: str,
    要求内容: str,
    利用者ID: str,
    プロジェクト: str = "",
    TASK_AI_NAME: str = TASK_AI_NAME既定,
    TASK_AI_MODEL: str = TASK_AI_MODEL既定,
    実行有効: bool = True,
) -> dict:
    """AI生成待ちの仮タスクを「準備開始」で登録する（実行は監視ループに任せる）。"""
    初期化()
    conn = 接続取得()
    try:
        監査 = _監査項目(利用者ID, 利用者ID)
        監査カラム = ", ".join(監査.keys())
        監査値 = list(監査.values())
        conn.execute(
            f"INSERT INTO {AIタスク要求テーブル} (利用者ID, タスクID, プロジェクト, タイトル, 要求内容, TASK_AI_NAME, TASK_AI_MODEL, 実行有効, 状態, {監査カラム}) "
            f"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, {', '.join('?' * len(監査値))})",
            [利用者ID, タスクID, プロジェクト, タイトル, 要求内容, TASK_AI_NAME, TASK_AI_MODEL, 1 if 実行有効 else 0, "準備開始", *監査値],
        )
        conn.commit()
        return _タスク要求取得(conn, 利用者ID, タスクID)
    finally:
        conn.close()


def 実行待ち一覧() -> list[dict]:
    """PID未設定の仮登録（準備開始）を返す。監視ループが5秒間隔で確認する。"""
    初期化()
    conn = 接続取得()
    try:
        rows = conn.execute(
            "SELECT 利用者ID, タスクID, プロジェクト, タイトル, 要求内容, TASK_AI_NAME, TASK_AI_MODEL, 実行回数, 登録利用者ID "
            f"FROM {AIタスク要求テーブル} WHERE 状態 = '準備開始' AND PID = '' ORDER BY タスクID"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def 実行開始記録(利用者ID: str, タスクID: str, pid: int) -> None:
    """sub_init起動時に準備中へ進め、PID・開始日時・実行回数を記録する。"""
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        conn.execute(
            f"UPDATE {AIタスク要求テーブル} SET 状態 = '準備中', PID = ?, 開始日時 = ?, "
            "終了日時 = '', 実行回数 = 実行回数 + 1, 更新日時 = ? "
            "WHERE 利用者ID = ? AND タスクID = ? AND 状態 = '準備開始' AND PID = ''",
            [str(pid), now, now, 利用者ID, タスクID],
        )
        conn.commit()
    finally:
        conn.close()


def 実行待ち明細一覧() -> list[dict]:
    """実行可能な AIタスク明細（実行有効・待機・PID なし・先行 SEQ が全て完了）を返す。

    親の AIタスク要求が 待機 / 実行中 のものだけを対象とする
    （準備開始・準備中・準備完了・失敗・完了のタスクは実行しない。準備完了は実行開始条件の充足待ちに使う）。
    明細の 実行有効 = 0 は実行対象にしない（明細作成は実行有効フラグに関係なく行う）。
    """
    初期化()
    conn = 接続取得()
    try:
        rows = conn.execute(
            "SELECT m.タスクID, m.明細SEQ, m.タイトル, m.先行SEQ, m.TASK_AI_NAME, m.TASK_AI_MODEL, m.実行回数 "
            f"FROM {AIタスク明細テーブル} m JOIN {AIタスク要求テーブル} r "
            "ON r.タスクID = m.タスクID "
            "WHERE m.実行有効 = 1 AND m.状態 = '待機' AND m.PID = '' AND r.状態 IN ('待機', '実行中') "
            "ORDER BY m.タスクID, m.明細SEQ"
        ).fetchall()
        候補 = [dict(row) for row in rows]
        if not 候補:
            return []

        # タスクごとの明細状態マップで先行 SEQ の完了を確認する
        状態マップ: dict[str, dict[int, str]] = {}
        for タスクID in {行["タスクID"] for 行 in 候補}:
            状態マップ[タスクID] = {
                int(r[0]): str(r[1])
                for r in conn.execute(
                    f"SELECT 明細SEQ, 状態 FROM {AIタスク明細テーブル} "
                    "WHERE タスクID = ?",
                    [タスクID],
                )
            }

        実行可能: list[dict] = []
        for 行 in 候補:
            状態表 = 状態マップ[行["タスクID"]]
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
            "SELECT タスクID, 明細SEQ, タイトル, PID "
            f"FROM {AIタスク明細テーブル} WHERE PID != '' ORDER BY タスクID, 明細SEQ"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def 明細実行開始記録(タスクID: str, 明細SEQ: int, pid: int) -> None:
    """明細実行の開始: 状態=実行中・PID・開始日時・実行回数+1。"""
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        conn.execute(
            f"UPDATE {AIタスク明細テーブル} SET 状態 = '実行中', PID = ?, 開始日時 = ?, "
            "実行回数 = 実行回数 + 1, 更新日時 = ? "
            "WHERE タスクID = ? AND 明細SEQ = ?",
            [str(pid), now, now, タスクID, 明細SEQ],
        )
        conn.execute(
            f"UPDATE {AIタスク要求テーブル} SET 状態 = CASE WHEN 状態 = '待機' THEN '実行中' ELSE 状態 END, "
            "更新日時 = ? WHERE タスクID = ?",
            [now, タスクID],
        )
        conn.commit()
    finally:
        conn.close()


def 明細完了(タスクID: str, 明細SEQ: int, 応答内容: str = "") -> dict:
    """明細を完了にする。全明細が完了したら AIタスク要求も完了にする。

    完了した明細のタイトルと応答内容は AIタスク要求の 応答タイトル・応答内容 へ
    反映する（最新ステップの結果表示用）。
    """
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        cur = conn.execute(
            f"UPDATE {AIタスク明細テーブル} SET 状態 = '完了', 終了日時 = ?, PID = '', 応答内容 = ?, 更新日時 = ? "
            "WHERE タスクID = ? AND 明細SEQ = ? AND 状態 != 'エラー'",
            [now, 応答内容, now, タスクID, 明細SEQ],
        )
        if cur.rowcount <= 0:
            conn.commit()
            return _タスク要求取得byタスクID(conn, タスクID)
        行 = conn.execute(
            f"SELECT タイトル FROM {AIタスク明細テーブル} "
            "WHERE タスクID = ? AND 明細SEQ = ?",
            [タスクID, 明細SEQ],
        ).fetchone()
        応答タイトル = str(行["タイトル"]) if 行 else ""
        残 = conn.execute(
            f"SELECT COUNT(*) FROM {AIタスク明細テーブル} "
            "WHERE タスクID = ? AND 状態 != '完了'",
            [タスクID],
        ).fetchone()[0]
        if 残 == 0:
            conn.execute(
                f"UPDATE {AIタスク要求テーブル} SET 状態 = '完了', 終了日時 = ?, 応答タイトル = ?, 応答内容 = ?, 更新日時 = ? "
                "WHERE タスクID = ? AND 状態 != 'エラー'",
                [now, 応答タイトル, 応答内容, now, タスクID],
            )
            _Aチーム作業反映(conn, タスクID, 状態="完了", 応答タイトル=応答タイトル, 応答内容=応答内容)
        else:
            conn.execute(
                f"UPDATE {AIタスク要求テーブル} SET 応答タイトル = ?, 応答内容 = ?, 更新日時 = ? "
                "WHERE タスクID = ? AND 状態 != 'エラー'",
                [応答タイトル, 応答内容, now, タスクID],
            )
            _Aチーム作業反映(conn, タスクID, 応答タイトル=応答タイトル, 応答内容=応答内容)
        conn.commit()
        return _タスク要求取得byタスクID(conn, タスクID)
    finally:
        conn.close()


def 開始明細完了(タスクID: str, 明細SEQ: int, 応答内容: str = "開始処理を完了しました。") -> dict:
    """開始明細を完了し、AIタスク要求を実行中にする。

    実行中への切り替え時に AIタスク要求の 応答タイトル・応答内容 はクリアする
    （前回実行分の結果を残さない）。
    """
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        cur = conn.execute(
            f"UPDATE {AIタスク明細テーブル} SET 状態 = '完了', 終了日時 = ?, PID = '', 応答内容 = ?, 更新日時 = ? "
            "WHERE タスクID = ? AND 明細SEQ = ? AND 状態 != 'エラー'",
            [now, 応答内容, now, タスクID, 明細SEQ],
        )
        if cur.rowcount <= 0:
            conn.commit()
            return _タスク要求取得byタスクID(conn, タスクID)
        conn.execute(
            f"UPDATE {AIタスク要求テーブル} SET 状態 = '実行中', 開始日時 = ?, 終了日時 = '', 実行回数 = 1, PID = '', "
            "応答タイトル = '', 応答内容 = '', 更新日時 = ? "
            "WHERE タスクID = ? AND 状態 != 'エラー'",
            [now, now, タスクID],
        )
        _Aチーム作業反映(conn, タスクID, 状態="実行中", 応答タイトル="", 応答内容="")
        conn.commit()
        return _タスク要求取得byタスクID(conn, タスクID)
    finally:
        conn.close()


def 終了明細完了(タスクID: str, 明細SEQ: int, 応答内容: str = "終了処理を完了しました。") -> dict:
    """終了明細を完了し、AIタスク要求を完了にする。

    AIタスク要求の 応答タイトル には終了明細のタイトル（通常「終了」）、
    応答内容 には検証の結論を反映する。
    """
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        cur = conn.execute(
            f"UPDATE {AIタスク明細テーブル} SET 状態 = '完了', 終了日時 = ?, PID = '', 応答内容 = ?, 更新日時 = ? "
            "WHERE タスクID = ? AND 明細SEQ = ? AND 状態 != 'エラー'",
            [now, 応答内容, now, タスクID, 明細SEQ],
        )
        if cur.rowcount <= 0:
            conn.commit()
            return _タスク要求取得byタスクID(conn, タスクID)
        行 = conn.execute(
            f"SELECT タイトル FROM {AIタスク明細テーブル} "
            "WHERE タスクID = ? AND 明細SEQ = ?",
            [タスクID, 明細SEQ],
        ).fetchone()
        応答タイトル = str(行["タイトル"]) if 行 else "終了"
        conn.execute(
            f"UPDATE {AIタスク要求テーブル} SET 状態 = '完了', 終了日時 = ?, PID = '', 応答タイトル = ?, 応答内容 = ?, 更新日時 = ? "
            "WHERE タスクID = ? AND 状態 != 'エラー'",
            [now, 応答タイトル, 応答内容, now, タスクID],
        )
        _Aチーム作業反映(conn, タスクID, 状態="完了", 応答タイトル=応答タイトル, 応答内容=応答内容)
        conn.commit()
        return _タスク要求取得byタスクID(conn, タスクID)
    finally:
        conn.close()


def 明細再試行(タスクID: str, 明細SEQ: int) -> dict:
    """自動リカバリーの再試行前に、明細とタスク要求の状態を実行中へ戻す（sub_proc.py 用）。

    操作検証NG・未報告により明細とタスク要求がエラーになっていても、再試行のため実行中に戻す。
    """
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        conn.execute(
            f"UPDATE {AIタスク明細テーブル} SET 状態 = '実行中', 終了日時 = '', 応答内容 = '', 更新日時 = ? "
            "WHERE タスクID = ? AND 明細SEQ = ?",
            [now, タスクID, 明細SEQ],
        )
        conn.execute(
            f"UPDATE {AIタスク要求テーブル} SET 状態 = '実行中', 更新日時 = ? "
            "WHERE タスクID = ? AND 状態 = 'エラー'",
            [now, タスクID],
        )
        _Aチーム作業反映(conn, タスクID, 状態="実行中", guard="状態 = 'エラー'")
        conn.commit()
        return _タスク要求取得byタスクID(conn, タスクID)
    finally:
        conn.close()


def 明細失敗(タスクID: str, 明細SEQ: int, メッセージ: str) -> dict:
    """明細をエラーにし、AIタスク要求もエラーにする（後続の実行を止める）。"""
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        conn.execute(
            f"UPDATE {AIタスク明細テーブル} SET 状態 = 'エラー', 終了日時 = ?, PID = '', 応答内容 = ?, 更新日時 = ? "
            "WHERE タスクID = ? AND 明細SEQ = ?",
            [now, メッセージ, now, タスクID, 明細SEQ],
        )
        conn.execute(
            f"UPDATE {AIタスク要求テーブル} SET 状態 = 'エラー', 要求内容 = 要求内容 || ?, 更新日時 = ? "
            "WHERE タスクID = ?",
            [f"\n[エラー] SEQ{明細SEQ}: {メッセージ}", now, タスクID],
        )
        _Aチーム作業反映(conn, タスクID, 状態="エラー", 応答内容=f"[エラー] SEQ{明細SEQ}: {メッセージ}", guard="")
        conn.commit()
        return _タスク要求取得byタスクID(conn, タスクID)
    finally:
        conn.close()


def タスクPID一覧(利用者ID: str, タスクID: str) -> list[int]:
    """指定タスクの AIタスク要求・AIタスク明細に残っている PID を返す。"""
    初期化()
    conn = 接続取得()
    try:
        結果: list[int] = []
        rows = conn.execute(
            f"SELECT PID FROM {AIタスク要求テーブル} WHERE 利用者ID = ? AND タスクID = ? AND PID != ''",
            [利用者ID, タスクID],
        ).fetchall()
        結果.extend(int(row[0]) for row in rows if str(row[0]).strip().isdigit())
        rows = conn.execute(
            f"SELECT PID FROM {AIタスク明細テーブル} WHERE タスクID = ? AND PID != ''",
            [タスクID],
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
            "WHERE タスクID = ? AND PID != '' AND 状態 = '実行中'",
            [タスクID],
        )
        conn.execute(
            f"UPDATE {AIタスク要求テーブル} SET PID = '', 更新日時 = ? "
            "WHERE 利用者ID = ? AND タスクID = ? AND PID != ''",
            [now, 利用者ID, タスクID],
        )
        conn.execute(
            f"UPDATE {AIタスク明細テーブル} SET PID = '', 更新日時 = ? "
            "WHERE タスクID = ? AND PID != ''",
            [now, タスクID],
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
    実行有効: bool,
    状態: str,
) -> dict:
    """修正ダイアログの内容で AIタスク要求を更新する（PID クリア済み前提）。

    準備開始（再準備）は開始日時・終了日時・実行回数をリセットし、監視ループに再分解させる。
    """
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        タイトル = 要求内容.splitlines()[0][:40] if 要求内容 else ""
        if 状態 == "準備開始":
            conn.execute(
                f"UPDATE {AIタスク要求テーブル} SET プロジェクト = ?, タイトル = ?, 要求内容 = ?, TASK_AI_NAME = ?, TASK_AI_MODEL = ?, 実行有効 = ?, 状態 = ?, "
                "PID = '', 開始日時 = '', 終了日時 = '', 実行回数 = 0, 更新日時 = ? "
                "WHERE 利用者ID = ? AND タスクID = ?",
                [プロジェクト, タイトル, 要求内容, TASK_AI_NAME, TASK_AI_MODEL, 1 if 実行有効 else 0, 状態, now, 利用者ID, タスクID],
            )
        elif 状態 == "中止":
            conn.execute(
                f"UPDATE {AIタスク要求テーブル} SET プロジェクト = ?, タイトル = ?, 要求内容 = ?, TASK_AI_NAME = ?, TASK_AI_MODEL = ?, 実行有効 = ?, 状態 = ?, "
                "PID = '', 終了日時 = ?, 更新日時 = ? "
                "WHERE 利用者ID = ? AND タスクID = ?",
                [プロジェクト, タイトル, 要求内容, TASK_AI_NAME, TASK_AI_MODEL, 1 if 実行有効 else 0, 状態, now, now, 利用者ID, タスクID],
            )
        else:
            # 更新前の状態を保持する更新: 終了日時は打刻しない
            conn.execute(
                f"UPDATE {AIタスク要求テーブル} SET プロジェクト = ?, タイトル = ?, 要求内容 = ?, TASK_AI_NAME = ?, TASK_AI_MODEL = ?, 実行有効 = ?, 状態 = ?, "
                "PID = '', 更新日時 = ? "
                "WHERE 利用者ID = ? AND タスクID = ?",
                [プロジェクト, タイトル, 要求内容, TASK_AI_NAME, TASK_AI_MODEL, 1 if 実行有効 else 0, 状態, now, 利用者ID, タスクID],
            )
        conn.commit()
        return _タスク要求取得(conn, 利用者ID, タスクID)
    finally:
        conn.close()


def タスク実行有効更新(利用者ID: str, タスクID: str, 実行有効: bool) -> dict:
    """タスク要求と全タスク明細の実行有効フラグをまとめて更新する。"""
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        実行有効値 = 1 if 実行有効 else 0
        conn.execute(
            f"UPDATE {AIタスク要求テーブル} SET 実行有効 = ?, 更新日時 = ? WHERE 利用者ID = ? AND タスクID = ?",
            [実行有効値, now, 利用者ID, タスクID],
        )
        conn.execute(
            f"UPDATE {AIタスク明細テーブル} SET 実行有効 = ?, 更新日時 = ? WHERE タスクID = ?",
            [実行有効値, now, タスクID],
        )
        conn.commit()
        return _タスク要求取得(conn, 利用者ID, タスクID)
    finally:
        conn.close()


def 明細実行有効更新(タスクID: str, 明細SEQ: int, 実行有効: bool) -> bool:
    """タスク明細 1 行の実行有効フラグを更新する。更新できたら True。"""
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        cur = conn.execute(
            f"UPDATE {AIタスク明細テーブル} SET 実行有効 = ?, 更新日時 = ? "
            "WHERE タスクID = ? AND 明細SEQ = ?",
            [1 if 実行有効 else 0, now, タスクID, 明細SEQ],
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def 明細更新登録(
    タスクID: str,
    明細SEQ: int,
    タイトル: str,
    要求内容: str,
    先行SEQ: str,
    TASK_AI_NAME: str,
    TASK_AI_MODEL: str,
    操作検証: bool,
    実行有効: bool,
    状態: str,
) -> dict:
    """明細編集ダイアログの内容で AIタスク明細 1 行を更新する。"""
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        if 状態 == "待機":
            cur = conn.execute(
                f"UPDATE {AIタスク明細テーブル} SET タイトル = ?, 要求内容 = ?, 先行SEQ = ?, TASK_AI_NAME = ?, TASK_AI_MODEL = ?, 操作検証 = ?, 実行有効 = ?, 状態 = ?, "
                "PID = '', 開始日時 = '', 終了日時 = '', 実行回数 = 0, 応答内容 = '', 更新日時 = ? "
                "WHERE タスクID = ? AND 明細SEQ = ?",
                [タイトル, 要求内容, 先行SEQ, TASK_AI_NAME, TASK_AI_MODEL, 1 if 操作検証 else 0, 1 if 実行有効 else 0, 状態, now, タスクID, 明細SEQ],
            )
        else:
            cur = conn.execute(
                f"UPDATE {AIタスク明細テーブル} SET タイトル = ?, 要求内容 = ?, 先行SEQ = ?, TASK_AI_NAME = ?, TASK_AI_MODEL = ?, 操作検証 = ?, 実行有効 = ?, 状態 = ?, "
                "PID = '', 更新日時 = ? WHERE タスクID = ? AND 明細SEQ = ?",
                [タイトル, 要求内容, 先行SEQ, TASK_AI_NAME, TASK_AI_MODEL, 1 if 操作検証 else 0, 1 if 実行有効 else 0, 状態, now, タスクID, 明細SEQ],
            )
        conn.execute(
            f"UPDATE {AIタスク要求テーブル} SET 更新日時 = ? WHERE タスクID = ?",
            [now, タスクID],
        )
        conn.commit()
        if cur.rowcount <= 0:
            return {}
        return タスク明細取得(タスクID, 明細SEQ)
    finally:
        conn.close()


def タスク明細全削除(タスクID: str) -> int:
    """指定タスクの AIタスク明細を全削除する（sub_init の再生成前クリア用）。"""
    初期化()
    conn = 接続取得()
    try:
        cur = conn.execute(
            f"DELETE FROM {AIタスク明細テーブル} WHERE タスクID = ?",
            [タスクID],
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
        rows = conn.execute(
            f"SELECT 利用者ID, タスクID, PID FROM {AIタスク要求テーブル} WHERE PID != ''"
        ).fetchall()
        結果.extend({"テーブル": AIタスク要求テーブル, **dict(row)} for row in rows)
        rows = conn.execute(
            f"SELECT タスクID, PID FROM {AIタスク明細テーブル} WHERE PID != ''"
        ).fetchall()
        結果.extend({"テーブル": AIタスク明細テーブル, **dict(row)} for row in rows)
        return 結果
    finally:
        conn.close()


def PID全クリア() -> None:
    """システム開始時: AIタスク要求・AIタスク明細に残った PID をエラーとして記録しクリアする。

    再起動時点でプロセスが生きているか判断できず、PID は OS に再利用され得るため
    強制停止はしない（別プロセスを誤って停止する恐れがあるため）。自動再実行はせずエラー化のみ行う。
    """
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        for テーブル in (AIタスク要求テーブル, AIタスク明細テーブル):
            conn.execute(
                f"UPDATE {_識別子(テーブル)} SET 状態 = 'エラー', 実行有効 = 0, "
                "終了日時 = ?, PID = '', 応答内容 = ?, 更新日時 = ? "
                "WHERE PID != ''",
                [now, "システム再起動のため中断しました", now],
            )
        conn.commit()
    finally:
        conn.close()


def タイムアウト対象一覧(制限分: int = 30) -> list[dict]:
    """開始日時だけが入ったまま制限分以上経過した行を返す。

    AIタスク要求・AIタスク明細の両方が対象。PID は残すと実行中扱いのまま
    後続明細が起動できないため、呼び出し側で PID のプロセスを停止してから
    タイムアウト対象エラー化() でエラー化する。
    """
    初期化()
    conn = 接続取得()
    try:
        閾値 = (datetime.now() - timedelta(minutes=制限分)).strftime("%Y-%m-%d %H:%M:%S")
        条件 = "開始日時 != '' AND 終了日時 = '' AND 状態 != 'エラー' AND 開始日時 <= ?"
        結果: list[dict] = []
        rows = conn.execute(
            f"SELECT 利用者ID, タスクID, '' AS 明細SEQ, 状態, PID, 開始日時 "
            f"FROM {AIタスク要求テーブル} WHERE {条件}",
            [閾値],
        ).fetchall()
        結果.extend({"テーブル": AIタスク要求テーブル, **dict(row)} for row in rows)
        rows = conn.execute(
            f"SELECT タスクID, 明細SEQ, 状態, PID, 開始日時 "
            f"FROM {AIタスク明細テーブル} WHERE {条件}",
            [閾値],
        ).fetchall()
        結果.extend({"テーブル": AIタスク明細テーブル, **dict(row)} for row in rows)
        return 結果
    finally:
        conn.close()


def タイムアウト対象エラー化(対象一覧: list[dict]) -> int:
    """タイムアウト対象を 状態='エラー'・実行有効=0・PID='' にする。"""
    if not 対象一覧:
        return 0
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        更新件数 = 0
        for 行 in 対象一覧:
            テーブル = str(行.get("テーブル", ""))
            タスクID = str(行.get("タスクID", ""))
            PID = str(行.get("PID", ""))
            開始日時 = str(行.get("開始日時", ""))
            if テーブル not in (AIタスク要求テーブル, AIタスク明細テーブル) or not タスクID:
                continue
            if テーブル == AIタスク明細テーブル:
                cur = conn.execute(
                    f"UPDATE {AIタスク明細テーブル} SET 状態 = 'エラー', 実行有効 = 0, PID = '', 更新日時 = ? "
                    "WHERE タスクID = ? AND 明細SEQ = ? "
                    "AND 状態 != 'エラー' AND 終了日時 = '' AND PID = ? AND 開始日時 = ?",
                    [now, タスクID, int(行.get("明細SEQ", 0) or 0), PID, 開始日時],
                )
            else:
                利用者ID = str(行.get("利用者ID", ""))
                if not 利用者ID:
                    continue
                cur = conn.execute(
                    f"UPDATE {AIタスク要求テーブル} SET 状態 = 'エラー', 実行有効 = 0, PID = '', 更新日時 = ? "
                    "WHERE 利用者ID = ? AND タスクID = ? "
                    "AND 状態 != 'エラー' AND 終了日時 = '' AND PID = ? AND 開始日時 = ?",
                    [now, 利用者ID, タスクID, PID, 開始日時],
                )
            更新件数 += cur.rowcount
        conn.commit()
        return 更新件数
    finally:
        conn.close()


def タイムアウトエラー化(制限分: int = 30) -> list[dict]:
    """互換用: タイムアウト対象を取得して、そのままエラー化する。"""
    対象一覧 = タイムアウト対象一覧(制限分)
    タイムアウト対象エラー化(対象一覧)
    return 対象一覧


def タスク本登録(
    利用者ID: str,
    タスクID: str,
    タイトル: str,
    要求内容: str,
    マーメイド記号: str,
    明細: list[dict],
    応答内容: str = "",
) -> dict:
    """AI 生成結果で AIタスク要求・AIタスク明細を書き込む。仮登録は削除（同タスクIDで置き換え）。

    仮登録の プロジェクト・実行有効・開始日時・実行回数 は引き継ぎ、終了日時を記録して PID をクリアする。
    実行有効フラグは各 AIタスク明細にもコピーする（明細実行の可否判定に使う）。
    要求の状態は常に 準備完了（実行開始条件の充足待ち）で書き込む。即時実行の場合は
    実行条件監視ループが 10 秒ごとに 準備完了 を 待機 へ戻して即座に実行を開始する。
    要求内容には仮登録時の人間の入力をそのまま引き継ぎ、AI がタスク分解のために整理した文章は
    応答内容へ書き込む（人間の元の要求が上書きされて消えないようにするため）。
    """
    初期化()
    conn = 接続取得()
    try:
        仮 = _タスク要求取得(conn, 利用者ID, タスクID)
        if str(仮.get("状態", "")) == "エラー":
            return 仮
        実行有効値 = int(仮.get("実行有効", 1)) if 仮 else 1
        要求TASK_AI_NAME = str(仮.get("TASK_AI_NAME", TASK_AI_NAME既定) or TASK_AI_NAME既定)
        要求TASK_AI_MODEL = str(仮.get("TASK_AI_MODEL", TASK_AI_MODEL既定) or TASK_AI_MODEL既定)
        初期状態 = "準備完了"
        conn.execute(f"DELETE FROM {AIタスク要求テーブル} WHERE 利用者ID = ? AND タスクID = ?", [利用者ID, タスクID])
        conn.execute(f"DELETE FROM {AIタスク明細テーブル} WHERE タスクID = ?", [タスクID])
        監査 = _監査項目(利用者ID, 利用者ID)
        監査カラム = ", ".join(監査.keys())
        監査値 = list(監査.values())
        conn.execute(
            f"INSERT INTO {AIタスク要求テーブル} (利用者ID, タスクID, プロジェクト, タイトル, 要求内容, TASK_AI_NAME, TASK_AI_MODEL, 実行有効, 状態, マーメイド記号, "
            f"PID, 開始日時, 終了日時, 実行回数, 応答内容, {監査カラム}) "
            f"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, {', '.join('?' * len(監査値))})",
            [
                利用者ID, タスクID, str(仮.get("プロジェクト", "")), タイトル, 要求内容,
                要求TASK_AI_NAME, 要求TASK_AI_MODEL, 実行有効値, 初期状態, マーメイド記号,
                "",
                str(仮.get("開始日時", "")),
                _現在日時(),
                int(仮.get("実行回数", 0) or 0),
                応答内容,
                *監査値,
            ],
        )
        for 行 in 明細:
            明細SEQ = int(行["明細SEQ"])
            conn.execute(
                f"INSERT INTO {AIタスク明細テーブル} (タスクID, 明細SEQ, タイトル, 要求内容, 先行SEQ, TASK_AI_NAME, TASK_AI_MODEL, 操作検証, 実行有効, 状態, {監査カラム}) "
                f"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, {', '.join('?' * len(監査値))})",
                [
                    タスクID,
                    明細SEQ,
                    str(行.get("タイトル", "")),
                    str(行.get("要求内容", "")),
                    str(行.get("先行SEQ", "")),
                    要求TASK_AI_NAME,
                    要求TASK_AI_MODEL,
                    1 if 行.get("操作検証") else 0,
                    実行有効値,
                    "待機",
                    *監査値,
                ],
            )
        conn.commit()
        return _タスク要求取得(conn, 利用者ID, タスクID)
    finally:
        conn.close()


def タスク失敗(利用者ID: str, タスクID: str, メッセージ: str) -> dict:
    """AI 生成に失敗した仮タスクを『エラー』の完了タスクにする（終了日時を記録し PID をクリア）。"""
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        conn.execute(
            f"UPDATE {AIタスク要求テーブル} SET 状態 = 'エラー', 要求内容 = 要求内容 || ?, "
            "PID = '', 終了日時 = ?, 更新日時 = ? WHERE 利用者ID = ? AND タスクID = ?",
            [f"\n[エラー] {メッセージ}", now, now, 利用者ID, タスクID],
        )
        conn.commit()
        return _タスク要求取得(conn, 利用者ID, タスクID)
    finally:
        conn.close()


def _チーム状況テーブル作成(conn: sqlite3.Connection) -> None:
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {AIチーム状況テーブル} (
            要員ID TEXT NOT NULL PRIMARY KEY,
            要員名 TEXT NOT NULL DEFAULT '',
            最終更新日時 TEXT NOT NULL DEFAULT '',
            待機数 INTEGER NOT NULL DEFAULT 0,
            実行数 INTEGER NOT NULL DEFAULT 0,
            完了数 INTEGER NOT NULL DEFAULT 0,
            エラー数 INTEGER NOT NULL DEFAULT 0,
            更新日時 TEXT NOT NULL DEFAULT ''
        )
    """)


def チーム状況更新() -> int:
    """有効なAチーム要員 × 実行有効なAタスク要求（24時間以内更新）を要員IDで集計し、Aチーム状況を作り直す。

    実行開始条件の監視ループ（10秒間隔）の最後に毎回呼ばれる。
    Aチーム要員はbackend_team側が作成するテーブルのため、未起動などで存在しない場合は何もしない。
    """
    初期化()
    conn = 接続取得()
    try:
        now = _現在日時()
        閾値 = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        _チーム状況テーブル作成(conn)
        try:
            conn.execute(f"DELETE FROM {AIチーム状況テーブル}")
            conn.execute(
                f"""
                INSERT INTO {AIチーム状況テーブル}
                    (要員ID, 要員名, 最終更新日時, 待機数, 実行数, 完了数, エラー数, 更新日時)
                SELECT
                    c.要員ID,
                    c.要員名,
                    MAX(t.更新日時),
                    SUM(CASE WHEN t.状態 IN ('準備完了', '待機') THEN 1 ELSE 0 END),
                    SUM(CASE WHEN t.状態 IN ('準備中', '実行中') THEN 1 ELSE 0 END),
                    SUM(CASE WHEN t.状態 = '完了' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN t.状態 = 'エラー' THEN 1 ELSE 0 END),
                    ?
                  FROM {AIチーム要員テーブル} c
                  JOIN {AIタスク要求テーブル} t ON t.利用者ID = c.要員ID
                 WHERE c.有効 = 1
                   AND t.実行有効 = 1
                   AND t.更新日時 >= ?
                 GROUP BY c.要員ID, c.要員名
                """,
                [now, 閾値],
            )
        except sqlite3.OperationalError:
            conn.rollback()
            return 0
        件数 = conn.execute(f"SELECT COUNT(*) FROM {AIチーム状況テーブル}").fetchone()[0]
        conn.commit()
        return 件数
    finally:
        conn.close()
