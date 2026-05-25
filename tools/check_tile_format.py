#!/usr/bin/env python3
"""直接查看嵌套DAT中的原始数据"""
import struct

dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    data = f.read()

count = struct.unpack_from('<I', data, 6)[0]
offsets = []
for i in range(count):
    offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(offset)

# 检查索引82
res82_start = offsets[82]
res82_end = offsets[83] if 83 < len(offsets) else len(data)
res82 = data[res82_start:res82_end]

print(f"索引82资源: {len(res82)} 字节")

# 偏移表
tile0_offset = struct.unpack_from('<I', res82, 10)[0]
print(f"Tile 0 偏移: 0x{tile0_offset:X}")

tile0_data = res82[tile0_offset:tile0_offset+32]
print(f"Tile 0 前32字节:")
for i in range(0, 32, 16):
    hex_str = ' '.join(f'{b:02X}' for b in tile0_data[i:i+16])
    print(f"  {i:03d}: {hex_str}")

# 字节值范围
values = list(tile0_data)
print(f"字节范围: {min(values)}-{max(values)}")
print(f"平均值: {sum(values)/len(values):.1f}")

# 这些值全部在0x71-0x8C范围 (113-140)
# 这正是8位调色板索引值，说明这些数据直接是RLE像素数据，没有宽高头！

# 检查索引6 (之前有合理的宽高)
res6_start = offsets[6]
res6_end = offsets[7] if 7 < len(offsets) else len(data)
res6 = data[res6_start:res6_end]

print(f"\n索引6资源: {len(res6)} 字节")

tile6_0_offset = struct.unpack_from('<I', res6, 10)[0]
print(f"Tile 0 偏移: 0x{tile6_0_offset:X}")

tile6_0_data = res6[tile6_0_offset:tile6_0_offset+32]
print(f"Tile 0 前32字节:")
for i in range(0, 32, 16):
    hex_str = ' '.join(f'{b:02X}' for b in tile6_0_data[i:i+16])
    print(f"  {i:03d}: {hex_str}")

w = struct.unpack_from('<H', tile6_0_data, 0)[0]
h = struct.unpack_from('<H', tile6_0_data, 2)[0]
print(f"  width={w}, height={h}")
