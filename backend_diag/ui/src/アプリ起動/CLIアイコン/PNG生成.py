#!/usr/bin/env python3
"""CLI 7 件の保存済み素材を再生成する。取得・インストールは行わない。"""
from pathlib import Path
import argparse
import base64
import hashlib
import os
import re
import shutil
import struct
import subprocess
import tempfile


アイコン名 = ("claude", "codex", "copilot", "agy", "grok", "opencode", "aidiy_hermes")
基準 = Path(__file__).resolve().parent
AiDiy原本 = 基準 / "upstream" / "AiDiy.png"
AiDiy原本SHA256 = "3b580e91b8e91a2accd55675c07f2b2b8c3c9cf85677da804ef6b74ae8267042"
外部原本 = {
    "claude": ("claude-code-color-lobe.svg", "670b3d8d749d0815ad8f7e62a59d51cb5e2053cb19403f3541a8aed7036a877f"),
    "codex": ("codex-color-lobe.svg", "4a2f43ce46b5b6e3722c95088f88d26ef91e6a8c2e598e70642a1c54367386e4"),
    "grok": ("Grok_Logomark_Light.svg", "b20648e2f111d7fbc91f58b22d1e76e9885b68a163cb5a1010f7f11bf5840491"),
    "opencode": ("opencode-logo-dark-square.svg", "d6a0e3b8a295f413543f41cb73957e670351b5cb088c8d9dbd186b9e9d633cca"),
}


def PNG確認(出力, 寸法):
    png = 出力.read_bytes()
    if len(png) < 33 or png[:8] != b"\x89PNG\r\n\x1a\n" or struct.unpack(">II", png[16:24]) != 寸法:
        raise RuntimeError(f"PNG のサイズ確認に失敗しました: {出力}")
    # PNG の color type 6 は透過つき RGB（RGBA）。
    if png[25] != 6:
        raise RuntimeError(f"PNG に RGBA 情報がありません: {出力}")
    print(f"{出力.name}: {寸法[0]}×{寸法[1]} / RGBA")


def AiDiy再利用():
    # frontend_web/public/icons/AiDiy.png から固定保存した原本。
    # PNG は変換せずコピーし、SVG は同一 PNG を内包するラッパーにする。
    # ベクター化・描き直し・色変更・文字帯追加は行わない。
    png = AiDiy原本.read_bytes()
    if hashlib.sha256(png).hexdigest() != AiDiy原本SHA256:
        raise RuntimeError("AiDiy 原本の SHA-256 が保存時と異なります。出典を再確認してください。")
    出力 = 基準 / "aidiy_hermes.png"
    出力.write_bytes(png)
    PNG確認(出力, (512, 512))
    埋込 = base64.b64encode(png).decode("ascii")
    (基準 / "aidiy_hermes.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 512 512">\n'
        '  <title>AiDiy Hermes</title>\n'
        '  <desc>既存 AiDiy PNG の無改変埋め込み。ベクター画像ではありません。出典: LICENSE_ICONS.md。</desc>\n'
        f'  <image width="512" height="512" href="data:image/png;base64,{埋込}"/>\n'
        '</svg>\n', encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("names", nargs="*", help="再生成する ID。省略時は 7 件すべて。")
    args = parser.parse_args()
    対象 = args.names or list(アイコン名)
    不明 = set(対象) - set(アイコン名)
    if 不明:
        parser.error(f"未登録のアイコン: {', '.join(sorted(不明))}")
    ベクター対象 = [名前 for 名前 in 対象 if 名前 != "aidiy_hermes"]
    inkscape = shutil.which("inkscape") if ベクター対象 else None
    if ベクター対象 and not inkscape:
        raise SystemExit("既存の Inkscape を PATH に指定してください。自動インストールは行いません。")
    if "aidiy_hermes" in 対象:
        AiDiy再利用()
    if not ベクター対象:
        return
    # Inkscape の一時設定もこのフォルダ内で完結させ、終了時に取り除く。
    with tempfile.TemporaryDirectory(prefix=".png-convert-", dir=基準) as tmp:
        env = os.environ.copy()
        env.update({
            "XDG_CONFIG_HOME": tmp,
            "XDG_CACHE_HOME": tmp,
            "XDG_DATA_HOME": tmp,
            "INKSCAPE_PROFILE_DIR": tmp,
        })
        for 名前 in ベクター対象:
            if 名前 in 外部原本:
                ファイル名, 期待ハッシュ = 外部原本[名前]
                # Windows のテキスト checkout による CRLF だけを原本の LF に戻す。
                原本 = (基準 / "upstream" / ファイル名).read_bytes().replace(b"\r\n", b"\n")
                if hashlib.sha256(原本).hexdigest() != 期待ハッシュ:
                    raise RuntimeError(f"{名前} 原本の SHA-256 が保存時と異なります。出典を再確認してください。")
                # 図形・色・寸法指定を含め、取得した SVG の全バイトを維持する。
                (基準 / f"{名前}.svg").write_bytes(原本)
            SVG入力 = 基準 / f"{名前}.svg"
            SVG内容 = SVG入力.read_text(encoding="utf-8")
            開始タグ = re.search(r"<svg\b[^>]*>", SVG内容)
            if 開始タグ and re.search(r'\b(?:width|height)="1em"', 開始タグ.group()):
                # Inkscape は単独 SVG の 1em viewport を空として扱う場合がある。
                # 保存 SVG は触らず、描画用の一時コピーの viewport だけを明示する。
                # viewBox・形状・色・縦横比は同一で、PNG 出力時の拡大縮小に限定する。
                変更タグ = re.sub(r'\b(width|height)="1em"', r'\1="96"', 開始タグ.group())
                SVG入力 = Path(tmp) / f"{名前}.svg"
                SVG入力.write_text(
                    SVG内容[:開始タグ.start()] + 変更タグ + SVG内容[開始タグ.end():],
                    encoding="utf-8",
                )
            出力 = 基準 / f"{名前}.png"
            subprocess.run([
                inkscape,
                str(SVG入力),
                "--export-type=png", "--export-area-page",
                "--export-width=96", "--export-height=96",
                "--export-background-opacity=0",
                f"--export-filename={出力}",
            ], check=True, env=env, capture_output=True)
            PNG確認(出力, (96, 96))


if __name__ == "__main__":
    main()
