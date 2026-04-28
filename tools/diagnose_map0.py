#!/usr/bin/env python3
"""Generate diagnostic images for map 0"""

import struct
import json
from PIL import Image
from pathlib import Path

output_dir = Path("output/maps")

# Load map 0 layout
with open(output_dir / "map_0_layout.json", "r") as f:
    layout = json.load(f)

terrain_ids = layout["terrain_ids"]
width = layout["width"]
height = layout["height"]

print(f"Map 0: {width}x{height}")
print(f"Terrain set ID: {layout['terrain_set_id']}")

# Load the generated map image
map_img = Image.open(output_dir / "map_0.png")
print(f"Map image size: {map_img.size}")

# Analyze terrain ID distribution
from collections import Counter
all_terrains = []
for row in terrain_ids:
    all_terrains.extend(row)

terrain_counter = Counter(all_terrains)
print(f"\nUnique terrain IDs: {len(terrain_counter)}")
print(f"Terrain ID range: {min(terrain_counter.keys())}-{max(terrain_counter.keys())}")

print(f"\nTop 20 terrain IDs by frequency:")
for tid, count in terrain_counter.most_common(20):
    tile_idx = tid & 0x7F
    print(f"  Terrain ID {tid:3d} -> tile index {tile_idx:3d}: {count:3d} tiles")

# Create a diagnostic image showing terrain IDs as colors
# Map terrain IDs to unique colors for visualization
diag_img = Image.new("RGB", (width * 20, height * 20), (0, 0, 0))
unique_terrains = sorted(terrain_counter.keys())
terrain_colors = {}
for i, tid in enumerate(unique_terrains):
    # Generate a unique color for each terrain ID
    r = (i * 37) % 256
    g = (i * 73) % 256
    b = (i * 151) % 256
    terrain_colors[tid] = (r, g, b)

for y in range(height):
    for x in range(width):
        tid = terrain_ids[y][x]
        color = terrain_colors.get(tid, (255, 0, 255))
        # Draw 20x20 block
        for py in range(20):
            for px in range(20):
                diag_img.putpixel((x * 20 + px, y * 20 + py), color)

diag_img.save(output_dir / "map_0_terrain_ids.png")
print(f"\nSaved terrain ID visualization to map_0_terrain_ids.png")

# Also show tile index distribution (after & 0x7F mapping)
tile_indices = [tid & 0x7F for tid in all_terrains]
tile_counter = Counter(tile_indices)
print(f"\nUnique tile indices (after & 0x7F): {len(tile_counter)}")
print(f"Tile index range: {min(tile_counter.keys())}-{max(tile_counter.keys())}")
