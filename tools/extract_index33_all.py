#!/usr/bin/env python3
"""提取索引33的所有tile图片"""
import os
import struct
from PIL import Image

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
OUTPUT_DIR = os.path.join(WORKSPACE, "output", "fdother13_tiles_index33_all")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 读取FDOTHER.DAT
fdother_path = os.path.join(WORKSPACE, "bin", "FDOTHER.DAT")
with open(fdother_path, 'rb') as f:
    fdother_data = f.read()

# 解析索引表
index_count = struct.unpack_from('<I', fdother_data, 6)[0]
offsets_start = 10
sizes_start = 10 + index_count * 4

# 获取索引33的资源
idx33_offset = struct.unpack_from('<I', fdother_data, offsets_start + 33 * 4)[0]
idx33_size = struct.unpack_from('<I', fdother_data, sizes_start + 33 * 4)[0]
res_data = fdother_data[idx33_offset:idx33_offset + idx33_size]

print(f"索引33资源大小: {len(res_data)} 字节")

# 解析资源头
tile_count = struct.unpack_from('<H', res_data, 0)[0]
print(f"Tile数量: {tile_count}")

# 偏移表从偏移8开始
offset_table_start = 8
tile_offsets = []
for i in range(tile_count):
    offset = struct.unpack_from('<I', res_data, offset_table_start + i * 4)[0]
    if offset < len(res_data):
        tile_offsets.append(offset)
    else:
        break

print(f"有效偏移数: {len(tile_offsets)}")

# RLE解压缩函数
def decompress_rle(src_data, width, height):
    dst_size = width * height
    dst = bytearray(dst_size)
    
    src_pos = 0
    dst_pos = 0
    
    while dst_pos < dst_size and src_pos < len(src_data):
        byte = src_data[src_pos]
        src_pos += 1
        
        if byte & 0x80:
            if byte & 0x40:
                # 跳过
                count = ((byte & 0x3F) + 1)
                dst_pos += count
            else:
                # 复制
                count = ((byte & 0x3F) + 1)
                for i in range(count):
                    if dst_pos < dst_size and src_pos < len(src_data):
                        dst[dst_pos] = src_data[src_pos]
                        src_pos += 1
                        dst_pos += 1
        else:
            # 填充
            count = byte + 1
            if src_pos < len(src_data):
                fill_value = src_data[src_pos]
                src_pos += 1
                for i in range(count):
                    if dst_pos < dst_size:
                        dst[dst_pos] = fill_value
                        dst_pos += 1
    
    return bytes(dst)

# 提取所有tile
extracted = 0
for tile_idx, tile_offset in enumerate(tile_offsets):
    if tile_idx + 1 < len(tile_offsets):
        tile_size = tile_offsets[tile_idx + 1] - tile_offset
    else:
        tile_size = len(res_data) - tile_offset
    
    tile_data = res_data[tile_offset:tile_offset + tile_size]
    
    if len(tile_data) < 9:
        continue
    
    tile_width = struct.unpack_from('<H', tile_data, 0)[0]
    tile_height = struct.unpack_from('<H', tile_data, 2)[0]
    
    if tile_width == 0 or tile_height == 0 or tile_width > 1024 or tile_height > 1024:
        continue
    
    rle_data = tile_data[9:]
    
    try:
        pixels = decompress_rle(rle_data, tile_width, tile_height)
        
        img = Image.new('P', (tile_width, tile_height))
        img.putdata(pixels)
        
        img_path = os.path.join(OUTPUT_DIR, f"tile_{tile_idx:04d}.png")
        img.save(img_path)
        extracted += 1
        
        if extracted <= 5 or extracted % 10 == 0:
            print(f"  Tile {tile_idx}: {tile_width}x{tile_height} -> {img_path}")
            
    except Exception as e:
        print(f"  Tile {tile_idx} 解压缩失败: {e}")

print(f"\n总计提取: {extracted} 个tile")
