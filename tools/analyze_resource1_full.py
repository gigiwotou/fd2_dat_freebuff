#!/usr/bin/env python3
"""分析FDSHAP资源1的完整结构"""

import struct
from pathlib import Path

fdshap = Path("game/FDSHAP.DAT").read_bytes()

# 获取资源1
res1_pos = 4 * 1 + 10
res1_offset = struct.unpack_from('<I', fdshap, res1_pos)[0]
res1_next = struct.unpack_from('<I', fdshap, res1_pos + 4)[0]
res1_size = res1_next - res1_offset

print(f"资源1: offset={res1_offset}, size={res1_size}")

# 打印前1000字节
print(f"\n前1000字节:")
data = fdshap[res1_offset:res1_offset+1000]
for i in range(0, len(data), 32):
    hex_str = ' '.join(f'{b:02x}' for b in data[i:i+32])
    print(f"{i:04x}: {hex_str}")

# 查找所有24x24 tile header (18 00 18 00)
print("\n=== 查找所有24x24 tile header ===")
tile_positions = []
search_data = fdshap[res1_offset:res1_offset+res1_size]
pos = 0
while True:
    pos = search_data.find(b'\x18\x00\x18\x00', pos)
    if pos == -1:
        break
    tile_positions.append(pos)
    pos += 1

print(f"找到 {len(tile_positions)} 个24x24 header")
print(f"前20个位置: {tile_positions[:20]}")

if len(tile_positions) > 1:
    # 计算间距
    diffs = [tile_positions[i+1] - tile_positions[i] for i in range(min(20, len(tile_positions)-1))]
    print(f"前20个间距: {diffs[:20]}")
    avg = sum(diffs) / len(diffs)
    print(f"平均间距: {avg:.0f}")
    print(f"估算tile总数: {res1_size / avg:.0f}")
