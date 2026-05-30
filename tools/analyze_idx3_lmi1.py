#!/usr/bin/env python3
"""分析索引3的LMI1结构"""

import struct
from pathlib import Path

FDOTHER_PATH = Path("game/FDOTHER.DAT")

def analyze_lmi1():
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
    
    # 索引3的数据
    idx3_start = offsets[3]
    idx3_end = offsets[4] if len(offsets) > 4 else len(data)
    idx3_data = data[idx3_start:idx3_end]
    idx3_size = len(idx3_data)
    
    print(f"=== 索引3 (LMI1) ===")
    print(f"起始偏移: {idx3_start}")
    print(f"结束偏移: {idx3_end}")
    print(f"大小: {idx3_size} 字节")
    
    # 解析LMI1头部
    if idx3_size < 6:
        print("错误: 数据太小")
        return
    
    magic = idx3_data[:4]
    tile_count = struct.unpack_from('<H', idx3_data, 4)[0]
    
    print(f"魔数: {magic}")
    print(f"Tile数量: {tile_count}")
    
    # 读取偏移表
    print(f"\n偏移表 (从字节6开始):")
    tile_offsets = []
    for i in range(min(tile_count, 10)):
        addr = 6 + i * 4
        if addr + 4 <= idx3_size:
            off = struct.unpack_from('<I', idx3_data, addr)[0]
            tile_offsets.append(off)
            print(f"  Tile[{i}] 偏移: {off} (0x{off:X})")
    
    if tile_count > 10:
        print(f"  ... 共 {tile_count} 个偏移")
    
    # 分析第一个tile
    if len(tile_offsets) >= 1:
        first_tile_off = tile_offsets[0]
        second_tile_off = tile_offsets[1] if len(tile_offsets) > 1 else idx3_size
        
        tile_size = second_tile_off - first_tile_off
        
        print(f"\n=== 第一个Tile ===")
        print(f"偏移: {first_tile_off}")
        print(f"下一个tile偏移: {second_tile_off}")
        print(f"Tile总大小: {tile_size} 字节")
        
        if first_tile_off + 4 <= idx3_size:
            w = struct.unpack_from('<H', idx3_data, first_tile_off)[0]
            h = struct.unpack_from('<H', idx3_data, first_tile_off + 2)[0]
            
            print(f"宽度: {w}")
            print(f"高度: {h}")
            print(f"w*h: {w*h}")
            
            # 检查像素数据
            if first_tile_off + 5 <= idx3_size:
                pixel_data = idx3_data[first_tile_off + 4 : first_tile_off + 20]
                print(f"前16字节像素数据: {' '.join(f'{b:02X}' for b in pixel_data)}")
                
                # RLE数据大小
                rle_size = tile_size - 4  # 减去4字节宽高
                print(f"RLE数据大小: {rle_size} 字节")
                
                # 验证RLE数据
                if rle_size > 0 and first_tile_off + 4 + rle_size <= idx3_size:
                    rle_data = idx3_data[first_tile_off + 4 : first_tile_off + 4 + rle_size]
                    print(f"RLE前16字节: {' '.join(f'{b:02X}' for b in rle_data[:16])}")
                    
                    # 简单的RLE分析
                    non_zero = sum(1 for b in rle_data if b != 0)
                    print(f"RLE数据非零字节: {non_zero}/{rle_size}")

if __name__ == '__main__':
    analyze_lmi1()
