# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""AIタスクの終了明細を処理するサブプロセス。

終了明細では最終ステータス更新の前に、sub_proc と同様の内容（処理目標と
実行済ステップの記録）を指定プロジェクトフォルダ・指定 AI へ渡し、
各実行ステップの検証と最終結果の検証を行って結論を応答内容へ記録する。
標準ライブラリのみで動作する。

処理の流れ:
1. 出力 JSON（AI 生成のタスク分解結果）から対象 SEQ（終了明細）を特定する
2. /task/タスク要求/取得 でプロジェクトを取得する
3. /task/タスク明細/一覧 から完了済み明細の応答内容を取得する
4. aidiy_code_agents MCP へ各実行ステップの検証と最終結果の検証を依頼する
5. 検証の結論を応答内容として /task/タスク明細/終了完了 を呼ぶ
"""

from __future__ import annotations

import json
import os
import sys
import traceback
import urllib.request
from urllib.parse import quote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TASK_API = "http://localhost:8093/task"
MCP_URL = "http://localhost:8095/aidiy_code_agents/run"
TASK_AI_NAME既定 = "claude_cli"
TASK_AI_MODEL既定 = "auto"

タスクID = ""
利用者ID = ""
ログパス = os.path.join(BASE_DIR, "temp", "task", "sub_terminate.log")


def ログ(メッセージ: str) -> None:
    print(メッセージ, flush=True)
    os.makedirs(os.path.dirname(ログパス), exist_ok=True)
    with open(ログパス, "a", encoding="utf-8") as f:
        f.write(メッセージ + "\n")


def POST送信(url: str, payload: dict, timeout: int = 3600) -> dict:
    # 日本語を含む URL パスは urllib がそのまま扱えないためパーセントエンコードする
    if url.startswith("http://"):
        本体 = url[len("http://"):]
        ホスト, _, パス = 本体.partition("/")
        url = "http://" + ホスト + "/" + quote(パス)
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode("utf-8"))


def タスク要求取得() -> dict:
    res = POST送信(f"{TASK_API}/タスク要求/取得", {
        "利用者ID": 利用者ID,
        "タスクID": タスクID,
    }, timeout=60)
    if res.get("status") != "OK":
        raise RuntimeError(f"AIタスク要求の取得に失敗しました: {res.get('message')}")
    return res.get("data", {}).get("item", {})


def 完了明細一覧取得() -> list[dict]:
    """完了済みの AIタスク明細（応答内容つき）を明細SEQ順で返す。"""
    res = POST送信(f"{TASK_API}/タスク明細/一覧", {
        "利用者ID": 利用者ID,
        "タスクID": タスクID,
    }, timeout=60)
    if res.get("status") != "OK":
        raise RuntimeError(f"タスク明細一覧の取得に失敗しました: {res.get('message')}")
    items = res.get("data", {}).get("items", [])
    return [行 for 行 in items if str(行.get("状態", "")).strip() == "完了"]


def プロンプト生成(データ: dict, 対象: dict, 完了明細: list[dict]) -> str:
    全ステップ = "\n".join(
        f"  {int(行['明細SEQ'])}. {str(行['タイトル']).strip()}（先行SEQ: {str(行['先行SEQ']).strip() or 'なし'}）"
        for 行 in データ["明細"]
    )
    実行済: list[str] = []
    for 行 in sorted(完了明細, key=lambda 行: int(行["明細SEQ"])):
        seq = int(行["明細SEQ"])
        タイトル = str(行.get("タイトル", "")).strip()
        応答内容 = str(行.get("応答内容", "")).strip()
        見出し = f"ステップ{seq} {タイトル} " + ("処理目標" if seq == 0 else "実行済")
        実行済.append(f"``` {見出し}\n{応答内容}\n```")
    実行済ブロック = "\n".join(実行済) if 実行済 else "（実行済ステップはまだありません）"
    return f"""あなたはタスクの 1 ステップを実行する担当です。今回のステップの作業だけを実行してください。

タスク全体のタイトル: {str(データ.get('タイトル', '')).strip()}

全ステップ:
{全ステップ}

実行済ステップの記録（ステップ0 開始 の応答内容が処理目標です）:
{実行済ブロック}

【今回のステップ】※この処理だけ実行してください。
ステップ{対象['明細SEQ']} {対象['タイトル']}
各実行ステップの検証と最終結果の検証をお願いします。

