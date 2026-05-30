#!/usr/bin/env python3
"""
追踪游戏实际渲染管线
sub_4E98D: RLE解压 → 输出原始像素索引
sub_4EBFF + sub_4EC66: 渲染像素到屏幕（使用不同的像素编码）
"""

import struct
from pathlib import Path
from PIL import Image

FDOTHER_PATH = Path("game/FDOTHER.DAT")

def decode_4ec66_pixel_stream(src_data, src_start, width, height):
    """
    按照sub_4EBFF + sub_4EC66解码像素流
    像素数据从src_start开始
    """
    if len(src_data) <= src_start:
        return bytearray()
    
    pixel_data = src_data[src_start:]
    dst = bytearray(width * height)
    
    src_pos = 0
    ah = 0  # 运行长度计数器
    prev_al = 0  # 上次读取的像素值
    
    dst_pos = 0
    for row in range(height):
        for col in range(width):
            if dst_pos >= len(dst):
                break
            
            if ah > 0:
                # AH > 0: 重复之前的像素值
                ah -= 1
                pixel = prev_al
            else:
                # AH == 0: 读取新字节
                if src_pos >= len(pixel_data):
                    break
                al = pixel_data[src_pos]
                src_pos += 1
                
                if al > 0xC0:
                    # AL > 0xC0: 运行长度编码
                    ah = al - 0xC1
                    if src_pos >= len(pixel_data):
                        break
                    al = pixel_data[src_pos]
                    src_pos += 1
                    prev_al = al
                    pixel = al
                else:
                    # AL <= 0xC0: 直接像素值
                    prev_al = al
                    pixel = al
            
            dst[dst_pos] = pixel
            dst_pos += 1
    
    return dst

def test_actual_pipeline():
    """测试实际游戏渲染管线"""
    with open(FDOTHER_PATH, 'rb') as f:
        data = f.read()
    
    # 读取索引表
    offsets = []
    table_offset = 6
    while table_offset + 4 <= len(data):
        res_offset = struct.unpack_from('<I', data, table_offset)[0]
        if res_offset == 0 or res_offset > len(data):
            break
        offsets.append(res_offset)
        table_offset += 4
    
    # 索引0调色板
    idx0_data = data[offsets[0]:offsets[1]]
    
    # 索引1数据
    idx1_data = data[offsets[1]:offsets[2]]
    
    print(f"索引1数据:")
    print(f"  大小: {len(idx1_data)} 字节")
    print(f"  前10字节: {' '.join(f'{b:02X}' for b in idx1_data[:10])}")
    
    # 尝试sub_4EC66解码（像素数据从偏移0开始）
    for start_offset in [0, 4, 5]:
        width = struct.unpack_from('<H', idx1_data, 0)[0]
        height = struct.unpack_from('<H', idx1_data, 2)[0]
        
        if width == 0 or height == 0:
            continue
        
        print(f"\n{'='*60}")
        print(f"尝试sub_4EC66解码 (像素数据从偏移{start_offset}开始):")
        print(f"  宽度: {width}, 高度: {height}")
        
        decoded = decode_4ec66_pixel_stream(idx1_data, start_offset, width, height)
        
        if len(decoded) == 0:
            continue
        
        # 统计
        non_zero = sum(1 for p in decoded if p != 0)
        unique_vals = sorted(set(decoded))
        
        print(f"  非零像素: {non_zero}/{width*height}")
        print(f"  唯一值数量: {len(unique_vals)}")
        if len(unique_vals) <= 30:
            print(f"  唯一值: {unique_vals}")
        else:
            print(f"  唯一值前30: {unique_vals[:30]}")
        
        # 渲染
        img = Image.new('RGB', (width, height))
        for y in range(height):
            for x in range(width):
                idx = y * width + x
                if idx < len(decoded):
                    pal_idx = decoded[idx]
                    if pal_idx < 256:
                        r = idx0_data[pal_idx * 3]
                        g = idx0_data[pal_idx * 3 + 1]
                        b = idx0_data[pal_idx * 3 + 2]
                        img.putpixel((x, y), (r, g, b))
        
        img.save(f'output/idx1_4ec66_offset{start_offset}.png')
        print(f"  已保存: output/idx1_4ec66_offset{start_offset}.png")

if __name__ == '__main__':
    test_actual_pipeline()
