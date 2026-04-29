import struct
from collections import Counter

data = open('game/FDFIELD.DAT', 'rb').read()

# Parse resource offsets
rc = struct.unpack_from('<I', data, 6)[0]
offsets = []
pos = 6
while pos < len(data) - 4 and len(offsets) < rc:
    offset = struct.unpack_from('<I', data, pos)[0]
    if offset > pos and offset < len(data):
        offsets.append(offset)
    else:
        break
    pos += 4

layout_start = offsets[0]
w = struct.unpack_from('<H', data, layout_start)[0]
h = struct.unpack_from('<H', data, layout_start + 2)[0]

# Check FDSHAP resource 1 tile count
fdshap = open('game/FDSHAP.DAT', 'rb').read()
fdshap_rc = struct.unpack_from('<I', fdshap, 6)[0]
fdshap_offsets = []
for i in range(fdshap_rc):
    fdshap_offsets.append(struct.unpack_from('<I', fdshap, 10 + i * 4)[0])

res1_start = fdshap_offsets[1]
tile_w = struct.unpack_from('<H', fdshap, res1_start)[0]
tile_h = struct.unpack_from('<H', fdshap, res1_start + 2)[0]

# Count tiles
tile_offsets = []
pos = res1_start + 4
while pos + 4 <= len(fdshap):
    offset_val = struct.unpack_from('<H', fdshap, pos)[0]
    zero_val = struct.unpack_from('<H', fdshap, pos + 2)[0]
    if zero_val == 0 and offset_val > 0:
        tile_offsets.append(offset_val)
    pos += 4
    if offset_val > len(fdshap) - 500:
        break

print(f'FDSHAP resource 1: {tile_w}x{tile_h} tiles')
print(f'Total tiles: {len(tile_offsets)}')

# Parse terrain IDs (original 16-bit)
tile_data = data[layout_start + 4:]
terrain_ids = []
pos = 0
for y in range(h):
    for x in range(w):
        if pos + 4 <= len(tile_data):
            tid = struct.unpack_from('<H', tile_data, pos)[0]
            terrain_ids.append(tid)
            pos += 4

print(f'\nTerrain IDs (raw 16-bit):')
print(f'Range: {min(terrain_ids)}-{max(terrain_ids)}')
print(f'Unique: {len(set(terrain_ids))}')

# Check which terrain IDs fit in tile count
max_tid = max(terrain_ids)
print(f'Max terrain ID: {max_tid}')
print(f'Fits in {len(tile_offsets)} tiles? {"[OK]" if max_tid < len(tile_offsets) else "[EXCEEDS]"}')

# Apply different masks to see which one fits best
print(f'\nMask analysis:')
for mask in [0x1F, 0x3F, 0x7F, 0xFF]:
    masked = [tid & mask for tid in terrain_ids]
    max_masked = max(masked)
    unique = len(set(masked))
    fits = "[OK]" if max_masked < len(tile_offsets) else "[EXCEEDS]"
    print(f'  Mask 0x{mask:02X}: {unique} unique, max {max_masked}, fits {len(tile_offsets)} tiles? {fits}')
