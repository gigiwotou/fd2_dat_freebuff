#!/usr/bin/env python3
"""
验证索引5的tile数据是否真的是RLE压缩
查看tile 1-17的实际像素数据
"""

import struct
import os

def analyze_tile_data():
    fdother_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'FDOTHER.DAT')
    
    if not os.path.exists(fdother_path):
        print(f"错误: 找不到FDOTHER.DAT文件")
        return
    
    print(f"分析文件: {fdother_path}")
    
    with open(fdother_path, 'rb') as f:
        # 读取文件头
        f.seek(6)
        resource_count = struct.unpack('<I', f.read(4))[0]
        print(f"资源数量: {resource_count}")
        
        # 读取偏移表
        f.seek(10)
        offsets = []
        for i in range(resource_count):
            offset = struct.unpack('<I', f.read(4))[0]
            offsets.append(offset)
        
        # 读取索引5
        start = offsets[5]
        end = offsets[6] if 6 < resource_count else os.path.getsize(fdother_path)
        size = end - start
        
        f.seek(start)
        index5_data = f.read(size)
        
        print(f"索引5: start=0x{start:X}, size={size}")
        print(f"魔术字节: {index5_data[0:4]}")
        tile_count = struct.unpack('<H', index5_data[4:6])[0]
        print(f"Tile数量: {tile_count}")
        
        # 分析tile 1-17
        print(f"\n分析Tile 1-17的实际数据:")
        for i in range(1, 18):
            offset_addr = 6 + i * 4
            tile_offset = struct.unpack('<I', index5_data[offset_addr:offset_addr+4])[0]
            
            # 读取tile数据
            tile_addr = tile_offset
            w = struct.unpack('<H', index5_data[tile_addr:tile_addr+2])[0]
            h = struct.unpack('<H', index5_data[tile_addr+2:tile_addr+4])[0]
            
            # 获取tile数据大小
            if i + 1 < tile_count:
                next_tile_offset = struct.unpack('<I', index5_data[6 + (i+1)*4:6 + (i+1)*4+4])[0]
                data_size = next_tile_offset - tile_offset
            else:
                data_size = size - tile_offset
            
            pixel_data_size = data_size - 4  # 减去宽高
            expected_size = w * h
            
            print(f"\nTile {i}: offset=0x{tile_offset:X}, {w}x{h}")
            print(f"  像素数据大小: {pixel_data_size}B, 预期: {expected_size}B")
            print(f"  压缩: {'是' if pixel_data_size < expected_size else '否'}")
            
            # 打印前20字节像素数据
            pixel_start = tile_addr + 4
            print(f"  前20字节: {index5_data[pixel_start:pixel_start+20].hex()}")
            
            # 检查是否是RLE格式（RLE控制字节特征）
            # RLE格式中，控制字节的高位决定操作类型
            # 如果第一个字节的高位是0，可能是FILL模式
            # 如果第一个字节的高位是1，可能是COPY或SKIP模式
            first_byte = index5_data[pixel_start]
            print(f"  第一个字节: 0x{first_byte:02X} (二进制: {first_byte:08b})")
            
            # RLE格式的特征：如果数据被压缩，像素数据大小会远小于w*h
            if pixel_data_size < expected_size * 0.8:
                print(f"  [结论] 明显是RLE压缩 (压缩比: {expected_size/pixel_data_size:.1f}:1)")
            else:
                print(f"  [结论] 可能是未压缩或轻度压缩")

if __name__ == '__main__':
    analyze_tile_data()
