# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from PIL import Image, ImageOps


def ポーズ画像一覧を検出(script_dir: Path) -> list[Path]:
    candidate_roots = [
        script_dir / "アバター制御" / "ポーズ集",
        script_dir / "ポーズ集",
        script_dir / "アバター制御" / "assets",
        script_dir / "assets",
        script_dir.parent / "frontend_server" / "public" / "icons",
        script_dir.parent / "backend_server" / "_icons",
    ]
    for root in candidate_roots:
        if not root.exists():
            continue
        if root.is_dir() and root.name == "ポーズ集":
            direct_images = sorted(root.glob("*.png"))
            if direct_images:
                return direct_images
        pose_dirs: list[Path] = []
        for file_path in root.rglob("1.png"):
            siblings = sorted(file_path.parent.glob("*.png"))
            if len(siblings) >= 3:
                pose_dirs.append(file_path.parent)
        if pose_dirs:
            pose_dir = sorted(set(pose_dirs), key=lambda item: str(item))[0]
            return sorted(pose_dir.glob("*.png"))
    return []


def 安定ポーズフレームを構築(pose_paths: Sequence[Path], scale: float) -> list[Image.Image]:
    cropped_images: list[Image.Image] = []
    max_width = 0
    max_height = 0

    for pose_path in pose_paths:
        with Image.open(pose_path) as image:
            rgba = image.convert("RGBA")
            bbox = rgba.getbbox()
            trimmed = rgba.crop(bbox) if bbox else rgba
            width = max(1, int(trimmed.width * scale))
            height = max(1, int(trimmed.height * scale))
            resized = trimmed.resize((width, height), Image.LANCZOS)
            cropped_images.append(resized.copy())
            max_width = max(max_width, resized.width)
            max_height = max(max_height, resized.height)

    stable_frames: list[Image.Image] = []
    for image in cropped_images:
        canvas = Image.new("RGBA", (max_width, max_height), (0, 0, 0, 0))
        offset_x = (max_width - image.width) // 2
        offset_y = max_height - image.height
        canvas.paste(image, (offset_x, offset_y), image)
        stable_frames.append(canvas)
    return stable_frames


def ウィンドウアイコンを検出(script_dir: Path) -> Path | None:
    candidate_roots = [
        script_dir / "アバター制御" / "assets",
        script_dir / "assets",
        script_dir.parent / "frontend_server" / "public" / "icons",
        script_dir.parent / "backend_server" / "_icons",
    ]
    for root in candidate_roots:
        if not root.exists():
            continue
        for pattern in ("AiDiy.ico", "AiDiy.png"):
            matches = sorted(root.rglob(pattern))
            if matches:
                return matches[0]
    return None


def スプライト画像を作成(pattern: list[str], scale: int) -> Image.Image:
    palette = {
        ".": (0, 0, 0, 0),
        "K": (39, 42, 54, 255),
        "W": (250, 247, 240, 255),
        "S": (214, 208, 198, 255),
        "P": (241, 168, 181, 255),
        "E": (28, 28, 28, 255),
    }
    width = len(pattern[0])
    height = len(pattern)
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = image.load()
    for y, row in enumerate(pattern):
        for x, key in enumerate(row):
            pixels[x, y] = palette.get(key, (0, 0, 0, 0))
    return image.resize((width * scale, height * scale), Image.Resampling.NEAREST)


