#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

"""根据MCP公式精确解析索引7 - tile_ptr = *(DWORD*)(base + 4*tile_index + 6) + base"""

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
    print(f"\n完整数据十六进制（前100字节）:")
    for i in range(0, min(100, len(idx7_data)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in idx7_data[i:i+16])
        print(f"  {i:4d} (0x{i:04X}): {hex_str}")
    
    # 根据MCP公式: tile_ptr = *(DWORD*)(base + 4*tile_index + 6) + base
    # 这意味着偏移表从+6开始，每个DWORD是相对偏移
    # 但偏移值是相对于数据开始的，所以实际地址是 base + offset
    
    print(f"\n根据MCP公式解析偏移表（从偏移6开始）:")
    
    # 读取前10个DWORD作为偏移表
    tile_index = 0
    while tile_index < 30:
        offset_addr = 6 + tile_index * 4
        if offset_addr + 4 > size:
            print(f"  ... 偏移表结束（共{tile_index}个tile）")
            break
        
        # 读取DWORD
        tile_offset = struct.unpack_from('<I', idx7_data, offset_addr)[0]
        
        # 如果偏移值超出范围，说明偏移表到此结束
        if tile_offset >= size or tile_offset < 6:
            print(f"  ... Tile {tile_index} 偏移={tile_offset} (无效，偏移表结束)")
            break
        
        print(f"  Tile {tile_index:2d}: 偏移表位置=0x{offset_addr:04X}, 相对偏移={tile_offset:5d} (0x{tile_offset:04X})")
        
        # 检查tile数据（在偏移位置）
        if tile_offset + 4 <= size:
            # 尝试读取宽高
            w = struct.unpack_from('<H', idx7_data, tile_offset)[0]
            h = struct.unpack_from('<H', idx7_data, tile_offset + 2)[0]
            
            # 检查宽高是否合理（1-320范围）
            if 0 < w <= 320 and 0 < h <= 200:
                pixel_size = w * h
                available = size - tile_offset - 4
                print(f"           宽高: {w}x{h}, 需要{pixel_size}字节, 可用{available}字节")
            else:
                # 打印前8字节作为调试
                bytes_at_offset = idx7_data[tile_offset:tile_offset+8]
                print(f"           宽高无效 ({w}x{h}), 数据: {' '.join(f'{b:02x}' for b in bytes_at_offset)}")
        
        tile_index += 1

if __name__ == "__main__":
    main()
