#!/usr/bin/env python3
"""分析地图0的地形ID范围"""
import struct

with open('game/FDFIELD.DAT', 'rb') as f:
    data = f.read()

# 解析FDFIELD偏移表（格式2）
fdfield_offsets = []
pos = 6
while pos < len(data) - 4:
    offset = struct.unpack_from("<I", data, pos)[0]
    if offset > pos and offset < len(data):
        fdfield_offsets.append(offset)
    else:
        break
    pos += 4

# 地图0的layout数据
layout_start = fdfield_offsets[0]
layout_data = data[layout_start:]

map_width = struct.unpack_from("<H", layout_data, 0)[0]
map_height = struct.unpack_from("<H", layout_data, 2)[0]

print(f"地图0: {map_width}x{map_height}")

# 解析地形ID
terrain_ids = []
pos = 4
for i in range(map_width * map_height):
    if pos + 4 > len(layout_data):
        break
    # 方式1：直接读取WORD
    terrain_id_word = struct.unpack_from("<H", layout_data, pos)[0]
    # 方式2：IDA公式 byte[0] | ((byte[1] & 0x03) << 8)
    byte0 = layout_data[pos]
    byte1 = layout_data[pos + 1]
    terrain_id_ida = byte0 | ((byte1 & 0x03) << 8)
    
    terrain_ids.append((terrain_id_word, terrain_id_ida))
    pos += 4

# 统计
word_ids = [t[0] for t in terrain_ids]
ida_ids = [t[1] for t in terrain_ids]

print(f"\n方式1 (WORD): 范围 {min(word_ids)}-{max(word_ids)}, 唯一值 {len(set(word_ids))}")
print(f"方式2 (IDA):  范围 {min(ida_ids)}-{max(ida_ids)}, 唯一值 {len(set(ida_ids))}")

# 如果瓦片有288个
print(f"\n瓦片集有288个瓦片:")
print(f"  方式1 & 0x7F: {len([t for t in word_ids if (t & 0x7F) < 288])} 个瓦片在范围内")
print(f"  方式1 直接: {len([t for t in word_ids if t < 288])} 个瓦片在范围内")
print(f"  方式2 & 0x7F: {len([t for t in ida_ids if (t & 0x7F) < 288])} 个瓦片在范围内")
print(f"  方式2 直接: {len([t for t in ida_ids if t < 288])} 个瓦片在范围内")

# 打印前20个地形ID
print(f"\n前20个瓦片的地形ID:")
for i in range(min(20, len(terrain_ids))):
    word, ida = terrain_ids[i]
    print(f"  [{i:2d}] WORD={word:4d} (0x{word:04x}), IDA={ida:4d} (0x{ida:04x}), WORD&0x7F={word & 0x7F}, IDA&0x7F={ida & 0x7F}")
