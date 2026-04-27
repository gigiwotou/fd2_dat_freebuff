import struct
import os

dat_path = 'game/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    magic = f.read(6)
    count = struct.unpack('<I', f.read(4))[0]
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])
    
    print(f'Total resources: {count}')
    print(f'\nMenu resources analysis:')
    print(f'FDOTHER #7 = menu palette (768 bytes)')
    print(f'FDOTHER #1-6 = menu item images\n')
    
    # Check resource #7 (palette)
    print(f'Resource #7 (Menu Palette):')
    start7 = offsets[7]
    end7 = offsets[8] if 8 < count else os.path.getsize(dat_path)
    size7 = end7 - start7
    print(f'  Size: {size7} bytes')
    
    if size7 == 768:
        f.seek(start7)
        pal = f.read(768)
        print(f'  Type: 256-color palette')
        print(f'  First entry: ({pal[0]}, {pal[1]}, {pal[2]})')
        print(f'  Entry 15: ({pal[45]}, {pal[46]}, {pal[47]})')
    
    # Check menu items #1-6
    print(f'\nMenu item resources #1-6:')
    for i in range(1, 7):
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else os.path.getsize(dat_path)
        size = end - start
        
        print(f'\n  Resource #{i}: size={size} bytes')
        
        if size >= 4:
            f.seek(start)
            header = f.read(4)
            w = header[0] | (header[1] << 8)
            h = header[2] | (header[3] << 8)
            
            if w > 0 and w <= 320 and h > 0 and h <= 50:
                print(f'    Type: MENU ITEM IMAGE')
                print(f'    Dimensions: {w}x{h}')
            else:
                print(f'    Type: OTHER')
                print(f'    Header: w={w}, h={h}')
