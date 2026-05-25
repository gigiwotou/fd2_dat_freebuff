#!/usr/bin/env python3
"""
详细分析tile_16的资源大小和RLE解压缩
检查是否是stride问题导致RLE数据不足
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
print(f"资源大小: {res16_size}")
print(f"RLE数据大小: {len(rle_data)}")
print(f"期望像素数: {w * h}")

# 分析RLE数据的实际使用量
print(f"\n分析RLE数据使用:")
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
            if src_pos + count <= src_len:
                src_pos += count
                total_pixels += count
            else:
                print(f"  警告: 复制命令超出数据边界 at pos {src_pos - 1}")
                break
    else:
        if src_pos < src_len:
            src_pos += 1
            total_pixels += count

print(f"RLE数据完全使用后产生的像素数: {total_pixels}")
print(f"期望像素数: {w * h}")
print(f"差值: {w * h - total_pixels}")

# 检查tile_0作为参考
res0_data, _, _ = read_dat_resource(idx63_data, 0, 0)
w0 = struct.unpack_from('<H', res0_data, 0)[0]
h0 = struct.unpack_from('<H', res0_data, 2)[0]
rle0 = res0_data[4:]

src_pos = 0
src_len = len(rle0)
total_pixels0 = 0

while src_pos < src_len:
    ctrl = rle0[src_pos]
    src_pos += 1
    count = (ctrl & 0x3F) + 1
    
    if ctrl & 0x80:
        if ctrl & 0x40:
            total_pixels0 += count
        else:
            if src_pos + count <= src_len:
                src_pos += count
                total_pixels0 += count
            else:
                break
    else:
        if src_pos < src_len:
            src_pos += 1
            total_pixels0 += count

print(f"\ntile_0 ({w0}x{h0}):")
print(f"RLE数据大小: {len(rle0)}")
print(f"解压缩像素数: {total_pixels0}")
print(f"期望像素数: {w0 * h0}")
print(f"差值: {w0 * h0 - total_pixels0}")
