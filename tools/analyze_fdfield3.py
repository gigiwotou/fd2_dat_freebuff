#!/usr/bin/env python3
"""Analyze FDFIELD.DAT map 0 layout data with different interpretations"""

import struct

fdfield_path = "game/FDFIELD.DAT"
with open(fdfield_path, "rb") as f:
    data = f.read()

resource_count = struct.unpack_from("<I", data, 6)[0]
offsets = []
for i in range(resource_count):
    offset = struct.unpack_from("<I", data, 10 + i * 4)[0]
    offsets.append(offset)

# Map 0 layout data
layout_start = offsets[0]
layout_end = offsets[1]
layout_size = layout_end - layout_start

print(f"Map 0 layout: offset={layout_start}, size={layout_size}")
print(f"Raw data (first 100 bytes): {data[layout_start:layout_start+100].hex()}")

# Interpretation 1: First 4 bytes are NOT width/height, but part of tile data
# Maybe width/height are stored elsewhere or have fixed values
print("\n--- Interpretation 1: Fixed map dimensions, all data is tiles ---")
# Try common dimensions
for w, h in [(12, 10), (16, 12), (20, 15), (24, 24), (30, 20)]:
    tile_data_size = w * h * 4
    if tile_data_size == layout_size:
        print(f"  MATCH: {w}x{h} = {tile_data_size} bytes")
    elif tile_data_size == layout_size - 4:
        print(f"  CLOSE: {w}x{h} = {tile_data_size} bytes (need 4 byte header)")

# Interpretation 2: Little-endian 16-bit width/height
w_le = struct.unpack_from("<H", data, layout_start)[0]
h_le = struct.unpack_from("<H", data, layout_start + 2)[0]
print(f"\n--- Interpretation 2: LE 16-bit ---")
print(f"  w={w_le} (0x{w_le:04x}), h={h_le} (0x{h_le:04x})")

# Interpretation 3: Big-endian 16-bit width/height
w_be = struct.unpack_from(">H", data, layout_start)[0]
h_be = struct.unpack_from(">H", data, layout_start + 2)[0]
print(f"\n--- Interpretation 3: BE 16-bit ---")
print(f"  w={w_be} (0x{w_be:04x}), h={h_be} (0x{h_be:04x})")

# Interpretation 4: Maybe width/height are stored in control data
control_start = offsets[1]
print(f"\n--- Interpretation 4: Check control data ---")
print(f"  Control first 50 bytes: {data[control_start:control_start+50].hex()}")

# Interpretation 5: Maybe the layout has no explicit width/height, 
# and we need to derive it from the tile data size
# Each tile is 4 bytes (2 bytes terrain + 2 bytes event)
if layout_size % 4 == 0:
    tile_count = layout_size // 4
    print(f"\n--- Interpretation 5: Derive dimensions from tile count ---")
    print(f"  Total tiles (if no header): {tile_count}")
    
    # Find factor pairs
    for w in range(10, 50):
        if tile_count % w == 0:
            h = tile_count // w
            if 5 <= h <= 50:
                print(f"  Possible: {w}x{h}")

# Interpretation 6: Maybe first 4 bytes ARE header but different format
first_4 = data[layout_start:layout_start+4]
print(f"\n--- Interpretation 6: First 4 bytes ---")
print(f"  Hex: {first_4.hex()}")
print(f"  As uint32: {struct.unpack_from('<I', data, layout_start)[0]}")
print(f"  Byte values: {list(first_4)}")

# If we assume 24x24 tiles
tile_data_with_header = layout_size
if layout_size > 4:
    for w in range(10, 40):
        for h in range(10, 40):
            if w * h * 4 + 4 == layout_size:
                print(f"\n  Found exact match: {w}x{h} map with 4-byte header")
                # Parse tile data
                tile_data_start = layout_start + 4
                terrain_id = struct.unpack_from("<H", data, tile_data_start)[0]
                event_id = struct.unpack_from("<H", data, tile_data_start + 2)[0]
                print(f"  First tile: terrain={terrain_id}, event={event_id}")
                break
