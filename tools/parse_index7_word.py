#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

"""重新解析索引7 - 可能是WORD偏移表而不是DWORD"""

import struct
from pathlib import Path

def main():
    fdother_path = Path("game/FDOTHER.DAT")
    data = fdother_path.read_bytes()
    
    resource_count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(resource_count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    idx = 7
    start = offsets[idx]
    end = offsets[idx + 1] if idx + 1 < resource_count else len(data)
    size = end - start
    idx7_data = data[start:end]
    
    print(f"索引7: 大小={size}字节")
    
    # 假设前2个字节是tile数量
    tile_count = struct.unpack_from('<H', idx7_data, 0)[0]
    print(f"假设前2字节是tile数量: {tile_count}")
    
    # 假设偏移表从+2开始，每个是WORD (2字节)
    print(f"\n假设偏移表是WORD格式（从偏移2开始）:")
    for i in range(min(tile_count, 30)):
        offset_addr = 2 + i * 2
        if offset_addr + 2 > size:
            break
        
        tile_offset = struct.unpack_from('<H', idx7_data, offset_addr)[0]
        print(f"  Tile {i:2d}: 偏移表位置=0x{offset_addr:04X}, 偏移={tile_offset:5d} (0x{tile_offset:04X})")
        
        # 检查tile数据
        if tile_offset < size and tile_offset + 4 <= size:
            w = struct.unpack_from('<H', idx7_data, tile_offset)[0]
            h = struct.unpack_from('<H', idx7_data, tile_offset + 2)[0]
            
            if 0 < w <= 320 and 0 < h <= 200:
                pixel_size = w * h
                available = size - tile_offset - 4
                print(f"           宽高: {w}x{h}, 需要{pixel_size}字节, 可用{available}字节")
            else:
                # 打印前几个字节
                bytes_at_offset = idx7_data[tile_offset:tile_offset+8]
                print(f"           宽高无效 ({w}x{h}), 数据: {' '.join(f'{b:02x}' for b in bytes_at_offset)}")
    
    print(f"\n{'='*60}")
    print(f"另一种解析：假设是LMI1格式，但tile_count在偏移4-5")
    
    if idx7_data[:4] == b'LMI1':
        print(f"  魔术字节: LMI1")
        tile_count = struct.unpack_from('<H', idx7_data, 4)[0]
        print(f"  Tile数量: {tile_count}")
    else:
        print(f"  不是LMI1格式")

if __name__ == "__main__":
    main()
