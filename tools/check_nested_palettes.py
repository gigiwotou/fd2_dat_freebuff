#!/usr/bin/env python3
"""
深度分析：检查嵌套DAT内部是否存在独立的调色板
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
    """检查数据块是否为调色板（768字节，每3字节为RGB，值在0-63范围内）"""
    if len(data_chunk) != 768:
        return False
    
    # 检查是否所有值都在0-63范围内（因为是6位颜色值）
    for i in range(0, 768, 3):
        r, g, b = data_chunk[i:i+3]
        if r > 63 or g > 63 or b > 63:  # 6位颜色值范围是0-63
            return False
    return True

def analyze_nested_content(nested_idx):
    """分析嵌套DAT的内容"""
    print(f"\\n=== 分析嵌套DAT {nested_idx} ===")
    
    nested_data, _, _ = read_dat_resource(data, 0, nested_idx)
    if not nested_data:
        print(f"无法读取嵌套DAT {nested_idx}")
        return
    
    magic = nested_data[:6]
    num_resources = struct.unpack_from('<I', nested_data, 6)[0]
    print(f"魔数: {magic.decode('ascii', errors='ignore')}")
    print(f"资源数量: {num_resources}")
    
    # 检查所有资源
    palettes_found = []
    for i in range(min(num_resources, 50)):  # 限制检查数量
        resource_data, offset, size = read_nested_dat_resource(nested_data, i)
        if resource_data is None:
            continue
        
        print(f"  索引 {i}: 偏移=0x{offset:04X}, 大小={size} 字节", end="")
        
        # 检查是否为调色板
        is_pal = check_if_palette(resource_data)
        if is_pal:
            palettes_found.append(i)
            print(f", 是调色板! RGB({resource_data[0]:02X},{resource_data[1]:02X},{resource_data[2]:02X})")
        else:
            # 检查是否为tile（有宽度和高度信息）
            if size >= 4:
                w = struct.unpack_from('<H', resource_data, 0)[0]
                h = struct.unpack_from('<H', resource_data, 2)[0]
                if w > 0 and w < 1000 and h > 0 and h < 1000:
                    print(f", 可能是tile ({w}x{h})")
                    # 检查是否有额外的偏移字节
                    if size >= 5:
                        extra_byte = resource_data[4]
                        print(f"    -> 额外字节(offset+4)=0x{extra_byte:02X}", end="")
                        if size >= 6:
                            next_byte = resource_data[5]
                            print(f", next=0x{next_byte:02X}")
                        else:
                            print()
                else:
                    print()
    
    if palettes_found:
        print(f"\\n  在嵌套DAT {nested_idx} 中发现调色板索引: {palettes_found}")
        # 分析这些调色板
        for pal_idx in palettes_found:
            pal_data, _, _ = read_nested_dat_resource(nested_data, pal_idx)
            if pal_data:
                print(f"    调色板 {pal_idx} 样本: RGB({pal_data[0]:02X},{pal_data[1]:02X},{pal_data[2]:02X}) -> ({(pal_data[0]<<2)|(pal_data[0]>>4)},{(pal_data[1]<<2)|(pal_data[1]>>4)},{(pal_data[2]<<2)|(pal_data[2]>>4)})")
    else:
        print(f"\\n  在嵌套DAT {nested_idx} 中未发现标准调色板")

# 分析有问题的嵌套DAT
analyze_nested_content(7)
analyze_nested_content(12)
analyze_nested_content(63)

print("\\n=== 分析完成 ===")
print("如果嵌套DAT内部没有调色板，那么offset+4处的值可能用于其他用途。")