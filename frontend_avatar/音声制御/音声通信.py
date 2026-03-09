# -*- coding: utf-8 -*-
#
# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from __future__ import annotations

import base64
import importlib
import math
import struct
import threading
from typing import Callable

from 通信制御.コア接続 import AIAvatarConnector
from util import AuthSession
from log_config import get_logger

logger = get_logger(__name__)


_sounddevice_module = None

OUTPUT_AUDIO_SAMPLE_RATE = 24000
OUTPUT_AUDIO_CHANNELS = 1
OUTPUT_AUDIO_SAMPLE_WIDTH = 2
OUTPUT_AUDIO_BLOCK_SIZE = 960
INPUT_AUDIO_GEMINI_SAMPLE_RATE = 16000
INPUT_AUDIO_OPENAI_SAMPLE_RATE = 24000
INPUT_AUDIO_BLOCK_SIZE = 1024


def sounddeviceモジュール取得():
    global _sounddevice_module
    if _sounddevice_module is None:
        try:
            _sounddevice_module = importlib.import_module("sounddevice")
        except ImportError:
            _sounddevice_module = False
    return None if _sounddevice_module is False else _sounddevice_module


def 音声MIMEからレートを抽出(mime_type: str | None, default_rate: int = OUTPUT_AUDIO_SAMPLE_RATE) -> int:
    if not mime_type:
        return default_rate
    lower_mime = mime_type.lower()
    for segment in lower_mime.split(";"):
        segment = segment.strip()
        if segment.startswith("rate="):
            try:
                parsed_rate = int(segment.split("=", 1)[1].strip())
            except ValueError:
                return default_rate
            if parsed_rate > 0:
                return parsed_rate
    return default_rate


class AudioOutputPlayer:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.stop_requested = False
        self.speaker_enabled = True
        self.output_stream = None
        self.output_sample_rate = OUTPUT_AUDIO_SAMPLE_RATE
        self.pending_audio = bytearray()
        self.pending_lip_audio = bytearray()
        self.underflow_count = 0
        self.lip_sync_callback: Callable[[float], None] | None = None
        self._出力ストリームを確保(self.output_sample_rate)

    @staticmethod
    def _pcm振幅を計算(audio_bytes: bytes) -> float:
        n = len(audio_bytes) // 2
        if n == 0:
            return 0.0
        samples = struct.unpack_from(f"<{n}h", audio_bytes)
        rms = math.sqrt(sum(s * s for s in samples) / n)
        return min(1.0, rms / 8000.0)

    def スピーカー有効を設定(self, enabled: bool) -> bool:
        self.speaker_enabled = enabled
        stream_ready = self._出力ストリームを確保(self.output_sample_rate)
        if not enabled:
            self.再生停止(clear_queue=True)
            logger.info("スピーカーをOFFにしました。受信は継続し、再生バッファのみ破棄します。")
            return True
        if not stream_ready:
            self.speaker_enabled = False
            self.再生停止(clear_queue=True)
            logger.warning("スピーカーを利用できないため、OFFに戻しました。")
            return False
        logger.info("スピーカーをONにしました。出力ストリームは接続維持します。")
        return True

    def base64音声を追加(self, base64_audio: str, mime_type: str) -> None:
        try:
            audio_bytes = base64.b64decode(base64_audio)
        except Exception:
            logger.warning("base64音声のデコードに失敗しました")
            return
        if not audio_bytes:
            return

        sample_rate = 音声MIMEからレートを抽出(mime_type, self.output_sample_rate)
        self._出力ストリームを確保(sample_rate)

        with self.lock:
            self.pending_lip_audio.extend(audio_bytes)
            if self.speaker_enabled:
                self.pending_audio.extend(audio_bytes)

        if not self.speaker_enabled:
            logger.info("スピーカーOFFのため無音再生でリップ同期のみ継続します: mime=%s bytes=%s", mime_type, len(audio_bytes))

    def 再生停止(self, clear_queue: bool = False) -> None:
        if not clear_queue:
            return
        with self.lock:
            self.pending_audio.clear()
            self.pending_lip_audio.clear()
        if self.lip_sync_callback is not None:
            try:
                self.lip_sync_callback(0.0)
            except Exception:
                pass

    def 終了(self) -> None:
        self.stop_requested = True
        self.再生停止(clear_queue=True)
        self._出力ストリームを閉じる()

    def _出力ストリームを確保(self, sample_rate: int) -> bool:
        sounddevice = sounddeviceモジュール取得()
        if sounddevice is None:
            logger.warning("sounddevice が未導入のため音声再生を無効化します")
            return False

        if sample_rate <= 0:
            sample_rate = OUTPUT_AUDIO_SAMPLE_RATE

        current_stream = self.output_stream
        if current_stream is not None and self.output_sample_rate == sample_rate:
            return True

        self._出力ストリームを閉じる()

        try:
            self.output_stream = sounddevice.RawOutputStream(
                samplerate=sample_rate,
                blocksize=OUTPUT_AUDIO_BLOCK_SIZE,
                channels=OUTPUT_AUDIO_CHANNELS,
                dtype="int16",
                callback=self._出力コールバック,
                prime_output_buffers_using_stream_callback=True,
            )
            self.output_stream.start()
            self.output_sample_rate = sample_rate
            self.underflow_count = 0
            logger.info("出力ストリームを開始しました: rate=%s block=%s", sample_rate, OUTPUT_AUDIO_BLOCK_SIZE)
            return True
        except Exception:
            self.output_stream = None
            logger.exception("出力ストリームの開始に失敗しました")
            return False

    def _出力ストリームを閉じる(self) -> None:
        stream = self.output_stream
        self.output_stream = None
        if stream is None:
            return
        try:
            stream.stop()
        except Exception:
            pass
        try:
            stream.close()
        except Exception:
            pass

    def _出力コールバック(self, outdata, frames, time_info, status) -> None:
        del time_info
        if status:
            status_text = str(status).strip()
            normalized_status = status_text.lower()
            if status_text and normalized_status not in {"priming output", "output underflow"}:
                logger.warning("出力ストリーム状態: %s", status_text)

        byte_count = frames * OUTPUT_AUDIO_CHANNELS * OUTPUT_AUDIO_SAMPLE_WIDTH
        chunk = b""
        lip_chunk = b""
        should_silence = self.stop_requested or not self.speaker_enabled

        with self.lock:
            if self.pending_lip_audio:
                lip_available = min(byte_count, len(self.pending_lip_audio))
                lip_chunk = bytes(self.pending_lip_audio[:lip_available])
                del self.pending_lip_audio[:lip_available]
            if not should_silence and self.pending_audio:
                available = min(byte_count, len(self.pending_audio))
                chunk = bytes(self.pending_audio[:available])
                del self.pending_audio[:available]

        if len(chunk) < byte_count:
            if not should_silence and chunk:
                self.underflow_count += 1
            chunk += b"\x00" * (byte_count - len(chunk))
        else:
            self.underflow_count = 0

        if self.lip_sync_callback is not None:
            try:
                self.lip_sync_callback(self._pcm振幅を計算(lip_chunk))
            except Exception:
                pass

        outdata[:] = chunk


