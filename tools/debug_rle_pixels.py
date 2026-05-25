#!/usr/bin/env python3
"""
调试RLE解压缩过程，检查像素值
"""
import struct

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"

with open(dat_path, 'rb') as f:
    data = f.read()

# 读取索引表
NUM_INDICES = 422
offsets = []
for i in range(NUM_INDICES):
    offset = struct.unpack_from('<I', data, 6 + i * 4)[0]
    offsets.append(offset)

# 获取索引34
idx34_start = offsets[34]
idx34_end = offsets[35]
res_data = data[idx34_start:idx34_end]

# 获取第一个tile
tile_offset = struct.unpack_from('<I', res_data, 8)[0]
tile_data = res_data[tile_offset:tile_offset + 100]

print("=== Tile 0 原始数据 ===")
for i in range(0, 100, 16):
    hex_str = ' '.join(f'{b:02X}' for b in tile_data[i:i+16])
    print(f"  {i:03d}: {hex_str}")

tile_width = struct.unpack_from('<H', tile_data, 0)[0]
tile_height = struct.unpack_from('<H', tile_data, 2)[0]
print(f"\n宽高: {tile_width}x{tile_height}")

rle_data = tile_data[9:]
print(f"\n=== RLE数据 ===")
for i in range(0, min(100, len(rle_data)), 16):
    hex_str = ' '.join(f'{b:02X}' for b in rle_data[i:i+16])
    print(f"  {i:03d}: {hex_str}")

# 手动解析前几个RLE命令
print(f"\n=== 手动解析RLE命令 ===")
src_pos = 0
pixel_count = 0

while pixel_count < 30 and src_pos < len(rle_data):
    value = rle_data[src_pos]
    src_pos += 1
    
    bit7 = (value >> 7) & 1
    bit6 = (value >> 6) & 1
    
    if bit7 == 1:
        if bit6 == 1:
            # 跳过
            count = (value & 0x3F) + 1
            print(f"  pos={src_pos-1}: 0x{value:02X} (bit7=1,bit6=1) -> 跳过 {count} 像素")
            pixel_count += count
        else:
            # 复制
            count = (value & 0x3F) + 1
            next_bytes = rle_data[src_pos:src_pos+count]
            hex_vals = ' '.join(f'0x{b:02X}' for b in next_bytes)
            print(f"  pos={src_pos-1}: 0x{value:02X} (bit7=1,bit6=0) -> 复制 {count} 像素: {hex_vals}")
            src_pos += count
            pixel_count += count
    else:
        if bit6 == 1:
            # 隔行
            count = (value & 0x3F) + 1
            fill = rle_data[src_pos]
            src_pos += 1
            print(f"  pos={src_pos-2}: 0x{value:02X} (bit7=0,bit6=1) -> 隔行填充 {count} 组(每组2像素), 值=0x{fill:02X}")
            pixel_count += count * 2
        else:
            # 填充
            count = (value & 0x3F) + 1
            fill = rle_data[src_pos]
            src_pos += 1
            print(f"  pos={src_pos-2}: 0x{value:02X} (bit7=0,bit6=0) -> 填充 {count} 像素, 值=0x{fill:02X}")
            pixel_count += count

print(f"\n总像素数: {pixel_count}")
print(f"期望像素数: {tile_width * tile_height}")

# 检查RLE数据中的非零值
non_zero_count = sum(1 for b in rle_data if b != 0)
print(f"\nRLE数据中非零字节数: {non_zero_count} / {len(rle_data)}")

# 统计像素值分布
print(f"\n=== 像素值分布（从RLE数据中提取的填充值） ===")
pixel_values = {}
src_pos = 0
while src_pos < len(rle_data):
    value = rle_data[src_pos]
    src_pos += 1
    
    bit7 = (value >> 7) & 1
    bit6 = (value >> 6) & 1
    
    if bit7 == 0 and bit6 == 0:
        # 填充
        count = (value & 0x3F) + 1
        fill = rle_data[src_pos]
        src_pos += 1
        pixel_values[fill] = pixel_values.get(fill, 0) + count
    elif bit7 == 1 and bit6 == 0:
        # 复制
        count = (value & 0x3F) + 1
        for i in range(count):
            if src_pos < len(rle_data):
                val = rle_data[src_pos]
                pixel_values[val] = pixel_values.get(val, 0) + 1
                src_pos += 1
    else:
        # 跳过或隔行
        count = (value & 0x3F) + 1
        if bit6 == 1:
            src_pos += 1  # 隔行需要额外读一个字节
        pixel_count += count

# 按像素值排序
sorted_values = sorted(pixel_values.items(), key=lambda x: x[1], reverse=True)
print("前20个最常见的像素值:")
for val, count in sorted_values[:20]:
    print(f"  0x{val:02X} ({val}): {count} 次")
