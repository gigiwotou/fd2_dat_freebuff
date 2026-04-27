"""
检查资源#8是否是资源集
结构：LMI1 + 偏移表 + 子资源数据
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
    
    print(f'Resource #8: offset={start8}, size={size8}')
    
    f.seek(start8)
    data = f.read(size8)
    
    # Header: LMI1 (4 bytes)
    # Then possibly offset table
    print(f'\nHeader: {data[0:4]}')
    
    # Check bytes 4+ for offsets
    print(f'\nPossible offset table (starting at byte 4):')
    for i in range(14):
        pos = 4 + i * 4
        if pos + 4 <= size8:
            off = struct.unpack('<I', data[pos:pos+4])[0]
            print(f'  Offset[{i}] = {off} (0x{off:08x})')
    
    # If these are offsets within the resource, check what they point to
    print(f'\nVerifying offsets:')
    for i in range(7):
        img_start = struct.unpack('<I', data[4 + i*4:8 + i*4])[0]
        img_end = struct.unpack('<I', data[4 + (i+1)*4:8 + (i+1)*4])[0]
        
        if img_start < size8 and img_end <= size8:
            img_size = img_end - img_start
            print(f'  Image {i}: offset {img_start}-{img_end}, size={img_size}')
            
            # Check RLE header at this offset
            if img_size >= 4:
                w = data[img_start] | (data[img_start+1] << 8)
                h = data[img_start+2] | (data[img_start+3] << 8)
                print(f'    Possible dims: {w}x{h}')
