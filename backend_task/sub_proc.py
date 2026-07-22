# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""タスク明細の 1 ステップ実行サブプロセス。

監視ループが `python sub_proc.py <temp/output/利用者ID.タスクID.json> <SEQ>` で起動する。
標準ライブラリのみで動作する。

処理の流れ:
1. 出力 JSON（AI 生成のタスク分解結果）から対象 SEQ のステップを特定する
2. temp/input/<タスクID>.json からプロジェクトパスを引き継ぐ（あれば）
3. /task/タスク明細/一覧 から完了済み明細の応答内容を取得する
   （ステップ0 開始 の応答内容は処理目標、実行済ステップの応答内容は作業記録として渡す）
4. aidiy_code_agents MCP へ、指定プロジェクトフォルダ・指定 AI で「このステップだけ実行」を依頼する
5. 正常時は /task/タスク明細/完了、エラー時は /task/タスク明細/失敗 を呼ぶ
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
通知音URL = "http://localhost:8095/aidiy_notification_sounds/play"
TASK_AI_NAME既定 = "claude_cli"
TASK_AI_MODEL既定 = "auto"

タスクID = ""
利用者ID = ""
明細SEQ = 0
ログパス = os.path.join(BASE_DIR, "temp", "task", "sub_proc.log")


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


def 明細行整形(行: dict) -> dict:
    return {
        "明細SEQ": int(行["明細SEQ"]),
        "タイトル": str(行["タイトル"]).strip(),
        "要求内容": str(行["要求内容"]).strip(),
        "先行SEQ": str(行["先行SEQ"]).strip(),
        "TASK_AI_NAME": str(行.get("TASK_AI_NAME", TASK_AI_NAME既定) or TASK_AI_NAME既定).strip(),
        "TASK_AI_MODEL": str(行.get("TASK_AI_MODEL", TASK_AI_MODEL既定) or TASK_AI_MODEL既定).strip(),
        "操作検証": bool(行.get("操作検証", False)),
    }


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
    操作検証ブロック = ""
    if 対象.get("操作検証"):
        操作検証ブロック = f"""
【操作検証】このステップはファイルの更新・追加・書込を伴う作業です。作業後に変更内容を
実際に確認し、意図した通りに反映されているか検証してください。検証したら、結果を必ず
次の HTTP エンドポイントへ直接報告してください（curl 等でこの AI エージェント自身が呼び出します）。
  POST http://localhost:8093/task_check_okng
  Content-Type: application/json
  Body: {{"利用者ID": "{利用者ID}", "タスクID": "{タスクID}", "SEQ": {対象['明細SEQ']}, "状態": "完了", "メッセージ": "検証内容の要約"}}
  検証で問題が見つかった場合は 状態 を "エラー" にし、メッセージ に理由を書いてください。
"""
    return f"""あなたはタスクの 1 ステップを実行する担当です。今回のステップの作業だけを実行してください。

タスク全体のタイトル: {str(データ.get('タイトル', '')).strip()}

全ステップ:
{全ステップ}

実行済ステップの記録（ステップ0 開始 の応答内容が処理目標です）:
{実行済ブロック}

【今回のステップ】※この処理だけ実行してください。
ステップ{対象['明細SEQ']} {対象['タイトル']}
{対象['要求内容']}
{操作検証ブロック}
注意:
- 今回のステップの作業のみを行い、先行・後続ステップの作業は行わないでください。
- AiDiy の MCP ツールが HTTP で利用できます。
  ツール一覧の確認: GET http://localhost:8095/<mcp名>/list
  ツールの実行: POST http://localhost:8095/<mcp名>/<メソッド> （JSON ボディ）
  例: aidiy_notification_sounds, aidiy_sqlite, aidiy_chrome_devtools など
- 作業が完了したら、実行した内容と結果を簡潔に報告してください。
"""


def 通知音種別取得(対象: dict) -> str:
    タイトル = str(対象.get("タイトル", "")).upper()
    if "準備" in タイトル or "確認" in タイトル:
        return "確認"
    if "通知音" not in タイトル and "再生" not in タイトル:
        return ""
    if "終了" in タイトル:
        return "終了"
    if "NG" in タイトル:
        return "注意"
    if "OK" in タイトル:
        return "完了"
    return ""


def 通知音直接再生(通知種別: str) -> dict:
    return POST送信(通知音URL, {
        "notification_type": 通知種別,
        "scene": "auto",
    }, timeout=60)


def 完了報告(応答内容: str) -> None:
    res = POST送信(f"{TASK_API}/タスク明細/完了", {
        "利用者ID": 利用者ID,
        "タスクID": タスクID,
        "明細SEQ": 明細SEQ,
        "応答内容": 応答内容,
    }, timeout=60)
    if res.get("status") != "OK":
        raise RuntimeError(f"完了報告に失敗しました: {res.get('message')}")


