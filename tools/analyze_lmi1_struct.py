"""比较LMI1 3, 5, 6的tile结构差异"""
import struct

with open("bin/FDOTHER.DAT", "rb") as f:
    data = f.read()

# 解析偏移表
offsets = []
table_offset = 6
while table_offset + 4 <= len(data):
    res_offset = struct.unpack_from("<I", data, table_offset)[0]
    if res_offset == 0 or res_offset > len(data):
        break
    offsets.append(res_offset)
    table_offset += 4

for lmi1_idx in [3, 5, 6, 9, 13, 14, 29]:
    if lmi1_idx >= len(offsets) - 1:
        continue
    lmi1_off = offsets[lmi1_idx]
    lmi1_size = offsets[lmi1_idx + 1] - lmi1_off
    lmi1_data = data[lmi1_off:lmi1_off+lmi1_size]
    
    print(f"\n=== LMI1 {lmi1_idx} ({lmi1_size} bytes) ===")
    print(f"magic: {lmi1_data[:4]}")
    tile_count = struct.unpack_from("<H", lmi1_data, 4)[0]
    print(f"tile_count: {tile_count}")
    
    # 读取tile偏移
    tile_offsets = []
    for i in range(tile_count):
        off = struct.unpack_from("<I", lmi1_data, 6 + i*4)[0]
        tile_offsets.append(off)
    
    for i in range(min(5, tile_count)):
        if i + 1 < tile_count:
            size = tile_offsets[i+1] - tile_offsets[i]
        else:
            size = lmi1_size - tile_offsets[i]
        
        if tile_offsets[i] + 4 <= lmi1_size:
            w0 = struct.unpack_from("<H", lmi1_data, tile_offsets[i])[0]
            h0 = struct.unpack_from("<H", lmi1_data, tile_offsets[i] + 2)[0]
            print(f"  tile[{i}]: offset={tile_offsets[i]} size={size} header=[w={w0},h={h0}]")
        else:
            print(f"  tile[{i}]: offset={tile_offsets[i]} size={size} (越界)")
    
    # 如果tile大小=256固定，尝试不带头解析
    if all((tile_offsets[i+1] - tile_offsets[i]) == 256 for i in range(min(tile_count-1, 10))):
        print(f"  → tile固定256字节, 可能无4字节头")
        # 显示tile[0]前16字节
        t0_off = tile_offsets[0]
        print(f"  tile[0]前16字节: {lmi1_data[t0_off:t0_off+16].hex()}")
