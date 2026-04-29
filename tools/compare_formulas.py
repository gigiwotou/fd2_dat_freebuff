import struct
from collections import Counter

with open("game/FDFIELD.DAT", "rb") as f:
    fdfield = f.read()

with open("game/FDSHAP.DAT", "rb") as f:
    fdshap = f.read()

# Parse FDFIELD.DAT
fdfield_offsets = []
pos = 6
while pos + 4 <= len(fdfield):
    offset = struct.unpack_from("<I", fdfield, pos)[0]
    if offset > pos and offset < len(fdfield):
        fdfield_offsets.append(offset)
    else:
        break
    pos += 4

# Map 0
layout_start = fdfield_offsets[0]
w = struct.unpack_from("<H", fdfield, layout_start)[0]
h = struct.unpack_from("<H", fdfield, layout_start + 2)[0]
print(f"Map 0: {w}x{h}")

# Parse terrain IDs using different formulas
tile_data = fdfield[layout_start + 4:]
terrain_ids_formula1 = []  # Original Python: raw 16-bit
terrain_ids_formula2 = []  # IDA sub_12E38: byte[0] | ((byte[1] & 3) << 8)

pos = 0
for y in range(h):
    for x in range(w):
        if pos + 4 <= len(tile_data):
            b0 = tile_data[pos]
            b1 = tile_data[pos + 1]
            b2 = tile_data[pos + 2]
            b3 = tile_data[pos + 3]
            
            # Formula 1: raw 16-bit
            tid1 = struct.unpack_from("<H", tile_data, pos)[0]
            terrain_ids_formula1.append(tid1)
            
            # Formula 2: byte[0] | ((byte[1] & 3) << 8)
            tid2 = b0 | ((b1 & 3) << 8)
            terrain_ids_formula2.append(tid2)
            
            pos += 4

print(f"\nFormula 1 (raw 16-bit):")
print(f"  Range: {min(terrain_ids_formula1)}-{max(terrain_ids_formula1)}")
print(f"  Unique: {len(set(terrain_ids_formula1))}")

print(f"\nFormula 2 (byte[0] | ((byte[1] & 3) << 8)):")
print(f"  Range: {min(terrain_ids_formula2)}-{max(terrain_ids_formula2)}")
print(f"  Unique: {len(set(terrain_ids_formula2))}")

# Check FDSHAP tile count
fdshap_rc = struct.unpack_from("<I", fdshap, 6)[0]
fdshap_offsets = []
for i in range(fdshap_rc):
    offset = struct.unpack_from("<I", fdshap, 10 + i * 4)[0]
    fdshap_offsets.append(offset)

res1_start = fdshap_offsets[1]
res1_end = fdshap_offsets[2] if 2 < len(fdshap_offsets) else len(fdshap)
res1_size = res1_end - res1_start

# Count tiles using DWORD offset table from byte 6
tile_offsets = []
pos = res1_start + 6
while pos + 4 <= res1_start + res1_size:
    offset_val = struct.unpack_from("<I", fdshap, pos)[0]
    if 0 < offset_val < res1_size:
        tile_offsets.append(offset_val)
    else:
        if len(tile_offsets) > 0 and offset_val >= res1_size:
            break
    pos += 4

print(f"\nFDSHAP resource 1 tiles: {len(tile_offsets)}")

# Check which formula fits
for name, tids in [("Formula 1", terrain_ids_formula1), ("Formula 2", terrain_ids_formula2)]:
    max_tid = max(tids)
    unique = len(set(tids))
    fits = "[OK]" if max_tid < len(tile_offsets) else "[EXCEEDS]"
    print(f"{name}: max={max_tid}, unique={unique}, fits {len(tile_offsets)} tiles? {fits}")
