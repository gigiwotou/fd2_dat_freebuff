#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

"""验证索引4的tile数据RLE解压是否正确"""

import struct
from pathlib import Path

def decode_rle(src, src_size, width, height):
    """RLE解压"""
    expected = width * height
    dst = [0] * expected
    pixel_idx = 0
    src_idx = 0
    
    while src_idx < src_size and pixel_idx < expected:
        control = src[src_idx]
        src_idx += 1
        
        if control >= 192:
            count = (control - 192) + 1
            for i in range(count):
                if pixel_idx < expected:
                    dst[pixel_idx] = 0
                    pixel_idx += 1
        elif control >= 128:
            if src_idx < src_size:
                color = src[src_idx]
                src_idx += 1
                count = (control - 128) + 1
                for i in range(count):
                    if pixel_idx < expected:
                        dst[pixel_idx] = color
                        pixel_idx += 1
        elif control >= 64:
            count = (control - 64) + 1
            for i in range(count):
                if src_idx < src_size and pixel_idx < expected:
                    dst[pixel_idx] = src[src_idx]
                    src_idx += 1
                    pixel_idx += 1
        else:
            if src_idx < src_size:
                color = src[src_idx]
                src_idx += 1
                count = control + 1
                for i in range(count):
                    if pixel_idx < expected:
                        dst[pixel_idx] = color
                        pixel_idx += 1
    
    return dst, pixel_idx == expected

def main():
    fdother_path = Path("game/FDOTHER.DAT")
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return
    
    data = fdother_path.read_bytes()
    
    # 解析FDOTHER文件头
    resource_count = struct.unpack_from('<I', data, 6)[0]
    
    # 读取偏移表
    offsets = []
    for i in range(resource_count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    # 分析索引4
    idx = 4
    start = offsets[idx]
    end = offsets[idx + 1] if idx + 1 < resource_count else len(data)
    tileset_data = data[start:end]
    
    print(f"索引{idx} tile集:")
    print(f"  大小: {len(tileset_data)} 字节")
    print(f"  魔术字节: {tileset_data[:4]}")
    tile_count = struct.unpack_from('<H', tileset_data, 4)[0]
    print(f"  Tile数量: {tile_count}")
    
    # 解析前17个tile（窗口边框需要的tile）
    print(f"\n解析前17个tile:")
    for i in range(min(17, tile_count)):
        offset_addr = 6 + i * 4
        tile_offset = struct.unpack_from('<I', tileset_data, offset_addr)[0]
        
        if start + tile_offset + 4 > end:
            continue
        
        w, h = struct.unpack_from('<HH', tileset_data, tile_offset)
        
        # 获取RLE数据
        rle_start = tile_offset + 4
        rle_data = tileset_data[rle_start:]
        rle_size = len(rle_data)
        if i + 1 < tile_count:
            next_offset = struct.unpack_from('<I', tileset_data, 6 + (i + 1) * 4)[0]
            rle_size = next_offset - tile_offset - 4
        
        # 解压
        decoded, success = decode_rle(rle_data, rle_size, w, h)
        
        # 统计唯一颜色值
        if success:
            unique_colors = len(set(decoded))
            non_zero = sum(1 for p in decoded if p != 0)
            print(f"  Tile {i:2d}: {w}x{h}, RLE大小={rle_size}, 解压={'成功' if success else '失败'}, 唯一颜色={unique_colors}, 非零像素={non_zero}/{w*h}")
        else:
            print(f"  Tile {i:2d}: {w}x{h}, RLE大小={rle_size}, 解压失败")

if __name__ == "__main__":
    main()
