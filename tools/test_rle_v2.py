#!/usr/bin/env python3
"""验证修正后的RLE解码逻辑"""

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
    
    width = struct.unpack('<H', res_data[0:2])[0]
    height = struct.unpack('<H', res_data[2:4])[0]
    pal_window = res_data[4]
    
    rle_data = res_data[5:]
    
    print(f"索引1: {width}x{height}, palette_window={pal_window}")
    print(f"RLE数据大小: {len(rle_data)}")
    
    def decompress_rle_v2(src, dst_width, dst_height):
        """修正后的RLE解码 (按行处理)"""
        dst_size = dst_width * dst_height
        dst = [0] * dst_size
        
        src_idx = 0
        src_size = len(src)
        
        for row in range(dst_height):
            remaining = dst_width
            dst_idx = row * dst_width
            
            while remaining > 0 and src_idx < src_size:
                ctrl = src[src_idx]
                src_idx += 1
                
                bit7 = (ctrl >> 7) & 1
                bit6 = (ctrl >> 6) & 1
                count = (ctrl & 0x3F) + 1
                
                if bit7 == 0:
                    if bit6 == 0:
                        # FILL: 连续填充
                        actual_count = min(count, remaining)
                        
                        if src_idx < src_size:
                            fill_val = src[src_idx]
                            src_idx += 1
                            
                            for i in range(actual_count):
                                if dst_idx < dst_size:
                                    dst[dst_idx] = fill_val
                                    dst_idx += 1
                        
                        remaining -= actual_count
                        
                    else:
                        # COPY_SPEC: 间隔写入 (每次循环dst前进2)
                        total_consume = count * 2
                        actual_count = count
                        
                        if total_consume > remaining:
                            actual_count = remaining // 2
                            total_consume = actual_count * 2
                        
                        if src_idx < src_size:
                            val = src[src_idx]
                            src_idx += 1
                            
                            for i in range(actual_count):
                                if dst_idx < dst_size:
                                    dst[dst_idx] = val
                                    dst_idx += 2  # 关键：前进2
                        
                        remaining -= total_consume
                        
                else:
                    if bit6 == 0:
                        # COPY_STD: 连续复制
                        actual_count = min(count, remaining)
                        actual_count = min(actual_count, src_size - src_idx)
                        
                        for i in range(actual_count):
                            if dst_idx < dst_size and src_idx < src_size:
                                dst[dst_idx] = src[src_idx]
                                src_idx += 1
                                dst_idx += 1
                        
                        remaining -= actual_count
                        
                    else:
                        # SKIP: 跳过
                        actual_count = min(count, remaining)
                        dst_idx += actual_count
                        remaining -= actual_count
        
        return dst
    
    # 解码
    decoded = decompress_rle_v2(rle_data, width, height)
    
    non_zero = sum(1 for p in decoded if p != 0)
    print(f"解码后非零像素: {non_zero}/{width*height}")
    
    # 应用palette_window
    adjusted = [(pal_window + p) & 0xFF for p in decoded]
    adjusted_non_zero = sum(1 for p in adjusted if p != 0)
    print(f"应用palette_window后非零像素: {adjusted_non_zero}/{width*height}")
    
    # 加载调色板
    f.seek(4 * 0 + 6)
    pal_data_info = f.read(8)
    pal_start, pal_end = struct.unpack('<II', pal_data_info)
    pal_size = pal_end - pal_start
    
    f.seek(pal_start)
    pal_data = f.read(pal_size)
    
    palette = []
    for i in range(0, 768, 3):
        r, g, b = pal_data[i], pal_data[i+1], pal_data[i+2]
        r = (r << 2) | (r >> 4)
        g = (g << 2) | (g >> 4)
        b = (b << 2) | (b >> 4)
        palette.append((r, g, b))
    
    # 渲染图像
    img = Image.new('RGB', (width, height))
    for y in range(height):
        for x in range(width):
            idx = y * width + x
            pal_idx = adjusted[idx]
            img.putpixel((x, y), palette[pal_idx])
    
    os.makedirs('output', exist_ok=True)
    output_path = 'output/idx1_rle_v2.png'
    img.save(output_path)
    print(f"\n保存图像: {output_path}")
    
    # 显示前3行
    print("\n" + "="*70)
    print("前3行像素分布:")
    print("="*70)
    
    for y in range(min(3, height)):
        row_start = y * width
        row_end = row_start + width
        row_data = adjusted[row_start:row_end]
        
        chars = []
        for p in row_data:
            if p == 0:
                chars.append('·')
            elif p < 32:
                chars.append('.')
            elif p < 64:
                chars.append('o')
            elif p < 128:
                chars.append('O')
            else:
                chars.append('#')
        
        non_zero_in_row = sum(1 for p in row_data if p != 0)
        print(f"行{y:2d} ({non_zero_in_row:2d}): {''.join(chars)}")
