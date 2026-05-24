#!/usr/bin/env python3
"""
扫描FDOTHER所有索引，找到包含LMI1 tile集的索引
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
    
    print(f"FDOTHER资源总数: {resource_count}")
    print(f"\n扫描所有索引，查找包含'LMI1'魔术字节的tile集:")
    print(f"{'='*60}")
    
    for i in range(resource_count):
        start = offsets[i]
        end = offsets[i + 1] if i + 1 < resource_count else os.path.getsize(fdother_path)
        size = end - start
        
        if size < 6:
            continue
        
        f.seek(start)
        magic = f.read(4)
        
        if magic == b'LMI1':
            # 读取tile数量
            f.seek(start + 4)
            tile_count = struct.unpack('<H', f.read(2))[0]
            print(f"\n索引 {i:3d}: LMI1 tile集")
            print(f"  偏移: 0x{start:X} (大小: {size} 字节)")
            print(f"  Tile数量: {tile_count}")
            
            # 读取前10个tile的偏移和尺寸
            for j in range(min(10, tile_count)):
                offset_addr = start + 6 + j * 4
                f.seek(offset_addr)
                tile_offset = struct.unpack('<I', f.read(4))[0]
                
                f.seek(start + tile_offset)
                wh = f.read(4)
                w, h = struct.unpack('<HH', wh)
                print(f"    Tile {j}: offset=0x{tile_offset:X}, {w}x{h}")
            
            if tile_count > 10:
                print(f"    ... 还有 {tile_count - 10} 个tile")
