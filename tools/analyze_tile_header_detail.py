#!/usr/bin/env python3
"""详细分析tile数据头"""
import struct

dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    data = f.read()

count = struct.unpack_from('<I', data, 6)[0]
offsets = []
for i in range(count):
    offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(offset)

res82_start = offsets[82]
res82_end = offsets[83] if 83 < len(offsets) else len(data)
res82 = data[res82_start:res82_end]

# tile 0数据
tile0_offset = struct.unpack_from('<I', res82, 10)[0]
tile1_offset = struct.unpack_from('<I', res82, 14)[0]
tile0_data = res82[tile0_offset:tile0_offset+64]
tile1_data = res82[tile1_offset:tile1_offset+64]

print(f"Tile 0 前64字节:")
for i in range(0, 64, 16):
    hex_str = ' '.join(f'{b:02X}' for b in tile0_data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in tile0_data[i:i+16])
    print(f"  {i:03d} (0x{i:03X}): {hex_str}  {ascii_str}")

print(f"\nTile 1 前64字节:")
for i in range(0, 64, 16):
    hex_str = ' '.join(f'{b:02X}' for b in tile1_data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in tile1_data[i:i+16])
    print(f"  {i:03d} (0x{i:03X}): {hex_str}  {ascii_str}")

# 检查字节值范围
print(f"\nTile 0 字节值统计:")
values = list(tile0_data)
print(f"  最小值: {min(values)} (0x{min(values):02X})")
print(f"  最大值: {max(values)} (0x{max(values):02X})")
print(f"  平均值: {sum(values)/len(values):.1f}")

# 尝试不同的偏移作为宽高头
print(f"\n尝试不同的偏移作为width/height:")
for header_offset in range(0, 20, 2):
    w = struct.unpack_from('<H', tile0_data, header_offset)[0]
    h = struct.unpack_from('<H', tile0_data, header_offset+2)[0]
    print(f"  偏移{header_offset}: w={w}, h={h}, w*h={w*h}")
