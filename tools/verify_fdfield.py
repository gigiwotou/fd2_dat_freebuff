#!/usr/bin/env python3
"""验证FDFIELD.DAT资源的正确结构"""

import struct
from pathlib import Path

def load_resource(data: bytes, index: int) -> bytes:
    """完全按照sub_111BA的行为加载资源"""
    pos = 4 * index + 6
    start, end = struct.unpack_from("<II", data, pos)
    size = end - start
    return data[start:start + size]

fdfield_path = Path("game/FDFIELD.DAT")
data = fdfield_path.read_bytes()

magic = data[:6]
print(f"Magic: {magic}")

resource_count = struct.unpack_from("<I", data, 6)[0]
print(f"Resource count: {resource_count}")

# 测试地图0
map_id = 0
print(f"\n=== Map {map_id} ===")

# 按照IDA代码：3*N是地图构成数据（含宽高）
res_layout = load_resource(data, 3 * map_id)
res_control = load_resource(data, 3 * map_id + 1)
res_spawn = load_resource(data, 3 * map_id + 2)

print(f"Resource {3*map_id} (layout): {len(res_layout)} bytes")
if len(res_layout) >= 4:
    w = struct.unpack_from("<H", res_layout, 0)[0]
    h = struct.unpack_from("<H", res_layout, 2)[0]
    print(f"  Width: {w}, Height: {h}")
    print(f"  First 20 bytes: {res_layout[:20].hex()}")

print(f"Resource {3*map_id+1} (control): {len(res_control)} bytes")
if len(res_control) >= 3:
    print(f"  First 3 bytes: {res_control[:3].hex()}")
    map_num = res_control[0]
    player_count = res_control[1]
    enemy_count = res_control[2]
    print(f"  Map number: {map_num}, Player count: {player_count}, Enemy count: {enemy_count}")

print(f"Resource {3*map_id+2} (spawn): {len(res_spawn)} bytes")
if len(res_spawn) >= 2:
    char_count = struct.unpack_from("<H", res_spawn, 0)[0]
    print(f"  Character count: {char_count}")
    print(f"  First 20 bytes: {res_spawn[:20].hex()}")

# 测试地图1
map_id = 1
print(f"\n=== Map {map_id} ===")

res_layout = load_resource(data, 3 * map_id)
res_control = load_resource(data, 3 * map_id + 1)
res_spawn = load_resource(data, 3 * map_id + 2)

print(f"Resource {3*map_id} (layout): {len(res_layout)} bytes")
if len(res_layout) >= 4:
    w = struct.unpack_from("<H", res_layout, 0)[0]
    h = struct.unpack_from("<H", res_layout, 2)[0]
    print(f"  Width: {w}, Height: {h}")

print(f"Resource {3*map_id+1} (control): {len(res_control)} bytes")
print(f"Resource {3*map_id+2} (spawn): {len(res_spawn)} bytes")

# 测试地图97
map_id = 97
print(f"\n=== Map {map_id} ===")

if 3 * map_id + 2 < resource_count:
    res_layout = load_resource(data, 3 * map_id)
    res_control = load_resource(data, 3 * map_id + 1)
    res_spawn = load_resource(data, 3 * map_id + 2)

    print(f"Resource {3*map_id} (layout): {len(res_layout)} bytes")
    if len(res_layout) >= 4:
        w = struct.unpack_from("<H", res_layout, 0)[0]
        h = struct.unpack_from("<H", res_layout, 2)[0]
        print(f"  Width: {w}, Height: {h}")

    print(f"Resource {3*map_id+1} (control): {len(res_control)} bytes")
    print(f"Resource {3*map_id+2} (spawn): {len(res_spawn)} bytes")
else:
    print(f"  Map {map_id} resources out of range!")
