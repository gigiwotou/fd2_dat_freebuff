#!/usr/bin/env python3
"""验证正确的地形ID解析和瓦片映射"""
import struct
from PIL import Image

fdfield = open("game/FDFIELD.DAT", "rb").read()
fdshap = open("game/FDSHAP.DAT", "rb").read()

# 解析FDFIELD偏移表
fdfield_offsets = []
pos = 6
while pos < len(fdfield) - 4:
    o = struct.unpack_from("<I", fdfield, pos)[0]
    if o > pos and o < len(fdfield):
        fdfield_offsets.append(o)
    else:
        break
    pos += 4

layout_start = fdfield_offsets[0]
layout_end = fdfield_offsets[1]
layout_data = fdfield[layout_start:layout_end]

w = struct.unpack_from("<H", layout_data, 0)[0]
h = struct.unpack_from("<H", layout_data, 2)[0]
print(f"Map 0: {w}x{h} = {w*h} tiles")

# 解析地形ID (从byte 4开始，每瓦片4字节)
terrain_ids = []
for i in range(w * h):
    pos = 4 + 4 * i
    b0 = layout_data[pos]
    b1 = layout_data[pos + 1]
    tid = b0 | (b1 << 8)
    terrain_ids.append(tid)

print(f"Terrain ID range: {min(terrain_ids)}-{max(terrain_ids)}")
print(f"Unique IDs: {len(set(terrain_ids))}")

# 解析FDSHAP资源
fdshap_count = struct.unpack_from("<I", fdshap, 6)[0]
fdshap_offsets = []
for i in range(fdshap_count):
    fdshap_offsets.append(struct.unpack_from("<I", fdshap, 10 + i * 4)[0])

# 使用资源0和1（terrain_set_id=0）
palette_start = fdshap_offsets[0]
palette_end = fdshap_offsets[1]
palette_data = fdshap[palette_start:palette_end]

tile_start = fdshap_offsets[1]
tile_end = fdshap_offsets[2]
tile_set_data = fdshap[tile_start:tile_end]

tile_w = struct.unpack_from("<H", tile_set_data, 0)[0]
tile_h = struct.unpack_from("<H", tile_set_data, 2)[0]
tile_count = struct.unpack_from("<H", tile_set_data, 4)[0]
print(f"Tile set: {tile_w}x{tile_h}, {tile_count} tiles")

# 解析瓦片偏移表（从byte 6开始）
tile_offsets = []
pos = 6
for i in range(tile_count):
    if pos + 4 > len(tile_set_data):
        break
    off = struct.unpack_from("<I", tile_set_data, pos)[0]
    tile_offsets.append(off)
    pos += 4

print(f"Tile offsets found: {len(tile_offsets)}")

# 测试不同地形ID映射方式
for map_name, map_func in [("raw", lambda x: x), ("mod192", lambda x: x % 192)]:
    rendered = 0
    for tid in terrain_ids:
        tile_idx = map_func(tid)
        if tile_idx < len(tile_offsets):
            rendered += 1
    print(f"{map_name}: rendered {rendered}/{w*h}")
