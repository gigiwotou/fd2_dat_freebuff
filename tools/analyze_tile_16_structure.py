#!/usr/bin/env python3
"""
分析tile_16的资源结构，检查是否有额外的头部信息
"""
import struct

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"

with open(dat_path, 'rb') as f:
    data = f.read()

def read_dat_resource(file_data, base_offset, index):
    index_offset = base_offset + 4 * index + 6
    offset0 = struct.unpack_from('<I', file_data, index_offset)[0]
    offset1 = struct.unpack_from('<I', file_data, index_offset + 4)[0]
    size = offset1 - offset0
    if size <= 0 or offset0 >= len(file_data):
        return None, 0, 0
    resource_data = file_data[offset0:offset0 + size]
    return resource_data, offset0, size

# 读取索引63
idx63_data, _, _ = read_dat_resource(data, 0, 63)

# 读取tile_16
res16_data, res16_offset, res16_size = read_dat_resource(idx63_data, 0, 16)

w = struct.unpack_from('<H', res16_data, 0)[0]
h = struct.unpack_from('<H', res16_data, 2)[0]

print(f"tile_16: {w}x{h}")
print(f"资源大小: {res16_size}")
print(f"期望像素数: {w * h}")
print(f"资源大小 - 4(头部): {res16_size - 4}")
print(f"资源大小 - 4 - 期望像素数: {res16_size - 4 - w * h}")

# 检查其他tile的资源结构
print(f"\n其他tile资源分析:")
for i in range(10):
    res_data, res_offset, res_size = read_dat_resource(idx63_data, 0, i)
    if res_data and len(res_data) >= 4:
        tw = struct.unpack_from('<H', res_data, 0)[0]
        th = struct.unpack_from('<H', res_data, 2)[0]
        expected_pixels = tw * th
        extra = res_size - 4 - expected_pixels
        print(f"  [{i}] {tw}x{th}: 资源大小 {res_size}, 期望 {expected_pixels}, 差值 {extra}")

# 检查tile_16的RLE数据是否包含行尾填充
print(f"\n检查tile_16的RLE数据行尾填充:")
rle_data = res16_data[4:]

# 按行分析RLE数据
src_pos = 0
src_len = len(rle_data)
row_pixels = 0
row_num = 0

while src_pos < src_len and row_num < h:
    ctrl = rle_data[src_pos]
    src_pos += 1
    count = (ctrl & 0x3F) + 1
    
    if ctrl & 0x80:
        if ctrl & 0x40:
            row_pixels += count
        else:
            src_pos += count
            row_pixels += count
    else:
        src_pos += 1
        row_pixels += count
    
    if row_pixels >= w:
        # 检查是否有剩余像素在当前控制字节中
        overflow = row_pixels - w
        if overflow > 0:
            print(f"  行{row_num}: 超出 {overflow} 像素")
        
        row_num += 1
        row_pixels = overflow  # 继续下一行

print(f"  成功解析 {row_num} 行")
print(f"  RLE数据使用 {src_pos}/{len(rle_data)} 字节")
print(f"  剩余RLE数据: {len(rle_data) - src_pos} 字节")
