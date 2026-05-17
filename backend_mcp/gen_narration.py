# -*- coding: utf-8 -*-
"""
5本の新ビデオのナレーション音声（short/long MP3）を一括生成するスクリプト
実行: cd backend_mcp && .venv/Scripts/python gen_narration.py
"""
import json
import os
import re
import sys
import time

# backend_mcp ディレクトリを sys.path に追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_proc.text_to_speech import TextToSpeech

BASE = r"D:\OneDrive\_sandbox\AiDiy2026\frontend_web\public\Xビデオ"

VIDEOS = [
    "AiDiy紹介_配車管理",
    "AiDiy紹介_生産管理",
    "AiDiy紹介_在庫管理",
    "AiDiy紹介_webAiDiy",
    "AiDiy紹介_avatarAiDiy",
]

def load_scenario(video_dir: str) -> dict:
    """scenario.js から window.SCENARIO = {...}; を読み込んで dict を返す"""
    path = os.path.join(video_dir, "scenario.js")
    with open(path, encoding="utf-8") as f:
        js = f.read()
    # window.SCENARIO = {...}; → JSON 部分だけ抽出
    m = re.search(r"window\.SCENARIO\s*=\s*(\{.*\})\s*;?\s*$", js, re.DOTALL)
    if not m:
        raise ValueError(f"window.SCENARIO が見つかりません: {path}")
    return json.loads(m.group(1))

def gen_audio(tts: TextToSpeech, text: str, save_path: str) -> float:
    """音声合成して保存。duration_sec を返す（ffprobe がなければ推定値）"""
    if os.path.exists(save_path):
        size = os.path.getsize(save_path)
        if size > 2000:
            print(f"    SKIP (already exists, {size} bytes): {os.path.basename(save_path)}")
            return 0.0

    print(f"    TTS: {os.path.basename(save_path)}")
    print(f"         text: {text[:60]}...")
    audio_bytes, info = tts.synthesize(
        speech_text=text,
        language="ja",
        provider="edge",
        voice="female",
    )
    tts.to_base64(audio_bytes, save_path=save_path)
    duration = info.get("duration_sec", len(audio_bytes) / 16000.0)
    print(f"         → saved {os.path.getsize(save_path)} bytes, ~{duration:.2f}s")
    return duration

def main():
    tts = TextToSpeech()
    total_ok = 0
    total_err = 0

    for video_name in VIDEOS:
        video_dir = os.path.join(BASE, video_name)
        audio_dir = os.path.join(video_dir, "audio")
        os.makedirs(audio_dir, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"  {video_name}")
        print(f"{'='*60}")

        try:
            scenario = load_scenario(video_dir)
        except Exception as e:
            print(f"  ERROR loading scenario: {e}")
            total_err += 1
            continue

        scenes = scenario.get("scenes", [])
        for scene in scenes:
            scene_id = scene["id"]
            short_text = scene.get("short_narration", "").strip()
            long_text = scene.get("long_narration", "").strip()

            print(f"\n  [{scene_id}]")

            # short MP3
            if short_text:
                short_path = os.path.join(audio_dir, f"short_{scene_id}.mp3")
                try:
                    gen_audio(tts, short_text, short_path)
                    total_ok += 1
                except Exception as e:
                    print(f"    ERROR short: {e}")
                    total_err += 1
                time.sleep(0.5)

            # long MP3
            if long_text:
                long_path = os.path.join(audio_dir, f"long_{scene_id}.mp3")
                try:
                    gen_audio(tts, long_text, long_path)
                    total_ok += 1
                except Exception as e:
                    print(f"    ERROR long: {e}")
                    total_err += 1
                time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"  完了: OK={total_ok}  ERR={total_err}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
