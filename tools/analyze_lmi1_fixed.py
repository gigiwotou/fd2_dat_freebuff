#!/usr/bin/env python3
"""分析LMI1 Tile的实际结构 - 可能是固定尺寸的tile"""

import struct
from pathlib import Path

FDOTHER_PATH = Path("game/FDOTHER.DAT")

def analyze_lmi1_fixed_tiles():
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
    
    magic = idx3_data[:4]
    tile_count = struct.unpack_from('<H', idx3_data, 4)[0]
    
    print(f"Tile数量: {tile_count}")
    print(f"总大小: {idx3_size} 字节")
    print(f"如果均匀分布: 每个tile {idx3_size // tile_count} 字节")
    
    # 读取偏移表
    tile_offsets = []
    for i in range(tile_count):
        addr = 6 + i * 4
        if addr + 4 <= idx3_size:
            off = struct.unpack_from('<I', idx3_data, addr)[0]
            tile_offsets.append(off)
    
    # 检查偏移之间的间距
    print(f"\n偏移间距:")
    for i in range(len(tile_offsets) - 1):
        gap = tile_offsets[i+1] - tile_offsets[i]
        print(f"  Tile[{i}] -> Tile[{i+1}]: {gap} 字节")
    
    # 尝试理解tile格式 - 可能没有宽高头
    # 每个tile 256字节，可能是16x16 (256像素) 或 32x8 等
    # RLE数据直接在偏移处
    
    print(f"\n假设: tile没有宽高头，RLE数据直接从偏移开始")
    print(f"每个tile {tile_offsets[1] - tile_offsets[0]} 字节")
    
    # 分析第一个tile的RLE数据
    tile0_data = idx3_data[tile_offsets[0]:tile_offsets[1]]
    print(f"\nTile[0] 数据 (前32字节):")
    for i in range(0, min(32, len(tile0_data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in tile0_data[i:i+16])
        print(f"  {i:03d}: {hex_str}")
    
    # 尝试不同的宽高假设
    test_sizes = [(16, 16), (32, 8), (8, 32), (64, 4)]
    for w, h in test_sizes:
        expected_size = w * h
        print(f"\n假设 {w}x{h} = {expected_size} 像素")
        if expected_size <= len(tile0_data):
            # 简单分析RLE控制字节
            first_byte = tile0_data[0]
            bit7 = (first_byte >> 7) & 1
            bit6 = (first_byte >> 6) & 1
            count = (first_byte & 0x3F) + 1
            print(f"  第一个控制字节: 0x{first_byte:02X}")
            print(f"  bit7={bit7}, bit6={bit6}, count={count}")
            if bit7 == 0 and bit6 == 0:
                print(f"  -> FILL操作，填充{count}个像素，值=0x{tile0_data[1]:02X}")

if __name__ == '__main__':
    analyze_lmi1_fixed_tiles()
