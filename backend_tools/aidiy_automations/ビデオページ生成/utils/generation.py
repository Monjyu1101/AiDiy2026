# -*- coding: utf-8 -*-
"""
generation.py — コンテンツ生成系統合モジュール

以下を統合:
  script_gen, scenario_utils, duration_utils, markdown_utils, fix_mode_utils
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ctx import VideoGenCtx

from .infra import post_mcp_method, check


# ================================================================== #
# シナリオ読み書き・検証 (scenario_utils)
# ================================================================== #

def load_scenario_object(path: str) -> dict:
    """window.SCENARIO = {...}; 形式の scenario.js を dict として読む。"""
    with open(path, encoding="utf-8-sig") as f:
        content = f.read()

    json_str = content.strip()
    if json_str.startswith("window.SCENARIO ="):
        json_str = json_str[len("window.SCENARIO ="):].strip()
    json_str = json_str.rstrip(";").strip()
    data = json.loads(json_str)
    if not isinstance(data, dict):
        raise RuntimeError(f"scenario.js の内容が object ではありません: {path}")
    return data


def save_scenario_object(path: str, data: dict) -> None:
    """scenario.js を window.SCENARIO 形式で保存する。"""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("window.SCENARIO = ")
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write(";\n")


def count_scenario_scenes(path: str) -> int:
    """scenario.js に含まれる scene 件数を返す。"""
    data = load_scenario_object(path)
    scenes = data.get("scenes", [])
    if not isinstance(scenes, list):
        return 0
    return sum(1 for scene in scenes if isinstance(scene, dict))


def count_scenario_dialogues(path: str) -> int:
    """scenario.js に含まれる音声ファイルの期待件数を返す（汎用設計）。"""
    data = load_scenario_object(path)
    count = 0
    for scene in data.get("scenes", []):
        dialogues = scene.get("dialogue", [])
        if isinstance(dialogues, list) and len(dialogues) > 0:
            count += sum(1 for dlg in dialogues if isinstance(dlg, dict))
        else:
            if str(scene.get("short_narration", "") or "").strip():
                count += 1
            if str(scene.get("long_narration", "") or "").strip():
                count += 1
    return count


def validate_scene_id_range(
    path: str,
    *,
    min_mid: int,
    max_mid: int,
    label: str,
) -> bool:
    """scene_000、scene_001..min_mid、任意で max_mid まで、scene_999 の構成を検証する。"""
    try:
        data = load_scenario_object(path)
    except Exception as e:
        print(f"  [scenario] {label} scene ID 検証をスキップ: {e}")
        return False
    scenes = data.get("scenes", [])
    if not isinstance(scenes, list):
        return check(f"{label} scenes 配列", False)
    ids = [str(scene.get("id", "")) for scene in scenes if isinstance(scene, dict)]
    expected_min_count = 1 + min_mid + 1
    expected_max_count = 1 + max_mid + 1
    ok_count = check(
        f"{label} scenes 件数: {len(ids)} 件（期待 {expected_min_count}〜{expected_max_count} 件）",
        expected_min_count <= len(ids) <= expected_max_count,
    )
    ok_edges = check(
        f"{label} scene_000 先頭 / scene_999 最後",
        bool(ids) and ids[0] == "scene_000" and ids[-1] == "scene_999",
    )
    required = [f"scene_{i:03d}" for i in range(1, min_mid + 1)]
    missing = [sid for sid in required if sid not in ids]
    ok_required = check(f"{label} 必須 scene_001〜scene_{min_mid:03d}", not missing)
    allowed = {"scene_000", "scene_999"} | {f"scene_{i:03d}" for i in range(1, max_mid + 1)}
    unexpected = [sid for sid in ids if sid not in allowed]
    ok_allowed = check(
        f"{label} 許可 scene 範囲 scene_000 / scene_001〜scene_{max_mid:03d} / scene_999",
        not unexpected,
    )
    return ok_count and ok_edges and ok_required and ok_allowed


def index_html_matches_theme(index_path: str, scenario_path: str, folder_name: str, topic: str) -> bool:
    """index.html が今回テーマ向けに更新済みかをざっくり判定する。"""
    if not os.path.isfile(index_path):
        return False

    with open(index_path, encoding="utf-8") as f:
        html = f.read()

    if "<title>" not in html or "scenario.js" not in html:
        return False

    markers = {folder_name.strip(), topic.strip()}
    if os.path.isfile(scenario_path):
        try:
            data = load_scenario_object(scenario_path)
            for key in ("title", "project_name"):
                value = str(data.get(key, "") or "").strip()
                if value:
                    markers.add(value)
        except Exception:
            pass

    return any(marker and marker in html for marker in markers)


def collect_scenario_duration_stats(path: str) -> dict:
    """scenario.js の再生時間欄が設定されているか確認する（汎用設計）。"""
    data = load_scenario_object(path)
    version = data.get("version", "mcp")

    audio_count = 0
    audio_ok = 0
    scene_count = 0
    scene_ok = 0
    total_short_sec = 0.0
    total_long_sec = 0.0
    total_duration_sec = 0.0
    total_from_scenes = 0.0

    for scene in data.get("scenes", []):
        scene_count += 1

        dialogues = scene.get("dialogue", [])
        if isinstance(dialogues, list) and len(dialogues) > 0:
            scene_sum = 0.0
            for dlg in dialogues:
                if not isinstance(dlg, dict):
                    continue
                audio_count += 1
                try:
                    dur = float(dlg.get("duration_sec", 0) or 0)
                except (TypeError, ValueError):
                    dur = 0.0
                if dur > 0:
                    audio_ok += 1
                scene_sum += dur

            try:
                scene_dur = float(scene.get("duration_sec", 0) or 0)
            except (TypeError, ValueError):
                scene_dur = 0.0
            if scene_dur > 0 and abs(scene_dur - round(scene_sum, 3)) <= 0.01:
                scene_ok += 1
            total_duration_sec += scene_dur
            total_from_scenes += scene_dur
        else:
            short_ok = False
            long_ok = False
            for kind in ("short", "long"):
                a_key = f"{kind}_audio"
                d_key = f"{kind}_duration_sec"
                if a_key in scene:
                    audio_count += 1
                    try:
                        dur = float(scene.get(d_key, 0) or 0)
                    except (TypeError, ValueError):
                        dur = 0.0
                    if dur > 0:
                        audio_ok += 1
                        if kind == "short":
                            short_ok = True
                            total_short_sec += dur
                        else:
                            long_ok = True
                            total_long_sec += dur
            if short_ok and long_ok:
                scene_ok += 1

    if version == "duo-v2" or "total_duration_sec" in data:
        try:
            total_duration_sec = float(data.get("total_duration_sec", 0) or 0)
        except (TypeError, ValueError):
            total_duration_sec = 0.0
        total_long_sec = total_duration_sec
        total_short_sec = 1.0

    return {
        "audio_count": audio_count,
        "audio_ok": audio_ok,
        "scene_count": scene_count,
        "scene_ok": scene_ok,
        "total_short_duration_sec": round(total_short_sec, 3),
        "total_long_duration_sec": round(total_long_sec, 3),
        "total_duration_sec": round(total_duration_sec, 3),
        "total_from_scenes": round(total_from_scenes, 3),
        "dialogue_count": audio_count,
        "dialogue_ok": audio_ok,
    }


# ================================================================== #
# 音声再生時間更新 (duration_utils)
# ================================================================== #

async def probe_media_duration_sec(ctx: "VideoGenCtx", media_path: str) -> float:
    """aidiy_ffmpeg_control HTTP API でメディア再生時間を取得する。"""
    result = await asyncio.to_thread(
        post_mcp_method,
        ctx.ffmpeg_api_url,
        "media_duration",
        {"input_path": media_path, "timeout_sec": 60},
        120,
    )
    raw = result.get("duration_sec")
    try:
        return round(float(raw), 3)
    except (TypeError, ValueError) as e:
        raise RuntimeError(f"ffmpeg API の duration_sec を数値化できません: {repr(raw)}") from e


async def update_scenario_audio_durations(
    ctx: "VideoGenCtx",
    scenario_path: str,
    new_dir: str,
) -> dict:
    """音声ファイルの実再生時間で scenario.js の duration_sec 群を更新する（汎用設計）。"""
    data = load_scenario_object(scenario_path)
    updated_audio = 0
    updated_scenes = 0
    total_duration_sec = 0.0
    total_short_sec = 0.0
    total_long_sec = 0.0

    version = data.get("version", "mcp")

    for scene in data.get("scenes", []):
        scene_id = str(scene.get("id", "") or "")
        scene_num = scene_id.replace("scene_", "")
        scene_sum = 0.0

        for prefix in ("short", "long"):
            a_key = f"{prefix}_audio"
            d_key = f"{prefix}_duration_sec"
            if a_key in scene:
                audio_ref = str(scene[a_key] or "").strip()
                if not audio_ref:
                    audio_ref = f"audio/{prefix}_scene_{scene_num}.mp3"
                    scene[a_key] = audio_ref

                audio_path = audio_ref.replace("/", os.sep)
                if not os.path.isabs(audio_path):
                    audio_path = os.path.join(new_dir, audio_path)
                audio_path = os.path.abspath(audio_path)
                if not os.path.isfile(audio_path):
                    raise RuntimeError(f"音声ファイルが見つかりません: {audio_path}")

                duration_sec = await probe_media_duration_sec(ctx, audio_path)
                scene[d_key] = duration_sec
                scene_sum += duration_sec
                if prefix == "short":
                    total_short_sec += duration_sec
                else:
                    total_long_sec += duration_sec
                updated_audio += 1

        dialogues = scene.get("dialogue", [])
        if isinstance(dialogues, list):
            dialogue_sum = 0.0
            for turn, dlg in enumerate(dialogues, start=1):
                if not isinstance(dlg, dict):
                    continue
                audio_ref = str(dlg.get("audio", "") or "").strip()
                speaker = str(dlg.get("speaker", "female") or "female")
                if not audio_ref:
                    audio_ref = f"audio/dlg_{scene_num}_{turn:02d}_{speaker}.mp3"
                    dlg["audio"] = audio_ref

                audio_path = audio_ref.replace("/", os.sep)
                if not os.path.isabs(audio_path):
                    audio_path = os.path.join(new_dir, audio_path)
                audio_path = os.path.abspath(audio_path)
                if not os.path.isfile(audio_path):
                    raise RuntimeError(f"音声ファイルが見つかりません: {audio_path}")

                duration_sec = await probe_media_duration_sec(ctx, audio_path)
                dlg["duration_sec"] = duration_sec
                dialogue_sum += duration_sec
                updated_audio += 1

            if dialogue_sum > 0 or len(dialogues) > 0:
                scene["duration_sec"] = round(dialogue_sum, 3)
                total_duration_sec += dialogue_sum
                updated_scenes += 1
            else:
                total_duration_sec += scene_sum
                updated_scenes += 1
        else:
            total_duration_sec += scene_sum
            updated_scenes += 1

    if version == "duo-v2" or "total_duration_sec" in data:
        data["total_duration_sec"] = round(total_duration_sec, 3)
        total_long_sec = total_duration_sec
    else:
        data["total_short_duration_sec"] = round(total_short_sec, 3)
        data["total_long_duration_sec"] = round(total_long_sec, 3)

    save_scenario_object(scenario_path, data)
    return {
        "audio_count": updated_audio,
        "scene_count": updated_scenes,
        "total_short_duration_sec": round(total_short_sec, 3),
        "total_long_duration_sec": round(total_long_sec, 3),
        "total_duration_sec": round(total_duration_sec, 3),
        "dialogue_count": updated_audio,
    }


# ================================================================== #
# 進捗 Markdown (markdown_utils)
# ================================================================== #

def ensure_step_markdown(md_path: str, folder_name: str, topic: str) -> None:
    """進捗 Markdown が無ければ Step 01 と同じ形式で再生成する。"""
    if os.path.isfile(md_path):
        return

    md_content = (
        f"# {folder_name}\n"
        f"テーマ: {topic}\n\n"
        "## 進捗\n"
        "- [x] フォルダ作成\n"
        "- [ ] シナリオ作成\n"
        "- [ ] HTML修正\n"
        "- [ ] 画像生成\n"
        "- [ ] 中間確認\n"
        "- [ ] 音声生成\n"
        "- [ ] 再生時間更新\n"
        "- [ ] 完成\n"
    )
    with open(md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(md_content)


def mark_step_done(md_path: str, step_label: str) -> None:
    """進捗 Markdown の対象行を [x] に更新する。"""
    if not os.path.isfile(md_path):
        print(f"  [md] 進捗ファイルが無いため更新をスキップ: {md_path}")
        return

    with open(md_path, encoding="utf-8") as f:
        content = f.read()

    if f"- [ ] {step_label}" in content:
        updated = content.replace(f"- [ ] {step_label}", f"- [x] {step_label}", 1)
    elif f"- [x] {step_label}" in content:
        return
    else:
        if "- [ ] 完成" in content:
            updated = content.replace("- [ ] 完成", f"- [x] {step_label}\n- [ ] 完成", 1)
        elif "- [x] 完成" in content:
            updated = content.replace("- [x] 完成", f"- [x] {step_label}\n- [x] 完成", 1)
        else:
            updated = content.rstrip() + f"\n- [x] {step_label}\n"

    with open(md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(updated)


# ================================================================== #
# fix mode 画像退避 (fix_mode_utils)
# ================================================================== #

def backup_images_for_fix_mode(ctx: "VideoGenCtx", images_dir: str) -> str:
    """fix_mode 時に既存画像を .orig/ へ退避し、退避先パスを返す。"""
    if not os.path.isdir(images_dir):
        return ""
    orig_images_dir = os.path.join(images_dir, ".orig")
    os.makedirs(orig_images_dir, exist_ok=True)
    for fname in os.listdir(images_dir):
        if fname.endswith(".png"):
            src = os.path.join(images_dir, fname)
            if os.path.getsize(src) > 1000:
                shutil.copy2(src, os.path.join(orig_images_dir, fname))
                os.remove(src)
    print(f"  [fix] 既存画像を退避しました: {orig_images_dir}")
    return orig_images_dir


# ================================================================== #
# 補助スクリプト生成 (script_gen)
# ================================================================== #

def render_scene_image_script(
    ctx: "VideoGenCtx",
    output_dir: str,
    template_image_dir: str,
    build_prompt_fn: str,
    language: str = "",
    extra_imports: str = "",
    extra_constants: str = "",
) -> str:
    """Step 04 用の _gen_scene_images.py 本文を返す。

    Parameters
    ----------
    ctx : VideoGenCtx
    output_dir : str
        images フォルダのパス
    template_image_dir : str
    build_prompt_fn : str
        build_prompt(scene) 関数の本体（インデント付き文字列）
    language : str
        出力言語コード（翻訳スクリプト用）
    extra_imports : str
        追加 import 文
    extra_constants : str
        build_prompt より前に置く定数定義
    """
    lang_line = f"LANGUAGE = {language!r}\n" if language else ""
    return (
        "# -*- coding: utf-8 -*-\n"
        '"""\n'
        "シーン画像生成スクリプト\n\n"
        "scenario.js の各 scene から images/scene_*.png を生成します。\n"
        "既存の画像ファイル（1000 bytes 超）は自動スキップします。\n"
        '"""\n\n'
        "import json\n"
        "import os\n"
        "import sys\n"
        "import time\n"
        "import urllib.error\n"
        "import urllib.request\n"
        + (extra_imports + "\n" if extra_imports else "")
        + "\n"
        "if sys.platform == 'win32':\n"
        "    sys.stdout.reconfigure(encoding='utf-8', errors='replace')\n"
        "    sys.stderr.reconfigure(encoding='utf-8', errors='replace')\n\n"
        f"OUTPUT_DIR = {output_dir!r}\n"
        f"TEMPLATE_IMAGE_DIR = {template_image_dir!r}\n"
        f"IMAGE_GEN_API_URL = {ctx.image_gen_api_url!r}\n"
        + lang_line
        + "os.makedirs(OUTPUT_DIR, exist_ok=True)\n\n\n"
        "def _clean_text(value):\n"
        '    return " ".join(str(value or "").replace("\\\\n", " ").replace("\\n", " ").split()).strip()\n\n\n'
        "def load_scenes():\n"
        '    scenario_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenario.js")\n'
        '    with open(scenario_file, encoding="utf-8-sig") as f:\n'
        "        content = f.read()\n\n"
        "    json_str = content.strip()\n"
        '    if json_str.startswith("window.SCENARIO ="):\n'
        '        json_str = json_str[len("window.SCENARIO ="):].strip()\n'
        '    json_str = json_str.rstrip(";").strip()\n\n'
        "    data = json.loads(json_str)\n"
        '    scenes = data.get("scenes", [])\n'
        "    return scenes if isinstance(scenes, list) else []\n\n\n"
        + (extra_constants + "\n\n" if extra_constants else "")
        + build_prompt_fn
        + "\n\n\n"
        "def get_template_image(num_str):\n"
        '    """テンプレート元画像のパスを返す。存在しない場合は None。"""\n'
        "    if not TEMPLATE_IMAGE_DIR:\n"
        "        return None\n"
        '    path = os.path.join(TEMPLATE_IMAGE_DIR, f"scene_{num_str}.png")\n'
        "    if os.path.isfile(path) and os.path.getsize(path) > 1000:\n"
        "        return path\n"
        "    return None\n\n\n"
        "def post_json(url, payload, timeout_sec=600):\n"
        "    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')\n"
        "    req = urllib.request.Request(\n"
        "        url,\n"
        "        data=data,\n"
        '        headers={"Content-Type": "application/json"},\n'
        '        method="POST",\n'
        "    )\n"
        "    try:\n"
        "        with urllib.request.urlopen(req, timeout=timeout_sec) as res:\n"
        '            raw = res.read().decode("utf-8", errors="replace")\n'
        "    except urllib.error.URLError as e:\n"
        '        raise RuntimeError(f"HTTP API に接続できません: {url} ({e})") from e\n'
        "    result = json.loads(raw)\n"
        "    if isinstance(result, dict) and result.get('error'):\n"
        "        raise RuntimeError(result['error'])\n"
        "    return result\n\n\n"
        "def generate_one(prompt, out_path, original_path=None):\n"
        "    payload = {\n"
        '        "prompt": prompt,\n'
        '        "provider": "auto",\n'
        '        "model": "auto",\n'
        '        "size": "auto",\n'
        '        "quality": "auto",\n'
        '        "save_path": out_path,\n'
        "    }\n"
        "    if original_path:\n"
        '        payload["original_path"] = original_path\n'
        "    result = post_json(IMAGE_GEN_API_URL, payload)\n"
        "    return {\n"
        '        "provider": result.get("provider", "auto"),\n'
        '        "model": result.get("model", "auto"),\n'
        '        "save_path": result.get("save_path", out_path),\n'
        "    }\n\n\n"
        "def main():\n"
        "    scenes = load_scenes()\n"
        "    total = len(scenes)\n"
        "    done = 0\n"
        "    skip = 0\n"
        "    fail = 0\n\n"
        "    for i, scene in enumerate(scenes):\n"
        "        if not isinstance(scene, dict):\n"
        "            continue\n"
        '        scene_id = str(scene.get("id", f"scene_{i:03d}") or f"scene_{i:03d}")\n'
        '        num_str = scene_id.replace("scene_", "")\n'
        '        out_path = os.path.join(OUTPUT_DIR, f"scene_{num_str}.png")\n\n'
        "        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:\n"
        '            print(f"  [SKIP] {os.path.basename(out_path)}")\n'
        "            skip += 1\n"
        "            continue\n\n"
        "        prompt = build_prompt(scene)\n"
        "        original_path = get_template_image(num_str)\n"
        '        title = _clean_text(scene.get("title", scene_id))\n'
        '        ref_label = f" (ref: {os.path.basename(original_path)})" if original_path else ""\n'
        '        print(f"  [GEN ] {os.path.basename(out_path)} : {title}{ref_label}")\n'
        "        try:\n"
        "            info = generate_one(prompt, out_path, original_path=original_path)\n"
        "            size = os.path.getsize(out_path) if os.path.exists(out_path) else 0\n"
        "            if size > 1000:\n"
        "                print(\n"
        "                    f\"         -> OK ({size:,} bytes) \"\n"
        "                    f\"[{info.get('provider', '?')}/{info.get('model', '?')}]\"\n"
        "                )\n"
        "                done += 1\n"
        "            else:\n"
        '                print("         -> FAIL (empty or too small)")\n'
        "                fail += 1\n"
        "        except Exception as e:\n"
        '            print(f"         -> ERROR: {e}")\n'
        "            fail += 1\n\n"
        "        time.sleep(1)\n\n"
        '    print(f"\\n完了: {done} 生成, {skip} スキップ, {fail} 失敗 (合計 {total} 件)")\n'
        "    if fail:\n"
        "        raise SystemExit(1)\n\n\n"
        'if __name__ == "__main__":\n'
        "    main()\n"
    )


