# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# See LICENSE for full terms.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""movie_generation テスト — 直接実行 + HTTP POST API"""

import json
import os
import sys
import time
from pathlib import Path
from urllib import request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_proc.movie_generation import MovieGeneration, MovieGenerationError


BASE_URL = os.environ.get("AIDIY_MCP_BASE_URL", "http://localhost:8095").rstrip("/")
HTTP_TIMEOUT = float(os.environ.get("AIDIY_MCP_EXTERNAL_TIMEOUT", "1200"))
POST_SAVE_DIR = Path(__file__).resolve().parent / "temp" / "post_movie"


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


def test_post_api(provider: str) -> None:
    """HTTP POST API で直接実行と同じ動画生成フローを確認する。"""
    POST_SAVE_DIR.mkdir(parents=True, exist_ok=True)
    saved1 = POST_SAVE_DIR / "movie_dog_16x9.mp4"
    saved2 = POST_SAVE_DIR / "movie_sakura_9x16.mp4"

    print()
    print("=" * 60)
    print("HTTP POST Test 1: テキストから動画生成（8秒・16:9）")
    print("=" * 60)

    movie1 = _post_json_retry(
        "POST movie dog",
        "/aidiy_movie_generation/generate",
        {
            "prompt": "A golden retriever running on a sunny beach with ocean waves",
            "provider": provider,
            "model": "auto",
            "duration_seconds": 8,
            "aspect_ratio": "16:9",
            "save_path": str(saved1),
        },
    )
    _assert_no_error("POST movie dog", movie1)
    print(f"  saved = {movie1.get('save_path')}")

    print()
    print("=" * 60)
    print("HTTP POST Test 2: ネガティブプロンプト付き生成（9:16）")
    print("=" * 60)

    movie2 = _post_json_retry(
        "POST movie sakura",
        "/aidiy_movie_generation/generate",
        {
            "prompt": "A peaceful Japanese cherry blossom garden with petals falling",
            "provider": provider,
            "model": "auto",
            "duration_seconds": 6,
            "aspect_ratio": "9:16",
            "negative_prompt": "people, crowd, urban, city",
            "save_path": str(saved2),
        },
    )
    _assert_no_error("POST movie sakura", movie2)
    print(f"  saved = {movie2.get('save_path')}")


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

    test_post_api(provider)

    print()
    print("OK")


if __name__ == "__main__":
    main()
