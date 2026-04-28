#!/usr/bin/env python3
"""
Verify the correct FDFIELD.DAT structure:
- Offset 0-5: Magic (6 bytes) 'LLLLLL'
- Offset 6-9: First map layout data OFFSET (4 bytes)
- Offset 10-13: Second map layout data OFFSET (4 bytes)
- etc.

Map count is NOT stored explicitly. We need to count valid map entries.
Each map entry is 12 bytes (3 offsets: layout, control, spawn)
"""

import struct

with open("game/FDFIELD.DAT", "rb") as f:
    data = f.read()

# First map layout offset is at byte 6
first_layout_offset = struct.unpack_from("<I", data, 6)[0]
print(f"First layout offset: {first_layout_offset}")

# If this is correct, then the map entry table starts at offset 6
# Each map entry is 12 bytes
# How many complete 12-byte entries fit before first_layout_offset?

map_entry_table_size = first_layout_offset - 6  # 6 bytes for magic
map_entry_count = map_entry_table_size // 12
print(f"Map entry table size: {map_entry_table_size}")
print(f"Map count: {map_entry_count}")

# Now let's parse all maps
print("\n--- Parsing all maps ---")
for map_idx in range(map_entry_count):
    entry_start = 6 + map_idx * 12
    
    if entry_start + 12 > first_layout_offset:
        print(f"Map {map_idx}: Entry extends beyond map table")
        break
    
    layout_offset = struct.unpack_from("<I", data, entry_start)[0]
    control_offset = struct.unpack_from("<I", data, entry_start + 4)[0]
    spawn_offset = struct.unpack_from("<I", data, entry_start + 8)[0]
    
    print(f"\nMap {map_idx}:")
    print(f"  Layout offset: {layout_offset}")
    
    if layout_offset < len(data) - 4:
        w = struct.unpack_from("<H", data, layout_offset)[0]
        h = struct.unpack_from("<H", data, layout_offset + 2)[0]
        print(f"  Dimensions: {w}x{h}")
        
        # Check if layout data size matches expected
        expected_tile_data_size = w * h * 4
        # Find next layout offset to calculate size
        if map_idx + 1 < map_entry_count:
            next_entry = 6 + (map_idx + 1) * 12
            next_layout_offset = struct.unpack_from("<I", data, next_entry)[0]
            actual_layout_size = next_layout_offset - layout_offset
            print(f"  Layout size: {actual_layout_size}, Expected: {expected_tile_data_size + 4}")
            if actual_layout_size == expected_tile_data_size + 4:
                print(f"  ✓ Size matches!")
            else:
                print(f"  ✗ Size mismatch")
