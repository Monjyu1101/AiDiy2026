# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# See LICENSE for full terms.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
テキスト音声合成（TTS）→ 音声認識（STT）連携テスト

テスト構成:
  Test 1: Edge TTS      → Google Speech API (auto) で認識
  Test 2: FreeAI TTS    → Google Speech API (auto) で認識
  Test 3: FreeAI TTS    → OpenAI Whisper で認識（OpenAI キーがある場合）
"""

import os
import sys
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_proc.text_to_speech import TextToSpeech, TextToSpeechError
from mcp_proc.speech_to_text import SpeechToText, SpeechToTextError


TEST_TEXT = "本日は晴天なり。音声合成と音声認識のテストです。"


def _mp3_to_wav_path(tts: TextToSpeech, audio_bytes: bytes) -> str | None:
    """TTS 出力（MP3）を WAV に変換して一時ファイルパスを返す。変換不可なら None"""
    wav_bytes = tts._convert_audio(audio_bytes, "mp3", "wav")
    if not wav_bytes:
        return None
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.write(wav_bytes)
    tmp.close()
    return tmp.name


def _run_stt(stt: SpeechToText, wav_path: str, provider: str) -> dict | None:
    """WAV ファイルを STT にかける。ファイルを必ず削除してから返す"""
    try:
        return stt.recognize(file_path=wav_path, provider=provider)
    finally:
        try:
            os.unlink(wav_path)
        except OSError:
            pass


def main():
    tts = TextToSpeech()
    stt = SpeechToText()

    freeai_key = tts._get_api_key("freeai")
    openai_key = tts._get_api_key("openai")

    print(f"ffmpeg   : {'利用可' if tts.ffmpeg_path else '不可（WAV変換スキップ）'}")
    print(f"freeai   : {'設定済' if freeai_key else '未設定'}")
    print(f"openai   : {'設定済' if openai_key else '未設定'}")
    print(f"テキスト : {TEST_TEXT}")
    print()

    # ------------------------------------------------------------------ #
    # Test 1: Edge TTS → Google Speech (auto)
    # ------------------------------------------------------------------ #
    print("=" * 60)
    print("Test 1: Edge TTS → Google Speech API (auto) で認識")
    print("=" * 60)

    audio1, tts1 = tts.synthesize(
        speech_text=TEST_TEXT,
        provider="edge",
        voice="female",
        ratio=1,
    )
    tts.to_base64(audio1)  # デフォルト保存

    print(f"  [TTS] provider = {tts1['used_provider']}")
    print(f"  [TTS] voice    = {tts1['voice']}")
    print(f"  [TTS] format   = {tts1['audio_format']}")
    print(f"  [TTS] bytes    = {tts1['audio_bytes_length']:,}")

    wav1 = _mp3_to_wav_path(tts, audio1)
    if wav1:
        stt1 = _run_stt(stt, wav1, provider="auto")
        print(f"  [STT] provider = {stt1['provider']}")
        print(f"  [STT] text     = {stt1['recognition_text']}")
    else:
        print("  [STT] SKIP: ffmpeg 不在のため WAV 変換不可")

    # ------------------------------------------------------------------ #
    # Test 2: FreeAI TTS → Google Speech (auto)
    # ------------------------------------------------------------------ #
    print()
    print("=" * 60)
    print("Test 2: FreeAI TTS → Google Speech API (auto) で認識")
    print("=" * 60)

    if not freeai_key:
        print("  SKIP: FreeAI API キーが設定されていません")
    else:
        audio2, tts2 = tts.synthesize(
            speech_text=TEST_TEXT,
            provider="freeai",
            voice="female",
            ratio=1,
        )
        tts.to_base64(audio2)

        print(f"  [TTS] provider = {tts2['used_provider']}")
        print(f"  [TTS] voice    = {tts2['voice']}")
        print(f"  [TTS] format   = {tts2['audio_format']}")
        print(f"  [TTS] bytes    = {tts2['audio_bytes_length']:,}")

        wav2 = _mp3_to_wav_path(tts, audio2)
        if wav2:
            stt2 = _run_stt(stt, wav2, provider="auto")
            print(f"  [STT] provider = {stt2['provider']}")
            print(f"  [STT] text     = {stt2['recognition_text']}")
        else:
            print("  [STT] SKIP: ffmpeg 不在のため WAV 変換不可")

    # ------------------------------------------------------------------ #
    # Test 3: FreeAI TTS → OpenAI Whisper
    # ------------------------------------------------------------------ #
    print()
    print("=" * 60)
    print("Test 3: FreeAI TTS → OpenAI Whisper で認識")
    print("=" * 60)

    missing = [n for n, k in [("FreeAI", freeai_key), ("OpenAI", openai_key)] if not k]
    if missing:
        print(f"  SKIP: {' / '.join(missing)} API キーが設定されていません")
    else:
        audio3, tts3 = tts.synthesize(
            speech_text=TEST_TEXT,
            provider="freeai",
            voice="male",
            ratio=1,
        )
        tts.to_base64(audio3)

        print(f"  [TTS] provider = {tts3['used_provider']}")
        print(f"  [TTS] voice    = {tts3['voice']}")
        print(f"  [TTS] format   = {tts3['audio_format']}")
        print(f"  [TTS] bytes    = {tts3['audio_bytes_length']:,}")

        wav3 = _mp3_to_wav_path(tts, audio3)
        if wav3:
            stt3 = _run_stt(stt, wav3, provider="openai")
            print(f"  [STT] provider = {stt3['provider']}")
            print(f"  [STT] model    = {stt3['model']}")
            print(f"  [STT] text     = {stt3['recognition_text']}")
        else:
            print("  [STT] SKIP: ffmpeg 不在のため WAV 変換不可")

    print()
    print("=" * 60)
    print("OK")


if __name__ == "__main__":
    main()
