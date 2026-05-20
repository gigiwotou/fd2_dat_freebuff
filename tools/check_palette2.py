import struct

with open('game/FDOTHER.DAT', 'rb') as f:
    data = f.read()

off_start = struct.unpack('<I', data[10+75*4:14+75*4])[0]
off_end = struct.unpack('<I', data[10+76*4:14+76*4])[0]
pal = data[off_start:off_end]
print(f'Palette size: {len(pal)}')

# Find bright colors that would be used for skin/hair
print('Colors with high values:')
for i in range(256):
    r, g, b = pal[i*3:i*3+3]
    if r > 40 or g > 40 or b > 40:
        print(f'  [{i}] r={r:3d} g={g:3d} b={b:3d}')
