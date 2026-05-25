#!/usr/bin/env python3
"""
检查tile_16是否是特殊格式
对比tile_0和tile_16的RLE模式
"""
import struct
from PIL import Image
import os

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

# 分析tile_0
res0_data, _, _ = read_dat_resource(idx63_data, 0, 0)
w0 = struct.unpack_from('<H', res0_data, 0)[0]
h0 = struct.unpack_from('<H', res0_data, 2)[0]
rle0 = res0_data[4:]

print(f"tile_0: {w0}x{h0}")
print(f"RLE数据大小: {len(rle0)}")
print(f"期望像素数: {w0 * h0}")

# 模拟tile_0的RLE解压缩
src_pos = 0
src_len = len(rle0)
total_pixels = 0

while src_pos < src_len:
    ctrl = rle0[src_pos]
    src_pos += 1
    count = (ctrl & 0x3F) + 1
    
    if ctrl & 0x80:
        if ctrl & 0x40:
            total_pixels += count
        else:
            src_pos += count
            total_pixels += count
    else:
        if src_pos < src_len:
            src_pos += 1
            total_pixels += count
    
    if total_pixels > w0 * h0 * 2:
        break

print(f"解压缩像素数: {total_pixels}")
print(f"压缩比: {len(rle0) / (w0 * h0):.3f}")

# 分析tile_16
res16_data, _, _ = read_dat_resource(idx63_data, 0, 16)
w16 = struct.unpack_from('<H', res16_data, 0)[0]
h16 = struct.unpack_from('<H', res16_data, 2)[0]
rle16 = res16_data[4:]

print(f"\ntile_16: {w16}x{h16}")
print(f"RLE数据大小: {len(rle16)}")
print(f"期望像素数: {w16 * h16}")

# 模拟tile_16的RLE解压缩
src_pos = 0
src_len = len(rle16)
total_pixels = 0

while src_pos < src_len:
    ctrl = rle16[src_pos]
    src_pos += 1
    count = (ctrl & 0x3F) + 1
    
    if ctrl & 0x80:
        if ctrl & 0x40:
            total_pixels += count
        else:
            src_pos += count
            total_pixels += count
    else:
        if src_pos < src_len:
            src_pos += 1
            total_pixels += count
    
    if total_pixels > w16 * h16 * 2:
        break

print(f"解压缩像素数: {total_pixels}")
print(f"压缩比: {len(rle16) / (w16 * h16):.3f}")

# 检查tile_16的资源末尾是否有特殊标记
print(f"\ntile_16资源末尾10字节:")
hex_str = ' '.join(f'{b:02X}' for b in res16_data[-10:])
print(f"  {hex_str}")

# 检查tile_16和tile_17之间的间隙
res17_data, res17_offset, res17_size = read_dat_resource(idx63_data, 0, 17)
print(f"\ntile_16结束: {res16_data is not None and len(res16_data)}")
print(f"tile_17偏移: {res17_offset}")
print(f"tile_17大小: {res17_size}")
