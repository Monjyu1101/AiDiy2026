# -*- coding: utf-8 -*-
"""
infra.py — インフラ系ユーティリティ統合モジュール

以下を統合:
  http_utils, backup_utils, agent_utils, verify_utils,
  ui_utils, guide_utils, browser_utils, step_tracker, config

VideoGenCtx を受け取る ctx_* ラッパーも含む。
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import TYPE_CHECKING

from .log_config import get_logger

_logger = get_logger("video_gen.infra")

if TYPE_CHECKING:
    from .ctx import VideoGenCtx


# ================================================================== #
# HTTP ユーティリティ (http_utils)
# ================================================================== #

def post_json(url: str, payload: dict, timeout_sec: int = 120) -> dict:
    """HTTP API へ JSON を POST し、JSON レスポンスを dict として返す。"""
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as res:
            raw = res.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        _logger.error("HTTP API 接続失敗: %s (%s)", url, e)
        raise RuntimeError(f"HTTP API に接続できません: {url} ({e})") from e

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        _logger.error("HTTP API JSON 解析失敗: %s ...", raw[:200])
        raise RuntimeError(f"HTTP API の JSON 解析に失敗しました: {raw[:200]}") from e
    if isinstance(result, dict) and result.get("error"):
        _logger.error("HTTP API エラー: %s", result['error'])
        raise RuntimeError(f"HTTP API エラー: {result['error']}")
    return result


def post_mcp_method(base_url: str, method_name: str, payload: dict | None = None, timeout_sec: int = 120) -> dict:
    """HTTP Transport の /{mcp_name}/{method_name} を POST で呼ぶ。"""
    url = f"{base_url.rstrip('/')}/{method_name.lstrip('/')}"
    return post_json(url, payload or {}, timeout_sec=timeout_sec)


# ================================================================== #
# コンソール表示・スクリプト実行 (ui_utils)
# ================================================================== #

def sep(title: str) -> None:
    """コンソール上でステップの区切りを見やすく表示する。"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def check(label: str, ok: bool) -> bool:
    """検証結果を統一フォーマットで出力し、呼び出し元へ真偽値を返す。"""
    mark = "✓" if ok else "✗"
    print(f"  [{mark}] {label}")
    return ok


