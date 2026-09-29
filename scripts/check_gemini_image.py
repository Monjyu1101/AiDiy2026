#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gemini 画像モデルの単独呼び出しを確認する。

実行: backend_server/.venv/bin/python scripts/check_gemini_image.py
API キーは GEMINI_API_KEY または _config/AiDiy_key.json から読む。
"""

import argparse
import json
import os
from pathlib import Path

from google import genai
from google.genai import types


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gemini-3.1-flash-image")
    parser.add_argument("--prompt", default="かわいい猫の画像を作ってください。")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "backend_server" / "temp" / "output" / "gemini_cat_check.png",
    )
    args = parser.parse_args()

    config_file = ROOT / "_config" / "AiDiy_key.json"
    config = json.loads(config_file.read_text(encoding="utf-8-sig")) if config_file.exists() else {}
    api_key = os.environ.get("GEMINI_API_KEY") or config.get("gemini_key_id", "")
    if not api_key or api_key.startswith("<"):
        raise SystemExit("Gemini API キーが設定されていません。")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=args.model,
        contents=args.prompt,
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )

    image_count = 0
    for part in response.parts or []:
        if part.text:
            print(f"TEXT: {part.text[:300]}")
        if part.inline_data and part.inline_data.data:
            mime_type = part.inline_data.mime_type or "image/png"
            extension = {
                "image/png": ".png",
                "image/jpeg": ".jpg",
                "image/webp": ".webp",
            }.get(mime_type)
            if extension is None:
                raise RuntimeError(f"未対応の画像形式: {mime_type}")
            output = args.output.with_suffix(extension)
            if image_count:
                output = output.with_name(f"{output.stem}_{image_count + 1}{extension}")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(part.inline_data.data)
            image_count += 1
            print(f"IMAGE: {output} ({mime_type}, {output.stat().st_size} bytes)")

    if not image_count:
        finish_reason = response.candidates[0].finish_reason if response.candidates else None
        raise RuntimeError(f"画像が返りませんでした。finish_reason={finish_reason}")


if __name__ == "__main__":
    main()
