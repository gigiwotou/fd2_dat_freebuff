#!/usr/bin/env python3
"""
详细分析FDOTHER索引0的结构，找出窗口tile集
"""

import struct
import os
from PIL import Image

fdother_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'FDOTHER.DAT')
output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')

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

with open(fdother_path, 'rb') as f:
    f.seek(6)
    resource_count = struct.unpack('<I', f.read(4))[0]
    f.seek(10)
    offsets = []
    for i in range(resource_count):
        offset = struct.unpack('<I', f.read(4))[0]
        offsets.append(offset)
    
    # 索引0
    start0 = offsets[0]
    end0 = offsets[1]
    size0 = end0 - start0
    
    f.seek(start0)
    data0 = f.read(size0)
    
    print(f"索引0:")
    print(f"  偏移: 0x{start0:X} - 0x{end0:X}")
    print(f"  大小: {size0}")
    print(f"  前32字节: {data0[:32].hex()}")
    
    # 解析头部
    # 格式可能是: WORD宽度 + WORD高度 + WORD tile数量 + WORD未知 + DWORD偏移表
    width = struct.unpack('<H', data0[0:2])[0]
    height = struct.unpack('<H', data0[2:4])[0]
    tile_count = struct.unpack('<H', data0[4:6])[0]
    
    print(f"\n头部解析:")
    print(f"  WORD[0]: {width} (可能是宽度)")
    print(f"  WORD[1]: {height} (可能是高度)")
    print(f"  WORD[2]: {tile_count} (可能是tile数量)")
    
    # 检查偏移表（从偏移6开始，每4字节一个DWORD）
    print(f"\n偏移表 (从偏移6开始):")
    tile_offsets = []
    for i in range(min(20, tile_count)):
        offset_addr = 6 + i * 4
        if offset_addr + 4 > size0:
            break
        tile_offset = struct.unpack('<I', data0[offset_addr:offset_addr+4])[0]
        tile_offsets.append(tile_offset)
        print(f"  Tile {i}: 偏移=0x{tile_offset:X}")
    
    palette = load_palette()
    
    # 检查前5个tile的实际数据
    print(f"\n{'='*60}")
    print(f"检查tile 0-4的实际数据:")
    print(f"{'='*60}")
    
    for i in range(min(5, len(tile_offsets))):
        tile_offset = tile_offsets[i]
        
        # 从索引0的起始位置+tile_offset读取
        f.seek(start0 + tile_offset)
        raw_data = f.read(64)
        
        print(f"\nTile {i} (偏移0x{tile_offset:X}):")
        print(f"  前32字节: {raw_data[:32].hex()}")
        
        # 尝试不同的解析方式
        # 方式1: WORD w + WORD h + 像素
        w1 = struct.unpack('<H', raw_data[0:2])[0]
        h1 = struct.unpack('<H', raw_data[2:4])[0]
        print(f"  解析1 (WORD w,h): {w1}x{h1}")
        
        # 方式2: 直接是像素数据（假设16x16）
        # 检查首字节是否是RLE控制字节
        first_byte = raw_data[0]
        if first_byte >= 192 or (128 <= first_byte < 192) or first_byte < 64:
            print(f"  可能是RLE压缩数据 (首字节=0x{first_byte:02X})")
            
            # 尝试用16x16解压
            try:
                decompressed = decompress_rle(raw_data, 16, 16)
                non_zero = sum(1 for p in decompressed if p != 0)
                print(f"  如果按16x16解压: 非零像素={non_zero}/256")
                
                # 保存图像
                img = Image.new('RGB', (16, 16))
                pixels = img.load()
                for y in range(16):
                    for x in range(16):
                        idx = decompressed[y * 16 + x]
                        pixels[x, y] = palette[idx]
                
                tile_path = os.path.join(output_dir, f'index0_tile_{i:02d}_16x16.png')
                img.save(tile_path)
                print(f"  已保存: {tile_path}")
            except Exception as e:
                print(f"  解压失败: {e}")
