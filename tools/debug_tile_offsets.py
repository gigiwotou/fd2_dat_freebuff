#!/usr/bin/env python3
"""Test correct tile offset parsing"""

import struct

with open("game/FDSHAP.DAT", "rb") as f:
    fdshap = f.read()

resource_count = struct.unpack_from("<I", fdshap, 6)[0]
offsets = []
for i in range(resource_count):
    offset = struct.unpack_from("<I", fdshap, 10 + i * 4)[0]
    offsets.append(offset)

res1_start = offsets[1]
res1_size = offsets[2] - offsets[1]

tile_w = struct.unpack_from("<H", fdshap, res1_start)[0]
tile_h = struct.unpack_from("<H", fdshap, res1_start + 2)[0]
first_tile_offset = struct.unpack_from("<H", fdshap, res1_start + 4)[0]

print(f"Tile dimensions: {tile_w}x{tile_h}")
print(f"First tile offset: {first_tile_offset}")

# Parse offset table from byte 6, 4 bytes per entry
tile_offsets = []
pos = res1_start + 6
max_offsets = 200  # Limit to prevent infinite loop

while len(tile_offsets) < max_offsets and pos + 4 <= res1_start + res1_size:
    offset_val = struct.unpack_from("<H", fdshap, pos)[0]
    zero_val = struct.unpack_from("<H", fdshap, pos + 2)[0]
    
    print(f"  pos={pos - res1_start}: offset={offset_val}, zero={zero_val}")
    
    if zero_val == 0 and offset_val > 0:
        tile_offsets.append(offset_val)
        print(f"    -> Added tile offset {len(tile_offsets)-1}")
    
    pos += 4
    
    # Stop when we reach the first tile data
    if offset_val >= first_tile_offset:
        print(f"    -> Reached first tile data at offset {offset_val}, stopping")
        break

print(f"\nTotal tile offsets found: {len(tile_offsets)}")
print(f"First 10 offsets: {tile_offsets[:10]}")
