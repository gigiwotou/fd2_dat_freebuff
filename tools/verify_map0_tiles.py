#!/usr/bin/env python3
"""验证地图0的瓦片索引是否正确"""
import struct
from PIL import Image
from pathlib import Path

GAME_DIR = Path(__file__).parent.parent / "game"
OUTPUT_DIR = Path(__file__).parent.parent / "output"

# 读取FDFIELD.DAT
with open(GAME_DIR / "FDFIELD.DAT", "rb") as f:
    fdfield_data = f.read()

# 解析FDFIELD偏移表
fdfield_offsets = []
pos = 6
while pos < len(fdfield_data) - 4:
    offset = struct.unpack_from("<I", fdfield_data, pos)[0]
    if offset > pos and offset < len(fdfield_data):
        fdfield_offsets.append(offset)
    else:
        break
    pos += 4

# 地图0的layout数据
layout_start = fdfield_offsets[0]
layout_end = fdfield_offsets[1]
layout_data = fdfield_data[layout_start:layout_end]

map_width = struct.unpack_from("<H", layout_data, 0)[0]
map_height = struct.unpack_from("<H", layout_data, 2)[0]

print(f"地图0尺寸: {map_width}x{map_height}")
print(f"\n前20个瓦片的地形ID (layout数据从byte 4开始):")

pos = 4
for i in range(min(20, map_width * map_height)):
    terrain_4bytes = layout_data[pos:pos+4]
    byte0 = terrain_4bytes[0]
    byte1 = terrain_4bytes[1]
    terrain_id = byte0 | ((byte1 & 0x03) << 8)
    print(f"  瓦片[{i:2d}] (x={i%map_width}, y={i//map_width}): byte[0-3]={terrain_4bytes.hex(' ')} -> terrain_id={terrain_id}")
    pos += 4

# 读取FDSHAP.DAT
with open(GAME_DIR / "FDSHAP.DAT", "rb") as f:
    fdshap_data = f.read()

# 解析FDSHAP偏移表（格式1：有计数）
fdshap_count = struct.unpack_from("<I", fdshap_data, 6)[0]
fdshap_offsets = []
for i in range(fdshap_count):
    offset = struct.unpack_from("<I", fdshap_data, 10 + i * 4)[0]
    fdshap_offsets.append(offset)

print(f"\nFDSHAP.DAT资源数: {fdshap_count}")

# 地图0的terrain_set_id从control数据读取
control_start = fdfield_offsets[1]
control_end = fdfield_offsets[2]
control_data = fdfield_data[control_start:control_end]
terrain_set_id = control_data[0]

print(f"地图0 terrain_set_id: {terrain_set_id}")

# FDSHAP资源索引
palette_res_idx = terrain_set_id * 2
tile_set_res_idx = terrain_set_id * 2 + 1

print(f"调色板资源索引: {palette_res_idx}")
print(f"瓦片集资源索引: {tile_set_res_idx}")

# 瓦片集
tile_set_start = fdshap_offsets[tile_set_res_idx]
tile_set_end = fdshap_offsets[tile_set_res_idx + 1]
tile_set_data = fdshap_data[tile_set_start:tile_set_end]

# 解析瓦片头
tile_w = struct.unpack_from("<H", tile_set_data, 0)[0]
tile_h = struct.unpack_from("<H", tile_set_data, 2)[0]
tile_count = struct.unpack_from("<H", tile_set_data, 4)[0]

print(f"\n瓦片集头:")
print(f"  瓦片尺寸: {tile_w}x{tile_h}")
print(f"  瓦片数量: {tile_count}")

# 瓦片偏移表
tile_offsets = []
pos = 6
for i in range(tile_count):
    offset = struct.unpack_from("<I", tile_set_data, pos)[0]
    tile_offsets.append(offset)
    pos += 4

print(f"  解析到 {len(tile_offsets)} 个瓦片偏移")
print(f"\n前10个瓦片的offset:")
for i in range(min(10, len(tile_offsets))):
    if i + 1 < len(tile_offsets):
        size = tile_offsets[i+1] - tile_offsets[i]
    else:
        size = len(tile_set_data) - tile_offsets[i]
    print(f"  瓦片[{i:2d}]: offset={tile_offsets[i]:6d}, size={size:6d}")

# 测试：地形ID 8应该对应哪个瓦片？
terrain_id_8 = 8
tile_idx_8 = terrain_id_8 % tile_count
print(f"\n地形ID 8 -> 瓦片索引 {tile_idx_8}")
if tile_idx_8 < len(tile_offsets):
    offset_8 = tile_offsets[tile_idx_8]
    next_offset_8 = tile_offsets[tile_idx_8 + 1] if tile_idx_8 + 1 < len(tile_offsets) else len(tile_set_data)
    print(f"  瓦片offset: {offset_8}")
    print(f"  瓦片size: {next_offset_8 - offset_8}")
