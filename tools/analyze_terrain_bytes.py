#!/usr/bin/env python3
"""Analyze terrain ID mapping with different masks based on IDA sub_4DF4C"""

import struct
from collections import Counter

with open("game/FDFIELD.DAT", "rb") as f:
    fdfield = f.read()

with open("game/FDSHAP.DAT", "rb") as f:
    fdshap = f.read()

# Parse FDFIELD map 0 layout
resource_count_fdfield = struct.unpack_from("<I", fdfield, 6)[0]
fdfield_offsets = []
pos = 10
while pos < len(fdfield) - 4:
    offset = struct.unpack_from("<I", fdfield, pos)[0]
    if offset > pos and offset < len(fdfield):
        fdfield_offsets.append(offset)
    else:
        break
    pos += 4

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

# Analyze terrain ID byte structure
print(f"\nTerrain ID analysis:")
print(f"Range: {min(terrain_ids)}-{max(terrain_ids)}")
print(f"Unique values: {len(set(terrain_ids))}")

# Check byte structure per IDA sub_4DF4C
# Each terrain_id is 2 bytes: [low_byte, high_byte]
# sub_4DF4C does: byte1 &= 3 (high_byte keeps low 2 bits)
# So terrain_id = low_byte | (high_byte & 3) << 8

masked_ids_10bit = []
for tid in terrain_ids:
    low = tid & 0xFF
    high = (tid >> 8) & 0xFF
    masked = low | ((high & 3) << 8)
    masked_ids_10bit.append(masked)

print(f"\nWith 10-bit mask (high_byte & 3):")
print(f"Range: {min(masked_ids_10bit)}-{max(masked_ids_10bit)}")
print(f"Unique: {len(set(masked_ids_10bit))}")

# Test different tile index mappings
masks_to_test = [0x1F, 0x3F, 0x7F, 0xFF, 0x1FF, 0x3FF]

print(f"\nTile index mapping with different masks:")
for mask in masks_to_test:
    tile_indices = [tid & mask for tid in masked_ids_10bit]
    unique_tiles = len(set(tile_indices))
    print(f"  Mask 0x{mask:03X}: {unique_tiles} unique tile indices, range {min(tile_indices)}-{max(tile_indices)}")

# Check FDSHAP tile count
fdshap_rc = struct.unpack_from("<I", fdshap, 6)[0]
fdshap_offsets = []
for i in range(fdshap_rc):
    offset = struct.unpack_from("<I", fdshap, 10 + i * 4)[0]
    fdshap_offsets.append(offset)

# Resource 1 tile set
res1_start = fdshap_offsets[1]
tile_w = struct.unpack_from("<H", fdshap, res1_start)[0]
tile_h = struct.unpack_from("<H", fdshap, res1_start + 2)[0]
print(f"\nFDSHAP Resource 1: {tile_w}x{tile_h} tiles")

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

print(f"Total tiles in resource 1: {len(tile_offsets)}")

# Which mask gives the best match?
print(f"\nComparing tile count with mapping results:")
for mask in masks_to_test:
    tile_indices = [tid & mask for tid in masked_ids_10bit]
    unique_tiles = len(set(tile_indices))
    max_tile = max(tile_indices)
    fits = "✓" if max_tile < len(tile_offsets) else "✗ EXCEEDS"
    print(f"  Mask 0x{mask:03X}: {unique_tiles} unique tiles, max index {max_tile} {fits} ({len(tile_offsets)} available)")
