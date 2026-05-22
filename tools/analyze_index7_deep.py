#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

"""深入分析FDOTHER.DAT索引7的tile数据格式"""

import struct
from pathlib import Path

def parse_fdother_offsets(data):
    """解析FDOTHER.DAT文件头"""
    offsets = []
    pos = 6
    while pos + 8 <= len(data):
        start = struct.unpack_from('<I', data, pos)[0]
        end = struct.unpack_from('<I', data, pos + 4)[0]
        if start > len(data) or end > len(data):
            break
        offsets.append((start, end))
        pos += 8
        if start == 0 and end == 0:
            break
    return offsets

def analyze_tile_data_detailed(data, tile_pos, tile_size, tile_idx):
    """详细分析单个tile数据"""
    w = struct.unpack_from('<H', data, tile_pos)[0]
    h = struct.unpack_from('<H', data, tile_pos + 2)[0]
    
    print(f"  Tile {tile_idx}: w={w}, h={h}, 数据大小={tile_size}")
    
    expected_pixels = w * h
    pixel_data_size = tile_size - 4  # 减去宽高字段
    
    print(f"    预期像素数: {expected_pixels}")
    print(f"    实际像素数据大小: {pixel_data_size}")
    
    if pixel_data_size == expected_pixels:
        print(f"    [匹配] 像素数据大小 = 预期像素数，可能是原始数据")
    elif pixel_data_size < expected_pixels:
        print(f"    [压缩] 像素数据 < 预期，可能是RLE压缩")
        compression_ratio = expected_pixels / pixel_data_size if pixel_data_size > 0 else 0
        print(f"    压缩比: {compression_ratio:.2f}:1")
    else:
        print(f"    [异常] 像素数据 > 预期")
    
    # 分析前100字节
    sample_size = min(100, pixel_data_size)
    sample = data[tile_pos + 4:tile_pos + 4 + sample_size]
    
    # 统计字节分布
    skip_count = sum(1 for b in sample if b >= 192)
    literal_count = sum(1 for b in sample if 128 <= b < 192)
    fill_count = sum(1 for b in sample if 64 <= b < 128)
    small_fill = sum(1 for b in sample if b < 64)
    
    print(f"    字节分布 (样本{sample_size}字节):")
    print(f"      >=192 (跳过): {skip_count} ({skip_count*100//sample_size}%)")
    print(f"      128-191 (字面): {literal_count} ({literal_count*100//sample_size}%)")
    print(f"      64-127 (填充): {fill_count} ({fill_count*100//sample_size}%)")
    print(f"      <64 (小填充): {small_fill} ({small_fill*100//sample_size}%)")
    
    control_ratio = (skip_count + literal_count + fill_count) * 100 // sample_size
    print(f"      控制字节占比: {control_ratio}%")
    
    is_rle = control_ratio > 50
    print(f"    判断: {'[RLE压缩]' if is_rle else '[原始数据]'}")
    
    # 显示前20字节
    first_20 = sample[:20] if len(sample) >= 20 else sample
    print(f"    前20字节: {list(first_20)}")
    
    return is_rle, w, h

def main():
    fdother_path = Path("game/FDOTHER.DAT")
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return
    
    data = fdother_path.read_bytes()
    offsets = parse_fdother_offsets(data)
    
    # 分析索引7
    print(f"FDOTHER.DAT 总大小: {len(data)} 字节")
    print(f"找到 {len(offsets)} 个资源")
    
    if 7 >= len(offsets):
        print(f"错误: 索引7不存在")
        return
    
    start, end = offsets[7]
    size = end - start
    
    print(f"\n{'='*60}")
    print(f"索引7数据分析:")
    print(f"  偏移: {start} - {end}")
    print(f"  大小: {size} 字节")
    
    # 读取头部
    header_w = struct.unpack_from('<H', data, start)[0]
    header_h = struct.unpack_from('<H', data, start + 2)[0]
    header_val = struct.unpack_from('<H', data, start + 4)[0]
    
    print(f"  头部: w={header_w}, h={header_h}, val={header_val}")
    
    # 读取tile偏移表
    tile_offsets = []
    pos = start + 6
    while pos + 4 < end:
        offset = struct.unpack_from('<I', data, pos)[0]
        if 0 < offset < size:
            tile_offsets.append(offset)
        else:
            break
        pos += 4
    
    print(f"\n  Tile偏移表: {len(tile_offsets)} 个tile")
    
    # 分析每个tile
    print(f"\n  {'='*60}")
    print(f"  分析前15个tile:")
    print(f"  {'='*60}")
    
    rle_count = 0
    raw_count = 0
    
    for i in range(min(15, len(tile_offsets))):
        tile_pos = start + tile_offsets[i]
        next_offset = tile_offsets[i+1] if i + 1 < len(tile_offsets) else size
        tile_size = next_offset - tile_offsets[i]
        
        is_rle, w, h = analyze_tile_data_detailed(data, tile_pos, tile_size, i)
        
        if is_rle:
            rle_count += 1
        else:
            raw_count += 1
        
        print()
    
    print(f"\n{'='*60}")
    print(f"统计:")
    print(f"  RLE压缩tile: {rle_count}")
    print(f"  原始数据tile: {raw_count}")
    
    # 对比检查索引74 (已知RLE)
    print(f"\n{'='*60}")
    print(f"对比：索引74 (已知使用sub_4E98D):")
    if 74 < len(offsets):
        s, e = offsets[74]
        print(f"  大小: {e - s}")
        analyze_tile_data_detailed(data, s, e - s, 74)
    
    print(f"\n{'='*60}")
    print(f"结论:")
    print(f"  根据代码分析:")
    print(f"  1. sub_111BA: 直接加载数据，不解压")
    print(f"  2. sub_1685C: 从数据中获取tile指针")
    print(f"     公式: tile_ptr = data + *(DWORD*)(data + 4*tile_index + 6)")
    print(f"  3. sub_4ED0B: 直接qmemcpy复制到屏幕")
    print(f"     count = *a2 (宽度)")
    print(f"     v6 = a2[1] (高度)")
    print(f"     src = (char*)(a2 + 2) (跳过宽高字段)")
    print(f"     do { qmemcpy(dst, src, count); src += count; dst += pitch; } while (--v6)")
    print(f"  ")
    print(f"  关键发现:")
    print(f"  - sub_4ED0B是直接的内存复制，不是RLE解压")
    print(f"  - 如果tile是RLE压缩的，游戏应该在使用前调用sub_4E98D解压")
    print(f"  - 但代码中没有看到对索引7调用sub_4E98D")
    print(f"  - 因此索引7的tile数据应该是未压缩的原始像素数据")
    print(f"  ")
    print(f"  但数据分析显示:")
    print(f"  - 部分tile的数据大小 < w*h (表示可能被压缩)")
    print(f"  - 部分tile的字节分布符合RLE特征")
    print(f"  ")
    print(f"  需要进一步验证:")
    print(f"  1. 检查游戏是否在其他地方调用sub_4E98D处理索引7")
    print(f"  2. 或者索引7的数据实际上不是tile集，而是其他格式")

if __name__ == "__main__":
    main()
