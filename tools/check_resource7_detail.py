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
    
    # Check resource #7 structure
    start7 = offsets[7]
    end7 = offsets[8] if 8 < count else os.path.getsize(dat_path)
    size7 = end7 - start7
    
    print(f'Resource #7:')
    print(f'  Offset: {start7}')
    print(f'  Size: {size7} bytes')
    print(f'  768 bytes = 256 colors * 3 bytes = PALETTE\n')
    
    f.seek(start7)
    pal_data = f.read(768)
    
    # Print all 256 palette entries
    print(f'All 256 palette entries:')
    for i in range(256):
        r = pal_data[i*3]
        g = pal_data[i*3+1]
        b = pal_data[i*3+2]
        if i < 32 or i > 240:
            print(f'  [{i:3d}] = ({r:3d}, {g:3d}, {b:3d})')
    
    # Also check resources #8-15
    print(f'\nResources #8-15:')
    for i in range(8, 16):
        if i >= count:
            continue
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else os.path.getsize(dat_path)
        size = end - start
        
        f.seek(start)
        header = f.read(4)
        w = header[0] | (header[1] << 8)
        h = header[2] | (header[3] << 8)
        
        type_str = f'RLE {w}x{h}' if (w > 0 and w <= 320 and h > 0 and h <= 200) else f'OTHER'
        if size == 768:
            type_str = 'PALETTE'
        
        print(f'  #{i}: size={size:8d} -> {type_str}')
