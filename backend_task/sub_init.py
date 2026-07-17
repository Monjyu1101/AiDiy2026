# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""AIタスク生成の共通サブプロセス。

backend_task の AI登録 API が temp/input/<タスクID>.json に入力値を書き、
このスクリプトを `python sub_init.py <入力JSONパス>` で起動する。
標準ライブラリのみで動作する。

処理の流れ:
1. 入力 JSON（利用者ID / タスクID / プロジェクト / 要求内容）を読み込む
2. 第1ステップ: 指定プロジェクトフォルダで指定 AI がタスク分解し、
   そのプロジェクトに最適な内容の JSON 形式文字列を応答本文で返す（ファイル書き込みなし）
3. 第2ステップ: AiDiy ルート（"../"）で指定 AI が分解結果を既定形式で
   temp/output/<利用者ID>.<タスクID>.json へ書き込む
4. 出力 JSON を検証する
5. 正常時は backend_task へ本登録（仮登録は置き換え）、エラー時は仮登録を『失敗』にする
"""

from __future__ import annotations

import json
import os
import sys
import traceback
import urllib.request
from urllib.parse import quote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AIDIYルート = os.path.normpath(os.path.join(BASE_DIR, ".."))
TASK_API = "http://localhost:8093/task"
MCP_URL = "http://localhost:8095/aidiy_code_agents/run"
TASK_AI_NAME既定 = "claude_cli"
TASK_AI_MODEL既定 = "auto"

タスクID = ""
利用者ID = ""
ログパス = os.path.join(BASE_DIR, "temp", "task", "sub_init.log")


def TASK_AI設定() -> tuple[str, str]:
    path = os.path.normpath(os.path.join(BASE_DIR, "..", "backend_server", "_config", "AiDiy_key.json"))
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        return str(data.get("TASK_AI_NAME", TASK_AI_NAME既定) or TASK_AI_NAME既定), str(data.get("TASK_AI_MODEL", TASK_AI_MODEL既定) or TASK_AI_MODEL既定)
    except Exception:
        return TASK_AI_NAME既定, TASK_AI_MODEL既定


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


def JSON形式サンプル(利用者ID: str, タスクID: str, プロジェクト: str, task_ai_name: str, task_ai_model: str) -> str:
    return f"""{{
  "利用者ID": "{利用者ID}",
  "タスクID": "{タスクID}",
  "プロジェクト": "{プロジェクト}",
  "タイトル": "タスク全体を一言で表すタイトル（40文字以内）",
  "要求内容": "入力された要求内容を整理した文章",
  "マーメイド記号": "TD",
  "明細": [
    {{"利用者ID": "{利用者ID}", "タスクID": "{タスクID}", "明細SEQ": 0, "タイトル": "開始", "要求内容": "", "先行SEQ": "", "TASK_AI_NAME": "{task_ai_name}", "TASK_AI_MODEL": "{task_ai_model}"}},
    {{"利用者ID": "{利用者ID}", "タスクID": "{タスクID}", "明細SEQ": 1, "タイトル": "明細タイトル", "要求内容": "明細要求内容", "先行SEQ": "0", "TASK_AI_NAME": "{task_ai_name}", "TASK_AI_MODEL": "{task_ai_model}"}},
    {{"利用者ID": "{利用者ID}", "タスクID": "{タスクID}", "明細SEQ": 2, "タイトル": "明細タイトル", "要求内容": "明細要求内容", "先行SEQ": "1", "TASK_AI_NAME": "{task_ai_name}", "TASK_AI_MODEL": "{task_ai_model}"}},
    {{"利用者ID": "{利用者ID}", "タスクID": "{タスクID}", "明細SEQ": 9999, "タイトル": "終了", "要求内容": "", "先行SEQ": "2", "TASK_AI_NAME": "{task_ai_name}", "TASK_AI_MODEL": "{task_ai_model}"}}
  ]
}}"""


def プロンプト生成_タスク分解(利用者ID: str, タスクID: str, プロジェクト: str, 要求内容: str, task_ai_name: str, task_ai_model: str) -> str:
    return f"""次の要求内容を分析してタスク分解し、結果を JSON 形式の文字列として応答本文にそのまま出力してください。
