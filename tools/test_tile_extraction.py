#!/usr/bin/env python3
"""分析资源1的前1000字节，查找多个24x24 tile"""

import struct
from pathlib import Path

fdshap = Path("game/FDSHAP.DAT").read_bytes()

# 获取资源1
pos = 4 * 1 + 10
offset = struct.unpack_from('<I', fdshap, pos)[0]
next_pos = 4 * 2 + 10
next_offset = struct.unpack_from('<I', fdshap, next_pos)[0]
size = next_offset - offset

print(f"资源1: offset={offset}, size={size}")
print(f"前200字节: {fdshap[offset:offset+200].hex()}")

# 解析多个tile，每个tile: 4字节header (w,h) + RLE数据
# RLE数据大小未知，但24x24=576像素，压缩后大约600-2000字节
pos = offset
tile_count = 0
tile_offsets = []

while pos < offset + size - 4 and tile_count < 300:
    w, h = struct.unpack_from('<HH', fdshap, pos)
    
    if w == 24 and h == 24:
        tile_offsets.append(pos - offset)
        tile_count += 1
        # 跳过header
        pos += 4
        # RLE数据：假设平均每个tile约1500字节
        # 我们需要找下一个24x24的header
        for search in range(pos, min(pos + 3000, offset + size - 4)):
            nw, nh = struct.unpack_from('<HH', fdshap, search)
            if nw == 24 and nh == 24:
                pos = search
                break
        else:
            break
    else:
        pos += 1

print(f"\n找到 {tile_count} 个24x24 tile")
print(f"Tile偏移: {tile_offsets[:20]}...")

# 计算tile之间的平均距离
if len(tile_offsets) > 1:
    distances = [tile_offsets[i+1] - tile_offsets[i] for i in range(min(10, len(tile_offsets)-1))]
    avg_distance = sum(distances) / len(distances)
    print(f"前10个tile的平均间距: {avg_distance:.0f} 字节")