注意:
- 検証のみを行い、コードの修正や新しい作業は行わないでください。
- 処理目標に対して各実行ステップの記録と実際の成果物を照合し、最終結果を検証してください。
- AiDiy の MCP ツールが HTTP で利用できます。
  ツール一覧の確認: GET http://localhost:8095/<mcp名>/list
  ツールの実行: POST http://localhost:8095/<mcp名>/<メソッド> （JSON ボディ）
  例: aidiy_notification_sounds, aidiy_sqlite, aidiy_chrome_devtools など
- 検証した内容と結論（成功 / 問題あり）を簡潔に報告してください。
"""


def 検証実行(データ: dict, 対象: dict, 完了明細: list[dict], プロジェクト: str) -> str:
    """code_agents で各実行ステップと最終結果を検証し、結論を返す（失敗しても例外にしない）。"""
    try:
        task_ai_name = str(対象.get("TASK_AI_NAME", "") or TASK_AI_NAME既定).strip()
        task_ai_model = str(対象.get("TASK_AI_MODEL", "") or TASK_AI_MODEL既定).strip()
        ログ(f"code_agents run 呼び出し (検証, ai={task_ai_name}, model={task_ai_model}, project_path={プロジェクト})")
        payload = {"prompt": プロンプト生成(データ, 対象, 完了明細), "ai_name": task_ai_name, "ai_model": task_ai_model}
        if プロジェクト:
            payload["project_path"] = プロジェクト
        res = POST送信(MCP_URL, payload)
        ログ(f"code_agents run 応答: {json.dumps(res, ensure_ascii=False)[:500]}")
        if res.get("error") or res.get("status") != "OK":
            raise RuntimeError(f"code_agents の実行に失敗しました: {res.get('error') or res.get('result')}")
        結論 = str(res.get("result") or "").strip()
        return 結論 or "終了処理を完了しました。"
    except Exception as e:
        ログ(f"検証失敗: {e}")
        return f"終了処理を完了しました。\n[注意] 検証失敗: {e}"


def main() -> int:
    global タスクID, 利用者ID, ログパス
    try:
        if len(sys.argv) < 3:
            raise ValueError("使い方: python sub_terminate.py <temp/output/利用者ID.タスクID.json> <SEQ>")
        出力JSONパス = os.path.abspath(sys.argv[1])
        明細SEQ = int(sys.argv[2])
        ファイルステム = os.path.splitext(os.path.basename(出力JSONパス))[0]
        ログパス = os.path.join(BASE_DIR, "temp", "task", f"{ファイルステム}.step{明細SEQ}.log")

        # 1. 出力 JSON から対象（終了明細）を特定
        with open(出力JSONパス, "r", encoding="utf-8-sig") as f:
            データ = json.load(f)
        利用者ID = str(データ.get("利用者ID", "")).strip()
        タスクID = str(データ.get("タスクID", "")).strip()
        if not 利用者ID or not タスクID:
            raise ValueError("出力 JSON に 利用者ID または タスクID がありません")
        対象 = None
        for 行 in データ.get("明細", []):
            if isinstance(行, dict) and int(行["明細SEQ"]) == 明細SEQ:
                対象 = 行
                break
        if 対象 is None:
            raise ValueError(f"出力 JSON に SEQ={明細SEQ} の明細がありません")

        ログ(f"=== 終了処理: {利用者ID}/{タスクID} SEQ={明細SEQ} ===")

        # 2. AIタスク要求 からプロジェクトを取得
        要求 = タスク要求取得()
        プロジェクト = str(要求.get("プロジェクト", "")).strip()

        # 3. 完了済み明細の応答内容を取得（ステップ0 の処理目標と実行済ステップの記録）
        完了明細 = 完了明細一覧取得()
        ログ(f"完了明細取得: {len(完了明細)} 件")

        # 4. 各実行ステップの検証と最終結果の検証（結論を応答内容にする）
        応答内容 = 検証実行(データ, 対象, 完了明細, プロジェクト)

        # 5. 検証の結論を応答内容として終了明細を完了
        res = POST送信(f"{TASK_API}/タスク明細/終了完了", {
            "利用者ID": 利用者ID,
            "タスクID": タスクID,
            "明細SEQ": 明細SEQ,
            "応答内容": 応答内容,
        }, timeout=60)
        if res.get("status") != "OK":
            raise RuntimeError(f"終了完了報告に失敗しました: {res.get('message')}")
        ログ("終了処理 完了")
        return 0
    except Exception as e:
        ログ(f"エラー: {e}\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
