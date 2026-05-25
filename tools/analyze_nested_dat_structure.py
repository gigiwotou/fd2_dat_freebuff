#!/usr/bin/env python3
"""
分析嵌套DAT的索引表结构

问题：嵌套DAT报告有130个资源，但偏移表只有29个条目。
需要检查索引表的实际格式。
"""
import os
import struct

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"

with open(dat_path, 'rb') as f:
    data = f.read()

# 读取主索引表
NUM_INDICES = 422
offsets = []
for i in range(NUM_INDICES):
    offset = struct.unpack_from('<I', data, 6 + i * 4)[0]
    offsets.append(offset)

# 获取索引63
idx63_start = offsets[63]
idx63_end = offsets[64]
res_data = data[idx63_start:idx63_end]

print(f"索引63 大小: {len(res_data)}")
print(f"\n嵌套DAT头部:")
print(f"  Magic: {res_data[:6]}")
print(f"  [6-9] 数量: {struct.unpack_from('<I', res_data, 6)[0]}")

# 检查索引表格式
# 可能是 [offset:4][size:4] 格式
nested_count = struct.unpack_from('<I', res_data, 6)[0]
print(f"\n嵌套资源数量: {nested_count}")

# 尝试 [offset:4][size:4] 格式
nested_offsets_start = 10
print(f"\n尝试 [offset:4][size:4] 格式:")
for i in range(nested_count):
    addr = nested_offsets_start + i * 8
    if addr + 8 > len(res_data):
        break
    offset = struct.unpack_from('<I', res_data, addr)[0]
    size = struct.unpack_from('<I', res_data, addr + 4)[0]
    
    if offset < len(res_data):
        print(f"  [{i}] 偏移 0x{offset:06X} ({offset:6d}), 大小 {size:6d}")
        # 查看该偏移处的数据
        if offset + 16 <= len(res_data):
            hex_str = ' '.join(f'{b:02X}' for b in res_data[offset:offset+16])
            print(f"      数据: {hex_str}")
    else:
        print(f"  [{i}] 偏移 0x{offset:08X} (超出范围)")
        break
