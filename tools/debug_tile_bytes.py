#!/usr/bin/env python3
"""直接查看嵌套DAT中tile数据的原始字节"""
import struct

dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    data = f.read()

# 获取索引82的资源
count = struct.unpack_from('<I', data, 6)[0]
offsets = []
for i in range(count):
    offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(offset)

res82_start = offsets[82]
res82_end = offsets[83] if 83 < len(offsets) else len(data)
res82 = data[res82_start:res82_end]

print(f"索引82资源:")
print(f"  大小: {len(res82)} 字节")
print(f"  Magic: {res82[:6]}")

nested_count = struct.unpack_from('<I', res82, 6)[0]
print(f"  嵌套资源数: {nested_count}")

offset_table_end = 10 + nested_count * 4
print(f"  偏移表结束: 0x{offset_table_end:X}")

# 查看tile 0的原始数据
tile0_offset = struct.unpack_from('<I', res82, 10)[0]
print(f"\nTile 0 偏移: 0x{tile0_offset:X} ({tile0_offset})")

tile0_data = res82[tile0_offset:tile0_offset+32]
print(f"Tile 0 前32字节(十六进制):")
for i in range(0, min(32, len(tile0_data)), 16):
    hex_str = ' '.join(f'{b:02X}' for b in tile0_data[i:i+16])
    print(f"  {i:04X}: {hex_str}")

# 尝试不同的解释
print(f"\n不同的解释:")
print(f"  [0-1] WORD LE: {struct.unpack_from('<H', tile0_data, 0)[0]}")
print(f"  [0-1] WORD BE: {struct.unpack_from('>H', tile0_data, 0)[0]}")
print(f"  [2-3] WORD LE: {struct.unpack_from('<H', tile0_data, 2)[0]}")
print(f"  [2-3] WORD BE: {struct.unpack_from('>H', tile0_data, 2)[0]}")
print(f"  [0-3] DWORD LE: {struct.unpack_from('<I', tile0_data, 0)[0]}")
print(f"  [0-3] DWORD BE: {struct.unpack_from('>I', tile0_data, 0)[0]}")

# 查看tile 1
if nested_count > 1:
    tile1_offset = struct.unpack_from('<I', res82, 14)[0]
    print(f"\nTile 1 偏移: 0x{tile1_offset:X} ({tile1_offset})")
    
    tile1_data = res82[tile1_offset:tile1_offset+32]
    print(f"Tile 1 前32字节(十六进制):")
    for i in range(0, min(32, len(tile1_data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in tile1_data[i:i+16])
        print(f"  {i:04X}: {hex_str}")
