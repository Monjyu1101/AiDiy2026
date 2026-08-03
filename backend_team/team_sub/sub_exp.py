# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""Aチーム経験を生成するサブプロセス。

team_watcher.py（1分ごとの処理）が temp/exp/<経験ID>.json に入力値を書き、
このスクリプトを `python sub_exp.py <入力JSONパス>` で起動する。
backend_task/task_sub/sub_init.py と同じ 2 段構えで動く。

処理の流れ:
1. 入力 JSON（経験ID / 依頼ID / タスクID / 要員ID / プロジェクト / 要求内容）を読み込む
2. backend_task から AIタスク明細の一覧を取得する
3. 第1ステップ: 対象プロジェクトのフォルダで AI が明細内容を読み、経験値をまとめて
   応答本文へ返す（ファイル書き込みなし）
4. 第2ステップ: AiDiy ルート（"../"）で AI がその結果を既定形式の JSON として
   temp/exp/output/<経験ID>.json へ書き込む
5. 出力 JSON を検証し、backend_team へ本登録する（失敗時は経験をエラーにする）
"""

from __future__ import annotations

import json
import os
import sys
import traceback
import urllib.request
from urllib.parse import quote

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AIDIYルート = os.path.normpath(os.path.join(BASE_DIR, ".."))
TEAM_API = "http://localhost:8094/team"
TASK_API = "http://localhost:8093/task"
MCP_URL = "http://127.0.0.1:8095/aidiy_code_agents/run"
_LOCAL_HTTP_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
TEAM_AI_NAME既定 = "claude_cli"
TEAM_AI_MODEL既定 = "auto"
TASK_AI_NAME既定 = "claude_cli"
TASK_AI_MODEL既定 = "auto"
JSON保存最大試行回数 = 2
明細最大件数 = 40

経験ID = ""
ログパス = os.path.join(BASE_DIR, "temp", "exp", "sub_exp.log")


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


def タスク明細を取得(タスクID: str) -> list[dict]:
    """backend_task からAIタスク明細の一覧を取得する。"""
    res = POST送信(f"{TASK_API}/タスク明細/一覧", {"タスクID": タスクID}, timeout=60)
    if res.get("status") != "OK":
        raise RuntimeError(f"AIタスク明細の取得に失敗しました: {res.get('message')}")
    items = res.get("data", {}).get("items", [])
    if not isinstance(items, list) or not items:
        raise RuntimeError(f"AIタスク明細が0件です: タスクID={タスクID}")
    return items


def 明細テキスト(明細: list[dict]) -> str:
    """AI へ渡す明細の要約テキストを作る（開始・終了行は除く）。"""
    行: list[str] = []
    for 項目 in 明細:
        seq = int(項目.get("明細SEQ", 0) or 0)
        if seq in (0, 9999):
            continue
        タイトル = str(項目.get("タイトル", "")).strip()
        要求内容 = str(項目.get("要求内容", "")).strip()
        状態 = str(項目.get("状態", "")).strip()
        応答内容 = str(項目.get("応答内容", "")).strip()
        行.append(
            f"- 明細SEQ {seq} / 状態 {状態} / タイトル: {タイトル}\n"
            f"  要求内容: {要求内容}\n"
            f"  実行結果: {応答内容[:600] or '（記録なし）'}"
        )
        if len(行) >= 明細最大件数:
            break
    return "\n".join(行)


def JSON形式サンプル(経験ID: str, 依頼ID: str) -> str:
    return f"""{{
  "経験ID": "{経験ID}",
  "依頼ID": "{依頼ID}",
  "タイトル": "この経験を一言で表すタイトル（40文字以内）",
  "経験値": 35,
  "分類": "実装",
  "まとめ内容": "何をどう進めて、どこまで到達したかの具体的なまとめ",
  "学び": "次の依頼に活かせる判断基準や注意点"
}}"""


def プロンプト生成_経験まとめ(
    経験ID: str, 依頼ID: str, 要員ID: str, プロジェクト: str, 要求内容: str, 明細本文: str
) -> str:
    return f"""次に示すのは、このプロジェクトで完了したAIタスクの明細内容です。
担当した要員がこの依頼から得た「経験値」としてまとめ、結果を JSON 形式の文字列として応答本文にそのまま出力してください。
このプロジェクトの構成や実装状況も確認し、実際に何が変わったのかを踏まえてまとめてください。
ファイルの作成・書き込み・コードの修正などの依頼は一切行わず、応答本文へ JSON を出力するだけにしてください。

要員ID: {要員ID}
対象プロジェクト: {プロジェクト or '（未指定）'}
依頼の要求内容:
{要求内容}

AIタスク明細の内容:
{明細本文}

出力する JSON の形式:
{JSON形式サンプル(経験ID, 依頼ID)}

まとめ方の指示:
- 経験値は 1〜100 の整数で、この依頼の難しさと学びの大きさを評価した点数にしてください。
  単純な確認だけなら 10 前後、複数ファイルにまたがる実装や不具合の切り分けを伴うなら 40〜70、
  設計から検証まで一通り行った大きな依頼なら 80 以上を目安にします。
