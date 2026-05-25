#!/usr/bin/env python3
"""
详细分析嵌套DAT的索引表结构

问题：嵌套DAT报告有130个资源，但只有29个有效偏移。
需要检查索引表的实际格式和值。
"""
import os
import struct

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"

with open(dat_path, 'rb') as f:
    data = f.read()

# 读取主索引表（正确的格式：从偏移6开始，每4字节一个偏移值）
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
print(f"  主DAT大小: {idx63_end - idx63_start}")
print(f"  嵌套DAT大小: {len(nested_dat)}")

# 检查嵌套DAT头部
print(f"\n嵌套DAT头部:")
print(f"  Magic: {nested_dat[:6]}")
nested_count = struct.unpack_from('<I', nested_dat, 6)[0]
print(f"  [6-9] 资源数量: {nested_count}")

# 输出索引表的前20个值
print(f"\n嵌套DAT索引表（前20个条目）:")
nested_offsets_start = 10
for i in range(min(20, nested_count)):
    addr = nested_offsets_start + i * 4
    if addr + 4 > len(nested_dat):
        break
    offset = struct.unpack_from('<I', nested_dat, addr)[0]
    print(f"  [{i}] 0x{offset:08X} ({offset}) {'< 嵌套DAT大小' if offset < len(nested_dat) else '>= 嵌套DAT大小'}")

# 检查索引表中的所有值
print(f"\n检查索引表中的所有{nested_count}个条目:")
valid_count = 0
for i in range(nested_count):
    addr = nested_offsets_start + i * 4
    if addr + 4 > len(nested_dat):
        print(f"  [{i}] 地址超出范围")
        break
    offset = struct.unpack_from('<I', nested_dat, addr)[0]
    if offset < len(nested_dat):
        valid_count += 1

print(f"  有效偏移数: {valid_count} / {nested_count}")

# 尝试 [offset:4][size:4] 格式
print(f"\n尝试 [offset:4][size:4] 格式（前10个条目）:")
for i in range(min(10, nested_count)):
    addr = nested_offsets_start + i * 8
    if addr + 8 > len(nested_dat):
        break
    offset = struct.unpack_from('<I', nested_dat, addr)[0]
    size = struct.unpack_from('<I', nested_dat, addr + 4)[0]
    print(f"  [{i}] 偏移 0x{offset:08X} ({offset}), 大小 {size}")
    if offset + size <= len(nested_dat):
        # 查看该偏移处的数据
        tile_data = nested_dat[offset:offset + 16]
        hex_str = ' '.join(f'{b:02X}' for b in tile_data)
        print(f"      数据: {hex_str}")
