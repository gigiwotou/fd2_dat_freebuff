#!/usr/bin/env python3
"""
分析嵌套DAT结构，检查索引0是否为调色板
"""
import struct

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"

with open(dat_path, 'rb') as f:
    data = f.read()

def read_dat_resource(file_data, base_offset, index):
    """正确的DAT读取方式"""
    index_offset = base_offset + 4 * index + 6
    if index_offset + 8 > len(file_data):
        return None, 0, 0
    offset0 = struct.unpack_from('<I', file_data, index_offset)[0]
    offset1 = struct.unpack_from('<I', file_data, index_offset + 4)[0]
    size = offset1 - offset0
    if size <= 0 or offset0 >= len(file_data):
        return None, 0, 0
    resource_data = file_data[offset0:offset0 + size]
    return resource_data, offset0, size

# 分析嵌套DAT索引12
idx12_data, _, _ = read_dat_resource(data, 0, 12)
print(f"索引12 (嵌套DAT):")
print(f"  Magic: {idx12_data[:6]}")
nested_count = struct.unpack_from('<I', idx12_data, 6)[0]
print(f"  嵌套资源数量: {nested_count}")

# 检查索引0是否可能是调色板
res0_data, res0_offset, res0_size = read_dat_resource(idx12_data, 0, 0)
print(f"\n  嵌套资源0:")
print(f"    偏移: {res0_offset}")
print(f"    大小: {res0_size}")
if res0_size >= 4:
    w = struct.unpack_from('<H', res0_data, 0)[0]
    h = struct.unpack_from('<H', res0_data, 2)[0]
    print(f"    尺寸: {w}x{h}")

# 检查嵌套DAT前122字节（索引表）
print(f"\n  嵌套DAT索引表前10项:")
for i in range(10):
    addr = 8 + i * 4
    offset = struct.unpack_from('<I', idx12_data, addr)[0]
    print(f"    [{i}] 偏移: {offset}")

# 分析索引63
idx63_data, _, _ = read_dat_resource(data, 0, 63)
print(f"\n索引63 (嵌套DAT):")
print(f"  Magic: {idx63_data[:6]}")
nested_count = struct.unpack_from('<I', idx63_data, 6)[0]
print(f"  嵌套资源数量: {nested_count}")

# 检查索引0
res0_data, res0_offset, res0_size = read_dat_resource(idx63_data, 0, 0)
print(f"\n  嵌套资源0:")
print(f"    偏移: {res0_offset}")
print(f"    大小: {res0_size}")
if res0_size >= 4:
    w = struct.unpack_from('<H', res0_data, 0)[0]
    h = struct.unpack_from('<H', res0_data, 2)[0]
    print(f"    尺寸: {w}x{h}")