def 失敗報告(メッセージ: str) -> None:
    if not 利用者ID or not タスクID or not 明細SEQ:
        return
    try:
        POST送信(f"{TASK_API}/タスク明細/失敗", {
            "利用者ID": 利用者ID,
            "タスクID": タスクID,
            "明細SEQ": 明細SEQ,
            "メッセージ": メッセージ[:500],
        }, timeout=60)
    except Exception as e:
        ログ(f"失敗報告もエラー: {e}")


def main() -> int:
    global タスクID, 利用者ID, 明細SEQ, ログパス
    try:
        if len(sys.argv) < 3:
            raise ValueError("使い方: python sub_proc.py <temp/output/利用者ID.タスクID.json> <SEQ>")
        出力JSONパス = os.path.abspath(sys.argv[1])
        明細SEQ = int(sys.argv[2])
        ファイルステム = os.path.splitext(os.path.basename(出力JSONパス))[0]

        ログパス = os.path.join(BASE_DIR, "temp", "task", f"{ファイルステム}.step{明細SEQ}.log")

        # 1. 出力 JSON から対象ステップを特定
        with open(出力JSONパス, "r", encoding="utf-8-sig") as f:
            データ = json.load(f)
        対象 = None
        for 行 in データ.get("明細", []):
            if isinstance(行, dict) and int(行["明細SEQ"]) == 明細SEQ:
                対象 = 明細行整形(行)
                break
        if 対象 is None:
            raise ValueError(f"出力 JSON に SEQ={明細SEQ} の明細がありません")

        # 2. 入力 JSON からプロジェクトパスを引き継ぐ（あれば）
        プロジェクト = ""
        入力JSONパス = os.path.join(BASE_DIR, "temp", "input", f"{ファイルステム}.json")
        if os.path.isfile(入力JSONパス):
            with open(入力JSONパス, "r", encoding="utf-8-sig") as f:
                入力 = json.load(f)
                利用者ID = str(入力.get("利用者ID", "")).strip()
                タスクID = str(入力.get("タスクID", "")).strip()
                プロジェクト = str(入力.get("プロジェクト", "")).strip()
        if not 利用者ID or not タスクID:
            raise ValueError("入力 JSON に 利用者ID または タスクID がありません")
        ログ(f"=== ステップ実行 開始: {利用者ID}/{タスクID} SEQ={明細SEQ} ===")

        # 3. 定型通知音は AI を経由せず直接再生する
        通知種別 = 通知音種別取得(対象)
        if 通知種別:
            if 通知種別 == "確認":
                res = {"status": "ok", "message": "再生完了確認を完了しました。"}
                ログ("再生完了確認: no-op")
            else:
                ログ(f"通知音直接再生: type={通知種別}")
                res = 通知音直接再生(通知種別)
                if res.get("error"):
                    raise RuntimeError(f"通知音再生に失敗しました: {res.get('error')}")
            応答内容 = json.dumps(res, ensure_ascii=False)
            完了報告(応答内容)
            ログ("ステップ完了")
            return 0

        # 4. 完了済み明細の応答内容を取得（ステップ0 の処理目標と実行済ステップの記録）
        完了明細 = 完了明細一覧取得()
        ログ(f"完了明細取得: {len(完了明細)} 件")

        # 5. code_agents へステップ実行を依頼（指定プロジェクトフォルダ・指定 AI）
        task_ai_name = 対象.get("TASK_AI_NAME") or TASK_AI_NAME既定
        task_ai_model = 対象.get("TASK_AI_MODEL") or TASK_AI_MODEL既定
        ログ(f"code_agents run 呼び出し (タイトル={対象['タイトル']}, ai={task_ai_name}, model={task_ai_model}, project_path={プロジェクト})")
        payload = {"prompt": プロンプト生成(データ, 対象, 完了明細), "ai_name": task_ai_name, "ai_model": task_ai_model}
        if プロジェクト:
            payload["project_path"] = プロジェクト
        res = POST送信(MCP_URL, payload)
        ログ(f"code_agents run 応答: {json.dumps(res, ensure_ascii=False)[:500]}")
        if res.get("error") or res.get("status") != "OK":
            raise RuntimeError(f"code_agents の実行に失敗しました: {res.get('error') or res.get('result')}")

        # 6. 完了報告
        応答内容 = str(res.get("result") or json.dumps(res, ensure_ascii=False))
        完了報告(応答内容)
        ログ("ステップ完了")
        return 0

    except Exception as e:
        ログ(f"エラー: {e}\n{traceback.format_exc()}")
        失敗報告(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
