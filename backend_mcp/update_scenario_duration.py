# -*- coding: utf-8 -*-
"""
生成した MP3 の実尺を ffprobe で計測し、scenario.js の duration_sec / start_sec を更新する
"""
import json
import os
import re
import subprocess
import sys

BASE = r"D:\OneDrive\_sandbox\AiDiy2026\frontend_web\public\Xビデオ"
VIDEOS = [
    "AiDiy紹介_配車管理",
    "AiDiy紹介_生産管理",
    "AiDiy紹介_在庫管理",
    "AiDiy紹介_webAiDiy",
    "AiDiy紹介_avatarAiDiy",
]

def get_duration(mp3_path: str) -> float:
    """ffprobe で MP3 の実尺を取得する"""
    if not os.path.exists(mp3_path):
        return 0.0
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", mp3_path],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except Exception:
        # ffprobe がなければファイルサイズから推定（128kbps MP3）
        size = os.path.getsize(mp3_path)
        return size / (128 * 1024 / 8)

def load_scenario(video_dir: str) -> dict:
    path = os.path.join(video_dir, "scenario.js")
    with open(path, encoding="utf-8") as f:
        js = f.read()
    m = re.search(r"window\.SCENARIO\s*=\s*(\{.*\})\s*;?\s*$", js, re.DOTALL)
    if not m:
        raise ValueError(f"window.SCENARIO が見つかりません: {path}")
    return json.loads(m.group(1))

def save_scenario(video_dir: str, data: dict):
    path = os.path.join(video_dir, "scenario.js")
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    content = f"window.SCENARIO = {json_str};\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  → saved {path}")

def main():
    for video_name in VIDEOS:
        video_dir = os.path.join(BASE, video_name)
        audio_dir = os.path.join(video_dir, "audio")

        print(f"\n{'='*60}")
        print(f"  {video_name}")

        scenario = load_scenario(video_dir)
        scenes = scenario["scenes"]

        short_cumulative = 0.0
        long_cumulative = 0.0

        for scene in scenes:
            sid = scene["id"]

            # short
            short_path = os.path.join(audio_dir, f"short_{sid}.mp3")
            short_dur = get_duration(short_path)
            scene["short_start_sec"] = round(short_cumulative, 3)
            scene["short_duration_sec"] = round(short_dur, 3)
            short_cumulative += short_dur

            # long
            long_path = os.path.join(audio_dir, f"long_{sid}.mp3")
            long_dur = get_duration(long_path)
            scene["long_start_sec"] = round(long_cumulative, 3)
            scene["long_duration_sec"] = round(long_dur, 3)
            long_cumulative += long_dur

            print(f"  {sid}: short={short_dur:.3f}s  long={long_dur:.3f}s")

        scenario["short_duration_sec"] = round(short_cumulative, 3)
        scenario["long_duration_sec"] = round(long_cumulative, 3)
        print(f"  合計: short={short_cumulative:.3f}s  long={long_cumulative:.3f}s")

        save_scenario(video_dir, scenario)

    print("\n完了")

if __name__ == "__main__":
    main()
