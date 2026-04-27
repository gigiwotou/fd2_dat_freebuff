import struct
import os

dat_path = 'game/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    # Read header
    magic = f.read(6)
    count = struct.unpack('<I', f.read(4))[0]
    
    # Read all offsets
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])
    
    # Check resource #7
    start7 = offsets[7]
    end7 = offsets[8] if 8 < count else os.path.getsize(dat_path)
    size7 = end7 - start7
    
    print(f'Resource #7: offset={start7}, size={size7} bytes')
    print(f'768 bytes = 256 colors * 3 bytes = palette?')
    
    if size7 == 768:
        print(f'\nThis is a PALETTE resource (256 colors)!')
        f.seek(start7)
        palette = f.read(768)
        
        # Print first 16 palette entries
        print(f'\nFirst 16 palette entries (RGB):')
        for i in range(16):
            r = palette[i*3]
            g = palette[i*3+1]
            b = palette[i*3+2]
            print(f'  [{i}] = ({r}, {g}, {b})')
    
    # Check other resources that might be menu images
    print(f'\nChecking resources 1-6 for menu images:')
    for i in range(1, 8):
        if i >= count:
            continue
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else os.path.getsize(dat_path)
        size = end - start
        
        print(f'\nResource {i}: size={size} bytes')
        
        if size >= 4:
            f.seek(start)
            header = f.read(8)
            w = header[0] | (header[1] << 8)
            h = header[2] | (header[3] << 8)
            
            if w > 0 and w < 500 and h > 0 and h < 500:
                print(f'  RLE header: {w}x{h} - POSSIBLE MENU IMAGE!')
            else:
                print(f'  Header: {header.hex()}')
