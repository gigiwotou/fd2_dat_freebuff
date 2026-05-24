#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

"""查找包含窗口边框tile的索引（3x3角部、16x3水平边框、3x16垂直边框、16x16内容区）"""

import struct
from pathlib import Path

def main():
    fdother_path = Path("game/FDOTHER.DAT")
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return
    
    data = fdother_path.read_bytes()
    
    # 解析FDOTHER文件头
    magic = data[:6]
    print(f"Magic: {magic}")
    resource_count = struct.unpack_from('<I', data, 6)[0]
    print(f"资源数量: {resource_count}")
    
    # 读取偏移表 (从偏移10开始，每个4字节)
    offsets = []
    for i in range(resource_count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    print(f"\n扫描所有LMI1格式的索引:")
    print(f"{'='*60}")
    
    for i in range(resource_count):
        start = offsets[i]
        end = offsets[i + 1] if i + 1 < resource_count else len(data)
        size = end - start
        
        if size < 6:
            continue
        
        # 检查是否是LMI1格式
        if data[start:start+4] == b'LMI1':
            tile_count = struct.unpack_from('<H', data, start + 4)[0]
            print(f"\n索引 {i:3d}: LMI1 tile集, 大小={size}字节, tile数={tile_count}")
            
            # 统计tile尺寸
            size_counts = {}
            for j in range(min(tile_count, 200)):
                offset_addr = start + 6 + j * 4
                if offset_addr + 4 > end:
                    break
                
                tile_offset = struct.unpack_from('<I', data, offset_addr)[0]
                if start + tile_offset + 4 > end:
                    continue
                
                w, h = struct.unpack_from('<HH', data, start + tile_offset)
                size_key = f"{w}x{h}"
                size_counts[size_key] = size_counts.get(size_key, 0) + 1
            
            # 检查是否包含窗口边框需要的tile
            has_3x3 = '3x3' in size_counts
            has_16x3 = '16x3' in size_counts
            has_3x16 = '3x16' in size_counts
            has_16x16 = '16x16' in size_counts
            
            if has_3x3 and has_16x3 and has_3x16 and has_16x16:
                print(f"  ★ 包含窗口边框tile: 3x3={size_counts.get('3x3',0)}, 16x3={size_counts.get('16x3',0)}, 3x16={size_counts.get('3x16',0)}, 16x16={size_counts.get('16x16',0)}")
            else:
                print(f"  ✗ 不包含完整窗口边框tile")
            
            # 打印尺寸统计
            print(f"  尺寸统计:")
            for size_str, count in sorted(size_counts.items(), key=lambda x: x[0]):
                print(f"    {size_str}: {count}")

if __name__ == "__main__":
    main()
