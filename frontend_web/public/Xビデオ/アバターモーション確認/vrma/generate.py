#!/usr/bin/env python3
"""待機モーション候補を VRM Animation (GLB) として生成する。"""

import json
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DURATION = 8.0
FPS = 30
TIMES = [i / FPS for i in range(int(DURATION * FPS) + 1)]

# 回転角は VRM の正規化ボーンを基準とする。A ポーズの腕を自然に下げる。
BASE = {
    "leftUpperArm": {"z": -75},
    "rightUpperArm": {"z": 75},
    "leftLowerArm": {"y": 10},
    "rightLowerArm": {"y": -10},
}
BONES = (
    "hips", "spine", "chest", "upperChest", "neck", "head",
    "leftShoulder", "rightShoulder", "leftUpperArm", "rightUpperArm",
    "leftLowerArm", "rightLowerArm", "leftHand", "rightHand",
)

# 00 は既存の「標準/VRMA_01.vrma」をそのままコピーする。
# 1〜20 は穏やかな待機動作の候補。腕の左右は VRM の左右に従う。
POSES = [
    ("右手を頬に添える", {"rightUpperArm": {"z": -30, "x": -10}, "rightLowerArm": {"z": -115, "y": -10}, "rightHand": {"z": 18}, "head": {"z": -4}}),
    ("左手を頬に添える", {"leftUpperArm": {"z": 30, "x": -10}, "leftLowerArm": {"z": 115, "y": 10}, "leftHand": {"z": -18}, "head": {"z": 4}}),
    ("左手を胸に当てる", {"leftUpperArm": {"z": -43, "x": -12}, "leftLowerArm": {"z": -125}, "leftHand": {"z": 12}}),
    ("右手を胸に当てる", {"rightUpperArm": {"z": 43, "x": -12}, "rightLowerArm": {"z": 125}, "rightHand": {"z": -12}}),
    ("両手を胸の前へ", {"leftUpperArm": {"z": -43, "x": -8}, "leftLowerArm": {"z": -120}, "rightUpperArm": {"z": 43, "x": -8}, "rightLowerArm": {"z": 120}}),
    ("右手を顎の近くへ", {"rightUpperArm": {"z": -25, "x": -8}, "rightLowerArm": {"z": -125}, "rightHand": {"z": 25}, "head": {"x": 6}}),
    ("左手を顎の近くへ", {"leftUpperArm": {"z": 25, "x": -8}, "leftLowerArm": {"z": 125}, "leftHand": {"z": -25}, "head": {"x": 6}}),
    ("右手を軽く上げる", {"rightUpperArm": {"z": -25, "x": -12}, "rightLowerArm": {"z": -40}, "rightHand": {"z": 12}}),
    ("左手を軽く上げる", {"leftUpperArm": {"z": 25, "x": -12}, "leftLowerArm": {"z": 40}, "leftHand": {"z": -12}}),
    ("両手をお腹の前へ", {"leftUpperArm": {"z": -58, "x": -12}, "leftLowerArm": {"z": -75}, "rightUpperArm": {"z": 58, "x": -12}, "rightLowerArm": {"z": 75}}),
    ("背筋を少し伸ばす", {"spine": {"x": -4}, "chest": {"x": -4}, "head": {"x": -2}}),
    ("右に重心を寄せる", {"hips": {"z": -4}, "spine": {"z": 3}, "head": {"z": 2}}),
    ("左に重心を寄せる", {"hips": {"z": 4}, "spine": {"z": -3}, "head": {"z": -2}}),
    ("右に視線を向ける", {"neck": {"y": -9}, "head": {"y": -10}}),
    ("左に視線を向ける", {"neck": {"y": 9}, "head": {"y": 10}}),
    ("少しうつむく", {"neck": {"x": 5}, "head": {"x": 8}, "spine": {"x": 2}}),
    ("少し上を見る", {"neck": {"x": -5}, "head": {"x": -8}, "chest": {"x": -2}}),
    ("肩を軽くすくめる", {"leftShoulder": {"z": 7}, "rightShoulder": {"z": -7}, "neck": {"x": 2}}),
    ("右手を軽く差し出す", {"rightUpperArm": {"z": 42, "y": -12}, "rightLowerArm": {"z": -42, "y": -10}, "rightHand": {"x": 10}}),
    ("左手を軽く差し出す", {"leftUpperArm": {"z": -42, "y": 12}, "leftLowerArm": {"z": 42, "y": 10}, "leftHand": {"x": 10}}),
]


