"""Compare C code vs Python tool for map 0 resource loading"""
import struct
from pathlib import Path

# Load DAT files
fdfield_path = Path("game/FDFIELD.DAT")
fdfield_data = fdfield_path.read_bytes()

# Python tool uses format 2: offsets from byte 6
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
print(f"offsets[0..5]: {fdfield_offsets[:6]}")

# Python tool (export_all_maps.py):
# layout_idx = 0 (for map 0)
# control_idx = 1 (for map 0)
print(f"\n=== Python tool reads: ===")
print(f"  layout_idx = 0, offset = {fdfield_offsets[0]}")
print(f"  control_idx = 1, offset = {fdfield_offsets[1]}")

layout_data_py = fdfield_data[fdfield_offsets[0]:fdfield_offsets[1]]
control_data_py = fdfield_data[fdfield_offsets[1]:fdfield_offsets[2]]

w_py = struct.unpack_from('<H', layout_data_py, 0)[0]
h_py = struct.unpack_from('<H', layout_data_py, 2)[0]
print(f"  Layout: {w_py}x{h_py}, size={len(layout_data_py)}")

ts_id_py = control_data_py[0]
print(f"  terrain_set_id = {ts_id_py}")

# Parse first row of terrain IDs
tile_data_py = layout_data_py[4:]
print(f"\n  First row terrain IDs: ", end="")
for x in range(min(w_py, 10)):
    b0 = tile_data_py[x * 4]
    b1 = tile_data_py[x * 4 + 1]
    tid = b0 | ((b1 & 0x03) << 8)
    print(f"{tid} ", end="")
print()

# C code currently uses:
# layout_idx = map_id * 3 = 0
# control_idx = map_id * 3 + 1 = 1
print(f"\n=== C code (current) reads: ===")
print(f"  layout_idx = 0, offset = {fdfield_offsets[0]}")
print(f"  control_idx = 1, offset = {fdfield_offsets[1]}")
print(f"  (Same as Python!)")

# But wait! The C code uses format 1 parsing which gives different offsets!
# Let me check what format 1 parsing gives:
print(f"\n=== What if C used format 1 parsing: ===")
count_f1 = struct.unpack_from('<I', fdfield_data, 6)[0]
print(f"  count = {count_f1}")
offset0_f1 = struct.unpack_from('<I', fdfield_data, 10)[0]
offset1_f1 = struct.unpack_from('<I', fdfield_data, 14)[0]
print(f"  layout_idx = 0, offset = {offset0_f1}")
print(f"  control_idx = 1, offset = {offset1_f1}")

# Check if the C code's resource indexing is correct
print(f"\n=== C code resource indices for map 0: ===")
print(f"  layout_idx = 0 * 3 = 0")
print(f"  control_idx = 0 * 3 + 1 = 1")
print(f"  These should match Python's indices!")

# The issue might be in how the C code loads the tileset
fdshap_path = Path("game/FDSHAP.DAT")
fdshap_data = fdshap_path.read_bytes()

# Python format 2 parsing for FDSHAP
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
print(f"offsets[0..3]: {fdshap_offsets[:4]}")

# C code uses tileset_idx = terrain_set_id * 2
tileset_idx = ts_id_py * 2
print(f"\ntileset_idx = {ts_id_py} * 2 = {tileset_idx}")
print(f"tileset offset = {fdshap_offsets[tileset_idx]}")

# Check tileset header
tileset_data = fdshap_data[fdshap_offsets[tileset_idx]:fdshap_offsets[tileset_idx + 1]]
tile_w = struct.unpack_from('<H', tileset_data, 0)[0]
tile_h = struct.unpack_from('<H', tileset_data, 2)[0]
tile_count = struct.unpack_from('<H', tileset_data, 4)[0]
print(f"Tileset header: {tile_w}x{tile_h}, {tile_count} tiles")

# Parse tile offsets from byte 6
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

# Check terrain ID to tile index mapping
print(f"\nTerrain ID mapping verification:")
for i in range(min(5, w_py)):
    b0 = tile_data_py[i * 4]
    b1 = tile_data_py[i * 4 + 1]
    tid = b0 | ((b1 & 0x03) << 8)
    print(f"  terrain_id={tid:3d} -> tile_idx={tid} (valid={tid < len(tile_offsets)})")
