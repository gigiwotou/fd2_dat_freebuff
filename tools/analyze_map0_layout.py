#!/usr/bin/env python3
"""Deep analyze map 0 layout data structure"""

import struct

fdfield_path = "game/FDFIELD.DAT"
with open(fdfield_path, "rb") as f:
    data = f.read()

resource_count = struct.unpack_from("<I", data, 6)[0]
offsets = []
for i in range(resource_count):
    offset = struct.unpack_from("<I", data, 10 + i * 4)[0]
    offsets.append(offset)

# Map 0 layout resource
layout_start = offsets[0]
layout_end = offsets[1]
layout_size = layout_end - layout_start

print(f"Map 0 layout: offset={layout_start}, size={layout_size}")

# Check if size minus different header sizes gives valid tile counts
print("\n--- Possible tile counts (tile = 4 bytes) ---")
for header_size in range(0, 10):
    remaining = layout_size - header_size
    if remaining > 0 and remaining % 4 == 0:
        tile_count = remaining // 4
        # Find factor pairs
        factors = []
        for w in range(5, 50):
            if tile_count % w == 0:
                h = tile_count // w
                if 5 <= h <= 50:
                    factors.append(f"{w}x{h}")
        if factors:
            print(f"  Header {header_size} bytes: {tile_count} tiles, possible dims: {', '.join(factors[:5])}")

# Check multiple map layouts to find a pattern
print("\n--- First 10 map layouts ---")
for map_idx in range(10):
    layout_res = map_idx * 3
    if layout_res >= resource_count:
        break
    
    l_start = offsets[layout_res]
    l_end = offsets[layout_res + 1]
    l_size = l_end - l_start
    
    # Check different header sizes
    valid_dims = []
    for header_size in [0, 1, 2, 4]:
        remaining = l_size - header_size
        if remaining > 0 and remaining % 4 == 0:
            tile_count = remaining // 4
            for w in range(8, 40):
                if tile_count % w == 0:
                    h = tile_count // w
                    if 8 <= h <= 40:
                        valid_dims.append((w, h, header_size))
    
    if valid_dims:
        # Show first few valid dimensions
        for w, h, hdr in valid_dims[:3]:
            print(f"  Map {map_idx}: size={l_size}, possible {w}x{h} (header={hdr})")

# Look at actual tile data patterns
print("\n--- Tile data analysis ---")
# If header is at offset 0-3, tile data starts at offset 4
# If no header, tile data starts at offset 0
for header_offset in [0, 4]:
    tile_data_start = layout_start + header_offset
    tile_data = data[tile_data_start:tile_data_start + 40]
    print(f"\n  Assuming tile data starts at offset {header_offset}:")
    print(f"  Hex: {tile_data.hex()}")
    
    # Parse as pairs of 2-byte values
    for i in range(0, min(20, len(tile_data)), 4):
        val1 = struct.unpack_from("<H", tile_data, i)[0]
        val2 = struct.unpack_from("<H", tile_data, i + 2)[0]
        print(f"    Tile {i//4}: terrain=0x{val1:04x}({val1}), event=0x{val2:04x}({val2})")
