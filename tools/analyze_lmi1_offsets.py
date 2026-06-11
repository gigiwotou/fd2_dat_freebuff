#!/usr/bin/env python
"""
分析LMI1 offset表的正确性
"""
import struct
import os

fdother_path = r"d:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT"

with open(fdother_path, 'rb') as f:
    data = f.read()

# 解析偏移表
offsets = []
pos = 6
while pos + 4 <= len(data):
    off = struct.unpack('<I', data[pos:pos+4])[0]
    if off == 0 or off > len(data):
        break
    offsets.append(off)
    pos += 4
offsets.append(len(data))

print("LMI1资源分析")
print("=" * 70)

lmi1_indices = [3, 5, 6, 9, 13, 14, 29]

for idx in lmi1_indices:
    start = offsets[idx]
    end = offsets[idx + 1]
    res_data = data[start:end]
    res_size = end - start

    if res_data[0:4] != b'LMI1':
        continue

    tile_count = struct.unpack('<H', res_data[4:6])[0]

    print(f"\n索引 {idx}: {res_size} bytes, {tile_count} tiles")

    # 解析所有偏移
    tile_offsets = []
    for i in range(tile_count + 1):
        off_pos = 6 + i * 4
        if off_pos + 4 <= res_size:
            off = struct.unpack('<I', res_data[off_pos:off_pos+4])[0]
            tile_offsets.append(off)

    # 计算tile大小
    tile_sizes = []
    for i in range(len(tile_offsets) - 1):
        size = tile_offsets[i+1] - tile_offsets[i]
        tile_sizes.append(size)

    # 统计
    if tile_sizes:
        avg_size = sum(tile_sizes) / len(tile_sizes)
        min_size = min(tile_sizes)
        max_size = max(tile_sizes)

        print(f"  Offset[0]: 0x{tile_offsets[0]:X} ({tile_offsets[0]})")
        print(f"  Offset[1]: 0x{tile_offsets[1]:X} ({tile_offsets[1]})")
        print(f"  Tile 0 大小: {tile_sizes[0]}")

        # 检查offset是否递增
        valid = all(tile_offsets[i] < tile_offsets[i+1] for i in range(len(tile_offsets)-1))
        print(f"  Offsets递增: {'是' if valid else '否'}")

        # 检查tile大小是否合理（假设最大64x64=4096）
        reasonable = all(s <= 5000 for s in tile_sizes)
        print(f"  Tile大小合理(<5000): {'是' if reasonable else '否'}")

        # 如果tile大小异常，打印样本
        if not reasonable:
            print(f"  前5个tile大小: {tile_sizes[:5]}")
