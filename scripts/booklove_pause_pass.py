# -*- coding: utf-8 -*-
"""本好きの下剋上の解説動画に、空文字列TTS由来の間合いを追加する。

初回: python scripts/booklove_pause_pass.py prepare
音声: python scripts/booklove_pause_pass.py apply
実測: python scripts/booklove_pause_pass.py timings
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIDEO_ROOT = ROOT / "frontend_web" / "public" / "Xビデオ"
SILENCE_PATH = VIDEO_ROOT / "_audio" / "空文字列_1秒無音.mp3"
PAUSE_NOTE = (
    '**間合い**：この場面の読み上げ後、独立した音声生成要求 '
    '`speech_text=""` から作る1秒の無音を入れる。'
)
POLICY_NOTE = (
    '- 間合いは本文中の `""` では表さない。指定した場面の後へ、'
    '独立した `speech_text=""` の音声生成要求による1秒無音を挿入する。'
)
KEYWORDS = (
    "別離", "決意", "選択", "約束", "救出", "危機", "真実", "秘密", "告白",
    "祈り", "祝福", "喪失", "死", "家族", "帰還", "再会", "戦い", "勝利",
    "裏切り", "王族", "書庫", "儀式", "名捧げ", "魔力", "未来",
)


def episodes() -> list[tuple[str, int, Path, Path]]:
    result = []
    for series, count, prefix, source_prefix in (
        ("貴族院編", 20, "本好きの下剋上_貴族院編解説", "本好き_貴族院編解説"),
        ("女神の化身編", 23, "本好きの下剋上_女神の化身", "本好き_女神の化身編解説"),
    ):
        for number in range(1, count + 1):
            code = f"{number:02d}"
            folder = VIDEO_ROOT / f"{prefix}{code}_ja"
            source = VIDEO_ROOT / source_prefix / f"{source_prefix}_{code}.md"
            if not folder.is_dir() or not source.is_file():
                raise FileNotFoundError(f"{folder} / {source}")
            result.append((series, number, folder, source))
    return result


def load_scenario(folder: Path) -> dict:
    return json.loads((folder / "scenario.json").read_text(encoding="utf-8-sig"))


def write_scenario(folder: Path, data: dict) -> None:
    value = json.dumps(data, ensure_ascii=False, indent=2)
    (folder / "scenario.json").write_text(value + "\n", encoding="utf-8")
    (folder / "scenario.js").write_text("window.SCENARIO = " + value + ";\n", encoding="utf-8")


def choose_pauses(scenes: list[dict]) -> list[str]:
    # 22ページを5区間に分け、各区間で意味の強い見出しを持つ場面を選ぶ。
    bands = ((0, 3), (4, 7), (8, 11), (12, 15), (16, 20))
    selected = []
    for lo, hi in bands:
        candidates = []
        for index in range(lo, hi + 1):
            scene = scenes[index]
            title = str(scene.get("title", ""))
            lead = str(scene.get("lead", ""))
            score = sum(3 for word in KEYWORDS if word in title)
            score += sum(1 for word in KEYWORDS if word in lead)
            score += len(str(scene.get("long_narration", ""))) / 10000
            candidates.append((score, index))
        index = max(candidates)[1]
        selected.append(scenes[index]["id"])
    return selected


def update_source(source: Path, selected: list[str]) -> None:
    content = source.read_text(encoding="utf-8-sig")
    old_policy = '- `` は読み上げない1秒の間合い記号として、場面転換や重要な余韻の位置に入れる。'
    content = content.replace(old_policy, POLICY_NOTE)
    if POLICY_NOTE not in content:
        heading = "## 語りの方針\n"
        if heading not in content:
            raise ValueError(f"語りの方針がない: {source}")
        content = content.replace(heading, heading + "\n" + POLICY_NOTE + "\n", 1)
    if "## 約30分版ナレーション正本" in content:
        head, tail = content.split("## 約30分版ナレーション正本", 1)
        prefix = head + "## 約30分版ナレーション正本"
    else:
        prefix, tail = "", content
    for scene_id in selected:
        pattern = rf"(?m)^(### {re.escape(scene_id)}[^\n]*\n)"
        if len(re.findall(pattern, tail)) != 1:
            raise ValueError(f"見出しが1件ではない: {source} {scene_id}")
        tail = re.sub(
            pattern,
            lambda match: match.group(1)
            if tail[match.end():].startswith(PAUSE_NOTE)
            else match.group(1) + PAUSE_NOTE + "\n",
            tail,
            count=1,
        )
    source.write_text(prefix + tail, encoding="utf-8")


def update_generator(folder: Path) -> None:
    path = folder / "_gen_audio.py"
    content = path.read_text(encoding="utf-8-sig")
    if "PAUSE_SCENES = {" in content:
        return
    content = content.replace(
        "    narrations = []\n",
        '    global PAUSE_SCENES\n'
        '    PAUSE_SCENES = {str(scene.get("id", "")).replace("scene_", "")\n'
        '                    for scene in data.get("scenes", [])\n'
        '                    if "pause_after_speech_text" in scene}\n'
        "    narrations = []\n",
        1,
    )
    if 'global PAUSE_SCENES' not in content:
        raise ValueError(f"生成スクリプトの構造が異なる: {path}")
    if "    force_long = " not in content:
        content = content.replace(
            "def main():\n",
            'def main():\n    force_long = "--force-long" in sys.argv[1:]\n',
            1,
        )
    old_skip = "if os.path.exists(fpath) and os.path.getsize(fpath) > 500:"
    new_skip = (
        'if os.path.exists(fpath) and os.path.getsize(fpath) > 500 '
        'and not (force_long and kind == "long"):'
    )
    content = content.replace(old_skip, new_skip)
    marker = "            synthesize_one(text, fpath)\n"
    replacement = (
        marker +
        '            if scene_num in PAUSE_SCENES:\n'
        '                scripts_dir = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", "..", "scripts"))\n'
        '                if scripts_dir not in sys.path:\n'
        '                    sys.path.insert(0, scripts_dir)\n'
        '                from booklove_pause_pass import append_silence, ensure_silence\n'
        '                append_silence(fpath, ensure_silence())\n'
    )
    if marker not in content:
        raise ValueError(f"合成箇所が見つからない: {path}")
    content = content.replace(marker, replacement, 1)
    path.write_text(content, encoding="utf-8")


def prepare() -> None:
    for series, number, folder, source in episodes():
        data = load_scenario(folder)
        selected = choose_pauses(data["scenes"])
        for scene in data["scenes"]:
            if scene["id"] in selected:
                scene["pause_after_speech_text"] = ""
                scene["pause_after_sec"] = 1
                scene.setdefault("pause_applied_modes", [])
        data["timing_status"] = "間合い指定済み。空文字列音声の追加後に実測尺を再計算する。"
        write_scenario(folder, data)
        update_source(source, selected)
        update_generator(folder)
        print(f"{series}{number:02d}: {', '.join(selected)}", flush=True)


def probe_duration(path: Path) -> float:
    process = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )
    return round(float(process.stdout.strip()), 3)


def ensure_silence() -> Path:
    if SILENCE_PATH.is_file() and SILENCE_PATH.stat().st_size > 500:
        return SILENCE_PATH
    SILENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    # 常駐HTTPサービスが旧版の場合も、同じTTS実装の空文字列処理を直接使う。
    sys.path.insert(0, str(ROOT / "backend_tools"))
    from tools_proc.text_to_speech import TextToSpeech
    audio, info = TextToSpeech().synthesize(
        speech_text="", language="ja", provider="edge", voice="female",
    )
    if not info.get("is_silence") or info.get("silence_duration_sec") != 1.0:
        raise RuntimeError("空文字列TTSが1秒無音を返さなかった")
    SILENCE_PATH.write_bytes(audio)
    if not SILENCE_PATH.is_file() or SILENCE_PATH.stat().st_size <= 500:
        raise RuntimeError("空文字列TTSによる無音生成に失敗")
    print(f"空文字列TTS無音: {probe_duration(SILENCE_PATH):.3f}秒", flush=True)
    return SILENCE_PATH


def append_silence(audio_path: str | Path, silence_path: str | Path) -> None:
    audio_path = Path(audio_path)
    silence_path = Path(silence_path)
    with tempfile.NamedTemporaryFile(
        prefix="pause_join_", suffix=".mp3", dir=audio_path.parent, delete=False,
    ) as handle:
        output = Path(handle.name)
    try:
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-i", str(audio_path), "-i", str(silence_path),
             "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1[a]",
             "-map", "[a]", "-codec:a", "libmp3lame", "-b:a", "48k", str(output)],
            check=True, capture_output=True, text=True, encoding="utf-8",
        )
        if output.stat().st_size <= 500:
            raise RuntimeError(f"連結後のMP3が空: {audio_path}")
        os.replace(output, audio_path)
    finally:
        if output.exists():
            output.unlink()


def apply_audio() -> None:
    silence = ensure_silence()
    for series, number, folder, _source in episodes():
        data = load_scenario(folder)
        applied = 0
        for scene in data["scenes"]:
            if "pause_after_speech_text" not in scene:
                continue
            if scene["pause_after_speech_text"] != "":
                raise ValueError(f"無音要求が空文字列でない: {folder} {scene['id']}")
            for mode in ("short", "long"):
                if mode in scene.get("pause_applied_modes", []):
                    continue
                audio_path = folder / scene[f"{mode}_audio"]
                append_silence(audio_path, silence)
                scene.setdefault("pause_applied_modes", []).append(mode)
                write_scenario(folder, data)
                applied += 1
        print(f"{series}{number:02d}: {applied}本の音声へ間合い追加", flush=True)


def timings() -> None:
    for series, number, folder, source in episodes():
        data = load_scenario(folder)
        assets_path = folder / "assets.json"
        assets = json.loads(assets_path.read_text(encoding="utf-8-sig"))
        audio_assets = {item["scene_id"]: item for item in assets["audio"]}
        for mode in ("short", "long"):
            elapsed = 0.0
            for scene in data["scenes"]:
                path = folder / scene[f"{mode}_audio"]
                duration = probe_duration(path)
                scene[f"{mode}_start_sec"] = round(elapsed, 3)
                scene[f"{mode}_duration_sec"] = duration
                asset = audio_assets[scene["id"]]
                asset[f"{mode}_bytes"] = path.stat().st_size
                asset[f"{mode}_duration_sec"] = duration
                elapsed += duration
            data[f"total_{mode}_duration_sec"] = round(elapsed, 3)
        if any(
            set(scene.get("pause_applied_modes", [])) != {"short", "long"}
            for scene in data["scenes"] if "pause_after_speech_text" in scene
        ):
            raise RuntimeError(f"間合い未適用の音声がある: {folder}")
        seconds = data["total_long_duration_sec"]
        minutes, rem = divmod(round(seconds), 60)
        data["timing_status"] = (
            "空文字列TTSから作った1秒無音を指定シーンのshort/long音声に挿入。"
            f"全MP3の実測尺と開始秒をシナリオに反映済み。ロング版は{minutes}分{rem:02d}秒。"
        )
        write_scenario(folder, data)
        assets_path.write_text(json.dumps(assets, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        content = source.read_text(encoding="utf-8-sig")
        measured = f"| 間合い追加後の実測尺 | {minutes}分{rem:02d}秒 |"
        if re.search(r"(?m)^\| 間合い追加後の実測尺 \|.*$", content):
            content = re.sub(r"(?m)^\| 間合い追加後の実測尺 \|.*$", measured, content, count=1)
        else:
            content = re.sub(r"(?m)^(\| 想定尺 \|[^\n]*\n)", r"\1" + measured + "\n", content, count=1)
        source.write_text(content, encoding="utf-8")
        print(f"{series}{number:02d}: {minutes}:{rem:02d} ({seconds:.3f}秒)", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("prepare", "apply", "timings"))
    step = parser.parse_args().step
    if step == "prepare":
        prepare()
    elif step == "apply":
        apply_audio()
    else:
        timings()


if __name__ == "__main__":
    main()
