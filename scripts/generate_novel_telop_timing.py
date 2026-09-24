"""Precompute sentence anchors from the actual narration MP3s.

Usage: python scripts/generate_novel_telop_timing.py [--write]
Without --write this reports match rates without modifying files.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1] / "frontend_web/public/Xビデオ"
SENTENCE = re.compile(r"[^。！？!?]+[。！？!?]?")
SILENCE_START = re.compile(r"silence_start: ([\d.]+)")
SILENCE_END = re.compile(r"silence_end: ([\d.]+)")


def analyse(item: tuple[Path, str, str, dict]) -> tuple[Path, str, str, list | None, int, int]:
    page, scene_id, mode, scene = item
    narration = str(scene.get(f"{mode}_narration") or "").replace('""', "").strip()
    sentences = [part.strip() for part in SENTENCE.findall(narration) if part.strip()]
    audio_path = scene.get(f"{mode}_audio") or ""
    audio = page / audio_path
    if not sentences or not audio_path or not audio.is_file():
        return page, scene_id, mode, None, len(sentences), 0
    begins: list[float] = []
    ends: list[float] = []
    for minimum_pause in (0.45, 0.40, 0.35):
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostats", "-i", str(audio),
             "-af", f"silencedetect=noise=-36dB:d={minimum_pause}", "-f", "null", "NUL"],
            capture_output=True, text=True, errors="replace", check=False,
        )
        begins = [float(value) for value in SILENCE_START.findall(result.stderr)]
        ends = [float(value) for value in SILENCE_END.findall(result.stderr)]
        if len(begins) == len(sentences) and len(ends) == len(sentences):
            break
    duration = float(scene.get(f"{mode}_duration_sec") or 0)
    if len(begins) == len(sentences) - 1 and ends and duration - ends[-1] > 1.0:
        begins.append(duration)
        ends.append(duration)
    if len(begins) != len(sentences) or len(ends) != len(sentences):
        return page, scene_id, mode, None, len(sentences), len(begins)
    # Only use one-to-one punctuation/silence matches. A partial match can
    # move all later captions to the wrong sentence.
    starts = [0.0] + ends[:-1]
    if duration <= 0 or any(start >= end for start, end in zip(starts, begins)):
        return page, scene_id, mode, None, len(sentences), len(begins)
    return page, scene_id, mode, [[round(start, 3), round(end, 3)] for start, end in zip(starts, begins)], len(sentences), len(begins)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--page", help="Only process a directory name under Xビデオ")
    parser.add_argument("--repair", action="store_true", help="Keep existing anchors and analyse only missing tracks")
    args = parser.parse_args()
    pages = [page for page in ROOT.iterdir() if page.is_dir() and (
        page.name.startswith("小説解説_") or page.name.startswith("本好きの下剋上_")
        or page.name == "四コマ漫画_伝説のプログラマ_ja"
    ) and (page / "scenario.json").is_file() and (not args.page or page.name == args.page)]
    jobs = []
    timings: dict[Path, dict] = {}
    for page in pages:
        timing_file = page / "telop_timing.json"
        timings[page] = json.loads(timing_file.read_text(encoding="utf-8")) if args.repair and timing_file.is_file() else {}
        scenario = json.loads((page / "scenario.json").read_text(encoding="utf-8-sig"))
        for scene in scenario.get("scenes", []):
            for mode in ("short", "long"):
                if args.repair and mode in timings[page].get(scene["id"], {}):
                    continue
                jobs.append((page, scene["id"], mode, scene))
    matched = 0
    missing = 0
    mismatched = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for future in as_completed([pool.submit(analyse, job) for job in jobs]):
            page, scene_id, mode, anchors, sentence_count, silence_count = future.result()
            if anchors is not None:
                timings[page].setdefault(scene_id, {})[mode] = anchors
                matched += 1
            elif silence_count:
                mismatched.append((page.name, scene_id, mode, sentence_count, silence_count))
            else:
                missing += 1
    print(f"pages={len(pages)} tracks={len(jobs)} matched={matched} mismatched={len(mismatched)} missing={missing}")
    for row in mismatched[:30]:
        print("mismatch", *row)
    if args.write:
        for page, cues in timings.items():
            (page / "telop_timing.json").write_text(
                json.dumps(cues, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
            )
        print(f"wrote={len(timings)}")


if __name__ == "__main__":
    main()
