# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""タスク明細の 1 ステップ実行サブプロセス。

起動監視ループが `python sub_proc.py <タスクID> <SEQ>` で起動する。
ローカルの temp/input・temp/output JSON には依存せず、タスクID と SEQ だけで完結する。
標準ライブラリのみで動作する。

処理の流れ:
1. /task/タスク要求/取得 でタスク全体（タイトル・プロジェクト）を取得する
2. /task/タスク明細/一覧 で全明細を取得し、対象 SEQ のステップを特定する
   （完了済み明細の応答内容は実行済み記録として渡す。ステップ0 開始 の応答内容は処理目標）
3. aidiy_code_agents MCP へ、指定プロジェクトフォルダ・指定 AI で「このステップだけ実行」を依頼する
4. 正常時は /task/タスク明細/完了、エラー時は /task/タスク明細/失敗 を呼ぶ
   （操作検証ありの明細は、AI が /task_check_okng で報告した状態を確認する。
   　書き込みなし・エラーのいずれかの場合は、検証結果を踏まえて1回だけ自動リトライする）
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
通知音URL = "http://127.0.0.1:8095/aidiy_notification_sounds/play"
_LOCAL_HTTP_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
TASK_AI_NAME既定 = "codex_cli"
TASK_AI_MODEL既定 = "auto"
# 1ステップの実行タイムアウト秒。tasks_watcher.実行タイムアウト分（既定60分）と揃える。
# 明示的に渡さないと aidiy_code_agents 側の既定値（30分）で先に打ち切られる。
CODE実行タイムアウト秒 = 3600
# HTTP 側は code_agents のタイムアウトが先に効くよう少し長く取る
# （HTTP が先に切れると、AI からの結果もエラー理由も受け取れないため）
CODE実行HTTPタイムアウト秒 = CODE実行タイムアウト秒 + 300

タスクID = ""
明細SEQ = 0
ログパス = os.path.join(BASE_DIR, "temp", "task", "sub_proc.log")


def _標準出力をUTF8化() -> None:
    """AI応答に含まれる — や絵文字で print が落ちないようにする。

    サブプロセスの標準出力は Windows では cp932 になるため、変換できない文字があると
    UnicodeEncodeError でステップ全体が失敗してしまう。UTF-8（変換不可は置換）へ切り替える。
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
    """AIタスク明細の全件（状態フィルタなし）を返す。"""
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


def プロンプト生成(タスクタイトル: str, 全明細: list[dict], 対象: dict, 完了明細: list[dict], 前回失敗理由: str = "") -> str:
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
    操作検証ブロック = ""
    if 対象.get("操作検証"):
        操作検証ブロック = f"""
【操作検証】このステップはファイルの更新・追加・書込を伴う作業です。作業後に変更内容を
実際に確認し、意図した通りに反映されているか検証してください。検証したら、結果を必ず
次の HTTP エンドポイントへ直接報告してください（curl 等でこの AI エージェント自身が呼び出します）。
  POST http://127.0.0.1:8093/task_check_okng
  Content-Type: application/json
  Body: {{"タスクID": "{タスクID}", "SEQ": {対象['明細SEQ']}, "状態": "完了", "メッセージ": "検証内容の要約"}}
  検証で問題が見つかった場合は 状態 を "エラー" にし、メッセージ に理由を書いてください。
"""
    リトライブロック = ""
    if 前回失敗理由:
        リトライブロック = f"""
【前回試行の検証結果】前回このステップを実行しましたが、検証NGまたは検証結果の未報告により
やり直しになっています。次の内容を踏まえて、問題を解消したうえで再実行してください。
前回の理由: {前回失敗理由}
"""
    return f"""あなたはタスクの 1 ステップを実行する担当です。今回のステップの作業だけを実行してください。

タスク全体のタイトル: {タスクタイトル}

全ステップ:
{全ステップ}

実行済ステップの記録（ステップ0 開始 の応答内容が処理目標です）:
{実行済ブロック}

【今回のステップ】※この処理だけ実行してください。
ステップ{対象['明細SEQ']} {対象['タイトル']}
{対象['要求内容']}
{リトライブロック}{操作検証ブロック}
注意:
- 今回のステップの作業のみを行い、先行・後続ステップの作業は行わないでください。
- AiDiy の MCP ツールが HTTP で利用できます。
  ツール一覧の確認: GET http://127.0.0.1:8095/<mcp名>/list
  ツールの実行: POST http://127.0.0.1:8095/<mcp名>/<メソッド> （JSON ボディ）
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
        "タスクID": タスクID,
        "明細SEQ": 明細SEQ,
        "応答内容": 応答内容,
    }, timeout=60)
    if res.get("status") != "OK":
        raise RuntimeError(f"完了報告に失敗しました: {res.get('message')}")


