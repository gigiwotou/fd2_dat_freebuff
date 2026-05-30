#!/usr/bin/env python3
"""
检查嵌套DAT是否包含调色板数据
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

def check_if_palette(data_chunk):
    """检查数据块是否为调色板（768字节，每3字节为RGB）"""
    if len(data_chunk) != 768:
        return False
    
    # 检查是否所有值都在0-255范围内
    for i in range(0, 768, 3):
        r, g, b = data_chunk[i:i+3]
        if r > 255 or g > 255 or b > 255:
            return False
    return True

def check_nested_dat_structure(nested_data, nested_idx):
    """检查嵌套DAT的结构"""
    print(f"\n嵌套DAT {nested_idx} 结构分析:")
    print(f"  总大小: {len(nested_data)} 字节")
    
    # 检查开头是否有魔数
    magic = nested_data[:6] if len(nested_data) >= 6 else nested_data
    print(f"  魔数 (前6字节): {''.join(f'{b:02X}' for b in magic)} ({magic.decode('ascii', errors='ignore')})")
    
    # 检查是否为嵌套DAT格式
    if magic == b'FFFFFF':
        print("  这是一个嵌套DAT文件")
        num_resources = struct.unpack_from('<I', nested_data, 6)[0]
        print(f"  资源数量: {num_resources}")
        
        # 检查每个资源
        for i in range(num_resources):
            offset_pos = 6 + 4 + i * 4  # 魔数(6) + 资源数量(4) + 索引*i
            if offset_pos + 4 > len(nested_data):
                break
                
            offset = struct.unpack_from('<I', nested_data, offset_pos)[0]
            print(f"    索引 {i}: 偏移 0x{offset:04X}")
            
            # 检查资源大小
            if i < num_resources - 1:
                next_offset = struct.unpack_from('<I', nested_data, offset_pos + 4)[0]
                size = next_offset - offset
            else:
                # 最后一个资源到文件结束
                size = len(nested_data) - offset
                
            print(f"      大小: {size} 字节")
            
            # 检查是否为调色板
            if offset + size <= len(nested_data):
                resource_data = nested_data[offset:offset + size]
                is_pal = check_if_palette(resource_data)
                print(f"      是调色板: {is_pal}")
                
                if is_pal:
                    print(f"      调色板样本: RGB({resource_data[0]}, {resource_data[1]}, {resource_data[2]})")
    else:
        print("  这不是一个标准的嵌套DAT文件")

# 检查嵌套DAT 7, 12, 63
nested_indices = [7, 12, 63]
for idx in nested_indices:
    nested_data, _, _ = read_dat_resource(data, 0, idx)
    if nested_data:
        check_nested_dat_structure(nested_data, idx)
    else:
        print(f"无法读取嵌套DAT {idx}")

# 检查嵌套DAT索引0是否有调色板
print("\n检查嵌套DAT内部索引0是否为调色板:")
for idx in nested_indices:
    nested_data, _, _ = read_dat_resource(data, 0, idx)
    if nested_data:
        # 尝试读取嵌套DAT内的索引0
        magic = nested_data[:6] if len(nested_data) >= 6 else nested_data
        if magic == b'FFFFFF':
            num_resources = struct.unpack_from('<I', nested_data, 6)[0]
            if num_resources > 0:
                offset0_pos = 6 + 4  # 魔数(6) + 资源数量(4)
                offset0 = struct.unpack_from('<I', nested_data, offset0_pos)[0]
                
                # 查找下一个偏移以确定大小
                if num_resources > 1:
                    offset1_pos = offset0_pos + 4
                    offset1 = struct.unpack_from('<I', nested_data, offset1_pos)[0]
                    size = offset1 - offset0
                else:
                    size = len(nested_data) - offset0
                
                if offset0 + size <= len(nested_data):
                    internal_resource = nested_data[offset0:offset0 + size]
                    is_pal = check_if_palette(internal_resource)
                    print(f"  嵌套DAT {idx} 内部索引0: 大小={size}, 是调色板={is_pal}")
                    if is_pal:
                        print(f"    调色板样本: RGB({internal_resource[0]}, {internal_resource[1]}, {internal_resource[2]})")