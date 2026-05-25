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
print(f"  偏移表[6]值: 0x{nested_count:08X}")

# 有效偏移只有6个
valid_offsets = [
    struct.unpack_from('<I', res_data, 10 + i*4)[0]
    for i in range(6)
]
print(f"  有效偏移: {[hex(x) for x in valid_offsets]}")

# 查看每个tile的数据
for tile_idx in range(len(valid_offsets) - 1):
    tile_offset = valid_offsets[tile_idx]
    tile_size = valid_offsets[tile_idx + 1] - tile_offset
    tile_data = res_data[tile_offset:tile_offset + min(tile_size, 128)]
    
    print(f"\n=== Tile {tile_idx} (偏移 0x{tile_offset:X}, 大小 {tile_size}) ===")
    
    # 前128字节
    for i in range(0, min(128, len(tile_data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in tile_data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in tile_data[i:i+16])
        print(f"  {i:03d}: {hex_str}  {ascii_str}")
    
    # 字节范围
    values = list(tile_data)
    print(f"  范围: {min(values)}-0x{min(values):02X} 到 {max(values)}-0x{max(values):02X}")
    
    # 尝试宽高头
    for header_offset in range(0, 12, 2):
        w = struct.unpack_from('<H', tile_data, header_offset)[0]
        h = struct.unpack_from('<H', tile_data, header_offset+2)[0]
        print(f"  头{header_offset}: w={w} (0x{w:04X}), h={h} (0x{h:04X})")
