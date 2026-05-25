# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# See LICENSE for full terms.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""image_generation テスト — 直接実行 + HTTP POST API"""

import base64
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from urllib import error, request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image as PILImage
from mcp_proc.image_generation import ImageGeneration, ImageGenerationError


BASE_URL = os.environ.get("AIDIY_MCP_BASE_URL", "http://localhost:8095").rstrip("/")
HTTP_TIMEOUT = float(os.environ.get("AIDIY_MCP_EXTERNAL_TIMEOUT", "1200"))
POST_SAVE_DIR = Path(__file__).resolve().parent / "temp" / "post_image"


def _post_json(path: str, payload: dict, timeout: float | None = None) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        f"{BASE_URL}{path}",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with request.urlopen(req, timeout=timeout or HTTP_TIMEOUT) as res:
        return json.loads(res.read().decode("utf-8", errors="replace"))


def _assert_no_error(label: str, result: dict) -> None:
    if "error" in result:
        raise AssertionError(f"{label}: {result['error']}")


def _post_json_retry(label: str, path: str, payload: dict, attempts: int = 3) -> dict:
    result = {}
    for i in range(1, attempts + 1):
        result = _post_json(path, payload)
        error_text = str(result.get("error", ""))
        if not error_text:
            return result
        if not any(s in error_text for s in ("503", "UNAVAILABLE", "high demand")):
            return result
        if i < attempts:
            wait_sec = 30 * i
            print(f"  RETRY {label}: {error_text[:120]}... wait {wait_sec}s")
            time.sleep(wait_sec)
    return result


def _write_base64(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(data))


def test_post_api() -> None:
    """HTTP POST API で直接実行と同じ画像生成/編集フローを確認する。"""
    POST_SAVE_DIR.mkdir(parents=True, exist_ok=True)
    freeai_path = POST_SAVE_DIR / "image_freeai.png"
    resized_path = POST_SAVE_DIR / "image_freeai_1024.png"
    openai_path = POST_SAVE_DIR / "image_openai_edit.png"
    gemini_path = POST_SAVE_DIR / "image_gemini_edit.png"

    print()
    print("=" * 60)
    print("HTTP POST Test 1: FreeAI で画像生成")
    print("=" * 60)

    img1 = _post_json_retry(
        "POST image freeai",
        "/aidiy_image_generation/generate",
        {
            "prompt": "森でたたずむオオカミ",
            "provider": "freeai",
            "size": "auto",
            "save_path": str(freeai_path),
        },
    )
    _assert_no_error("POST image freeai", img1)
    _write_base64(freeai_path, img1["data"])
    with PILImage.open(freeai_path) as image:
        image.resize((1024, 1024), PILImage.LANCZOS).save(resized_path, format="PNG")
    print(f"  saved  = {freeai_path}")
    print(f"  base64 = {len(img1['data'])} chars")

    print()
    print("=" * 60)
    print("HTTP POST Test 2: OpenAI で調整")
    print("=" * 60)

    img2 = _post_json_retry(
        "POST image openai edit",
        "/aidiy_image_generation/generate",
        {
            "prompt": "背景は変えずに、オオカミを子猫に変更してください",
            "provider": "openai",
            "model": "gpt-image-2",
            "size": "auto",
            "quality": "auto",
            "original_path": str(resized_path),
            "save_path": str(openai_path),
        },
    )
    _assert_no_error("POST image openai edit", img2)
    _write_base64(openai_path, img2["data"])
    print(f"  saved  = {openai_path}")
    print(f"  base64 = {len(img2['data'])} chars")

    print()
    print("=" * 60)
    print("HTTP POST Test 3: Gemini で背景変更")
    print("=" * 60)

    img3 = _post_json_retry(
        "POST image gemini edit",
        "/aidiy_image_generation/generate",
        {
            "prompt": "猫は変えずに、背景を住宅地に変更してください",
            "provider": "gemini",
            "size": "1024x1024",
            "original_path": str(openai_path),
            "save_path": str(gemini_path),
        },
    )
    _assert_no_error("POST image gemini edit", img3)
    _write_base64(gemini_path, img3["data"])
    print(f"  saved  = {gemini_path}")
    print(f"  base64 = {len(img3['data'])} chars")


