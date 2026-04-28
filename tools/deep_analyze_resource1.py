#!/usr/bin/env python3
"""深度分析FDSHAP资源1的结构"""

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

# 从偏移4开始，分析数据结构
# 可能是: 偏移表 + 压缩数据
# 或者是: 整个大图像的压缩数据

# 打印前500字节，查找模式
print(f"\n前500字节(hex):")
data = fdshap[offset:offset+500]
for i in range(0, len(data), 16):
    hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
    print(f"  {i:04x}: {hex_str}")

# 检查是否有递增的偏移值表
print(f"\n从偏移4开始，每2字节的值:")
for i in range(100):
    pos = offset + 4 + i * 2
    val = struct.unpack_from('<H', fdshap, pos)[0]
    if val < 100000:  # 只打印合理的偏移值
        print(f"  [{i}] {val}")