def xneko風フレームを構築(scale: int) -> dict[str, list[Image.Image]]:
    stand = [
        "................",
        ".....KKKK.......",
        "....KWWWWKK.....",
        "...KWWWPPWWK....",
        "..KWWWEWWEWWK...",
        "..KWWWWWWWWWK...",
        ".KWWWWKKWWWWWK..",
        ".KWWWKWWKWWWWK..",
        "..KWWWWWWWWWK...",
        "...KWWWWWWWK....",
        "...KWWKWWKWWK...",
        "..KKK.KK.KKKK...",
        ".K..K....K..K...",
        "....K....K......",
        "...KK....KK.....",
        "................",
    ]
    walk_1 = [
        "................",
        ".....KKKK.......",
        "....KWWWWKK.....",
        "...KWWWPPWWK....",
        "..KWWWEWWEWWK...",
        "..KWWWWWWWWWK...",
        ".KWWWWKKWWWWWK..",
        ".KWWWKWWKWWWWK..",
        "..KWWWWWWWWWK...",
        "...KWWWWWWWK....",
        "..KKWWKWWKWWK...",
        ".K..K.KK...KK...",
        "....K....KK.....",
        "...KK...........",
        "..KK............",
        "................",
    ]
    walk_2 = [
        "................",
        ".....KKKK.......",
        "....KWWWWKK.....",
        "...KWWWPPWWK....",
        "..KWWWEWWEWWK...",
        "..KWWWWWWWWWK...",
        ".KWWWWKKWWWWWK..",
        ".KWWWKWWKWWWWK..",
        "..KWWWWWWWWWK...",
        "...KWWWWWWWK....",
        "...KWWKWWKWWKK..",
        "..KK...KK.K..K..",
        ".....KK....K....",
        "..........KK....",
        ".........KK.....",
        "................",
    ]
    sit = [
        "................",
        "......KKK.......",
        "....KKWWWKK.....",
        "...KWWWPPWWK....",
        "..KWWWEWWEWWK...",
        "..KWWWWWWWWWK...",
        "...KWWWWWWWK....",
        "..KWWWWWWWWWK...",
        ".KWWWWKKKWWWK...",
        ".KWWWK...KWWK...",
        "..KKK.....KKK...",
        "...K.......K....",
        "..KK.......KK...",
        "................",
        "................",
        "................",
    ]
    yawn = [
        "................",
        "......KKK.......",
        "....KKWWWKK.....",
        "...KWWWPPWWK....",
        "..KWWWPPPWWWK...",
        "..KWWWWWWWWWK...",
        "...KWWWWWWWK....",
        "..KWWWWWWWWWK...",
        ".KWWWWKKKWWWK...",
        ".KWWWK...KWWK...",
        "..KKK.....KKK...",
        "...K.......K....",
        "..KK.......KK...",
        "................",
        "................",
        "................",
    ]
    sleep = [
        "................",
        "................",
        ".....KKKKK......",
        "...KKWWWWWKK....",
        "..KWWWWPPWWWK...",
        "..KWWWWWWWWWK...",
        "..KWWWEWWWWEK...",
        "...KWWWWWWWK....",
        "....KWWWWWK.....",
        "..KKKWWWWKKK....",
        ".KWWSKKKKSSWK...",
        ".KWWK....KWWK...",
        "..KK......KK....",
        "................",
        "................",
        "................",
    ]

    right_walk = [スプライト画像を作成(walk_1, scale), スプライト画像を作成(walk_2, scale)]
    right_run = [スプライト画像を作成(walk_2, scale), スプライト画像を作成(walk_1, scale)]
    right_sit = [スプライト画像を作成(sit, scale)]
    right_yawn = [スプライト画像を作成(sit, scale), スプライト画像を作成(yawn, scale)]
    right_sleep = [スプライト画像を作成(sleep, scale)]
    right_stand = [スプライト画像を作成(stand, scale)]
    return {
        "walk_right": right_walk,
        "walk_left": [ImageOps.mirror(frame) for frame in right_walk],
        "run_right": right_run,
        "run_left": [ImageOps.mirror(frame) for frame in right_run],
        "sit_right": right_sit,
        "sit_left": [ImageOps.mirror(frame) for frame in right_sit],
        "yawn_right": right_yawn,
        "yawn_left": [ImageOps.mirror(frame) for frame in right_yawn],
        "sleep_right": right_sleep,
        "sleep_left": [ImageOps.mirror(frame) for frame in right_sleep],
        "stand_right": right_stand,
        "stand_left": [ImageOps.mirror(frame) for frame in right_stand],
    }
