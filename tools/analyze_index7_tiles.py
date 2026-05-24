#!/usr/bin/env python3
"""
分析FDOTHER索引7 - 对话框tile集
根据文档，索引7才是正确的对话框tile数据源
"""

import struct
import os
from PIL import Image

fdother_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'FDOTHER.DAT')
output_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'index7_tiles')
os.makedirs(output_dir, exist_ok=True)

with open(fdother_path, 'rb') as f:
    f.seek(6)
    resource_count = struct.unpack('<I', f.read(4))[0]
    f.seek(10)
    offsets = []
    for i in range(resource_count):
        offset = struct.unpack('<I', f.read(4))[0]
        offsets.append(offset)
    
    # 分析索引7
    start7 = offsets[7]
    end7 = offsets[8] if 8 < resource_count else os.path.getsize(fdother_path)
    size7 = end7 - start7
    
    f.seek(start7)
    data7 = f.read(size7)
    
    print(f"索引7数据分析:")
    print(f"  起始偏移: 0x{start7:X}")
    print(f"  数据大小: {size7} 字节")
    print()
    
    # 根据文档，头部格式：
    # [0-1]: WORD - 总宽度
    # [2-3]: WORD - 总高度  
    # [4-5]: WORD - tile数量
    # [6+]: tile偏移表 (DWORD数组)
    
    total_width = struct.unpack('<H', data7[0:2])[0]
    total_height = struct.unpack('<H', data7[2:4])[0]
    tile_count = struct.unpack('<H', data7[4:6])[0]
    
    print(f"  总宽度: {total_width}")
    print(f"  总高度: {total_height}")
    print(f"  Tile数量: {tile_count}")
    print()
    
    # 读取tile偏移表
    tile_offsets = []
    for i in range(tile_count):
        offset_addr = 6 + i * 4
        tile_offset = struct.unpack('<I', data7[offset_addr:offset_addr+4])[0]
        tile_offsets.append(tile_offset)
    
    print(f"前20个tile的偏移:")
    for i in range(min(20, tile_count)):
        print(f"  Tile {i:3d}: 偏移=0x{tile_offsets[i]:05X} ({tile_offsets[i]})")
    print()
    
    # 分析tile 1-17（用于窗口边框的tile）
    print(f"{'='*60}")
    print(f"分析tile 1-17 (窗口边框tile):")
    print(f"{'='*60}")
    
    for i in range(1, 18):
        if i >= tile_count:
            break
        
        tile_offset = tile_offsets[i]
        next_offset = tile_offsets[i + 1] if i + 1 < tile_count else size7
        
        # Tile格式（无压缩）：
        # [0-1]: WORD - 宽度
        # [2-3]: WORD - 高度
        # [4+]: 像素数据（宽度*高度字节）
        
        w = struct.unpack('<H', data7[tile_offset:tile_offset+2])[0]
        h = struct.unpack('<H', data7[tile_offset+2:tile_offset+4])[0]
        
        # 像素数据大小
        pixel_data_size = w * h
        actual_data_size = next_offset - tile_offset
        
        print(f"\nTile {i}:")
        print(f"  偏移: 0x{tile_offset:05X}")
        print(f"  宽度: {w}")
        print(f"  高度: {h}")
        print(f"  预期像素数据大小: {pixel_data_size}")
        print(f"  实际数据大小: {actual_data_size}")
        
        # 提取像素数据
        pixel_data_start = tile_offset + 4
        pixel_data = data7[pixel_data_start:pixel_data_start + pixel_data_size]
        
        # 统计非零像素
        non_zero = sum(1 for p in pixel_data if p != 0)
        print(f"  非零像素: {non_zero}/{pixel_data_size}")
        
        # 打印前16个字节的十六进制
        print(f"  前16字节: {pixel_data[:16].hex()}")
        
        # 创建图像保存
        if len(pixel_data) >= pixel_data_size:
            img = Image.new('P', (w, h))
            img.putdata(pixel_data)
            img_path = os.path.join(output_dir, f'tile_{i:02d}_{w}x{h}.png')
            img.save(img_path)
            print(f"  已保存: {img_path}")
