#!/usr/bin/env python3
"""
正确模拟RLE解压缩，分析tile_16的问题
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
res16_data, _, _ = read_dat_resource(idx63_data, 0, 16)

w = struct.unpack_from('<H', res16_data, 0)[0]
h = struct.unpack_from('<H', res16_data, 2)[0]
rle_data = res16_data[4:]

print(f"tile_16: {w}x{h}")
print(f"RLE数据大小: {len(rle_data)}")

# 正确模拟RLE解压缩
print(f"\nRLE解压缩详细分析:")
src_pos = 0
src_len = len(rle_data)
total_pixels = 0
instructions = 0

while src_pos < src_len:
    ctrl = rle_data[src_pos]
    src_pos += 1
    count = (ctrl & 0x3F) + 1
    instructions += 1
    
    if ctrl & 0x80:
        if ctrl & 0x40:
            total_pixels += count
            if instructions <= 5:
                print(f"  [{src_pos-1}] 0x{ctrl:02X}: 跳过 {count} 像素 (累计 {total_pixels})")
        else:
            src_pos += count
            total_pixels += count
            if instructions <= 5:
                print(f"  [{src_pos-count-1}] 0x{ctrl:02X}: 复制 {count} 字节 (累计 {total_pixels})")
    else:
        if src_pos < src_len:
            fill_value = rle_data[src_pos]
            src_pos += 1
            total_pixels += count
            if instructions <= 5:
                print(f"  [{src_pos-2}] 0x{ctrl:02X} 0x{fill_value:02X}: 填充 {count} 像素=0x{fill_value:02X} (累计 {total_pixels})")
    
    if total_pixels > w * h * 2:
        print(f"  警告: 像素数超过预期2倍")
        break

print(f"\n总指令数: {instructions}")
print(f"解压缩像素数: {total_pixels}")
print(f"期望像素数: {w * h}")
