#!/usr/bin/env python3
"""
检查FDOTHER索引0的tile 1-17，看是否包含窗口边框tile
"""

import struct
import os
from PIL import Image

fdother_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'FDOTHER.DAT')
output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')

def decompress_rle(src_data, width, height):
    """RLE解压算法"""
    compressed = src_data[4:]
    comp_size = len(compressed)
    
    dst = [0] * (width * height)
    
    num4 = 0
    num3 = comp_size - 1
    num7 = 0
    num8 = 0
    num9 = 0
    b = 0
    num10 = 0
    num11 = 0
    
    pixel_idx = 0
    expected = width * height
    
    while num4 <= num3 and pixel_idx < expected:
        flag = (num8 != 0)
        
        if not flag:
            num7 = 0
            num8 = 0
            num9 = 0
            
            if num4 < comp_size:
                b = compressed[num4]
                if b >= 192:
                    num7 = b - 192 + 1
                elif b >= 128:
                    num8 = b - 128 + 1
                elif b >= 64:
                    num9 = b - 64
                    num8 = 1
                else:
                    num8 = 1
                    num9 = b
            
            num10 += num7
            if num10 >= width:
                num10 = 0
                num11 += 1
        else:
            num12 = num9
            num13 = 0
            while num13 <= num12:
                if b >= 64 and b < 128:
                    num10 += 1
                
                if num4 < comp_size:
                    index = compressed[num4]
                    if num10 >= 0 and num10 < width and num11 >= 0 and num11 < height:
                        if pixel_idx < expected:
                            dst[pixel_idx] = index
                            pixel_idx += 1
                
                num10 += 1
                if num10 >= width:
                    num10 = 0
                    num11 += 1
                
                num13 += 1
            
            num8 -= 1
        
        num4 += 1
        
        if num11 >= height:
            break
    
    return bytes(dst)

def load_palette():
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
    
    # 检查索引0
    start0 = offsets[0]
    end0 = offsets[1]
    size0 = end0 - start0
    
    f.seek(start0)
    data0 = f.read(size0)
    
    print(f"索引0:")
    print(f"  偏移: 0x{start0:X} - 0x{end0:X}")
    print(f"  大小: {size0}")
    
    # 解析头部
    # 索引0的头部格式: WORD宽度 + WORD高度 + WORD tile数量
    width = struct.unpack('<H', data0[0:2])[0]
    height = struct.unpack('<H', data0[2:4])[0]
    tile_count = struct.unpack('<H', data0[4:6])[0]
    
    print(f"  宽度: {width}")
    print(f"  高度: {height}")
    print(f"  Tile数量: {tile_count}")
    
    palette = load_palette()
    
    print(f"\n{'='*60}")
    print(f"分析tile 1-17:")
    print(f"{'='*60}")
    
    # 读取tile偏移表（从偏移6开始）
    tile_offsets = []
    for i in range(tile_count):
        offset_addr = 6 + i * 4
        if offset_addr + 4 > size0:
            break
        tile_offset = struct.unpack('<I', data0[offset_addr:offset_addr+4])[0]
        tile_offsets.append(tile_offset)
    
    # 检查tile 1-17
    for i in range(1, min(18, len(tile_offsets))):
        tile_offset = tile_offsets[i]
        
        # 从索引0的起始位置+tile_offset读取数据
        f.seek(start0 + tile_offset)
        
        # 尝试读取宽高+像素数据
        wh_data = f.read(4)
        if len(wh_data) < 4:
            print(f"Tile {i}: 数据不足")
            continue
            
        w = struct.unpack('<H', wh_data[0:2])[0]
        h = struct.unpack('<H', wh_data[2:4])[0]
        
        # 读取压缩数据
        # 预估大小
        compressed_size = 1024
        if i + 1 < len(tile_offsets):
            next_offset = tile_offsets[i + 1]
            compressed_size = next_offset - tile_offset
        
        f.seek(start0 + tile_offset)
        compressed_data = f.read(compressed_size)
        
        # 解压
        try:
            decompressed = decompress_rle(compressed_data, w, h)
            non_zero = sum(1 for p in decompressed if p != 0)
            
            print(f"Tile {i:2d}: {w:2d}x{h:2d}, 非零像素={non_zero:3d}/{w*h}")
            
            # 保存图像
            img = Image.new('RGB', (w, h))
            pixels = img.load()
            for y in range(h):
                for x in range(w):
                    idx = decompressed[y * w + x]
                    pixels[x, y] = palette[idx]
            
            tile_path = os.path.join(output_dir, f'index0_tile_{i:02d}_{w}x{h}.png')
            img.save(tile_path)
        except Exception as e:
            print(f"Tile {i}: 解压失败 - {e}")
