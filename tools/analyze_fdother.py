import struct
import os

dat_path = 'game/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    # Read header
    magic = f.read(6)
    count = struct.unpack('<I', f.read(4))[0]
    print(f'File: {dat_path}')
    print(f'Magic: {magic}')
    print(f'Resource count: {count}')
    
    # Read all offsets
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])
    
    # Show resources 0-10
    print(f'\nResources 0-10:')
    for i in range(min(11, count)):
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else os.path.getsize(dat_path)
        size = end - start
        
        # Read header if possible
        f.seek(start)
        header = f.read(min(8, size))
        
        print(f'\n  Resource {i}: offset={start}, size={size}')
        print(f'    Header: {header.hex()}')
        
        if size >= 4:
            val = struct.unpack('<I', header[:4])[0]
            print(f'    First 4 bytes as u32: {val}')
