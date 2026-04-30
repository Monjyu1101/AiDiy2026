"""AiDiy Hermes TTS tool.

OpenAI の音声生成 API を使い、テキストを音声ファイルに変換する。
API キーは backend_server/_config/AiDiy_key.json の openai_key_id を読む。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from openai import OpenAI

from tools.registry import registry, tool_error, tool_result


_AIDIY_KEY_JSON = Path(__file__).resolve().parents[2] / "backend_server" / "_config" / "AiDiy_key.json"
_DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "temp" / "tts"


def _load_aidiy_config() -> Dict[str, Any]:
    try:
        with open(_AIDIY_KEY_JSON, "r", encoding="utf-8-sig") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _valid_key(value: str) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not value.strip().startswith("<")


def _check_tts_requirements() -> bool:
    cfg = _load_aidiy_config()
    return _valid_key(cfg.get("openai_key_id", ""))


def _handle_text_to_speech(args: Dict[str, Any], **_kw) -> str:
    text = str(args.get("text") or "").strip()
    if not text:
        return tool_error("text is required")

    cfg = _load_aidiy_config()
    api_key = cfg.get("openai_key_id", "")
    if not _valid_key(api_key):
        return tool_error("openai_key_id is not configured in AiDiy_key.json")

    model = str(args.get("model") or "gpt-4o-mini-tts").strip()
    voice = str(args.get("voice") or "alloy").strip()
    response_format = str(args.get("format") or "mp3").strip().lower()
    if response_format not in {"mp3", "opus", "aac", "flac", "wav", "pcm"}:
        return tool_error("format must be one of: mp3, opus, aac, flac, wav, pcm")

    output_path = str(args.get("output_path") or "").strip()
    if output_path:
        path = Path(output_path).expanduser().resolve()
    else:
        _DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = (_DEFAULT_OUTPUT_DIR / f"tts_{timestamp}.{response_format}").resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        client = OpenAI(api_key=api_key.strip())
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format=response_format,
        )
        response.write_to_file(path)
        return tool_result(success=True, path=str(path), model=model, voice=voice, format=response_format)
    except Exception as exc:
        return tool_error(f"TTS generation failed: {exc}")


TEXT_TO_SPEECH_SCHEMA = {
    "description": "Convert text to a local audio file using the OpenAI TTS API configured in AiDiy_key.json.",
    "parameters": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to synthesize.",
            },
            "voice": {
                "type": "string",
                "description": "Voice name, for example alloy, ash, ballad, coral, echo, fable, nova, onyx, sage, shimmer.",
                "default": "alloy",
            },
            "model": {
                "type": "string",
                "description": "TTS model name.",
                "default": "gpt-4o-mini-tts",
            },
            "format": {
                "type": "string",
                "description": "Output format.",
                "enum": ["mp3", "opus", "aac", "flac", "wav", "pcm"],
                "default": "mp3",
            },
            "output_path": {
                "type": "string",
                "description": "Optional output file path. If omitted, backend_hermes/temp/tts is used.",
            },
        },
        "required": ["text"],
    },
}


registry.register(
    name="text_to_speech",
    toolset="tts",
    schema=TEXT_TO_SPEECH_SCHEMA,
    handler=_handle_text_to_speech,
    check_fn=_check_tts_requirements,
    requires_env=["openai_key_id"],
    description="テキストを音声ファイルに変換する",
)
