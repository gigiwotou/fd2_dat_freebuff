#!/usr/bin/env python3
"""
分析嵌套DAT的结构，检查是否包含调色板
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
    if 6 + (i + 1) * 4 > len(data):
        break
    offset = struct.unpack_from('<I', data, 6 + i * 4)[0]
    offsets.append(offset)

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
    if offset0 + size > len(file_data):
        size = len(file_data) - offset0
    resource_data = file_data[offset0:offset0 + size]
    return resource_data, offset0, size

# 分析嵌套DAT结构
nested_indices = [7, 12, 63]

for idx in nested_indices:
    print(f"\n{'='*60}")
    print(f"索引 {idx} 分析:")
    res_data, res_offset, res_size = read_dat_resource(data, 0, idx)
    if res_data is None or len(res_data) < 10:
        print(f"  资源数据无效")
        continue
    
    # 检查头部
    magic = res_data[:6]
    print(f"  Magic: {magic}")
    
    nested_count = struct.unpack_from('<I', res_data, 6)[0]
    print(f"  嵌套资源数量: {nested_count}")
    
    # 分析嵌套资源
    print(f"\n  嵌套资源列表:")
    print(f"  {'索引':<5} {'偏移':<10} {'大小':<10} {'类型'}")
    print(f"  {'-'*50}")
    
    for j in range(min(30, nested_count)):
        nested_res, nested_offset, nested_size = read_dat_resource(res_data, 0, j)
        if nested_res is None or len(nested_res) < 4:
            continue
        
        # 检查是否是调色板
        is_palette = (nested_size == 768)
        
        # 检查是否是tile
        is_tile = False
        try:
            w = struct.unpack_from('<H', nested_res, 0)[0]
            h = struct.unpack_from('<H', nested_res, 2)[0]
            if 0 < w <= 320 and 0 < h <= 200:
                is_tile = True
        except:
            pass
        
        type_str = ""
        if is_palette:
            type_str = "调色板"
        elif is_tile:
            type_str = f"Tile {w}x{h}"
        elif nested_size < 50:
            type_str = "小资源"
        else:
            type_str = "其他"
        
        print(f"  {j:<5} {nested_offset:<10} {nested_size:<10} {type_str}")
