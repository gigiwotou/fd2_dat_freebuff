#!/usr/bin/env python3
"""Analyze tile data structure in FDSHAP resource 1"""

import struct
from PIL import Image
from collections import Counter

with open("game/FDSHAP.DAT", "rb") as f:
    fdshap = f.read()

# Parse FDSHAP.DAT offset table
resource_count = struct.unpack_from("<I", fdshap, 6)[0]
fdshap_offsets = []
for i in range(resource_count):
    offset = struct.unpack_from("<I", fdshap, 10 + i * 4)[0]
    fdshap_offsets.append(offset)

# Resource 1
res1_start = fdshap_offsets[1]
res1_end = fdshap_offsets[2]
res1_size = res1_end - res1_start

tile_w = struct.unpack_from("<H", fdshap, res1_start)[0]
tile_h = struct.unpack_from("<H", fdshap, res1_start + 2)[0]
first_tile_offset = struct.unpack_from("<H", fdshap, res1_start + 4)[0]

print(f"Resource 1: size={res1_size}")
print(f"Tile dimensions: {tile_w}x{tile_h}")
print(f"First tile data at: {first_tile_offset}")

# Maybe the tile data is NOT using an offset table
# Maybe tiles are stored sequentially after first_tile_offset
# Each tile is RLE compressed, so we need to decompress to know the size

# Let's try to decompress tiles starting from first_tile_offset
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

# Try to decompress sequential tiles
tile_data_start = res1_start + first_tile_offset
remaining_data = fdshap[tile_data_start:tile_data_start + res1_size]

print(f"\nTrying to decompress sequential tiles from offset {first_tile_offset}...")

tiles_found = 0
pos = 0
max_tiles = 200  # Limit to prevent infinite loop

while pos < len(remaining_data) - 10 and tiles_found < max_tiles:
    # Try to decompress a tile
    try:
        # We don't know the compressed size, so try different sizes
        # A 24x24 tile with RLE should be at least 24 bytes (one byte per row minimum)
        # and at most 24*24*2 = 1152 bytes (worst case RLE)
        
        compressed_data = remaining_data[pos:pos+2000]
        pixels = rle_decompress(compressed_data, tile_w, tile_h)
        
        # Check if decompression produced valid data
        unique_pixels = len(set(pixels))
        if unique_pixels > 0:
            tiles_found += 1
            if tiles_found <= 5:
                print(f"  Tile {tiles_found-1}: at pos {pos}, unique pixels={unique_pixels}")
            
            # Move to next tile - we need to find where this tile's data ends
            # This is tricky without knowing the compressed size
            # Let's assume the offset table is correct and use it
            break
        else:
            pos += 1
    except:
        pos += 1

print(f"Found {tiles_found} tiles by sequential decompression")

# Alternative: maybe the offset table IS correct, and there are really 4409 tiles
# But the terrain_id & 0x7F mapping is wrong

# Let's check what the actual tile index mapping should be
# According to IDA sub_4DF4C:
# v2[2] &= 0x1F  -> terrain_id low 5 bits (0-31)
# But we saw terrain IDs up to 286, which would need more bits

# Maybe the mapping is different. Let's check the terrain_id byte structure
print(f"\n\nTerrain ID byte structure analysis:")

# Load map 0 terrain IDs
with open("game/FDFIELD.DAT", "rb") as f:
    fdfield = f.read()

fdfield_offsets = []
pos = 6
while pos + 4 <= len(fdfield):
    offset = struct.unpack_from("<I", fdfield, pos)[0]
    if offset > pos and offset < len(fdfield):
        fdfield_offsets.append(offset)
    else:
        break
    pos += 4

layout_start = fdfield_offsets[0]
w = struct.unpack_from("<H", fdfield, layout_start)[0]
h = struct.unpack_from("<H", fdfield, layout_start + 2)[0]

tile_data = fdfield[layout_start + 4:]
terrain_ids = []
pos = 0
for y in range(h):
    for x in range(w):
        if pos + 4 <= len(tile_data):
            tid = struct.unpack_from("<H", tile_data, pos)[0]
            terrain_ids.append(tid)
            pos += 4

# Check terrain_id high and low bytes
low_bytes = [tid & 0xFF for tid in terrain_ids]
high_bytes = [(tid >> 8) & 0xFF for tid in terrain_ids]

print(f"Low byte range: {min(low_bytes)}-{max(low_bytes)}, unique: {len(set(low_bytes))}")
print(f"High byte range: {min(high_bytes)}-{max(high_bytes)}, unique: {len(set(high_bytes))}")

# If high byte is always small (0-2), maybe it's used for something else
high_counter = Counter(high_bytes)
print(f"High byte distribution:")
for val, count in high_counter.most_common():
    print(f"  0x{val:02X}: {count} times")

# Check if terrain_id can be decomposed:
# Maybe: terrain_id = tile_index + (attribute_bits << N)
# Or: terrain_id = (tile_index & 0x7F) | (flags << 7)
