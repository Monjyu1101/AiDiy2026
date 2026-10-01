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
# glTF のノードも VRMA 仕様どおり T ポーズの階層として配置する。
# 各位置は VRM_female.vrm のボーン長に近い値。回転の基準は全ノード identity。
SKELETON = {
    "hips": (None, (0, 0.9, 0)),
    "spine": ("hips", (0, 0.10, 0)),
    "chest": ("spine", (0, 0.15, 0)),
    "upperChest": ("chest", (0, 0.15, 0)),
    "neck": ("upperChest", (0, 0.14, 0)),
    "head": ("neck", (0, 0.09, 0)),
    "leftShoulder": ("upperChest", (0.06, 0.08, 0)),
    "leftUpperArm": ("leftShoulder", (0.09, 0, 0)),
    "leftLowerArm": ("leftUpperArm", (0.19, 0, 0)),
    "leftHand": ("leftLowerArm", (0.18, 0, 0)),
    "rightShoulder": ("upperChest", (-0.06, 0.08, 0)),
    "rightUpperArm": ("rightShoulder", (-0.09, 0, 0)),
    "rightLowerArm": ("rightUpperArm", (-0.19, 0, 0)),
    "rightHand": ("rightLowerArm", (-0.18, 0, 0)),
    "leftUpperLeg": ("hips", (0.09, -0.10, 0)),
    "leftLowerLeg": ("leftUpperLeg", (0, -0.38, 0)),
    "leftFoot": ("leftLowerLeg", (0, -0.36, 0.05)),
    "rightUpperLeg": ("hips", (-0.09, -0.10, 0)),
    "rightLowerLeg": ("rightUpperLeg", (0, -0.38, 0)),
    "rightFoot": ("rightLowerLeg", (0, -0.36, 0.05)),
}
BONES = tuple(SKELETON)

