#!/usr/bin/env python3
"""
分析嵌套DAT 12和63的tile数据是否相同
如果数据相同但调色板不同，说明调色板是在加载时动态应用的
"""
import struct

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"

with open(dat_path, 'rb') as f:
    data = f.read()

def read_dat_resource(file_data, base_offset, index):
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

# 比较嵌套DAT 12和63的tile数据
nested12_data, _, _ = read_dat_resource(data, 0, 12)
nested63_data, _, _ = read_dat_resource(data, 0, 63)

print("比较嵌套DAT 12和63的tile数据:")
for tile_idx in range(1, 6):
    tile12_data, _, tile12_size = read_dat_resource(nested12_data, 0, tile_idx)
    tile63_data, _, tile63_size = read_dat_resource(nested63_data, 0, tile_idx)
    
    if tile12_data and tile63_data:
        # 比较数据是否相同
        same_data = (tile12_data == tile63_data)
        print(f"  tile {tile_idx}: 大小12={tile12_size}, 大小63={tile63_size}, 数据相同={same_data}")
        
        if tile_idx <= 3:
            # 显示前16字节
            hex12 = ' '.join(f'{b:02X}' for b in tile12_data[:16])
            hex63 = ' '.join(f'{b:02X}' for b in tile63_data[:16])
            print(f"    12: {hex12}")
            print(f"    63: {hex63}")

# 检查嵌套DAT 7
nested7_data, _, _ = read_dat_resource(data, 0, 7)
print(f"\n分析嵌套DAT 7:")
for tile_idx in range(1, 4):
    tile7_data, _, tile7_size = read_dat_resource(nested7_data, 0, tile_idx)
    if tile7_data:
        hex7 = ' '.join(f'{b:02X}' for b in tile7_data[:16])
        print(f"  tile {tile_idx}: 大小={tile7_size}, 前16字节: {hex7}")

# 分析FDOTHER.DAT索引表，找出哪些索引可能是调色板
print(f"\n分析FDOTHER.DAT索引表，寻找调色板:")
NUM_INDICES = 103  # 只分析前103个索引
offsets = []
for i in range(NUM_INDICES):
    offset = struct.unpack_from('<I', data, 6 + i * 4)[0]
    offsets.append(offset)

for i in range(NUM_INDICES - 1):
    size = offsets[i + 1] - offsets[i]
    if size == 768:
        print(f"  索引 {i}: 大小=768 (调色板)")
