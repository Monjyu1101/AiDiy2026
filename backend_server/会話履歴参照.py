# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""次入力予測用のプロジェクト履歴参照。DB の作成・変更は行わない。"""

from collections import deque
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3

from 会話履歴パス import normalize_project_path


HISTORY_MAX_TURNS = 10
HISTORY_WINDOW_SECONDS = 2 * 60 * 60
_ROLES = {
    "input_text": "user",
    "input_request": "user",
    "output_text": "assistant",
    "output_request": "assistant",
}


def _local_second(now: datetime | None) -> datetime:
    """DB の datetime.now().strftime と同じサーバーローカル・秒精度に揃える。"""
    value = datetime.now() if now is None else now
    if not isinstance(value, datetime):
        raise ValueError("now は日時で指定してください")
    if value.tzinfo is not None:
        value = value.astimezone().replace(tzinfo=None)
    return value.replace(microsecond=0)


def read_prediction_history(
    database_path: str | Path,
    project_path: str,
    max_turns: int = HISTORY_MAX_TURNS,
    max_chars: int = 24000,
    max_message_chars: int = 4000,
    *,
    now: datetime | None = None,
) -> list[dict[str, str | int]]:
    """直近2時間の同一プロジェクトから最新最大10ターンを古い順に返す。

    1ターンは同一セッション・チャンネルのユーザー入力と、次の入力までの
    返答群。未返信入力も1ターン。期間外入力への返答だけを拾うことはしない。
    戻り値は role / content / turn_id。交差する会話を混同しないよう、関連する
    入出力に同じ一時的な turn_id を付ける。セッションIDはモデルに渡さない。

    時間範囲は呼び出し時点のローカル時刻（秒精度）から2時間前まで、両端を
    含む。未来・期間外・所属不明・他プロジェクトへフォールバックしない。
    now は呼び出し元で一度確定した時刻／検証用。aware値はサーバー時刻へ変換。

    期間内の候補をカーソルで順次処理し、最新 max_turns ターンだけを保持する。
    本文は各 max_message_chars 文字、最終総計 max_chars 文字まで。文字数制限時も
    入力を先に確保し、新しいターン・新しい返答を優先する。古い会話で補充しない。
    DB 初期化・マイグレーション・書込は行わず、DB不在等は sqlite3.Error。
    """
    normalized_path = normalize_project_path(project_path)
    if normalized_path is None:
        raise ValueError("プロジェクトパスは空でない絶対パスで指定してください")
    for name, value in (
        ("max_turns", max_turns),
        ("max_chars", max_chars),
        ("max_message_chars", max_message_chars),
    ):
        if type(value) is not int or value <= 0:
            raise ValueError(f"{name} は正の整数で指定してください")
    if max_turns > HISTORY_MAX_TURNS:
        raise ValueError(f"max_turns は{HISTORY_MAX_TURNS}以下で指定してください")
    end = _local_second(now)
    start = end - timedelta(seconds=HISTORY_WINDOW_SECONDS)
    bounds = (start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S"))
    # 境界直前の元入力をch0ミラーだけで新しいターンと誤認しない。本文は返さない。
    mirror_bounds = ((start - timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S"), bounds[1])
    turns = deque()
    active = {}
    ordinal = 0

    # as_uri() で ? / # / % を含むファイル名も URI と混同せず扱う。
    uri = Path(database_path).absolute().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True, timeout=1.0)) as connection:
        connection.execute("PRAGMA query_only = ON")
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT h."セッションID", h."シーケンス", h."チャンネル",
                   h."メッセージ識別", h."登録日時",
                   substr(h."メッセージ内容", 1, ?) AS "本文"
              FROM "A会話履歴" AS h
             WHERE h."プロジェクトパス" = ?
               AND h."登録日時" BETWEEN ? AND ?
               AND h."チャンネル" IN ('0', '1', '2', '3', '4', '5', '6')
               AND h."メッセージ識別" IN (
                   'input_text', 'input_request', 'output_text', 'output_request'
               )
               AND typeof(h."メッセージ内容") = 'text'
               AND h."メッセージ内容" != ''
               AND NOT (h."チャンネル" = '0' AND EXISTS (
                   SELECT 1 FROM "A会話履歴" AS p
                    WHERE p."セッションID" = h."セッションID"
                      AND p."シーケンス" = h."シーケンス" - 1
                      AND p."プロジェクトパス" = h."プロジェクトパス"
                      AND p."登録日時" BETWEEN ? AND ?
                      AND p."チャンネル" IN ('1', '2', '3', '4', '5', '6')
                      AND ((p."メッセージ識別" = 'input_request' AND h."メッセージ識別" = 'input_text')
                        OR (p."メッセージ識別" = 'output_text' AND h."メッセージ識別" = 'output_request'))
                      AND p."メッセージ内容" = h."メッセージ内容"
                      AND CAST(strftime('%s', h."登録日時") AS INTEGER)
                        - CAST(strftime('%s', p."登録日時") AS INTEGER) BETWEEN 0 AND 1
               ))
             ORDER BY h."登録日時", h."セッションID", h."シーケンス"
            """,
            (max_message_chars, normalized_path, *bounds, *mirror_bounds),
        )
        for row in rows:
            # DB の保存形式以外や壊れた日時は推測せず除外する。
            try:
                stored = datetime.strptime(row["登録日時"], "%Y-%m-%d %H:%M:%S")
            except (TypeError, ValueError):
                continue
            if stored.strftime("%Y-%m-%d %H:%M:%S") != row["登録日時"] or not start <= stored <= end:
                continue
            content = row["本文"].strip()
            if not content:
                continue
            ordinal += 1
            lane = (row["セッションID"], row["チャンネル"])
            role = _ROLES[row["メッセージ識別"]]
            if role == "user":
                turn = {"lane": lane, "user": (ordinal, "user", content[:max_chars]),
                        "replies": deque(), "reply_chars": 0}
                turns.append(turn)
                active[lane] = turn
                if len(turns) > max_turns:
                    old = turns.popleft()
                    if active.get(old["lane"]) is old:
                        del active[old["lane"]]
            elif lane in active:
                turn = active[lane]
                room = max_chars - len(turn["user"][2])
                if room <= 0:
                    continue
                reply = content[:room]
                turn["replies"].append((ordinal, "assistant", reply))
                turn["reply_chars"] += len(reply)
                while turn["reply_chars"] > room:
                    old_index, old_role, old_content = turn["replies"].popleft()
                    excess = turn["reply_chars"] - room
                    removed = min(len(old_content), excess)
                    turn["reply_chars"] -= removed
                    if removed < len(old_content):
                        turn["replies"].appendleft((old_index, old_role, old_content[:-removed]))

    selected = []
    remaining = max_chars
    # 最新ターンから本文予算を割り当てる。返答だけが残ることはない。
    for turn_id, turn in reversed(list(enumerate(turns, 1))):
        if remaining <= 0:
            break
        index, role, content = turn["user"]
        content = content[:remaining]
        selected.append((index, {"role": role, "content": content, "turn_id": turn_id}))
        remaining -= len(content)
        for index, role, content in reversed(turn["replies"]):
            if remaining <= 0:
                break
            content = content[:remaining]
            selected.append((index, {"role": role, "content": content, "turn_id": turn_id}))
            remaining -= len(content)
    return [message for _, message in sorted(selected, key=lambda item: item[0])]
