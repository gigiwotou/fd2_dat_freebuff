#!/usr/bin/env python3
"""
根据MCP反汇编精确实现sub_4E98D的value_1==-1分支

关键发现 - COPY_SPEC模式(0x4EA00):
4ea0c  inc     edi     ; dst前进1
4ea0d  stosb           ; 写入值, dst再前进1
4ea0e  loop    loc_4EA0C

这意味着每次循环dst前进2! (inc edi + stosb自动增加edi)
所以COPY_SPEC写入count个值,但占用2*count个位置
写入位置: 0, 2, 4, 6, ... (偶数索引)
"""

print("="*70)
print("基于MCP反汇编的RLE算法精确实现 (value_1 == -1)")
print("="*70)

# 查找FDOTHER.dat
import os
import glob

dat_files = glob.glob('**/FDOTHER.dat', recursive=True) + glob.glob('**/FDOTHER.DAT', recursive=True)
if not dat_files:
    dat_files = glob.glob('data/FDOTHER*', recursive=True)

if not dat_files:
    print("未找到FDOTHER.dat文件, 尝试在output目录查找...")
    dat_files = glob.glob('output/FDOTHER*', recursive=True)

if not dat_files:
    print("错误: 未找到FDOTHER.dat")
    exit(1)

dat_path = dat_files[0]
print(f"使用数据文件: {dat_path}")

import struct

