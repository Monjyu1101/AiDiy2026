# -*- coding: utf-8 -*-

from __future__ import annotations

import importlib.util
from functools import lru_cache
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_SERVER_DIR = PROJECT_ROOT / "backend_server"
KEY_JSON_PATH = BACKEND_SERVER_DIR / "_config" / "AiDiy_key.json"
CONF_JSON_PATH = BACKEND_SERVER_DIR / "conf" / "conf_json.py"


def _load_conf_json_class() -> type:
    """conf パッケージ全体を読み込まず、共通 conf_json 実装だけを利用する。"""
    spec = importlib.util.spec_from_file_location("_aidiy_team_conf_json", CONF_JSON_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"conf_json.py を読み込めません: {CONF_JSON_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.conf_json


@lru_cache(maxsize=1)
def load_config() -> Any:
    """共通 conf_json で AiDiy_key.json を読み、不足キーも共通規則で補完する。"""
    return _load_conf_json_class()(json=str(KEY_JSON_PATH))


def get_team_port() -> int:
    """TEAM_BASE を返す。初期値と不足キー補完は conf_json.DEFAULT_CONFIG に集約する。"""
    return int(load_config().TEAM_BASE)
