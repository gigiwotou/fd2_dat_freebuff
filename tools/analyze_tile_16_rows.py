#!/usr/bin/env python3
"""
分析tile_16的RLE数据，检查行边界对齐问题
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
rle_data = res16_data[4:]

print(f"tile_16: {w}x{h}")
print(f"RLE数据大小: {len(rle_data)}")
print(f"期望未压缩大小: {w * h}")
print(f"压缩比: {len(rle_data) / (w * h):.2f}")

# 分析RLE数据，按行分组
print(f"\n分析RLE数据的行边界:")
src_pos = 0
src_len = len(rle_data)
row_num = 0
row_pixels = 0

while src_pos < src_len and row_num < h:
    ctrl = rle_data[src_pos]
    src_pos += 1
    count = (ctrl & 0x3F) + 1
    
    if ctrl & 0x80:
        if ctrl & 0x40:
            row_pixels += count
            # print(f"  行{row_num}: 跳过 {count} 像素 (累计 {row_pixels}/{w})")
        else:
            src_pos += count
            row_pixels += count
            # print(f"  行{row_num}: 复制 {count} 像素 (累计 {row_pixels}/{w})")
    else:
        src_pos += 1
        row_pixels += count
        # print(f"  行{row_num}: 填充 {count} 像素 (累计 {row_pixels}/{w})")
    
    if row_pixels >= w:
        row_num += 1
        row_pixels = 0

print(f"  成功解析 {row_num} 行")
print(f"  RLE数据使用 {src_pos}/{len(rle_data)} 字节")
print(f"  剩余RLE数据: {len(rle_data) - src_pos} 字节")