- 分類は「実装」「調査」「修正」「検証」「運用」「その他」のいずれか 1 語にしてください。
- まとめ内容は、対象（ファイル名・機能名・画面名・API名など）と、行った変更・確認の内容、
  到達点が第三者に伝わるように 200 文字程度で具体的に書いてください。
- 学びは、次に似た依頼を行うときの判断基準や注意点を 100 文字程度で書いてください。
- 文体は「〜する」「〜を確認した」調の常体で統一し、口語表現は避けてください。
- 絵文字、顔文字、矢印記号、囲み文字、装飾的な特殊記号は一切使用しないでください。
  Windows 環境の cp932 エンコードで書き込みエラーになるため、通常の漢字・ひらがな・カタカナ・
  半角英数字と、句点「。」読点「、」カギ括弧「」丸括弧()程度の一般的な句読点記号だけを使ってください。
"""


def プロンプト生成_JSON保存(まとめ結果: str, 出力JSONパス: str, 経験ID: str, 依頼ID: str) -> str:
    return f"""次の「経験まとめ結果」から JSON オブジェクトを取り出し、JSON ファイルとして保存してください。
ファイルの保存先: {出力JSONパス}
保存先フォルダは既に存在します。UTF-8（BOMなし）で保存してください。
コードフェンスや説明文は取り除き、下記の既定形式（キー名は完全一致）に整えて保存してください。
まとめの内容（タイトル・経験値・分類・まとめ内容・学び）は変更しないでください。
このファイル保存以外の依頼（コードの修正、他ファイルの作成など）は一切行わないでください。

既定形式:
{JSON形式サンプル(経験ID, 依頼ID)}

