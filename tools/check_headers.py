import struct
import os

dat_path = 'game/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    magic = f.read(6)
    count = struct.unpack('<I', f.read(4))[0]
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])
    
    print('Resource headers:\n')
    
    for i in range(8):
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else os.path.getsize(dat_path)
        size = end - start
        
        f.seek(start)
        header = f.read(min(16, size))
        
        print(f'Resource #{i}: size={size}')
        print(f'  Hex: {header.hex()}')
        
        # Try to interpret as RLE header
        if size >= 4:
            w = header[0] | (header[1] << 8)
            h = header[2] | (header[3] << 8)
            print(f'  As RLE: {w}x{h}')
            
            # Check if valid
            if w > 0 and w < 500 and h > 0 and h < 500:
                print(f'  -> VALID RLE IMAGE')
            else:
                print(f'  -> NOT RLE (invalid dimensions)')
        print()
