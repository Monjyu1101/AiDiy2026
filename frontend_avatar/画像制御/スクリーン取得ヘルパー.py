# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import io
import json
import sys

import mss
from PIL import Image


def _スクリーン一覧を取得() -> list[dict[str, int]]:
    with mss.mss() as sct:
        return [
            {
                "left": int(monitor["left"]),
                "top": int(monitor["top"]),
                "width": int(monitor["width"]),
                "height": int(monitor["height"]),
            }
            for monitor in sct.monitors[1:]
        ]


def _画像を取得(left: int, top: int, right: int, bottom: int, max_width: int | None, max_height: int | None) -> bytes:
    with mss.mss() as sct:
        shot = sct.grab(
            {
                "left": left,
                "top": top,
                "width": max(1, right - left),
                "height": max(1, bottom - top),
            }
        )
    image = Image.frombytes("RGB", shot.size, shot.rgb)
    if max_width and max_height:
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list")

    grab_parser = subparsers.add_parser("grab")
    grab_parser.add_argument("--left", type=int, required=True)
    grab_parser.add_argument("--top", type=int, required=True)
    grab_parser.add_argument("--right", type=int, required=True)
    grab_parser.add_argument("--bottom", type=int, required=True)
    grab_parser.add_argument("--max-width", type=int)
    grab_parser.add_argument("--max-height", type=int)

    args = parser.parse_args()
    if args.command == "list":
        sys.stdout.write(json.dumps(_スクリーン一覧を取得(), ensure_ascii=False))
        return 0

    image_bytes = _画像を取得(
        left=args.left,
        top=args.top,
        right=args.right,
        bottom=args.bottom,
        max_width=args.max_width,
        max_height=args.max_height,
    )
    sys.stdout.buffer.write(image_bytes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
