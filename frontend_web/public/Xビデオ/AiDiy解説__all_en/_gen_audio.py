# -*- coding: utf-8 -*-
"""
ナレーション音声生成スクリプト（汎用設計）

scenario.js のナレーション・対話記述から対応する音声 MP3 を自動生成します。
既存の音声ファイル（500 bytes 超）は自動スキップします。
"""

import json
import os
import urllib.error
import urllib.request

OUTPUT_DIR = 'D:/OneDrive/_sandbox/AiDiy2026/frontend_web/public/Xビデオ\\AiDiy解説__all_en\\audio'
TTS_API_URL = 'http://localhost:8095/aidiy_text_to_speech/synthesize'
TTS_LANGUAGE = 'en'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_narrations():
    scenario_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenario.js")
    with open(scenario_file, encoding="utf-8-sig") as f:
        content = f.read()

    json_str = content.strip()
    if json_str.startswith("window.SCENARIO ="):
        json_str = json_str[len("window.SCENARIO ="):].strip()
    json_str = json_str.rstrip(";").strip()

    data = json.loads(json_str)
    tasks = []

    for scene in data.get("scenes", []):
        # 1. mcp形式などの short_audio / long_audio のスキャン
        for prefix in ("short", "long"):
            a_key = f"{prefix}_audio"
            t_key = f"{prefix}_narration"
            if a_key in scene and t_key in scene:
                text = str(scene[t_key] or "").strip()
                audio = str(scene[a_key] or "").strip()
                if text and audio:
                    tasks.append((text, "female", audio))

        # 2. dialogue配列（掛け合い形式など）のスキャン
        dialogues = scene.get("dialogue", [])
        if isinstance(dialogues, list):
            for dlg in dialogues:
                if not isinstance(dlg, dict):
                    continue
                audio = str(dlg.get("audio", "") or "").strip()
                text = ""
                for tk in ("naration_text", "text", "content"):
                    if tk in dlg:
                        text = str(dlg[tk] or "").strip()
                        break
                speaker = str(dlg.get("speaker", "female") or "female")
                if text and audio:
                    tasks.append((text, speaker, audio))
    return tasks

NARRATIONS = load_narrations()


def post_json(url, payload, timeout_sec=300):
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
        raise RuntimeError(f"HTTP API に接続できません: {url} ({e})") from e
    result = json.loads(raw)
    if isinstance(result, dict) and result.get("error"):
        raise RuntimeError(result["error"])
    return result


def synthesize_one(text, speaker, out_path):
    # edge supports stable voice synthesizing for both male/female and diverse languages
    return post_json(TTS_API_URL, {
        "speech_text": text,
        "language": TTS_LANGUAGE,
        "provider": "edge",
        "voice": speaker,
        "save_path": out_path,
    })


def main():
    total = len(NARRATIONS)
    done = 0
    skip = 0
    fail = 0

    for text, speaker, audio_ref in NARRATIONS:
        fname = os.path.basename(audio_ref)
        fpath = os.path.join(OUTPUT_DIR, fname)

        if os.path.exists(fpath) and os.path.getsize(fpath) > 500:
            print(f"  [SKIP] {fname}")
            skip += 1
            continue

        print(f"  [GEN ] {fname}")
        try:
            synthesize_one(text, speaker, fpath)
            size = os.path.getsize(fpath) if os.path.exists(fpath) else 0
            if size > 500:
                print(f"         -> OK ({size:,} bytes)")
                done += 1
            else:
                print("         -> FAIL (empty or too small)")
                fail += 1
        except Exception as e:
            print(f"         -> ERROR: {e}")
            fail += 1

    print(f"\n完了: {done} 生成, {skip} スキップ, {fail} 失敗 (合計 {total} 件)")
    if fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
