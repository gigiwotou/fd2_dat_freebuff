#!/usr/bin/env python3
"""
检查嵌套DAT的tile数据结构
根据sub_2EB9F代码，tile数据可能包含额外的调色板偏移字段
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

# 分析嵌套DAT 63的tile 1-10
nested63_data, _, _ = read_dat_resource(data, 0, 63)

print("分析嵌套DAT 63的tile数据结构:")
print(f"{'索引':<5} {'大小':<6} {'前8字节'}")
print("-" * 40)

for tile_idx in range(1, 11):
    tile_data, _, tile_size = read_dat_resource(nested63_data, 0, tile_idx)
    if not tile_data or len(tile_data) < 8:
        continue
    
    # 显示前8字节
    hex_bytes = ' '.join(f'{b:02X}' for b in tile_data[:8])
    
    w = struct.unpack_from('<H', tile_data, 0)[0]
    h = struct.unpack_from('<H', tile_data, 2)[0]
    field4 = struct.unpack_from('<H', tile_data, 4)[0]
    field6 = struct.unpack_from('<H', tile_data, 6)[0]
    
    print(f"{tile_idx:<5} {tile_size:<6} {hex_bytes} (w={w}, h={h}, f4={field4}, f6={field6})")

# 再分析嵌套DAT 7和12
print(f"\n{'='*60}")
print("分析嵌套DAT 7的tile数据结构:")
print(f"{'索引':<5} {'大小':<6} {'前8字节'}")
print("-" * 40)

nested7_data, _, _ = read_dat_resource(data, 0, 7)
for tile_idx in range(1, 7):
    tile_data, _, tile_size = read_dat_resource(nested7_data, 0, tile_idx)
    if not tile_data or len(tile_data) < 8:
        continue
    
    hex_bytes = ' '.join(f'{b:02X}' for b in tile_data[:8])
    w = struct.unpack_from('<H', tile_data, 0)[0]
    h = struct.unpack_from('<H', tile_data, 2)[0]
    field4 = struct.unpack_from('<H', tile_data, 4)[0]
    field6 = struct.unpack_from('<H', tile_data, 6)[0]
    
    print(f"{tile_idx:<5} {tile_size:<6} {hex_bytes} (w={w}, h={h}, f4={field4}, f6={field6})")
