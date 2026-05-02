#!/usr/bin/env python3
"""
详细分析res78头部，找到正确的样本偏移
"""
import struct
import os

dat_path = os.path.join('game', 'FDOTHER.DAT')

with open(dat_path, 'rb') as f:
    magic = f.read(6)
    count = struct.unpack('<I', f.read(4))[0]
    
    f.seek(0x0A)
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])

idx = 78
start = offsets[idx]
end = offsets[idx + 1] if idx + 1 < count else os.path.getsize(dat_path)
size = end - start

with open(dat_path, 'rb') as f:
    f.seek(start)
    raw = f.read(size)

print(f"res78总大小: {size} bytes")
print(f"\n前256字节详细分析:")
for i in range(0, min(256, len(raw)), 16):
    hex_str = ' '.join(f'{b:02x}' for b in raw[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in raw[i:i+16])
    print(f"  {i:04x}: {hex_str:<48s} {ascii_str}")

# 尝试不同的字段解释
print(f"\n可能的偏移字段分析:")
for offset in [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]:
    if offset + 4 <= len(raw):
        val = struct.unpack_from('<I', raw, offset)[0]
        if val < size and val > 0:
            print(f"  *({offset}) = {val} (0x{val:x}) - 在范围内")

# 检查是否有子偏移表
print(f"\n查找可能的样本边界:")
for i in range(0, min(64, size-4), 2):
    val = struct.unpack_from('<H', raw, i)[0]
    if val > 0 and val < size:
        print(f"  偏移{i} (WORD): {val}")

# 重点: 检查*(0x10)和*(0x14)等
print(f"\n关键位置值:")
for offset in [0x10, 0x14, 0x18, 0x1C, 0x20, 0x24]:
    if offset + 4 <= len(raw):
        val = struct.unpack_from('<I', raw, offset)[0]
        print(f"  *(0x{offset:x}) = {val} (0x{val:x})")