with open(dat_path, 'rb') as f:
    # 读取offset table (从0x800开始, 每个条目12字节)
    f.seek(0x800)
    offset_table = []
    for i in range(200):
        data = f.read(12)
        if len(data) < 12:
            break
        offset, size, flags = struct.unpack('<III', data)
        offset_table.append((offset, size, flags))
    
    print(f"Offset table entries: {len(offset_table)}")
    
    # 索引1
    if len(offset_table) > 1:
        idx1_off, idx1_sz, idx1_flags = offset_table[1]
        print(f"\n索引1: offset=0x{idx1_off:08x}, size={idx1_sz}, flags=0x{idx1_flags:08x}")
        
        f.seek(idx1_off)
        idx1_data = f.read(idx1_sz)
        
        # 解析头部 (假设5字节: width:2 + height:2 + palette_window:1)
        if len(idx1_data) >= 5:
            width = struct.unpack('<H', idx1_data[0:2])[0]
            height = struct.unpack('<H', idx1_data[2:4])[0]
            pal_window = idx1_data[4]
            
            print(f"头部: {width}x{height}, palette_window={pal_window}")
            print(f"预期像素: {width * height}")
            print(f"RLE数据大小: {idx1_sz - 5}")
            
            rle_data = idx1_data[5:]
            
            def decompress_rle_mcp_exact(src, dst_width, dst_height):
                """
                100%按照MCP反汇编实现sub_4E98D (value_1 == -1分支)
                """
                dst_size = dst_width * dst_height
                dst = [0] * dst_size
                
                src_idx = 0
                dst_idx = 0
                src_size = len(src)
                
                # 外层循环: 按行处理 (arg8 = height)
                for row in range(dst_height):
                    remaining = dst_width  # bx = width
                    
                    while remaining > 0 and src_idx < src_size:
                        # 读取控制字节
                        ctrl = src[src_idx]
                        src_idx += 1
                        
                        bit7 = (ctrl >> 7) & 1
                        bit6 = (ctrl >> 6) & 1
                        
                        # cl = ctrl, 然后shl cl, 1两次检查bit7和bit6
                        if bit7 == 0:
                            if bit6 == 0:
                                # FILL (0x4E9EE)
                                # count = (ctrl >> 2) + 1
                                count = ((ctrl & 0x3F) >> 2) + 1
                                
                                # sub bx, cx
                                if count > remaining:
                                    count = remaining
                                
                                # lodsb - 读取填充值
                                if src_idx < src_size:
                                    fill_val = src[src_idx]
                                    src_idx += 1
                                    
                                    # rep stosb - 连续填充count次
                                    for i in range(count):
                                        if dst_idx < dst_size:
                                            dst[dst_idx] = fill_val
                                            dst_idx += 1
                                
                                remaining -= count
                                
                            else:
                                # COPY_SPEC (0x4EA00) - 关键!
                                # count = (ctrl >> 2) + 1
                                count = ((ctrl & 0x3F) >> 2) + 1
                                
                                # sub bx, cx (第一次)
                                # sub bx, cx (第二次)
                                # 总共消耗2*count!
                                total_consume = count * 2
                                if total_consume > remaining:
                                    # 如果剩余不够,调整count
                                    count = remaining // 2
                                    total_consume = count * 2
                                
                                # lodsb - 读取值
                                if src_idx < src_size:
                                    value = src[src_idx]
                                    src_idx += 1
                                    
                                    # loop: inc edi; stosb
                                    # 每次循环: dst前进2 (inc + stosb)
                                    for i in range(count):
                                        if dst_idx < dst_size:
                                            dst[dst_idx] = value
                                            dst_idx += 2  # inc edi + stosb
                                
                                remaining -= total_consume
                                
                        else:
                            if bit6 == 0:
                                # COPY_STD (0x4EA17)
                                # count = (ctrl >> 2) + 1
                                count = ((ctrl & 0x3F) >> 2) + 1
                                
                                if count > remaining:
                                    count = remaining
                                
                                # rep movsb - 从src复制count个字节
                                for i in range(count):
                                    if dst_idx < dst_size and src_idx < src_size:
                                        dst[dst_idx] = src[src_idx]
                                        src_idx += 1
                                        dst_idx += 1
                                
                                remaining -= count
                                
                            else:
                                # SKIP (0x4EA2C)
                                # count = (ctrl >> 2) + 1
                                count = ((ctrl & 0x3F) >> 2) + 1
                                
                                if count > remaining:
                                    count = remaining
                                
                                # add edi, ecx - 跳过count个位置
                                dst_idx += count
                                remaining -= count
                    
                    # 行结束: add edi, edx (edx = stride - width)
                    # 这里假设stride = width, 所以不需要额外前进
            
                return dst
            
            # 解码
            decoded = decompress_rle_mcp_exact(rle_data, width, height)
            
            non_zero = sum(1 for p in decoded if p != 0)
            print(f"\n解码后非零像素: {non_zero}/{width*height}")
            
            # 应用palette_window
            adjusted = [(pal_window + p) & 0xFF for p in decoded]
            adjusted_non_zero = sum(1 for p in adjusted if p != 0)
            print(f"应用palette_window后非零像素: {adjusted_non_zero}/{width*height}")
            
            # 加载调色板并渲染
            pal_files = glob.glob('**/PALETTE*', recursive=True)
            if pal_files:
                pal_path = pal_files[0]
                print(f"\n使用调色板: {pal_path}")
                
                with open(pal_path, 'rb') as pf:
                    pf.seek(0x800)
                    pal_hdr = pf.read(12)
                    pal_off, pal_sz, pal_flags = struct.unpack('<III', pal_hdr)
                    
                    pf.seek(pal_off)
                    pal_data = pf.read(pal_sz)
                    
                    palette = []
                    for i in range(0, min(pal_sz, 256*3), 3):
                        r, g, b = pal_data[i], pal_data[i+1], pal_data[i+2]
                        palette.append((r, g, b))
                    
                    while len(palette) < 256:
                        palette.append((0, 0, 0))
                
                # 渲染图像
                from PIL import Image
                
                img = Image.new('RGB', (width, height))
                for y in range(height):
                    for x in range(width):
                        idx = y * width + x
                        pal_idx = adjusted[idx]
                        img.putpixel((x, y), palette[pal_idx])
                
                os.makedirs('output', exist_ok=True)
                output_path = 'output/idx1_mcp_exact.png'
                img.save(output_path)
                print(f"\n保存图像: {output_path}")
                print(f"图像尺寸: {width}x{height}")
                
                # 分析COPY_SPEC效果
                print("\n" + "="*70)
                print("COPY_SPEC间隔写入效果:")
                print("="*70)
                
                # 显示前5行
                for y in range(min(5, height)):
                    row_start = y * width
                    row_end = row_start + width
                    row_data = adjusted[row_start:row_end]
                    non_zero_in_row = sum(1 for p in row_data if p != 0)
                    print(f"行{y:2d}: 非零像素={non_zero_in_row}/{width}")
                    # 显示像素值(用字符表示)
                    chars = []
                    for p in row_data:
                        if p == 0:
                            chars.append('·')
                        elif p < 50:
                            chars.append('.')
                        elif p < 100:
                            chars.append('o')
                        elif p < 150:
                            chars.append('O')
                        else:
                            chars.append('#')
                    print(f"  {''.join(chars)}")
                
            else:
                print("\n未找到PALETTE文件, 使用灰度渲染")
                from PIL import Image
                
                img = Image.new('L', (width, height))
                for y in range(height):
                    for x in range(width):
                        idx = y * width + x
                        img.putpixel((x, y), adjusted[idx])
                
                os.makedirs('output', exist_ok=True)
                output_path = 'output/idx1_mcp_exact_gray.png'
                img.save(output_path)
                print(f"保存灰度图像: {output_path}")
