#!/usr/bin/env python3
"""
深度分析嵌套DAT内部结构，查找可能的内部调色板
"""
import struct
import os

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"

with open(dat_path, 'rb') as f:
    data = f.read()

def read_dat_resource(file_data, base_offset, index):
    index_offset = base_offset + 4 * index + 6
    if index_offset + 8 > len(file_data):
        return None, 0, 0
    offset0 = struct.unpack_from('<I', file_data, index_offset)[0]
    offset1 = struct.unpack_from('<I', file_data, index_offset + 4)[0]
    size = offset1 - offset0
    if size <= 0 or offset0 >= len(file_data):
        return None, 0, 0
    resource_data = file_data[offset0:offset0 + size]
    return resource_data, offset0, size

def read_nested_dat_resource(nested_data, index):
    """读取嵌套DAT中的资源"""
    if len(nested_data) < 10:
        return None, 0, 0
    
    # 检查魔数
    magic = nested_data[:6]
    if magic != b'LLLLLL':
        return None, 0, 0
    
    num_resources = struct.unpack_from('<I', nested_data, 6)[0]
    if index >= num_resources or index < 0:
        return None, 0, 0
    
    # 计算偏移位置
    offset_pos = 6 + 4 + index * 4  # 魔数(6) + 资源数量(4) + 索引*4
    if offset_pos + 4 > len(nested_data):
        return None, 0, 0
    
    offset = struct.unpack_from('<I', nested_data, offset_pos)[0]
    
    # 计算大小
    if index < num_resources - 1:
        next_offset_pos = offset_pos + 4
        if next_offset_pos + 4 <= len(nested_data):
            next_offset = struct.unpack_from('<I', nested_data, next_offset_pos)[0]
            size = next_offset - offset
        else:
            # 如果无法获取下一个偏移，则读取到文件末尾
            size = len(nested_data) - offset
    else:
        # 最后一个资源到文件结束
        size = len(nested_data) - offset
    
    # 检查偏移是否合理
    if offset >= len(nested_data) or size <= 0 or size > 100000:  # 限制最大大小防止错误
        return None, 0, 0
    
    resource_data = nested_data[offset:offset + size]
    return resource_data, offset, size

def check_if_palette(data_chunk):
    """检查数据块是否为调色板（768字节，每3字节为RGB）"""
    if len(data_chunk) != 768:
        return False
    
    # 检查是否所有值都在0-63范围内（因为是6位颜色值）
    for i in range(0, 768, 3):
        r, g, b = data_chunk[i:i+3]
        if r > 63 or g > 63 or b > 63:  # 6位颜色值范围是0-63
            return False
    return True

def analyze_nested_dat_content(nested_idx, nested_data):
    """分析嵌套DAT的内容，查找调色板和其他资源"""
    print(f"\n=== 分析嵌套DAT {nested_idx} ===")
    print(f"总大小: {len(nested_data)} 字节")
    
    magic = nested_data[:6]
    num_resources = struct.unpack_from('<I', nested_data, 6)[0]
    print(f"魔数: {magic.decode('ascii', errors='ignore')} (0x{' '.join(f'{b:02X}' for b in magic)})")
    print(f"资源数量: {num_resources}")
    
    # 检查每个资源
    for i in range(min(num_resources, 50)):  # 限制检查的数量避免过多输出
        resource_data, offset, size = read_nested_dat_resource(nested_data, i)
        if resource_data is None:
            continue
        
        print(f"  索引 {i}: 偏移=0x{offset:04X}, 大小={size} 字节")
        
        # 检查是否为调色板
        is_pal = check_if_palette(resource_data)
        print(f"    是调色板(6位): {is_pal}", end="")
        
        # 检查前几个字节的模式
        if len(resource_data) >= 8:
            header_info = ' '.join(f'{b:02X}' for b in resource_data[:8])
            print(f", 前8字节: {header_info}")
        else:
            print()
        
        if is_pal:
            print(f"      调色板样本: RGB({resource_data[0]:02X}, {resource_data[1]:02X}, {resource_data[2]:02X})")
    
    # 特别检查可能的调色板索引
    print(f"\n检查可能的调色板资源...")
    for i in range(min(num_resources, 20)):
        resource_data, offset, size = read_nested_dat_resource(nested_data, i)
        if resource_data is None:
            continue
        
        # 尝试不同的大小判断是否为调色板
        if size == 768:  # 标准调色板大小
            print(f"  索引 {i}: 大小正好是768字节，检查是否为调色板...")
            is_pal = check_if_palette(resource_data)
            if is_pal:
                print(f"    -> 确实是调色板！RGB({resource_data[0]}, {resource_data[1]}, {resource_data[2]})")
            else:
                print(f"    -> 不是标准调色板，样本 RGB({resource_data[0]}, {resource_data[1]}, {resource_data[2]})")

# 分析所有嵌套DAT
nested_indices = [7, 12, 63]
for idx in nested_indices:
    nested_data, _, _ = read_dat_resource(data, 0, idx)
    if nested_data:
        analyze_nested_dat_content(idx, nested_data)
    else:
        print(f"无法读取嵌套DAT {idx}")

print("\n=== 分析完成 ===")