#!/usr/bin/env python3
"""
详细分析tile_16的RLE解压缩问题
查看tile_16资源的完整结构
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
print(f"tile_16:")
print(f"  资源偏移: {res16_offset}")
print(f"  资源大小: {res16_size}")

# 解析头部
w = struct.unpack_from('<H', res16_data, 0)[0]
h = struct.unpack_from('<H', res16_data, 2)[0]
print(f"  宽度: {w}")
print(f"  高度: {h}")
print(f"  期望像素数: {w * h}")

# 查看资源的完整前64字节
print(f"\n资源前64字节:")
for i in range(0, min(64, len(res16_data)), 16):
    hex_str = ' '.join(f'{b:02X}' for b in res16_data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res16_data[i:i+16])
    print(f"  {i:4d}: {hex_str}")
    print(f"        {ascii_str}")

# 分析RLE控制字节
print(f"\nRLE数据前50个控制字节:")
rle_data = res16_data[4:]
for i in range(min(50, len(rle_data))):
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

# 计算RLE解压缩的总像素数
print(f"\nRLE解压缩分析:")
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

print(f"  RLE数据大小: {len(rle_data)}")
print(f"  解压缩像素数: {total_pixels}")
print(f"  期望像素数: {w * h}")
print(f"  比例: {total_pixels / (w * h):.4f}")

# 检查tile_17的头部
res17_data, res17_offset, res17_size = read_dat_resource(idx63_data, 0, 17)
print(f"\ntile_17:")
print(f"  资源偏移: {res17_offset}")
print(f"  资源大小: {res17_size}")
if res17_data and len(res17_data) >= 4:
    w17 = struct.unpack_from('<H', res17_data, 0)[0]
    h17 = struct.unpack_from('<H', res17_data, 2)[0]
    print(f"  宽度: {w17}")
    print(f"  高度: {h17}")
