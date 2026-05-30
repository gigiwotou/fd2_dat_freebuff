#!/usr/bin/env python3
"""分析LMI1 Tile的实际数据格式"""

import struct
from pathlib import Path

FDOTHER_PATH = Path("game/FDOTHER.DAT")

def analyze_lmi1_tile_format():
    with open(FDOTHER_PATH, 'rb') as f:
        data = f.read()
    
    # 读取索引表
    offsets = []
    table_offset = 6
    while table_offset + 4 <= len(data):
        res_offset = struct.unpack_from('<I', data, table_offset)[0]
        if res_offset == 0 or res_offset > len(data):
            break
        offsets.append(res_offset)
        table_offset += 4
    
    # 索引3的数据
    idx3_start = offsets[3]
    idx3_end = offsets[4] if len(offsets) > 4 else len(data)
    idx3_data = data[idx3_start:idx3_end]
    
    magic = idx3_data[:4]
    tile_count = struct.unpack_from('<H', idx3_data, 4)[0]
    
    print(f"Tile数量: {tile_count}")
    print(f"\n=== Tile数据分析 ===")
    
    for i in range(min(tile_count, 5)):
        addr = 6 + i * 4
        tile_offset = struct.unpack_from('<I', idx3_data, addr)[0]
        next_addr = 6 + (i + 1) * 4
        next_tile_offset = struct.unpack_from('<I', idx3_data, next_addr)[0] if next_addr + 4 <= len(idx3_data) else len(idx3_data)
        
        tile_size = next_tile_offset - tile_offset
        
        print(f"\n--- Tile[{i}] ---")
        print(f"偏移: {tile_offset}, 大小: {tile_size}")
        
        # 读取前10字节
        tile_data = idx3_data[tile_offset:tile_offset + min(20, tile_size)]
        print(f"前10字节: {' '.join(f'{b:02X}' for b in tile_data[:10])}")
        
        # 尝试不同的格式解释
        print(f"假设1 (2字节宽高): w={struct.unpack_from('<H', tile_data, 0)[0]}, h={struct.unpack_from('<H', tile_data, 2)[0]}")
        
        # 假设tile偏移指向的是调色板窗口+宽高
        if tile_size >= 5:
            pw = tile_data[0]
            w = struct.unpack_from('<H', tile_data, 1)[0]
            h = struct.unpack_from('<H', tile_data, 3)[0]
            print(f"假设2 (pw + 2字节宽高): pw={pw}, w={w}, h={h}")
        
        if tile_size >= 6:
            w = struct.unpack_from('<H', tile_data, 0)[0]
            h = struct.unpack_from('<H', tile_data, 2)[0]
            pw = tile_data[4]
            extra = tile_data[5]
            print(f"假设3 (2字节宽高 + pw + extra): w={w}, h={h}, pw={pw}, extra={extra}")
        
        if tile_size >= 8:
            w = struct.unpack_from('<H', tile_data, 0)[0]
            h = struct.unpack_from('<H', tile_data, 2)[0]
            pw = struct.unpack_from('<H', tile_data, 4)[0]
            extra = struct.unpack_from('<H', tile_data, 6)[0]
            print(f"假设4 (2字节宽高 + 2字节pw + 2字节extra): w={w}, h={h}, pw={pw}, extra={extra}")

if __name__ == '__main__':
    analyze_lmi1_tile_format()
