#!/usr/bin/env python3
"""
验证palette_window应用是否正确
"""
import struct
from PIL import Image
import os

dat_path = 'bin/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    # 读取索引1
    f.seek(4 * 1 + 6)
    data = f.read(8)
    start_offset, end_offset = struct.unpack('<II', data)
    size = end_offset - start_offset
    
    f.seek(start_offset)
    res_data = f.read(size)
    
    width = 24
    height = 24
    pal_window = 20
    
    rle_data = res_data[5:]
    
    # 简化RLE解码 (假设全是FILL)
    dst = [0] * (width * height)
    src_idx = 0
    dst_idx = 0
    
    for row in range(height):
        remaining = width
        
        while remaining > 0 and src_idx < len(rle_data) - 1:
            ctrl = rle_data[src_idx]
            src_idx += 1
            
            count = (ctrl & 0x3F) + 1
            fill_val = rle_data[src_idx]
            src_idx += 1
            
            actual = min(count, remaining)
            for i in range(actual):
                dst[dst_idx] = fill_val
                dst_idx += 1
            
            remaining -= actual
    
    # 应用palette_window
    adjusted = [(pal_window + p) & 0xFF for p in dst]
    
    # 加载调色板
    f.seek(4 * 0 + 6)
    pal_data_info = f.read(8)
    pal_start, pal_end = struct.unpack('<II', pal_data_info)
    
    f.seek(pal_start)
    pal_data = f.read(pal_end - pal_start)
    
    palette = []
    for i in range(0, 768, 3):
        r, g, b = pal_data[i], pal_data[i+1], pal_data[i+2]
        r = (r << 2) | (r >> 4)
        g = (g << 2) | (g >> 4)
        b = (b << 2) | (b >> 4)
        palette.append((r, g, b))
    
    # 渲染原始和解调后的图像
    img_raw = Image.new('RGB', (width, height))
    img_adj = Image.new('RGB', (width, height))
    
    for y in range(height):
        for x in range(width):
            idx = y * width + x
            img_raw.putpixel((x, y), palette[dst[idx]])
            img_adj.putpixel((x, y), palette[adjusted[idx]])
    
    os.makedirs('output', exist_ok=True)
    img_raw.save('output/idx1_no_palette_window.png')
    img_adj.save('output/idx1_with_palette_window.png')
    
    print("保存图像:")
    print("  output/idx1_no_palette_window.png")
    print("  output/idx1_with_palette_window.png")
    
    # 统计
    print(f"\n原始非零像素: {sum(1 for p in dst if p != 0)}/{width*height}")
    print(f"调整后非零像素: {sum(1 for p in adjusted if p != 0)}/{width*height}")
    
    # 显示调色板颜色样本
    print(f"\n调色板颜色样本 (索引0, 20, 50, 86):")
    for idx in [0, 20, 50, 86]:
        r, g, b = palette[idx]
        print(f"  [{idx}] RGB=({r},{g},{b})")
