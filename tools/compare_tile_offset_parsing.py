#!/usr/bin/env python3
"""对比两种瓦片偏移表解析方式"""
import struct

with open('game/FDSHAP.DAT', 'rb') as f:
    data = f.read()

# 解析FDSHAP偏移表（格式2）
fdshap_offsets = []
pos = 6
while pos < len(data) - 4:
    offset = struct.unpack_from("<I", data, pos)[0]
    if offset > pos and offset < len(data):
        fdshap_offsets.append(offset)
    else:
        break
    pos += 4

print(f"FDSHAP.DAT资源数: {len(fdshap_offsets)}")

# 地图0: terrain_set_id=0, 资源0
tile_set_res_idx = 0
tile_set_start = fdshap_offsets[tile_set_res_idx]
tile_set_end = fdshap_offsets[tile_set_res_idx + 1]
tile_set_data = data[tile_set_start:tile_set_end]

print(f"\n地图0瓦片集 (资源{tile_set_res_idx}):")
print(f"  大小: {len(tile_set_data)} 字节")

# 方式1：使用tile_count限制
tile_count_from_header = struct.unpack_from("<H", tile_set_data, 4)[0]
tile_width = struct.unpack_from("<H", tile_set_data, 0)[0]
tile_height = struct.unpack_from("<H", tile_set_data, 2)[0]

print(f"  瓦片头: {tile_set_data[:6].hex(' ')}")
print(f"  瓦片尺寸: {tile_width}x{tile_height}")
print(f"  Tile count (header): {tile_count_from_header}")

# 解析tile_count个偏移
tile_offsets_method1 = []
pos = 6
for i in range(tile_count_from_header):
    if pos + 4 > len(tile_set_data):
        break
    offset = struct.unpack_from("<I", tile_set_data, pos)[0]
    tile_offsets_method1.append(offset)
    pos += 4

print(f"\n方式1 (使用tile_count={tile_count_from_header}):")
print(f"  解析到 {len(tile_offsets_method1)} 个偏移")
print(f"  前5个偏移: {tile_offsets_method1[:5]}")

# 方式2：读取直到无效（像map_verify.py）
tile_offsets_method2 = []
pos = 6
while pos + 4 <= len(tile_set_data):
    offset = struct.unpack_from("<I", tile_set_data, pos)[0]
    if 0 < offset < len(tile_set_data):
        tile_offsets_method2.append(offset)
    else:
        break
    pos += 4

print(f"\n方式2 (读取直到无效):")
print(f"  解析到 {len(tile_offsets_method2)} 个偏移")
print(f"  前5个偏移: {tile_offsets_method2[:5]}")

# 对比
print(f"\n对比:")
print(f"  方式1: {len(tile_offsets_method1)} 个偏移")
print(f"  方式2: {len(tile_offsets_method2)} 个偏移")

if len(tile_offsets_method1) != len(tile_offsets_method2):
    print(f"\n  差异: {len(tile_offsets_method2) - len(tile_offsets_method1)}")
    print(f"  方式1的最后一个偏移: {tile_offsets_method1[-1]}")
    print(f"  方式2的第{len(tile_offsets_method1)}个偏移: {tile_offsets_method2[len(tile_offsets_method1)-1]}")
else:
    print(f"\n  两种方法结果相同")
