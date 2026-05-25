#!/usr/bin/env python3
"""
检查tile_16是否是特殊格式或数据损坏
比较不同tile的压缩比
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

# 分析所有tile的压缩比
print("所有tile资源分析:")
print(f"{'索引':<5} {'尺寸':<12} {'像素数':<8} {'资源大小':<8} {'压缩比':<8}")
print("-" * 50)

for i in range(30):
    res_data, res_offset, res_size = read_dat_resource(idx63_data, 0, i)
    if res_data and len(res_data) >= 4:
        w = struct.unpack_from('<H', res_data, 0)[0]
        h = struct.unpack_from('<H', res_data, 2)[0]
        pixels = w * h
        ratio = res_size / pixels if pixels > 0 else 0
        print(f"{i:<5} {w}x{h:<10} {pixels:<8} {res_size:<8} {ratio:.3f}")

# 检查tile_16前后的资源
print(f"\n检查tile_15,16,17,18:")
for i in range(15, 19):
    res_data, res_offset, res_size = read_dat_resource(idx63_data, 0, i)
    if res_data:
        w = struct.unpack_from('<H', res_data, 0)[0]
        h = struct.unpack_from('<H', res_data, 2)[0]
        print(f"  [{i}] 偏移 {res_offset}, 大小 {res_size}, 尺寸 {w}x{h}")
        print(f"      前20字节: {' '.join(f'{b:02X}' for b in res_data[:min(20, len(res_data))])}")

# 检查tile_16资源末尾
res16_data, _, _ = read_dat_resource(idx63_data, 0, 16)
if res16_data:
    print(f"\ntile_16资源末尾30字节:")
    for i in range(max(0, len(res16_data) - 30), len(res16_data), 16):
        hex_str = ' '.join(f'{b:02X}' for b in res16_data[i:min(i+16, len(res16_data))])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res16_data[i:min(i+16, len(res16_data))])
        print(f"  {i:4d}: {hex_str}")
        print(f"        {ascii_str}")
