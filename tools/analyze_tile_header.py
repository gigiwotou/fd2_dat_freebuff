#!/usr/bin/env python3
"""Analyze Resource 1 header (first 192 bytes) for palette data"""

import struct
from PIL import Image

with open("game/FDSHAP.DAT", "rb") as f:
    fdshap = f.read()

# Resource 1 starts at offset 149214
res1_start = 149214
res1_size = 87915

print(f"Resource 1: start={res1_start}, size={res1_size}")

# First 4 bytes: tile dimensions
tile_w = struct.unpack_from("<H", fdshap, res1_start)[0]
tile_h = struct.unpack_from("<H", fdshap, res1_start+2)[0]
print(f"Tile dimensions: {tile_w}x{tile_h}")

# Check bytes 4-191 (188 bytes) before first tile at offset 192
header_data = fdshap[res1_start+4:res1_start+192]
print(f"\nHeader bytes 4-191 ({len(header_data)} bytes):")
print(f"Hex: {header_data.hex()}")
print(f"First 50 bytes: {list(header_data[:50])}")

# Check if there's a palette embedded here
# 188 bytes could be ~62 colors (3 bytes each) or 47 colors (4 bytes each)
# Or maybe there's a count field followed by palette

# Check bytes 4-7 as potential count
count_4 = struct.unpack_from("<H", fdshap, res1_start+4)[0]
count_4_32 = struct.unpack_from("<I", fdshap, res1_start+4)[0]
print(f"\nBytes 4-5 (16-bit): {count_4}")
print(f"Bytes 4-7 (32-bit): {count_4_32}")

# Check bytes 8-11
count_8 = struct.unpack_from("<H", fdshap, res1_start+8)[0]
print(f"Bytes 8-9 (16-bit): {count_8}")

# Let's look at the pattern from byte 4 to 191
print(f"\nAnalyzing bytes 4-191:")
for i in range(0, 188, 4):
    chunk = header_data[i:i+4]
    print(f"  Offset {4+i}: {chunk.hex()} = {list(chunk)}")

# Maybe the palette is 256 colors * 3 = 768 bytes somewhere else
# Let's check if there's another pattern

# Check if Resource 0 might be shared across terrain sets
# Resource 0 (1200 bytes) could be a metadata or index table

# Let's look at the actual tile pixel data
def rle_decompress(src: bytes, width: int, height: int):
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

# Get first tile data
tile0_start = res1_start + 192
tile1_start = res1_start + 774
tile0_data = fdshap[tile0_start:tile1_start]
print(f"\nTile 0 data: {len(tile0_data)} bytes")

# Decompress
pixels = rle_decompress(tile0_data, tile_w, tile_h)

# Analyze pixel values
from collections import Counter
pixel_counter = Counter(pixels)
print(f"Unique pixel values: {len(pixel_counter)}")
print(f"Most common 20 pixel values:")
for pixel_val, count in pixel_counter.most_common(20):
    print(f"  Value {pixel_val:3d}: {count} pixels")

# Check the range of pixel values
pixel_vals = list(pixel_counter.keys())
print(f"\nPixel value range: {min(pixel_vals)}-{max(pixel_vals)}")

# If pixel values are 0-255, they're palette indices
# If they're small (0-50), they might be direct RGB components

# Let's check all pixel values across first 5 tiles
all_pixel_vals = set()
for tile_idx in range(5):
    tile_start = res1_start + [192, 774, 1065, 1400, 1800][tile_idx]
    tile_end = res1_start + [774, 1065, 1400, 1800, 2252][tile_idx]
    tile_data = fdshap[tile_start:tile_end]
    tile_pixels = rle_decompress(tile_data, tile_w, tile_h)
    all_pixel_vals.update(tile_pixels)

print(f"\nAcross first 5 tiles:")
print(f"Unique pixel values: {len(all_pixel_vals)}")
print(f"Values: {sorted(all_pixel_vals)}")
print(f"Max pixel value: {max(all_pixel_vals)}")

# If max is around 50-60, it's likely palette indices with a small palette
# If max is 255, it could be 8-bit grayscale or full palette

# Check if palette might be at the start of the tile data itself
# Or maybe palette is stored elsewhere in the DAT file

# Let's look for a palette by searching for repeating RGB patterns
# A palette should have distinct colors, not just 0, 4, 1 patterns