def multiply(a, b):
    x, y, z, w = a
    X, Y, Z, W = b
    return (w*X + x*W + y*Z - z*Y,
            w*Y - x*Z + y*W + z*X,
            w*Z + x*Y - y*X + z*W,
            w*W - x*X - y*Y - z*Z)


def quaternion(angles):
    result = (0.0, 0.0, 0.0, 1.0)
    for axis in ("x", "y", "z"):
        angle = math.radians(angles.get(axis, 0)) / 2
        s, c = math.sin(angle), math.cos(angle)
        rotation = {"x": (s, 0, 0, c), "y": (0, s, 0, c), "z": (0, 0, s, c)}[axis]
        result = multiply(result, rotation)
    length = math.sqrt(sum(v*v for v in result))
    return tuple(v/length for v in result)


def make_vrma(name, pose):
    # 全候補で同じボーンを出力し、ページを戻したとき前の姿勢が残らないようにする。
    binary = bytearray()
    views, accessors, samplers, channels = [], [], [], []
    nodes = [{"name": bone, "translation": [0, 0.9, 0] if bone == "hips" else [0, 0, 0]} for bone in BONES]

    def accessor(values, width, minimum=None, maximum=None):
        offset = len(binary)
        binary.extend(struct.pack(f"<{len(values)}f", *values))
        view = len(views)
        views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(values)*4})
        result = len(accessors)
        entry = {"bufferView": view, "componentType": 5126, "count": len(values)//width,
                 "type": {1: "SCALAR", 3: "VEC3", 4: "VEC4"}[width]}
        if minimum is not None:
            entry["min"], entry["max"] = minimum, maximum
        accessors.append(entry)
        return result

    time_accessor = accessor(TIMES, 1, [0.0], [DURATION])
    for node, bone in enumerate(BONES):
        values = []
        for t in TIMES:
            # 8 秒の端点が一致。静止姿勢に呼吸とごく小さい揺れを加える。
            breath = math.sin(2 * math.pi * t / DURATION)
            sway = math.sin(4 * math.pi * t / DURATION)
            angles = dict(BASE.get(bone, {}))
            angles.update(pose.get(bone, {}))
            if bone in ("spine", "chest"):
                angles["x"] = angles.get("x", 0) + breath * 0.8
            if bone in ("neck", "head"):
                angles["y"] = angles.get("y", 0) + sway * 1.0
            if bone in ("leftUpperArm", "rightUpperArm"):
                angles["x"] = angles.get("x", 0) + breath * 1.2
            values.extend(quaternion(angles))
        output = accessor(values, 4)
        sampler = len(samplers)
        samplers.append({"input": time_accessor, "output": output, "interpolation": "LINEAR"})
        channels.append({"sampler": sampler, "target": {"node": node, "path": "rotation"}})

    gltf = {
        "asset": {"version": "2.0", "generator": "AiDiy idle motion candidates"},
        "extensionsUsed": ["VRMC_vrm_animation"],
        "extensions": {"VRMC_vrm_animation": {"specVersion": "1.0", "humanoid": {
            "humanBones": {bone: {"node": index} for index, bone in enumerate(BONES)}
        }}},
        "scene": 0, "scenes": [{"nodes": list(range(len(BONES)))}], "nodes": nodes,
        "animations": [{"name": name, "channels": channels, "samplers": samplers}],
        "accessors": accessors, "bufferViews": views, "buffers": [{"byteLength": len(binary)}],
    }
    json_chunk = json.dumps(gltf, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    json_chunk += b" " * (-len(json_chunk) % 4)
    binary.extend(b"\x00" * (-len(binary) % 4))
    length = 12 + 8 + len(json_chunk) + 8 + len(binary)
    return (struct.pack("<III", 0x46546C67, 2, length)
            + struct.pack("<II", len(json_chunk), 0x4E4F534A) + json_chunk
            + struct.pack("<II", len(binary), 0x004E4942) + binary)


if __name__ == "__main__":
    for number, (name, pose) in enumerate(POSES, 1):
        path = ROOT / f"VRMA_{number:02d}_{name}.vrma"
        path.write_bytes(make_vrma(name, pose))
        print(f"{path.name}: {name}")
