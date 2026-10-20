#!/usr/bin/env python3
"""CLI 7 件の保存済み素材を再生成する。取得・インストールは行わない。"""
from pathlib import Path
import argparse
import base64
import hashlib
import os
import shutil
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET


アイコン名 = ("claude", "codex", "copilot", "agy", "grok", "opencode", "aidiy_hermes")
基準 = Path(__file__).resolve().parent
AiDiy原本 = 基準 / "upstream" / "AiDiy.png"
AiDiy原本SHA256 = "3b580e91b8e91a2accd55675c07f2b2b8c3c9cf85677da804ef6b74ae8267042"
外部原本 = {
    "claude": ("claude-code-color-lobe.svg", "670b3d8d749d0815ad8f7e62a59d51cb5e2053cb19403f3541a8aed7036a877f"),
    "codex": ("codex-color-lobe.svg", "4a2f43ce46b5b6e3722c95088f88d26ef91e6a8c2e598e70642a1c54367386e4"),
    "grok": ("Grok_Logomark_Light.svg", "b20648e2f111d7fbc91f58b22d1e76e9885b68a163cb5a1010f7f11bf5840491"),
    "opencode": ("opencode-logo-dark-square.svg", "d6a0e3b8a295f413543f41cb73957e670351b5cb088c8d9dbd186b9e9d633cca"),
    "copilot": ("copilot-24.svg", "eeafb3c2f333e04ccf7d031ae215f7adafaed4c6352556b0bf79496e048bcdd7"),
}
表示名 = {"claude": "Claude", "codex": "Codex", "copilot": "Copilot", "agy": "Agy", "grok": "Grok", "opencode": "OpenCode", "aidiy_hermes": "HERMES"}
SVG名前空間 = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG名前空間)


def SVG合成(名前):
    """ロゴの形状・色を維持し、重ならない白帯と黒い製品名を付ける。"""
    if 名前 in 外部原本:
        ファイル名, 期待ハッシュ = 外部原本[名前]
    else:
        ファイル名 = "agy-aidiy.svg"
        期待ハッシュ = "a5b63771f310b55952380ba50f9d5533ab0d0ba69fa7e2fb8538dbbd5b6f3dde"
    # Windows checkout の CRLF のみ取得時の LF に戻して照合する。
    原本 = (基準 / "upstream" / ファイル名).read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(原本).hexdigest() != 期待ハッシュ:
        raise RuntimeError(f"{名前} 原本の SHA-256 が保存時と異なります。出典を再確認してください。")
    図形 = ET.fromstring(原本)
    # 原本の viewBox・全パス・色・縦横比は保持し、配置先の viewport だけを指定する。
    図形.attrib.update({"x": "18", "y": "3", "width": "84", "height": "84", "id": "brandmark", "preserveAspectRatio": "xMidYMid meet"})
    if 名前 == "copilot":
        # Octicons の指定色なしの図形を、従来どおり暗色 UI 用の白で描画する。
        図形.set("fill", "#f0f6fc")
    SVG保存(名前, 図形)


def SVG保存(名前, 図形):
    svg = ET.Element(f"{{{SVG名前空間}}}svg", {"width": "120", "height": "120", "viewBox": "0 0 120 120"})
    ET.SubElement(svg, "title").text = 表示名[名前]
    ET.SubElement(svg, "desc").text = "既存の図形と、識別用の白い帯・黒い名前を含む CLI ランチャー用画像。出典・加工内容: LICENSE_ICONS.md。" + ("人物部分は無改変の AiDiy PNG の埋め込みで、ベクター画像ではありません。" if 名前 == "aidiy_hermes" else "")
    svg.append(図形)
    ET.SubElement(svg, "rect", {"id": "caption-band", "x": "0", "y": "90", "width": "120", "height": "30", "fill": "#ffffff"})
    ET.SubElement(svg, "text", {"id": "caption-label", "x": "60", "y": "111", "text-anchor": "middle", "font-family": "Arial, Liberation Sans, sans-serif", "font-size": "22", "font-weight": "700", "fill": "#000000"}).text = 表示名[名前]
    (基準 / f"{名前}.svg").write_text(ET.tostring(svg, encoding="unicode") + "\n", encoding="utf-8")


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
    # 人物の PNG バイトは無改変で埋め込み、画像の外側に識別用の文字帯を置く。
    # 人物のベクター化・描き直し・色変更・切り抜きは行わない。
    png = AiDiy原本.read_bytes()
    if hashlib.sha256(png).hexdigest() != AiDiy原本SHA256:
        raise RuntimeError("AiDiy 原本の SHA-256 が保存時と異なります。出典を再確認してください。")
    PNG確認(AiDiy原本, (512, 512))
    埋込 = base64.b64encode(png).decode("ascii")
    図形 = ET.Element("image", {"id": "brandmark", "x": "18", "y": "3", "width": "84", "height": "84", "preserveAspectRatio": "xMidYMid meet", "href": f"data:image/png;base64,{埋込}"})
    SVG保存("aidiy_hermes", 図形)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("names", nargs="*", help="再生成する ID。省略時は 7 件すべて。")
    args = parser.parse_args()
    対象 = args.names or list(アイコン名)
    不明 = set(対象) - set(アイコン名)
    if 不明:
        parser.error(f"未登録のアイコン: {', '.join(sorted(不明))}")
    inkscape = shutil.which("inkscape")
    if not inkscape:
        raise SystemExit("既存の Inkscape を PATH に指定してください。自動インストールは行いません。")
    # Inkscape の一時設定もこのフォルダ内で完結させ、終了時に取り除く。
    with tempfile.TemporaryDirectory(prefix=".png-convert-", dir=基準) as tmp:
        env = os.environ.copy()
        env.update({
            "XDG_CONFIG_HOME": tmp,
            "XDG_CACHE_HOME": tmp,
            "XDG_DATA_HOME": tmp,
            "INKSCAPE_PROFILE_DIR": tmp,
        })
        for 名前 in 対象:
            if 名前 == "aidiy_hermes":
                AiDiy再利用()
            else:
                SVG合成(名前)
            SVG入力 = 基準 / f"{名前}.svg"
            出力 = 基準 / f"{名前}.png"
            subprocess.run([
                inkscape,
                str(SVG入力),
                "--export-type=png", "--export-area-page",
                "--export-width=120", "--export-height=120",
                "--export-background-opacity=0",
                f"--export-filename={出力}",
            ], check=True, env=env, capture_output=True)
            PNG確認(出力, (120, 120))


if __name__ == "__main__":
    main()
