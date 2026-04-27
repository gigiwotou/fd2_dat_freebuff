import struct
import os

dat_path = 'game/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    # Read header
    magic = f.read(6)
    count = struct.unpack('<I', f.read(4))[0]
    print(f'File: {dat_path}')
    print(f'Resource count: {count}')
    
    # Read all offsets
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0]))
    
    # Resource #7
    start7 = offsets[7]
    end7 = offsets[8] if 8 < count else os.path.getsize(dat_path)
    size7 = end7 - start7
    
    print(f'\nResource #7: offset={start7}, size={size7}')
    
    f.seek(start7)
    data = f.read(size7)
    
    # Check if it's a resource set (header with sub-resource offsets)
    if size7 > 4:
        # First 4 bytes might be sub-resource count
        sub_count = struct.unpack('<I', data[:4])[0]
        print(f'First 4 bytes as u32: {sub_count}')
        
        # Check if it looks like a resource set header
        # Format: count + offsets
        if 4 + sub_count * 4 <= size7:
            print(f'Possible resource set with {sub_count} sub-resources')
            print('Sub-resource offsets:')
            for i in range(sub_count):
                off = struct.unpack('<I', data[4 + i*4:8 + i*4])[0]
                print(f'  [{i}] offset={off}')
