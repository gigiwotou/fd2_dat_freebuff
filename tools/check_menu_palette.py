import struct
import os

dat_path = 'game/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    magic = f.read(6)
    count = struct.unpack('<I', f.read(4))[0]
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])
    
    print(f'Total resources: {count}\n')
    
    # Resources around #7-8 (palette and menu related)
    print('Checking palette/menu related resources:')
    for i in [7, 8, 9, 99, 101, 102]:
        if i >= count:
            continue
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else os.path.getsize(dat_path)
        size = end - start
        
        print(f'\nResource #{i}: size={size}')
        if size == 768:
            print(f'  -> PALETTE')
            f.seek(start)
            pal = f.read(48)
            print(f'  First 16 entries (RGB):')
            for j in range(16):
                r, g, b = pal[j*3], pal[j*3+1], pal[j*3+2]
                print(f'    [{j}] = ({r},{g},{b})')
        elif size >= 4:
            f.seek(start)
            header = f.read(4)
            w = header[0] | (header[1] << 8)
            h = header[2] | (header[3] << 8)
            if w > 0 and w <= 320 and h > 0 and h <= 200:
                print(f'  -> RLE IMAGE {w}x{h}')
            else:
                print(f'  -> OTHER (w={w}, h={h})')
