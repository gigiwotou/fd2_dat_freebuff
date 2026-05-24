#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

"""分析tile数据是否是RLE压缩"""

import struct
from pathlib import Path

def main():
    fdother_path = Path("game/FDOTHER.DAT")
    data = fdother_path.read_bytes()
    
    resource_count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(resource_count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    idx = 4
    start = offsets[idx]
    end = offsets[idx + 1] if idx + 1 < resource_count else len(data)
    tileset_data = data[start:end]
    tile_count = struct.unpack_from('<H', tileset_data, 4)[0]
    
    # 分析前20个tile的RLE数据
    for i in range(min(20, tile_count)):
        offset_addr = 6 + i * 4
        tile_offset = struct.unpack_from('<I', tileset_data, offset_addr)[0]
        
        if start + tile_offset + 4 > end:
            continue
        
        w, h = struct.unpack_from('<HH', tileset_data, tile_offset)
        
        # 计算RLE数据大小
        rle_start = tile_offset + 4
        if i + 1 < tile_count:
            next_offset = struct.unpack_from('<I', tileset_data, 6 + (i + 1) * 4)[0]
            rle_size = next_offset - tile_offset - 4
        else:
            rle_size = len(tileset_data) - rle_start
        
        pixel_count = w * h
        
        # 检查RLE数据前几个字节
        rle_data = tileset_data[rle_start:rle_start + min(20, rle_size)]
        
        # 判断是否是RLE压缩
        is_rle = rle_size < pixel_count
        status = "RLE压缩" if is_rle else "未压缩"
        
        print(f"Tile {i:2d}: {w:3d}x{h:3d}, RLE大小={rle_size:5d}, 像素数={pixel_count:5d}, {status}")
        print(f"          前20字节: {' '.join(f'{b:02x}' for b in rle_data)}")

if __name__ == "__main__":
    main()
