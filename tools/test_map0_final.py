#!/usr/bin/env python3
"""正确解析FDSHAP.DAT并生成地图0 - 修复版"""

import struct
from pathlib import Path
from PIL import Image
import json
import os

def rle_decompress(src: bytes, width: int, height: int) -> bytes:
    dst = bytearray(width * height)
    p = 0
    src_end = len(src)
    
    for row in range(height):
        row_dst = row * width
        count = width
        
        while count > 0 and p < src_end:
            value = src[p]
            p += 1
            count_1 = (value & 0x3F) + 1
            bit7 = (value >> 7) & 1
            bit6 = (value >> 6) & 1
            
            if bit7 and bit6:
                row_dst += count_1
                count -= count_1 if count >= count_1 else count
            elif bit7 and not bit6:
                for i in range(count_1):
                    if count > 0 and p < src_end:
                        if row_dst < len(dst):
                            dst[row_dst] = src[p]
                        row_dst += 1
                        p += 1
                        count -= 1
            elif not bit7 and bit6:
                if p < src_end:
                    fill = src[p]
                    p += 1
                    for i in range(count_1):
                        if count >= 2:
                            if row_dst + 1 < len(dst):
                                dst[row_dst + 1] = fill
                            row_dst += 2
                            count -= 2
                        else:
                            if row_dst < len(dst):
                                dst[row_dst] = fill
                            row_dst += 1
                            count -= 1
            else:
                if p < src_end:
                    fill = src[p]
                    p += 1
                    for i in range(count_1):
                        if count > 0:
                            if row_dst < len(dst):
                                dst[row_dst] = fill
                            row_dst += 1
                            count -= 1
    
    return bytes(dst)

def palette_6bit_to_8bit(palette_768: bytes):
    palette = []
    for i in range(256):
        r6 = palette_768[i * 3]
        g6 = palette_768[i * 3 + 1]
        b6 = palette_768[i * 3 + 2]
        r8 = (r6 << 2) | (r6 >> 4)
        g8 = (g6 << 2) | (g6 >> 4)
        b8 = (b6 << 2) | (b6 >> 4)
        palette.append((min(255, max(0, r8)), min(255, max(0, g8)), min(255, max(0, b8))))
    return palette

# 确保输出目录存在
output_dir = Path("output/maps")
output_dir.mkdir(parents=True, exist_ok=True)

# 加载FDSHAP.DAT
fdshap = Path("game/FDSHAP.DAT").read_bytes()

# 解析资源表
resource_count = struct.unpack_from('<I', fdshap, 6)[0]
print(f"FDSHAP.DAT: {resource_count} resources")

# 读取所有资源偏移
resource_offsets = []
for i in range(resource_count):
    pos = 4 * i + 10
    offset = struct.unpack_from('<I', fdshap, pos)[0]
    resource_offsets.append(offset)

# 资源1
res1_start = resource_offsets[1]
res1_end = resource_offsets[2] if 2 < len(resource_offsets) else len(fdshap)
res1_size = res1_end - res1_start

print(f"\n资源1: start={res1_start}, size={res1_size}")

# Tile尺寸
tile_w, tile_h = struct.unpack_from('<HH', fdshap, res1_start)
print(f"Tile尺寸: {tile_w}x{tile_h}")

# 解析tile偏移表（从偏移4开始，每2字节一个偏移）
tile_offsets = []
pos = res1_start + 4
while pos < res1_start + res1_size - 2:
    offset_val = struct.unpack_from('<H', fdshap, pos)[0]
    if 0 < offset_val < res1_size:
        if not tile_offsets or offset_val > tile_offsets[-1]:
            tile_offsets.append(offset_val)
    pos += 2

print(f"找到 {len(tile_offsets)} 个tile")

# 获取调色板（资源0）
res0_start = resource_offsets[0]
res0_end = resource_offsets[1]
res0_size = res0_end - res0_start

palette_data = fdshap[res0_start:res0_start + res0_size]
palette = palette_6bit_to_8bit(palette_data[:768])
print(f"调色板: {len(palette)} 色")

# 解压tile
tile_images = {}
success_count = 0
for i, tile_offset in enumerate(tile_offsets):
    if i + 1 < len(tile_offsets):
        tile_size = tile_offsets[i + 1] - tile_offset
    else:
        tile_size = res1_size - tile_offset
    
    try:
        tile_data_start = res1_start + tile_offset
        tile_data = fdshap[tile_data_start:tile_data_start + min(tile_size, 3000)]
        pixels = rle_decompress(tile_data, tile_w, tile_h)
        
        img = Image.new("P", (tile_w, tile_h))
        img.putdata(pixels)
        img.putpalette([c for rgb in palette for c in rgb])
        tile_images[i] = img
        
        # 保存前5个tile用于测试
        if i < 5:
            tile_path = output_dir / f"tile_{i}.png"
            img.save(str(tile_path))
            print(f"保存 tile_{i}.png - 文件存在: {tile_path.exists()}")
        
        success_count += 1
    except Exception as e:
        print(f"Tile {i} 解压失败: {e}")

print(f"\n成功解压 {success_count}/{len(tile_offsets)} 个tile")

# 加载地图0
layout = json.load(open(output_dir / 'map_0_layout.json'))
width = layout['width']
height = layout['height']
terrain_ids = layout['terrain_ids']

print(f"\n生成地图0: {width}x{height}")

map_img = Image.new("RGB", (width * tile_w, height * tile_h), (0, 0, 0))

rendered = 0
for y in range(height):
    for x in range(width):
        tid = terrain_ids[y][x]
        if tid in tile_images:
            tile_img = tile_images[tid].convert("RGB")
            map_img.paste(tile_img, (x * tile_w, y * tile_h))
            rendered += 1

print(f"渲染了 {rendered}/{width*height} 个tile")

# 保存地图
map_path = output_dir / "map_0_final.png"
map_img.save(str(map_path))
print(f"地图保存到 {map_path}")
print(f"文件存在: {map_path.exists()}")
print(f"文件大小: {map_path.stat().st_size if map_path.exists() else 0} 字节")
