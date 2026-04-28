#!/usr/bin/env python3
"""验证FDSHAP资源1的偏移表结构"""

import struct
from pathlib import Path

fdshap = Path("game/FDSHAP.DAT").read_bytes()
count = struct.unpack_from('<I', fdshap, 6)[0]

# 获取资源1
pos = 4 * 1 + 10
offset = struct.unpack_from('<I', fdshap, pos)[0]
next_pos = 4 * 2 + 10
next_offset = struct.unpack_from('<I', fdshap, next_pos)[0]
size = next_offset - offset

print(f"资源1: offset={offset}, size={size}")

# 前4字节是w=24, h=24
w, h = struct.unpack_from('<HH', fdshap, offset)
print(f"头部: w={w}, h={h}")

# 从偏移4开始是偏移表，每4字节一个条目: [tile_offset][0x0000]
# 读取所有偏移
tile_offsets = []
pos = offset + 4
while pos < offset + size - 4:
    tile_offset = struct.unpack_from('<H', fdshap, pos)[0]
    zero = struct.unpack_from('<H', fdshap, pos + 2)[0]
    
    if zero == 0 and tile_offset > 0 and tile_offset < size:
        tile_offsets.append(tile_offset)
        pos += 4
    else:
        break

print(f"\n找到 {len(tile_offsets)} 个tile偏移")
print(f"前20个偏移: {tile_offsets[:20]}")

# 验证这些偏移是否指向有效的tile数据
# 每个tile是24x24=576像素，RLE压缩后约1000-2000字节
for i, tile_off in enumerate(tile_offsets[:10]):
    # 检查偏移处的数据
    data_at_offset = fdshap[offset + tile_off:offset + tile_off + 4]
    print(f"Tile {i} at offset {tile_off}: {data_at_offset.hex()}")

# 计算tile之间的平均距离
if len(tile_offsets) > 1:
    distances = [tile_offsets[i+1] - tile_offsets[i] for i in range(min(20, len(tile_offsets)-1))]
    avg = sum(distances) / len(distances)
    print(f"\n前20个tile的平均间距: {avg:.0f} 字节")
    print(f"估算的tile总数: {size / avg:.0f}")
