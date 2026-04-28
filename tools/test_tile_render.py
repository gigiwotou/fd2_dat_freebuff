#!/usr/bin/env python3
"""测试tile渲染 - 根据IDA分析修复"""

import struct
from pathlib import Path
from PIL import Image
import json

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

# 加载地图0数据
layout = json.load(open('output/maps/map_0_layout.json'))
width = layout['width']
height = layout['height']
terrain_ids = layout['terrain_ids']

print(f"地图0: {width}x{height}, terrain_set_id={layout['terrain_set_id']}")

# 加载FDSHAP.DAT
fdshap = Path("game/FDSHAP.DAT").read_bytes()
count = struct.unpack_from('<I', fdshap, 6)[0]

# 获取资源0（调色板）和资源1（tile集）
res0_pos = 4 * 0 + 10
res0_offset = struct.unpack_from('<I', fdshap, res0_pos)[0]
res0_next = struct.unpack_from('<I', fdshap, res0_pos + 4)[0]
res0_size = res0_next - res0_offset

palette_data = fdshap[res0_offset:res0_offset + res0_size]
palette = palette_6bit_to_8bit(palette_data[:768])
print(f"调色板: {len(palette)} 色")

# 获取资源1（tile集）
res1_pos = 4 * 1 + 10
res1_offset = struct.unpack_from('<I', fdshap, res1_pos)[0]
res1_next = struct.unpack_from('<I', fdshap, res1_pos + 4)[0]
res1_size = res1_next - res1_offset

print(f"\n资源1 (tile集): offset={res1_offset}, size={res1_size}")
print(f"前20字节: {fdshap[res1_offset:res1_offset+20].hex()}")

# 尝试解析tile集 - 假设它是一个大图像包含所有tile
# 前4字节可能是总宽高
total_w = struct.unpack_from('<H', fdshap, res1_offset)[0]
total_h = struct.unpack_from('<H', fdshap, res1_offset + 2)[0]
print(f"Tile集头部: w={total_w}, h={total_h}")

if total_w == 24 and total_h == 24:
    print("头部显示是单个24x24 tile")
    # 解压这个tile
    pixels = rle_decompress(fdshap[res1_offset+4:res1_offset+res1_size], 24, 24)
    img = Image.new("P", (24, 24))
    img.putdata(pixels)
    img.putpalette([c for rgb in palette for c in rgb])
    img.save("output/maps/test_single_tile.png")
    print("保存了单个tile到 test_single_tile.png")
else:
    # 尝试作为tile集解压
    print(f"尝试解压tile集 {total_w}x{total_h}")
    pixels = rle_decompress(fdshap[res1_offset+4:res1_offset+res1_size], total_w, total_h)
    
    # 提取24x24 tile
    tile_w, tile_h = 24, 24
    tiles_per_row = total_w // tile_w
    tiles_per_col = total_h // tile_h
    
    print(f"Tile网格: {tiles_per_row}x{tiles_per_col} = {tiles_per_row * tiles_per_col} tiles")
    
    # 提取前10个tile
    for tile_idx in range(min(10, tiles_per_row * tiles_per_col)):
        tile_row = tile_idx // tiles_per_row
        tile_col = tile_idx % tiles_per_row
        
        tile_pixels = []
        for ty in range(tile_h):
            for tx in range(tile_w):
                src_y = tile_row * tile_h + ty
                src_x = tile_col * tile_w + tx
                pixel_idx = src_y * total_w + src_x
                if pixel_idx < len(pixels):
                    tile_pixels.append(pixels[pixel_idx])
                else:
                    tile_pixels.append(0)
        
        if len(tile_pixels) == tile_w * tile_h:
            img = Image.new("P", (tile_w, tile_h))
            img.putdata(tile_pixels)
            img.putpalette([c for rgb in palette for c in rgb])
            img.save(f"output/maps/test_tile_{tile_idx}.png")
