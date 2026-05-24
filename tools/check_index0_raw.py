#!/usr/bin/env python3
"""
直接检查索引0中tile偏移位置的数据
"""

import struct
import os

fdother_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'FDOTHER.DAT')

with open(fdother_path, 'rb') as f:
    f.seek(6)
    resource_count = struct.unpack('<I', f.read(4))[0]
    f.seek(10)
    offsets = []
    for i in range(resource_count):
        offset = struct.unpack('<I', f.read(4))[0]
        offsets.append(offset)
    
    start0 = offsets[0]
    end0 = offsets[1]
    size0 = end0 - start0
    
    f.seek(start0)
    data0 = f.read(size0)
    
    print(f"索引0大小: {size0}字节")
    print(f"\n检查前几个tile偏移位置的数据:")
    
    # 读取前5个tile的偏移
    for i in range(5):
        offset_addr = 6 + i * 4
        tile_offset = struct.unpack('<I', data0[offset_addr:offset_addr+4])[0]
        
        print(f"\nTile {i} (偏移0x{tile_offset:X}):")
        
        # 从索引0的起始位置+tile_offset读取数据
        f.seek(start0 + tile_offset)
        raw_data = f.read(32)
        
        print(f"  前32字节: {raw_data.hex()}")
        
        # 尝试不同解析方式
        # 方式1: WORD宽度 + WORD高度 + 像素
        w1 = struct.unpack('<H', raw_data[0:2])[0]
        h1 = struct.unpack('<H', raw_data[2:4])[0]
        print(f"  解析1 (WORD w,h): {w1}x{h1}")
        
        # 方式2: 直接是像素数据（24x24=576字节）
        if len(raw_data) >= 4:
            # 检查是否是RLE压缩
            first_byte = raw_data[0]
            print(f"  首字节: 0x{first_byte:02X}")
            if first_byte >= 192 or (first_byte >= 128 and first_byte < 192) or first_byte < 64:
                print(f"  可能是RLE压缩数据")
            
        # 方式3: 查看是否是其他结构
        # 打印前16字节的ASCII表示（如果可打印）
        ascii_repr = ''.join(chr(b) if 32 <= b < 127 else '.' for b in raw_data[:16])
        print(f"  ASCII: {ascii_repr}")
