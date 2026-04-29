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

print(f'Parsed {len(offsets)} resource offsets')

# Map 0
layout_start = offsets[0]
w = struct.unpack_from('<H', data, layout_start)[0]
h = struct.unpack_from('<H', data, layout_start + 2)[0]
print(f'Map 0: {w}x{h}')

# Parse terrain IDs using IDA sub_4DF4C formula
# After sub_4DF4C processes the data:
#   byte[2] = byte[2] & 0x1F  (5 bits, 0-31)
#   byte[1] = byte[1] & 3     (2 bits, 0-3)
# terrain_id = byte[2] | (byte[1] << 5) = (byte[1] << 5) | byte[2]

tile_data = data[layout_start + 4:]
terrain_ids_old = []
terrain_ids_new = []
pos = 0
for y in range(h):
    for x in range(w):
        if pos + 4 <= len(tile_data):
            b0 = tile_data[pos]
            b1 = tile_data[pos + 1]
            b2 = tile_data[pos + 2]
            b3 = tile_data[pos + 3]
            
            # OLD formula (what Python was using before)
            tid_old = struct.unpack_from('<H', tile_data, pos)[0]
            terrain_ids_old.append(tid_old)
            
            # NEW formula (from IDA sub_4DF4C)
            # After masking: b2 &= 0x1F, b1 &= 3
            # terrain_id = (b1 << 5) | b2
            tid_new = ((b1 & 3) << 5) | (b2 & 0x1F)
            terrain_ids_new.append(tid_new)
            
            pos += 4

print(f'\nOLD formula (raw 16-bit):')
print(f'  Range: {min(terrain_ids_old)}-{max(terrain_ids_old)}')
print(f'  Unique: {len(set(terrain_ids_old))}')
counter_old = Counter(terrain_ids_old)
print(f'  Top 10:')
for tid, count in counter_old.most_common(10):
    print(f'    {tid}: {count} times')

print(f'\nNEW formula ((b1&3)<<5 | (b2&0x1F)):')
print(f'  Range: {min(terrain_ids_new)}-{max(terrain_ids_new)}')
print(f'  Unique: {len(set(terrain_ids_new))}')
counter_new = Counter(terrain_ids_new)
print(f'  Top 10:')
for tid, count in counter_new.most_common(10):
    print(f'    {tid}: {count} times')