def main():
    ig = ImageGeneration()

    # ------------------------------------------------------------------ #
    # キー確認
    # ------------------------------------------------------------------ #
    freeai_key = ig._get_freeai_api_key()
    openai_key = ig._get_openai_api_key()

    if not freeai_key:
        print("SKIP: FreeAI API キーが設定されていません")
    if not openai_key:
        print("SKIP: OpenAI API キーが設定されていません")
    if not freeai_key or not openai_key:
        return

    # ------------------------------------------------------------------ #
    # Test 1: FreeAI で生成
    # ------------------------------------------------------------------ #
    print("=" * 60)
    print("Test 1: FreeAI で画像生成")
    print("=" * 60)

    img1, info1 = ig.generate(
        prompt="森でたたずむオオカミ",
        provider="freeai",
        size="auto",
    )
    b64_1 = ig.to_base64(img1, "png", 85)

    print(f"  provider= {info1['provider']}")
    print(f"  model   = {info1['model']}")
    print(f"  size    = {info1['width']}x{info1['height']}")
    print(f"  aspect  = {info1['aspect_ratio']}")
    print(f"  img_size= {info1['image_size']}")
    print(f"  engine  = {info1['engine_note']}")
    print(f"  base64  = {len(b64_1)} chars")

    # ------------------------------------------------------------------ #
    # Test 2: 512x512 → 1024x1024 にリサイズ
    # ------------------------------------------------------------------ #
    print()
    print("=" * 60)
    print("Test 2: 512x512 → 1024x1024 にリサイズ")
    print("=" * 60)

    img1_resized = img1.resize((1024, 1024), PILImage.LANCZOS)
    b64_1r = ig.to_base64(img1_resized, "png", 85)

    # Test 3 への橋渡し用一時ファイル
    tmp_resized = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp_resized_path = tmp_resized.name
    tmp_resized.close()
    img1_resized.save(tmp_resized_path, format="PNG")

    print(f"  before  = {img1.width}x{img1.height}")
    print(f"  after   = {img1_resized.width}x{img1_resized.height}")
    print(f"  base64  = {len(b64_1r)} chars")

    # ------------------------------------------------------------------ #
    # Test 3: OpenAI で調整（リサイズ後画像を元に）
    # ------------------------------------------------------------------ #
    print()
    print("=" * 60)
    print("Test 3: OpenAI で調整（リサイズ画像を元に）")
    print("=" * 60)

    img2, info2 = ig.generate(
        prompt="背景は変えずに、オオカミを子猫に変更してください",
        provider="openai",
        model="gpt-image-2",
        size="auto",
        quality="auto",
        original_path=tmp_resized_path,
    )
    b64_2 = ig.to_base64(img2, "png", 85)

    # Test 4 への橋渡し用一時ファイル
    tmp_kitten = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp_kitten_path = tmp_kitten.name
    tmp_kitten.close()
    img2.save(tmp_kitten_path, format="PNG")

    print(f"  provider= {info2['provider']}")
    print(f"  model   = {info2['model']}")
    print(f"  size    = {info2['width']}x{info2['height']}")
    print(f"  quality = {info2['quality']}")
    print(f"  engine  = {info2['engine_note']}")
    print(f"  base64  = {len(b64_2)} chars")

    # ------------------------------------------------------------------ #
    # Test 4: Gemini で背景変更（猫はそのまま、背景→住宅地）
    # ------------------------------------------------------------------ #
    print()
    print("=" * 60)
    print("Test 4: Gemini で背景変更（猫は変えずに背景を住宅地に）")
    print("=" * 60)

    img3, info3 = ig.generate(
        prompt="猫は変えずに、背景を住宅地に変更してください",
        provider="gemini",
        size="1024x1024",
        original_path=tmp_kitten_path,
    )
    b64_3 = ig.to_base64(img3, "png", 85)

    print(f"  provider= {info3['provider']}")
    print(f"  model   = {info3['model']}")
    print(f"  size    = {info3['width']}x{info3['height']}")
    print(f"  aspect  = {info3['aspect_ratio']}")
    print(f"  img_size= {info3['image_size']}")
    print(f"  engine  = {info3['engine_note']}")
    print(f"  base64  = {len(b64_3)} chars")

    # 一時ファイルを削除
    os.unlink(tmp_resized_path)
    os.unlink(tmp_kitten_path)

    # ------------------------------------------------------------------ #
    # 結果
    # ------------------------------------------------------------------ #
    print()
    print("=" * 60)
    print("結果")
    print("=" * 60)
    print(f"  [1] FreeAI 生成  (512x512)   : base64 {len(b64_1)} chars")
    print(f"  [2] リサイズ (1024x1024)     : base64 {len(b64_1r)} chars")
    print(f"  [3] OpenAI 調整 (1024x1024)  : base64 {len(b64_2)} chars")
    print(f"  [4] Gemini 背景変更 (住宅地) : base64 {len(b64_3)} chars")

    test_post_api()

    print()
    print("OK")


if __name__ == "__main__":
    main()
