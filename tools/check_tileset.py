#!/usr/bin/env python3
"""
Verify FDSHAP.DAT tileset structure for map 32
"""

import struct

fdfield_path = r'd:\testworkspace\fd2_dat_freebuff\bin\FDFIELD.DAT'
fdshap_path = r'd:\testworkspace\fd2_dat_freebuff\bin\FDSHAP.DAT'

# Parse FDFIELD.DAT to get terrain_set_id for map 32
with open(fdfield_path, 'rb') as f:
    fdfield = f.read()

# Map 32 offsets
idx_offset = 6 + 32 * 12
layout_off, control_off, charpos_off = struct.unpack_from('<III', fdfield, idx_offset)

# Control data byte 0 = terrain_set_id
terrain_set_id = fdfield[control_off]
print(f"Map 32 terrain_set_id: {terrain_set_id}")

# Parse FDSHAP.DAT
with open(fdshap_path, 'rb') as f:
    fdshap = f.read()

print(f"\nFDSHAP.DAT file size: {len(fdshap)} bytes")

# Tileset is at terrain_set_id * 2
tileset_idx = terrain_set_id * 2

# Parse tileset structure
# First, find the tileset resource offset
# FDSHAP also uses the same format: 6 bytes header + offset table
pos = 6
offsets = []
while pos + 4 <= len(fdshap):
    offset = struct.unpack_from('<I', fdshap, pos)[0]
    if offset > len(fdshap):
        break
    offsets.append(offset)
    pos += 4

print(f"FDSHAP.DAT parsed {len(offsets)} resources")

if tileset_idx < len(offsets):
    tileset_off = offsets[tileset_idx]
    tileset_next_off = offsets[tileset_idx + 1] if tileset_idx + 1 < len(offsets) else len(fdshap)
    tileset_size = tileset_next_off - tileset_off
    
    print(f"\nTileset {tileset_idx} at offset {tileset_off} (0x{tileset_off:06X})")
    print(f"Tileset size: {tileset_size} bytes")
    
    # Parse tileset header
    tileset_data = fdshap[tileset_off:tileset_off + tileset_size]
    
    tile_width = struct.unpack_from('<H', tileset_data, 0)[0]
    tile_height = struct.unpack_from('<H', tileset_data, 2)[0]
    tile_count = struct.unpack_from('<H', tileset_data, 4)[0]
    
    print(f"Tile dimensions: {tile_width} x {tile_height} pixels")
    print(f"Tile count: {tile_count}")
    print(f"Tile size constant: {tile_width} (should match MAP_TILE_SIZE in code)")
else:
    print(f"ERROR: Tileset index {tileset_idx} out of range")
