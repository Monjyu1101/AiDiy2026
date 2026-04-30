"""AiDiy Hermes vision tool."""

import base64
import json
from pathlib import Path
from typing import Any, Dict

from openai import OpenAI

from tools.registry import registry, tool_error, tool_result


_AIDIY_KEY_JSON = Path(__file__).resolve().parents[2] / "backend_server" / "_config" / "AiDiy_key.json"


def _load_aidiy_config() -> Dict[str, Any]:
    try:
        with open(_AIDIY_KEY_JSON, "r", encoding="utf-8-sig") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _valid_key(value: str) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not value.strip().startswith("<")


def _check_vision_requirements() -> bool:
    return _valid_key(_load_aidiy_config().get("openai_key_id", ""))


def _image_data_url(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".") or "png"
    mime = "jpeg" if suffix in {"jpg", "jpeg"} else suffix
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/{mime};base64,{data}"


def _handle_vision_analyze(args: Dict[str, Any], **_kw) -> str:
    image_path = str(args.get("image_path") or "").strip()
    if not image_path:
        return tool_error("image_path is required")
    path = Path(image_path).expanduser().resolve()
    if not path.exists() or not path.is_file():
        return tool_error(f"image not found: {path}")

    prompt = str(args.get("prompt") or "Describe this image in detail.").strip()
    model = str(args.get("model") or "gpt-5.2").strip()
    cfg = _load_aidiy_config()
    api_key = cfg.get("openai_key_id", "")
    if not _valid_key(api_key):
        return tool_error("openai_key_id is not configured in AiDiy_key.json")

    try:
        client = OpenAI(api_key=api_key.strip())
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": _image_data_url(path)}},
                    ],
                }
            ],
        )
        text = response.choices[0].message.content or ""
        return tool_result(success=True, analysis=text, image_path=str(path), model=model)
    except Exception as exc:
        return tool_error(f"vision analysis failed: {exc}")


VISION_ANALYZE_SCHEMA = {
    "description": "Analyze a local image using an OpenAI vision-capable model configured in AiDiy_key.json.",
    "parameters": {
        "type": "object",
        "properties": {
            "image_path": {"type": "string", "description": "Local image path to analyze."},
            "prompt": {"type": "string", "description": "Question or instruction for the image."},
            "model": {"type": "string", "default": "gpt-5.2"},
        },
        "required": ["image_path"],
    },
}


registry.register(
    name="vision_analyze",
    toolset="vision",
    schema=VISION_ANALYZE_SCHEMA,
    handler=_handle_vision_analyze,
    check_fn=_check_vision_requirements,
    requires_env=["openai_key_id"],
    description="ローカル画像を解析する",
)
