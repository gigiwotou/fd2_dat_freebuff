#!/usr/bin/env python3
"""调试tile像素值"""
import struct

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = os.path.join(WORKSPACE, "bin", "FDOTHER.DAT")

with open(dat_path, 'rb') as f:
    data = f.read()

# 读取索引表
NUM_INDICES = 422
offsets = []
for i in range(NUM_INDICES):
    offset = struct.unpack_from('<I', data, 6 + i * 4)[0]
    offsets.append(offset)

# 获取索引34的资源
idx34_start = offsets[34]
idx34_end = offsets[35]
res_data = data[idx34_start:idx34_end]

# 获取第一个tile
tile_offset = struct.unpack_from('<I', res_data, 8)[0]
tile_data = res_data[tile_offset:]

print(f"Tile 0 偏移: {tile_offset}")
print(f"Tile 0 数据前32字节:")
for i in range(0, 32, 16):
    hex_str = ' '.join(f'{b:02X}' for b in tile_data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in tile_data[i:i+16])
    print(f"  {i:03d}: {hex_str}  {ascii_str}")

tile_width = struct.unpack_from('<H', tile_data, 0)[0]
tile_height = struct.unpack_from('<H', tile_data, 2)[0]

print(f"\n宽高: {tile_width}x{tile_height}")

rle_data = tile_data[9:]
print(f"\nRLE数据前64字节:")
for i in range(0, 64, 16):
    if i < len(rle_data):
        hex_str = ' '.join(f'{b:02X}' for b in rle_data[i:i+16])
        print(f"  {i:03d}: {hex_str}")

# 手动解析前几个RLE命令
print(f"\n手动解析RLE命令:")
src_pos = 0
count = 0
while count < 50 and src_pos < len(rle_data):
    value = rle_data[src_pos]
    src_pos += 1
    
    if value & 0x80:
        if value & 0x40:
            count_val = (value & 0x3F) + 1
            print(f"  [{src_pos-1}] 0x{value:02X}: 跳过 {count_val} 字节 (bit7=1,bit6=1)")
            count += count_val
        else:
            count_val = (value & 0x3F) + 1
            next_bytes = rle_data[src_pos:src_pos+count_val]
            print(f"  [{src_pos-1}] 0x{value:02X}: 复制 {count_val} 字节: {' '.join(f'{b:02X}' for b in next_bytes)}")
            src_pos += count_val
            count += count_val
    else:
        if value & 0x40:
            count_val = (value & 0x3F) + 1
            fill = rle_data[src_pos]
            src_pos += 1
            print(f"  [{src_pos-2}] 0x{value:02X}: 隔行填充 {count_val}*2 字节, 值=0x{fill:02X}")
            count += count_val * 2
        else:
            count_val = (value & 0x3F) + 1
            fill = rle_data[src_pos]
            src_pos += 1
            print(f"  [{src_pos-2}] 0x{value:02X}: 填充 {count_val} 字节, 值=0x{fill:02X}")
            count += count_val
