# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# See LICENSE for full terms.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""image_generation テスト"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from mcp_proc.image_generation import ImageGeneration, ImageGenerationError


def main():
    ig = ImageGeneration()

    if not ig._get_api_key():
        print("SKIP: OpenAI API キーが設定されていません")
        return

    out_dir = os.path.join(os.path.dirname(__file__), "temp", "output")
    os.makedirs(out_dir, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Test 1: 森でたたずむオオカミ
    # ------------------------------------------------------------------ #
    print("=" * 60)
    print("Test 1: 森でたたずむオオカミ")
    print("=" * 60)

    img1, info1 = ig.generate(
        prompt="森でたたずむオオカミ",
        model="gpt-image-2",
        size="auto",
        quality="auto",
    )
    save1 = os.path.join(out_dir, "test_wolf.png")
    b64_1 = ig.to_base64(img1, "png", 85, save1)

    print(f"  model  = {info1['model']}")
    print(f"  size   = {info1['width']}x{info1['height']}")
    print(f"  quality= {info1['quality']}")
    print(f"  engine = {info1['engine_note']}")
    print(f"  base64 = {len(b64_1)} chars")
    print(f"  saved  = {save1}")

    # ------------------------------------------------------------------ #
    # Test 2: オオカミ → 子猫に一部変更
    # ------------------------------------------------------------------ #
    print()
    print("=" * 60)
    print("Test 2: オオカミ → 子猫に変更")
    print("=" * 60)

    img2, info2 = ig.generate(
        prompt="背景かえないでオオカミを子猫に変更",
        model=info1["model"],
        size=info1["size"],
        quality=info1["quality"],
        original_path=save1,
    )
    save2 = os.path.join(out_dir, "test_kitten.png")
    b64_2 = ig.to_base64(img2, "png", 85, save2)

    print(f"  model  = {info2['model']}")
    print(f"  size   = {info2['width']}x{info2['height']}")
    print(f"  quality= {info2['quality']}")
    print(f"  engine = {info2['engine_note']}")
    print(f"  base64 = {len(b64_2)} chars")
    print(f"  saved  = {save2}")

    # ------------------------------------------------------------------ #
    # 結果
    # ------------------------------------------------------------------ #
    print()
    print("=" * 60)
    print("結果")
    print("=" * 60)
    print(f"  [1] {save1}")
    print(f"  [2] {save2}")
    print()
    print("OK")


if __name__ == "__main__":
    main()
