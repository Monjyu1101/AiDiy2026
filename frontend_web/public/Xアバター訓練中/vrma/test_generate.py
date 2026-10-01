import importlib.util
import json
import math
import struct
from pathlib import Path

root = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('motions', root / 'generate.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
for number, (name, pose) in enumerate(m.POSES, 1):
    path = root / f'VRMA_{number:02d}_{name}.vrma'
    data = path.read_bytes()
    assert data == m.make_vrma(name, pose), ('stale generated file', number)
    magic, version, length = struct.unpack_from('<III', data)
    assert (magic, version, length) == (0x46546c67, 2, len(data))
    json_length, kind = struct.unpack_from('<II', data, 12)
    gltf = json.loads(data[20:20+json_length])
    assert gltf['extensions']['VRMC_vrm_animation']['specVersion'] == '1.0'
    assert len(gltf['animations'][0]['channels']) == len(m.BONES) + 1
    for bone in m.BONES:
        quats = []
        for t in m.TIMES:
            angles = m.bone_angles(bone, pose, t, name)
            q = m.bone_quaternion(bone, angles)
            assert abs(sum(v*v for v in q) - 1) < 1e-10
            if bone in ('leftLowerArm', 'rightLowerArm'):
                flex = angles['y'] * (1 if bone.startswith('left') else -1)
                assert 0 <= flex <= 150, (number, bone, t, flex)
                assert abs(angles['x']) <= 60
                assert abs(angles['z']) < 1e-10
            if bone in ('leftHand', 'rightHand'):
                assert abs(angles['z']) <= 7
            quats.append(q)
        assert sum(a*b for a,b in zip(quats[0],quats[-1])) > 0.99999999
        for a,b in zip(quats,quats[1:]):
            dot = abs(sum(x*y for x,y in zip(a,b)))
            step = math.degrees(2*math.acos(min(1,dot)))
            assert step < 8, (number, bone, step)
        if bone in ('leftUpperArm','rightUpperArm'):
            # 長軸の回旋で肘の位置まで回らないことを確認する。
            q = m.bone_quaternion(bone, {'x':130, 'y':20, 'z':60})
            swing = m.bone_quaternion(bone, {'x':0, 'y':20, 'z':60})
            def rotate_x(q):
                x,y,z,w=q
                return (1-2*(y*y+z*z),2*(x*y+w*z),2*(x*z-w*y))
            assert max(abs(a-b) for a,b in zip(rotate_x(q), rotate_x(swing))) < 1e-10
for number in (5,):
    name, pose = m.POSES[number - 1]
    for part in ('UpperArm', 'LowerArm', 'Hand'):
        for t in m.TIMES:
            left = m.bone_quaternion('left'+part, m.bone_angles('left'+part,pose,t,name))
            right = m.bone_quaternion('right'+part, m.bone_angles('right'+part,pose,t,name))
            reflected = (right[0], -right[1], -right[2], right[3])
            assert abs(sum(a*b for a,b in zip(left,reflected))) > 0.9999999, ('mirror',number,part,t)
print(f'PASS: 20 generated GLBs, {len(m.POSES)*len(m.BONES)*len(m.TIMES)} rotation samples, elbow/wrist limits, shoulder twist axis, mirrored chest pose, continuity and neutral endpoints')
