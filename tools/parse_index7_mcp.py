#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

"""根据MCP汇编公式重新解析索引7"""

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
    print(f"\n完整十六进制数据:")
    for i in range(0, len(idx7_data), 16):
        hex_str = ' '.join(f'{b:02x}' for b in idx7_data[i:i+16])
        print(f"  {i:4d} (0x{i:04X}): {hex_str}")
    
    print(f"\n{'='*80}")
    print(f"根据MCP公式解析: tile_ptr = *(DWORD*)(base + 4*tile_index + 6) + base")
    print(f"偏移表从+6开始:")
    
    # 从偏移6开始读取DWORD
    offset_table_start = 6
    tile_index = 0
    while offset_table_start + tile_index * 4 + 4 <= size:
        offset_addr = offset_table_start + tile_index * 4
        tile_offset = struct.unpack_from('<I', idx7_data, offset_addr)[0]
        
        # 检查偏移是否有效
        if tile_offset >= size:
            # 可能偏移表到此结束
            print(f"\n  [结束] Tile {tile_index} 偏移={tile_offset} (超出范围，偏移表结束)")
            break
        
        print(f"  Tile {tile_index:2d}: 偏移={tile_offset:5d} (0x{tile_offset:04X})")
        
        # 尝试解析tile数据 (宽度WORD + 高度WORD + 像素)
        if tile_offset + 4 <= size:
            w = struct.unpack_from('<H', idx7_data, tile_offset)[0]
            h = struct.unpack_from('<H', idx7_data, tile_offset + 2)[0]
            if 0 < w <= 320 and 0 < h <= 200:
                pixel_size = w * h
                available = size - tile_offset - 4
                print(f"           宽高: {w}x{h}, 需要{pixel_size}字节, 可用{available}字节")
            else:
                # 打印前几个像素值
                pixels = idx7_data[tile_offset:tile_offset+8]
                print(f"           宽高无效 ({w}x{h}), 前8字节: {' '.join(f'{b:02x}' for b in pixels)}")
        
        tile_index += 1
        if tile_index > 30:
            print(f"  ... (超过30个tile，停止)")
            break

if __name__ == "__main__":
    main()
