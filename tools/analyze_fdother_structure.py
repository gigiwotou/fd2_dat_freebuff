#!/usr/bin/env python3
"""
详细分析FDOTHER.DAT文件结构
"""

import struct
import os

fdother_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'FDOTHER.DAT')

with open(fdother_path, 'rb') as f:
    # 读取文件头
    magic = f.read(6)
    print(f"魔术字节: {magic}")
    
    # 根据sub_111BA的逻辑：fseek(_rb_, 4 * a7 + 6, 0) 然后读取8字节
    # 这意味着偏移6开始就是偏移表，每8字节一个资源（2个DWORD）
    
    f.seek(6)
    resource_count_data = f.read(8)
    
    # 尝试解析为资源0的起始和结束
    start0 = struct.unpack('<I', resource_count_data[0:4])[0]
    end0 = struct.unpack('<I', resource_count_data[4:8])[0]
    
    print(f"\n如果偏移6是资源0的起始/结束:")
    print(f"  资源0: 0x{start0:X} - 0x{end0:X}, 大小={end0-start0}")
    
    # 再尝试解析为资源数量+偏移表
    f.seek(6)
    possible_count = struct.unpack('<I', f.read(4))[0]
    print(f"\n如果偏移6-9是资源数量: {possible_count}")
    
    # 检查索引5
    if possible_count > 5:
        f.seek(10 + 5 * 4)
        start5 = struct.unpack('<I', f.read(4))[0]
        f.seek(10 + 6 * 4)
        end5 = struct.unpack('<I', f.read(4))[0]
        print(f"索引5 (从偏移10+5*4): 0x{start5:X} - 0x{end5:X}, 大小={end5-start5}")
        
        f.seek(start5)
        data5 = f.read(20)
        print(f"  前20字节: {data5.hex()}")
        if data5[:4] == b'LMI1':
            tile_count = struct.unpack('<H', data5[4:6])[0]
            print(f"  Tile数量: {tile_count}")
    
    # 现在检查偏移6开始的每8字节
    print(f"\n{'='*60}")
    print(f"检查偏移6开始的资源表（每8字节一个资源）:")
    print(f"{'='*60}")
    
    f.seek(6)
    for i in range(10):
        data = f.read(8)
        if len(data) < 8:
            break
        start = struct.unpack('<I', data[0:4])[0]
        end = struct.unpack('<I', data[4:8])[0]
        size = end - start
        
        f.seek(start)
        header = f.read(6)
        
        print(f"\n资源{i}: 0x{start:06X} - 0x{end:06X}, 大小={size}")
        print(f"  头部: {header.hex()}")
        
        if header[:4] == b'LMI1':
            tile_count = struct.unpack('<H', header[4:6])[0]
            print(f"  LMI1格式, tile数量={tile_count}")
        elif header[:4] == b'FDAT' or header[:4] == b'FD2A':
            print(f"  可能是FDAT格式")
        elif size < 100:
            print(f"  小资源")
