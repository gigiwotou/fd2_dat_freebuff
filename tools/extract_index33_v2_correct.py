#!/usr/bin/env python3
"""
使用正确的DAT格式读取索引33的资源

DAT文件格式:
- 文件头: 6字节 (LLLLLL)
- 索引表: 从偏移6开始，每个索引4字节（只有偏移）
- 索引n的数据: offsets[n] 到 offsets[n+1]
- 数据大小 = offsets[n+1] - offsets[n]
"""
import os
import struct
from PIL import Image

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
OUTPUT_DIR = os.path.join(WORKSPACE, "output", "fdother_index33_correct")
os.makedirs(OUTPUT_DIR, exist_ok=True)

dat_path = os.path.join(WORKSPACE, "bin", "FDOTHER.DAT")

with open(dat_path, 'rb') as f:
    data = f.read()

print(f"文件大小: {len(data)} 字节")

# 验证magic
magic = data[:6]
if magic != b'LLLLLL':
    print("错误: 无效的DAT文件")
    exit(1)

# 读取所有索引偏移
NUM_INDICES = 422
offsets = []
for i in range(NUM_INDICES):
    offset = struct.unpack_from('<I', data, 6 + i * 4)[0]
    offsets.append(offset)

# 获取索引33的资源
idx33_start = offsets[33]
idx33_end = offsets[34]
idx33_size = idx33_end - idx33_start
res_data = data[idx33_start:idx33_end]

print(f"\n索引33:")
print(f"  起始偏移: 0x{idx33_start:08X} ({idx33_start})")
print(f"  结束偏移: 0x{idx33_end:08X} ({idx33_end})")
print(f"  大小: {idx33_size} 字节")
print(f"  前32字节: {' '.join(f'{b:02X}' for b in res_data[:32])}")

# 解析资源结构
# 根据之前的分析，可能是: [tile_count:2][?:2][offset_table...]
tile_count = struct.unpack_from('<H', res_data, 0)[0]
print(f"\n解析:")
print(f"  [0-1] tile_count?: {tile_count}")

# 偏移表从偏移4或8开始
# 尝试偏移4
offset_table_start = 4
print(f"\n尝试偏移表从偏移{offset_table_start}开始:")

tile_offsets = []
for i in range(tile_count):
    addr = offset_table_start + i * 4
    if addr + 4 > len(res_data):
        break
    offset = struct.unpack_from('<I', res_data, addr)[0]
    if offset < len(res_data):
        tile_offsets.append(offset)
    else:
        break

print(f"  有效偏移数: {len(tile_offsets)}")

# 打印前10个偏移
for i, offset in enumerate(tile_offsets[:10]):
    print(f"  Tile {i}: 偏移 {offset}")
    if offset + 16 <= len(res_data):
        print(f"    数据: {' '.join(f'{b:02X}' for b in res_data[offset:offset+16])}")

# RLE解压缩
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

# 提取每个tile
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
        
        img_path = os.path.join(OUTPUT_DIR, f"tile_{tile_idx:04d}_{tile_width}x{tile_height}.png")
        img.save(img_path)
        extracted += 1
        
        if extracted <= 10:
            print(f"\n  Tile {tile_idx} 提取成功: {tile_width}x{tile_height}")
            
    except Exception as e:
        print(f"  Tile {tile_idx} 解压缩失败: {e}")

print(f"\n总计提取: {extracted} 个tile")
print(f"输出目录: {OUTPUT_DIR}")