経験まとめ結果:
{まとめ結果}
"""


def JSON検証(データ: dict, 依頼ID: str) -> dict:
    """出力 JSON を検証して本登録用の dict に整える。不正なら ValueError。"""
    if not isinstance(データ, dict):
        raise ValueError("JSON のルートがオブジェクトではありません")
    for キー in ("経験ID", "依頼ID", "タイトル", "経験値", "分類", "まとめ内容", "学び"):
        if キー not in データ:
            raise ValueError(f"キー '{キー}' がありません")
    if str(データ["経験ID"]).strip() != 経験ID:
        raise ValueError("経験IDが入力 JSON と一致していません")
    if str(データ["依頼ID"]).strip() != 依頼ID:
        raise ValueError("依頼IDが入力 JSON と一致していません")
    タイトル = str(データ["タイトル"]).strip()
    まとめ内容 = str(データ["まとめ内容"]).strip()
    if not タイトル:
        raise ValueError("タイトルが空です")
    if not まとめ内容:
        raise ValueError("まとめ内容が空です")
    try:
        経験値 = int(str(データ["経験値"]).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"経験値が整数ではありません: {データ['経験値']!r}") from exc
    if not 1 <= 経験値 <= 100:
        raise ValueError(f"経験値が 1〜100 の範囲外です: {経験値}")
    return {
        "タイトル": タイトル[:120],
        "経験値": 経験値,
        "分類": str(データ["分類"]).strip()[:40],
        "まとめ内容": まとめ内容,
        "学び": str(データ["学び"]).strip(),
    }


def JSON保存と検証(
    まとめ結果: str,
    出力JSONパス: str,
    依頼ID: str,
    team_ai_name: str,
    team_ai_model: str,
) -> dict:
    """第2ステップ（JSON保存）と第3ステップ（検証）を実行する。失敗時は例外を送出する。"""
    if os.path.exists(出力JSONパス):
        os.remove(出力JSONパス)

    ログ(
        f"第2ステップ: JSON保存 (ai={team_ai_name}, model={team_ai_model}, "
        f"project_path={AIDIYルート})"
    )
    res = POST送信(MCP_URL, {
        "prompt": プロンプト生成_JSON保存(まとめ結果, 出力JSONパス, 経験ID, 依頼ID),
        "ai_name": team_ai_name,
        "ai_model": team_ai_model,
        "project_path": AIDIYルート,
    })
    ログ(f"第2ステップ応答: {json.dumps(res, ensure_ascii=False)[:300]}")
    if res.get("error") or res.get("status") != "OK":
        raise RuntimeError(f"第2ステップ（JSON保存）に失敗しました: {res.get('error') or res.get('result')}")

    if not os.path.isfile(出力JSONパス):
        raise RuntimeError(f"出力 JSON が生成されませんでした: {出力JSONパス}")
    with open(出力JSONパス, "r", encoding="utf-8-sig") as f:
        データ = json.load(f)
    整形 = JSON検証(データ, 依頼ID)
    ログ(f"JSON 検証 OK: 経験値 {整形['経験値']} / {整形['タイトル']}")
    return 整形


def 本登録(整形: dict) -> None:
    res = POST送信(f"{TEAM_API}/経験/本登録", {"経験ID": 経験ID, **整形}, timeout=60)
    if res.get("status") != "OK":
        raise RuntimeError(f"本登録に失敗しました: {res.get('message')}")


def 失敗登録(メッセージ: str) -> None:
    if not 経験ID:
        return
    try:
        POST送信(
            f"{TEAM_API}/経験/失敗",
            {"経験ID": 経験ID, "メッセージ": メッセージ[:500]},
            timeout=60,
        )
    except Exception as e:
        ログ(f"失敗登録もエラー: {e}")


def main() -> int:
    global 経験ID, ログパス
    try:
        if len(sys.argv) < 2:
            raise ValueError("使い方: python sub_exp.py <temp/exp/経験ID.json>")
        入力パス = os.path.abspath(sys.argv[1])
        with open(入力パス, "r", encoding="utf-8-sig") as f:
            入力 = json.load(f)
        経験ID = str(入力.get("経験ID", "")).strip()
        依頼ID = str(入力.get("依頼ID", "")).strip()
        タスクID = str(入力.get("タスクID", "")).strip()
        要員ID = str(入力.get("要員ID", "")).strip()
        プロジェクト = str(入力.get("プロジェクト", "")).strip()
        要求内容 = str(入力.get("要求内容", "")).strip()
        team_ai_name = str(
            入力.get("TEAM_AI_NAME", TEAM_AI_NAME既定) or TEAM_AI_NAME既定
        ).strip()
        team_ai_model = str(
            入力.get("TEAM_AI_MODEL", TEAM_AI_MODEL既定) or TEAM_AI_MODEL既定
        ).strip()
        task_ai_name = str(
            入力.get("TASK_AI_NAME", TASK_AI_NAME既定) or TASK_AI_NAME既定
        ).strip()
        task_ai_model = str(
            入力.get("TASK_AI_MODEL", TASK_AI_MODEL既定) or TASK_AI_MODEL既定
        ).strip()
        if not 経験ID or not 依頼ID or not タスクID:
            raise ValueError("入力 JSON に 経験ID、依頼ID または タスクID がありません")

        ファイルステム = os.path.splitext(os.path.basename(入力パス))[0]
        ログパス = os.path.join(BASE_DIR, "temp", "exp", f"{ファイルステム}.log")
        ログ(f"=== AIチーム経験 生成開始: {経験ID} (依頼={依頼ID} / タスク={タスクID}) ===")

        出力DIR = os.path.join(BASE_DIR, "temp", "exp", "output")
        os.makedirs(出力DIR, exist_ok=True)
        出力JSONパス = os.path.join(出力DIR, f"{ファイルステム}.json").replace("\\", "/")
        if os.path.exists(出力JSONパス):
            os.remove(出力JSONパス)

        # 1. AIタスク明細を取得
        明細 = タスク明細を取得(タスクID)
        明細本文 = 明細テキスト(明細)
        if not 明細本文:
            raise RuntimeError("経験化できる明細（開始・終了以外）がありません")
        ログ(f"明細取得: {len(明細)} 件")

        # 2. 第1ステップ: 対象プロジェクトで経験値をまとめる（ファイル書き込みなし）
        ログ(
            f"第1ステップ: 経験まとめ (ai={task_ai_name}, model={task_ai_model}, "
            f"project_path={プロジェクト or '既定'})"
        )
        payload = {
            "prompt": プロンプト生成_経験まとめ(経験ID, 依頼ID, 要員ID, プロジェクト, 要求内容, 明細本文),
            "ai_name": task_ai_name,
            "ai_model": task_ai_model,
        }
        if プロジェクト:
            payload["project_path"] = プロジェクト
        res = POST送信(MCP_URL, payload)
        ログ(f"第1ステップ応答: {json.dumps(res, ensure_ascii=False)[:300]}")
        if res.get("error") or res.get("status") != "OK":
            raise RuntimeError(f"第1ステップ（経験まとめ）に失敗しました: {res.get('error') or res.get('result')}")
        まとめ結果 = str(res.get("result") or "").strip()
        if not まとめ結果 or まとめ結果 == "（応答なし）":
            raise RuntimeError("第1ステップ（経験まとめ）の応答が空です")

        # 3. 第2ステップ（JSON保存）と第3ステップ（検証）。AI 応答の揺れで失敗することがあるため1回リトライする
        for 試行 in range(1, JSON保存最大試行回数 + 1):
            try:
                整形 = JSON保存と検証(
                    まとめ結果,
                    出力JSONパス,
                    依頼ID,
                    team_ai_name,
                    team_ai_model,
                )
                break
            except Exception as e:
                ログ(f"第2/第3ステップ 試行{試行}回目 失敗: {e}")
                if 試行 >= JSON保存最大試行回数:
                    raise
                ログ("自動リカバリー: 第2ステップ（JSON保存）を再試行します")

        # 4. backend_team へ本登録
        本登録(整形)
        ログ("本登録 完了")
        return 0

    except Exception as e:
        ログ(f"エラー: {e}\n{traceback.format_exc()}")
        失敗登録(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
