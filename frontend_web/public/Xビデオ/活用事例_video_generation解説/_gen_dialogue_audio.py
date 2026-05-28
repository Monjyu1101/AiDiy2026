# -*- coding: utf-8 -*-
"""
掛け合い音声生成スクリプト

scenario.js の dialogue.naration_text から MP3 を生成します。
既存の音声ファイル（500 bytes 超）は自動スキップします。
"""

import json
import os
import sys

_MCP_DIR = 'D:\\OneDrive\\_sandbox\\AiDiy2026\\backend_tools'
if _MCP_DIR not in sys.path:
    sys.path.insert(0, _MCP_DIR)

from mcp_proc.text_to_speech import TextToSpeech

OUTPUT_DIR = 'D:\\OneDrive\\_sandbox\\AiDiy2026\\frontend_web\\public\\Xビデオ\\活用事例_video_generation解説\\audio'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_dialogues():
    scenario_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenario.js")
    with open(scenario_file, encoding="utf-8-sig") as f:
        content = f.read()

    json_str = content.strip()
    if json_str.startswith("window.SCENARIO ="):
        json_str = json_str[len("window.SCENARIO ="):].strip()
    json_str = json_str.rstrip(";").strip()

    data = json.loads(json_str)
    dialogues = []
    for scene in data.get("scenes", []):
        scene_num = str(scene.get("id", "")).replace("scene_", "")
        for turn, dlg in enumerate(scene.get("dialogue", []), start=1):
            speaker = str(dlg.get("speaker", "female") or "female")
            text = str(dlg.get("naration_text", "") or "").strip()
            if not text:
                continue
            dialogues.append((scene_num, turn, speaker, text))
    return dialogues


DIALOGUES = load_dialogues()


def main():
    tts = TextToSpeech()
    total = len(DIALOGUES)
    done = 0
    skip = 0
    fail = 0

    for scene, turn, speaker, text in DIALOGUES:
        fname = f"dlg_{scene}_{turn:02d}_{speaker}.mp3"
        fpath = os.path.join(OUTPUT_DIR, fname)

        if os.path.exists(fpath) and os.path.getsize(fpath) > 500:
            print(f"  [SKIP] {fname}")
            skip += 1
            continue

        print(f"  [GEN ] {fname}")
        try:
            audio_bytes, _ = tts.synthesize(
                speech_text=text,
                language="ja",
                provider="edge",
                voice=speaker,
            )
            with open(fpath, "wb") as wf:
                wf.write(audio_bytes)
            size = len(audio_bytes)
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
