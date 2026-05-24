# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# See LICENSE for full terms.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""movie_generation テスト — Gemini Veo でテキストから動画生成"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_proc.movie_generation import MovieGeneration, MovieGenerationError


def main():
    mg = MovieGeneration()

    # ------------------------------------------------------------------ #
    # キー確認
    # ------------------------------------------------------------------ #
    freeai_key = mg._get_freeai_api_key()
    gemini_key = mg._get_gemini_api_key()

    if not freeai_key and not gemini_key:
        print("SKIP: Gemini / FreeAI API キーが設定されていません")
        return

    provider = "freeai" if freeai_key else "gemini"
    print(f"使用 provider: {provider}")

    # ------------------------------------------------------------------ #
    # Test 1: テキストから動画生成（短め・縦向き）
    # ------------------------------------------------------------------ #
    print("=" * 60)
    print("Test 1: テキストから動画生成（8秒・16:9）")
    print("=" * 60)

    video_bytes1, info1 = mg.generate(
        prompt="A golden retriever running on a sunny beach with ocean waves",
        provider=provider,
        model="auto",
        duration_seconds=8,
        aspect_ratio="16:9",
    )
    saved1 = mg.save(video_bytes1)

    print(f"  provider       = {info1['provider']}")
    print(f"  model          = {info1['model']}")
    print(f"  duration_sec   = {info1['duration_seconds']}")
    print(f"  aspect_ratio   = {info1['aspect_ratio']}")
    print(f"  video_bytes    = {info1['video_bytes_length']:,} bytes")
    print(f"  engine_note    = {info1['engine_note']}")
    print(f"  saved          = {saved1}")

    # ------------------------------------------------------------------ #
    # Test 2: ネガティブプロンプト付き生成（縦向き）
    # ------------------------------------------------------------------ #
    print()
    print("=" * 60)
    print("Test 2: ネガティブプロンプト付き生成（縦向き 9:16）")
    print("=" * 60)

    video_bytes2, info2 = mg.generate(
        prompt="A peaceful Japanese cherry blossom garden with petals falling",
        provider=provider,
        model="auto",
        duration_seconds=6,
        aspect_ratio="9:16",
        negative_prompt="people, crowd, urban, city",
    )
    saved2 = mg.save(video_bytes2)

    print(f"  provider       = {info2['provider']}")
    print(f"  model          = {info2['model']}")
    print(f"  duration_sec   = {info2['duration_seconds']}")
    print(f"  aspect_ratio   = {info2['aspect_ratio']}")
    print(f"  video_bytes    = {info2['video_bytes_length']:,} bytes")
    print(f"  saved          = {saved2}")

    # ------------------------------------------------------------------ #
    # 結果
    # ------------------------------------------------------------------ #
    print()
    print("=" * 60)
    print("結果")
    print("=" * 60)
    print(f"  [1] ビーチの犬 (16:9, 8s) : {saved1}")
    print(f"  [2] 桜の庭 (9:16, 6s)    : {saved2}")
    print()
    print("OK")


if __name__ == "__main__":
    main()
