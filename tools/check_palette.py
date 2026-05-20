import struct

with open('game/FDOTHER.DAT', 'rb') as f:
    data = f.read()

off_start = struct.unpack('<I', data[10+75*4:14+75*4])[0]
off_end = struct.unpack('<I', data[10+76*4:14+76*4])[0]
pal = data[off_start:off_end]

print(f'Palette size: {len(pal)}')
print(f'First 32 colors (raw RGB):')
for i in range(32):
    r, g, b = pal[i*3], pal[i*3+1], pal[i*3+2]
    print(f'  [{i}] R={r:3d} G={g:3d} B={b:3d}  (0x{r:02X}{g:02X}{b:02X})')

# Check if it might be BGR order
print(f'\nIf interpreted as BGR:')
for i in range(16):
    b, g, r = pal[i*3], pal[i*3+1], pal[i*3+2]
    print(f'  [{i}] R={r:3d} G={g:3d} B={b:3d}')
