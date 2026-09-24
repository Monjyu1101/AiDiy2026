# -*- coding: utf-8 -*-
"""本好き動画の「学園」「学院」を正しい「貴族院」に直し、音声と尺を同期する。"""

from __future__ import annotations

import copy
import json
import os
import re
import sys
import tempfile
from pathlib import Path

from booklove_pause_pass import (
    append_silence,
    ensure_silence,
    episodes,
    probe_duration,
    write_scenario,
)


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend_tools"))
from tools_proc.text_to_speech import TextToSpeech  # noqa: E402


def correct(text: str) -> str:
    return text.replace("学園祭", "領地対抗戦").replace("学園", "貴族院").replace("学院", "貴族院")


def correct_values(value):
    if isinstance(value, str):
        return correct(value)
    if isinstance(value, list):
        return [correct_values(item) for item in value]
    if isinstance(value, dict):
        return {key: correct_values(item) for key, item in value.items()}
    return value


def correct_prompt_files() -> None:
    """各回フォルダ内の制作指示も、後日の再生成用に同じ表記へそろえる。"""
    for _series, _number, folder, _source in episodes():
        for path in folder.glob("*.md"):
            original = path.read_text(encoding="utf-8-sig")
            revised = correct(original)
            if revised != original:
                path.write_text(revised, encoding="utf-8")
                print(f"制作指示を修正: {path}", flush=True)


def collect():
    changed = []
    audio_targets = []
    for _series, _number, folder, source in episodes():
        original = json.loads((folder / "scenario.json").read_text(encoding="utf-8-sig"))
        revised = correct_values(copy.deepcopy(original))
        source_text = source.read_text(encoding="utf-8-sig")
        if revised == original and correct(source_text) == source_text:
            continue
        changed.append((folder, source, revised, correct(source_text)))
        for before, after in zip(original["scenes"], revised["scenes"], strict=True):
            for mode in ("short", "long"):
                if before[f"{mode}_narration"] == after[f"{mode}_narration"]:
                    continue
                path = folder / after[f"{mode}_audio"]
                if not path.is_file() or path.stat().st_size <= 500:
                    raise FileNotFoundError(path)
                audio_targets.append((folder, after, mode, path))
    if len(changed) != 10 or len(audio_targets) != 14:
        raise RuntimeError(f"修正対象が想定と異なる: {len(changed)}話、{len(audio_targets)}音声")
    return changed, audio_targets


def stage_audio(audio_targets):
    tts = TextToSpeech()
    pending = []
    try:
        for folder, scene, mode, path in audio_targets:
            with tempfile.NamedTemporaryFile(
                prefix="kizokuin_new_", suffix=".mp3", dir=path.parent, delete=False
            ) as handle:
                staged = Path(handle.name)
            pending.append((staged, path))
            audio, info = tts.synthesize(
                scene[f"{mode}_narration"], language="ja", provider="edge", voice="female"
            )
            if info["used_provider"] != "edge" or re.search(r"学園|学院", info["speech_text"]):
                raise RuntimeError(f"再録条件が不正: {path}: {info}")
            staged.write_bytes(audio)
            if "pause_after_speech_text" in scene:
                if scene["pause_after_speech_text"] != "":
                    raise RuntimeError(f"間合い指定が空文字列でない: {path}")
                append_silence(staged, ensure_silence())
            duration = probe_duration(staged)
            if staged.stat().st_size <= 500 or duration <= 1:
                raise RuntimeError(f"音声が不正: {path}")
            print(f"生成: {folder.name}/{path.name} {duration:.3f}秒", flush=True)
        return pending
    except Exception:
        for staged, _ in pending:
            staged.unlink(missing_ok=True)
        raise


def recalculate(folder: Path, data: dict, source: Path, source_text: str) -> None:
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
            audio_assets[scene["id"]][f"{mode}_bytes"] = path.stat().st_size
            audio_assets[scene["id"]][f"{mode}_duration_sec"] = duration
            elapsed += duration
        data[f"total_{mode}_duration_sec"] = round(elapsed, 3)
    minutes, seconds = divmod(round(data["total_long_duration_sec"]), 60)
    data["timing_status"] = (
        "貴族院の名称を修正し、該当音声を再録。"
        f"全MP3の実測尺と開始秒をシナリオに反映済み。ロング版は{minutes}分{seconds:02d}秒。"
    )
    write_scenario(folder, data)
    assets_path.write_text(json.dumps(assets, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    measured = f"| 間合い追加後の実測尺 | {minutes}分{seconds:02d}秒 |"
    if not re.search(r"(?m)^\| 間合い追加後の実測尺 \|.*$", source_text):
        raise RuntimeError(f"実測尺行がない: {source}")
    source_text = re.sub(
        r"(?m)^\| 間合い追加後の実測尺 \|.*$", measured, source_text, count=1
    )
    source.write_text(source_text, encoding="utf-8")

    # 同名ファイルのブラウザキャッシュが旧音声を返さないよう、この話だけ識別子を更新する。
    index_path = folder / "index.html"
    index = index_path.read_text(encoding="utf-8")
    old_audio = 'return `${audioPath}?v=${encodeURIComponent(audioMode)}`;'
    if index.count(old_audio) != 1:
        raise RuntimeError(f"キャッシュ識別子の更新箇所が想定と異なる: {index_path}")
    index = index.replace(old_audio, 'return `${audioPath}?v=${encodeURIComponent(audioMode)}-kizokuin-1`;')
    index_path.write_text(index, encoding="utf-8")
    print(f"更新: {folder.name} ロング {minutes}:{seconds:02d}", flush=True)


if __name__ == "__main__":
    changes, targets = collect()
    staged_audio = stage_audio(targets)
    try:
        for staged, path in staged_audio:
            os.replace(staged, path)
        for folder, source, data, source_text in changes:
            recalculate(folder, data, source, source_text)
    finally:
        for staged, _ in staged_audio:
            staged.unlink(missing_ok=True)
