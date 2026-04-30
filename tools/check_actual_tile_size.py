#!/usr/bin/env python3
"""
Verify the actual tile size used in map rendering

Map 32: 18 x 51 tiles
If tile = 24x24:
  Map pixel size: 18*24 x 51*24 = 432 x 1224 pixels
If tile = 64x64:
  Map pixel size: 18*64 x 51*64 = 1152 x 3264 pixels
If tile = 128x128:
  Map pixel size: 18*128 x 51*128 = 2304 x 6528 pixels

Screen is 320x200, so:
- With 24x24 tiles: would see ~13x8 tiles on screen
- With 64x64 tiles: would see ~5x3 tiles on screen
- With 128x128 tiles: would see ~2x1 tiles on screen

Let's check what IDA says about tile size
"""

# From previous IDA analysis:
# sub_2921A shows tile rendering with 128x128 stride
# But FDSHAP.DAT tileset says 24x24

# Check if there's a scaling factor
print("Analysis of tile size:")
print()
print("FDSHAP.DAT tileset header says: 24x24 pixels")
print("But this might be for character icons, not map tiles!")
print()
print("Let's check multiple tilesets...")

import struct

fdshap_path = r'd:\testworkspace\fd2_dat_freebuff\bin\FDSHAP.DAT'

with open(fdshap_path, 'rb') as f:
    fdshap = f.read()

# Parse offsets
pos = 6
offsets = []
while pos + 4 <= len(fdshap):
    offset = struct.unpack_from('<I', fdshap, pos)[0]
    if offset > len(fdshap):
        break
    offsets.append(offset)
    pos += 4

print(f"Total resources in FDSHAP.DAT: {len(offsets)}")
print()

# Check several tilesets
for terrain_id in [0, 1, 2, 4, 8, 16, 32]:
    tileset_idx = terrain_id * 2
    if tileset_idx + 1 < len(offsets):
        tileset_off = offsets[tileset_idx]
        tileset_data = fdshap[tileset_off:tileset_off+6]
        
        tile_w = struct.unpack_from('<H', tileset_data, 0)[0]
        tile_h = struct.unpack_from('<H', tileset_data, 2)[0]
        tile_count = struct.unpack_from('<H', tileset_data, 4)[0]
        
        print(f"Terrain {terrain_id:2d} (tileset {tileset_idx:3d}): {tile_w:3d}x{tile_h:3d} pixels, {tile_count:3d} tiles")

print()
print("Note: If terrain 32 shows 24x24, that's likely wrong.")
print("Map tiles should be larger than character sprites.")
