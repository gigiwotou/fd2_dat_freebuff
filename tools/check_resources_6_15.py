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
    print('Checking resources #6-#15 for menu images:\n')
    
    for i in range(6, 16):
        if i >= count:
            break
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else os.path.getsize(dat_path)
        size = end - start
        
        print(f'Resource {i}: size={size} bytes')
        
        if size >= 4:
            f.seek(start)
            header = f.read(4)
            w = header[0] | (header[1] << 8)
            h = header[2] | (header[3] << 8)
            
            if size == 768:
                print(f'  -> PALETTE')
            elif w > 0 and w <= 320 and h > 0 and h <= 200:
                print(f'  -> RLE IMAGE {w}x{h}')
            else:
                print(f'  -> OTHER (header={header.hex()})')
