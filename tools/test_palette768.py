#!/usr/bin/env python3
"""Test if Resource 0 first 768 bytes is the palette"""

import struct
from PIL import Image

with open("game/FDSHAP.DAT", "rb") as f:
    fdshap = f.read()

# Parse offset table
resource_count = struct.unpack_from("<I", fdshap, 6)[0]
offsets = []
for i in range(resource_count):
    offset = struct.unpack_from("<I", fdshap, 10 + i * 4)[0]
    offsets.append(offset)

# Resource 0: 1200 bytes
res0_start = offsets[0]
res0_end = offsets[1]
res0_size = res0_end - res0_start

print(f"Resource 0: offset={res0_start}, size={res0_size}")

# First 768 bytes as 6-bit palette (256 colors × 3 bytes)
palette_6bit = fdshap[res0_start:res0_start+768]

print(f"\nFirst 10 palette entries (6-bit RGB):")
for i in range(10):
    r = palette_6bit[i*3]
    g = palette_6bit[i*3+1]
    b = palette_6bit[i*3+2]
    print(f"  Color {i}: RGB=({r},{g},{b})")

# Check byte patterns
print(f"\nByte frequency analysis (first 768 bytes):")
from collections import Counter
byte_freq = Counter(palette_6bit)
print(f"Unique values: {len(byte_freq)}")
print(f"Most common:")
for val, count in byte_freq.most_common(20):
    print(f"  Value {val}: {count} times")

# If palette is 6-bit, values should be 0-63
# Convert to 8-bit and save
palette_8bit = []
for i in range(256):
    r6 = palette_6bit[i*3]
    g6 = palette_6bit[i*3+1]
    b6 = palette_6bit[i*3+2]
    r8 = (r6 << 2) | (r6 >> 4)
    g8 = (g6 << 2) | (g6 >> 4)
    b8 = (b6 << 2) | (b6 >> 4)
    palette_8bit.append((r8, g8, b8))

# Save palette visualization
palette_img = Image.new("RGB", (256, 10))
for x in range(256):
    for y in range(10):
        palette_img.putpixel((x, y), palette_8bit[x])
palette_img.save("output/maps/palette_6bit_test.png")
print(f"\nSaved palette_6bit_test.png")

# Now parse Resource 1 tile offset table correctly
res1_start = offsets[1]
res1_end = offsets[2]
res1_size = res1_end - res1_start

tile_w = struct.unpack_from("<H", fdshap, res1_start)[0]
tile_h = struct.unpack_from("<H", fdshap, res1_start + 2)[0]
print(f"\nResource 1: Tile dimensions {tile_w}x{tile_h}")

# Try: offset table is 2-byte entries at byte 4, every other entry is valid
# Pattern: offset, 0, offset, 0, ...
# So valid offsets are at: 4, 8, 12, 16, ... (every 4 bytes)
tile_offsets_4byte = []
pos = res1_start + 4
for i in range(150):
    offset_val = struct.unpack_from("<H", fdshap, pos)[0]
    pos += 4  # skip 4 bytes each time (offset + 2 zero bytes)
    if offset_val > 0 and offset_val < res1_size:
        if not tile_offsets_4byte or offset_val > tile_offsets_4byte[-1]:
            tile_offsets_4byte.append(offset_val)

print(f"4-byte stride: Found {len(tile_offsets_4byte)} tile offsets")
print(f"First 10: {tile_offsets_4byte[:10]}")

# Alternative: read 4-byte entries as (offset, next_offset)
# Entry: [offset_low, offset_high, next_offset_low, next_offset_high]
# But pattern shows: c0 00 00 00 -> offset=192, zero=0
#                    29 04 00 00 -> offset=1065, zero=0

# Actually, let me check if bytes 4-5 are tile count
byte_4_5 = struct.unpack_from("<H", fdshap, res1_start + 4)[0]
print(f"\nBytes 4-5: {byte_4_5}")

# Try: bytes 4-5 is tile count, then offset table starts at byte 6
if byte_4_5 <= 200:
    print(f"  Could be tile count: {byte_4_5}")
    
    tile_offsets_v2 = []
    pos = res1_start + 6
    for i in range(byte_4_5):
        if pos + 2 > res1_start + res1_size:
            break
        offset_val = struct.unpack_from("<H", fdshap, pos)[0]
        tile_offsets_v2.append(offset_val)
        pos += 2
    
    print(f"  Starting at byte 6: Found {len(tile_offsets_v2)} offsets")
    print(f"  First 10: {tile_offsets_v2[:10]}")

# Let me try yet another approach: look at the actual data
print(f"\nBytes 4-200 hex dump:")
hex_data = fdshap[res1_start+4:res1_start+200]
for i in range(0, len(hex_data), 16):
    hex_str = ' '.join(f'{b:02x}' for b in hex_data[i:i+16])
    print(f"  {4+i:04d}: {hex_str}")
