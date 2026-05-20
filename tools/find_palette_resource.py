#!/usr/bin/env python3
"""查找FDOTHER.DAT中的调色板资源"""
import struct

with open('game/FDOTHER.DAT', 'rb') as f:
    data = f.read()

count = struct.unpack('<I', data[6:10])[0]
print(f"FDOTHER.DAT: {count} resources, size: {len(data)}\n")

# 解析所有资源偏移
for i in range(count - 1):
    s = struct.unpack_from('<I', data, 10 + i*4)[0]
    e = struct.unpack_from('<I', data, 10 + (i+1)*4)[0]
    sz = e - s
    if sz == 768:  # 256色 * 3字节
        print(f"索引 {i}: 大小 {sz} (可能是调色板)")
        # 分析前5个颜色
        for j in range(5):
            r, g, b = struct.unpack_from('<BBB', data, s + j*3)
            print(f"  颜色[{j}]: R={r:3d} G={g:3d} B={b:3d}")