def ensure_scene_image_script(
    ctx: "VideoGenCtx",
    gen_img_py: str,
    output_dir: str,
    template_image_dir: str,
    build_prompt_fn: str,
    language: str = "",
    extra_imports: str = "",
    extra_constants: str = "",
) -> None:
    """Step 04 用の補助スクリプトを再生成する。"""
    content = render_scene_image_script(
        ctx=ctx,
        output_dir=output_dir,
        template_image_dir=template_image_dir,
        build_prompt_fn=build_prompt_fn,
        language=language,
        extra_imports=extra_imports,
        extra_constants=extra_constants,
    )
    with open(gen_img_py, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def render_dialogue_audio_script(
    ctx: "VideoGenCtx",
    output_dir: str,
    load_tasks_body: str,
    synthesize_body: str,
    main_loop_body: str,
    script_docstring: str = "ナレーション音声生成スクリプト",
    extra_imports: str = "",
) -> str:
    """Step 06 用の _gen_audio.py 本文を返す。"""
    return (
        "# -*- coding: utf-8 -*-\n"
        f'"""\n{script_docstring}\n\n'
        "既存の音声ファイル（500 bytes 超）は自動スキップします。\n"
        '"""\n\n'
        "import json\n"
        "import os\n"
        "import sys\n"
        "import urllib.error\n"
        "import urllib.request\n"
        + (extra_imports + "\n" if extra_imports else "")
        + "\n"
        "if sys.platform == 'win32':\n"
        "    sys.stdout.reconfigure(encoding='utf-8', errors='replace')\n"
        "    sys.stderr.reconfigure(encoding='utf-8', errors='replace')\n\n"
        f"OUTPUT_DIR = {output_dir!r}\n"
        f"TTS_API_URL = {ctx.tts_api_url!r}\n"
        f"TTS_LANGUAGE = {ctx.language!r}\n"
        "os.makedirs(OUTPUT_DIR, exist_ok=True)\n\n\n"
        + load_tasks_body
        + "\n\n\n"
        "def post_json(url, payload, timeout_sec=300):\n"
        "    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')\n"
        "    req = urllib.request.Request(\n"
        "        url,\n"
        "        data=data,\n"
        '        headers={"Content-Type": "application/json"},\n'
        '        method="POST",\n'
        "    )\n"
        "    try:\n"
        "        with urllib.request.urlopen(req, timeout=timeout_sec) as res:\n"
        '            raw = res.read().decode("utf-8", errors="replace")\n'
        "    except urllib.error.URLError as e:\n"
        '        raise RuntimeError(f"HTTP API に接続できません: {url} ({e})") from e\n'
        "    result = json.loads(raw)\n"
        "    if isinstance(result, dict) and result.get('error'):\n"
        "        raise RuntimeError(result['error'])\n"
        "    return result\n\n\n"
        + synthesize_body
        + "\n\n\n"
        "def main():\n"
        + main_loop_body
        + "\n\n\n"
        'if __name__ == "__main__":\n'
        "    main()\n"
    )


def ensure_dialogue_audio_script(
    ctx: "VideoGenCtx",
    gen_aud_py: str,
    output_dir: str,
    load_tasks_body: str,
    synthesize_body: str,
    main_loop_body: str,
    script_docstring: str = "ナレーション音声生成スクリプト",
    extra_imports: str = "",
) -> None:
    """Step 06 用の補助スクリプトを再生成する。"""
    content = render_dialogue_audio_script(
        ctx=ctx,
        output_dir=output_dir,
        load_tasks_body=load_tasks_body,
        synthesize_body=synthesize_body,
        main_loop_body=main_loop_body,
        script_docstring=script_docstring,
        extra_imports=extra_imports,
    )
    with open(gen_aud_py, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
