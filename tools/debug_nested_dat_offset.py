#!/usr/bin/env python3
"""
验证嵌套DAT偏移是否相对于主DAT文件
"""
import os
import struct
from PIL import Image

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"

with open(dat_path, 'rb') as f:
    data = f.read()

# 读取主索引表
NUM_INDICES = 422
main_offsets = []
for i in range(NUM_INDICES):
    offset = struct.unpack_from('<I', data, 6 + i * 4)[0]
    main_offsets.append(offset)

# 获取索引63
idx63_start = main_offsets[63]
idx63_end = main_offsets[64] if 64 < len(main_offsets) else len(data)
nested_dat = data[idx63_start:idx63_end]

print(f"索引63:")
print(f"  主DAT偏移: 0x{idx63_start:08X} ({idx63_start})")
print(f"  嵌套DAT大小: {len(nested_dat)}")

# 读取嵌套DAT头部
nested_count = struct.unpack_from('<I', nested_dat, 6)[0]
print(f"  资源数量: {nested_count}")

# 测试假设：偏移是相对于主DAT的
print(f"\n测试假设1：偏移相对于主DAT文件")
nested_offsets_start = 10
for i in range(min(10, nested_count)):
    addr = nested_offsets_start + i * 4
    if addr + 4 > len(nested_dat):
        break
    nested_offset = struct.unpack_from('<I', nested_dat, addr)[0]
    absolute_offset = idx63_start + nested_offset
    print(f"  [{i}] 嵌套内偏移: 0x{nested_offset:08X} ({nested_offset}), 绝对偏移: 0x{absolute_offset:08X} ({absolute_offset})")
    if absolute_offset < len(data):
        # 查看数据
        tile_data = data[absolute_offset:absolute_offset + 16]
        hex_str = ' '.join(f'{b:02X}' for b in tile_data)
        print(f"      数据: {hex_str}")

# 测试假设2：偏移就是绝对偏移
print(f"\n测试假设2：偏移就是绝对偏移")
for i in range(min(10, nested_count)):
    addr = nested_offsets_start + i * 4
    if addr + 4 > len(nested_dat):
        break
    nested_offset = struct.unpack_from('<I', nested_dat, addr)[0]
    if nested_offset < len(data):
        tile_data = data[nested_offset:nested_offset + 16]
        hex_str = ' '.join(f'{b:02X}' for b in tile_data)
        print(f"  [{i}] 偏移: 0x{nested_offset:08X} ({nested_offset})")
        print(f"      数据: {hex_str}")

# 测试假设3：检查嵌套DAT内的数据是否包含LMI1或tile头
print(f"\n测试假设3：检查嵌套DAT内的数据模式")
# 在嵌套DAT数据中搜索可能的tile数据模式
# Tile数据通常以宽度(2字节)和高度(2字节)开头
for search_offset in range(10, min(1000, len(nested_dat))):
    if search_offset + 4 > len(nested_dat):
        break
    w = struct.unpack_from('<H', nested_dat, search_offset)[0]
    h = struct.unpack_from('<H', nested_dat, search_offset + 2)[0]
    # 检查是否是合理的tile尺寸
    if 0 < w <= 320 and 0 < h <= 200:
        # 检查后续数据是否看起来像像素数据
        pixel_data_start = search_offset + 4
        if pixel_data_start + w * h <= len(nested_dat):
            # 检查像素值范围
            pixels = nested_dat[pixel_data_start:pixel_data_start + min(100, w * h)]
            max_pixel = max(pixels)
            min_pixel = min(pixels)
            print(f"  可能tile在偏移{search_offset}: {w}x{h}, 像素范围: {min_pixel}-{max_pixel}")