def run_python_script(mcp_python: str, script_path: str) -> None:
    """指定の Python インタープリタで補助スクリプトを実行する。"""
    _logger.info("run_python_script: %s", os.path.basename(script_path))
    result = subprocess.run(
        [mcp_python, script_path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.stdout.strip():
        print(result.stdout.rstrip())
        _logger.debug("stdout: %s", result.stdout.rstrip()[:500])
    if result.stderr.strip():
        print(result.stderr.rstrip())
        _logger.warning("stderr: %s", result.stderr.rstrip()[:500])
    if result.returncode != 0:
        _logger.error("スクリプト実行失敗: %s (exit=%s)", script_path, result.returncode)
        raise RuntimeError(f"スクリプト実行に失敗しました: {script_path} (exit={result.returncode})")


# ================================================================== #
# 設定 JSON 読み込み (config)
# ================================================================== #

def require_mapping(data: dict, key: str, setting_json_name: str) -> dict:
    value = data.get(key)
    if not isinstance(value, dict):
        raise RuntimeError(f"{setting_json_name} に {key} セクションが必要です")
    return value


def require_string(data: dict, key: str, setting_json_name: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{setting_json_name} に文字列 {key} が必要です")
    return value


def require_bool(data: dict, key: str, setting_json_name: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise RuntimeError(f"{setting_json_name} に bool {key} が必要です")
    return value


def require_int(data: dict, key: str, setting_json_name: str) -> int:
    value = data.get(key)
    if not isinstance(value, int):
        raise RuntimeError(f"{setting_json_name} に int {key} が必要です")
    return value


def load_setting_json(setting_json_path: str, setting_json_name: str = "") -> dict:
    """設定 JSON を読み込んで返す。ファイルが無ければ空辞書。"""
    if not os.path.isfile(setting_json_path):
        return {}
    try:
        with open(setting_json_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"WARNING: {setting_json_name or setting_json_path} の読み込みに失敗しました: {e}")
        return {}


# ================================================================== #
# ステップ進捗 JSON 管理 (step_tracker)
# ================================================================== #

def _save_steps_json(steps_json_path: str, data: dict) -> None:
    """実行完了ステップ JSON を UTF-8 で保存する。"""
    with open(steps_json_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


STEPS_JSON_KEY = "complete_steps"


def ensure_steps_json(steps_json_path: str, steps_json_name: str, required_keys: tuple = ()) -> dict:
    """実行完了ステップ JSON を初期化し、complete_steps を必ず持つ dict を返す。"""
    data: dict = {}
    if os.path.isfile(steps_json_path):
        try:
            with open(steps_json_path, encoding="utf-8-sig") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data = loaded
        except Exception as e:
            print(f"WARNING: {steps_json_name} の読み込みに失敗しました。初期化します: {e}")

    changed = False
    if STEPS_JSON_KEY not in data or not isinstance(data.get(STEPS_JSON_KEY), str):
        migrated_value = ""
        for key in required_keys:
            if isinstance(data.get(key), str) and data.get(key):
                migrated_value = data.get(key, "")
                break
        data[STEPS_JSON_KEY] = migrated_value
        changed = True
    for key in required_keys:
        if key in data:
            del data[key]
            changed = True
    if changed or not os.path.isfile(steps_json_path):
        _save_steps_json(steps_json_path, data)
    return data


def step_no_to_value(step_no: int) -> str:
    """ステップ番号を JSON 保存値へ変換する。"""
    return "99" if step_no == 99 else f"{step_no:02d}"


def step_value_to_int(value: str) -> int:
    """JSON 保存値を比較用の整数へ変換する。未実行は -1。"""
    text = str(value or "").strip()
    if not text:
        return -1
    try:
        return int(text)
    except ValueError:
        return -1


def next_step_after(value: str) -> int:
    """完了済みステップ値から次に実行するステップ番号を返す。"""
    current = step_value_to_int(value)
    if current < 0:
        return 0
    if 0 <= current < 8:
        return current + 1
    if current == 8:
        return 99
    return 99


def get_completed_step(ctx: "VideoGenCtx") -> str:
    """ctx から現在の完了ステップ文字列を返す。"""
    data = ensure_steps_json(ctx.steps_json_path, ctx.steps_json_name, (ctx.script_type,))
    return str(data.get(STEPS_JSON_KEY, "") or "")


def set_completed_step(ctx: "VideoGenCtx", step_no: int) -> None:
    """ctx の完了ステップを更新して保存する。"""
    data = ensure_steps_json(ctx.steps_json_path, ctx.steps_json_name, (ctx.script_type,))
    value = step_no_to_value(step_no)
    data[STEPS_JSON_KEY] = value
    _save_steps_json(ctx.steps_json_path, data)
    print(f"  [steps] complete_steps = {value}")


# ================================================================== #
# バックアップユーティリティ (backup_utils)
# ================================================================== #

def post_backup_api(backup_url: str, dry_run: bool) -> dict:
    """dry_run=True → /scan（コピーなし）、dry_run=False → /run（差分コピー）"""
    method = "scan" if dry_run else "run"
    url = f"{backup_url}/{method}"
    try:
        return post_json(url, {}, timeout_sec=120)
    except RuntimeError as e:
        raise RuntimeError(str(e).replace("HTTP API", "backup API")) from e


# Internal alias kept for backward compat within this module
_post_backup_api = post_backup_api


def backup_diff_count(ctx: "VideoGenCtx") -> int:
    """POST /aidiy_backup/save/scan で現時点の差分バックアップ対象ファイル数を返す。"""
    result = _post_backup_api(ctx.backup_api_url, dry_run=True)
    count = int(result.get("count", 0))
    files = result.get("差分ファイル", []) or []
    print(f"  [backup] dry_run 差分ファイル数: {count}")
    if files:
        for path in files[:10]:
            print(f"    - {path}")
        if len(files) > 10:
            print(f"    ... 他 {len(files) - 10} 件")
    return count


def backup_diff_count_url(backup_url: str) -> int:
    """URL 直接版（step_create_folder などで使用）。"""
    result = _post_backup_api(backup_url, dry_run=True)
    count = int(result.get("count", 0))
    files = result.get("差分ファイル", []) or []
    print(f"  [backup] dry_run 差分ファイル数: {count}")
    if files:
        for path in files[:10]:
            print(f"    - {path}")
        if len(files) > 10:
            print(f"    ... 他 {len(files) - 10} 件")
    return count


def backup_save_once(ctx: "VideoGenCtx") -> bool:
    """POST /aidiy_backup/save/run で差分バックアップを 1 回実行し、成功可否を返す。"""
    result = _post_backup_api(ctx.backup_api_url, dry_run=False)
    ok = bool(result.get("ok"))
    print(
        "  [backup] "
        f"ok={ok} バックアップ件数={result.get('バックアップ件数')} "
        f"差分なし={result.get('差分なし')} 先={result.get('バックアップ先')}"
    )
    return ok


def backup_save_once_url(backup_url: str) -> bool:
    """URL 直接版（step_create_folder などで使用）。"""
    result = _post_backup_api(backup_url, dry_run=False)
    ok = bool(result.get("ok"))
    print(
        "  [backup] "
        f"ok={ok} バックアップ件数={result.get('バックアップ件数')} "
        f"差分なし={result.get('差分なし')} 先={result.get('バックアップ先')}"
    )
    return ok


# ================================================================== #
# TTS 音声案内 (guide_utils)
# ================================================================== #

_PROGRESS_TTS_EDGE_VOICES_EN = {
    "female": "en-US-AvaNeural",
    "male": "en-US-AndrewNeural",
}


def _progress_tts_voice_en(voice: str) -> str:
    return _PROGRESS_TTS_EDGE_VOICES_EN.get((voice or "female").lower(), voice)


def progress_step_label(step_name: str) -> str:
    """Japanese step labels → English progress speech labels."""
    labels = {
        "Step 00: 初期確認": "Step zero, preflight",
        "Step 01: フォルダ作成": "Step one, folder preparation",
        "Step 02: シナリオ作成": "Step two, scenario translation",
        "Step 03: HTML修正": "Step three, HTML translation",
        "Step 04: 画像生成": "Step four, image generation",
        "Step 05: 中間確認": "Step five, mid review",
        "Step 06: 音声生成": "Step six, audio generation",
        "Step 07: 再生時間更新": "Step seven, duration update",
        "Step 08: 最終確認": "Step eight, final review",
        "Step 99: 完成案内": "Step ninety-nine, completion notice",
    }
    return labels.get(step_name, step_name)


def guide_tts(
    ctx: "VideoGenCtx",
    message: str,
    *,
    voice: str = "female",
) -> None:
    """
    aidiy_text_to_speech API で実行状況を読み上げる。

    Parameters
    ----------
    ctx : VideoGenCtx
    message : str
    voice : str  "female" または "male"
    """
    if not ctx.tts_guide:
        return
    text = message.strip()
    if not text:
        return

    actual_voice = voice
    if ctx.use_english_voice:
        actual_voice = _progress_tts_voice_en(voice)

    payload = {
        "speech_text": text,
        "language": ctx.progress_tts_language,
        "provider": ctx.progress_tts_provider,
        "voice": actual_voice,
        "play": True,
        "local_play": True,
    }
    try:
        post_json(ctx.tts_api_url, payload, timeout_sec=90)
    except Exception as e:
        print(f"  [tts] 案内音声をスキップしました: {e}")


# ================================================================== #
# Chrome ブラウザプレビュー (browser_utils)
# ================================================================== #

PREVIEW_MIN_SCENE_SEC = 5.0


def _preview_url(frontend_base_url: str, folder_name: str, *, speaker_enabled: bool = True) -> str:
    base = frontend_base_url.rstrip("/")
    folder = urllib.parse.quote(folder_name.replace("\\", "/"), safe="")
    speaker_query = "" if speaker_enabled else "&speaker=false"
    return f"{base}/Xビデオ/{folder}/index.html?auto=loop&preview_min_sec={PREVIEW_MIN_SCENE_SEC:g}{speaker_query}"


def ensure_preview_minimum_duration_mcp(index_path: str) -> None:
    """mcp 形式 index.html に preview_min_sec 対応パッチを適用する。"""
    if not os.path.isfile(index_path):
        return

    with open(index_path, encoding="utf-8") as f:
        html = f.read()

    original = html

    if (
        "const autoPlayRequested = requestedAutoMode !== \"\" || searchParams.get(\"autoplay\") === \"1\";" in html
        and "const previewMinSceneSec" not in html
    ):
        html = html.replace(
            '    const autoPlayRequested = requestedAutoMode !== "" || searchParams.get("autoplay") === "1";',
            '    const autoPlayRequested = requestedAutoMode !== "" || searchParams.get("autoplay") === "1";\n'
            '    const previewMinSceneSec = requestedAutoMode\n'
            '      ? Math.max(0, Number.parseFloat(searchParams.get("preview_min_sec") || "0") || 0)\n'
            '      : 0;',
        )

    if "function getSceneDurationSec(scene) {\n      return audioMode === \"long\" ? (scene.long_duration_sec || 0) : (scene.short_duration_sec || 0);\n    }" in html:
        html = html.replace(
            '    function getSceneDurationSec(scene) {\n'
            '      return audioMode === "long" ? (scene.long_duration_sec || 0) : (scene.short_duration_sec || 0);\n'
            '    }',
            '    function getSceneDurationSec(scene) {\n'
            '      const raw = audioMode === "long" ? (scene.long_duration_sec || 0) : (scene.short_duration_sec || 0);\n'
            '      return raw || previewMinSceneSec;\n'
            '    }',
        )

    if "_shortStartSecs.push(sa); sa += (sc.short_duration_sec || 0);" in html:
        html = html.replace(
            "_shortStartSecs.push(sa); sa += (sc.short_duration_sec || 0);",
            "_shortStartSecs.push(sa); sa += (sc.short_duration_sec || previewMinSceneSec || 0);",
        )
    if "_longStartSecs.push(la);  la += (sc.long_duration_sec  || 0);" in html:
        html = html.replace(
            "_longStartSecs.push(la);  la += (sc.long_duration_sec  || 0);",
            "_longStartSecs.push(la);  la += (sc.long_duration_sec  || previewMinSceneSec || 0);",
        )

    if "function getTotalDurationSec() {\n      return audioMode === \"long\" ? (scenario.long_duration_sec || 1) : (scenario.short_duration_sec || 1);\n    }" in html:
        html = html.replace(
            '    function getTotalDurationSec() {\n'
            '      return audioMode === "long" ? (scenario.long_duration_sec || 1) : (scenario.short_duration_sec || 1);\n'
            '    }',
            '    function getTotalDurationSec() {\n'
            '      const raw = audioMode === "long" ? (scenario.long_duration_sec || 0) : (scenario.short_duration_sec || 0);\n'
            '      if (raw > 0) return raw;\n'
            '      const fallbackTotal = (scenario.scenes || []).reduce((sum, scene) => sum + getSceneDurationSec(scene), 0);\n'
            '      return fallbackTotal || 1;\n'
            '    }',
        )

    if html != original:
        with open(index_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        print(f"  [browser] preview_min_sec={PREVIEW_MIN_SCENE_SEC:g} を index.html に反映しました")


def ensure_preview_minimum_duration_duo(index_path: str) -> None:
    """duo-v2 形式 index.html に preview_min_sec 対応パッチを適用する。"""
    if not os.path.isfile(index_path):
        return

    with open(index_path, encoding="utf-8") as f:
        html = f.read()

    original = html

    if 'const _loopPlay = _qp.get("auto") === "loop";' in html and "const _previewMinSceneSec" not in html:
        html = html.replace(
            '    const _loopPlay = _qp.get("auto") === "loop";',
            '    const _loopPlay = _qp.get("auto") === "loop";\n'
            '    const _previewMinSceneSec = _loopPlay\n'
            '      ? Math.max(0, Number.parseFloat(_qp.get("preview_min_sec") || "0") || 0)\n'
            '      : 0;',
        )

    if "function beginTurnPlayback() {\n      const turn  = currentTurn();\n      if (!turn) return;\n      const token = ++playbackToken;" in html:
        html = html.replace(
            '    function beginTurnPlayback() {\n'
            '      const turn  = currentTurn();\n'
            '      if (!turn) return;\n'
            '      const token = ++playbackToken;',
            '    function beginTurnPlayback() {\n'
            '      const turn  = currentTurn();\n'
            '      if (!turn) {\n'
            '        const token = ++playbackToken;\n'
            '        clearTimers();\n'
            '        turnStartedAt = Date.now();\n'
            '        tickTimer = setInterval(() => {\n'
            '          if (token !== playbackToken || !playing) return;\n'
            '          turnElapsedMs = Date.now() - turnStartedAt;\n'
            '          updateTimerAndProgress();\n'
            '        }, 100);\n'
            '        armTurnEndTimer((_previewMinSceneSec || 5) * 1000, token);\n'
            '        return;\n'
            '      }\n'
            '      const token = ++playbackToken;',
        )

    if "let effectiveDuration = turn.duration_sec || 5;" in html:
        html = html.replace(
            "let effectiveDuration = turn.duration_sec || 5;",
            "let effectiveDuration = turn.duration_sec || _previewMinSceneSec || 5;",
        )

    if html != original:
        with open(index_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        print(f"  [browser] preview_min_sec={PREVIEW_MIN_SCENE_SEC:g} を index.html に反映しました")


async def refresh_browser_preview(
    ctx: "VideoGenCtx",
    step_label: str,
    *,
    ensure_fn=None,
    require_existing_index: bool = True,
    speaker_enabled: bool = True,
) -> None:
    """
    aidiy_chrome_devtools HTTP API で、生成中ビデオを ?auto=loop 表示する。

    Parameters
    ----------
    ctx : VideoGenCtx
    step_label : str
    ensure_fn : callable or None
        index.html にパッチを当てる関数
    require_existing_index : bool
    speaker_enabled : bool
        False の場合は ?speaker=false を付けてプレビュー音声を無効化する
    """
    if not ctx.browser_preview:
        return
    index_path = os.path.join(ctx.output_dir, "index.html")
    if require_existing_index and not os.path.isfile(index_path):
        print(f"  [browser] index.html 未作成のため再描写をスキップ: {index_path}")
        return

    if ensure_fn is not None:
        ensure_fn(index_path)
    url = _preview_url(ctx.frontend_base_url, ctx.folder_name, speaker_enabled=speaker_enabled)
    try:
        result = await asyncio.to_thread(
            post_mcp_method,
            ctx.chrome_api_url,
            "navigate",
            {"url": url, "show_automation_banner": False},
            90,
        )
        print(f"  [browser] {step_label}: {result}")
    except Exception as e:
        print(f"  [browser] 再描写をスキップしました: {e}")


# ================================================================== #
# CodeAgents ユーティリティ (agent_utils)
# ================================================================== #

def step_instruction_header(ctx: "VideoGenCtx", step_name: str, step_summary: str) -> str:
    """CodeAgents への各作業指示に付ける共通ヘッダー。"""
    return (
        "以下は AiDiy の自動ビデオ生成ワークフローの 1 ステップです。\n\n"
        "【今やっていること】\n"
        f"  {step_name} を実行しています。\n\n"
        "【出力言語】\n"
        f"  language={ctx.language}\n"
        "  scenario.js、index.html、字幕、ナレーション原稿、音声合成にはこの言語設定を反映してください。\n\n"
        "【今回のステップ内容】\n"
        f"{step_summary}\n\n"
        "【既存成果物の扱い】\n"
        "  対象ファイルやフォルダが既にある場合は、存在だけで完了扱いにせず、内容を検証してください。\n"
        "  今回のフォルダ名・テーマ・scenario.js と整合しない、必須項目が足りない、破損している、\n"
        "  テンプレート元の文言が残っている、生成途中の空ファイルがある場合は修正してください。\n"
        "  問題がない場合は不要な上書きや再生成をせず、確認結果を表示してください。\n\n"
    )


async def agent_run(
    ctx: "VideoGenCtx",
    ca: dict,
    prompt: str,
    timeout_sec: int = 300,
) -> str:
    """aidiy_code_agents HTTP API に作業指示を投げる共通ラッパー。"""
    api_url = ca.get("api_url", ctx.code_agents_api_url)
    payload = {
        "prompt": prompt,
        "project_path": ctx.repo_dir,
        "ai_name": "auto",
        "ai_model": "auto",
        "max_turns": 15,
        "code_plan": "off",
        "code_verify": "off",
        "code_permissions": "full",
        "resume": False,
        "timeout_sec": timeout_sec,
    }
    result = await asyncio.to_thread(
        post_mcp_method,
        api_url,
        "run",
        payload,
        max(timeout_sec + 60, 180),
    )
    status = result.get("status", "NG")
    text = result.get("result", "（応答なし）")
    used_ai = result.get("ai_name", "auto")
    print(f"  [agent] ai={used_ai} status={status}  result_length={len(text)}")
    if status == "NG":
        _logger.error("agent_run NG: ai=%s result=%s", used_ai, text[:300])
    else:
        _logger.info("agent_run OK: ai=%s result_len=%d", used_ai, len(text))
    return text


async def _agent_verify_step(
    ctx: "VideoGenCtx",
    ca: dict,
    step_name: str,
    step_summary: str,
    target_paths: list,
    timeout_sec: int = 300,
) -> None:
    """作業後に CodeAgents へ検証専用の確認を依頼する。"""
    target_list = "\n".join(f"  - {path}" for path in target_paths)
    prompt = (
        step_instruction_header(ctx, step_name, step_summary)
        + "以下の対象を検証してください。\n\n"
        "【検証対象】\n"
        f"{target_list}\n\n"
        "【検証・修正方針】\n"
        "  1. 今回のステップで作られるべき成果物が存在するか確認してください。\n"
        "  2. 既に存在する場合も内容を読み、今回のフォルダ名・テーマと合っているか確認してください。\n"
        "  3. 問題があればこの場で修正してください。\n"
        "  4. 問題がなければ変更せず、OK と判断した根拠を短く表示してください。\n"
        "  5. 最後に、修正したファイルと未修正で OK としたファイルを一覧表示してください。\n"
    )
    await agent_run(ctx, ca, prompt, timeout_sec=timeout_sec)


# ================================================================== #
# 検証・バックアップ安定化 (verify_utils)
# ================================================================== #

async def verify_and_backup_until_stable(
    ctx: "VideoGenCtx",
    ca: dict,
    step_name: str,
    step_summary: str,
    target_paths: list,
    validate: Callable[[], bool],
    verify_timeout_sec: int = 300,
    attempt: int = 1,
    *,
    backup_url: str | None = None,
) -> bool:
    """backup_url は互換性のために残す。省略時は ctx.backup_api_url を使う。"""
    """
    CodeAgents 作業後の安定化処理。

    1. 検証専用の CodeAgents 実行で内容を確認・必要なら修正する。
    2. Python 側の機械的チェックを通す。
    3. POST /aidiy_backup/save/scan で差分を確認する。
    4. 差分があれば POST /aidiy_backup/save/run で差分バックアップを保存する。
    5. バックアップ保存後はもう一度検証へ戻り、差分がゼロになるまで続ける。
    """
    def _tts(msg: str, *, voice: str = "female") -> None:
        guide_tts(ctx, msg, voice=voice)

    label = ctx.progress_label_fn(step_name) if ctx.progress_label_fn else step_name

    for round_no in range(1, ctx.max_backup_stabilize + 1):
        print(f"  [verify] {step_name} 検証ラウンド {round_no}/{ctx.max_backup_stabilize}")
        if ctx.use_english_voice:
            _tts(f"{label} verification is starting. Attempt {attempt}.")
        else:
            _tts(f"{step_name} の検証を開始します。試行 {attempt}回目です。")
        await _agent_verify_step(
            ctx, ca,
            step_name=step_name,
            step_summary=step_summary,
            target_paths=target_paths,
            timeout_sec=verify_timeout_sec,
        )

        if not validate():
            print("  [verify] Python 側検証が NG です")
            if ctx.use_english_voice:
                _tts(f"{label} verification found an issue. Retrying the same step.", voice="male")
            else:
                _tts(f"{step_name} の検証で問題が見つかりました。同じステップをやり直します。", voice="male")
            return False

        diff_count = backup_diff_count(ctx)
        if diff_count == 0:
            print("  [backup] 差分なし。次のステップへ進みます")
            if ctx.use_english_voice:
                _tts(f"{label} has no remaining differences. Moving to the next step.")
            else:
                _tts(f"{step_name} の差分はありません。次のステップへ進みます。")
            return True

        print("  [backup] 差分あり。POST /aidiy_backup/save/run で保存して同ステップを再確認します")
        if ctx.use_english_voice:
            _tts(f"{label} has {diff_count} changed files. Saving a backup and checking again.", voice="male")
        else:
            _tts(f"{step_name} で差分が {diff_count} 件あります。差分バックアップを保存して、もう一度確認します。", voice="male")
        if not backup_save_once(ctx):
            if ctx.use_english_voice:
                _tts(f"{label} failed to save the backup.", voice="male")
            else:
                _tts(f"{step_name} の差分バックアップに失敗しました。", voice="male")
            return False

        after_count = backup_diff_count(ctx)
        if after_count != 0:
            print("  [backup] バックアップ後も差分が残っています。同ステップを継続します")
            if ctx.use_english_voice:
                _tts(f"{after_count} changed files remain after the backup. Continuing the same step.", voice="male")
            else:
                _tts(f"バックアップ後も差分が {after_count} 件残っています。同じステップを継続します。", voice="male")

    print(f"  [backup] 差分ゼロ確認が {ctx.max_backup_stabilize} 回以内に完了しませんでした")
    if ctx.use_english_voice:
        _tts(f"{label} could not reach a clean backup state. Please check the process.", voice="male")
    else:
        _tts(f"{step_name} の差分ゼロ確認が完了しませんでした。処理を確認してください。", voice="male")
    return False


# ================================================================== #
# VideoGenCtx 構築 (config.build_ctx を含む)
# ================================================================== #

def build_ctx(
    argv: list,
    *,
    script_type: str,
    setting_json_path: str,
    setting_json_name: str,
    steps_json_path: str,
    steps_json_name: str,
    steps_keys: tuple,
    valid_steps: set | None = None,
    mcp_dir: str = "",
    repo_dir: str = "",
    progress_tts_language: str = "ja",
    progress_tts_provider: str = "edge",
    use_english_voice: bool = False,
    progress_label_fn=None,
) -> "VideoGenCtx":
    """設定 JSON と CLI 引数から VideoGenCtx を構築する。"""
    from .ctx import VideoGenCtx

    if valid_steps is None:
        valid_steps = {0, 1, 2, 3, 4, 5, 6, 7, 8, 99}

    setting = load_setting_json(setting_json_path, setting_json_name)
    sn = setting_json_name

    s_shared = require_mapping(setting, "shared", sn)

    if len(argv) > 2:
        print("ERROR: 引数は実行ステップ番号を 1 つだけ指定できます（00、01〜08、99）")
        sys.exit(1)

    step_specified = len(argv) == 2
    if step_specified:
        try:
            start_step = int(argv[1])
        except ValueError:
            print(f"ERROR: 実行ステップは整数で指定してください（指定値: {argv[1]}）")
            sys.exit(1)
        if start_step not in valid_steps:
            print(f"ERROR: 実行ステップは 00、01〜08、99 で指定してください（指定値: {start_step}）")
            sys.exit(1)
    else:
        data = ensure_steps_json(steps_json_path, steps_json_name, steps_keys)
        completed = str(data.get(STEPS_JSON_KEY, "") or "")
        start_step = next_step_after(completed)
    stop_step = start_step

    folder_name = require_string(setting, "folder_name", sn)
    raw_topic = setting.get("topic")
    if isinstance(raw_topic, list):
        topic = " ".join(str(s).strip() for s in raw_topic if str(s).strip())
    elif isinstance(raw_topic, str) and raw_topic.strip():
        topic = raw_topic.strip()
    else:
        raise RuntimeError(f"{sn} に topic が必要です")
    if not topic:
        raise RuntimeError(f"{sn} の topic が空です")

    template_dir = require_string(setting, "template_dir", sn)

    mcp_python = os.path.join(mcp_dir, ".venv", "Scripts", "python.exe") if mcp_dir else ""
    if not mcp_python or not os.path.isfile(mcp_python):
        mcp_python = sys.executable

    ctx = VideoGenCtx(
        folder_name=folder_name,
        topic=topic,
        template_dir=template_dir,
        video_base_dir=require_string(s_shared, "video_base_dir", sn),
        backup_api_url=require_string(s_shared, "backup_api_url", sn),
        tts_api_url=require_string(s_shared, "tts_api_url", sn),
        image_gen_api_url=require_string(s_shared, "image_gen_api_url", sn),
        code_agents_api_url=require_string(s_shared, "code_agents_api_url", sn),
        chrome_api_url=require_string(s_shared, "chrome_api_url", sn),
        ffmpeg_api_url=require_string(s_shared, "ffmpeg_api_url", sn),
        language=require_string(setting, "language", sn),
        tts_guide=require_bool(s_shared, "tts_guide", sn),
        frontend_base_url=require_string(s_shared, "frontend_base_url", sn),
        browser_preview=require_bool(s_shared, "browser_preview", sn),
        chrome_debug_port=require_int(s_shared, "chrome_debug_port", sn),
        max_retries=require_int(s_shared, "max_retries", sn),
        retry_wait_sec=require_int(s_shared, "retry_wait_sec", sn),
        max_backup_stabilize=require_int(s_shared, "max_backup_stabilize", sn),
        start_step=start_step,
        stop_step=stop_step,
        step_specified=step_specified,
        script_type=script_type,
        steps_json_path=steps_json_path,
        steps_json_name=steps_json_name,
        setting_json_name=setting_json_name,
        fix_mode=os.path.normpath(template_dir) == os.path.normpath(
            os.path.join(require_string(s_shared, "video_base_dir", sn), folder_name)
        ),
        mcp_python=mcp_python,
        repo_dir=repo_dir,
        progress_tts_language=progress_tts_language,
        progress_tts_provider=progress_tts_provider,
        use_english_voice=use_english_voice,
        progress_label_fn=progress_label_fn,
    )
    return ctx
