#!/usr/bin/env python3
"""分析资源1的前200字节，查找偏移表"""

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

# 前4字节是w=24, h=24
w, h = struct.unpack_from('<HH', fdshap, offset)
print(f"头部: w={w}, h={h}")

# 分析从offset+4开始的字节，看看是否是偏移表
print("\n=== 分析offset+4开始的数据（可能是偏移表）===")
data_start = offset + 4

for i in range(50):
    pos = data_start + i * 4
    if pos >= offset + size - 4:
        break
    
    val = struct.unpack_from('<I', fdshap, pos)[0]
    print(f"偏移[{i}]: {val} (0x{val:x})")

# 检查这些值是否递增（如果是偏移表）
print("\n=== 检查偏移是否递增 ===")
offsets = []
for i in range(min(100, (size - 4) // 4)):
    pos = data_start + i * 4
    val = struct.unpack_from('<I', fdshap, pos)[0]
    offsets.append(val)

# 打印前30个偏移和它们之间的差值
for i in range(min(30, len(offsets))):
    if i > 0:
        diff = offsets[i] - offsets[i-1]
        print(f"偏移[{i}]={offsets[i]}, 差值={diff}")
    else:
        print(f"偏移[{i}]={offsets[i]}")
