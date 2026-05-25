#!/usr/bin/env python3
"""
分析RLE数据的像素值分布，确认图像内容
"""
import os
import struct
from PIL import Image

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
OUTPUT_DIR = os.path.join(WORKSPACE, "output", "fdother_index34_debug")
os.makedirs(OUTPUT_DIR, exist_ok=True)

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

# 获取tile数量
tile_count = struct.unpack_from('<H', res_data, 0)[0]

# 解析偏移表
offset_table_start = 8
tile_offsets = []
for i in range(tile_count):
    addr = offset_table_start + i * 4
    if addr + 4 > len(res_data):
        break
    offset = struct.unpack_from('<I', res_data, addr)[0]
    if offset < len(res_data):
        tile_offsets.append(offset)

print(f"索引34: {len(tile_offsets)} 个tile")

# RLE解压缩（精确实现）
def decompress_rle_exact(src_data, width, height):
    dst_size = width * height
    dst = bytearray(dst_size)
    
    src_pos = 0
    row = 0
    
    while row < height:
        count = width
        dst_pos = row * width
        
        while count > 0 and src_pos < len(src_data):
            value = src_data[src_pos]
            src_pos += 1
            
            bit7 = (value >> 7) & 1
            bit6 = (value >> 6) & 1
            
            if bit7 == 1:
                if bit6 == 1:
                    # 跳过
                    count_val = (value & 0x3F) + 1
                    dst_pos += count_val
                    count -= count_val
                else:
                    # 复制
                    count_val = (value & 0x3F) + 1
                    for i in range(count_val):
                        if count > 0 and dst_pos < dst_size and src_pos < len(src_data):
                            dst[dst_pos] = src_data[src_pos]
                            src_pos += 1
                            dst_pos += 1
                            count -= 1
            else:
                if bit6 == 1:
                    # 隔行写入
                    count_val = (value & 0x3F) + 1
                    fill_value = src_data[src_pos]
                    src_pos += 1
                    for i in range(count_val):
                        if count >= 2 and dst_pos + 1 < dst_size:
                            dst[dst_pos + 1] = fill_value
                            dst_pos += 2
                            count -= 2
                else:
                    # 填充
                    count_val = (value & 0x3F) + 1
                    fill_value = src_data[src_pos]
                    src_pos += 1
                    for i in range(count_val):
                        if count > 0 and dst_pos < dst_size:
                            dst[dst_pos] = fill_value
                            dst_pos += 1
                            count -= 1
        
        row += 1
    
    return bytes(dst)

# 统计所有tile的像素值分布
all_pixel_values = {}
total_pixels = 0

for tile_idx in range(min(10, len(tile_offsets))):
    tile_offset = tile_offsets[tile_idx]
    
    if tile_idx + 1 < len(tile_offsets):
        tile_size = tile_offsets[tile_idx + 1] - tile_offset
    else:
        tile_size = len(res_data) - tile_offset
    
    tile_data = res_data[tile_offset:tile_offset + tile_size]
    
    if len(tile_data) < 9:
        continue
    
    tile_width = struct.unpack_from('<H', tile_data, 0)[0]
    tile_height = struct.unpack_from('<H', tile_data, 2)[0]
    
    if tile_width == 0 or tile_height == 0:
        continue
    
    rle_data = tile_data[9:]
    
    try:
        pixels = decompress_rle_exact(rle_data, tile_width, tile_height)
        
        # 统计像素值
        for p in pixels:
            all_pixel_values[p] = all_pixel_values.get(p, 0) + 1
            total_pixels += 1
        
        # 保存图像
        img = Image.new('P', (tile_width, tile_height))
        img.putdata(pixels)
        img_path = os.path.join(OUTPUT_DIR, f"tile_{tile_idx:04d}_{tile_width}x{tile_height}.png")
        img.save(img_path)
        
        # 检查像素值范围
        unique_values = len(set(pixels))
        max_value = max(pixels) if pixels else 0
        non_zero_count = sum(1 for p in pixels if p != 0)
        
        print(f"\nTile {tile_idx} ({tile_width}x{tile_height}):")
        print(f"  唯一像素值: {unique_values}")
        print(f"  最大像素值: {max_value} (0x{max_value:02X})")
        print(f"  非零像素: {non_zero_count} / {len(pixels)} ({non_zero_count/len(pixels)*100:.1f}%)")
        
    except Exception as e:
        print(f"Tile {tile_idx} 失败: {e}")

# 总体统计
print(f"\n=== 总体统计 ===")
print(f"总像素数: {total_pixels}")
print(f"唯一像素值: {len(all_pixel_values)}")

sorted_values = sorted(all_pixel_values.items(), key=lambda x: x[1], reverse=True)
print(f"\n最常见的像素值:")
for val, count in sorted_values[:20]:
    print(f"  0x{val:02X} ({val:3d}): {count} 次 ({count/total_pixels*100:.1f}%)")
