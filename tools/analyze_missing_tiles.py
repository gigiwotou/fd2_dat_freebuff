#!/usr/bin/env python3
"""Analyze unrendered tiles in map 0"""

import struct
import json
from collections import Counter

with open("game/FDFIELD.DAT", "rb") as f:
    fdfield_data = f.read()

# Load map 0 layout
with open("output/maps/map_0_layout.json", "r") as f:
    layout = json.load(f)

terrain_ids = layout["terrain_ids"]
width = layout["width"]
height = layout["height"]

print(f"Map 0: {width}x{height} tiles")
print(f"Terrain set ID: {layout['terrain_set_id']}")

# Parse FDFIELD.DAT to get layout data
# Map 0 layout starts at offset 406
layout_start = 406
w = struct.unpack_from("<H", fdfield_data, layout_start)[0]
h = struct.unpack_from("<H", fdfield_data, layout_start + 2)[0]

print(f"Dimensions from file: {w}x{h}")

# Parse tile data
tile_data_offset = layout_start + 4
pos = 0
terrain_counter = Counter()

for y in range(height):
    for x in range(width):
        if pos + 4 <= (width * height * 4):
            terrain_id = struct.unpack_from("<H", fdfield_data, tile_data_offset + pos)[0]
            terrain_counter[terrain_id] += 1
            pos += 4

print(f"\nUnique terrain IDs in map: {len(terrain_counter)}")
print(f"Min terrain ID: {min(terrain_counter.keys())}")
print(f"Max terrain ID: {max(terrain_counter.keys())}")

# We had 148 tiles (0-147) extracted from FDSHAP resource 1
rendered_count = sum(count for terrain_id, count in terrain_counter.items() if terrain_id < 148)
missing_count = sum(count for terrain_id, count in terrain_counter.items() if terrain_id >= 148)

print(f"\nRendered tiles: {rendered_count}")
print(f"Missing tiles: {missing_count}")

print(f"\nTop 20 most common terrain IDs:")
for terrain_id, count in terrain_counter.most_common(20):
    status = "OK" if terrain_id < 148 else "MISSING"
    print(f"  Terrain {terrain_id}: {count} tiles [{status}]")

# Show all missing terrain IDs with their counts
print(f"\nAll missing terrain IDs (>= 148):")
missing_terrains = {tid: count for tid, count in terrain_counter.items() if tid >= 148}
for tid in sorted(missing_terrains.keys()):
    print(f"  Terrain {tid}: {missing_terrains[tid]} tiles")
