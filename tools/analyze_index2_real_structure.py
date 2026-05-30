#!/usr/bin/env python3
"""分析索引2资源的真实结构"""

import sys
from pathlib import Path

FDOTHER_PATH = Path("game/FDOTHER.DAT")

def analyze_index2():
    """分析索引2资源的真实数据结构"""
    
    with open(FDOTHER_PATH, 'rb') as f:
        data = f.read()
    
    # 读取索引表（从偏移6开始，每项4字节）
    offsets = []
    table_offset = 6
    
    while table_offset + 4 <= len(data):
        res_offset = int.from_bytes(data[table_offset:table_offset+4], 'little')
        if res_offset == 0 or res_offset > len(data):
            break
        offsets.append(res_offset)
        table_offset += 4
    
    print(f"总资源数量: {len(offsets)}")
    
    if len(offsets) > 2:
        # 索引2的起始和结束偏移
        idx2_start = offsets[2]
        idx2_end = offsets[3] if len(offsets) > 3 else len(data)
        idx2_size = idx2_end - idx2_start
        
        print(f"\n=== 索引2 ===")
        print(f"起始偏移: {idx2_start} (0x{idx2_start:X})")
        print(f"结束偏移: {idx2_end} (0x{idx2_end:X})")
        print(f"大小: {idx2_size} 字节")
        
        # 读取索引2的数据
        idx2_data = data[idx2_start:idx2_end]
        
        # 分析数据结构
        print(f"\n前32字节（十六进制）:")
        for i in range(0, min(32, len(idx2_data)), 16):
            hex_str = ' '.join(f'{b:02X}' for b in idx2_data[i:i+16])
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in idx2_data[i:i+16])
            print(f"  {i:04X}: {hex_str:<48} {ascii_str}")
        
        # 检查文件头
        print(f"\n文件头分析:")
        if idx2_size >= 6 and idx2_data[:6] == b'LLLLLL':
            print(f"  魔数: LLLLLL (嵌套DAT)")
            if idx2_size >= 10:
                count = int.from_bytes(idx2_data[6:10], 'little')
                print(f"  子资源数量: {count}")
                
                # 分析偏移表
                offset_table_start = 10
                offset_table_size = count * 4
                
                print(f"\n偏移表 (从偏移{offset_table_start}开始，{count}项，共{offset_table_size}字节):")
                
                # 读取所有偏移
                resource_offsets = []
                for i in range(min(count, 20)):  # 只读取前20个
                    addr = offset_table_start + i * 4
                    if addr + 4 <= len(idx2_data):
                        res_off = int.from_bytes(idx2_data[addr:addr+4], 'little')
                        resource_offsets.append(res_off)
                        print(f"  [{i:3d}] 偏移: {res_off:6d} (0x{res_off:X})")
                
                if count > 20:
                    print(f"  ... 还有 {count - 20} 个偏移未显示")
                
                # 分析第一个子资源
                if len(resource_offsets) >= 2:
                    first_res_start = resource_offsets[0]
                    first_res_end = resource_offsets[1]
                    first_res_size = first_res_end - first_res_start
                    
                    print(f"\n第一个子资源:")
                    print(f"  起始: {first_res_start}")
                    print(f"  结束: {first_res_end}")
                    print(f"  大小: {first_res_size} 字节")
                    
                    if first_res_size >= 4:
                        first_data = idx2_data[first_res_start:first_res_end]
                        print(f"  前4字节: {' '.join(f'{b:02X}' for b in first_data[:4])}")
                        
                        # 检查是否是TILE
                        if first_res_size >= 5:
                            w = first_data[0] | (first_data[1] << 8)
                            h = first_data[2] | (first_data[3] << 8)
                            pal_win = first_data[4]
                            print(f"  如果是TILE: {w}x{h}, palette_window={pal_win}")
        
        elif idx2_size >= 768 and idx2_size == 768:
            print(f"  大小=768: 调色板资源")
        
        else:
            # 检查是否是TILE
            if idx2_size >= 5:
                w = idx2_data[0] | (idx2_data[1] << 8)
                h = idx2_data[2] | (idx2_data[3] << 8)
                print(f"  可能是TILE: {w}x{h}")
                print(f"  字节4: 0x{idx2_data[4]:02X} ({idx2_data[4]})")
                
                if idx2_size >= 8 and idx2_data[5] != 0:
                    pal_win_16 = idx2_data[4] | (idx2_data[5] << 8)
                    print(f"  8字节头: palette_window={pal_win_16}")

if __name__ == '__main__':
    analyze_index2()
