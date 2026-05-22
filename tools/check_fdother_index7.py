#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

"""分析FDOTHER.DAT索引7的数据格式，检查是否RLE压缩"""

import struct
from pathlib import Path

def parse_fdother_header(data):
    """解析FDOTHER.DAT文件头"""
    # 前6字节未知，从偏移6开始是资源偏移表
    # 每个资源条目是8字节：[start_offset:4][end_offset:4]
    
    # 读取前6字节
    print(f"FDOTHER.DAT 前6字节: {list(data[:6])}")
    print(f"FDOTHER.DAT 总大小: {len(data)} 字节")
    
    # 读取前几个资源条目来确定数量
    offsets = []
    pos = 6
    while pos + 8 <= len(data):
        start = struct.unpack_from('<I', data, pos)[0]
        end = struct.unpack_from('<I', data, pos + 4)[0]
        
        # 如果start或end超出文件范围，说明到达了文件头末尾
        if start > len(data) or end > len(data):
            break
            
        offsets.append((start, end))
        pos += 8
        
        # 如果start为0，可能是文件头结束
        if start == 0 and end == 0:
            break
    
    print(f"找到 {len(offsets)} 个资源")
    return offsets

def analyze_index7(data, offsets, index=7):
    """分析索引7的数据"""
    if index >= len(offsets):
        print(f"错误: 索引{index}超出范围")
        return
    
    start, end = offsets[index]
    size = end - start
    
    print(f"\n{'='*60}")
    print(f"索引{index}数据分析:")
    print(f"  偏移范围: {start} - {end}")
    print(f"  数据大小: {size} 字节")
    
    # 读取前4字节作为可能的宽度/高度
    if size < 4:
        print(f"  数据太小")
        return
    
    w = struct.unpack_from('<H', data, start)[0]
    h = struct.unpack_from('<H', data, start + 2)[0]
    
    print(f"  前4字节: w={w}, h={h}")
    
    # 检查是否是tile集头部
    # tile集可能有：[total_width:2][total_height:2][tile_count:2] + offset_table
    # 或者：[tile_width:2][tile_height:2] + offset_table (从偏移6开始)
    
    # 尝试解析为tile集
    if size >= 6:
        tile_count_or_val = struct.unpack_from('<H', data, start + 4)[0]
        print(f"  偏移4-5: {tile_count_or_val} (可能是tile数量或其他值)")
    
    # 读取偏移表（从偏移6开始）
    offset_table_start = start + 6
    tile_offsets = []
    
    print(f"\n  从偏移{6}开始读取tile偏移表:")
    pos = offset_table_start
    
    # 读取最多30个tile偏移
    max_tiles = min(30, (size - 6) // 4)
    
    for i in range(max_tiles):
        if pos + 4 > start + size:
            break
        offset = struct.unpack_from('<I', data, pos)[0]
        tile_offsets.append(offset)
        print(f"    Tile {i}: offset={offset} (0x{offset:X})")
        pos += 4
    
    # 分析tile偏移
    valid_offsets = [o for o in tile_offsets if 0 < o < size]
    print(f"\n  有效tile偏移数量: {len(valid_offsets)}")
    
    if valid_offsets:
        # 检查是否递增
        is_sorted = all(valid_offsets[i] < valid_offsets[i+1] for i in range(len(valid_offsets)-1))
        print(f"    偏移是否递增: {is_sorted}")
        
        # 尝试解析前几个tile
        print(f"\n  解析前10个tile:")
        for i in range(min(10, len(valid_offsets))):
            tile_pos = start + valid_offsets[i]
            if tile_pos + 4 > start + size:
                break
            
            tile_w = struct.unpack_from('<H', data, tile_pos)[0]
            tile_h = struct.unpack_from('<H', data, tile_pos + 2)[0]
            
            print(f"    Tile {i}: w={tile_w}, h={tile_h}, 预期像素={tile_w*tile_h}")
            
            # 检查尺寸合理性
            if tile_w > 320 or tile_h > 200 or tile_w == 0 or tile_h == 0:
                print(f"      [警告] 尺寸异常！可能不是直接的宽高字段")
            else:
                # 读取像素数据样本
                pixel_start = tile_pos + 4
                if pixel_start + 20 <= start + size:
                    sample = data[pixel_start:pixel_start+20]
                    print(f"      像素前20字节: {list(sample)}")
                    
                    # 检查是否是RLE格式
                    rle_markers = sum(1 for b in sample if b >= 128)
                    if rle_markers > 10:
                        print(f"      [提示] 可能是RLE压缩数据 (控制字节: {rle_markers}/20)")
                    else:
                        print(f"      [OK] 可能是原始像素数据")
                
                # 计算下一个tile的位置
                if i + 1 < len(valid_offsets):
                    next_tile_pos = start + valid_offsets[i+1]
                    tile_data_size = next_tile_pos - tile_pos
                    print(f"      数据大小: {tile_data_size} 字节")

def check_rle_in_tile_data(data, tile_start, tile_w, tile_h, max_check=100):
    """检查tile数据是否是RLE压缩"""
    print(f"\n  RLE压缩详细检查:")
    
    pixel_start = tile_start + 4  # 跳过宽高字段
    sample_size = min(max_check, len(data) - pixel_start)
    sample = data[pixel_start:pixel_start + sample_size]
    
    # 统计各类控制字节
    skip_count = sum(1 for b in sample if b >= 192)
    literal_count = sum(1 for b in sample if 128 <= b < 192)
    fill_count = sum(1 for b in sample if 64 <= b < 128)
    small_fill = sum(1 for b in sample if b < 64)
    
    print(f"    样本大小: {sample_size} 字节")
    print(f"    字节分布:")
    print(f"      >=192 (跳过): {skip_count} ({skip_count*100//sample_size}%)")
    print(f"      128-191 (字面): {literal_count} ({literal_count*100//sample_size}%)")
    print(f"      64-127 (填充): {fill_count} ({fill_count*100//sample_size}%)")
    print(f"      <64 (小填充): {small_fill} ({small_fill*100//sample_size}%)")
    
    control_ratio = (skip_count + literal_count + fill_count) * 100 // sample_size
    print(f"\n    控制字节占比: {control_ratio}%")
    
    return control_ratio > 50

def main():
    fdother_path = Path("game/FDOTHER.DAT")
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return
    
    data = fdother_path.read_bytes()
    
    # 解析文件头
    offsets = parse_fdother_header(data)
    
    # 分析索引7
    analyze_index7(data, offsets, index=7)
    
    # 同时也检查其他已知使用sub_4E98D的索引作为对比
    print(f"\n{'='*60}")
    print(f"对比检查：索引76 (调色板，已知非RLE):")
    if 76 < len(offsets):
        start, end = offsets[76]
        print(f"  大小: {end - start} 字节")
        print(f"  前20字节: {list(data[start:start+20])}")
    
    print(f"\n{'='*60}")
    print(f"对比检查：索引74 (标题文字，已知使用sub_4E98D):")
    if 74 < len(offsets):
        start, end = offsets[74]
        size = end - start
        print(f"  大小: {size} 字节")
        w = struct.unpack_from('<H', data, start)[0]
        h = struct.unpack_from('<H', data, start + 2)[0]
        print(f"  前4字节: w={w}, h={h}")
        print(f"  RLE检查:")
        is_rle = check_rle_in_tile_data(data, start, w, h)
        print(f"    {'是RLE压缩' if is_rle else '非RLE压缩'}")
    
    print(f"\n{'='*60}")
    print(f"总结:")
    print(f"  根据代码分析:")
    print(f"    1. sub_111BA (0x111BA): 只负责加载数据到内存，不做任何解密或解压")
    print(f"    2. sub_1685C (0x1685C): 从数据中获取tile指针，调用sub_4ED0B")
    print(f"    3. sub_4ED0B (0x4ED0B): 直接qmemcpy复制像素数据到屏幕")
    print(f"  ")
    print(f"  关键点:")
    print(f"    - sub_4ED0B 是直接的内存复制函数，不是RLE解压函数")
    print(f"    - 如果索引7的tile数据是RLE压缩的，游戏必须先调用sub_4E98D解压")
    print(f"    - 但在所有调用sub_111BA(..., 7)的代码中，没有看到调用sub_4E98D")
    print(f"    - 因此，索引7的tile数据应该是未压缩的原始像素数据")

if __name__ == "__main__":
    main()
