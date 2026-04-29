import struct

data = open('game/FDSHAP.DAT', 'rb').read()
rc = struct.unpack_from('<I', data, 6)[0]
print(f'FDSHAP.DAT: {rc} resources')

# Parse resource offsets
offsets = []
for i in range(rc):
    offsets.append(struct.unpack_from('<I', data, 10 + i * 4)[0])

# Resource 0 (palette)
print(f'\nResource 0 (palette):')
print(f'  Start: {offsets[0]}, Size: {offsets[1] - offsets[0]}')
print(f'  First 16 bytes: {data[offsets[0]:offsets[0]+16].hex(" ")}')

# Resource 1 (tiles)
res1_start = offsets[1]
res1_end = offsets[2] if 2 < len(offsets) else len(data)
print(f'\nResource 1 (tiles):')
print(f'  Start: {res1_start}, Size: {res1_end - res1_start}')
print(f'  First 32 bytes: {data[res1_start:res1_start+32].hex(" ")}')

# Parse header
tile_w = struct.unpack_from('<H', data, res1_start)[0]
tile_h = struct.unpack_from('<H', data, res1_start + 2)[0]
print(f'  Tile dimensions: {tile_w}x{tile_h}')

# Check offset table starting at byte 4
print(f'\nOffset table analysis:')
print(f'  Byte 4-5 (H): {struct.unpack_from("<H", data, res1_start + 4)[0]}')
print(f'  Byte 6-7 (H): {struct.unpack_from("<H", data, res1_start + 6)[0]}')
print(f'  Byte 8-9 (H): {struct.unpack_from("<H", data, res1_start + 8)[0]}')
print(f'  Byte 10-11 (H): {struct.unpack_from("<H", data, res1_start + 10)[0]}')

# Check if offsets are 4-byte entries
print(f'\nChecking 4-byte entries (offset + zero):')
pos = res1_start + 4
for i in range(10):
    offset_val = struct.unpack_from('<H', data, pos)[0]
    zero_val = struct.unpack_from('<H', data, pos + 2)[0]
    print(f'  Entry {i}: offset={offset_val}, zero={zero_val} (at pos {pos - res1_start})')
    pos += 4
