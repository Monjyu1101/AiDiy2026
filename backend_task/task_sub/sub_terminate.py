# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""AIタスクの終了明細を処理するサブプロセス。

終了明細（DB上の操作検証フラグ、他のいずれかの明細でファイル操作があれば true）に
応じて処理を分岐する。
- 操作検証=false: ファイル操作を伴う明細が無いため、AIを介さずそのまま終了完了にする
- 操作検証=true : sub_proc と同様の内容（処理目標と実行済ステップの記録）を指定
  プロジェクトフォルダ・指定 AI へ渡し、最終検証と結論の task_check_okng 報告を依頼する。
  AI が報告せずに戻ってきた場合は、明細を強制的にエラーで確定する。
ローカルの temp/input・temp/output JSON には依存せず、タスクID と SEQ だけで完結する。
標準ライブラリのみで動作する。

処理の流れ:
1. /task/タスク要求/取得 でタスク全体（タイトル・プロジェクト）を取得する
2. /task/タスク明細/一覧 から全明細（完了済みの応答内容、対象行の操作検証フラグ）を取得する
3. 操作検証=false なら /task/タスク明細/終了完了 を呼んで終了する
4. 操作検証=true なら aidiy_code_agents MCP へ最終検証を依頼し、結論は AI 自身が
   http://127.0.0.1:8093/task_check_okng へ直接報告する
5. AI 応答後に明細の状態を確認し、完了/エラーのいずれにも更新されていなければ
   /task/タスク明細/失敗 で強制的にエラーにする
"""

from __future__ import annotations

import json
import os
import sys
import traceback
import urllib.request
from urllib.parse import quote

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASK_API = "http://127.0.0.1:8093/task"
MCP_URL = "http://127.0.0.1:8095/aidiy_code_agents/run"
_LOCAL_HTTP_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
TASK_AI_NAME既定 = "codex_cli"
TASK_AI_MODEL既定 = "auto"

タスクID = ""
明細SEQ = 0
ログパス = os.path.join(BASE_DIR, "temp", "task", "sub_terminate.log")


def _標準出力をUTF8化() -> None:
    """AI応答に含まれる — や絵文字で print が落ちないようにする。

    サブプロセスの標準出力は Windows では cp932 になるため、変換できない文字があると
    UnicodeEncodeError で処理全体が失敗してしまう。UTF-8（変換不可は置換）へ切り替える。
    """
    for ストリーム in (sys.stdout, sys.stderr):
        try:
            ストリーム.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


_標準出力をUTF8化()


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
    with _LOCAL_HTTP_OPENER.open(req, timeout=timeout) as res:
        return json.loads(res.read().decode("utf-8"))


def タスク要求取得() -> dict:
    res = POST送信(f"{TASK_API}/タスク要求/取得", {
        "タスクID": タスクID,
    }, timeout=60)
    if res.get("status") != "OK":
        raise RuntimeError(f"AIタスク要求の取得に失敗しました: {res.get('message')}")
    return res.get("data", {}).get("item", {})


def 明細一覧取得() -> list[dict]:
    """AIタスク明細の全件（状態フィルタなし）を返す。DB上の操作検証フラグもここから取れる。"""
    res = POST送信(f"{TASK_API}/タスク明細/一覧", {
        "タスクID": タスクID,
    }, timeout=60)
    if res.get("status") != "OK":
        raise RuntimeError(f"タスク明細一覧の取得に失敗しました: {res.get('message')}")
    return res.get("data", {}).get("items", [])


def 明細1件取得(全明細: list[dict], 対象SEQ: int) -> dict:
    for 行 in 全明細:
        if int(行.get("明細SEQ", -1)) == 対象SEQ:
            return 行
    return {}


def プロンプト生成(タスクタイトル: str, 全明細: list[dict], 対象: dict, 完了明細: list[dict]) -> str:
    全ステップ = "\n".join(
        f"  {int(行['明細SEQ'])}. {str(行['タイトル']).strip()}（先行SEQ: {str(行['先行SEQ']).strip() or 'なし'}）"
        for 行 in 全明細
    )
    実行済: list[str] = []
    for 行 in sorted(完了明細, key=lambda 行: int(行["明細SEQ"])):
        seq = int(行["明細SEQ"])
        タイトル = str(行.get("タイトル", "")).strip()
        応答内容 = str(行.get("応答内容", "")).strip()
        見出し = f"ステップ{seq} {タイトル} " + ("処理目標" if seq == 0 else "実行済")
        実行済.append(f"``` {見出し}\n{応答内容}\n```")
    実行済ブロック = "\n".join(実行済) if 実行済 else "（実行済ステップはまだありません）"
    return f"""あなたはタスク全体の最終検証（操作検証）を行う担当です。今回は検証のみを行ってください。

タスク全体のタイトル: {タスクタイトル}

全ステップ:
{全ステップ}

実行済ステップの記録（ステップ0 開始 の応答内容が処理目標です）:
{実行済ブロック}

【今回のステップ】※検証のみを行ってください。
ステップ{対象['明細SEQ']} {対象['タイトル']}
各実行ステップの検証と最終結果の検証をお願いします。

注意:
- 検証のみを行い、コードの修正や新しい作業は行わないでください。
- 処理目標に対して各実行ステップの記録と実際の成果物を照合し、最終結果を検証してください。
- ファイル操作を伴わない処理は、渡された実行済ステップの記録だけから簡素に判断し、ファイル確認や追加のツール実行は行わないでください。
- AiDiy の MCP ツールが HTTP で利用できます。
  ツール一覧の確認: GET http://127.0.0.1:8095/<mcp名>/list
  ツールの実行: POST http://127.0.0.1:8095/<mcp名>/<メソッド> （JSON ボディ）
  例: aidiy_notification_sounds, aidiy_sqlite, aidiy_chrome_devtools など
