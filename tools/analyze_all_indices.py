#!/usr/bin/env python3
"""
分析FDOTHER.DAT所有索引，找出可能的图片资源
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

print("分析FDOTHER.DAT所有索引:")
print(f"总索引数: {NUM_INDICES}")
print(f"文件大小: {len(data)}")

# 分析每个资源的大小和可能的类型
print(f"\n{'索引':<5} {'偏移':<10} {'大小':<10} {'可能类型'}")
print("-" * 60)

for i in range(NUM_INDICES):
    size = offsets[i + 1] - offsets[i] if i + 1 < NUM_INDICES else len(data) - offsets[i]
    resource_data = data[offsets[i]:offsets[i] + min(20, size)]
    
    # 检查是否是tile数据 (w,h, pixel_data)
    possible_tile = False
    if size >= 4:
        w = struct.unpack_from('<H', resource_data, 0)[0]
        h = struct.unpack_from('<H', resource_data, 2)[0]
        if 0 < w <= 320 and 0 < h <= 200:
            expected_pixels = w * h
            # 如果是tile数据，大小应该接近 4 + 像素数
            if abs(size - (4 + expected_pixels)) < size * 0.5:
                possible_tile = True
    
    # 检查是否是嵌套DAT
    is_nested_dat = resource_data[:6] == b"LLLLLL"
    
    # 检查是否是调色板
    is_palette = size == 768
    
    type_str = ""
    if is_palette:
        type_str = "调色板"
    elif is_nested_dat:
        type_str = "嵌套DAT"
    elif possible_tile:
        type_str = f"Tile {w}x{h}"
    elif size < 100:
        type_str = "小资源"
    else:
        type_str = "其他"
    
    if i < 50 or possible_tile or is_nested_dat or is_palette:
        print(f"{i:<5} {offsets[i]:<10} {size:<10} {type_str}")
