# -*- coding: utf-8 -*-
"""「王城」の読み修正に伴う女神の化身編01・10話の音声再録と尺更新。"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path

from booklove_pause_pass import append_silence, ensure_silence, probe_duration, write_scenario


ROOT = Path(__file__).resolve().parents[1]
VIDEO_ROOT = ROOT / "frontend_web" / "public" / "Xビデオ"
sys.path.insert(0, str(ROOT / "backend_tools"))
from tools_proc.text_to_speech import TextToSpeech  # noqa: E402


def targets() -> list[tuple[Path, dict, str, Path]]:
    result = []
    for episode in (1, 10):
        folder = VIDEO_ROOT / f"本好きの下剋上_女神の化身{episode:02d}_ja"
        data = json.loads((folder / "scenario.json").read_text(encoding="utf-8-sig"))
        for scene in data["scenes"]:
            for mode in ("short", "long"):
                narration = scene[f"{mode}_narration"]
                if "王城" not in narration:
                    continue
                audio_path = folder / scene[f"{mode}_audio"]
                if not audio_path.is_file() or audio_path.stat().st_size <= 500:
                    raise FileNotFoundError(audio_path)
                result.append((folder, scene, mode, audio_path))
    if len(result) != 10:
        raise RuntimeError(f"再録対象が想定と異なる: {len(result)}件")
    return result


def regenerate_audio() -> set[Path]:
    tts = TextToSpeech()
    pending: list[tuple[Path, Path]] = []
    try:
        for folder, scene, mode, audio_path in targets():
            narration = scene[f"{mode}_narration"]
            with tempfile.NamedTemporaryFile(
                prefix="oujou_new_", suffix=".mp3", dir=audio_path.parent, delete=False
            ) as handle:
                staged_path = Path(handle.name)
            pending.append((staged_path, audio_path))
            audio, info = tts.synthesize(
                narration, language="ja", provider="edge", voice="female"
            )
            if (info["used_provider"] != "edge"
                    or "おうじょう" not in info["speech_text"]
                    or "王城" in info["speech_text"]):
                raise RuntimeError(f"発音設定またはプロバイダが不正: {audio_path}: {info}")
            staged_path.write_bytes(audio)
            if "pause_after_speech_text" in scene:
                if scene["pause_after_speech_text"] != "":
                    raise RuntimeError(f"間合い指定が空文字列でない: {audio_path}")
                append_silence(staged_path, ensure_silence())
            duration = probe_duration(staged_path)
            if staged_path.stat().st_size <= 500 or duration <= 1:
                raise RuntimeError(f"再録音声が不正: {audio_path}")
            print(f"生成: {folder.name}/{audio_path.name} {duration:.3f}秒", flush=True)
        for staged_path, audio_path in pending:
            os.replace(staged_path, audio_path)
        return {folder for folder, *_ in targets()}
    finally:
        for staged_path, _ in pending:
            staged_path.unlink(missing_ok=True)


def recalculate(folder: Path) -> None:
    data = json.loads((folder / "scenario.json").read_text(encoding="utf-8-sig"))
    assets_path = folder / "assets.json"
    assets = json.loads(assets_path.read_text(encoding="utf-8-sig"))
    audio_assets = {asset["scene_id"]: asset for asset in assets["audio"]}
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

    minutes, seconds = divmod(round(data["total_long_duration_sec"]), 60)
    data["timing_status"] = (
        "王城の発音を『おうじょう』へ修正した音声を再録。"
        f"全MP3の実測尺と開始秒をシナリオに反映済み。ロング版は{minutes}分{seconds:02d}秒。"
    )
    write_scenario(folder, data)
    assets_path.write_text(json.dumps(assets, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    episode = int(re.search(r"(\d\d)_ja$", folder.name).group(1))
    source = (VIDEO_ROOT / "本好き_女神の化身編解説"
              / f"本好き_女神の化身編解説_{episode:02d}.md")
    content = source.read_text(encoding="utf-8-sig")
    measured = f"| 間合い追加後の実測尺 | {minutes}分{seconds:02d}秒 |"
    if not re.search(r"(?m)^\| 間合い追加後の実測尺 \|.*$", content):
        raise RuntimeError(f"実測尺行がない: {source}")
    content = re.sub(r"(?m)^\| 間合い追加後の実測尺 \|.*$", measured, content, count=1)
    source.write_text(content, encoding="utf-8")
    print(f"再計算: {folder.name} ロング {minutes}:{seconds:02d}", flush=True)


if __name__ == "__main__":
    for updated_folder in sorted(regenerate_audio()):
        recalculate(updated_folder)
