#!/usr/bin/env python3
"""
查找FDOTHER.DAT中的调色板资源
调色板通常是768字节 (256色 × 3字节)
"""
import struct

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"

with open(dat_path, 'rb') as f:
    data = f.read()

# 读取索引表
NUM_INDICES = 422
offsets = []
for i in range(NUM_INDICES):
    offset = struct.unpack_from('<I', data, 6 + i * 4)[0]
    offsets.append(offset)

print("查找大小接近768字节的资源:")
print("=" * 50)

for i in range(len(offsets) - 1):
    size = offsets[i + 1] - offsets[i]
    # 查找大小在700-850字节之间的资源
    if 700 <= size <= 850:
        print(f"索引 {i}: 偏移 {offsets[i]}, 大小 {size}")
        
        # 查看前24字节（8个颜色）
        resource_start = offsets[i]
        print(f"  前24字节: {' '.join(f'{b:02X}' for b in data[resource_start:resource_start + 24])}")
        
        # 检查是否是有效的调色板（有多种不同的颜色）
        unique_colors = set()
        for j in range(min(256, size // 3)):
            r = data[resource_start + j * 3]
            g = data[resource_start + j * 3 + 1]
            b = data[resource_start + j * 3 + 2]
            unique_colors.add((r, g, b))
        
        print(f"  唯一颜色数: {len(unique_colors)}")
        print()

print("\n查找大小正好是768字节的资源:")
print("=" * 50)

for i in range(len(offsets) - 1):
    size = offsets[i + 1] - offsets[i]
    if size == 768:
        print(f"索引 {i}: 偏移 {offsets[i]}, 大小 {size}")
        
        resource_start = offsets[i]
        unique_colors = set()
        for j in range(256):
            r = data[resource_start + j * 3]
            g = data[resource_start + j * 3 + 1]
            b = data[resource_start + j * 3 + 2]
            unique_colors.add((r, g, b))
        
        print(f"  唯一颜色数: {len(unique_colors)}")
        print(f"  前10色:")
        for j in range(10):
            r = data[resource_start + j * 3]
            g = data[resource_start + j * 3 + 1]
            b = data[resource_start + j * 3 + 2]
            print(f"    颜色{j}: ({r}, {g}, {b})")
        print()
