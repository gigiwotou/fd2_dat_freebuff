#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

"""对比索引4和索引13，确定哪个是正确的窗口边框tile集"""

import struct
from pathlib import Path

def analyze_index(data, idx, offsets):
    """分析指定索引"""
    start = offsets[idx]
    end = offsets[idx + 1] if idx + 1 < len(offsets) else len(data)
    size = end - start
    idx_data = data[start:end]
    
    print(f"\n{'='*60}")
    print(f"索引{idx}: 大小={size}字节")
    
    if idx_data[:4] != b'LMI1':
        print(f"  不是LMI1格式")
        return
    
    tile_count = struct.unpack_from('<H', idx_data, 4)[0]
    print(f"  LMI1 tile集, tile数量={tile_count}")
    
    # 统计tile尺寸
    size_counts = {}
    tile_details = []
    
    for i in range(min(tile_count, 50)):
        offset_addr = 6 + i * 4
        if offset_addr + 4 > len(idx_data):
            break
        
        tile_offset = struct.unpack_from('<I', idx_data, offset_addr)[0]
        if tile_offset + 4 > len(idx_data):
            continue
        
        w = struct.unpack_from('<H', idx_data, tile_offset)[0]
        h = struct.unpack_from('<H', idx_data, tile_offset + 2)[0]
        
        size_key = f"{w}x{h}"
        size_counts[size_key] = size_counts.get(size_key, 0) + 1
        tile_details.append((i, w, h))
    
    print(f"  Tile尺寸统计:")
    for size_str, count in sorted(size_counts.items(), key=lambda x: int(x[0].split('x')[0]) * 1000 + int(x[0].split('x')[1])):
        print(f"    {size_str}: {count}个")
    
    # 检查是否包含窗口边框tile
    has_3x3 = '3x3' in size_counts
    has_16x3 = '16x3' in size_counts
    has_3x16 = '3x16' in size_counts
    has_16x16 = '16x16' in size_counts
    
    if has_3x3 and has_16x3 and has_3x16 and has_16x16:
        print(f"  ★ 是窗口边框tile集!")
        print(f"    3x3角部: {size_counts['3x3']}个")
        print(f"    16x3水平边框: {size_counts['16x3']}个")
        print(f"    3x16垂直边框: {size_counts['3x16']}个")
        print(f"    16x16内容区: {size_counts['16x16']}个")
        
        # 打印前20个tile的详细信息
        print(f"  前20个tile:")
        for idx, w, h in tile_details[:20]:
            print(f"    Tile {idx:2d}: {w}x{h}")

def main():
    fdother_path = Path("game/FDOTHER.DAT")
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return
    
    data = fdother_path.read_bytes()
    resource_count = struct.unpack_from('<I', data, 6)[0]
    
    offsets = []
    for i in range(resource_count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    # 分析可能的窗口边框tile集索引
    for idx in [0, 4, 7, 13, 14]:
        if idx < resource_count:
            analyze_index(data, idx, offsets)

if __name__ == "__main__":
    main()
