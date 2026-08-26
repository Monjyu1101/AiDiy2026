# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""AIタスクの定型コンテキスト読込。

`_config/AiDiy_task__context.json` が無ければひな形を書き出し、あればその内容を使う。
AIコア/AIチャット.py の定型コンテキスト読込と同じ方式で、標準ライブラリのみで動作する。

フェーズ名は `AiDiy_key.json` の `TASK_AI_MODEL_<フェーズ>` と同じ plan / do / check。
  plan  : sub_init.py      タスク分解（第1ステップ）と JSON 保存（第2ステップ）
  do    : sub_proc.py      明細 1 ステップの実行
  check : sub_terminate.py 最終検証

各テンプレートは `{名前}` 形式の差込キーを含む。差込は str.replace で行うため、
プロンプト中に出てくる JSON の例（`{"タスクID": ...}`）はそのまま書いてよい。
"""

from __future__ import annotations

import json
import os
import re

# 差込キー `{名前}` の検出用。波括弧を含まない 1 行内の名前だけを対象にするので、
# プロンプト中の JSON 例の外側の波括弧には一致しない。
_差込パターン = re.compile(r"\{([^{}\n]+)\}")

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TASK_CONTEXT_JSON_PATH = os.path.normpath(
    os.path.join(_BASE_DIR, "..", "_config", "AiDiy_task__context.json")
)

_PLAN_INSTRUCTION_TEMPLATE_LINES = [
    "次の要求内容を分析してタスク分解し、結果を JSON 形式の文字列として応答本文にそのまま出力してください。",
    "このプロジェクトの構成や実装状況を確認し、このプロジェクトに最適なタスク分解にしてください。",
    "ファイルの作成・書き込み・コードの修正などの作業は一切行わず、応答本文へ JSON を出力するだけにしてください。",
    "",
    "要求内容:",
    "{要求内容}",
    "",
    "出力する JSON の形式:",
    "{JSON形式サンプル}",
    "",
    "JSON のキー名は上記のテーブル項目名だけを使ってください。別名は禁止です。",
    "TASK_AI_NAME と TASK_AI_MODEL_do は全明細に必ず設定してください。通常は上記例の値をそのまま使います。",
    "明細は必ずオブジェクト配列にしてください。配列行は禁止です。",
    "- 明細SEQ=0 は開始行、タイトルは必ず「開始」、先行SEQ は空文字",
    "- 明細SEQ=9999 は終了行、タイトルは必ず「終了」",
    "- 実作業の明細SEQ は 1 から始まる整数",
    "- 実作業の先行SEQ は先行する明細SEQのカンマ区切り文字列。最初の実作業は 0 を先行SEQ に含めてください",
    "- 終了行 9999 の先行SEQ には、後続のない実作業明細SEQを設定してください",
    "- どの明細でも先行SEQに自分自身の明細SEQを含めないでください。特に開始行の先行SEQに 0 を入れることは禁止です",
    "- 操作検証は、その明細がファイルの更新・追加・書込を伴う作業であれば true、調査・確認・実行のみなど書込を伴わない作業であれば false にしてください",
    "- 明細SEQ=0（開始行）の操作検証は必ず false にしてください",
    "- 明細SEQ=9999（終了行）の操作検証は、他のいずれかの明細で操作検証が true であれば true、1件も無ければ false にしてください",
    "- Mermaid のコードは出力せず、マーメイド記号には LR または TD だけを入れてください。標準は TD（縦表示）です",
    "- 開始から終了まで依存関係がつながるように、実作業を 3〜10 件程度に分解してください",
    "- 複数の処理を1つの明細にまとめた複合処理は禁止です。「Aして、Bして、Cする」のように「〜して」で複数の作業をつなげたタイトルや要求内容は不可です。1明細＝1処理になるまで細かく分割してください",
    "- 要求内容が「通知音OK,NG,終了を順にならして。」のような通知音再生だけの場合、準備・確認などの余分な明細は作らず、",
    "  明細SEQ=0 開始、明細SEQ=1 OK通知音再生、明細SEQ=2 NG通知音再生、明細SEQ=3 終了通知音再生、明細SEQ=9999 終了だけにしてください。",
    "",
    "記述内容の詳しさとスタイルについて（タスク全体の要求内容、および各明細のタイトル・要求内容すべてに適用）:",
    "- 各明細の要求内容は、その明細を担当する実行AIがこの一文だけを読んで着手できるように、対象（ファイル名・機能名・画面名・API名など）、作業内容（何をどう変更・確認・実行するか）、完了の目安を具体的に書いてください。「実装する」「確認する」「対応する」のような一文だけで終わる簡素な記述は禁止です",
    "- タスク全体の要求内容も、入力された要求内容の要点を薄めずに、対象範囲と目的が伝わる具体的な文章に整理してください。単なる一言要約は禁止です",
    "- 文体はビジネス文書の報告・指示文として通用する「〜する」「〜を確認する」調の常体で統一してください。口語表現、砕けた言い回し、過度な感嘆符・記号の連打は避けてください",
    "- 絵文字、顔文字、矢印記号、囲み文字、装飾的な特殊記号は一切使用しないでください。Windows 環境の cp932 エンコードで書き込みエラーになるため、通常の漢字・ひらがな・カタカナ・半角英数字と、句点「。」読点「、」カギ括弧「」丸括弧()程度の一般的な句読点記号だけを使ってください",
    "",
    "依存関係は次の Mermaid 図サンプルと同じ考え方で組み立ててください。",
    "この例では 1 と 2 が開始後に並列実行でき、3 は 1 と 2 の完了後、9999 は 3 の完了後です。",
    "",
    "```mermaid",
    "flowchart LR",
    "  N0((\"開始\"))",
    "  N1[\"調査\"]",
    "  N2[\"設計\"]",
    "  N3[\"実装\"]",
    "  N9999((\"終了\"))",
    "  N0 --> N1",
    "  N0 --> N2",
    "  N1 --> N3",
    "  N2 --> N3",
    "  N3 --> N9999",
    "```",
    "",
    "上の Mermaid 図に対応する明細は次の通りです。",
    "- 明細SEQ=0: タイトル=開始, 先行SEQ=\"\"",
    "- 明細SEQ=1: タイトル=調査, 先行SEQ=\"0\"",
    "- 明細SEQ=2: タイトル=設計, 先行SEQ=\"0\"",
    "- 明細SEQ=3: タイトル=実装, 先行SEQ=\"1,2\"",
    "- 明細SEQ=9999: タイトル=終了, 先行SEQ=\"3\"",
]

_PLAN_SAVE_TEMPLATE_LINES = [
    "次の「タスク分解結果」から JSON オブジェクトを取り出し、JSON ファイルとして保存してください。",
    "ファイルの保存先: {出力JSONパス}",
    "保存先フォルダは既に存在します。UTF-8（BOMなし）で保存してください。",
    "コードフェンスや説明文は取り除き、下記の既定形式（キー名は完全一致）に整えて保存してください。",
    "明細の内容（タイトル・要求内容・先行SEQ の依存関係）は変更しないでください。",
    "このファイル保存以外の作業（コードの修正、他ファイルの作成など）は一切行わないでください。",
    "",
    "既定形式:",
    "{JSON形式サンプル}",
    "",
    "タスク分解結果:",
    "{分解結果}",
]

# do / check 共通の外枠。ここに差込キーを増やすと先頭が毎回変わりキャッシュが効かなくなる。
# 役割やフェーズ固有の指示は {今回要求ブロック} 側（末尾）に置くこと。
_COMMON_INSTRUCTION_TEMPLATE_LINES = [
    "このプロンプトは [タイトル] [全体タスク] [実行済み] [今回要求] の順に並んでいます。",
    "実際に行うのは [今回要求] に書かれた内容だけです。あなたの役割も [今回要求] の冒頭に書いてあります。",
    "[タイトル] [全体タスク] [実行済み] は前提を把握するための情報なので、読むだけで作業はしないでください。",
    "",
    "注意:",
    "- [実行済み] のステップは完了済みです。やり直したり作り直したりしないでください。",
    "- [全体タスク] は依存関係の把握用の一覧です。ここから作業を拾わないでください。",
    "- AiDiy の MCP ツールが HTTP で利用できます。",
    "  ツール一覧の確認: GET http://127.0.0.1:8095/<mcp名>/list",
    "  ツールの実行: POST http://127.0.0.1:8095/<mcp名>/<メソッド> （JSON ボディ）",
    "  例: aidiy_notification_sounds, aidiy_sqlite, aidiy_chrome_devtools など",
    "",
    "[タイトル]:",
    "{タスクタイトル}",
    "",
    "[全体タスク]:",
    "{全ステップ}",
    "",
    "[実行済み]:（ステップ0 開始 の応答内容が処理目標です）",
    "{実行済ブロック}",
    "",
    "[今回要求]:※ここだけ実行してください。",
    "{今回要求ブロック}",
]

_DO_REQUEST_TEMPLATE_LINES = [
    "あなたはタスクの 1 ステップを実行する担当です。",
    "このステップの作業だけを行い、先行・後続ステップの作業は行わないでください。",
    "作業が完了したら、実行した内容と結果を簡潔に報告してください。",
    "",
    "ステップ{明細SEQ} {明細タイトル}",
    "{明細要求内容}",
    "{再試行ブロック}{操作検証ブロック}",
]

_DO_VERIFY_TEMPLATE_LINES = [
    "",
    "【操作検証】このステップはファイルの更新・追加・書込を伴う作業です。作業後に変更内容を",
    "実際に確認し、意図した通りに反映されているか検証してください。検証したら、結果を必ず",
    "次の HTTP エンドポイントへ直接報告してください（curl 等でこの AI エージェント自身が呼び出します）。",
    "  POST http://127.0.0.1:8093/task_check_okng",
    "  Content-Type: application/json",
    "  Body: {\"タスクID\": \"{タスクID}\", \"SEQ\": {明細SEQ}, \"状態\": \"完了\", \"メッセージ\": \"検証内容の要約\"}",
    "  検証で問題が見つかった場合は 状態 を \"エラー\" にし、メッセージ に理由を書いてください。",
]

_DO_RETRY_TEMPLATE_LINES = [
    "",
    "【前回試行の検証結果】前回このステップを実行しましたが、検証NGまたは検証結果の未報告により",
    "やり直しになっています。次の内容を踏まえて、問題を解消したうえで再実行してください。",
    "前回の理由: {前回失敗理由}",
]

_CHECK_REQUEST_TEMPLATE_LINES = [
    "あなたはタスク全体の最終検証（操作検証）を行う担当です。",
    "検証のみを行い、コードの修正や新しい作業は行わないでください。",
    "[実行済み] の処理目標に対して、各実行ステップの記録と実際の成果物を照合し、最終結果を検証してください。",
    "ファイル操作を伴わない処理は、渡された実行済ステップの記録だけから簡素に判断し、",
    "ファイル確認や追加のツール実行は行わないでください。",
    "",
    "ステップ{明細SEQ} {明細タイトル}",
    "各実行ステップの検証と最終結果の検証をお願いします。",
    "検証結果は必ず次の HTTP エンドポイントへ直接報告してください（あなた自身が curl 等で呼び出します）。",
    "  POST http://127.0.0.1:8093/task_check_okng",
    "  Content-Type: application/json",
    "  Body: {\"タスクID\": \"{タスクID}\", \"SEQ\": {明細SEQ}, \"状態\": \"完了\", \"メッセージ\": \"検証結論の要約\"}",
    "  問題が見つかった場合は 状態 を \"エラー\" にし、メッセージ に理由を書いてください。",
    "  この報告が今回のステップの完了条件です。報告を行わずに終えないでください。",
]


# JSON のキー名 -> ひな形の行データ
_TEMPLATE_KEYS = {
    "plan_instruction_lines": _PLAN_INSTRUCTION_TEMPLATE_LINES,
    "plan_save_instruction_lines": _PLAN_SAVE_TEMPLATE_LINES,
    "common_instruction_lines": _COMMON_INSTRUCTION_TEMPLATE_LINES,
    "do_request_lines": _DO_REQUEST_TEMPLATE_LINES,
    "do_verify_lines": _DO_VERIFY_TEMPLATE_LINES,
    "do_retry_lines": _DO_RETRY_TEMPLATE_LINES,
    "check_request_lines": _CHECK_REQUEST_TEMPLATE_LINES,
}


def _context_template_payload() -> dict:
    payload = {
        "version": 1,
        "description": "AIタスク 定型コンテキスト（plan=分解 / do=ステップ実行 / check=最終検証）",
    }
    payload.update({キー: list(行) for キー, 行 in _TEMPLATE_KEYS.items()})
    return payload


def _compose_instruction(lines: list) -> str:
    text = "\n".join(str(行) for 行 in lines)
    if not text.endswith("\n"):
        text += "\n"
    return text


def _ひな形書き出し(理由: str) -> dict:
    payload = _context_template_payload()
    try:
        os.makedirs(os.path.dirname(_TASK_CONTEXT_JSON_PATH), exist_ok=True)
        with open(_TASK_CONTEXT_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"[Task] 定型コンテキストJSONを{理由}: {_TASK_CONTEXT_JSON_PATH}", flush=True)
    except Exception as e:
        print(f"[Task] 定型コンテキストJSON書き出しエラー: {e}", flush=True)
    return payload


def _load_or_create_task_context() -> dict:
    """定型コンテキストJSONを読み込む。無ければひな形を作成して返す。

    キー単位で検証し、欠けているキー・形式不正なキーだけひな形で補う。
    """
    if not os.path.exists(_TASK_CONTEXT_JSON_PATH):
        return _ひな形書き出し("作成")

    try:
        with open(_TASK_CONTEXT_JSON_PATH, "r", encoding="utf-8-sig") as f:
            payload = json.load(f)
    except Exception as e:
        print(f"[Task] 定型コンテキスト読込エラー: {e}", flush=True)
        return _context_template_payload()

    if not isinstance(payload, dict):
        return _ひな形書き出し("形式不正のため再作成")

    結果 = dict(payload)
    for キー, ひな形 in _TEMPLATE_KEYS.items():
        値 = payload.get(キー)
        if not isinstance(値, list):
            print(f"[Task] 定型コンテキストのキー '{キー}' が不正。ひな形を使います", flush=True)
            結果[キー] = list(ひな形)
    return 結果


_コンテキスト = None


def コンテキスト取得(キー: str) -> str:
    """指定キーの定型コンテキストを 1 本のテキストとして返す（プロセス内で1回だけ読込）"""
    global _コンテキスト
    if _コンテキスト is None:
        _コンテキスト = _load_or_create_task_context()
    行 = _コンテキスト.get(キー)
    if not isinstance(行, list):
        行 = _TEMPLATE_KEYS.get(キー, [])
    return _compose_instruction(行)


def 差し込み(キー: str, 値: dict) -> str:
    """定型コンテキストの `{名前}` を値で置換して返す。

    str.format ではなく 1 回だけの走査で置換する。
      - プロンプト中の JSON 例（`{"タスクID": ...}`）をエスケープしなくてよい
      - 値に含まれない `{...}` はそのまま残す
      - 差し込んだ値の中身は再走査しない（ブロックの入れ子で二重置換が起きない）
    """
    テキスト = コンテキスト取得(キー)

    def _置換(m):
        名前 = m.group(1)
        return str(値[名前]) if 名前 in 値 else m.group(0)

    return _差込パターン.sub(_置換, テキスト)
