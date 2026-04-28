#!/usr/bin/env python3
"""Analyze terrain ID distribution in map 0"""

import struct
from collections import Counter

with open("game/FDFIELD.DAT", "rb") as f:
    fdfield = f.read()

with open("game/FDSHAP.DAT", "rb") as f:
    fdshap = f.read()

# Parse FDFIELD.DAT - offset table starts at 6
fdfield_offsets = []
pos = 6
while pos + 4 <= len(fdfield):
    offset = struct.unpack_from("<I", fdfield, pos)[0]
    if offset > pos and offset < len(fdfield):
        fdfield_offsets.append(offset)
    else:
        break
    pos += 4

print(f"FDFIELD.DAT: {len(fdfield_offsets)} resources, {len(fdfield_offsets)//3} maps")

# Map 0 layout at resource 0
layout_start = fdfield_offsets[0]
w = struct.unpack_from("<H", fdfield, layout_start)[0]
h = struct.unpack_from("<H", fdfield, layout_start + 2)[0]
print(f"Map 0: {w}x{h}")

# Parse terrain IDs
tile_data = fdfield[layout_start + 4:]
terrain_ids = []
pos = 0
for y in range(h):
    for x in range(w):
        if pos + 4 <= len(tile_data):
            tid = struct.unpack_from("<H", tile_data, pos)[0]
            terrain_ids.append(tid)
            pos += 4

# Analyze terrain ID distribution
print(f"\nTerrain ID analysis:")
print(f"Range: {min(terrain_ids)}-{max(terrain_ids)}")
print(f"Unique values: {len(set(terrain_ids))}")

# Test different bit masks
print(f"\nTerrain ID bit analysis:")
counter = Counter(terrain_ids)
print(f"Top 20 terrain IDs:")
for tid, count in counter.most_common(20):
    binary = f"{tid:016b}"
    low5 = tid & 0x1F
    low7 = tid & 0x7F
    print(f"  {tid:5d} (0x{tid:04x}, bin={binary[-8:]}): low5={low5}, low7={low7}, count={count}")

# Count unique tile indices with different masks
masks = [0x1F, 0x3F, 0x7F, 0xFF]
print(f"\nTile index uniqueness with different masks:")
for mask in masks:
    indices = [tid & mask for tid in terrain_ids]
    unique = len(set(indices))
    max_idx = max(indices)
    print(f"  Mask 0x{mask:02X}: {unique} unique tiles, max index {max_idx}")

# Check FDSHAP resource 1 tile count
fdshap_rc = struct.unpack_from("<I", fdshap, 6)[0]
fdshap_offsets = []
for i in range(fdshap_rc):
    offset = struct.unpack_from("<I", fdshap, 10 + i * 4)[0]
    fdshap_offsets.append(offset)

res1_start = fdshap_offsets[1]
tile_w = struct.unpack_from("<H", fdshap, res1_start)[0]
tile_h = struct.unpack_from("<H", fdshap, res1_start + 2)[0]
print(f"\nFDSHAP resource 1: {tile_w}x{tile_h} tiles")

# Count tiles
tile_offsets = []
first_offset = struct.unpack_from("<H", fdshap, res1_start + 4)[0]
if first_offset > 0:
    tile_offsets.append(first_offset)
pos = res1_start + 6
while pos + 4 <= len(fdshap):
    offset_val = struct.unpack_from("<H", fdshap, pos)[0]
    zero_val = struct.unpack_from("<H", fdshap, pos + 2)[0]
    if zero_val == 0 and offset_val > 0:
        tile_offsets.append(offset_val)
    pos += 4
    if offset_val > len(fdshap) - 500:
        break

print(f"Total tiles in FDSHAP resource 1: {len(tile_offsets)}")

# Check which mask gives the best fit
print(f"\nBest mask analysis:")
for mask in masks:
    indices = [tid & mask for tid in terrain_ids]
    unique = len(set(indices))
    max_idx = max(indices)
    fits = "✓" if max_idx < len(tile_offsets) else "✗ EXCEEDS"
    print(f"  Mask 0x{mask:02X}: {unique} unique tiles, max {max_idx}, fits {len(tile_offsets)} tiles? {fits}")

# Check if terrain IDs have a pattern
print(f"\nTerrain ID byte analysis:")
low_bytes = [tid & 0xFF for tid in terrain_ids]
high_bytes = [(tid >> 8) & 0xFF for tid in terrain_ids]
print(f"Low byte range: {min(low_bytes)}-{max(low_bytes)}, unique: {len(set(low_bytes))}")
print(f"High byte range: {min(high_bytes)}-{max(high_bytes)}, unique: {len(set(high_bytes))}")

# Check high byte values
high_counter = Counter(high_bytes)
print(f"High byte distribution:")
for val, count in high_counter.most_common():
    print(f"  0x{val:02X}: {count} times")
