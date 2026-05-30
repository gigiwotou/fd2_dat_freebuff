#!/usr/bin/env python3
"""
检查嵌套DAT索引0的数据结构
确认是否可能是调色板而不是tile
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
print(f"嵌套DAT 索引12:")
print(f"  总大小: {len(idx12_data)}")
print(f"  Magic: {idx12_data[:6]}")

# 嵌套资源数量
nested_count = struct.unpack_from('<I', idx12_data, 6)[0]
print(f"  嵌套资源数量: {nested_count}")

# 检查嵌套资源0
res0_data, res0_offset, res0_size = read_dat_resource(idx12_data, 0, 0)
print(f"\n嵌套资源0:")
print(f"  偏移: {res0_offset}")
print(f"  大小: {res0_size}")
print(f"  前40字节: {' '.join(f'{b:02X}' for b in res0_data[:40])}")

# 尝试解析为tile
if res0_size >= 4:
    w = struct.unpack_from('<H', res0_data, 0)[0]
    h = struct.unpack_from('<H', res0_data, 2)[0]
    print(f"  解析为tile: {w}x{h}")
    print(f"  期望像素数: {w * h}")
    print(f"  RLE数据大小: {res0_size - 4}")
    
    # 检查是否是合理的tile
    if w == 320 and h == 200:
        print(f"  -> 320x200 tile，期望未压缩大小: {320 * 200} = 64000")
        print(f"  -> 实际大小 {res0_size}，压缩比: {res0_size / 64000:.3f}")

# 检查索引1
res1_data, res1_offset, res1_size = read_dat_resource(idx12_data, 0, 1)
print(f"\n嵌套资源1:")
print(f"  偏移: {res1_offset}")
print(f"  大小: {res1_size}")
if res1_size >= 4:
    w = struct.unpack_from('<H', res1_data, 0)[0]
    h = struct.unpack_from('<H', res1_data, 2)[0]
    print(f"  解析为tile: {w}x{h}")

# 检查索引2
res2_data, res2_offset, res2_size = read_dat_resource(idx12_data, 0, 2)
print(f"\n嵌套资源2:")
print(f"  偏移: {res2_offset}")
print(f"  大小: {res2_size}")
if res2_size >= 4:
    w = struct.unpack_from('<H', res2_data, 0)[0]
    h = struct.unpack_from('<H', res2_data, 2)[0]
    print(f"  解析为tile: {w}x{h}")
