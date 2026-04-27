"""
分析资源#8是否是菜单资源集（LMI1格式）
"""
import struct
import os

dat_path = 'game/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    magic = f.read(6)
    count = struct.unpack('<I', f.read(4))[0]
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])
    
    # Resource #8
    start8 = offsets[8]
    end8 = offsets[9] if 9 < count else os.path.getsize(dat_path)
    size8 = end8 - start8
    
    print(f'Resource #8: size={size8} bytes\n')
    
    f.seek(start8)
    data = f.read(size8)
    
    # Structure:
    # Bytes 0-3: "LMI1" (magic)
    # Bytes 4-39: 14 x 2-byte LE offsets (7 pairs defining sub-resource boundaries)
    # Bytes 40+: sub-resource data
    
    # Parse offsets
    print('Sub-resource boundaries (2-byte LE offsets):')
    bounds = []
    for i in range(14):
        pos = 4 + i * 2
        val = struct.unpack('<H', data[pos:pos+2])[0]
        bounds.append(val)
        print(f'  [{i}] = {val} (0x{val:04x})')
    
    # Calculate sub-resource sizes
    print(f'\n7 sub-resources:')
    for i in range(7):
        img_start = bounds[i*2]
        img_end = bounds[i*2+1]
        img_size = img_end - img_start
        
        print(f'\n  Image {i}: offset {img_start}-{img_end}, size={img_size}')
        
        if img_size >= 2 and img_start + 2 < size8:
            w = data[img_start]
            h = data[img_start+1]
            print(f'    Header: w={w}, h={h}')
            print(f'    First 16 bytes: {data[img_start:img_start+16].hex()}')
            
            # Check if pixel data follows
            if img_size > 2:
                pixels = data[img_start+2:img_start+18]
                print(f'    Pixel data: {pixels.hex()}')
