#!/usr/bin/env python3
"""
详细分析索引4的tile 1-17，确认窗口边框tile的正确使用方式
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
    
    start4 = offsets[4]
    end4 = offsets[5] if 5 < resource_count else os.path.getsize(fdother_path)
    size4 = end4 - start4
    
    f.seek(start4)
    data4 = f.read(size4)
    
    tile_count = struct.unpack('<H', data4[4:6])[0]
    print(f"索引4 tile数量: {tile_count}")
    
    palette = load_palette()
    
    print(f"\n{'='*60}")
    print(f"分析tile 1-17 (窗口边框tile):")
    print(f"{'='*60}")
    
    # 创建组合图像展示tile 1-17
    # 按功能分组：角(1-4), 上边框(5-6), 下边框(7-8), 左边框(9-11), 右边框(12,14-17), 内容(13)
    
    # 先收集所有tile信息
    tile_info = []
    for i in range(1, 18):
        if i >= tile_count:
            break
            
        offset_addr = 6 + i * 4
        tile_offset = struct.unpack('<I', data4[offset_addr:offset_addr+4])[0]
        
        f.seek(start4 + tile_offset)
        wh_data = f.read(4)
        w = struct.unpack('<H', wh_data[0:2])[0]
        h = struct.unpack('<H', wh_data[2:4])[0]
        
        # 读取压缩数据
        if i + 1 < tile_count:
            next_offset = struct.unpack('<I', data4[6 + (i+1)*4:6 + (i+1)*4+4])[0]
            compressed_size = next_offset - tile_offset
        else:
            compressed_size = size4 - tile_offset
        
        f.seek(start4 + tile_offset)
        compressed_data = f.read(compressed_size)
        
        # 解压
        decompressed = decompress_rle(compressed_data, w, h)
        non_zero = sum(1 for p in decompressed if p != 0)
        
        tile_info.append({
            'index': i,
            'width': w,
            'height': h,
            'data': decompressed,
            'non_zero': non_zero
        })
        
        print(f"Tile {i:2d}: {w:2d}x{h:2d}, 非零像素={non_zero:3d}/{w*h}")
    
    # 创建组合图像
    # 布局：角(1-4)在上排，边框(5-8)在第二排，边框(9-17)在第三排
    # 每个tile按16x16网格显示
    
    grid_size = 16
    combined_width = grid_size * 6  # 最多6列
    combined_height = grid_size * 3  # 3行
    
    combined = Image.new('RGB', (combined_width, combined_height), (0, 0, 0))
    
    # 第一行：角tile 1-4
    for idx, info in enumerate(tile_info[:4]):
        i = info['index']
        w = info['width']
        h = info['height']
        data = info['data']
        
        x_pos = idx * grid_size
        y_pos = 0
        
        for y in range(h):
            for x in range(w):
                pixel = data[y * w + x]
                if pixel != 0:
                    combined.putpixel((x_pos + x, y_pos + y), palette[pixel])
    
    # 第二行：上/下边框 5-8
    for idx, info in enumerate(tile_info[4:8]):
        i = info['index']
        w = info['width']
        h = info['height']
        data = info['data']
        
        x_pos = idx * grid_size
        y_pos = grid_size
        
        for y in range(h):
            for x in range(w):
                pixel = data[y * w + x]
                if pixel != 0:
                    combined.putpixel((x_pos + x, y_pos + y), palette[pixel])
    
    # 第三行：左右边框 9-17
    for idx, info in enumerate(tile_info[8:14]):
        i = info['index']
        w = info['width']
        h = info['height']
        data = info['data']
        
        x_pos = idx * grid_size
        y_pos = grid_size * 2
        
        for y in range(h):
            for x in range(w):
                pixel = data[y * w + x]
                if pixel != 0:
                    combined.putpixel((x_pos + x, y_pos + y), palette[pixel])
    
    combined_path = os.path.join(output_dir, 'window_tiles_1_17_16x16grid.png')
    combined.save(combined_path)
    print(f"\n已保存组合图到: {combined_path}")
    
    # 同时保存每个tile的16x16版本
    for info in tile_info:
        i = info['index']
        w = info['width']
        h = info['height']
        data = info['data']
        
        # 创建16x16图像
        img_16x16 = Image.new('RGB', (16, 16), (0, 0, 0))
        for y in range(h):
            for x in range(w):
                pixel = data[y * w + x]
                if pixel != 0:
                    img_16x16.putpixel((x, y), palette[pixel])
        
        tile_path = os.path.join(output_dir, f'index4_tile_{i:02d}_16x16.png')
        img_16x16.save(tile_path)
    
    print(f"已保存tile 1-17的16x16版本到: {output_dir}")
