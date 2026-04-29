import struct

with open("game/FDSHAP.DAT", "rb") as f:
    fdshap = f.read()

# Parse resource offsets
fdshap_rc = struct.unpack_from('<I', fdshap, 6)[0]
print(f"FDSHAP.DAT: {fdshap_rc} resources")

fdshap_offsets = []
for i in range(fdshap_rc):
    offset = struct.unpack_from('<I', fdshap, 10 + i * 4)[0]
    fdshap_offsets.append(offset)

# Resource 1 (tiles)
res1_start = fdshap_offsets[1]
res1_end = fdshap_offsets[2] if 2 < len(fdshap_offsets) else len(fdshap)
res1_size = res1_end - res1_start

print(f"\nResource 1: start={res1_start}, size={res1_size}")

tile_w, tile_h = struct.unpack_from('<HH', fdshap, res1_start)
print(f"Tile dimensions: {tile_w}x{tile_h}")

# Analyze byte 4-5
byte4_5 = struct.unpack_from('<H', fdshap, res1_start + 4)[0]
print(f"Byte 4-5: 0x{byte4_5:04X} = {byte4_5}")

# Parse DWORD offsets from byte 6
tile_offsets_dword = []
pos = res1_start + 6
consecutive_invalid = 0
while pos + 4 <= res1_start + res1_size:
    offset_val = struct.unpack_from('<I', fdshap, pos)[0]
    if 0 < offset_val < res1_size:
        tile_offsets_dword.append(offset_val)
        consecutive_invalid = 0
    else:
        consecutive_invalid += 1
        if consecutive_invalid >= 3:
            break
    pos += 4

print(f"\nDWORD offset table (from byte 6):")
print(f"Found {len(tile_offsets_dword)} tiles")
print(f"First 5 offsets: {tile_offsets_dword[:5]}")
print(f"Last 5 offsets: {tile_offsets_dword[-5:] if len(tile_offsets_dword) >= 5 else tile_offsets_dword}")

# Parse [offset(2), zero(2)] format from byte 6
tile_offsets_word = []
pos = res1_start + 6
consecutive_invalid = 0
while pos + 4 <= res1_start + res1_size:
    offset_val = struct.unpack_from('<H', fdshap, pos)[0]
    zero_val = struct.unpack_from('<H', fdshap, pos + 2)[0]
    if zero_val == 0 and 0 < offset_val < res1_size:
        tile_offsets_word.append(offset_val)
        consecutive_invalid = 0
    else:
        consecutive_invalid += 1
        if consecutive_invalid >= 3:
            break
    pos += 4

print(f"\n[Offset(2), zero(2)] format (from byte 6):")
print(f"Found {len(tile_offsets_word)} tiles")
print(f"First 5 offsets: {tile_offsets_word[:5]}")

# Check if tile offsets match terrain IDs
with open("game/FDFIELD.DAT", "rb") as f:
    fdfield = f.read()

fdfield_offsets = []
pos = 6
while pos + 4 <= len(fdfield):
    offset = struct.unpack_from('<I', fdfield, pos)[0]
    if offset > pos and offset < len(fdfield):
        fdfield_offsets.append(offset)
    else:
        break
    pos += 4

# Map 0 layout
layout_start = fdfield_offsets[0]
w = struct.unpack_from('<H', fdfield, layout_start)[0]
h = struct.unpack_from('<H', fdfield, layout_start + 2)[0]

# Parse terrain IDs
tile_data = fdfield[layout_start + 4:]
terrain_ids = []
pos = 0
for y in range(h):
    for x in range(w):
        if pos + 4 <= len(tile_data):
            tid = struct.unpack_from('<H', tile_data, pos)[0]
            terrain_ids.append(tid)
            pos += 4

print(f"\nMap 0 terrain IDs: {w}x{h}")
print(f"Range: {min(terrain_ids)}-{max(terrain_ids)}")
print(f"Unique: {len(set(terrain_ids))}")

# Check which tile count fits better
print(f"\nComparison:")
print(f"  DWORD table: {len(tile_offsets_dword)} tiles, max terrain {max(terrain_ids)} fits? {'[OK]' if max(terrain_ids) < len(tile_offsets_dword) else '[EXCEEDS]'}")
print(f"  WORD table: {len(tile_offsets_word)} tiles, max terrain {max(terrain_ids)} fits? {'[OK]' if max(terrain_ids) < len(tile_offsets_word) else '[EXCEEDS]'}")