# 00 は既存の「標準/VRMA_01.vrma」をそのままコピーする。
# 1〜20 は穏やかな待機動作の候補。腕の左右は VRM の左右に従う。
# 左右鏡映では Y/Z を反転し、長軸 X の回旋は同符号にする。
# 上腕の X は長軸の回旋。肘は左 +Y / 右 -Y の屈曲（150度まで）。
# 前腕 X は回内外（±60度）、手首は小さな Z の傾きだけにして掌の反転を避ける。
POSES = [
    ("右手を頬に添える", {"rightUpperArm": {"z": 25, "x": 90}, "rightLowerArm": {"y": -150, "x": -60}, "rightHand": {"z": -5}, "head": {"z": -4}}),
    ("後ろ手で少し前かがみ", {"leftUpperArm": {"z": -75, "y": 35}, "leftLowerArm": {"y": 20}, "rightUpperArm": {"z": 75, "y": -35}, "rightLowerArm": {"y": -20}, "spine": {"x": 8}, "chest": {"x": 5}, "neck": {"x": -8}, "head": {"x": -5, "z": 4}}),
    ("左右にゆっくり揺れる", {}),
    ("右手を胸に当てる", {"rightUpperArm": {"z": 60, "y": -20, "x": -140}, "rightLowerArm": {"y": -130}}),
    ("両手を胸の前へ", {"leftUpperArm": {"z": -60, "y": 20, "x": -140}, "leftLowerArm": {"y": 130}, "rightUpperArm": {"z": 60, "y": -20, "x": -140}, "rightLowerArm": {"y": -130}}),
    ("右手を顎の近くへ", {"rightUpperArm": {"z": 65, "x": 145}, "rightLowerArm": {"y": -150, "x": -60}, "rightHand": {"z": -5}, "head": {"x": 4}}),
    ("目が合って照れてそらす", {"spine": {"y": 4, "x": 3}, "neck": {"y": 8, "x": 6}, "head": {"y": 13, "x": 10, "z": 5}}),
    ("ひざをそろえて軽くかがむ", {"hips": {"x": 3}, "spine": {"x": 4}, "neck": {"x": -4}, "head": {"x": -5}, "leftUpperLeg": {"x": -20}, "rightUpperLeg": {"x": -20}, "leftLowerLeg": {"x": 40}, "rightLowerLeg": {"x": 40}, "leftFoot": {"x": -20}, "rightFoot": {"x": -20}}),
    ("左向きから画面をのぞき込む", {"hips": {"x": 4, "y": -35}, "spine": {"x": 16}, "chest": {"x": 13}, "upperChest": {"x": 8}, "neck": {"x": -24, "y": 18}, "head": {"x": -22, "y": 17}}),
    ("両手をお腹の前へ", {"leftUpperArm": {"z": -70, "y": 15, "x": -135}, "leftLowerArm": {"y": 95}, "rightUpperArm": {"z": 70, "y": -15, "x": -135}, "rightLowerArm": {"y": -105}}),
    ("背筋を少し伸ばす", {"spine": {"x": -4}, "chest": {"x": -4}, "head": {"x": -2}}),
    ("片足を内側に寄せる", {}),
    ("左に重心を寄せる", {"hips": {"z": 4}, "spine": {"z": -3}, "head": {"z": -2}}),
    ("右に視線を向ける", {"neck": {"y": -9}, "head": {"y": -10}}),
    ("左肩越しに振り返る", {"hips": {"y": -14}, "spine": {"y": -12}, "chest": {"y": -9}, "neck": {"y": -9}, "head": {"y": -8, "z": 4}}),
    ("少しうつむく", {"neck": {"x": 5}, "head": {"x": 8}, "spine": {"x": 2}}),
    ("少し上を見る", {"neck": {"x": -5}, "head": {"x": -8}, "chest": {"x": -2}}),
    ("小さく一回うなずく", {}),
    ("左に首をかしげる", {"neck": {"z": 6}, "head": {"z": 10}, "chest": {"z": -2}}),
    ("小さくおじぎする", {"spine": {"x": 7}, "chest": {"x": 5}, "neck": {"x": -2}, "head": {"x": 6}}),
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


def bone_quaternion(bone, angles):
    """腕を向けてから長軸(X)で回旋する。肘の屈曲(Y)と回内外を混ぜない。"""
    if bone in ("leftUpperArm", "rightUpperArm"):
        swing = quaternion({"y": angles["y"], "z": angles["z"]})
        return multiply(swing, quaternion({"x": angles["x"]}))
    if bone in ("leftLowerArm", "rightLowerArm"):
        flexion = quaternion({"y": angles["y"]})
        return multiply(flexion, quaternion({"x": angles["x"], "z": angles["z"]}))
    return quaternion(angles)


def smoothstep(value):
    x = max(0.0, min(1.0, value))
    return x * x * (3 - 2 * x)


def gesture_weight(t):
    """中立 → ポーズ → 中立。両端は同じ姿勢なのでループで跳ねない。"""
    return smoothstep((t - 0.25) / 1.8) * (1 - smoothstep((t - 5.4) / 1.8))


def bone_angles(bone, pose, t, name):
    base = BASE.get(bone, {})
    goal = pose.get(bone, {})
    is_lean = "画面をのぞき込む" in name
    turn = smoothstep((t - 0.2) / 1.2) * (1 - smoothstep((t - 6.1) / 1.3))
    bend = smoothstep((t - 1.1) / 1.7) * (1 - smoothstep((t - 5.1) / 1.6))
    gaze = smoothstep((t - 1.6) / 1.2) * (1 - smoothstep((t - 4.9) / 1.8))
    def weight_for(axis):
        if name == "目が合って照れてそらす" and bone in ("neck", "head"):
            return smoothstep((t - 1.5) / 1.0) * (1 - smoothstep((t - 5.1) / 1.4))
        if not is_lean:
            return gesture_weight(t)
        if bone in ("neck", "head"):
            return gaze
        if bone == "hips" and axis == "y":
            return turn
        return bend
    angles = {axis: base.get(axis, 0) + (goal.get(axis, base.get(axis, 0)) - base.get(axis, 0)) * weight_for(axis)
              for axis in ("x", "y", "z")}
    if name == "左右にゆっくり揺れる":
        sway = math.sin(2 * math.pi * (t - 1.1) / 3.5) * gesture_weight(t)
        if bone == "hips":
            angles["z"] -= 5 * sway
        elif bone == "spine":
            angles["z"] += 4 * sway
        elif bone == "head":
            angles["z"] += 2 * sway
        elif bone == "leftUpperArm":
            angles["z"] -= 2 * sway
        elif bone == "rightUpperArm":
            angles["z"] += 2 * sway
    elif name == "片足を内側に寄せる":
        tap_window = smoothstep((t - 1.0) / 0.6) * (1 - smoothstep((t - 5.7) / 0.8))
        tap = math.sin(math.pi * (t - 1.0) / 1.5) ** 2 * tap_window
        if bone == "leftUpperLeg":
            angles["x"] -= 7 * tap
            angles["z"] -= 10 * tap
        elif bone == "leftLowerLeg":
            angles["x"] += 10 * tap
            angles["z"] += 4 * tap
        elif bone == "leftFoot":
            angles["x"] -= 3 * tap
            angles["y"] += 8 * tap
            angles["z"] += 6 * tap
    elif name == "小さく一回うなずく":
        nod = smoothstep((t - 1.5) / 0.55) * (1 - smoothstep((t - 2.6) / 0.65))
        if bone == "chest":
            angles["x"] += 1.5 * nod
        elif bone == "neck":
            angles["x"] += 8 * nod
        elif bone == "head":
            angles["x"] += 18 * nod
    # 前腕と手首も動かす。ポーズ保持中の動きは小さく、入口・出口は中立へ戻す。
    breathing = math.sin(2 * math.pi * t / DURATION)
    fidget = math.sin(4 * math.pi * t / DURATION)
    if bone in ("spine", "chest"):
        angles["x"] += breathing * 1.2
    elif bone in ("neck", "head"):
        angles["y"] += fidget * 1.5
    elif bone in ("leftUpperArm", "rightUpperArm"):
        angles["x"] += breathing * 2.5
    elif bone in ("leftLowerArm", "rightLowerArm"):
        angles["y"] += fidget * (2 if bone.startswith("left") else -2)
        sign = 1 if bone.startswith("left") else -1
        angles["y"] = sign * max(0, min(150, sign * angles["y"]))
    elif bone in ("leftHand", "rightHand"):
        angles["z"] += breathing * (2 if bone.startswith("left") else -2)
    return angles


def make_vrma(name, pose):
    # 全候補で同じボーンを出力し、ページを戻したとき前の姿勢が残らないようにする。
    binary = bytearray()
    views, accessors, samplers, channels = [], [], [], []
    node_index = {bone: index for index, bone in enumerate(BONES)}
    nodes = [{"name": bone, "translation": list(SKELETON[bone][1])} for bone in BONES]
    for bone, (parent, _) in SKELETON.items():
        if parent:
            nodes[node_index[parent]].setdefault("children", []).append(node_index[bone])

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
            values.extend(bone_quaternion(bone, bone_angles(bone, pose, t, name)))
        output = accessor(values, 4)
        sampler = len(samplers)
        samplers.append({"input": time_accessor, "output": output, "interpolation": "LINEAR"})
        channels.append({"sampler": sampler, "target": {"node": node, "path": "rotation"}})

    hips_values = []
    for t in TIMES:
        weight = gesture_weight(t)
        side = -1 if name == "右に重心を寄せる" else (1 if name == "左に重心を寄せる" else 0)
        lean = "画面をのぞき込む" in name
        lean_weight = smoothstep((t - 1.1) / 1.7) * (1 - smoothstep((t - 5.1) / 1.6))
        hips_values.extend((side * 0.045 * weight,
                            0.9 - (0.045 * lean_weight if lean else 0)
                                - (0.045 * weight if name == "ひざをそろえて軽くかがむ" else 0)
                                + 0.006 * math.sin(2 * math.pi * t / DURATION),
                            0.08 * lean_weight if lean else 0.0))
    hips_output = accessor(hips_values, 3)
    hips_sampler = len(samplers)
    samplers.append({"input": time_accessor, "output": hips_output, "interpolation": "LINEAR"})
    channels.append({"sampler": hips_sampler, "target": {"node": node_index["hips"], "path": "translation"}})

    gltf = {
        "asset": {"version": "2.0", "generator": "AiDiy idle motion candidates"},
        "extensionsUsed": ["VRMC_vrm_animation"],
        "extensions": {"VRMC_vrm_animation": {"specVersion": "1.0", "humanoid": {
            "humanBones": {bone: {"node": index} for index, bone in enumerate(BONES)}
        }}},
        "scene": 0, "scenes": [{"nodes": [node_index["hips"]]}], "nodes": nodes,
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
