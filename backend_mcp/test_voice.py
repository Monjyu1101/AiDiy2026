# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
音声合成 → 音声認識 のエンドツーエンドテスト

aidiy_text_to_speech で合成した MP3 を WAV に変換し、
aidiy_speech_to_text で認識して結果を確認する。
"""

import base64
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_proc.text_to_speech import TextToSpeech, TextToSpeechError
from mcp_proc.speech_to_text import SpeechToText, SpeechToTextError


TEST_PHRASES = [
    "こんにちは、今日はいい天気ですね。",
    "明日の会議は午後三時からです。",
    "東京タワーは高さ三百三十三メートルです。",
    "私は毎朝コーヒーを飲みます。",
    "ありがとうございます、助かりました。",
    "すみません、駅はどちらですか。",
]


def _mp3_to_wav16k(mp3_bytes: bytes) -> bytes:
    """ffmpeg で MP3 を 16kHz モノラル WAV に変換"""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg が見つかりません。PATH に追加してください。")

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(mp3_bytes)
        mp3_path = tmp.name

    wav_path = mp3_path.rsplit(".", 1)[0] + ".wav"
    try:
        subprocess.run(
            [
                ffmpeg, "-i", mp3_path,
                "-ar", "16000", "-ac", "1", "-sample_fmt", "s16",
                "-y", "-loglevel", "error", wav_path,
            ],
            check=True, timeout=30,
        )
        with open(wav_path, "rb") as f:
            return f.read()
    finally:
        for p in (mp3_path, wav_path):
            try:
                os.remove(p)
            except OSError:
                pass


def main():
    print("=" * 60)
    print(" 音声合成 → 音声認識 エンドツーエンドテスト")
    print("=" * 60)

    tts = TextToSpeech()
    stt = SpeechToText()

    total = len(TEST_PHRASES)
    ok = 0
    ng = 0

    for i, phrase in enumerate(TEST_PHRASES, 1):
        print(f"\n[{i}/{total}] 元: {phrase}")

        try:
            # 音声合成
            t_start = time.time()
            mp3_bytes, tts_info = tts.synthesize(
                speech_text=phrase,
                language="ja",
                provider="edge",
            )
            t_synth = time.time() - t_start

            # MP3 → WAV
            wav_bytes = _mp3_to_wav16k(mp3_bytes)

            # 音声認識
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(wav_bytes)
                wav_path = tmp.name

            t_start = time.time()
            result = stt.recognize(file_path=wav_path)
            t_recog = time.time() - t_start
            os.remove(wav_path)

            recognized = result["recognition_text"]
            print(f"  合成: {tts_info['used_provider']} {len(mp3_bytes)}bytes ({t_synth:.1f}s)")
            print(f"  認識: {result['provider']} -> \"{recognized}\" ({t_recog:.1f}s)")

            if recognized:
                ok += 1
            else:
                print(f"  NG: 認識結果が空です")
                ng += 1

        except (TextToSpeechError, SpeechToTextError, RuntimeError) as e:
            print(f"  エラー: {e}")
            ng += 1
        except Exception as e:
            print(f"  予期せぬエラー: {e}")
            ng += 1

    print("\n" + "=" * 60)
    print(f" 結果: 成功 {ok} / 失敗 {ng} / 合計 {total}")
    print("=" * 60)

    if ng > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
