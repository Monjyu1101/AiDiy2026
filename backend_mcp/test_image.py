# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# See LICENSE for full terms.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""image_generation テスト — freeai で生成 → openai で調整"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image as PILImage
from mcp_proc.image_generation import ImageGeneration, ImageGenerationError


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

    out_dir = os.path.join(os.path.dirname(__file__), "temp", "output")
    os.makedirs(out_dir, exist_ok=True)

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
    save1 = os.path.join(out_dir, "test_freeai_wolf.png")
    b64_1 = ig.to_base64(img1, "png", 85, save1)

    print(f"  provider= {info1['provider']}")
    print(f"  model   = {info1['model']}")
    print(f"  size    = {info1['width']}x{info1['height']}")
    print(f"  aspect  = {info1['aspect_ratio']}")
    print(f"  img_size= {info1['image_size']}")
    print(f"  engine  = {info1['engine_note']}")
    print(f"  base64  = {len(b64_1)} chars")
    print(f"  saved   = {save1}")

    # ------------------------------------------------------------------ #
    # Test 2: 512x512 → 1024x1024 にリサイズ
    # ------------------------------------------------------------------ #
    print()
    print("=" * 60)
    print("Test 2: 512x512 → 1024x1024 にリサイズ")
    print("=" * 60)

    img1_resized = img1.resize((1024, 1024), PILImage.LANCZOS)
    save1_resized = os.path.join(out_dir, "test_freeai_wolf_1024.png")
    b64_1r = ig.to_base64(img1_resized, "png", 85, save1_resized)

    print(f"  before  = {img1.width}x{img1.height}")
    print(f"  after   = {img1_resized.width}x{img1_resized.height}")
    print(f"  saved   = {save1_resized}")

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
        original_path=save1_resized,
    )
    save2 = os.path.join(out_dir, "test_openai_kitten.png")
    b64_2 = ig.to_base64(img2, "png", 85, save2)

    print(f"  provider= {info2['provider']}")
    print(f"  model   = {info2['model']}")
    print(f"  size    = {info2['width']}x{info2['height']}")
    print(f"  quality = {info2['quality']}")
    print(f"  engine  = {info2['engine_note']}")
    print(f"  base64  = {len(b64_2)} chars")
    print(f"  saved   = {save2}")

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
        original_path=save2,
    )
    save3 = os.path.join(out_dir, "test_gemini_kitten_residential.png")
    b64_3 = ig.to_base64(img3, "png", 85, save3)

    print(f"  provider= {info3['provider']}")
    print(f"  model   = {info3['model']}")
    print(f"  size    = {info3['width']}x{info3['height']}")
    print(f"  aspect  = {info3['aspect_ratio']}")
    print(f"  img_size= {info3['image_size']}")
    print(f"  engine  = {info3['engine_note']}")
    print(f"  base64  = {len(b64_3)} chars")
    print(f"  saved   = {save3}")

    # ------------------------------------------------------------------ #
    # 結果
    # ------------------------------------------------------------------ #
    print()
    print("=" * 60)
    print("結果")
    print("=" * 60)
    print(f"  [1] FreeAI 生成  (512x512)   : {save1}")
    print(f"  [2] リサイズ (1024x1024) : {save1_resized}")
    print(f"  [3] OpenAI 調整 (1024x1024) : {save2}")
    print(f"  [4] Gemini 背景変更 (住宅地) : {save3}")
    print()
    print("OK")


if __name__ == "__main__":
    main()