このプロジェクトの構成や実装状況を確認し、このプロジェクトに最適なタスク分解にしてください。
ファイルの作成・書き込み・コードの修正などの作業は一切行わず、応答本文へ JSON を出力するだけにしてください。

要求内容:
{要求内容}

出力する JSON の形式:
{JSON形式サンプル(利用者ID, タスクID, プロジェクト, task_ai_name, task_ai_model)}

JSON のキー名は上記のテーブル項目名だけを使ってください。別名は禁止です。
TASK_AI_NAME と TASK_AI_MODEL は全明細に必ず設定してください。通常は上記例の値をそのまま使います。
明細は必ずオブジェクト配列にしてください。配列行は禁止です。
- 明細SEQ=0 は開始行、タイトルは必ず「開始」、先行SEQ は空文字
- 明細SEQ=9999 は終了行、タイトルは必ず「終了」
- 実作業の明細SEQ は 1 から始まる整数
- 実作業の先行SEQ は先行する明細SEQのカンマ区切り文字列。最初の実作業は 0 を先行SEQ に含めてください
- 終了行 9999 の先行SEQ には、後続のない実作業明細SEQを設定してください
- どの明細でも先行SEQに自分自身の明細SEQを含めないでください。特に開始行の先行SEQに 0 を入れることは禁止です
- Mermaid のコードは出力せず、マーメイド記号には LR または TD だけを入れてください。標準は TD（縦表示）です
- 開始から終了まで依存関係がつながるように、実作業を 3〜10 件程度に分解してください
- 複数の処理を1つの明細にまとめた複合処理は禁止です。「Aして、Bして、Cする」のように「〜して」で複数の作業をつなげたタイトルや要求内容は不可です。1明細＝1処理になるまで細かく分割してください
- 要求内容が「通知音OK,NG,終了を順にならして。」のような通知音再生だけの場合、準備・確認などの余分な明細は作らず、
  明細SEQ=0 開始、明細SEQ=1 OK通知音再生、明細SEQ=2 NG通知音再生、明細SEQ=3 終了通知音再生、明細SEQ=9999 終了だけにしてください。

記述内容の詳しさとスタイルについて（タスク全体の要求内容、および各明細のタイトル・要求内容すべてに適用）:
- 各明細の要求内容は、その明細を担当する実行AIがこの一文だけを読んで着手できるように、対象（ファイル名・機能名・画面名・API名など）、作業内容（何をどう変更・確認・実行するか）、完了の目安を具体的に書いてください。「実装する」「確認する」「対応する」のような一文だけで終わる簡素な記述は禁止です
- タスク全体の要求内容も、入力された要求内容の要点を薄めずに、対象範囲と目的が伝わる具体的な文章に整理してください。単なる一言要約は禁止です
- 文体はビジネス文書の報告・指示文として通用する「〜する」「〜を確認する」調の常体で統一してください。口語表現、砕けた言い回し、過度な感嘆符・記号の連打は避けてください
- 絵文字、顔文字、矢印記号、囲み文字、装飾的な特殊記号は一切使用しないでください。Windows 環境の cp932 エンコードで書き込みエラーになるため、通常の漢字・ひらがな・カタカナ・半角英数字と、句点「。」読点「、」カギ括弧「」丸括弧()程度の一般的な句読点記号だけを使ってください

依存関係は次の Mermaid 図サンプルと同じ考え方で組み立ててください。
この例では 1 と 2 が開始後に並列実行でき、3 は 1 と 2 の完了後、9999 は 3 の完了後です。

