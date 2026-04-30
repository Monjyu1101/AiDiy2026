"""AiDiy Hermes media tools.

OpenAI の画像生成 API を提供する。
API キーは backend_server/_config/AiDiy_key.json の openai_key_id を読む。
"""

import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from openai import OpenAI

from tools.registry import registry, tool_error, tool_result


_AIDIY_KEY_JSON = Path(__file__).resolve().parents[2] / "backend_server" / "_config" / "AiDiy_key.json"
_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "temp" / "media"


def _load_aidiy_config() -> Dict[str, Any]:
    try:
        with open(_AIDIY_KEY_JSON, "r", encoding="utf-8-sig") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _valid_key(value: str) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not value.strip().startswith("<")


def _check_openai_key() -> bool:
    return _valid_key(_load_aidiy_config().get("openai_key_id", ""))


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _handle_image_generate(args: Dict[str, Any], **_kw) -> str:
    prompt = str(args.get("prompt") or "").strip()
    if not prompt:
        return tool_error("prompt is required")

    cfg = _load_aidiy_config()
    api_key = cfg.get("openai_key_id", "")
    if not _valid_key(api_key):
        return tool_error("openai_key_id is not configured in AiDiy_key.json")

    model = str(args.get("model") or "gpt-image-1").strip()
    size = str(args.get("size") or "1024x1024").strip()
    quality = str(args.get("quality") or "auto").strip()
    output_format = str(args.get("format") or "png").strip().lower()
    if output_format not in {"png", "jpeg", "webp"}:
        return tool_error("format must be one of: png, jpeg, webp")

    output_path = str(args.get("output_path") or "").strip()
    if output_path:
        path = Path(output_path).expanduser().resolve()
    else:
        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        path = (_OUTPUT_DIR / f"image_{_timestamp()}.{output_format}").resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        client = OpenAI(api_key=api_key.strip())
        response = client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            quality=quality,
            output_format=output_format,
            n=1,
        )
        item = response.data[0]
        b64_json = getattr(item, "b64_json", None)
        if not b64_json:
            return tool_error("image response did not include b64_json")
        path.write_bytes(base64.b64decode(b64_json))
        return tool_result(success=True, path=str(path), model=model, size=size, format=output_format)
    except Exception as exc:
        return tool_error(f"image generation failed: {exc}")


IMAGE_GENERATE_SCHEMA = {
    "description": "Generate an image file using the OpenAI image API configured in AiDiy_key.json.",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Image prompt."},
            "model": {"type": "string", "default": "gpt-image-1"},
            "size": {"type": "string", "default": "1024x1024"},
            "quality": {"type": "string", "default": "auto"},
            "format": {"type": "string", "enum": ["png", "jpeg", "webp"], "default": "png"},
            "output_path": {"type": "string", "description": "Optional output file path."},
        },
        "required": ["prompt"],
    },
}


registry.register(
    name="image_generate",
    toolset="image_gen",
    schema=IMAGE_GENERATE_SCHEMA,
    handler=_handle_image_generate,
    check_fn=_check_openai_key,
    requires_env=["openai_key_id"],
    description="画像を生成する",
)
