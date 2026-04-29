import struct
from collections import Counter

data = open('game/FDFIELD.DAT', 'rb').read()
layout_start = 406
w = 24
h = 24

tile_data = data[layout_start + 4:layout_start + 4 + w*h*4]
print(f'Tile data size: {len(tile_data)} bytes')
print(f'First 10 tiles raw bytes:')
for i in range(10):
    b0 = tile_data[i*4]
    b1 = tile_data[i*4 + 1]
    b2 = tile_data[i*4 + 2]
    b3 = tile_data[i*4 + 3]
    terrain_id = ((b2 & 0x1F) << 2) | (b1 & 3)
    print(f'  Tile {i}: [{b0:02x} {b1:02x} {b2:02x} {b3:02x}] -> terrain_id={terrain_id}')

# Calculate all terrain IDs with the IDA formula
terrain_ids = []
pos = 0
for y in range(h):
    row = []
    for x in range(w):
        if pos + 4 <= len(tile_data):
            b0 = tile_data[pos]
            b1 = tile_data[pos + 1]
            b2 = tile_data[pos + 2]
            b3 = tile_data[pos + 3]
            tid = ((b2 & 0x1F) << 2) | (b1 & 3)
            terrain_ids.append(tid)
            pos += 4

print(f'\nTerrain ID stats:')
print(f'Range: {min(terrain_ids)}-{max(terrain_ids)}')
print(f'Unique: {len(set(terrain_ids))}')
counter = Counter(terrain_ids)
print('Top 15 terrain IDs:')
for tid, count in counter.most_common(15):
    print(f'  {tid}: {count} times')