```mermaid
flowchart LR
  N0(("開始"))
  N1["調査"]
  N2["設計"]
  N3["実装"]
  N9999(("終了"))
  N0 --> N1
  N0 --> N2
  N1 --> N3
  N2 --> N3
  N3 --> N9999
```

上の Mermaid 図に対応する明細は次の通りです。
- 明細SEQ=0: タイトル=開始, 先行SEQ=""
- 明細SEQ=1: タイトル=調査, 先行SEQ="0"
- 明細SEQ=2: タイトル=設計, 先行SEQ="0"
- 明細SEQ=3: タイトル=実装, 先行SEQ="1,2"
- 明細SEQ=9999: タイトル=終了, 先行SEQ="3"
"""


def プロンプト生成_JSON保存(分解結果: str, 出力JSONパス: str, 利用者ID: str, タスクID: str, プロジェクト: str, task_ai_name: str, task_ai_model: str) -> str:
    return f"""次の「タスク分解結果」から JSON オブジェクトを取り出し、JSON ファイルとして保存してください。
ファイルの保存先: {出力JSONパス}
保存先フォルダは既に存在します。UTF-8（BOMなし）で保存してください。
コードフェンスや説明文は取り除き、下記の既定形式（キー名は完全一致）に整えて保存してください。
明細の内容（タイトル・要求内容・先行SEQ の依存関係）は変更しないでください。
このファイル保存以外の作業（コードの修正、他ファイルの作成など）は一切行わないでください。

既定形式:
{JSON形式サンプル(利用者ID, タスクID, プロジェクト, task_ai_name, task_ai_model)}

