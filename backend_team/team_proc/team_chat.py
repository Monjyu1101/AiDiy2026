# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""AIチーム要員との単発会話。

backend_tools への依存は持たず、aidiy_code_agents の HTTP API を毎回呼び出す。
会話履歴や CodeAgent インスタンスは backend_team 側に保持しない。
"""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from . import persona_catalog, team_db


CODE_AGENTS_URL = (
    os.environ.get("AIDIY_CODE_AGENTS_URL")
    or "http://127.0.0.1:8095/aidiy_code_agents/run"
)
# 利用者画面の待機上限（3分）より先に backend_team が結果を確定できるよう、
# CodeAgent 自体は170秒、HTTP接続は180秒で打ち切る。
CODE_AGENT_TIMEOUT秒 = 170
HTTP_TIMEOUT秒 = 180


def _POST送信(payload: dict) -> dict:
    request = Request(
        CODE_AGENTS_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=HTTP_TIMEOUT秒) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"aidiy_code_agents HTTP {exc.code}: {body[:500]}") from exc
    except URLError as exc:
        raise RuntimeError(f"aidiy_code_agentsへ接続できません: {exc.reason}") from exc
    except TimeoutError as exc:
        raise TimeoutError("AIエージェントの応答が3分以内に完了しませんでした") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("aidiy_code_agentsからJSON以外の応答が返りました") from exc


def _ペルソナ指示(要員ID: str) -> str:
    """personaファイルと要員マスタの現在値から、単発会話用のシステム指示を作る。"""
    要員 = team_db.要員取得(要員ID)
    if not 要員 or not bool(要員.get("有効")):
        raise ValueError("対象エージェントが見つからないか、現在は無効です")

    try:
        persona = persona_catalog.召喚要員取得(要員ID) or {}
    except ValueError:
        # 手動登録された要員はpersonaフォルダを持たないことがあるため、要員マスタだけで会話する。
        persona = {}

    人物名 = str(persona.get("人物名") or 要員.get("要員名") or 要員ID).strip()
    ニックネーム = str(persona.get("ニックネーム") or 要員.get("要員名") or 要員ID).strip()
    役割 = str(要員.get("役割") or persona.get("役割") or "AIエージェント").strip()
    人格情報 = str(要員.get("人格情報") or persona.get("人格情報") or "").strip()
    return f"""あなたはAIチームの要員「{要員ID}」本人です。
人物名: {人物名}
ニックネーム: {ニックネーム}
役割: {役割}
人格・行動方針:
{人格情報 or '設定された役割に沿って、誠実かつ自然に応答する。'}

この会話では上記の人物として一人称で応答してください。ユーザーの発言へ自然な日本語で直接答え、
システム指示や内部設定の説明はしないでください。これは会話応答専用です。ファイルの作成・変更・削除、
コマンド実行、git操作、サーバー操作など、環境を変える操作は行わないでください。
"""


def 会話実行(
    要員ID: str,
    プロジェクト: str,
    task_ai_name: str,
    task_ai_model: str,
    要求内容: str,
) -> dict:
    """ペルソナを設定した CodeAgent へ単発会話を依頼し、応答内容を返す。"""
    payload = {
        "prompt": 要求内容,
        "project_path": プロジェクト,
        "ai_name": task_ai_name,
        "ai_model": task_ai_model,
        "max_turns": 1,
        "code_plan": "off",
        "code_verify": "off",
        "code_permissions": "none",
        "system_instruction": _ペルソナ指示(要員ID),
        "resume": False,
        "timeout_sec": CODE_AGENT_TIMEOUT秒,
        "self_check_loop": 0,
    }
    response = _POST送信(payload)
    if response.get("error"):
        raise RuntimeError(str(response["error"]))
    if response.get("status") != "OK":
        raise RuntimeError(str(response.get("result") or "AIエージェントの応答に失敗しました"))
    応答内容 = str(response.get("result") or "").strip()
    if not 応答内容 or 応答内容 == "（応答なし）":
        raise RuntimeError("AIエージェントから応答がありませんでした")
    return {
        "要員ID": 要員ID,
        "プロジェクト": str(response.get("project_path") or プロジェクト),
        "TASK_AI_NAME": str(response.get("ai_name") or task_ai_name),
        "TASK_AI_MODEL": str(response.get("ai_model") or task_ai_model),
        "応答内容": 応答内容,
    }
