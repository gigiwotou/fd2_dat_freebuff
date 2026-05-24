#!/usr/bin/env python3
"""
检查FDOTHER.DAT的索引0和索引5，找出哪个是窗口tile集
"""

import struct
import os

def analyze_index(fdother_path, index_num):
    print(f"\n{'='*60}")
    print(f"分析索引{index_num}")
    print(f"{'='*60}")
    
    with open(fdother_path, 'rb') as f:
        f.seek(6)
        resource_count = struct.unpack('<I', f.read(4))[0]
        print(f"资源总数: {resource_count}")
        
        if index_num >= resource_count:
            print(f"索引{index_num}不存在")
            return
        
        f.seek(10)
        offsets = []
        for i in range(resource_count):
            offset = struct.unpack('<I', f.read(4))[0]
            offsets.append(offset)
        
        start = offsets[index_num]
        end = offsets[index_num + 1] if index_num + 1 < resource_count else os.path.getsize(fdother_path)
        size = end - start
        
        f.seek(start)
        data = f.read(size)
        
        print(f"偏移: 0x{start:X} - 0x{end:X}")
        print(f"大小: {size} 字节")
        print(f"前20字节: {data[:20].hex()}")
        
        # 检查魔术字节
        if data[:4] == b'LMI1':
            print(f"魔术字节: LMI1 (tile集)")
            tile_count = struct.unpack('<H', data[4:6])[0]
            print(f"Tile数量: {tile_count}")
            
            # 读取前几个tile的信息
            print(f"\n前5个Tile信息:")
            for i in range(min(5, tile_count)):
                offset_addr = 6 + i * 4
                if offset_addr + 4 > len(data):
                    break
                    
                tile_offset = struct.unpack('<I', data[offset_addr:offset_addr+4])[0]
                print(f"  Tile {i}: 偏移=0x{tile_offset:X}")
                
                tile_addr = tile_offset
                if tile_addr + 4 <= len(data):
                    w = struct.unpack('<H', data[tile_addr:tile_addr+2])[0]
                    h = struct.unpack('<H', data[tile_addr+2:tile_addr+4])[0]
                    print(f"         尺寸={w}x{h}")
                    
                    # 检查是否是RLE压缩
                    if tile_addr + 4 < len(data):
                        first_byte = data[tile_addr + 4]
                        print(f"         首字节=0x{first_byte:02X}")
                        
        elif data[:4] == b'RIFF' or data[:4] == b'FORM':
            print(f"可能是音频/图片资源")
        else:
            print(f"未知格式，尝试分析...")
            # 检查前4字节是否像tile数量
            possible_count = struct.unpack('<H', data[0:2])[0]
            if possible_count < 500:
                print(f"  可能的tile数量: {possible_count}")

fdother_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'FDOTHER.DAT')

if not os.path.exists(fdother_path):
    print(f"错误: 找不到FDOTHER.DAT")
else:
    print(f"分析文件: {fdother_path}")
    
    # 检查索引0
    analyze_index(fdother_path, 0)
    
    # 检查索引5
    analyze_index(fdother_path, 5)
    
    # 也检查一下其他可能的索引（1-10）
    for i in range(1, 11):
        try:
            with open(fdother_path, 'rb') as f:
                f.seek(6)
                resource_count = struct.unpack('<I', f.read(4))[0]
                f.seek(10)
                offsets = []
                for j in range(resource_count):
                    offset = struct.unpack('<I', f.read(4))[0]
                    offsets.append(offset)
                
                if i < resource_count:
                    start = offsets[i]
                    f.seek(start)
                    header = f.read(6)
                    if header[:4] == b'LMI1':
                        tile_count = struct.unpack('<H', header[4:6])[0]
                        print(f"\n索引{i}: LMI1格式, tile数量={tile_count}")
        except:
            pass
