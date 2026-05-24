#!/usr/bin/env python3
"""
详细分析索引4的tile 1-17，检查tile数据是否包含padding
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
    
    # 读取tile偏移表
    tile_offsets_raw = []
    for i in range(tile_count):
        offset_addr = 6 + i * 4
        tile_offset = struct.unpack('<I', data4[offset_addr:offset_addr+4])[0]
        tile_offsets_raw.append(tile_offset)
    
    palette = load_palette()
    
    print(f"\n{'='*60}")
    print(f"分析tile 1-17的原始数据:")
    print(f"{'='*60}")
    
    for i in range(1, 18):
        if i >= tile_count:
            break
            
        tile_offset = tile_offsets_raw[i]
        next_offset = tile_offsets_raw[i + 1] if i + 1 < tile_count else size4
        
        f.seek(start4 + tile_offset)
        wh_data = f.read(4)
        w = struct.unpack('<H', wh_data[0:2])[0]
        h = struct.unpack('<H', wh_data[2:4])[0]
        
        compressed_size = next_offset - tile_offset
        
        # 读取原始压缩数据
        f.seek(start4 + tile_offset)
        raw_data = f.read(compressed_size)
        
        # 打印原始数据前16字节
        print(f"\nTile {i}:")
        print(f"  声明尺寸: {w}x{h}")
        print(f"  压缩数据大小: {compressed_size}")
        print(f"  原始数据前32字节: {raw_data[:32].hex()}")
        
        # 解压
        decompressed = decompress_rle(raw_data, w, h)
        non_zero = sum(1 for p in decompressed if p != 0)
        print(f"  非零像素: {non_zero}/{w*h}")
        
        # 检查是否是16x16的tile但声明为小尺寸
        # 如果tile实际包含16x16的数据，但只声明了部分区域
        # 那么压缩数据大小应该接近16*16=256字节
        expected_full_size = 16 * 16
        if compressed_size > expected_full_size:
            print(f"  >>> 压缩数据大于16x16，可能包含padding <<<")
        
        # 创建图像
        img = Image.new('RGB', (w, h))
        pixels = img.load()
        for y in range(h):
            for x in range(w):
                idx = decompressed[y * w + x]
                pixels[x, y] = palette[idx]
        
        # 也创建16x16版本
        img_16x16 = Image.new('RGB', (16, 16), (0, 0, 0))
        for y in range(h):
            for x in range(w):
                idx = decompressed[y * w + x]
                if idx != 0:
                    img_16x16.putpixel((x, y), palette[idx])
        
        tile_path = os.path.join(output_dir, f'index4_tile_{i:02d}_{w}x{h}.png')
        img.save(tile_path)
        
        tile_16x16_path = os.path.join(output_dir, f'index4_tile_{i:02d}_16x16.png')
        img_16x16.save(tile_16x16_path)
        
        print(f"  已保存: {tile_path}")
        print(f"  已保存: {tile_16x16_path}")
