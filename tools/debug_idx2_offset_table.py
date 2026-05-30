#!/usr/bin/env python3
"""
根据MCP反汇编sub_111BA分析索引2的偏移表结构

索引2数据：
- 大小=37680字节
- 前312字节是78个偏移值（每个4字节）
- 这些偏移是相对于索引2数据区起始的
"""

import struct
from PIL import Image
import os

dat_path = 'bin/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    # 读取索引2
    f.seek(4 * 2 + 6)
    data = f.read(8)
    start_offset, end_offset = struct.unpack('<II', data)
    size = end_offset - start_offset
    
    print(f"索引2: 偏移=0x{start_offset:08x}, 大小={size}")
    
    f.seek(start_offset)
    idx2_data = f.read(size)
    
    # 解析偏移表 (前312字节 = 78个dword)
    offset_count = 78
    offsets = []
    
    print(f"\n偏移表 (78个偏移值):")
    for i in range(offset_count):
        addr = i * 4
        off = struct.unpack('<I', idx2_data[addr:addr+4])[0]
        offsets.append(off)
        
        if i < 10 or i >= 73:  # 显示前10个和后5个
            print(f"  偏移[{i:2d}] = 0x{off:08x} ({off:6d})")
        elif i == 10:
            print(f"  ...")
    
    # 验证偏移值的合理性
    print(f"\n验证偏移值:")
    valid_offsets = [off for off in offsets if off < size]
    invalid_offsets = [off for off in offsets if off >= size]
    
    print(f"  有效偏移 (<{size}): {len(valid_offsets)}")
    print(f"  无效偏移 (>={size}): {len(invalid_offsets)}")
    
    if invalid_offsets:
        print(f"  无效偏移值: {[f'0x{o:08x}' for o in invalid_offsets[:5]]}")
    
    # 分析前5个子资源
    print(f"\n" + "="*70)
    print("前5个子资源分析:")
    print("="*70)
    
    for i in range(min(5, offset_count - 1)):
        start = offsets[i]
        end = offsets[i + 1]
        
        if start >= size or end > size:
            print(f"\n子资源[{i}]: 偏移无效 (start=0x{start:08x}, end=0x{end:08x})")
            continue
        
        res_size = end - start
        print(f"\n子资源[{i}]: 偏移=0x{start:08x}, 大小={res_size}")
        
        # 读取子资源数据
        res_data = idx2_data[start:start+min(res_size, 50)]
        print(f"  前20字节: {' '.join(f'{b:02x}' for b in res_data[:20])}")
        
        # 尝试解析为Tile
        if res_size >= 5:
            w = struct.unpack('<H', res_data[0:2])[0]
            h = struct.unpack('<H', res_data[2:4])[0]
            pal_window = res_data[4]
            
            if w > 0 and w <= 640 and h > 0 and h <= 480:
                print(f"  -> Tile: {w}x{h}, palette_window={pal_window}")
                
                # 简单解码并渲染前3个子资源
                if i < 3:
                    rle_data = res_data[5:]
                    dst = [0] * (w * h)
                    src_idx = 0
                    dst_idx = 0
                    
                    for row in range(h):
                        remaining = w
                        while remaining > 0 and src_idx < len(rle_data) - 1:
                            ctrl = rle_data[src_idx]
                            src_idx += 1
                            count = (ctrl & 0x3F) + 1
                            fill_val = rle_data[src_idx]
                            src_idx += 1
                            actual = min(count, remaining)
                            for j in range(actual):
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
                    for j in range(0, 768, 3):
                        r, g, b = pal_data[j], pal_data[j+1], pal_data[j+2]
                        r = (r << 2) | (r >> 4)
                        g = (g << 2) | (g >> 4)
                        b = (b << 2) | (b >> 4)
                        palette.append((r, g, b))
                    
                    # 渲染
                    img = Image.new('RGB', (w, h))
                    for y in range(h):
                        for x in range(w):
                            idx = y * w + x
                            img.putpixel((x, y), palette[adjusted[idx]])
                    
                    os.makedirs('output', exist_ok=True)
                    output_path = f'output/idx2_sub{i}.png'
                    img.save(output_path)
                    print(f"  保存图像: {output_path}")
