"""
重新分析资源#8的LMI1格式
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
    
    # Resource #8 (用户说的#7，但从0开始计数是#8)
    start8 = offsets[8]
    end8 = offsets[9] if 9 < count else os.path.getsize(dat_path)
    size8 = end8 - start8
    
    print(f'Resource #8 (LMI1): size={size8} bytes\n')
    
    f.seek(start8)
    data = f.read(size8)
    
    # Print header bytes
    print('Header analysis:')
    print(f'  Bytes 0-3: {data[0:4]} (LMI1 magic)')
    
    # Bytes 4+ look like 3-byte offsets
    print('\nParsing as 3-byte offsets starting at byte 4:')
    sub_offsets = []
    for i in range(14):
        pos = 4 + i * 3
        if pos + 3 <= size8:
            val = data[pos] | (data[pos+1] << 8) | (data[pos+2] << 16)
            sub_offsets.append(val)
            print(f'  [{i}] = {val} (0x{val:06x})')
    
    if len(sub_offsets) == 14:
        print('\n7 sub-resources:')
        for i in range(7):
            img_start = sub_offsets[i*2]
            img_end = sub_offsets[i*2+1]
            img_size = img_end - img_start
            
            print(f'\n  Image {i}: offset {img_start}-{img_end}, size={img_size}')
            
            if img_size > 0 and img_start < size8:
                # Print first few bytes
                end = min(img_start + 20, size8)
                print(f'    First bytes: {data[img_start:end].hex()}')
