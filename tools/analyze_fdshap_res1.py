#!/usr/bin/env python3
"""分析FDSHAP资源1的前100字节"""

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

# 打印前200字节，每行16字节
data = fdshap[offset:offset+200]
for i in range(0, len(data), 16):
    hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
    print(f"{i:04x}: {hex_str:<48} {ascii_str}")

# 解析前4字节
w, h = struct.unpack_from('<HH', fdshap, offset)
print(f"\n头部: w={w}, h={h}")

# 从偏移4开始，每隔4字节读取一个值，看看是否是偏移表
print(f"\n从偏移4开始，每4字节的值:")
for i in range(10):
    pos = offset + 4 + i * 4
    val = struct.unpack_from('<I', fdshap, pos)[0]
    print(f"  [{i}] {val} (0x{val:x})")
