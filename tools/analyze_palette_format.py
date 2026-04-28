#!/usr/bin/env python3
"""Deep analyze FDSHAP resource 0 (palette) structure"""

import struct
from PIL import Image

with open("game/FDSHAP.DAT", "rb") as f:
    fdshap = f.read()

# FDSHAP structure:
# - Offset 6-9: resource count (274)
# - Offset 10+: resource offset table
# - Resource 0 at offset 148014, size 1200 bytes
# - Resource 1 at offset 149214, size 87915 bytes

# Parse offset table
resource_count = struct.unpack_from("<I", fdshap, 6)[0]
print(f"Resource count: {resource_count}")

offsets = []
for i in range(resource_count):
    pos = 10 + i * 4
    offset = struct.unpack_from("<I", fdshap, pos)[0]
    offsets.append(offset)

# Resource 0: supposed to be palette for terrain set 0
res0_start = offsets[0]
res0_end = offsets[1]
res0_size = res0_end - res0_start
print(f"\nResource 0 (palette?):")
print(f"  Start: {res0_start}, Size: {res0_size}")
print(f"  First 100 bytes: {fdshap[res0_start:res0_start+100].hex()}")

# 1200 bytes / 3 = 400 colors? Or 1200 / 4 = 300 entries with alpha?
# Or maybe it's 256 colors * 4 bytes (with padding)?
# Or maybe it's a different format

# Let's check the byte patterns
print(f"\nByte values analysis:")
print(f"  Bytes divisible by 4: 0, 4, 8...")
print(f"  First 50 bytes as list:")
for i in range(0, 50, 10):
    chunk = list(fdshap[res0_start+i:res0_start+i+10])
    print(f"    {i:3d}: {chunk}")

# Check if it could be 4-byte entries (RGBA or BGRX)
print(f"\nAs 4-byte entries (first 20):")
for i in range(20):
    entry = fdshap[res0_start+i*4:res0_start+(i+1)*4]
    print(f"  Color {i:3d}: {list(entry)} (hex: {entry.hex()})")

# Check Resource 1 (tile images for terrain set 0)
res1_start = offsets[1]
res1_end = offsets[2]
res1_size = res1_end - res1_start
print(f"\n\nResource 1 (tiles for terrain set 0):")
print(f"  Start: {res1_start}, Size: {res1_size}")

# First 4 bytes: tile dimensions
tile_w = struct.unpack_from("<H", fdshap, res1_start)[0]
tile_h = struct.unpack_from("<H", fdshap, res1_start+2)[0]
print(f"  Tile dimensions: {tile_w}x{tile_h}")

# From offset 4: offset table for individual tiles
# Check bytes at offset 4 onwards
print(f"\n  Bytes 4-40 (offset table):")
for i in range(0, 40, 2):
    val = struct.unpack_from("<H", fdshap, res1_start+4+i)[0]
    print(f"    Offset {4+i}: {val}")

# Extract tile offsets
tile_offsets = []
pos = res1_start + 4
max_pos = res1_start + min(res1_size, 2000)
while pos < max_pos - 2:
    val = struct.unpack_from("<H", fdshap, pos)[0]
    if 0 < val < res1_size:
        if not tile_offsets or val > tile_offsets[-1]:
            tile_offsets.append(val)
    pos += 2

print(f"\n  Found {len(tile_offsets)} tile offsets")
print(f"  First 10: {tile_offsets[:10]}")

# Decompress first tile using RLE
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

# Extract and save first 5 tiles as grayscale to check if decompression works
print(f"\n--- Extracting first 5 tiles (grayscale) ---")
for tile_idx in range(min(5, len(tile_offsets))):
    tile_start = res1_start + tile_offsets[tile_idx]
    tile_end = res1_start + (tile_offsets[tile_idx+1] if tile_idx+1 < len(tile_offsets) else res1_size)
    tile_data = fdshap[tile_start:tile_end]
    
    pixels = rle_decompress(tile_data, tile_w, tile_h)
    
    # Save as grayscale to verify decompression
    img = Image.new("L", (tile_w, tile_h))
    img.putdata(pixels)
    img.save(f"output/maps/tile_{tile_idx}_gray.png")
    print(f"  Saved tile {tile_idx} (size={len(tile_data)} bytes)")

# Now let's figure out the palette format
# If Resource 0 is 1200 bytes for 256 colors, it could be:
# - 256 colors * 4 bytes (RGBA with unused byte)
# - Or packed differently

# Let's check if 1200 = 256 * 4 + some header
if res0_size == 1200:
    print(f"\n--- Resource 0 is 1200 bytes ---")
    print(f"1200 / 4 = 300 (maybe 300 colors with 4 bytes each)")
    print(f"1200 - 256*4 = 176 (maybe header + 256 colors)")
    
    # Try interpreting as 4-byte entries starting from offset 0
    print(f"\nInterpreting as 4-byte entries (RGBA):")
    num_entries = res0_size // 4
    print(f"Number of 4-byte entries: {num_entries}")
    
    # Check if there's a header
    first_entry = fdshap[res0_start:res0_start+4]
    print(f"First 4 bytes: {first_entry.hex()} = {list(first_entry)}")
    
    # Check bytes 4-8 (could be count or dimensions)
    bytes_4_8 = struct.unpack_from("<I", fdshap, res0_start+4)[0]
    print(f"Bytes 4-7 as uint32: {bytes_4_8}")
    
    # If first 4 bytes are header, then palette starts at offset 4
    # 1200 - 4 = 1196, 1196 / 3 = 398.67 (not clean)
    # 1200 - 4 = 1196, 1196 / 4 = 299 (close to 300)
