# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import re
from pathlib import Path


PERSONA_ROOT = Path(__file__).resolve().parents[1] / "persona"
要員ID最大長 = 16
要員ID形式 = re.compile(r"^[\w-]+$", re.UNICODE)


def _文字列一覧(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _要員ID検証(member_id: str) -> None:
    if not 1 <= len(member_id) <= 要員ID最大長:
        raise ValueError(
            f"personaフォルダ名は1～{要員ID最大長}文字にしてください: {member_id}"
        )
    if not 要員ID形式.fullmatch(member_id):
        raise ValueError(
            "personaフォルダ名に使用できるのは、空白を含まない"
            f"英数字・日本語・_・-だけです: {member_id}"
        )


def _persona読込(persona_folder: Path) -> dict:
    member_id = persona_folder.name
    _要員ID検証(member_id)
    json_path = persona_folder / "persona.json"
    if not json_path.is_file():
        raise ValueError(f"persona.jsonがありません: {member_id}")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"persona.jsonを読み込めません: {member_id}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"persona.jsonのルートはオブジェクトにしてください: {member_id}")

    specialties = _文字列一覧(data.get("得意分野"))
    personalities = _文字列一覧(data.get("性格"))
    role = str(data.get("役割", "")).strip() or (
        specialties[0] if specialties else "AIエージェント"
    )
    return {
        "要員ID": member_id,
        "要員名": member_id,
        "役割": role,
        "人格情報": "\n".join(personalities),
        "人物名": str(data.get("人物名", member_id)).strip() or member_id,
        "ニックネーム": str(data.get("ニックネーム", member_id)).strip() or member_id,
        "有効": True,
    }


def list_personas() -> list[dict]:
    if not PERSONA_ROOT.is_dir():
        return []
    folders = sorted(
        (path for path in PERSONA_ROOT.iterdir() if path.is_dir()),
        key=lambda path: (path.name != "admin", path.name.casefold()),
    )
    items = [_persona読込(folder) for folder in folders]
    if not any(item["要員ID"] == "admin" for item in items):
        raise ValueError("初期メンバーのpersona/adminがありません")
    return items


def get_persona(member_id: str) -> dict | None:
    member_id = member_id.strip()
    _要員ID検証(member_id)
    persona_folder = PERSONA_ROOT / member_id
    if not persona_folder.is_dir():
        return None
    return _persona読込(persona_folder)
