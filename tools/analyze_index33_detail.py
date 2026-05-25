#!/usr/bin/env python3
"""详细分析索引33的资源结构"""
import struct

dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    data = f.read()

count = struct.unpack_from('<I', data, 6)[0]
offsets = []
for i in range(count):
    offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(offset)

# 索引33
res_start = offsets[33]
res_end = offsets[34] if 34 < len(offsets) else len(data)
res_data = data[res_start:res_end]

print(f"索引33资源:")
print(f"  大小: {len(res_data)} 字节")
print(f"  前6字节: {res_data[:6].hex()} = {res_data[:6]}")

# 假设格式: [count:2][?:2][offset_table...]
# 或者 [width:2][height:2][offset_table...]

# 查看前256字节
print(f"\n前256字节:")
for i in range(0, 256, 16):
    hex_str = ' '.join(f'{b:02X}' for b in res_data[i:i+16])
    print(f"  {i:03d}: {hex_str}")

# 尝试解析为偏移表
# 假设[0-1]是数量，[2-3]是其他，[4+]是偏移表
val0 = struct.unpack_from('<H', res_data, 0)[0]
val2 = struct.unpack_from('<H', res_data, 2)[0]

print(f"\n解析:")
print(f"  [0-1]: 0x{val0:04X} = {val0}")
print(f"  [2-3]: 0x{val2:04X} = {val2}")

# 假设偏移表从偏移4开始，每个条目4字节
offset_table_start = 4
num_entries = (len(res_data) - offset_table_start) // 4

print(f"\n假设偏移表从偏移{offset_table_start}开始 ({num_entries}个条目):")

# 读取前20个偏移
valid_offsets = []
for i in range(min(20, num_entries)):
    offset = struct.unpack_from('<I', res_data, offset_table_start + i*4)[0]
    if offset < len(res_data):
        valid_offsets.append(offset)
        print(f"  [{i}] 0x{offset:06X} ({offset})")
    else:
        print(f"  [{i}] 0x{offset:08X} (超出范围)")
        break

print(f"\n有效偏移数: {len(valid_offsets)}")

# 检查第一个tile的数据
if valid_offsets:
    tile0_offset = valid_offsets[0]
    tile0_data = res_data[tile0_offset:tile0_offset+64]
    print(f"\nTile 0 (偏移 0x{tile0_offset:X}) 前64字节:")
    for i in range(0, 64, 16):
        hex_str = ' '.join(f'{b:02X}' for b in tile0_data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in tile0_data[i:i+16])
        print(f"  {i:03d}: {hex_str}  {ascii_str}")
    
    # 尝试解析宽高头
    w = struct.unpack_from('<H', tile0_data, 0)[0]
    h = struct.unpack_from('<H', tile0_data, 2)[0]
    print(f"\n  [0-1] width?: {w}")
    print(f"  [2-3] height?: {h}")
    
    # 字节范围
    values = list(tile0_data)
    print(f"  字节范围: {min(values)}-0x{min(values):02X} 到 {max(values)}-0x{max(values):02X}")
