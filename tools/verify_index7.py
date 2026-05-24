#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

"""验证索引7的实际数据结构，找出正确的tile集"""

import struct
from pathlib import Path

def main():
    fdother_path = Path("bin/FDOTHER.DAT")
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
    
    # 分析索引7
    idx = 7
    start = offsets[idx]
    end = offsets[idx + 1] if idx + 1 < resource_count else len(data)
    size = end - start
    
    print(f"\n{'='*60}")
    print(f"索引{idx}分析:")
    print(f"  起始位置: {start} (0x{start:X})")
    print(f"  结束位置: {end} (0x{end:X})")
    print(f"  数据大小: {size} 字节")
    
    # 读取索引7数据
    idx7_data = data[start:end]
    
    # 打印前100字节原始数据
    print(f"\n  前100字节:")
    for i in range(0, min(100, len(idx7_data)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in idx7_data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in idx7_data[i:i+16])
        print(f"    {i:4d}: {hex_str:<48s} {ascii_str}")
    
    # 根据文档解析索引7头部
    # [0-1]: 总宽度 (WORD)
    # [2-3]: 总高度 (WORD)
    # [4-5]: tile数量 (WORD)
    # [6+]: tile偏移表 (DWORD数组)
    
    total_width = struct.unpack_from('<H', idx7_data, 0)[0]
    total_height = struct.unpack_from('<H', idx7_data, 2)[0]
    tile_count = struct.unpack_from('<H', idx7_data, 4)[0]
    
    print(f"\n  文档描述的头部:")
    print(f"    总宽度: {total_width}")
    print(f"    总高度: {total_height}")
    print(f"    Tile数量: {tile_count}")
    
    # 检查是否包含LMI1
    if idx7_data[:4] == b'LMI1':
        print(f"\n  [发现] 包含LMI1魔术字节")
        tile_count_lmi = struct.unpack_from('<H', idx7_data, 4)[0]
        print(f"    LMI1 Tile数量: {tile_count_lmi}")
        
        # 读取tile偏移表
        print(f"\n  Tile偏移表:")
        for i in range(min(tile_count_lmi, 30)):
            offset_addr = 6 + i * 4
            if offset_addr + 4 > len(idx7_data):
                break
            tile_offset = struct.unpack_from('<I', idx7_data, offset_addr)[0]
            print(f"    Tile {i:2d}: offset={tile_offset:6d} (0x{tile_offset:05X})")
            
            # 检查tile数据
            if tile_offset < len(idx7_data):
                if tile_offset + 4 <= len(idx7_data):
                    w, h = struct.unpack_from('<HH', idx7_data, tile_offset)
                    print(f"             尺寸: {w}x{h}")
                    
                    # 检查像素数据
                    if tile_offset + 4 + 20 <= len(idx7_data):
                        pixels = idx7_data[tile_offset+4:tile_offset+24]
                        unique_vals = len(set(pixels))
                        print(f"             前20字节唯一值: {unique_vals}")
    
    else:
        print(f"\n  [注意] 不包含LMI1魔术字节")
        
        # 检查是否是另一种格式：直接包含tile数据
        # 偏移表从6开始，每个DWORD是tile在数据块中的偏移
        # 尝试解析tile数量
        possible_tile_counts = [struct.unpack_from('<H', idx7_data, 4)[0],
                               struct.unpack_from('<H', idx7_data, 0)[0],
                               struct.unpack_from('<H', idx7_data, 2)[0]]
        
        for tc in possible_tile_counts:
            if 0 < tc < 1000:
                print(f"\n  尝试tile数量={tc}:")
                for i in range(min(tc, 20)):
                    offset_addr = 6 + i * 4
                    if offset_addr + 4 > len(idx7_data):
                        print(f"    ... 偏移表超出范围")
                        break
                    tile_offset = struct.unpack_from('<I', idx7_data, offset_addr)[0]
                    print(f"    Tile {i:2d}: offset={tile_offset:6d} (0x{tile_offset:05X})")
                    
                    # 检查是否是相对偏移
                    if tile_offset < len(idx7_data) and tile_offset > 0:
                        if tile_offset + 4 <= len(idx7_data):
                            w, h = struct.unpack_from('<HH', idx7_data, tile_offset)
                            if 0 < w <= 320 and 0 < h <= 200:
                                print(f"             尺寸: {w}x{h} (有效)")
                            else:
                                print(f"             尺寸: {w}x{h} (无效)")
    
    # 同时检查索引4
    print(f"\n{'='*60}")
    print(f"索引4分析 (用于对比):")
    idx4_start = offsets[4]
    idx4_end = offsets[5] if 5 < resource_count else len(data)
    idx4_size = idx4_end - idx4_start
    idx4_data = data[idx4_start:idx4_end]
    
    print(f"  数据大小: {idx4_size} 字节")
    print(f"  前4字节: {idx4_data[:4]}")
    
    if idx4_data[:4] == b'LMI1':
        tile_count = struct.unpack_from('<H', idx4_data, 4)[0]
        print(f"  Tile数量: {tile_count}")
        
        # 统计tile尺寸
        sizes = {}
        for i in range(tile_count):
            offset_addr = 6 + i * 4
            if offset_addr + 4 > len(idx4_data):
                break
            tile_offset = struct.unpack_from('<I', idx4_data, offset_addr)[0]
            if tile_offset + 4 <= len(idx4_data):
                w, h = struct.unpack_from('<HH', idx4_data, tile_offset)
                key = f"{w}x{h}"
                sizes[key] = sizes.get(key, 0) + 1
        
        print(f"  Tile尺寸统计:")
        for size_str, count in sorted(sizes.items()):
            print(f"    {size_str}: {count} 个tile")

if __name__ == "__main__":
    main()
