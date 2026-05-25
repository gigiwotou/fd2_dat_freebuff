#!/usr/bin/env python3
"""
详细检查tile_16的资源数据
查看tile_16和tile_17之间的间隙
"""
import struct

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"

with open(dat_path, 'rb') as f:
    data = f.read()

# 读取主索引表
NUM_INDICES = 422
main_offsets = []
for i in range(NUM_INDICES):
    offset = struct.unpack_from('<I', data, 6 + i * 4)[0]
    main_offsets.append(offset)

# 获取索引63
idx63_start = main_offsets[63]
idx63_end = main_offsets[64] if 64 < len(main_offsets) else len(data)
nested_dat = data[idx63_start:idx63_end]

print(f"索引63:")
print(f"  主DAT偏移: 0x{idx63_start:08X} ({idx63_start})")
print(f"  嵌套DAT大小: {len(nested_dat)}")

# 读取嵌套DAT的tile_16
# 根据之前的分析，tile_16在嵌套DAT中的偏移是48331
tile16_offset = 48331
tile17_offset = 49893

print(f"\ntile_16:")
print(f"  嵌套DAT内偏移: {tile16_offset}")
print(f"  tile_17偏移: {tile17_offset}")
print(f"  tile_16可用空间: {tile17_offset - tile16_offset}")

# 查看tile_16的数据
tile16_data = nested_dat[tile16_offset:tile17_offset]
print(f"  tile_16实际数据大小: {len(tile16_data)}")

w = struct.unpack_from('<H', tile16_data, 0)[0]
h = struct.unpack_from('<H', tile16_data, 2)[0]
print(f"  宽度: {w}")
print(f"  高度: {h}")
print(f"  期望像素数: {w * h}")

rle_data = tile16_data[4:]
print(f"  RLE数据大小: {len(rle_data)}")

# 分析tile_16的RLE数据结尾
print(f"\ntile_16 RLE数据最后50字节:")
for i in range(max(0, len(rle_data) - 50), len(rle_data), 16):
    hex_str = ' '.join(f'{b:02X}' for b in rle_data[i:min(i+16, len(rle_data))])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in rle_data[i:min(i+16, len(rle_data))])
    print(f"  {i:4d}: {hex_str}")
    print(f"        {ascii_str}")

# 检查tile_17的前几个字节
tile17_data = nested_dat[tile17_offset:tile17_offset + 20]
print(f"\ntile_17前20字节:")
hex_str = ' '.join(f'{b:02X}' for b in tile17_data)
ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in tile17_data)
print(f"  0: {hex_str}")
print(f"     {ascii_str}")
