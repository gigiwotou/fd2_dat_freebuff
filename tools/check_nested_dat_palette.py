#!/usr/bin/env python3
"""
检查嵌套DAT是否包含调色板资源
分析嵌套DAT的完整结构
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

# 分析嵌套DAT索引7
idx7_data, _, _ = read_dat_resource(data, 0, 7)
print(f"嵌套DAT 索引7:")
print(f"  总大小: {len(idx7_data)}")
print(f"  Magic: {idx7_data[:6]}")

# 嵌套资源数量
nested_count = struct.unpack_from('<I', idx7_data, 6)[0]
print(f"  嵌套资源数量: {nested_count}")

# 检查嵌套资源0（320x200 tile）
res0_data, res0_offset, res0_size = read_dat_resource(idx7_data, 0, 0)
print(f"\n嵌套资源0:")
print(f"  偏移: {res0_offset}")
print(f"  大小: {res0_size}")
if res0_size >= 4:
    w = struct.unpack_from('<H', res0_data, 0)[0]
    h = struct.unpack_from('<H', res0_data, 2)[0]
    print(f"  尺寸: {w}x{h}")
    print(f"  前20字节: {' '.join(f'{b:02X}' for b in res0_data[:20])}")

# 检查嵌套资源1-6
for i in range(1, 7):
    res_data, res_offset, res_size = read_dat_resource(idx7_data, 0, i)
    if res_data:
        w = struct.unpack_from('<H', res_data, 0)[0]
        h = struct.unpack_from('<H', res_data, 2)[0]
        print(f"  嵌套资源{i}: {w}x{h}, 大小 {res_size}")
        print(f"    前12字节: {' '.join(f'{b:02X}' for b in res_data[:12])}")
