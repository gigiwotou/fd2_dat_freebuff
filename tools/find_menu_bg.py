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
    
    # Check resource #101 (menu background)
    print('Resource #101 (Menu Background):')
    start101 = offsets[101] if 101 < count else 0
    end101 = offsets[102] if 102 < count else os.path.getsize(dat_path)
    size101 = end101 - start101 if start101 else 0
    print(f'  Offset: {start101}, Size: {size101}')
    
    if size101 >= 4:
        f.seek(start101)
        header = f.read(8)
        w = header[0] | (header[1] << 8)
        h = header[2] | (header[3] << 8)
        print(f'  Header: {header[:4].hex()}')
        print(f'  W={w}, H={h}')
        print(f'  First 32 bytes: {f.seek(start101) or f.read(32).hex()}')
    
    # Check resources #73-76 (title screen related)
    print(f'\nChecking title screen resources (#73-76):')
    for i in [73, 74, 75, 76]:
        if i >= count:
            continue
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else os.path.getsize(dat_path)
        size = end - start
        
        print(f'\n  Resource #{i}: size={size}')
        if size >= 4:
            f.seek(start)
            header = f.read(4)
            w = header[0] | (header[1] << 8)
            h = header[2] | (header[3] << 8)
            print(f'    W={w}, H={h}, header={header.hex()}')
    
    # Search for resources that look like RLE images (valid w,h)
    print(f'\n\nSearching for valid RLE images (w<=320, h<=200):')
    for i in range(count):
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else os.path.getsize(dat_path)
        size = end - start
        
        if size >= 4 and size <= 100000:
            f.seek(start)
            header = f.read(4)
            w = header[0] | (header[1] << 8)
            h = header[2] | (header[3] << 8)
            
            if w > 0 and w <= 320 and h > 0 and h <= 200:
                print(f'  Resource #{i}: {w}x{h}, size={size}')