class MicrophoneInputStreamer:
    def __init__(self, auth_session: AuthSession, connector: AIAvatarConnector) -> None:
        self.auth_session = auth_session
        self.connector = connector
        self.input_stream = None
        self.sample_rate = INPUT_AUDIO_GEMINI_SAMPLE_RATE
        self.is_recording = False
        self.audio_input_started = False
        self.lock = threading.Lock()

    def LiveAI名を設定(self, live_ai_name: str) -> None:
        new_rate = INPUT_AUDIO_OPENAI_SAMPLE_RATE if str(live_ai_name).lower() == "openai_live" else INPUT_AUDIO_GEMINI_SAMPLE_RATE
        restart_required = self.is_recording and new_rate != self.sample_rate
        self.sample_rate = new_rate
        if restart_required:
            logger.info("LiveAI変更によりマイク入力レートを切り替えます: rate=%s", new_rate)
            self.停止()
            self.開始()

    def 開始(self) -> bool:
        sounddevice = sounddeviceモジュール取得()
        if sounddevice is None:
            logger.warning("sounddevice が未導入のためマイク開始できません")
            return False
        with self.lock:
            if self.is_recording:
                return True
            try:
                self.audio_input_started = False
                self.input_stream = sounddevice.RawInputStream(
                    samplerate=self.sample_rate,
                    blocksize=INPUT_AUDIO_BLOCK_SIZE,
                    channels=1,
                    dtype="int16",
                    callback=self._音声コールバック,
                )
                self.input_stream.start()
                self.is_recording = True
                logger.info("マイク入力を開始しました: rate=%s block=%s", self.sample_rate, INPUT_AUDIO_BLOCK_SIZE)
                return True
            except Exception:
                self.input_stream = None
                self.is_recording = False
                logger.exception("マイク入力の開始に失敗しました")
                return False

    def 停止(self) -> None:
        with self.lock:
            stream = self.input_stream
            self.input_stream = None
            self.audio_input_started = False
            self.is_recording = False
        if stream is not None:
            try:
                stream.stop()
            except Exception:
                pass
            try:
                stream.close()
            except Exception:
                pass
        logger.info("マイク入力を停止しました")

    def _音声コールバック(self, indata, _frames, _time_info, status) -> None:
        if status:
            logger.warning("マイク入力状態: %s", status)
        audio_bytes = bytes(indata)
        if not audio_bytes:
            return
        if not self.audio_input_started:
            self.audio_input_started = True
            self.connector.JSONを送信(
                "audio",
                {
                    "セッションID": self.auth_session.user_id,
                    "チャンネル": "audio",
                    "メッセージ識別": "cancel_audio",
                    "メッセージ内容": None,
                    "ファイル名": None,
                    "サムネイル画像": None,
                },
            )
        self.connector.JSONを送信(
            "audio",
            {
                "セッションID": self.auth_session.user_id,
                "チャンネル": "audio",
                "メッセージ識別": "input_audio",
                "メッセージ内容": "audio/pcm",
                "ファイル名": base64.b64encode(audio_bytes).decode("ascii"),
                "サムネイル画像": None,
            },
        )
