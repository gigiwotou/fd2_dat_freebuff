#!/usr/bin/env python3
"""
精确解码索引1的24x24 Tile图像
根据MCP反汇编sub_4E98D (value_1 == -1分支)
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
    
    print(f"索引1: 偏移=0x{start_offset:08x}, 大小={size}")
    
    f.seek(start_offset)
    res_data = f.read(size)
    
    # 解析Tile头
    width = struct.unpack('<H', res_data[0:2])[0]
    height = struct.unpack('<H', res_data[2:4])[0]
    pal_window = res_data[4]
    
    print(f"Tile: {width}x{height}, palette_window={pal_window}")
    print(f"RLE数据大小: {size - 5}")
    
    rle_data = res_data[5:]
    
    def decompress_rle_exact(src, dst_width, dst_height):
        """
        100%按照sub_4E98D汇编实现 (value_1 == -1分支)
        
        操作类型 (bit7, bit6):
        - 00: FILL - 读取1个值，填充count个位置 (连续)
        - 01: COPY_SPEC - 读取1个值，写入count个位置，但消耗2*count (间隔)
        - 10: COPY_STD - 从src复制count个字节
        - 11: SKIP - 跳过count个位置
        """
        dst_size = dst_width * dst_height
        dst = [0] * dst_size
        
        src_idx = 0
        dst_idx = 0
        src_size = len(src)
        
        for row in range(dst_height):
            remaining = dst_width
            
            while remaining > 0 and src_idx < src_size:
                ctrl = src[src_idx]
                src_idx += 1
                
                bit7 = (ctrl >> 7) & 1
                bit6 = (ctrl >> 6) & 1
                count = (ctrl & 0x3F) + 1
                
                if bit7 == 0:
                    if bit6 == 0:
                        # FILL (0x4E9EE)
                        if count > remaining:
                            count = remaining
                        
                        if src_idx < src_size:
                            fill_val = src[src_idx]
                            src_idx += 1
                            
                            for i in range(count):
                                if dst_idx < dst_size:
                                    dst[dst_idx] = fill_val
                                    dst_idx += 1
                        
                        remaining -= count
                        
                    else:
                        # COPY_SPEC (0x4EA00) - 关键！
                        # sub bx, cx 执行两次 = 消耗2*count
                        # 但每次循环只写入1个值，dst前进2
                        count = (ctrl & 0x3F) + 1
                        
                        total_consume = count * 2
                        if total_consume > remaining:
                            count = remaining // 2
                            total_consume = count * 2
                        
                        if src_idx < src_size:
                            value = src[src_idx]
                            src_idx += 1
                            
                            # loop: inc edi; stosb
                            # 每次循环: dst前进2 (inc edi + stosb自动增加)
                            for i in range(count):
                                if dst_idx < dst_size:
                                    dst[dst_idx] = value
                                    dst_idx += 2
                        
                        remaining -= total_consume
                        
                else:
                    if bit6 == 0:
                        # COPY_STD (0x4EA17)
                        if count > remaining:
                            count = remaining
                        
                        for i in range(count):
                            if dst_idx < dst_size and src_idx < src_size:
                                dst[dst_idx] = src[src_idx]
                                src_idx += 1
                                dst_idx += 1
                        
                        remaining -= count
                        
                    else:
                        # SKIP (0x4EA2C)
                        if count > remaining:
                            count = remaining
                        
                        dst_idx += count
                        remaining -= count
        
        return dst
    
    # 解码
    decoded = decompress_rle_exact(rle_data, width, height)
    
    non_zero = sum(1 for p in decoded if p != 0)
    print(f"\n解码后非零像素: {non_zero}/{width*height}")
    
    # 应用palette_window
    adjusted = [(pal_window + p) & 0xFF for p in decoded]
    adjusted_non_zero = sum(1 for p in adjusted if p != 0)
    print(f"应用palette_window后非零像素: {adjusted_non_zero}/{width*height}")
    
    # 加载调色板 (索引0)
    f.seek(4 * 0 + 6)
    pal_data_info = f.read(8)
    pal_start, pal_end = struct.unpack('<II', pal_data_info)
    pal_size = pal_end - pal_start
    
    f.seek(pal_start)
    pal_data = f.read(pal_size)
    
    palette = []
    for i in range(0, min(pal_size, 768), 3):
        r, g, b = pal_data[i], pal_data[i+1], pal_data[i+2]
        # 6bit转8bit
        r = (r << 2) | (r >> 4)
        g = (g << 2) | (g >> 4)
        b = (b << 2) | (b >> 4)
        palette.append((r, g, b))
    
    while len(palette) < 256:
        palette.append((0, 0, 0))
    
    print(f"\n调色板加载完成: {len(palette)}色")
    
    # 渲染图像
    img = Image.new('RGB', (width, height))
    for y in range(height):
        for x in range(width):
            idx = y * width + x
            pal_idx = adjusted[idx]
            img.putpixel((x, y), palette[pal_idx])
    
    os.makedirs('output', exist_ok=True)
    output_path = 'output/idx1_correct.png'
    img.save(output_path)
    print(f"\n保存图像: {output_path}")
    print(f"图像尺寸: {width}x{height}")
    
    # 显示像素分布
    print("\n" + "="*70)
    print("图像像素分布:")
    print("="*70)
    
    for y in range(height):
        row_start = y * width
        row_end = row_start + width
        row_data = adjusted[row_start:row_end]
        
        # 用字符表示
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
