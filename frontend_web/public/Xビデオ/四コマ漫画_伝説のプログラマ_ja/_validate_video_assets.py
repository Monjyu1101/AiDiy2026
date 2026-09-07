# -*- coding: utf-8 -*-
"""「四コマ漫画_伝説のプログラマ_ja」動画素材一式の最終検証。"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image


PROJECT_NAME = "四コマ漫画_伝説のプログラマ_ja"
EXPECTED_SCENE_IDS = [
    "scene_000",
    "scene_001",
    "scene_002",
    "scene_003",
    "scene_004",
    "scene_005",
    "scene_999",
]
CREDIT_SENTENCE = "この動画は AiDiy のビデオページ生成で作りました。"
BASE_DIR = Path(__file__).resolve().parent
SOURCE_PLAYER_PATH = BASE_DIR.parent / "小説解説_AiDiy誕生_ja" / "index.html"
SCENARIO_PATH = BASE_DIR / "scenario.js"
SCENARIO_JSON_PATH = BASE_DIR / "scenario.json"
INDEX_PATH = BASE_DIR / "index.html"
ASSETS_PATH = BASE_DIR / "assets.json"
AUDIO_GENERATOR_PATH = BASE_DIR / "_gen_audio.py"
IMAGE_GENERATOR_PATH = BASE_DIR / "_gen_scene_images.py"


def read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def load_json(path: Path) -> dict:
    data = json.loads(read_utf8(path))
    if not isinstance(data, dict):
        raise ValueError("ルートがオブジェクトではありません")
    return data


def load_scenario(content: str) -> dict:
    prefix = "window.SCENARIO ="
    stripped = content.lstrip()
    if not stripped.startswith(prefix):
        raise ValueError("window.SCENARIO 代入形式ではありません")
    data = json.loads(stripped[len(prefix) :].strip().removesuffix(";").strip())
    if not isinstance(data, dict):
        raise ValueError("シナリオのルートがオブジェクトではありません")
    return data


def png_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        if image.format != "PNG":
            raise ValueError("PNG 形式ではありません")
        size = image.size
        image.verify()
    with Image.open(path) as image:
        image.load()
    return size


def mp3_has_header(path: Path) -> bool:
    with path.open("rb") as stream:
        header = stream.read(10)
    return header.startswith(b"ID3") or (
        len(header) >= 2 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0
    )


def contains_japanese(value: object) -> bool:
    return bool(re.search(r"[\u3040-\u30ff\u3400-\u9fff]", str(value or "")))


def normalized_player_markup(content: str) -> str:
    """作品固有の表示文言だけを除外し、コピー元プレイヤーと比較する。"""
    normalized = content.replace("\r\n", "\n")
    patterns = (
        (r"<title>.*?</title>", "<title>__PROJECT__</title>"),
        (r'(<div class="brand">).*?(</div>)', r"\1__BRAND__\2"),
        (r'(<div class="top-note">).*?(</div>)', r"\1__TOP_NOTE__\2"),
        (
            r'(<iframe id="sceneFrame" class="scene-frame" title=").*?("></iframe>)',
            r"\1__FRAME_TITLE__\2",
        ),
    )
    for pattern, replacement in patterns:
        normalized = re.sub(pattern, replacement, normalized, count=1, flags=re.DOTALL)
    return normalized


def missing_local_references(path: Path) -> list[str]:
    content = read_utf8(path)
    missing: list[str] = []
    for reference in re.findall(r'''(?:src|href)=["']([^"'#?]+)''', content):
        if reference.startswith(("http:", "https:", "data:", "//")):
            continue
        if not (path.parent / reference).resolve().is_file():
            missing.append(f"{path.name}: {reference}")
    return missing


def probe_duration(ffprobe: str, path: Path) -> float:
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        duration = float(result.stdout.strip())
    except ValueError:
        duration = 0.0
    return duration if result.returncode == 0 else 0.0


def decodes_without_error(ffmpeg: str, path: Path) -> bool:
    result = subprocess.run(
        [ffmpeg, "-v", "error", "-i", str(path), "-f", "null", "NUL"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode == 0


def main() -> int:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    results: list[tuple[str, bool, str]] = []

    def check(label: str, condition: bool, detail: str) -> None:
        results.append((label, bool(condition), detail))

    scenario_content = read_utf8(SCENARIO_PATH) if SCENARIO_PATH.is_file() else ""
    check(
        "確認 1: scenario.js",
        SCENARIO_PATH.is_file()
        and "window.SCENARIO" in scenario_content
        and "scene_999" in scenario_content,
        "window.SCENARIO と scene_999 を確認",
    )

    scenario: dict = {}
    try:
        scenario = load_scenario(scenario_content)
        check("scenario.js JSON 構文", True, "正常に解析可能")
    except Exception as exc:
        check("scenario.js JSON 構文", False, str(exc))

    scenes = scenario.get("scenes", []) if isinstance(scenario.get("scenes"), list) else []
    scene_ids = [str(scene.get("id", "")) for scene in scenes if isinstance(scene, dict)]
    check(
        "シーン構成",
        scene_ids == EXPECTED_SCENE_IDS,
        f"{len(scene_ids)} シーン / 順序: {', '.join(scene_ids)}",
    )
    check(
        "プロジェクト名",
        scenario.get("project_name") == PROJECT_NAME and BASE_DIR.name == PROJECT_NAME,
        f"scenario={scenario.get('project_name')!r}, folder={BASE_DIR.name!r}",
    )

    required_fields = ("short_narration", "long_narration", "short_audio", "long_audio")
    incomplete_scenes = [
        str(scene.get("id", "(IDなし)"))
        for scene in scenes
        if not isinstance(scene, dict)
        or any(not str(scene.get(field, "")).strip() for field in required_fields)
    ]
    check(
        "確認 7: シーン必須項目",
        bool(scenes) and not incomplete_scenes,
        "全7シーンに4項目あり" if not incomplete_scenes else ", ".join(incomplete_scenes),
    )

    japanese_errors = [
        str(scene.get("id", "(IDなし)"))
        for scene in scenes
        if not contains_japanese(scene.get("short_narration"))
        or not contains_japanese(scene.get("long_narration"))
    ]
    target_language = str(scenario.get("target", {}).get("language", ""))
    check(
        "日本語設定・原稿",
        target_language in {"ja", "ja-JP"} and not japanese_errors,
        f"target.language={target_language!r}、全ナレーションが日本語",
    )

    forbidden_keys = {
        "content_type",
        "manga_title",
        "panel_count",
        "panel_layout",
        "panel_number",
        "page_number",
        "display_order",
        "speech_bubbles",
        "dialogue_text",
        "audio",
        "duration_sec",
        "hero_image_focus",
        "background_word",
    }
    dedicated_key_errors = [
        f"{scene.get('id', '(IDなし)')}: {', '.join(sorted(forbidden_keys & set(scene)))}"
        for scene in scenes
        if isinstance(scene, dict) and forbidden_keys & set(scene)
    ]
    check(
        "シーン項目構造",
        not dedicated_key_errors,
        "コピー元 mcp 構造を維持" if not dedicated_key_errors else "; ".join(dedicated_key_errors),
    )

    aidiy_pattern = re.compile(r"aidiy|ai\s*diy|アイディー", re.IGNORECASE)
    visible_fields = (
        "title",
        "kicker",
        "headline",
        "lead",
        "subtitle",
        "background_word",
        "chips",
        "metrics",
        "cards",
        "facts",
        "factual_bullets",
        "evidence",
    )
    credit_errors: list[str] = []
    for scene in scenes:
        scene_id = str(scene.get("id", ""))
        for field in visible_fields:
            if aidiy_pattern.search(json.dumps(scene.get(field, ""), ensure_ascii=False)):
                credit_errors.append(f"{scene_id}.{field}: 表示文言に AiDiy への言及あり")
        for field in ("short_narration", "long_narration"):
            narration = str(scene.get(field, ""))
            if scene_id == "scene_999":
                prefix = narration[: -len(CREDIT_SENTENCE)] if narration.endswith(CREDIT_SENTENCE) else narration
                if (
                    narration.count(CREDIT_SENTENCE) != 1
                    or not narration.endswith(CREDIT_SENTENCE)
                    or aidiy_pattern.search(prefix)
                ):
                    credit_errors.append(f"{scene_id}.{field}: 最後のひとこと以外に言及あり")
            elif aidiy_pattern.search(narration):
                credit_errors.append(f"{scene_id}.{field}: 本編に AiDiy への言及あり")
    index_content = read_utf8(INDEX_PATH) if INDEX_PATH.is_file() else ""
    for class_name in ("brand", "top-note"):
        match = re.search(
            rf'<div class="{re.escape(class_name)}">(.*?)</div>',
            index_content,
            flags=re.DOTALL,
        )
        if match and aidiy_pattern.search(match.group(1)):
            credit_errors.append(f"index.html.{class_name}: 冒頭表示に AiDiy への言及あり")
    check(
        "確認 6: AiDiy への言及",
        not credit_errors,
        "本編・冒頭になく、scene_999 の両ナレーション末尾だけ"
        if not credit_errors
        else "; ".join(credit_errors),
    )

    image_files = sorted((BASE_DIR / "images").glob("*.png"))
    audio_files = sorted((BASE_DIR / "audio").glob("*.mp3"))
    check("確認 2: PNG 枚数", len(image_files) >= 7, f"{len(image_files)} 枚（必要: 7 枚以上）")
    check("確認 3: MP3 個数", len(audio_files) >= 14, f"{len(audio_files)} 個（必要: 14 個以上）")

    expected_images = {
        str(scene.get("image", ""))
        for scene in scenes
        if isinstance(scene, dict) and scene.get("image")
    }
    expected_audio = {
        str(scene.get(field, ""))
        for scene in scenes
        if isinstance(scene, dict)
        for field in ("short_audio", "long_audio")
        if scene.get(field)
    }
    actual_images = {path.relative_to(BASE_DIR).as_posix() for path in image_files}
    actual_audio = {path.relative_to(BASE_DIR).as_posix() for path in audio_files}
    check(
        "画像参照の対応",
        expected_images == actual_images,
        f"scenario {len(expected_images)} 件 / disk {len(actual_images)} 件",
    )
    check(
        "音声参照の対応",
        expected_audio == actual_audio,
        f"scenario {len(expected_audio)} 件 / disk {len(actual_audio)} 件",
    )

    invalid_png: list[str] = []
    image_sizes: list[str] = []
    for path in image_files:
        try:
            width, height = png_size(path)
            image_sizes.append(f"{path.name}={width}x{height}")
            ratio = width / height if height else 0
            if path.stat().st_size <= 1000 or width < 1280 or height < 720 or abs(ratio - 16 / 9) > 0.08:
                invalid_png.append(path.name)
        except Exception:
            invalid_png.append(path.name)
    check(
        "PNG 実体",
        not invalid_png,
        "全ファイル正常・16:9" if not invalid_png else ", ".join(invalid_png),
    )

    invalid_mp3 = [
        path.name for path in audio_files if path.stat().st_size <= 500 or not mp3_has_header(path)
    ]
    measured_durations: dict[str, float] = {}
    ffprobe = shutil.which("ffprobe")
    ffmpeg = shutil.which("ffmpeg")
    if not ffprobe:
        invalid_mp3.append("ffprobe が見つかりません")
    else:
        for path in audio_files:
            duration = probe_duration(ffprobe, path)
            if duration <= 0:
                invalid_mp3.append(path.name)
            else:
                measured_durations[path.relative_to(BASE_DIR).as_posix()] = duration
    decode_errors: list[str] = []
    if not ffmpeg:
        decode_errors.append("ffmpeg が見つかりません")
    else:
        decode_errors.extend(path.name for path in audio_files if not decodes_without_error(ffmpeg, path))
    check("MP3 実体・尺", not invalid_mp3, "全ファイル正常" if not invalid_mp3 else ", ".join(invalid_mp3))
    check(
        "MP3 デコード",
        not decode_errors,
        "全14ファイルを末尾までデコード可能" if not decode_errors else ", ".join(decode_errors),
    )

    duration_errors: list[str] = []
    for scene in scenes:
        for mode in ("short", "long"):
            audio = str(scene.get(f"{mode}_audio", ""))
            declared = float(scene.get(f"{mode}_duration_sec", 0))
            measured = measured_durations.get(audio, 0.0)
            if measured <= 0 or abs(declared - measured) > 0.15:
                duration_errors.append(f"{audio}: 宣言 {declared:.3f} / 実測 {measured:.3f}")
    check(
        "音声尺の一致",
        bool(measured_durations) and not duration_errors,
        "全音声が実測値と一致" if not duration_errors else "; ".join(duration_errors),
    )

    timeline_errors: list[str] = []
    for mode in ("short", "long"):
        cumulative = 0.0
        for scene in scenes:
            start = float(scene.get(f"{mode}_start_sec", -1))
            duration = float(scene.get(f"{mode}_duration_sec", 0))
            if abs(start - cumulative) > 0.01:
                timeline_errors.append(
                    f"{scene.get('id')}.{mode}: 開始 {start:.3f} / 期待 {cumulative:.3f}"
                )
            cumulative = round(cumulative + duration, 3)
        declared_total = float(scenario.get(f"total_{mode}_duration_sec", 0))
        if abs(cumulative - declared_total) > 0.01:
            timeline_errors.append(
                f"{mode}: 全体尺 {declared_total:.3f} / シーン合計 {cumulative:.3f}"
            )
    check(
        "開始時間・全体尺",
        not timeline_errors,
        "short / long とも累積値が一致" if not timeline_errors else "; ".join(timeline_errors),
    )

    check(
        "確認 4: index.html",
        INDEX_PATH.is_file() and PROJECT_NAME in index_content,
        f"フォルダ名 {PROJECT_NAME} の記載を確認",
    )
    check(
        "index.html 日本語・シナリオ読込",
        '<html lang="ja">' in index_content and 'src="scenario.js"' in index_content,
        "lang=ja と scenario.js 読込を確認",
    )
    player_markers = (
        'id="sceneFrame"',
        "new Audio()",
        'addEventListener("ended"',
        "setTimeout(",
        "new URLSearchParams(window.location.search)",
        "sceneFrame.src = `${scenario.scenes[sceneIndex].id}.html`",
    )
    missing_player_markers = [marker for marker in player_markers if marker not in index_content]
    check(
        "プレイヤー進行機構",
        not missing_player_markers,
        "iframe・音声 ended・保険 timer・?scene 起動を確認"
        if not missing_player_markers
        else ", ".join(missing_player_markers),
    )
    source_player_content = read_utf8(SOURCE_PLAYER_PATH) if SOURCE_PLAYER_PATH.is_file() else ""
    same_player = (
        bool(source_player_content)
        and normalized_player_markup(index_content) == normalized_player_markup(source_player_content)
    )
    check(
        "確認 8: コピー元プレイヤー構造",
        same_player,
        "表示文言以外は小説解説_AiDiy誕生_ja と一致"
        if same_player
        else "コピー元 index.html と予期しない差分あり",
    )

    avatar = str(scenario.get("assets_policy", {}).get("avatar", ""))
    avatar_path = (BASE_DIR / avatar).resolve() if avatar else Path()
    avatar_ok = (
        "VRM_female.vrm" in avatar
        and "VRM_AiDiy" not in scenario_content
        and "VRM_female.vrm" in index_content
        and "VRM_AiDiy" not in index_content
        and avatar_path.is_file()
    )
    check("アバター設定", avatar_ok, f"scenario avatar={avatar!r} / 実体={avatar_path.is_file()}")

    expected_pages = {f"{scene_id}.html" for scene_id in EXPECTED_SCENE_IDS}
    actual_pages = {path.name for path in BASE_DIR.glob("scene_*.html")}
    wrapper_errors: list[str] = []
    if actual_pages != expected_pages:
        wrapper_errors.append(
            f"期待 {', '.join(sorted(expected_pages))} / 実体 {', '.join(sorted(actual_pages))}"
        )
    for index, scene_id in enumerate(EXPECTED_SCENE_IDS):
        path = BASE_DIR / f"{scene_id}.html"
        if not path.is_file():
            wrapper_errors.append(f"{path.name}: なし")
            continue
        content = read_utf8(path)
        required = (
            '<html lang="ja">',
            f"window._SCENE_INDEX = {index};",
            'src="scenario.js"',
            'src="../_common/aidiy_scene.js"',
            'src="scene-layout.js"',
            "四コマ漫画『伝説のプログラマ』",
        )
        missing = [marker for marker in required if marker not in content]
        if missing:
            wrapper_errors.append(f"{path.name}: {', '.join(missing)}")
    check(
        "シーン確認ページ",
        not wrapper_errors,
        "7ページの順序・日本語設定・読込が正常"
        if not wrapper_errors
        else "; ".join(wrapper_errors),
    )

    reference_errors = missing_local_references(INDEX_PATH) if INDEX_PATH.is_file() else ["index.html なし"]
    for scene_id in EXPECTED_SCENE_IDS:
        path = BASE_DIR / f"{scene_id}.html"
        if path.is_file():
            reference_errors.extend(missing_local_references(path))
    check(
        "HTML ローカル参照",
        not reference_errors,
        "index.html と全シーンページに参照切れなし"
        if not reference_errors
        else "; ".join(reference_errors),
    )

    check(
        "確認 5: _gen_audio.py",
        AUDIO_GENERATOR_PATH.is_file(),
        AUDIO_GENERATOR_PATH.name if AUDIO_GENERATOR_PATH.is_file() else "なし",
    )
    helper_errors: list[str] = []
    for path in (AUDIO_GENERATOR_PATH, IMAGE_GENERATOR_PATH):
        if not path.is_file():
            helper_errors.append(f"{path.name}: なし")
            continue
        try:
            compile(read_utf8(path), str(path), "exec")
        except SyntaxError as exc:
            helper_errors.append(f"{path.name}: {exc}")
    check(
        "生成補助スクリプト構文",
        not helper_errors,
        "_gen_audio.py / _gen_scene_images.py とも正常"
        if not helper_errors
        else "; ".join(helper_errors),
    )

    audio_script = read_utf8(AUDIO_GENERATOR_PATH) if AUDIO_GENERATOR_PATH.is_file() else ""
    image_script = read_utf8(IMAGE_GENERATOR_PATH) if IMAGE_GENERATOR_PATH.is_file() else ""
    helper_config_ok = (
        "TTS_LANGUAGE = 'ja'" in audio_script
        and "scenario.js" in audio_script
        and "aidiy_text_to_speech/synthesize" in audio_script
        and "scenario.js" in image_script
        and "aidiy_image_generation/generate" in image_script
        and "小説解説_AiDiy誕生_ja" not in image_script
    )
    check(
        "生成補助スクリプト設定",
        helper_config_ok,
        "日本語・scenario.js 連携・対象APIを確認",
    )

    stale_markers = (
        "小説解説_AiDiy誕生_ja",
        "小説解説『AiDiy誕生』",
        "小説解説_本好きの下剋上_ja",
        "本好きの下剋上",
        "VRM_AiDiy",
    )
    checked_paths = [
        SCENARIO_PATH,
        SCENARIO_JSON_PATH,
        INDEX_PATH,
        ASSETS_PATH,
        AUDIO_GENERATOR_PATH,
        IMAGE_GENERATOR_PATH,
        BASE_DIR / "scene-layout.js",
    ] + sorted(BASE_DIR.glob("scene_*.html"))
    stale_found: list[str] = []
    for path in checked_paths:
        if not path.is_file():
            continue
        content = read_utf8(path)
        stale_found.extend(f"{path.name}: {marker}" for marker in stale_markers if marker in content)
    check(
        "テンプレート固有文言",
        not stale_found,
        "残存なし" if not stale_found else "; ".join(stale_found),
    )

    try:
        scenario_json = load_json(SCENARIO_JSON_PATH)
        scenario_json_ok = scenario_json == scenario
        scenario_json_detail = "scenario.js と一致" if scenario_json_ok else "scenario.js と内容不一致"
    except Exception as exc:
        scenario_json_ok = False
        scenario_json_detail = str(exc)
    check("scenario.json 同期", scenario_json_ok, scenario_json_detail)

    try:
        assets = load_json(ASSETS_PATH)
        image_items = [item for item in assets.get("images", []) if isinstance(item, dict)]
        audio_items = [item for item in assets.get("audio", []) if isinstance(item, dict)]
        asset_images = {str(item.get("path", "")) for item in image_items}
        asset_audio = {
            str(item.get(field, ""))
            for item in audio_items
            for field in ("short_path", "long_path")
            if item.get(field)
        }
        image_metadata_ok = all(
            (BASE_DIR / str(item.get("path", ""))).is_file()
            and item.get("bytes") == (BASE_DIR / str(item.get("path", ""))).stat().st_size
            for item in image_items
        )
        audio_metadata_ok = all(
            (BASE_DIR / str(item.get(field, ""))).is_file()
            and item.get(f"{mode}_bytes") == (BASE_DIR / str(item.get(field, ""))).stat().st_size
            and abs(
                float(item.get(f"{mode}_duration_sec", 0))
                - measured_durations.get(str(item.get(field, "")), 0.0)
            )
            <= 0.15
            for item in audio_items
            for mode, field in (("short", "short_path"), ("long", "long_path"))
        )
        assets_ok = (
            assets.get("project_name") == PROJECT_NAME
            and assets.get("status") == "complete"
            and assets.get("policy", {}).get("language") == "ja"
            and assets.get("policy", {}).get("avatar_model") == "../_vrm/VRM_female.vrm"
            and asset_images == expected_images
            and asset_audio == expected_audio
            and all(item.get("status") == "generated" for item in image_items)
            and all(item.get("status") == "generated" for item in audio_items)
            and image_metadata_ok
            and audio_metadata_ok
        )
        assets_detail = "シナリオ・実ファイルと一致" if assets_ok else "件数・状態・メタデータのいずれかが不一致"
    except Exception as exc:
        assets_ok = False
        assets_detail = str(exc)
    check("assets.json 同期", assets_ok, assets_detail)

    empty_files = [
        path.relative_to(BASE_DIR).as_posix()
        for path in BASE_DIR.rglob("*")
        if path.is_file() and path.stat().st_size == 0
    ]
    check("空ファイル", not empty_files, "なし" if not empty_files else ", ".join(empty_files))

    failed = 0
    for label, ok, detail in results:
        print(f"[{'OK' if ok else 'NG'}] {label}: {detail}")
        if not ok:
            failed += 1
    print(f"\n最終結果: {'OK' if failed == 0 else 'NG'} ({len(results) - failed}/{len(results)} 項目成功)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
