# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
backend_tools HTTP POST API スモークテスト

前提:
  backend_tools (port 8095) が起動済みであること。

方針:
  外部 AI 生成や長時間実行を避け、HTTP ルート、必須引数、代表的な
  ローカル処理だけを確認する。画像/動画/AI agent の実実行は行わない。

実行:
    cd backend_tools
    .venv/Scripts/python.exe tests/test_post_api_smoke.py
"""

from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path
from urllib import error, request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = os.environ.get("AIDIY_MCP_BASE_URL", "http://localhost:8095").rstrip("/")
TIMEOUT = float(os.environ.get("AIDIY_MCP_HTTP_TIMEOUT", "30"))
TEMP_DIR = Path(__file__).resolve().parent / "temp"


def _json_request(method: str, path: str, payload: dict | None = None) -> dict:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(f"{BASE_URL}{path}", data=data, method=method, headers=headers)
    try:
        with request.urlopen(req, timeout=TIMEOUT) as res:
            body = res.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed: HTTP {exc.code} {body}") from exc
    return json.loads(body)


def get(path: str) -> dict:
    return _json_request("GET", path)


def post(path: str, payload: dict | None = None) -> dict:
    return _json_request("POST", path, payload or {})


def assert_no_error(label: str, result: dict, allow_error: bool = False) -> None:
    if "error" in result and not allow_error:
        raise AssertionError(f"{label}: {result['error']}")


def main() -> None:
    print("=== backend_tools HTTP POST API スモークテスト ===")
    print(f"BASE_URL: {BASE_URL}")

    root = get("/")
    assert root.get("message") == "MCP Server is running", root
    print("  OK root")

    docs_paths = [
        "/aidiy_chrome_devtools/docs",
        "/aidiy_desktop_capture/docs",
        "/aidiy_sqlite/docs",
        "/aidiy_postgres/docs",
        "/aidiy_logs/docs",
        "/aidiy_code_check/docs",
        "/aidiy_backup/docs",
        "/aidiy_image_generation/docs",
        "/aidiy_movie_generation/docs",
        "/aidiy_speech_to_text/docs",
        "/aidiy_text_to_speech/docs",
        "/aidiy_obs_studio_control/docs",
        "/aidiy_ffmpeg_control/docs",
        "/aidiy_code_agents/docs",
    ]
    for path in docs_paths:
        doc = get(path)
        if "service" not in doc:
            raise AssertionError(f"{path}: service がありません")
    print(f"  OK docs ({len(docs_paths)})")

    # Chrome DevTools
    chrome_version = post("/aidiy_chrome_devtools/get_version")
    assert_no_error("chrome get_version", chrome_version)
    if "Browser" not in chrome_version and "result" not in chrome_version:
        raise AssertionError(f"chrome get_version: unexpected {chrome_version}")
    print("  OK chrome")

    # Desktop Capture
    cursor = post("/aidiy_desktop_capture/cursor_pos")
    assert_no_error("desktop cursor_pos", cursor)
    if "x" not in cursor or "y" not in cursor:
        raise AssertionError(f"cursor_pos: unexpected {cursor}")

    screen = post("/aidiy_desktop_capture/screen_info")
    assert_no_error("desktop screen_info", screen)
    if not isinstance(screen.get("monitors"), list):
        raise AssertionError(f"screen_info: unexpected {screen}")

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    shot_path = TEMP_DIR / "post_api_desktop.png"
    shot = post(
        "/aidiy_desktop_capture/screenshot",
        {"screen_number": "auto", "format": "png", "save_path": str(shot_path)},
    )
    assert_no_error("desktop screenshot", shot)
    if shot.get("type") != "image" or not shot.get("data"):
        raise AssertionError("desktop screenshot: image data がありません")
    base64.b64decode(shot["data"])
    print("  OK desktop_capture")

    # SQLite
    tables = post("/aidiy_sqlite/list_tables")
    assert_no_error("sqlite list_tables", tables)
    if not isinstance(tables.get("tables"), list):
        raise AssertionError(f"sqlite list_tables: unexpected {tables}")

    query = post("/aidiy_sqlite/query", {"sql": "SELECT 1 AS ok"})
    assert_no_error("sqlite query", query)
    if query.get("rows", [{}])[0].get("ok") != 1:
        raise AssertionError(f"sqlite query: unexpected {query}")
    print("  OK sqlite")

    # PostgreSQL は未設定環境があり得るので、ルート疎通とエラー整形だけ確認
    pg = post("/aidiy_postgres/server_info")
    assert isinstance(pg, dict)
    print("  OK postgres route" + (" (configured)" if "error" not in pg else " (error response checked)"))

    # Logs
    logs = post("/aidiy_logs/list")
    assert_no_error("logs list", logs)
    if "logs" not in logs:
        raise AssertionError(f"logs list: unexpected {logs}")

    tail = post("/aidiy_logs/tail", {"server": "mcp", "lines": 5})
    assert_no_error("logs tail", tail)
    print("  OK logs")

    # Code Check
    targets = post("/aidiy_code_check/list_targets")
    assert_no_error("code_check list_targets", targets)

    syntax = post(
        "/aidiy_code_check/python_syntax",
        {"file_path": "backend_tools/tools_main.py", "venv_project": "backend_tools"},
    )
    assert_no_error("code_check python_syntax", syntax)
    if syntax.get("ok") is not True:
        raise AssertionError(f"python_syntax: unexpected {syntax}")
    print("  OK code_check")

    # Backup
    backup_info = post("/aidiy_backup/check/info")
    assert_no_error("backup info", backup_info)

    backup_scan = post("/aidiy_backup/save/scan")
    assert_no_error("backup scan", backup_scan)

    versions = post("/aidiy_backup/check/versions", {"path": "backend_tools/tools_main.py"})
    assert isinstance(versions, dict)
    print("  OK backup")

    # Media generation routes: 実生成は行わず、未知メソッドで POST validation と routing を確認
    img_unknown = post("/aidiy_image_generation/unknown", {"prompt": "route check"})
    if "未知のメソッド" not in img_unknown.get("error", ""):
        raise AssertionError(f"image unknown: unexpected {img_unknown}")

    movie_unknown = post("/aidiy_movie_generation/unknown", {"prompt": "route check"})
    if "未知のメソッド" not in movie_unknown.get("error", ""):
        raise AssertionError(f"movie unknown: unexpected {movie_unknown}")
    print("  OK image/movie routes")

    # TTS は edge provider で短文のみ実行
    tts_path = TEMP_DIR / "post_api_tts.mp3"
    tts = post(
        "/aidiy_text_to_speech/synthesize",
        {
            "speech_text": "HTTP POST API のテストです。",
            "provider": "edge",
            "voice": "female",
            "ratio": 1,
            "save_path": str(tts_path),
        },
    )
    assert_no_error("tts synthesize", tts)
    if not tts.get("base64_audio") or not tts.get("save_path"):
        raise AssertionError(f"tts synthesize: unexpected {tts}")
    base64.b64decode(tts["base64_audio"])

    stt_missing = post("/aidiy_speech_to_text/recognize", {})
    if "いずれかが必要" not in stt_missing.get("error", ""):
        raise AssertionError(f"stt missing input: unexpected {stt_missing}")
    print("  OK tts/stt")

    # OBS / ffmpeg
    obs = post("/aidiy_obs_studio_control/startup_status")
    assert_no_error("obs startup_status", obs)

    ffmpeg = post("/aidiy_ffmpeg_control/versions")
    assert_no_error("ffmpeg versions", ffmpeg)
    checks = ffmpeg.get("checks", ffmpeg)
    if "ffmpeg" not in checks:
        raise AssertionError(f"ffmpeg versions: unexpected {ffmpeg}")
    print("  OK obs/ffmpeg")

    # Code agents は config のみ。run は別途明示して実行する。
    config = post("/aidiy_code_agents/config")
    assert_no_error("agents config", config)
    if "version_info" not in config and "ai_versions" not in config:
        raise AssertionError(f"agents config: unexpected keys {sorted(config.keys())}")
    print("  OK code_agents")

    print("\nOK")


if __name__ == "__main__":
    main()
