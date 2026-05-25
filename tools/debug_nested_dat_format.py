#!/usr/bin/env python3
"""
尝试不同格式解析嵌套DAT索引表
"""
import struct
from PIL import Image
import os

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
magic = nested_dat[:6]
nested_count = struct.unpack_from('<I', nested_dat, 6)[0]
print(f"  Magic: {magic}")
print(f"  资源数量: {nested_count}")

# 测试1: 假设索引表格式是 [offset:4][size:4] 从偏移10开始
print(f"\n测试1: 假设索引表格式是 [offset:4][size:4]")
nested_offsets_start = 10
entry_size = 8
for i in range(min(20, nested_count)):
    addr = nested_offsets_start + i * entry_size
    if addr + entry_size > len(nested_dat):
        break
    offset = struct.unpack_from('<I', nested_dat, addr)[0]
    size = struct.unpack_from('<I', nested_dat, addr + 4)[0]
    print(f"  [{i}] 偏移: 0x{offset:08X} ({offset}), 大小: {size}")
    if offset < len(nested_dat) and offset + size <= len(nested_dat):
        tile_data = nested_dat[offset:offset + min(20, size)]
        hex_str = ' '.join(f'{b:02X}' for b in tile_data)
        print(f"      数据: {hex_str}")

# 测试2: 假设偏移10开始的4字节不是索引表，而是其他头部信息
print(f"\n测试2: 检查偏移10-14的4字节值")
value_at_10 = struct.unpack_from('<I', nested_dat, 10)[0]
print(f"  [10-13] 值: 0x{value_at_10:08X} ({value_at_10})")
print(f"  这可能是第一个资源的实际偏移")

# 测试3: 假设索引表在嵌套DAT的末尾
print(f"\n测试3: 假设索引表在嵌套DAT末尾")
# 最后130*4 = 520字节可能是索引表
index_table_at_end = nested_dat[-(nested_count * 4):]
print(f"  从末尾读取 {nested_count * 4} 字节作为索引表")
for i in range(min(20, nested_count)):
    offset = struct.unpack_from('<I', index_table_at_end, i * 4)[0]
    print(f"  [{i}] 偏移: 0x{offset:08X} ({offset}) {'有效' if offset < len(nested_dat) else '无效'}")

# 测试4: 直接在嵌套DAT数据中搜索tile模式
print(f"\n测试4: 在嵌套DAT中搜索可能的tile数据")
# tile数据通常以宽度(2字节)和高度(2字节)开头
found_tiles = []
for search_offset in range(10, len(nested_dat) - 4):
    w = struct.unpack_from('<H', nested_dat, search_offset)[0]
    h = struct.unpack_from('<H', nested_dat, search_offset + 2)[0]
    if 0 < w <= 320 and 0 < h <= 200:
        # 检查是否是合理的tile尺寸
        found_tiles.append((search_offset, w, h))

print(f"  找到 {len(found_tiles)} 个可能的tile数据位置")
for offset, w, h in found_tiles[:30]:
    print(f"  偏移 {offset}: {w}x{h}")