def 再試行登録() -> None:
    """自動リカバリーの再試行前に、明細とタスク要求の状態を実行中へ戻す。"""
    res = POST送信(f"{TASK_API}/タスク明細/再試行", {
        "タスクID": タスクID,
        "明細SEQ": 明細SEQ,
    }, timeout=60)
    if res.get("status") != "OK":
        raise RuntimeError(f"明細の再試行登録に失敗しました: {res.get('message')}")


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
            raise ValueError("使い方: python sub_proc.py <タスクID> <SEQ>")
        タスクID = str(sys.argv[1]).strip()
        明細SEQ = int(sys.argv[2])
        if not タスクID:
            raise ValueError("タスクIDが指定されていません")
        ログパス = os.path.join(BASE_DIR, "temp", "task", f"{タスクID}.step{明細SEQ}.log")
        ログ(f"=== ステップ実行 開始: {タスクID} SEQ={明細SEQ} ===")

        # 1. AIタスク要求 からタイトル・プロジェクトを取得
        要求 = タスク要求取得()
        タスクタイトル = str(要求.get("タイトル", "")).strip()
        プロジェクト = str(要求.get("プロジェクト", "")).strip()

        # 2. 全明細を取得し、対象ステップを特定する
        全明細 = 明細一覧取得()
        対象 = 明細1件取得(全明細, 明細SEQ)
        if not 対象:
            raise ValueError(f"タスク明細に SEQ={明細SEQ} がありません")

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
        完了明細 = [行 for 行 in 全明細 if str(行.get("状態", "")).strip() == "完了"]
        ログ(f"完了明細取得: {len(完了明細)} 件")

        # 5. code_agents へステップ実行を依頼（指定プロジェクトフォルダ・指定 AI）
        # 6. 操作検証ありの明細は、AI が task_check_okng で報告した状態を確認する。
        #    書き込みなし・エラーのいずれかの場合は、検証結果を踏まえて1回だけ自動リトライする
        task_ai_name = 対象.get("TASK_AI_NAME") or TASK_AI_NAME既定
        task_ai_model = 対象.get("TASK_AI_MODEL") or TASK_AI_MODEL既定
        最大試行回数 = 2 if 対象.get("操作検証") else 1
        前回失敗理由 = ""
        for 試行 in range(1, 最大試行回数 + 1):
            ログ(f"code_agents run 呼び出し (試行{試行}/{最大試行回数}, タイトル={対象['タイトル']}, ai={task_ai_name}, model={task_ai_model}, project_path={プロジェクト})")
            payload = {
                "prompt": プロンプト生成(タスクタイトル, 全明細, 対象, 完了明細, 前回失敗理由),
                "ai_name": task_ai_name,
                "ai_model": task_ai_model,
                "timeout_sec": CODE実行タイムアウト秒,
            }
            if プロジェクト:
                payload["project_path"] = プロジェクト
            res = POST送信(MCP_URL, payload, timeout=CODE実行HTTPタイムアウト秒)
            ログ(f"code_agents run 応答: {json.dumps(res, ensure_ascii=False)[:500]}")

            失敗理由 = ""
            if res.get("error") or res.get("status") != "OK":
                失敗理由 = f"code_agents の実行に失敗しました: {res.get('error') or res.get('result')}"
            elif not 対象.get("操作検証"):
                # 操作検証なし: そのまま完了報告
                応答内容 = str(res.get("result") or json.dumps(res, ensure_ascii=False))
                完了報告(応答内容)
                ログ("ステップ完了")
                return 0
            else:
                # 操作検証あり: AI が task_check_okng で報告した状態を確認する
                最終行 = 明細1件取得(明細一覧取得(), 明細SEQ)
                最終状態 = str(最終行.get("状態", "")).strip()
                if 最終状態 == "完了":
                    ログ("ステップ完了（操作検証OK）")
                    return 0
                elif 最終状態 == "エラー":
                    失敗理由 = str(最終行.get("応答内容", "")).strip() or "操作検証でNGと判定されました。"
                else:
                    失敗理由 = f"操作検証の結果がAIから報告されませんでした（task_check_okng 未呼び出し、現状態={最終状態 or '不明'}）。"

            if 試行 >= 最大試行回数:
                raise RuntimeError(失敗理由)
            ログ(f"試行{試行}回目 失敗: {失敗理由}")
            ログ("自動リカバリー: 検証結果を踏まえてステップを再試行します")
            前回失敗理由 = 失敗理由
            再試行登録()

    except Exception as e:
        ログ(f"エラー: {e}\n{traceback.format_exc()}")
        失敗報告(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
