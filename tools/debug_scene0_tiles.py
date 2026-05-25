#!/usr/bin/env python3
"""详细查看场景0 (索引63) 的tile数据原始字节"""
import struct

dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    data = f.read()

count = struct.unpack_from('<I', data, 6)[0]
offsets = []
for i in range(count):
    offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(offset)

# 场景0 (索引63)
res_start = offsets[63]
res_end = offsets[64] if 64 < len(offsets) else len(data)
res_data = data[res_start:res_end]

print(f"索引63资源:")
print(f"  大小: {len(res_data)} 字节")
print(f"  Magic: {res_data[:6].hex()}")

nested_count = struct.unpack_from('<I', res_data, 6)[0]
print(f"  嵌套资源数: {nested_count}")

# 查看完整偏移表
print(f"\n偏移表 (前20个):")
for i in range(min(20, nested_count)):
    offset = struct.unpack_from('<I', res_data, 10 + i*4)[0]
    print(f"  [{i:2d}] 0x{offset:06X} ({offset:5d})")

# 查看tile 0的完整数据
tile0_offset = struct.unpack_from('<I', res_data, 10)[0]
tile1_offset = struct.unpack_from('<I', res_data, 14)
tile0_size = tile1_offset - tile0_offset if tile1_offset > tile0_offset else 1000

tile0_data = res_data[tile0_offset:tile0_offset+min(tile0_size, 256)]

print(f"\n=== Tile 0 ===")
print(f"  偏移: 0x{tile0_offset:X}")
print(f"  大小: {tile0_size}")
print(f"  前256字节:")

for i in range(0, min(256, len(tile0_data)), 16):
    hex_str = ' '.join(f'{b:02X}' for b in tile0_data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in tile0_data[i:i+16])
    print(f"    {i:03d} (0x{i:03X}): {hex_str}  {ascii_str}")

# 统计字节值范围
values = list(tile0_data)
print(f"\n  字节统计:")
print(f"    最小值: {min(values)} (0x{min(values):02X})")
print(f"    最大值: {max(values)} (0x{max(values):02X})")
print(f"    平均值: {sum(values)/len(values):.1f}")
print(f"    最常见值: {max(set(values), key=values.count)} (出现{values.count(max(set(values), key=values.count))}次)")

# 检查是否有合理的宽高头
print(f"\n  可能的宽高头:")
for header_offset in range(0, 20, 2):
    w = struct.unpack_from('<H', tile0_data, header_offset)[0]
    h = struct.unpack_from('<H', tile0_data, header_offset+2)[0]
    print(f"    偏移{header_offset}: w={w} (0x{w:04X}), h={h} (0x{h:04X})")