タスク分解結果:
{分解結果}
"""


def JSON検証(データ: dict, default_task_ai_name: str, default_task_ai_model: str) -> list[dict]:
    """出力 JSON を検証し、タスク明細の行リストへ変換する。不正なら ValueError。"""
    if not isinstance(データ, dict):
        raise ValueError("JSON のルートがオブジェクトではありません")
    for キー in ("利用者ID", "タスクID", "プロジェクト", "タイトル", "要求内容", "マーメイド記号", "明細"):
        if キー not in データ:
            raise ValueError(f"キー '{キー}' がありません")
    if str(データ["利用者ID"]).strip() != 利用者ID:
        raise ValueError("利用者IDが入力 JSON と一致していません")
    if str(データ["タスクID"]).strip() != タスクID:
        raise ValueError("タスクIDが入力 JSON と一致していません")
    if not str(データ["タイトル"]).strip():
        raise ValueError("タイトルが空です")
    明細 = データ["明細"]
    if not isinstance(明細, list) or len(明細) == 0:
        raise ValueError("明細が空です")
    行リスト: list[dict] = []
    for 行 in 明細:
        if not isinstance(行, dict):
            raise ValueError(f"明細行の形式が不正です: {行!r}")
        for キー in ("利用者ID", "タスクID", "明細SEQ", "タイトル", "要求内容", "先行SEQ"):
            if キー not in 行:
                raise ValueError(f"明細行にキー '{キー}' がありません: {行!r}")
        if str(行["利用者ID"]).strip() != 利用者ID:
            raise ValueError(f"明細行の利用者IDが一致していません: {行!r}")
        if str(行["タスクID"]).strip() != タスクID:
            raise ValueError(f"明細行のタスクIDが一致していません: {行!r}")
        n = int(行["明細SEQ"])
        行リスト.append({
            "明細SEQ": n,
            "タイトル": str(行["タイトル"]).strip(),
            "要求内容": str(行["要求内容"]).strip(),
            "先行SEQ": str(行["先行SEQ"]).strip(),
            "TASK_AI_NAME": str(行.get("TASK_AI_NAME", default_task_ai_name) or default_task_ai_name).strip(),
            "TASK_AI_MODEL": str(行.get("TASK_AI_MODEL", default_task_ai_model) or default_task_ai_model).strip(),
        })
    明細SEQ集合 = {行["明細SEQ"] for 行 in 行リスト}
    if len(明細SEQ集合) != len(行リスト):
        raise ValueError("明細SEQが重複しています")
    if 0 not in 明細SEQ集合:
        raise ValueError("開始行（明細SEQ=0）がありません")
    if 9999 not in 明細SEQ集合:
        raise ValueError("終了行（明細SEQ=9999）がありません")
    for 行 in 行リスト:
        if 行["明細SEQ"] == 0:
            if 行["タイトル"] != "開始" or 行["先行SEQ"]:
                raise ValueError("開始行（明細SEQ=0）は タイトル='開始'、先行SEQ='' にしてください")
        elif 行["明細SEQ"] == 9999:
            if 行["タイトル"] != "終了" or not 行["先行SEQ"]:
                raise ValueError("終了行（明細SEQ=9999）は タイトル='終了'、先行SEQに終端明細を指定してください")
        elif 行["明細SEQ"] < 1:
            raise ValueError(f"明細SEQが不正です: {行['明細SEQ']}")
        elif not 行["タイトル"]:
            raise ValueError(f"明細タイトルが空です: {行!r}")
        elif not 行["先行SEQ"]:
            raise ValueError(f"実作業明細の先行SEQが空です: {行!r}")
        for p in 行["先行SEQ"].split(","):
            p = p.strip()
            if p and (not p.isdigit() or int(p) not in 明細SEQ集合):
                raise ValueError(f"先行SEQ '{行['先行SEQ']}' が明細SEQと対応していません")
            if p and int(p) == 行["明細SEQ"]:
                raise ValueError(f"先行SEQに自分自身が含まれています: {行!r}")
    return 行リスト


def 本登録(データ: dict, 行リスト: list[dict], 元要求内容: str) -> None:
    # 要求内容は仮登録時の人間の入力をそのまま残し、AI がタスク分解のために整理した
    # 文章（データ["要求内容"]）は応答内容へ送る（人間の元の要求が消えないようにするため）
    res = POST送信(f"{TASK_API}/タスク要求/本登録", {
        "利用者ID": 利用者ID,
        "タスクID": タスクID,
        "タイトル": str(データ["タイトル"]).strip(),
        "要求内容": 元要求内容,
        "マーメイド記号": str(データ["マーメイド記号"]).strip(),
        "明細": 行リスト,
        "応答内容": str(データ["要求内容"]).strip(),
    }, timeout=60)
    if res.get("status") != "OK":
        raise RuntimeError(f"本登録に失敗しました: {res.get('message')}")


def 失敗登録(メッセージ: str) -> None:
    if not タスクID:
        return
    try:
        POST送信(f"{TASK_API}/タスク要求/AI失敗", {
            "利用者ID": 利用者ID,
            "タスクID": タスクID,
            "メッセージ": メッセージ[:500],
        }, timeout=60)
    except Exception as e:
        ログ(f"失敗登録もエラー: {e}")


def main() -> int:
    global タスクID, 利用者ID, ログパス
    try:
        if len(sys.argv) < 2:
            raise ValueError("使い方: python sub_init.py <temp/input/タスクID.json>")
        入力パス = os.path.abspath(sys.argv[1])
        with open(入力パス, "r", encoding="utf-8-sig") as f:
            入力 = json.load(f)
        利用者ID = str(入力.get("利用者ID", "")).strip()
        タスクID = str(入力.get("タスクID", "")).strip()
        プロジェクト = str(入力.get("プロジェクト", "")).strip()
        要求内容 = str(入力.get("要求内容", "")).strip()
        task_ai_name = str(入力.get("TASK_AI_NAME", TASK_AI_NAME既定) or TASK_AI_NAME既定).strip()
        task_ai_model = str(入力.get("TASK_AI_MODEL", TASK_AI_MODEL既定) or TASK_AI_MODEL既定).strip()
        if not 利用者ID or not タスクID or not 要求内容:
            raise ValueError("入力 JSON に 利用者ID、タスクID または 要求内容 がありません")

        ファイルステム = os.path.splitext(os.path.basename(入力パス))[0]
        ログパス = os.path.join(BASE_DIR, "temp", "task", f"{ファイルステム}.log")
        ログ(f"=== AIタスク生成 開始: {利用者ID}/{タスクID} ===")
        ログ(f"入力: {入力パス}")

        # 0. 既存のタスク明細をクリアして再生成できる状態にする
        #    （明細に PID が残っていれば API 側で処理を停止してからレコードを消去する）
        res = POST送信(f"{TASK_API}/タスク明細/全消去", {"利用者ID": 利用者ID, "タスクID": タスクID}, timeout=60)
        ログ(f"既存明細クリア: {json.dumps(res, ensure_ascii=False)[:200]}")

        出力DIR = os.path.join(BASE_DIR, "temp", "output")
        os.makedirs(出力DIR, exist_ok=True)
        出力JSONパス = os.path.join(出力DIR, f"{ファイルステム}.json").replace("\\", "/")
        if os.path.exists(出力JSONパス):
            os.remove(出力JSONパス)

        # 1. 第1ステップ: 指定プロジェクトフォルダで AI がタスク分解（ファイル書き込みなし）
        ログ(f"第1ステップ: タスク分解 (ai={task_ai_name}, model={task_ai_model}, project_path={プロジェクト or '既定'})")
        payload = {
            "prompt": プロンプト生成_タスク分解(利用者ID, タスクID, プロジェクト, 要求内容, task_ai_name, task_ai_model),
            "ai_name": task_ai_name,
            "ai_model": task_ai_model,
        }
        if プロジェクト:
            payload["project_path"] = プロジェクト
        res = POST送信(MCP_URL, payload)
        ログ(f"第1ステップ応答: {json.dumps(res, ensure_ascii=False)[:300]}")
        if res.get("error") or res.get("status") != "OK":
            raise RuntimeError(f"第1ステップ（タスク分解）に失敗しました: {res.get('error') or res.get('result')}")
        分解結果 = str(res.get("result") or "").strip()
        if not 分解結果 or 分解結果 == "（応答なし）":
            raise RuntimeError("第1ステップ（タスク分解）の応答が空です")

        # 2. 第2ステップ: AiDiy ルート（"../"）で AI が既定形式の JSON を temp/output へ書き込む
        ログ(f"第2ステップ: JSON保存 (ai={task_ai_name}, model={task_ai_model}, project_path={AIDIYルート})")
        res = POST送信(MCP_URL, {
            "prompt": プロンプト生成_JSON保存(分解結果, 出力JSONパス, 利用者ID, タスクID, プロジェクト, task_ai_name, task_ai_model),
            "ai_name": task_ai_name,
            "ai_model": task_ai_model,
            "project_path": AIDIYルート,
        })
        ログ(f"第2ステップ応答: {json.dumps(res, ensure_ascii=False)[:300]}")
        if res.get("error") or res.get("status") != "OK":
            raise RuntimeError(f"第2ステップ（JSON保存）に失敗しました: {res.get('error') or res.get('result')}")

        # 3. 出力 JSON の確認と検証
        if not os.path.isfile(出力JSONパス):
            raise RuntimeError(f"出力 JSON が生成されませんでした: {出力JSONパス}")
        with open(出力JSONパス, "r", encoding="utf-8-sig") as f:
            データ = json.load(f)
        行リスト = JSON検証(データ, task_ai_name, task_ai_model)
        ログ(f"JSON 検証 OK: 明細 {len(行リスト)} 件")

        # 4. DB へ本登録（仮登録は置き換え）
        本登録(データ, 行リスト, 要求内容)
        ログ("本登録 完了")
        return 0

    except Exception as e:
        ログ(f"エラー: {e}\n{traceback.format_exc()}")
        失敗登録(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
