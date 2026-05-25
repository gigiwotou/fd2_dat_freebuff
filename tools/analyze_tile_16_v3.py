#!/usr/bin/env python3
"""
分析tile_16的RLE解压缩问题
检查tile_16是否是特殊格式
"""
import struct
from PIL import Image
import os

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

# 分析RLE控制字节序列
print(f"\nRLE控制字节序列分析:")
src_pos = 0
src_len = len(rle_data)
instructions = []

while src_pos < src_len:
    ctrl = rle_data[src_pos]
    src_pos += 1
    count = (ctrl & 0x3F) + 1
    
    if ctrl & 0x80:
        if ctrl & 0x40:
            instructions.append(('skip', count, src_pos - 1))
        else:
            instructions.append(('copy', count, src_pos - 1))
            src_pos += count
    else:
        if src_pos < src_len:
            fill_value = rle_data[src_pos]
            src_pos += 1
            instructions.append(('fill', count, src_pos - 2, fill_value))
    
    if len(instructions) > 100:
        break

print(f"总指令数: {len(instructions)}")
print(f"前20条指令:")
for i, instr in enumerate(instructions[:20]):
    if instr[0] == 'fill':
        print(f"  [{i}] 填充 {instr[1]} 像素=0x{instr[3]:02X} (位置 {instr[2]})")
    else:
        print(f"  [{i}] {instr[0]} {instr[1]} (位置 {instr[2]})")

# 检查tile_16资源末尾
print(f"\ntile_16资源末尾20字节:")
for i in range(max(0, len(res16_data) - 20), len(res16_data), 16):
    hex_str = ' '.join(f'{b:02X}' for b in res16_data[i:min(i+16, len(res16_data))])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res16_data[i:min(i+16, len(res16_data))])
    print(f"  {i:4d}: {hex_str}")
    print(f"        {ascii_str}")

# 检查tile_16前后的资源
print(f"\n检查tile_15,16,17:")
for i in range(15, 18):
    res_data, res_offset, res_size = read_dat_resource(idx63_data, 0, i)
    if res_data:
        w_i = struct.unpack_from('<H', res_data, 0)[0]
        h_i = struct.unpack_from('<H', res_data, 2)[0]
        print(f"  [{i}] 偏移 {res_offset}, 大小 {res_size}, 尺寸 {w_i}x{h_i}")
