#!/usr/bin/env python3
"""Analyze FDSHAP palette and tile structure correctly"""

import struct
from PIL import Image

with open("game/FDSHAP.DAT", "rb") as f:
    fdshap = f.read()

resource_count = struct.unpack_from("<I", fdshap, 6)[0]
print(f"FDSHAP resource count: {resource_count}")

# Read resource offsets
offsets = []
for i in range(resource_count):
    pos = 10 + i * 4
    offset = struct.unpack_from("<I", fdshap, pos)[0]
    offsets.append(offset)

# Resource 0 is palette for terrain set 0
res0_start = offsets[0]
res0_end = offsets[1]
res0_size = res0_end - res0_start

print(f"\n=== Resource 0 (Palette) ===")
print(f"Start: {res0_start}, Size: {res0_size}")
print(f"First 200 bytes: {fdshap[res0_start:res0_start+200].hex()}")

# Check if 1200 bytes could be:
# - 256 colors * 4 bytes (RGBX) = 1024 + 176 header? No.
# - 300 colors * 4 bytes? 
# - Or maybe it's a different structure

# Let's check the byte pattern more carefully
# Pattern seems to be: 00 00 XX 00 repeating
# This could be little-endian 32-bit values where only byte 2 is non-zero

print(f"\nFirst 50 32-bit values:")
values = []
for i in range(0, min(200, res0_size), 4):
    val = struct.unpack_from("<I", fdshap, res0_start + i)[0]
    values.append(val)
    print(f"  Entry {i//4}: 0x{val:08x} ({val})")

# If these are palette indices or mappings
# Let's check if they correlate with terrain IDs

# Now check Resource 1 structure more carefully
res1_start = offsets[1]
res1_end = offsets[2]
res1_size = res1_end - res1_start

print(f"\n=== Resource 1 (Tiles) ===")
print(f"Start: {res1_start}, Size: {res1_size}")

# First 4 bytes: tile dimensions
tile_w = struct.unpack_from("<H", fdshap, res1_start)[0]
tile_h = struct.unpack_from("<H", fdshap, res1_start + 2)[0]
print(f"Tile dimensions: {tile_w}x{tile_h}")

# Bytes 4 onwards: tile offset table
# Each entry seems to be 6 bytes: [offset_low, offset_high, count_low, count_high, 0, 0]
# The offset is a 16-bit value pointing to the tile data

# Extract tile offset table properly
tile_entries = []
pos = res1_start + 4
while pos < res1_start + 200:  # First 200 bytes should be offset table
    # Each entry is 6 bytes
    if pos + 6 > res1_start + res1_size:
        break
    
    entry = fdshap[pos:pos+6]
    offset_val = struct.unpack_from("<H", fdshap, pos)[0]
    count_val = struct.unpack_from("<H", fdshap, pos + 2)[0]
    zero_val = struct.unpack_from("<H", fdshap, pos + 4)[0]
    
    tile_entries.append({
        "offset": offset_val,
        "count": count_val,
        "zero": zero_val
    })
    
    if zero_val != 0:
        # Not an offset table entry
        break
    
    pos += 6

print(f"\nTile offset table ({len(tile_entries)} entries):")
for i, entry in enumerate(tile_entries[:10]):
    print(f"  Tile {i}: offset={entry['offset']}, count={entry['count']}, zero={entry['zero']}")

# Now let's understand the palette mapping
# The pixel values in tiles are palette indices
# We need to map these indices to actual RGB colors

# Check if Resource 0 contains a lookup table
# Entry at index N tells us what color palette index N maps to

# Let's create a palette from Resource 0
# Assuming each 4-byte entry maps a palette index to something

# Actually, let's re-examine: maybe Resource 0 is NOT a palette but a tile index mapping
# The actual palette might be elsewhere or hardcoded

# Let's check what the pixel values mean by visualizing the first tile
# with different palette assumptions

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
tile0_offset = tile_entries[0]["offset"]
tile1_offset = tile_entries[1]["offset"]
tile0_data = fdshap[res1_start + tile0_offset:res1_start + tile1_offset]

print(f"\nTile 0: offset={tile0_offset}, size={len(tile0_data)}")

# Decompress
pixels = rle_decompress(tile0_data, tile_w, tile_h)

# Test different palette interpretations

# Interpretation 1: Resource 0 entries map palette index -> color index
# Entry[i] tells us what color to use for pixel value i
palette_from_res0 = []
for i in range(min(256, res0_size // 4)):
    val = struct.unpack_from("<I", fdshap, res0_start + i * 4)[0]
    # The actual color might be derived from this value
    # Let's try using it directly as an RGB component
    r = val & 0xFF
    g = (val >> 8) & 0xFF
    b = (val >> 16) & 0xFF
    palette_from_res0.append((r, g, b))

# Save tile with this palette
img1 = Image.new("RGB", (tile_w, tile_h))
for i, pixel in enumerate(pixels):
    x = i % tile_w
    y = i // tile_w
    if pixel < len(palette_from_res0):
        img1.putpixel((x, y), palette_from_res0[pixel])
    else:
        img1.putpixel((x, y), (255, 0, 255))  # Magenta for missing

img1.save("output/maps/tile0_test1.png")
print(f"Saved tile0_test1.png (using Resource 0 as direct RGB)")

# Interpretation 2: Resource 0 is a lookup table where entry[i] is the actual color value
# Each entry could be a single byte representing a grayscale value
palette_gray = []
for i in range(256):
    if i < res0_size:
        val = fdshap[res0_start + i]
        palette_gray.append((val, val, val))
    else:
        palette_gray.append((0, 0, 0))

img2 = Image.new("RGB", (tile_w, tile_h))
for i, pixel in enumerate(pixels):
    x = i % tile_w
    y = i // tile_w
    img2.putpixel((x, y), palette_gray[pixel])

img2.save("output/maps/tile0_test2.png")
print(f"Saved tile0_test2.png (using Resource 0 bytes as grayscale)")

# Interpretation 3: Resource 0 entries are tile index mappings
# entry[terrain_id & 0x7F] = actual tile index in the tile set
tile_mapping = []
for i in range(min(128, res0_size // 4)):
    val = struct.unpack_from("<I", fdshap, res0_start + i * 4)[0]
    tile_mapping.append(val)

print(f"\nFirst 20 tile mapping entries:")
for i in range(20):
    print(f"  Index {i} -> {tile_mapping[i]}")
