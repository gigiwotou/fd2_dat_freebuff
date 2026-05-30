#!/usr/bin/env python3
"""深入分析索引2的偏移表结构"""

import struct
from pathlib import Path

FDOTHER_PATH = Path("game/FDOTHER.DAT")

def deep_analyze_index2():
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
    
    # 索引2的数据
    idx2_start = offsets[2]
    idx2_end = offsets[3] if len(offsets) > 3 else len(data)
    idx2_data = data[idx2_start:idx2_end]
    idx2_size = len(idx2_data)
    
    print(f"索引2大小: {idx2_size} 字节")
    print(f"如果是纯偏移表: {idx2_size} / 4 = {idx2_size // 4} 个偏移")
    
    # 读取所有4字节值
    all_dwords = []
    for i in range(0, min(312, idx2_size - 3), 4):
        val = struct.unpack_from('<I', idx2_data, i)[0]
        all_dwords.append((i, val))
    
    print(f"\n前312字节的所有dword值:")
    for addr, val in all_dwords:
        print(f"  [{addr:3d}] 0x{val:08X} = {val:5d}")
    
    # 检查是否是嵌套DAT (LLLLLL)
    if idx2_data[:6] == b'LLLLLL':
        print(f"\n魔数: LLLLLL")
        if idx2_size >= 10:
            count = struct.unpack_from('<I', idx2_data, 6)[0]
            print(f"子资源数量: {count}")
            return
    
    # 分析前312字节作为偏移表
    print(f"\n=== 假设前312字节是偏移表 ===")
    first_312_offsets = []
    for i in range(0, 312, 4):
        if i + 4 <= idx2_size:
            off = struct.unpack_from('<I', idx2_data, i)[0]
            first_312_offsets.append(off)
    
    print(f"前78个偏移:")
    for i, off in enumerate(first_312_offsets[:20]):
        print(f"  [{i:2d}] {off:5d} (0x{off:X})")
    
    if len(first_312_offsets) > 20:
        print(f"  ... 共 {len(first_312_offsets)} 个偏移")
    
    # 检查这些偏移是否指向有效数据
    print(f"\n=== 分析偏移表指向的资源 ===")
    valid_count = 0
    for i in range(len(first_312_offsets) - 1):
        start = first_312_offsets[i]
        end = first_312_offsets[i + 1]
        
        if start < idx2_size and end <= idx2_size and end > start:
            res_size = end - start
            res_data = idx2_data[start:end]
            
            # 检查前4字节
            if res_size >= 4:
                w = struct.unpack_from('<H', res_data, 0)[0]
                h = struct.unpack_from('<H', res_data, 2)[0] if res_size >= 4 else 0
                
                if 0 < w <= 640 and 0 < h <= 480:
                    pw = res_data[4] if res_size >= 5 else 0
                    print(f"  资源{i}: 偏移{start}-{end}, 大小{res_size}, TILE {w}x{h}, palette_window={pw}")
                    valid_count += 1
                    if valid_count >= 10:
                        print(f"  ... (只显示前10个)")
                        break
    
    # 如果前312字节不是偏移表，尝试整个数据都是偏移表
    if valid_count == 0:
        print(f"\n=== 尝试将整个数据作为偏移表 ===")
        # 检查前几个值
        first_vals = []
        for i in range(0, min(40, idx2_size - 3), 4):
            val = struct.unpack_from('<I', idx2_data, i)[0]
            first_vals.append(val)
        
        print(f"前10个值:")
        for i, val in enumerate(first_vals[:10]):
            print(f"  [{i}] {val:5d}")
        
        # 如果值是递增的，说明是偏移表
        is_increasing = all(first_vals[i] < first_vals[i+1] for i in range(min(10, len(first_vals)-1)))
        if is_increasing:
            print(f"\n值是递增的，确认是偏移表")
            print(f"总偏移数: {idx2_size // 4}")
            print(f"资源数: {idx2_size // 4 - 1}")
            
            # 分析第一个资源
            if len(first_vals) >= 2:
                start = first_vals[0]
                end = first_vals[1]
                size = end - start
                print(f"\n第一个资源:")
                print(f"  偏移: {start}-{end}")
                print(f"  大小: {size}")
                
                if start + size <= idx2_size:
                    res_data = idx2_data[start:end]
                    if size >= 5:
                        w = struct.unpack_from('<H', res_data, 0)[0]
                        h = struct.unpack_from('<H', res_data, 2)[0]
                        pw = res_data[4]
                        print(f"  如果是TILE: {w}x{h}, palette_window={pw}")

if __name__ == '__main__':
    deep_analyze_index2()
