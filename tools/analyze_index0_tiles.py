#!/usr/bin/env python3
"""
检查索引0中的tile数据
"""

import struct
import os
from PIL import Image

fdother_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'FDOTHER.DAT')
output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')

def load_palette_from_index75():
    """加载调色板"""
    with open(fdother_path, 'rb') as f:
        f.seek(6)
        resource_count = struct.unpack('<I', f.read(4))[0]
        f.seek(10)
        offsets = []
        for i in range(resource_count):
            offset = struct.unpack('<I', f.read(4))[0]
            offsets.append(offset)
        
        start = offsets[75]
        end = offsets[76] if 76 < resource_count else os.path.getsize(fdother_path)
        size = end - start
        
        f.seek(start)
        pal_data = f.read(size)
        
        palette = []
        for i in range(256):
            r = (pal_data[i * 3 + 0] << 2) | (pal_data[i * 3 + 0] >> 4)
            g = (pal_data[i * 3 + 1] << 2) | (pal_data[i * 3 + 1] >> 4)
            b = (pal_data[i * 3 + 2] << 2) | (pal_data[i * 3 + 2] >> 4)
            palette.append((r, g, b))
        
        return palette

with open(fdother_path, 'rb') as f:
    f.seek(6)
    resource_count = struct.unpack('<I', f.read(4))[0]
    f.seek(10)
    offsets = []
    for i in range(resource_count):
        offset = struct.unpack('<I', f.read(4))[0]
        offsets.append(offset)
    
    # 读取索引0
    start0 = offsets[0]
    end0 = offsets[1]
    size0 = end0 - start0
    
    f.seek(start0)
    data0 = f.read(size0)
    
    # 解析头部
    width = struct.unpack('<H', data0[0:2])[0]
    height = struct.unpack('<H', data0[2:4])[0]
    tile_count = struct.unpack('<H', data0[4:6])[0]
    
    print(f"索引0解析:")
    print(f"  宽度: {width}")
    print(f"  高度: {height}")
    print(f"  Tile数量: {tile_count}")
    
    # 解析偏移表（从偏移6开始，每个DWORD一个偏移）
    tile_offsets = []
    for i in range(tile_count):
        offset_addr = 6 + i * 4
        if offset_addr + 4 > size0:
            break
        tile_offset = struct.unpack('<I', data0[offset_addr:offset_addr+4])[0]
        tile_offsets.append(tile_offset)
        print(f"  Tile {i}: 偏移=0x{tile_offset:X}")
    
    # 读取每个tile的数据并可视化
    palette = load_palette_from_index75()
    
    print(f"\n{'='*60}")
    print(f"读取并保存tile图像:")
    print(f"{'='*60}")
    
    for i, tile_offset in enumerate(tile_offsets[:10]):
        # 从索引0的起始位置+偏移读取tile数据
        f.seek(start0 + tile_offset)
        
        # 尝试读取宽高+像素数据
        # tile数据格式: 宽(WORD) + 高(WORD) + 像素
        wh_data = f.read(4)
        if len(wh_data) < 4:
            continue
            
        tw = struct.unpack('<H', wh_data[0:2])[0]
        th = struct.unpack('<H', wh_data[2:4])[0]
        
        print(f"\nTile {i}: 尺寸={tw}x{th}")
        
        # 读取像素数据
        pixel_data = f.read(tw * th)
        if len(pixel_data) < tw * th:
            print(f"  数据不足")
            continue
        
        # 创建图像
        img = Image.new('RGB', (tw, th))
        pixels = img.load()
        
        for y in range(th):
            for x in range(tw):
                idx = pixel_data[y * tw + x]
                pixels[x, y] = palette[idx]
        
        # 保存
        tile_path = os.path.join(output_dir, f'index0_tile_{i:03d}_{tw}x{th}.png')
        img.save(tile_path)
        print(f"  已保存到: {tile_path}")
        
        # 统计非零像素
        non_zero = sum(1 for p in pixel_data if p != 0)
        print(f"  非零像素: {non_zero}/{tw*th}")
