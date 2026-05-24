#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

"""详细分析FDOTHER索引7的数据结构"""

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
    
    # 分析索引7
    idx = 7
    start = offsets[idx]
    end = offsets[idx + 1] if idx + 1 < resource_count else len(data)
    size = end - start
    
    print(f"\n{'='*80}")
    print(f"索引{idx}详细分析:")
    print(f"  起始位置: {start} (0x{start:X})")
    print(f"  结束位置: {end} (0x{end:X})")
    print(f"  数据大小: {size} 字节")
    
    # 读取索引7数据
    idx7_data = data[start:end]
    
    # 打印前200字节原始数据（十六进制）
    print(f"\n  前200字节十六进制:")
    for i in range(0, min(200, len(idx7_data)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in idx7_data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in idx7_data[i:i+16])
        print(f"    {i:4d} (0x{i:04X}): {hex_str:<48s} {ascii_str}")
    
    # 尝试解析为LMI1格式
    print(f"\n{'='*80}")
    print(f"尝试解析为LMI1 tile集格式:")
    
    if idx7_data[:4] == b'LMI1':
        print(f"  ✓ 魔术字节: LMI1")
        tile_count = struct.unpack_from('<H', idx7_data, 4)[0]
        print(f"  ✓ Tile数量: {tile_count}")
        
        # 读取tile偏移表
        print(f"\n  Tile偏移表（前20个）:")
        for i in range(min(tile_count, 20)):
            offset_addr = 6 + i * 4
            if offset_addr + 4 > len(idx7_data):
                break
            tile_offset = struct.unpack_from('<I', idx7_data, offset_addr)[0]
            print(f"    Tile {i:2d}: 偏移={tile_offset:6d} (0x{tile_offset:05X})")
            
            # 尝试读取tile头部（宽高）
            if tile_offset < len(idx7_data) and tile_offset + 4 <= len(idx7_data):
                w = struct.unpack_from('<H', idx7_data, tile_offset)[0]
                h = struct.unpack_from('<H', idx7_data, tile_offset + 2)[0]
                print(f"           宽高: {w}x{h}")
    else:
        print(f"  ✗ 魔术字节不是LMI1: {idx7_data[:4]}")
        print(f"  尝试其他解析方式...")
        
        # 检查是否是直接的tile偏移表（无魔术字节）
        # 前2字节可能是tile数量
        possible_tile_count = struct.unpack_from('<H', idx7_data, 0)[0]
        print(f"\n  假设前2字节是tile数量: {possible_tile_count}")
        
        if 0 < possible_tile_count < 1000:
            print(f"  尝试读取tile偏移表:")
            for i in range(min(possible_tile_count, 20)):
                offset_addr = 2 + i * 4
                if offset_addr + 4 > len(idx7_data):
                    break
                tile_offset = struct.unpack_from('<I', idx7_data, offset_addr)[0]
                print(f"    Tile {i:2d}: 偏移={tile_offset:6d} (0x{tile_offset:05X})")
                
                if tile_offset < len(idx7_data) and tile_offset + 4 <= len(idx7_data):
                    w = struct.unpack_from('<H', idx7_data, tile_offset)[0]
                    h = struct.unpack_from('<H', idx7_data, tile_offset + 2)[0]
                    if 0 < w <= 320 and 0 < h <= 200:
                        print(f"           宽高: {w}x{h} (有效)")
                    else:
                        print(f"           宽高: {w}x{h} (无效)")

if __name__ == "__main__":
    main()
