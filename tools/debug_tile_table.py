#!/usr/bin/env python3
"""Debug tile offset table parsing"""

import struct

with open("game/FDSHAP.DAT", "rb") as f:
    fdshap = f.read()

# Parse offset table
resource_count = struct.unpack_from("<I", fdshap, 6)[0]
offsets = []
for i in range(resource_count):
    offset = struct.unpack_from("<I", fdshap, 10 + i * 4)[0]
    offsets.append(offset)

# Resource 1
res1_start = offsets[1]
res1_size = offsets[2] - offsets[1]

print(f"Resource 1: start={res1_start}, size={res1_size}")

tile_w = struct.unpack_from("<H", fdshap, res1_start)[0]
tile_h = struct.unpack_from("<H", fdshap, res1_start + 2)[0]
tile_count = struct.unpack_from("<H", fdshap, res1_start + 4)[0]
print(f"Tile dimensions: {tile_w}x{tile_h}, count: {tile_count}")

# Check bytes 4-200 hex dump
print(f"\nBytes 4-100 hex dump:")
hex_data = fdshap[res1_start+4:res1_start+100]
for i in range(0, len(hex_data), 16):
    hex_str = ' '.join(f'{b:02x}' for b in hex_data[i:i+16])
    print(f"  {4+i:04d}: {hex_str}")

# Try different entry sizes for offset table
print(f"\n=== Trying 2-byte entries starting at byte 6 ===")
pos = res1_start + 6
for i in range(min(20, tile_count)):
    val = struct.unpack_from("<H", fdshap, pos)[0]
    print(f"  Entry {i} at {pos - res1_start}: {val} (0x{val:04x})")
    pos += 2

# Try 4-byte entries at byte 6
print(f"\n=== Trying 4-byte entries starting at byte 6 ===")
pos = res1_start + 6
for i in range(min(10, tile_count)):
    val = struct.unpack_from("<I", fdshap, pos)[0]
    print(f"  Entry {i} at {pos - res1_start}: {val} (0x{val:08x})")
    pos += 4

# Try 6-byte entries at byte 6
print(f"\n=== Trying 6-byte entries starting at byte 6 ===")
pos = res1_start + 6
for i in range(min(10, tile_count)):
    if pos + 6 > res1_start + res1_size:
        break
    off = struct.unpack_from("<H", fdshap, pos)[0]
    sz = struct.unpack_from("<H", fdshap, pos + 2)[0]
    zero = struct.unpack_from("<H", fdshap, pos + 4)[0]
    print(f"  Entry {i} at {pos - res1_start}: offset={off}, size={sz}, zero={zero}")
    pos += 6

# Maybe the offset table is at a different location?
# Let's search for the pattern: c0 00 06 03 00 00
print(f"\n=== Searching for pattern c0 00 06 03 00 00 ===")
pattern = bytes([0xc0, 0x00, 0x06, 0x03, 0x00, 0x00])
search_start = res1_start
pos = search_start
while pos < search_start + 500:
    idx = fdshap[pos:pos+500].find(pattern)
    if idx != -1:
        abs_pos = pos + idx
        print(f"Found at offset {abs_pos - res1_start} from resource start")
        break
    pos += 500

# Let's try to find where the tile data actually starts
# The first tile should be at some offset from resource start
# Let's look for non-zero data after the header
print(f"\n=== Looking for first non-trivial data after byte 200 ===")
for pos in range(res1_start + 200, res1_start + 300, 2):
    val = struct.unpack_from("<H", fdshap, pos)[0]
    if val > 0 and val < 1000:
        print(f"  Offset {pos - res1_start}: {val}")
