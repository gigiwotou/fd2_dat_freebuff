"""Verify terrain ID extraction and tile index mapping for map 0"""
import struct
from pathlib import Path

# Load FDFIELD.DAT with format 2 parsing
fdfield_path = Path("game/FDFIELD.DAT")
fdfield_data = fdfield_path.read_bytes()

# Format 2: offsets from byte 6
fdfield_offsets = []
pos = 6
while pos + 4 <= len(fdfield_data):
    offset = struct.unpack_from('<I', fdfield_data, pos)[0]
    if offset < len(fdfield_data):
        fdfield_offsets.append(offset)
    else:
        break
    pos += 4

print(f"FDFIELD.DAT format 2: {len(fdfield_offsets)} resources")
print(f"offsets[0..3]: {fdfield_offsets[:4]}")

# Map 0: layout_idx=0
layout_idx = 0
layout_start = fdfield_offsets[layout_idx]
layout_end = fdfield_offsets[layout_idx + 1]
layout_data = fdfield_data[layout_start:layout_end]

print(f"\nLayout: offset {layout_start}-{layout_end}, size={len(layout_data)}")

# Parse layout dimensions
w = struct.unpack_from('<H', layout_data, 0)[0]
h = struct.unpack_from('<H', layout_data, 2)[0]
print(f"Dimensions: {w}x{h}")

# Parse terrain IDs
tile_data = layout_data[4:]
print(f"\nFirst 30 terrain IDs (first row):")
for i in range(min(30, w * h)):
    b0 = tile_data[i * 4]
    b1 = tile_data[i * 4 + 1]
    b2 = tile_data[i * 4 + 2]
    b3 = tile_data[i * 4 + 3]
    terrain_id = b0 | ((b1 & 0x03) << 8)
    
    if i < w:
        print(f"  [{i:2d}] bytes={b0:02x} {b1:02x} {b2:02x} {b3:02x}, terrain_id={terrain_id:3d}")

# Load FDSHAP.DAT with format 2 parsing
fdshap_path = Path("game/FDSHAP.DAT")
fdshap_data = fdshap_path.read_bytes()

fdshap_offsets = []
pos = 6
while pos + 4 <= len(fdshap_data):
    offset = struct.unpack_from('<I', fdshap_data, pos)[0]
    if offset < len(fdshap_data):
        fdshap_offsets.append(offset)
    else:
        break
    pos += 4

print(f"\nFDSHAP.DAT format 2: {len(fdshap_offsets)} resources")

# Load control data to get terrain_set_id
control_idx = 1
control_start = fdfield_offsets[control_idx]
control_end = fdfield_offsets[control_idx + 1]
control_data = fdfield_data[control_start:control_end]
terrain_set_id = control_data[0]

print(f"terrain_set_id = {terrain_set_id}")

# Load tileset
tileset_idx = terrain_set_id * 2
print(f"tileset_idx = {tileset_idx}")
print(f"tileset offset = {fdshap_offsets[tileset_idx]}")

tileset_start = fdshap_offsets[tileset_idx]
tileset_end = fdshap_offsets[tileset_idx + 1]
tileset_data = fdshap_data[tileset_start:tileset_end]

# Parse tileset header
tile_width = struct.unpack_from('<H', tileset_data, 0)[0]
tile_height = struct.unpack_from('<H', tileset_data, 2)[0]
tile_count = struct.unpack_from('<H', tileset_data, 4)[0]

print(f"Tileset header: {tile_width}x{tile_height}, {tile_count} tiles")

# Parse tile offsets (format 2 from byte 6)
tile_offsets = []
pos = 6
while pos + 4 <= len(tileset_data):
    offset = struct.unpack_from('<I', tileset_data, pos)[0]
    if offset < len(tileset_data):
        tile_offsets.append(offset)
    else:
        break
    pos += 4

print(f"Tile offsets: {len(tile_offsets)}")

# Check if terrain IDs map to valid tile indices
print(f"\nTerrain ID mapping:")
for i in range(min(30, w * h)):
    b0 = tile_data[i * 4]
    b1 = tile_data[i * 4 + 1]
    terrain_id = b0 | ((b1 & 0x03) << 8)
    
    # Try direct mapping
    tile_idx_direct = terrain_id
    valid_direct = tile_idx_direct < len(tile_offsets)
    
    # Try modulo mapping
    tile_idx_mod = terrain_id % tile_count
    valid_mod = tile_idx_mod < len(tile_offsets)
    
    if i < w:
        print(f"  terrain_id={terrain_id:3d}: direct={tile_idx_direct:3d}({'ok' if valid_direct else 'FAIL'}), mod={tile_idx_mod:3d}({'ok' if valid_mod else 'FAIL'})")
