#!/usr/bin/env python3
"""
检查嵌套DAT索引0的数据结构
看它是否是调色板或者包含调色板信息
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

# 分析嵌套DAT索引7、12、63的索引0
nested_indices = [7, 12, 63]

for nested_idx in nested_indices:
    print(f"\n嵌套DAT {nested_idx} 索引0分析:")
    nested_data, _, _ = read_dat_resource(data, 0, nested_idx)
    if not nested_data:
        continue
    
    res0_data, res0_offset, res0_size = read_dat_resource(nested_data, 0, 0)
    if not res0_data:
        print(f"  索引0数据无效")
        continue
    
    print(f"  大小: {res0_size}")
    print(f"  前32字节: {' '.join(f'{b:02X}' for b in res0_data[:32])}")
    
    # 检查是否是调色板
    if res0_size == 768:
        print(f"  -> 是调色板 (768字节)")
    else:
        # 尝试解析为tile
        w = struct.unpack_from('<H', res0_data, 0)[0]
        h = struct.unpack_from('<H', res0_data, 2)[0]
        print(f"  -> 解析为tile: {w}x{h}")
        
        # 检查offset+4处的值
        if len(res0_data) > 6:
            field4 = struct.unpack_from('<H', res0_data, 4)[0]
            print(f"  -> offset+4处的WORD: {field4} (0x{field4:04X})")
