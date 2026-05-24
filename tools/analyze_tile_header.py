#!/usr/bin/env python3
"""分析嵌套 DAT 文件的 tile 头数据"""

import struct
import os

def analyze_nested_dat(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    
    magic = data[:6]
    if magic != b'LLLLLL':
        print(f"不是有效的 DAT 文件: {file_path}")
        return
    
    count = struct.unpack_from('<I', data, 6)[0]
    print(f"资源数量: {count}")
    
    # 解析偏移表
    offset_table = []
    for i in range(count):
        offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offset_table.append(offset)
        print(f"  偏移表[{i}]: 0x{offset:X} ({offset})")
    
    # 检查第一个资源的结构
    if count > 0:
        res0_start = offset_table[0]
        print(f"\n=== 资源 0 分析 (起始于 0x{res0_start:X}) ===")
        
        # 检查是否也是 DAT
        if data[res0_start:res0_start+6] == b'LLLLLL':
            print("资源 0 是嵌套 DAT")
            inner_count = struct.unpack_from('<I', data, res0_start + 6)[0]
            print(f"  内部资源数量: {inner_count}")
            
            # 解析内部偏移表
            inner_offsets = []
            for i in range(inner_count):
                offset = struct.unpack_from('<I', data, res0_start + 10 + i * 4)[0]
                inner_offsets.append(offset)
                print(f"    内部偏移表[{i}]: 0x{offset:X} ({offset})")
            
            # 分析 tile 头
            offset_table_end = res0_start + 10 + inner_count * 4
            for i, offset in enumerate(inner_offsets):
                if offset < len(data) and offset >= offset_table_end:
                    print(f"\n  === Tile {i} 头分析 (偏移 0x{offset:X}) ===")
                    tile_header = data[offset:offset+20]
                    print(f"  原始十六进制: {tile_header.hex()}")
                    
                    # 尝试不同的解释
                    if len(tile_header) >= 10:
                        w1 = struct.unpack_from('<H', tile_header, 0)[0]
                        h1 = struct.unpack_from('<H', tile_header, 2)[0]
                        v3 = struct.unpack_from('<I', tile_header, 4)[0]
                        v4 = struct.unpack_from('<H', tile_header, 8)[0]
                        print(f"  [0-1] WORD: 0x{w1:04X} = {w1}")
                        print(f"  [2-3] WORD: 0x{h1:04X} = {h1}")
                        print(f"  [4-7] DWORD: 0x{v3:08X} = {v3}")
                        print(f"  [8-9] WORD: 0x{v4:04X} = {v4}")
                        
                        # 检查从 +9 开始的 2 字节
                        if len(tile_header) >= 11:
                            w2 = struct.unpack_from('<H', tile_header, 9)[0]
                            print(f"  [9-10] WORD: 0x{w2:04X} = {w2}")

if __name__ == '__main__':
    analyze_nested_dat('output/fdother7/scene_0_nested.dat')
