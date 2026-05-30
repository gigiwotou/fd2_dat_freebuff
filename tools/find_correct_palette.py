#!/usr/bin/env python3
"""系统测试不同调色板和palette_window组合"""

import struct
from pathlib import Path
from PIL import Image
import itertools

FDOTHER_PATH = Path("game/FDOTHER.DAT")

# RLE操作定义
OP_FILL = 0
OP_COPY_SPEC = 1
OP_COPY_STD = 2
OP_SKIP = 3

OP_NAMES = {
    OP_FILL: "FILL",
    OP_COPY_SPEC: "COPY_SPEC",
    OP_COPY_STD: "COPY_STD",
    OP_SKIP: "SKIP"
}

# 正确的RLE映射 (基于MCP分析)
CORRECT_MAPPING = {
    (0, 0): OP_FILL,
    (0, 1): OP_COPY_SPEC,
    (1, 0): OP_COPY_STD,
    (1, 1): OP_SKIP,
}

def decode_rle(rle_data, w, h, mapping=None):
    """使用指定映射解码RLE"""
    if mapping is None:
        mapping = CORRECT_MAPPING
    
    dst = bytearray(w * h)
    dst_idx = 0
    src_idx = 0
    
    for row in range(h):
        remaining = w
        
        while remaining > 0 and src_idx < len(rle_data):
            ctrl = rle_data[src_idx]
            src_idx += 1
            
            bit7 = (ctrl >> 7) & 1
            bit6 = (ctrl >> 6) & 1
            count = (ctrl & 0x3F) + 1
            
            op = mapping.get((bit7, bit6), OP_FILL)
            
            if op == OP_FILL:
                actual_count = min(count, remaining)
                if src_idx < len(rle_data):
                    fill_val = rle_data[src_idx]
                    src_idx += 1
                    for i in range(actual_count):
                        if dst_idx < len(dst):
                            dst[dst_idx] = fill_val
                            dst_idx += 1
                remaining -= actual_count
                
            elif op == OP_COPY_SPEC:
                total_consume = count * 2
                actual_count = count
                if total_consume > remaining:
                    actual_count = remaining // 2
                    total_consume = actual_count * 2
                if src_idx < len(rle_data):
                    val = rle_data[src_idx]
                    src_idx += 1
                    for i in range(actual_count):
                        if dst_idx < len(dst):
                            dst[dst_idx] = val
                            dst_idx += 2
                remaining -= total_consume
                
            elif op == OP_COPY_STD:
                actual_count = min(count, remaining, len(rle_data) - src_idx)
                for i in range(actual_count):
                    if dst_idx < len(dst) and src_idx < len(rle_data):
                        dst[dst_idx] = rle_data[src_idx]
                        src_idx += 1
                        dst_idx += 1
                remaining -= actual_count
                
            elif op == OP_SKIP:
                actual_count = min(count, remaining)
                dst_idx += actual_count
                remaining -= actual_count
    
    return dst

def find_palettes(data, offsets):
    """找到所有调色板资源"""
    palettes = {}
    for idx, offset in enumerate(offsets):
        if idx + 1 < len(offsets):
            size = offsets[idx + 1] - offset
        else:
            size = len(data) - offset
        
        if size == 768:
            palettes[idx] = data[offset:offset + 768]
    
    return palettes

def test_palette_combinations():
    """测试所有调色板和palette_window组合"""
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
    
    # 找到所有调色板
    palettes = find_palettes(data, offsets)
    print(f"找到 {len(palettes)} 个调色板资源: {list(palettes.keys())}")
    
    # 索引1数据
    idx1_data = data[offsets[1]:offsets[2]]
    w = struct.unpack_from('<H', idx1_data, 0)[0]
    h = struct.unpack_from('<H', idx1_data, 2)[0]
    pw = idx1_data[4]
    
    print(f"\n索引1: {w}x{h}, palette_window={pw}")
    
    # RLE数据
    rle_data = idx1_data[5:]
    
    # 解码
    decoded = decode_rle(rle_data, w, h)
    
    non_zero = sum(1 for p in decoded if p != 0)
    unique_vals = sorted(set(decoded))
    print(f"解码结果: {non_zero} 非零像素, {len(unique_vals)} 唯一值")
    print(f"唯一值: {unique_vals[:20]}")
    
    # 测试所有调色板 + 不同palette_window
    results = []
    
    for pal_idx, pal_data in palettes.items():
        for test_pw in [0, pw, 16, 32, 48, 64, 96, 128]:
            # 渲染
            img = Image.new('RGB', (w, h))
            color_count = {}
            
            for y in range(h):
                for x in range(w):
                    idx = y * w + x
                    pixel_val = decoded[idx]
                    pal_entry = (test_pw + pixel_val) & 0xFF
                    r = pal_data[pal_entry * 3]
                    g = pal_data[pal_entry * 3 + 1]
                    b = pal_data[pal_entry * 3 + 2]
                    img.putpixel((x, y), (r, g, b))
                    
                    # 统计颜色使用
                    if pixel_val != 0:
                        color = (r, g, b)
                        color_count[color] = color_count.get(color, 0) + 1
            
            # 评分: 图标应该有少量主要颜色
            main_colors = len(color_count)
            
            results.append({
                'palette_idx': pal_idx,
                'pw': test_pw,
                'img': img,
                'main_colors': main_colors,
                'color_distribution': color_count,
            })
    
    # 按颜色数量排序（图标应该使用较少颜色）
    results.sort(key=lambda x: x['main_colors'])
    
    print(f"\n{'='*60}")
    print(f"Top 15 最佳调色板+pw组合:")
    print(f"{'='*60}")
    
    for i, result in enumerate(results[:15]):
        pal_idx = result['palette_idx']
        pw = result['pw']
        colors = result['main_colors']
        
        print(f"\n排名 {i+1}: 调色板索引{pal_idx}, pw={pw}, 颜色数={colors}")
        if result['color_distribution']:
            print(f"  主要颜色:")
            sorted_colors = sorted(result['color_distribution'].items(), key=lambda x: x[1], reverse=True)[:5]
            for color, count in sorted_colors:
                print(f"    RGB{color}: {count}像素")
        
        # 保存图像
        filename = f'output/idx1_pal{pal_idx}_pw{pw}_colors{colors}.png'
        result['img'].save(filename)
        print(f"  已保存: {filename}")

if __name__ == '__main__':
    test_palette_combinations()
