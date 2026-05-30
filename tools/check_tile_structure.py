#!/usr/bin/env python3
"""
检查嵌套DAT的tile数据结构，寻找可能的调色板偏移
根据sub_2EB9F代码，value参数可能来自tile数据本身
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

# 分析嵌套DAT 63的tile 1-5
nested63_data, _, _ = read_dat_resource(data, 0, 63)

print("分析嵌套DAT 63的tile数据结构:")
for tile_idx in range(1, 6):
    tile_data, _, tile_size = read_dat_resource(nested63_data, 0, tile_idx)
    if not tile_data:
        continue
    
    print(f"\ntile {tile_idx}:")
    print(f"  总大小: {tile_size}")
    
    # 显示前20字节
    print(f"  前20字节:")
    for i in range(0, min(20, len(tile_data)), 4):
        chunk = tile_data[i:i+4]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        print(f"    offset+{i}: {hex_str}")
    
    # 解析可能的字段
    w = struct.unpack_from('<H', tile_data, 0)[0]
    h = struct.unpack_from('<H', tile_data, 2)[0]
    print(f"  宽度: {w}, 高度: {h}")
    
    # 检查offset+4处是否有额外数据
    if len(tile_data) > 6:
        extra = struct.unpack_from('<H', tile_data, 4)[0]
        print(f"  offset+4处的WORD值: {extra} (0x{extra:04X})")
    
    # 检查可能的调色板偏移（在w,h之后，RLE数据之前）
    if len(tile_data) > 8:
        possible_palette_offset = struct.unpack_from('<H', tile_data, 4)[0]
        print(f"  可能的调色板偏移: {possible_palette_offset}")