- 検証結果は必ず次の HTTP エンドポイントへ直接報告してください（あなた自身が curl 等で呼び出します）。
  POST http://127.0.0.1:8093/task_check_okng
  Content-Type: application/json
  Body: {{"タスクID": "{タスクID}", "SEQ": {対象['明細SEQ']}, "状態": "完了", "メッセージ": "検証結論の要約"}}
  問題が見つかった場合は 状態 を "エラー" にし、メッセージ に理由を書いてください。
  この報告が今回のステップの完了条件です。報告を行わずに終えないでください。
"""


def 検証実行(タスクタイトル: str, 全明細: list[dict], 対象: dict, 完了明細: list[dict], プロジェクト: str) -> str:
    """code_agents で各実行ステップと最終結果を検証させる（結論は AI が task_check_okng へ報告する）。

    失敗しても例外にはしない。呼び出し元は AI 応答後に明細の状態を見て成否を判定する。
    """
    try:
        task_ai_name = str(対象.get("TASK_AI_NAME", "") or TASK_AI_NAME既定).strip()
        task_ai_model = str(対象.get("TASK_AI_MODEL", "") or TASK_AI_MODEL既定).strip()
        ログ(f"code_agents run 呼び出し (検証, ai={task_ai_name}, model={task_ai_model}, project_path={プロジェクト})")
        payload = {"prompt": プロンプト生成(タスクタイトル, 全明細, 対象, 完了明細), "ai_name": task_ai_name, "ai_model": task_ai_model}
        if プロジェクト:
            payload["project_path"] = プロジェクト
        res = POST送信(MCP_URL, payload)
        ログ(f"code_agents run 応答: {json.dumps(res, ensure_ascii=False)[:500]}")
        if res.get("error") or res.get("status") != "OK":
            raise RuntimeError(f"code_agents の実行に失敗しました: {res.get('error') or res.get('result')}")
        return str(res.get("result") or "").strip()
    except Exception as e:
        ログ(f"検証実行失敗: {e}")
        return f"[注意] 検証実行失敗: {e}"


def 失敗報告(メッセージ: str) -> None:
    if not タスクID or not 明細SEQ:
        return
    try:
        POST送信(f"{TASK_API}/タスク明細/失敗", {
            "タスクID": タスクID,
            "明細SEQ": 明細SEQ,
            "メッセージ": メッセージ[:500],
        }, timeout=60)
    except Exception as e:
        ログ(f"失敗報告もエラー: {e}")


def main() -> int:
    global タスクID, 明細SEQ, ログパス
    try:
        if len(sys.argv) < 3:
            raise ValueError("使い方: python sub_terminate.py <タスクID> <SEQ>")
        タスクID = str(sys.argv[1]).strip()
        明細SEQ = int(sys.argv[2])
        if not タスクID:
            raise ValueError("タスクIDが指定されていません")
        ログパス = os.path.join(BASE_DIR, "temp", "task", f"{タスクID}.step{明細SEQ}.log")

        ログ(f"=== 終了処理: {タスクID} SEQ={明細SEQ} ===")

        # 1. AIタスク要求 からタイトル・プロジェクトを取得
        要求 = タスク要求取得()
        タスクタイトル = str(要求.get("タイトル", "")).strip()
        プロジェクト = str(要求.get("プロジェクト", "")).strip()

        # 2. 全明細を取得（対象＝終了明細の特定、完了済み明細の応答内容、DB上の操作検証フラグ）
        全明細 = 明細一覧取得()
        対象 = 明細1件取得(全明細, 明細SEQ)
        if not 対象:
            raise ValueError(f"タスク明細に SEQ={明細SEQ} がありません")
        完了明細 = [行 for 行 in 全明細 if str(行.get("状態", "")).strip() == "完了"]
        操作検証 = bool(対象.get("操作検証", False))
        ログ(f"完了明細取得: {len(完了明細)} 件, 操作検証={操作検証}")

        if not 操作検証:
            # 4a. ファイル操作を伴う明細が無いため、AIを介さずそのまま終了完了にする
            res = POST送信(f"{TASK_API}/タスク明細/終了完了", {
                "タスクID": タスクID,
                "明細SEQ": 明細SEQ,
                "応答内容": "操作検証対象のファイル操作がないため、終了処理を完了しました。",
            }, timeout=60)
            if res.get("status") != "OK":
                raise RuntimeError(f"終了完了報告に失敗しました: {res.get('message')}")
            ログ("終了処理 完了（操作検証なし）")
            return 0

        # 4b. 操作検証あり: これまでの応答結果を全て渡し、AIに最終検証と
        #     task_check_okng による状態報告を依頼する（状態更新は AI 自身が行う）
        結論 = 検証実行(タスクタイトル, 全明細, 対象, 完了明細, プロジェクト)
        ログ(f"検証結果: {結論[:300]}")

        # 5. AIが task_check_okng で状態を更新したか確認する
        最終行 = 明細1件取得(明細一覧取得(), 明細SEQ)
        最終状態 = str(最終行.get("状態", "")).strip()

        # 6. 完了/エラーのいずれにも更新されていなければ、強制的にエラーで確定する
        if 最終状態 not in ("完了", "エラー"):
            ログ(f"AIによる状態報告がありませんでした（現状態={最終状態 or '不明'}）。強制的にエラーにします。")
            失敗報告("操作検証の結果がAIから報告されませんでした（task_check_okng 未呼び出し）。")
            return 1

        ログ(f"終了処理 完了（操作検証あり、状態={最終状態}）")
        return 0 if 最終状態 == "完了" else 1

    except Exception as e:
        ログ(f"エラー: {e}\n{traceback.format_exc()}")
        失敗報告(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
