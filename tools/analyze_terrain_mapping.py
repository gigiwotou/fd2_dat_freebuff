#!/usr/bin/env python3
"""Analyze terrain ID to tile index mapping"""

import struct
from collections import Counter

with open("game/FDFIELD.DAT", "rb") as f:
    fdfield_data = f.read()

# Map 0 layout starts at offset 406
layout_start = 406
w = struct.unpack_from("<H", fdfield_data, layout_start)[0]
h = struct.unpack_from("<H", fdfield_data, layout_start + 2)[0]

print(f"Map 0: {w}x{h} tiles")

# Parse all terrain IDs
tile_data_offset = layout_start + 4
terrain_ids = []
pos = 0
for y in range(h):
    for x in range(w):
        if pos + 4 <= (w * h * 4):
            terrain_id = struct.unpack_from("<H", fdfield_data, tile_data_offset + pos)[0]
            terrain_ids.append(terrain_id)
            pos += 4

# Test hypothesis: terrain_id & 0x7F maps to tile index
print("\n--- Testing: tile_index = terrain_id & 0x7F (low 7 bits) ---")
mapped_indices = [tid & 0x7F for tid in terrain_ids]
max_mapped = max(mapped_indices)
print(f"Mapped index range: 0-{max_mapped}")
print(f"Max mapped index < 148? {max_mapped < 148}")

# Count unique mapped indices
unique_mapped = set(mapped_indices)
print(f"Unique mapped indices: {len(unique_mapped)}")

# Test other masking patterns
print("\n--- Testing different masks ---")
for mask in [0x7F, 0xFF, 0x3F, 0x1F]:
    mapped = [tid & mask for tid in terrain_ids]
    max_val = max(mapped)
    unique = len(set(mapped))
    fits = "YES" if max_val < 148 else "NO"
    print(f"  Mask 0x{mask:02X}: max={max_val}, unique={unique}, fits in 148 tiles? {fits}")

# Test: terrain_id % 148
print("\n--- Testing: tile_index = terrain_id % 148 ---")
modulo_mapped = [tid % 148 for tid in terrain_ids]
max_modulo = max(modulo_mapped)
unique_modulo = len(set(modulo_mapped))
print(f"Modulo mapped range: 0-{max_modulo}")
print(f"Unique mapped indices: {unique_modulo}")

# Show terrain IDs with bit analysis
print("\n--- Terrain ID bit analysis (sample of high IDs) ---")
high_ids = [tid for tid in set(terrain_ids) if tid >= 128]
for tid in sorted(high_ids)[:20]:
    binary = f"{tid:010b}"
    low7 = tid & 0x7F
    bit7 = (tid >> 7) & 1
    print(f"  Terrain {tid}: binary={binary}, bit7={bit7}, low7={low7}")
