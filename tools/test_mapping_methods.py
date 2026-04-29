#!/usr/bin/env python3
"""对比不同地形ID映射方式"""
import struct
from PIL import Image

fdfield = open("game/FDFIELD.DAT", "rb").read()
fdshap = open("game/FDSHAP.DAT", "rb").read()

# 解析FDFIELD
fdfield_offsets = []
pos = 6
while pos < len(fdfield) - 4:
    o = struct.unpack_from("<I", fdfield, pos)[0]
    if o > pos and o < len(fdfield):
        fdfield_offsets.append(o)
    else:
        break
    pos += 4

layout_data = fdfield[fdfield_offsets[0]:fdfield_offsets[1]]
w = struct.unpack_from("<H", layout_data, 0)[0]
h = struct.unpack_from("<H", layout_data, 2)[0]

terrain_ids = []
for i in range(w * h):
    pos = 4 + 4 * i
    tid = struct.unpack_from("<H", layout_data, pos)[0]
    terrain_ids.append(tid)

# 解析FDSHAP
fdshap_count = struct.unpack_from("<I", fdshap, 6)[0]
fdshap_offsets = [struct.unpack_from("<I", fdshap, 10 + i * 4)[0] for i in range(fdshap_count)]
tile_set_data = fdshap[fdshap_offsets[1]:fdshap_offsets[2]]
tile_w = struct.unpack_from("<H", tile_set_data, 0)[0]
tile_h = struct.unpack_from("<H", tile_set_data, 2)[0]
tile_count = struct.unpack_from("<H", tile_set_data, 4)[0]

tile_offsets = []
pos = 6
for i in range(tile_count):
    off = struct.unpack_from("<I", tile_set_data, pos)[0]
    tile_offsets.append(off)
    pos += 4

print(f"Map: {w}x{h} = {w*h} tiles")
print(f"Terrain ID range: {min(terrain_ids)}-{max(terrain_ids)}, unique: {len(set(terrain_ids))}")
print(f"Tile count: {tile_count}")
print()

# 对比映射方式
for name, func in [
    ("& 0x7F (7 bits)", lambda x: x & 0x7F),
    ("% tile_count", lambda x: x % tile_count),
    ("direct", lambda x: x),
]:
    rendered = 0
    tile_indices_used = set()
    for tid in terrain_ids:
        idx = func(tid)
        if 0 <= idx < len(tile_offsets):
            rendered += 1
            tile_indices_used.add(idx)
    print(f"{name}: {rendered}/{w*h}, tiles used: {len(tile_indices_used)}")
