# -*- coding: utf-8 -*-
"""小説解説ビデオ 1 回分の MP3 実尺を、scenario.json/js と assets.json へ反映する（Step 09 相当）。

使い方:
    python scripts/novel_update_durations.py <動画ページのフォルダ> ["timing_status の文面（{LONG} は総尺に置換）"]

- 各シーンの short/long の start_sec・duration_sec、total_*_duration_sec を更新する。
- assets.json の audio[] の path・bytes・duration_sec も更新する。
- ffprobe が必要。改行コード（CRLF/LF）は元のファイルに合わせる。
"""
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True, check=True).stdout.strip()
    return round(float(out), 3)


def read(path):
    raw = open(path, encoding="utf-8", newline="").read()
    return raw, ("\r\n" if "\r\n" in raw else "\n")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    folder = sys.argv[1]
    status = sys.argv[2] if len(sys.argv) > 2 else None

    raw, nl = read(os.path.join(folder, "scenario.json"))
    data = json.loads(raw.lstrip("﻿"))
    total = {"short": 0.0, "long": 0.0}
    info = {}
    for scene in data["scenes"]:
        for kind in ("short", "long"):
            path = os.path.join(folder, scene[f"{kind}_audio"])
            sec = duration(path)
            scene[f"{kind}_start_sec"] = round(total[kind], 3)
            scene[f"{kind}_duration_sec"] = sec
            total[kind] += sec
            info[(scene["id"], kind)] = (scene[f"{kind}_audio"], os.path.getsize(path), sec)
    data["total_short_duration_sec"] = round(total["short"], 3)
    data["total_long_duration_sec"] = round(total["long"], 3)
    minutes, seconds = divmod(total["long"], 60)
    if status:
        data["timing_status"] = status.replace("{LONG}", f"{int(minutes)}分{seconds:06.3f}秒")

    body = json.dumps(data, ensure_ascii=False, indent=2)
    open(os.path.join(folder, "scenario.json"), "w", encoding="utf-8", newline="").write(
        body.replace("\n", nl) + (nl if raw.endswith("\n") else ""))
    raw_js, js_nl = read(os.path.join(folder, "scenario.js"))
    open(os.path.join(folder, "scenario.js"), "w", encoding="utf-8", newline="").write(
        ("window.SCENARIO = " + body + ";\n").replace("\n", js_nl))

    assets_path = os.path.join(folder, "assets.json")
    if os.path.exists(assets_path):
        raw_a, a_nl = read(assets_path)
        assets = json.loads(raw_a.lstrip("﻿"))
        for entry in assets.get("audio", []):
            for kind in ("short", "long"):
                key = (entry["scene_id"], kind)
                if key in info:
                    path, size, sec = info[key]
                    entry[f"{kind}_path"], entry[f"{kind}_bytes"], entry[f"{kind}_duration_sec"] = path, size, sec
        open(assets_path, "w", encoding="utf-8", newline="").write(
            json.dumps(assets, ensure_ascii=False, indent=2).replace("\n", a_nl) + (a_nl if raw_a.endswith("\n") else ""))
    print(f"short {total['short']:.3f}s / long {total['long']:.3f}s = {int(minutes)}分{seconds:.1f}秒")


if __name__ == "__main__":
    main()
