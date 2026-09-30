# -*- coding: utf-8 -*-
"""MP3 を音声認識にかけ、読み間違いがないか確認する（Step 08 を手で行うときの道具）。

使い方（backend_tools の venv で実行する。speech_recognition が必要）:
    backend_tools/.venv/Scripts/python.exe scripts/novel_stt_check.py <mp3> [...] [--find 語1,語2]

- 20 秒ごとに区切って Google の認識を呼ぶ。区切りにまたがる語は認識が欠けるので、
  気になる語がある場合は --window を変えて重ねて確認する（例: --window 12）。
- --find を付けると、その語が認識結果に含まれるかを表示する。
  「お父様→ととさま」のように誤読すると、認識結果でも別の語になる。
"""
import io
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
import speech_recognition as sr  # noqa: E402


def recognize(path, window):
    total = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True).stdout)
    out, start = [], 0.0
    while start < total:
        wave = subprocess.run(
            ["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(window), "-i", path,
             "-ac", "1", "-ar", "16000", "-f", "wav", "pipe:1"], capture_output=True).stdout
        recognizer = sr.Recognizer()
        recognizer.operation_timeout = 30
        try:
            with sr.AudioFile(io.BytesIO(wave)) as source:
                audio = recognizer.record(source)
            out.append((start, recognizer.recognize_google(audio, language="ja-JP")))
        except Exception as exc:  # 無音・通信エラーなど
            out.append((start, f"<{type(exc).__name__}>"))
        start += window
    return out


def main():
    args = sys.argv[1:]
    window, find = 20.0, []
    for opt in ("--window", "--find"):
        if opt in args:
            i = args.index(opt)
            value = args[i + 1]
            del args[i:i + 2]
            if opt == "--window":
                window = float(value)
            else:
                find = [w for w in value.split(",") if w]
    if not args:
        raise SystemExit(__doc__)
    for path in args:
        print("==", path)
        text = ""
        for start, result in recognize(path, window):
            print(f"{start:6.1f}s {result}")
            text += result
        for word in find:
            print(f"  [{'あり' if word in text.replace(' ', '') else 'なし'}] {word}")


if __name__ == "__main__":
    main()
