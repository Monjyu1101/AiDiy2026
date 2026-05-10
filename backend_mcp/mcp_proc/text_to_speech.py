# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
テキスト音声合成モジュール

テキストを受け取り、MP3 音声データを合成する。
対応 provider: edge, openai, gemini, freeai
"""

import asyncio
import base64
import json
import os
import re
import shutil
import struct
import subprocess
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


class TextToSpeechError(Exception):
    """テキスト音声合成エラー"""
    pass


class TextToSpeech:
    """
    テキスト音声合成クラス

    provider:
        "auto"   — edge（デフォルト、無料・API キー不要）
        "edge"   — Microsoft Edge ニューラル TTS
        "gemini" — Google Gemini TTS（GEMINI_API_KEY が必要）
        "freeai" — FreeAI TTS（FREEAI_API_KEY が必要、実体は Gemini）
        "openai" — OpenAI TTS（OPENAI_API_KEY が必要）
    """

    DEFAULT_OUTPUT_DIR = "backend_server/temp/output"

    # デフォルト音声（provider 別）
    DEFAULT_VOICES = {
        "edge":   "ja-JP-NanamiNeural",
        "openai": "marin",
        "gemini": "Zephyr",
        "freeai": "Zephyr",
    }

    # OpenAI デフォルト
    DEFAULT_OPENAI_MODEL = "gpt-4o-mini-tts"
    DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"

    # Gemini デフォルト
    DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-preview-tts"
    DEFAULT_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    GEMINI_SAMPLE_RATE = 24000
    GEMINI_CHANNELS = 1
    GEMINI_SAMPLE_WIDTH = 2  # 16-bit PCM

    PROVIDER_KEYS = {
        "openai": "openai_key_id",
        "gemini": "gemini_key_id",
        "freeai": "freeai_key_id",
    }

    # AiDiy_key.json へのパス（backend_mcp 起点）
    _KEY_CONFIG_REL = "../backend_server/_config/AiDiy_key.json"
    _TTS_CONFIG_REL = "../backend_server/_config/aidiy_text_to_speech.json"

    # 読み上げ用の用語変換辞書。
    # 入力テキスト自体は変えず、音声合成へ渡す直前だけ適用する。
    DEFAULT_PRONUNCIATION_DICTIONARY = [
        ("AiDiy", "アイディー"),
        ("aidiy", "アイディー"),
        ("横展開", "よこてんかい"),
        ("FastAPI", "ファスト エーピーアイ"),
        ("PostgreSQL", "ポストグレス キューエル"),
        ("OpenAI", "オープン エーアイ"),
        ("OpenCode", "オープンコード"),
        ("Code CLI", "コード シーエルアイ"),
        ("WebSocket", "ウェブソケット"),
        ("GitHub", "ギットハブ"),
        ("SQLite", "エスキューライト"),
        ("Claude", "クロード"),
        ("Copilot", "コパイロット"),
        ("Codex", "コーデックス"),
        ("Gemini", "ジェミニ"),
        ("Hermes", "ヘルメス"),
        ("Electron", "エレクトロン"),
        ("backend", "バックエンド"),
        ("frontend", "フロントエンド"),
        ("Vite", "ヴィート"),
        ("Vue", "ビュー"),
        ("JWT", "ジェイ ダブリュー ティー"),
        ("JSON", "ジェイソン"),
        ("HTML", "エイチティーエムエル"),
        ("HTTP", "エイチティーティーピー"),
        ("URL", "ユーアールエル"),
        ("API", "エーピーアイ"),
        ("CLI", "シーエルアイ"),
        ("MCP", "エムシーピー"),
        ("TTS", "ティーティーエス"),
        ("STT", "エスティーティー"),
        ("MP3", "エムピースリー"),
        ("DB", "データベース"),
        ("UI", "ユーアイ"),
        ("AI", "エーアイ"),
        ("VRMA", "ブイアールエムエー"),
        ("VRM", "ブイアールエム"),
    ]

    # ------------------------------------------------------------------ #
    # API キー解決
    # ------------------------------------------------------------------ #

    @staticmethod
    def _is_valid_key(key: str) -> bool:
        """キーが有効か判定（空文字列 / '<' 始まりは無効）"""
        return bool(key) and not key.startswith("<")

    def _get_api_key(self, provider: str) -> Optional[str]:
        """AiDiy_key.json から API キーを取得する。
        無効なキーの場合は None を返す。
        """
        json_key = self.PROVIDER_KEYS.get(provider, "")
        key = self._read_key_from_config(json_key)
        if self._is_valid_key(key):
            return key
        return None

    def _read_key_from_config(self, key_name: str) -> str:
        """AiDiy_key.json から指定キーを読み出す"""
        config_path = Path(__file__).resolve().parent.parent / self._KEY_CONFIG_REL
        try:
            if not config_path.exists():
                return ""
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            value = data.get(key_name, "")
            return value.strip() if isinstance(value, str) else ""
        except (json.JSONDecodeError, OSError):
            return ""

    # ------------------------------------------------------------------ #
    # TTS 設定ファイル
    # ------------------------------------------------------------------ #

    def _tts_config_path(self) -> Path:
        return Path(__file__).resolve().parent.parent / self._TTS_CONFIG_REL

    def _default_pronunciation_config(self) -> dict:
        return {
            "version": 1,
            "description": (
                "aidiy_text_to_speech の読み上げ用変換辞書。"
                " speech_text の原文は変えず、音声合成へ渡す直前だけ from を to に変換する。"
            ),
            "pronunciation_dictionary": [
                {"from": source, "to": target}
                for source, target in self.DEFAULT_PRONUNCIATION_DICTIONARY
            ],
        }

    def _write_default_tts_config(self, config_path: Path) -> None:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(self._default_pronunciation_config(), f, ensure_ascii=False, indent=2)
            f.write("\n")

    def _load_pronunciation_dictionary(self) -> list[tuple[str, str]]:
        """設定ファイルがあればそれを使い、なければデフォルトを書き出して使う"""
        config_path = self._tts_config_path()
        if not config_path.exists():
            self._write_default_tts_config(config_path)
            return list(self.DEFAULT_PRONUNCIATION_DICTIONARY)

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise TextToSpeechError(
                f"TTS 設定ファイルの読み込みに失敗しました: {config_path} ({e})"
            ) from e

        raw_items = data.get("pronunciation_dictionary", [])
        if not isinstance(raw_items, list):
            raise TextToSpeechError(
                f"TTS 設定ファイルの pronunciation_dictionary は配列で指定してください: {config_path}"
            )

        dictionary: list[tuple[str, str]] = []
        for index, item in enumerate(raw_items, 1):
            if isinstance(item, dict):
                source = item.get("from", "")
                target = item.get("to", "")
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                source, target = item
            else:
                raise TextToSpeechError(
                    f"TTS 変換辞書の {index} 件目は {{\"from\": ..., \"to\": ...}} 形式で指定してください"
                )

            if not isinstance(source, str) or not isinstance(target, str):
                raise TextToSpeechError(
                    f"TTS 変換辞書の {index} 件目は文字列で指定してください"
                )
            source = source.strip()
            target = target.strip()
            if source and target:
                dictionary.append((source, target))

        return dictionary

    # ------------------------------------------------------------------ #
    # description 動的生成
    # ------------------------------------------------------------------ #

    PROVIDER_LIST = ["edge", "gemini", "freeai", "openai"]

    def get_description(self) -> str:
        available = []
        unavailable = []
        for p in self.PROVIDER_LIST:
            if p == "edge" or self._get_api_key(p) is not None:
                available.append(p)
            else:
                unavailable.append(p)
        desc = f"テキストを音声（MP3）に変換する。利用可能: {', '.join(available)}。"
        if unavailable:
            desc += f" 利用不可: {', '.join(unavailable)}（API キー未設定）。"
        desc += " AiDiy、DB、API、MCP などのシステム用語は backend_server/config/aidiy_text_to_speech.json の読み上げ用辞書で自動変換する。"
        return desc

    # ------------------------------------------------------------------ #
    # 読み上げテキスト正規化
    # ------------------------------------------------------------------ #

    def normalize_for_speech(self, text: str) -> tuple[str, list[dict]]:
        """TTS に渡す直前の読み上げ用テキストへ変換する"""
        normalized = text
        applied: list[dict] = []

        for source, target in self._load_pronunciation_dictionary():
            if re.search(r"^[A-Za-z0-9 +._-]+$", source):
                pattern = re.compile(
                    rf"(?<![A-Za-z0-9_]){re.escape(source)}(?![A-Za-z0-9_])"
                )
                normalized, count = pattern.subn(target, normalized)
            else:
                count = normalized.count(source)
                if count:
                    normalized = normalized.replace(source, target)

            if count:
                applied.append({
                    "from": source,
                    "to": target,
                    "count": count,
                })

        return normalized, applied
    # ------------------------------------------------------------------ #
    # 音声合成（dispatch）
    # ------------------------------------------------------------------ #

    def synthesize(
        self,
        speech_text: str,
        language: str = "ja",
        provider: str = "auto",
        model: str = "auto",
        voice: str = "auto",
    ) -> tuple[bytes, dict]:
        """
        テキストから音声を合成する。
        指定 provider のキーが無効な場合は自動で edge にフォールバックする。

        Returns:
            (mp3_bytes, info_dict)
        """
        if not speech_text or not speech_text.strip():
            raise TextToSpeechError("speech_text は必須です")

        normalized_text, replacements = self.normalize_for_speech(speech_text)
        requested = self._normalize_provider(provider)
        model = model.strip().lower()
        language = language.strip().lower()

        # キーが必要な provider でキーが無効 → edge にフォールバック
        used = requested
        if requested in ("openai", "gemini", "freeai"):
            if self._get_api_key(requested) is None:
                used = "edge"

        voice = self._resolve_voice(voice, used)

        try:
            if used == "edge":
                mp3_bytes = self._synthesize_edge(normalized_text, voice)
            elif used == "gemini":
                mp3_bytes = self._synthesize_gemini(normalized_text, voice, model, used)
            elif used == "freeai":
                mp3_bytes = self._synthesize_gemini(normalized_text, voice, model, used)
            elif used == "openai":
                mp3_bytes = self._synthesize_openai(normalized_text, voice, model)
            else:
                raise TextToSpeechError(f"未対応の provider です: '{used}'")
        except Exception:
            if used == "edge":
                raise
            used = "edge"
            voice = self._resolve_voice("auto", used)
            mp3_bytes = self._synthesize_edge(normalized_text, voice)

        info = {
            "requested_provider": requested,
            "used_provider": used,
            "model": model if model != "auto" else self._default_model(used),
            "voice": voice,
            "language": language,
            "speech_text": normalized_text,
            "original_speech_text": speech_text,
            "pronunciation_replacements": replacements,
            "mp3_bytes_length": len(mp3_bytes),
        }
        return mp3_bytes, info

    # ------------------------------------------------------------------ #
    # Edge TTS
    # ------------------------------------------------------------------ #

    def _synthesize_edge(self, text: str, voice: str) -> bytes:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            asyncio.run(communicate.save(tmp_path))
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    # ------------------------------------------------------------------ #
    # OpenAI TTS
    # ------------------------------------------------------------------ #

    def _synthesize_openai(self, text: str, voice: str, model: str) -> bytes:
        try:
            from openai import OpenAI
        except ImportError:
            raise TextToSpeechError(
                "openai パッケージがインストールされていません。pip install openai で導入してください。"
            )
        api_key = self._get_api_key("openai") or ""

        if model == "auto":
            model = self.DEFAULT_OPENAI_MODEL

        client = OpenAI(api_key=api_key)
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name
            response = client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                response_format="mp3",
                extra_headers={"x-idempotency-key": str(uuid.uuid4())},
            )
            response.stream_to_file(tmp_path)
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            close = getattr(client, "close", None)
            if callable(close):
                close()
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    # ------------------------------------------------------------------ #
    # Gemini / FreeAI TTS
    # ------------------------------------------------------------------ #

    def _synthesize_gemini(self, text: str, voice: str, model: str, provider: str) -> bytes:
        import requests
        api_key = self._get_api_key(provider) or ""

        if model == "auto":
            model = self.DEFAULT_GEMINI_MODEL

        # Gemini の場合は GEMINI_BASE_URL、FreeAI は別途環境変数 or デフォルト
        if provider == "freeai":
            base_url = os.environ.get("FREEAI_BASE_URL", self.DEFAULT_GEMINI_BASE_URL)
        else:
            base_url = os.environ.get("GEMINI_BASE_URL", self.DEFAULT_GEMINI_BASE_URL)
        base_url = base_url.strip().rstrip("/")

        # Gemini TTS は音声生成用の指示が必要
        tts_prompt = (
            f"Generate spoken audio of the following text exactly as written. "
            f"Do not add any commentary, explanations, or extra words. "
            f"Just speak this text naturally: {text}"
        )

        payload = {
            "contents": [{"parts": [{"text": tts_prompt}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {"voiceName": voice},
                    },
                },
            },
        }

        endpoint = f"{base_url}/models/{model}:generateContent"
        resp = requests.post(
            endpoint,
            params={"key": api_key},
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )

        if resp.status_code != 200:
            try:
                err = resp.json().get("error", {})
                detail = err.get("message", resp.text[:300])
            except Exception:
                detail = resp.text[:300]
            raise TextToSpeechError(
                f"Gemini API エラー (HTTP {resp.status_code}): {detail}"
            )

        try:
            data = resp.json()
            parts = data["candidates"][0]["content"]["parts"]
            audio_part = next(
                (p for p in parts if "inlineData" in p or "inline_data" in p), None
            )
            if audio_part is None:
                raise TextToSpeechError("Gemini レスポンスに音声データが含まれていません")
            inline = audio_part.get("inlineData") or audio_part.get("inline_data") or {}
            audio_b64 = inline.get("data", "")
        except (KeyError, IndexError, TypeError) as e:
            raise TextToSpeechError(f"Gemini レスポンスの解析に失敗: {e}")

        if not audio_b64:
            raise TextToSpeechError("Gemini が空の音声データを返しました")

        pcm_bytes = base64.b64decode(audio_b64)
        wav_bytes = self._pcm_to_wav(pcm_bytes)

        return self._wav_to_mp3(wav_bytes)

    # ------------------------------------------------------------------ #
    # PCM / WAV / MP3 変換
    # ------------------------------------------------------------------ #

    def _pcm_to_wav(self, pcm_bytes: bytes) -> bytes:
        """16kHz 16bit モノラル PCM を WAV に変換"""
        sample_rate = self.GEMINI_SAMPLE_RATE
        channels = self.GEMINI_CHANNELS
        sample_width = self.GEMINI_SAMPLE_WIDTH
        byte_rate = sample_rate * channels * sample_width
        block_align = channels * sample_width
        data_size = len(pcm_bytes)

        fmt_chunk = struct.pack(
            "<4sIHHIIHH",
            b"fmt ",
            16,
            1,
            channels,
            sample_rate,
            byte_rate,
            block_align,
            sample_width * 8,
        )
        data_header = struct.pack("<4sI", b"data", data_size)
        riff_size = 4 + len(fmt_chunk) + len(data_header) + data_size
        riff_header = struct.pack("<4sI4s", b"RIFF", riff_size, b"WAVE")
        return riff_header + fmt_chunk + data_header + pcm_bytes

    def _wav_to_mp3(self, wav_bytes: bytes) -> bytes:
        """ffmpeg で WAV → MP3 変換。ffmpeg 不在時は WAV のまま返す"""
        ffmpeg = shutil.which("ffmpeg")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(wav_bytes)
            wav_path = tmp.name
        mp3_path = wav_path.rsplit(".", 1)[0] + ".mp3"
        try:
            if ffmpeg:
                subprocess.run(
                    [ffmpeg, "-i", wav_path, "-y", "-loglevel", "error", mp3_path],
                    check=True, timeout=30,
                )
                if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
                    with open(mp3_path, "rb") as f:
                        return f.read()
            # ffmpeg 不在 → WAV のまま返す
            return wav_bytes
        finally:
            for p in (wav_path, mp3_path):
                try:
                    os.remove(p)
                except OSError:
                    pass

    # ------------------------------------------------------------------ #
    # ローカル再生
    # ------------------------------------------------------------------ #

    def play_mp3(self, mp3_bytes: bytes, speed: float = 1.0) -> bool:
        if not mp3_bytes:
            return False
        mp3_path = None
        try:
            fd, mp3_path = tempfile.mkstemp(suffix=".mp3")
            os.write(fd, mp3_bytes)
            os.close(fd)

            if speed != 1.0 and shutil.which("ffmpeg"):
                mp3_path = self._tempo_mp3(mp3_path, speed)

            self._playsound(mp3_path)
            return True
        except Exception:
            return False
        finally:
            if mp3_path:
                try:
                    os.remove(mp3_path)
                except OSError:
                    pass

    def _tempo_mp3(self, path: str, speed: float) -> str:
        """ffmpeg atempo で速度調整した一時ファイルを作ってパスを返す"""
        out_path = path.rsplit(".", 1)[0] + "_t.mp3"
        subprocess.run(
            [shutil.which("ffmpeg"), "-i", path, "-af", f"atempo={speed}",
             "-y", "-loglevel", "error", out_path],
            check=True, timeout=30,
        )
        return out_path

    @staticmethod
    def _playsound(path: str) -> None:
        """playsound 風の最小実装。Windows: winmm, macOS: afplay, Linux: gst"""
        import platform
        pf = platform.system()
        if pf == "Windows":
            import ctypes
            ctypes.windll.winmm.mciSendStringW(
                f'open "{path}" type mpegvideo alias _tts', None, 0, None)
            ctypes.windll.winmm.mciSendStringW(
                'play _tts wait', None, 0, None)
            ctypes.windll.winmm.mciSendStringW(
                'close _tts', None, 0, None)
        elif pf == "Darwin":
            subprocess.run(["afplay", path], timeout=120)
        else:
            subprocess.run(["gst-launch-1.0", "playbin", f"uri=file://{path}"],
                           timeout=60, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # ------------------------------------------------------------------ #
    # 出力
    # ------------------------------------------------------------------ #

    def to_base64(
        self,
        mp3_bytes: bytes,
        save_path: Optional[str] = None,
    ) -> str:
        """MP3 バイト列を Base64 文字列で返す。

        Args:
            mp3_bytes: MP3 バイナリデータ
            save_path: 保存先。フォルダ指定なら yyyymmdd.hhmmss.mp3 で保存。
                       ファイル指定なら指定ファイルに上書き保存。省略時は保存しない。
        """
        if save_path:
            if os.path.isdir(save_path) or save_path.endswith(("/", "\\")):
                os.makedirs(save_path, exist_ok=True)
                fname = datetime.now().strftime("%Y%m%d.%H%M%S") + ".mp3"
                dest = os.path.join(save_path, fname)
            else:
                dest = save_path
                parent = os.path.dirname(os.path.abspath(dest))
                if parent:
                    os.makedirs(parent, exist_ok=True)
            with open(dest, "wb") as f:
                f.write(mp3_bytes)

        return base64.b64encode(mp3_bytes).decode("ascii")

    # ------------------------------------------------------------------ #
    # 内部ヘルパー
    # ------------------------------------------------------------------ #

    def _normalize_provider(self, provider: str) -> str:
        p = provider.strip().lower()
        if p == "auto":
            return "edge"
        if p in ("edge", "openai", "gemini", "freeai"):
            return p
        raise TextToSpeechError(
            f"未対応の provider です: '{provider}'（edge / openai / gemini / freeai）"
        )

    def _resolve_voice(self, voice: str, provider: str) -> str:
        v = voice.strip()
        if v.lower() == "auto":
            return self.DEFAULT_VOICES.get(provider, self.DEFAULT_VOICES["edge"])
        return v

    def _default_model(self, provider: str) -> str:
        if provider == "openai":
            return self.DEFAULT_OPENAI_MODEL
        elif provider in ("gemini", "freeai"):
            return self.DEFAULT_GEMINI_MODEL
        return "auto"
