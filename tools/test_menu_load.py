import struct
import os

dat_path = 'game/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    # Read FDOTHER header
    magic = f.read(6)
    count = struct.unpack('<I', f.read(4))[0]
    
    # Read offset table (starts at byte 10)
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])
    
    print(f'FDOTHER.DAT: {count} resources\n')
    print('Checking menu resources #1-6:\n')
    
    for i in range(1, 7):
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else os.path.getsize(dat_path)
        size = end - start
        
        print(f'Resource #{i}:')
        print(f'  File offset: 0x{start:06x} ({start})')
        print(f'  Size: {size} bytes')
        
        if size >= 4:
            f.seek(start)
            header = f.read(4)
            w = header[0] | (header[1] << 8)
            h = header[2] | (header[3] << 8)
            
            print(f'  First 4 bytes: {header.hex()}')
            print(f'  Width={w}, Height={h}')
            
            # Check if valid RLE
            if w > 0 and w <= 320 and h > 0 and h <= 50:
                print(f'  -> VALID RLE MENU ITEM')
            else:
                print(f'  -> INVALID RLE (not a menu item?)')
                print(f'  First 16 bytes: {f.seek(start) or f.read(16).hex()}')
        print()
