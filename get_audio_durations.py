import subprocess
import json
import os

# 音声ファイルのディレクトリ
audio_dir = "/workspaces/AiDiy2026/frontend_web/public/Xビデオ/解説_Gemini3-5Flash/audio"

# MP3ファイルをソートして取得
files = sorted([f for f in os.listdir(audio_dir) if f.endswith('.mp3')])
results = {}

for f in files:
    path = os.path.join(audio_dir, f)
    # ffprobeで音声ファイルの実時間を取得
    r = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', path],
        capture_output=True, text=True
    )
    dur = float(r.stdout.strip()) if r.stdout.strip() else None
    results[f] = dur

# 結果をJSON形式で出力
print(json.dumps(results, indent=2, ensure_ascii=False))