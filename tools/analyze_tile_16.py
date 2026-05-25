#!/usr/bin/env python3
"""
详细分析tile_16的RLE解压缩问题
检查stride是否不等于width
"""
import struct

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"

with open(dat_path, 'rb') as f:
    data = f.read()

def read_dat_resource(file_data, base_offset, index):
    """正确的DAT读取方式"""
    index_offset = base_offset + 4 * index + 6
    offset0 = struct.unpack_from('<I', file_data, index_offset)[0]
    offset1 = struct.unpack_from('<I', file_data, index_offset + 4)[0]
    size = offset1 - offset0
    if size <= 0 or offset0 >= len(file_data):
        return None, 0, 0
    resource_data = file_data[offset0:offset0 + size]
    return resource_data, offset0, size

# 读取索引63
idx63_data, idx63_offset, idx63_size = read_dat_resource(data, 0, 63)

# 读取tile_16
res16_data, res16_offset, res16_size = read_dat_resource(idx63_data, 0, 16)
print(f"tile_16:")
print(f"  资源偏移: {res16_offset}")
print(f"  资源大小: {res16_size}")

if res16_data and len(res16_data) >= 4:
    w = struct.unpack_from('<H', res16_data, 0)[0]
    h = struct.unpack_from('<H', res16_data, 2)[0]
    print(f"  宽度: {w}")
    print(f"  高度: {h}")
    print(f"  期望像素数: {w * h}")
    
    rle_data = res16_data[4:]
    rle_size = len(rle_data)
    print(f"  RLE数据大小: {rle_size}")
    
    # 计算期望的RLE数据大小（如果是未压缩的）
    uncompressed_size = w * h
    print(f"  未压缩数据大小: {uncompressed_size}")
    
    # 分析RLE控制字节
    print(f"\nRLE控制字节分析 (前100字节):")
    for i in range(min(100, len(rle_data))):
        ctrl = rle_data[i]
        bit7 = (ctrl & 0x80) >> 7
        bit6 = (ctrl & 0x40) >> 6
        count = (ctrl & 0x3F) + 1
        if bit7 == 1:
            if bit6 == 1:
                type_str = "跳过"
            else:
                type_str = "复制"
        else:
            type_str = "填充"
        print(f"  [{i}] 0x{ctrl:02X}: {type_str} (count={count})")
    
    # 模拟RLE解压缩，统计输出像素数
    print(f"\n模拟RLE解压缩:")
    src_pos = 0
    src_len = len(rle_data)
    total_pixels = 0
    
    while src_pos < src_len:
        ctrl = rle_data[src_pos]
        src_pos += 1
        count = (ctrl & 0x3F) + 1
        
        if ctrl & 0x80:
            if ctrl & 0x40:
                total_pixels += count
            else:
                src_pos += count
                total_pixels += count
        else:
            src_pos += 1
            total_pixels += count
        
        if total_pixels > w * h:
            break
    
    print(f"  模拟解压缩像素数: {total_pixels}")
    print(f"  期望像素数: {w * h}")
    print(f"  比例: {total_pixels / (w * h):.2f}")
