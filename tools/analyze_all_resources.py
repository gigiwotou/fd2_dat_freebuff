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
    
    print(f'Total resources: {count}\n')
    
    # Check resources around #7-10
    print('Checking resources #0-#15:')
    for i in range(16):
        if i >= count:
            break
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else os.path.getsize(dat_path)
        size = end - start
        
        print(f'\nResource {i}: offset={start}, size={size} bytes')
        
        if size >= 4:
            f.seek(start)
            header = f.read(8)
            w = header[0] | (header[1] << 8)
            h = header[2] | (header[3] << 8)
            
            print(f'  Header: {header.hex()}')
            
            if size == 768:
                print(f'  Type: PALETTE (256 colors)')
            elif w > 0 and w <= 320 and h > 0 and h <= 200:
                print(f'  Type: RLE IMAGE {w}x{h}')
            else:
                print(f'  Type: OTHER (not RLE: {w}x{h})')
