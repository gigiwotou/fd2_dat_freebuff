import struct
import os

dat_path = 'game/FDOTHER.DAT'
if not os.path.exists(dat_path):
    print(f"Error: {dat_path} not found")
    exit(1)

with open(dat_path, 'rb') as f:
    magic = f.read(6)
    print(f'Magic: {magic}')
    
    count = struct.unpack('<I', f.read(4))[0]
    print(f'Resource count: {count}')
    
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])
    
    print(f'\nOffsets[0..19]:')
    for i in range(min(20, count)):
        print(f'  [{i}] = {offsets[i]}')
    
    print(f'\nResource sizes:')
    for i in range(min(15, count)):
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else os.path.getsize(dat_path)
        size = end - start
        print(f'  Resource {i}: offset={start}, size={size}')
    
    print(f'\nChecking resource #7 (menu resource set):')
    start7 = offsets[7]
    end7 = offsets[8] if 8 < count else os.path.getsize(dat_path)
    size7 = end7 - start7
    print(f'  Resource 7: offset={start7}, size={size7}')
    
    # Read resource #7 header to check if it's a container
    f.seek(start7)
    header = f.read(16)
    print(f'  Header bytes: {header.hex()}')
    
    # Check first few bytes for possible dimensions
    if size7 > 4:
        f.seek(start7)
        w = struct.unpack('<H', f.read(2))[0]
        h = struct.unpack('<H', f.read(2))[0]
        print(f'  Possible dimensions: {w}x{h}')
