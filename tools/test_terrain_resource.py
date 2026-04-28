#!/usr/bin/env python3
"""验证每个terrain_id是否对应FDSHAP.DAT中的独立资源"""

import struct
from pathlib import Path

# 加载地图0的terrain_id
import json
layout = json.load(open('output/maps/map_0_layout.json'))
terrain_ids = set()
for row in layout['terrain_ids']:
    for tid in row:
        terrain_ids.add(tid)

print(f"地图0使用的terrain_id: {sorted(terrain_ids)}")
print(f"唯一terrain_id数量: {len(terrain_ids)}")
print(f"最大terrain_id: {max(terrain_ids)}")

# 检查FDSHAP.DAT资源数量
fdshap = Path("game/FDSHAP.DAT").read_bytes()
count = struct.unpack_from('<I', fdshap, 6)[0]
print(f"\nFDSHAP.DAT资源数量: {count}")

# 检查奇数资源（tile资源）的数量和尺寸
tile_resources = []
for i in range(1, count, 2):  # 奇数索引
    pos = 4 * i + 10
    if pos + 4 > len(fdshap):
        break
    offset = struct.unpack_from('<I', fdshap, pos)[0]
    next_pos = 4 * (i + 1) + 10
    next_offset = struct.unpack_from('<I', fdshap, next_pos)[0] if i + 1 < count else len(fdshap)
    size = next_offset - offset
    
    if size > 0 and size < 200000:
        w, h = struct.unpack_from('<HH', fdshap, offset)
        if w == 24 and h == 24:
            tile_resources.append({
                'index': i,
                'size': size,
                'w': w,
                'h': h
            })

print(f"24x24 tile资源数量: {len(tile_resources)}")
print(f"前10个tile资源:")
for tr in tile_resources[:10]:
    print(f"  资源{tr['index']}: size={tr['size']}")
